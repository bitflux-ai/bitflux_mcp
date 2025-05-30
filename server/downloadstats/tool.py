import argparse
from ..bitflux_catcher_api import DefaultApi
from ..bitflux_catcher_api import Configuration
from ..bitflux_catcher_api import ApiClient
from ..bitflux_catcher_api import DownloadStatsRequest
from ..machine_lookup import machine_lookup
from ..bitflux_catcher_api import downloadstats_pb2
from google.protobuf import json_format
from typing import Any, Dict, List
import polars as pl
import io
import math

def transform_data_format(data_list: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    """
    Transform data from a list of dictionaries to a dictionary of lists.
    
    Args:
        data_list: List of dictionaries where each dictionary represents a data point
        
    Returns:
        Dictionary where keys are column names and values are lists of data points
    """
    if not data_list:
        return {}
    
    result = {}
    # Initialize the result dictionary with empty lists for each key
    for key in data_list[0].keys():
        result[key] = []
    
    # Populate the lists
    for data_point in data_list:
        for key, value in data_point.items():
            result[key].append(value)
            
    return result

def scale_bitflux_data(stats: Dict[str, Any], df: pl.DataFrame) -> pl.DataFrame:
    """
    Reformat the dataframe from a ring buffer to a linear sequence and scale values by unitsize.

    Args:
        stats: Dictionary containing metadata about the stats (head, tail, length, unitsize)
        df: DataFrame containing the raw stats data

    Returns:
        Reformatted DataFrame with values properly scaled
    """
    if stats.get('length', 0) == 0:
        return df

    # Extract ring buffer parameters
    head = stats.get('head', 0)
    tail = stats.get('tail', 0)
    length = stats.get('length', 0)
    unitsize = stats.get('unitsize', 1)

    # Reorder the dataframe to represent the correct time sequence
    if tail <= head:
        # Data is contiguous in the buffer
        df_reordered = df.slice(tail, length)
    else:
        # Data wraps around the buffer
        # Concatenate the two parts: from tail to end, and from start to head
        df_tail_to_end = df.slice(tail, len(df) - tail)
        df_start_to_head = df.slice(0, head + 1)
        df_reordered = pl.concat([df_tail_to_end, df_start_to_head])

    # Scale all columns except idle_cpu by unitsize
    columns_to_scale = [col for col in df_reordered.columns if col != 'idle_cpu']

    # Resize column types before scaling
    df_reordered = df_reordered.with_columns(
        [pl.col(c).cast(pl.UInt64) for c in columns_to_scale]
    )

    # Create a new dataframe with scaled values
    scaled_cols = []
    for col in df_reordered.columns:
        if col in columns_to_scale:
            # Multiply by unitsize for all columns except idle_cpu
            scaled_cols.append(df_reordered[col] * unitsize)
        else:
            # Keep idle_cpu as is
            scaled_cols.append(df_reordered[col])

    # Create new dataframe with scaled columns
    scaled_df = pl.DataFrame({
        col: scaled_cols[i] for i, col in enumerate(df_reordered.columns)
    })

    # if the first row has reclaimable as 0, drop it
    if scaled_df.shape[0] > 0 and scaled_df.get_column('reclaimable').first() == 0:
        scaled_df = scaled_df.slice(1, scaled_df.shape[0] - 1)

    return scaled_df

def summarize_bitflux_data(df: pl.DataFrame) -> Dict[str, Any]:
    """
    Summarize bitflux data into a structured dictionary with statistical metrics.
    
    Args:
        df: DataFrame containing the bitflux data
        
    Returns:
        Dictionary with statistical summaries for each column
    """
    if df.is_empty():
        return {"error": "No data available for summary"}

    # Suppose df is your DataFrame
    n = len(df)

    # 1. Decide max "9's" = floor(log10(n))
    #    E.g. n=1000 → log10(1000)=3 → up to .999
    max_nines = max(1, int(math.floor(math.log10(n))))

    # (Optional) Cap it so you don't go crazy if n is huge
    max_nines = min(max_nines, 5)  # at most .99999

    # 2. Build percentiles: for k in 1..max_nines, percentile = 1 - 10**(-k)
    percentiles = [1 - 10**(-k) for k in range(1, max_nines+1)]
    # 3. Add 95th percentile for fun
    percentiles.insert(1, 0.95)

    # Get basic statistics using describe
    stats_df = df.describe(percentiles=percentiles)

    # Convert to a more structured dictionary format
    summary = {}

    # Extract column names (excluding the 'statistic' column)
    columns = [col for col in stats_df.columns if col != 'statistic']

    # For each column in the original dataframe
    for col in columns:
        # Create a dictionary for this column's statistics
        col_stats = {}

        # Extract statistics for this column
        for i, stat_name in enumerate(stats_df['statistic']):
            # Convert to native Python type for JSON serialization
            value = stats_df[col][i]
            if isinstance(value, (pl.Decimal, pl.Float32, pl.Float64)):
                value = float(value)
            elif isinstance(value, (pl.Int8, pl.Int16, pl.Int32, pl.Int64, 
                                   pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64)):
                value = int(value)

            col_stats[stat_name] = value

        summary[col] = col_stats

    # Add additional useful statistics
    for col in columns:
        # Add median if not already included
        if 'median' not in summary[col] and df.shape[0] > 0:
            summary[col]['median'] = float(df[col].median())

        # Add sum for relevant columns (excluding percentages or ratios)
        if col not in ['idle_cpu']:  # Add other columns to exclude if needed
            summary[col]['sum'] = float(df[col].sum())

    return summary

def download_stats_by_machine_key(machine_key: str, url: str) -> Dict[str, Any]:
    # Initialize API client
    configuration = Configuration(host=url)
    with ApiClient(configuration) as api_client:
        api_instance = DefaultApi(api_client)
        body = DownloadStatsRequest(machine_key=machine_key)

        response = None
        try:
            # Call the API
            response = api_instance.download_stats(download_stats_request=body)
        except Exception as e:
            print(f"Error calling download_stats: {e}")
            return {}

        # Parse Protobuf response
        statspb = downloadstats_pb2.Stats()
        statspb.ParseFromString(response)
        bitfluxstats = statspb.bitflux
        statspb.bitflux = b''
        stats = json_format.MessageToDict(statspb)
        stats.pop('bitflux', None)
        if not len(bitfluxstats) > 0:
            print("No bitflux data received")
            return stats

        try:
            df = pl.read_parquet(io.BytesIO(bitfluxstats))
        except Exception as e:
            print(f"Failed to read Parquet: {e}")
            return {}

        scaled_df = scale_bitflux_data(stats,df)

        output = {}
        output['timestamp'] = stats['timestamp']
        output['sample_rate'] = stats['sampleRate']
        output['mem_total'] = stats['system']['memTotal']
        output['swap_total'] = stats['system']['swapTotal']
        output['num_cpus'] = stats['system']['numCpus']

        # Alternative implementation with safety check
        num_rows = min(25, scaled_df.shape[0])
        data_dicts = scaled_df.tail(num_rows).to_dicts()

        # Transform data from list of dicts to dict of lists
        output['data'] = transform_data_format(data_dicts)

        output['summary'] = summarize_bitflux_data(scaled_df)
        #print(json.dumps(output, indent=4, default=str))
        return output

def download_stats_by_instance_id(instance_id: str, url: str) -> Dict[str, Any]:
    """Download stats from bitflux daemon by instance id"""
    result = machine_lookup(instance_id, "", url)
    machines = []
    for machine in result:
        machines.append(machine['machineKey'])
    if len(machines) == 0:
        raise Exception(f"No machines found for instance_id {instance_id}")
    stats = download_stats_by_machine_key(machines[0], url)
    return stats

def manual() -> None:
    import json
    parser = argparse.ArgumentParser(description="Bitflux DownloadStats CLI")
    parser.add_argument("--machine_key", default="", help="Machine UUID (e.g., 1b5490ef-5bb3-4b1c-92e0-5ccbfc5fa25e)")
    parser.add_argument("--account_id", default="", help="Account ID (e.g., 1234567890)")
    parser.add_argument("--instance_id", default="", help="Instance ID (e.g., i-1234567890)")
    parser.add_argument("--url", default="https://catcher.bitflux.ai", help="API base URL")
    args = parser.parse_args()

    if args.machine_key != "":
        stats = download_stats_by_machine_key(args.machine_key, args.url)
        print(json.dumps(stats, indent=4))
    elif args.instance_id != "":
        stats = download_stats_by_instance_id(args.instance_id, args.url)
        print(json.dumps(stats, indent=4))
    else:
        print("Please provide either machine_key or instance_id")

if __name__ == "__main__":
    manual()
