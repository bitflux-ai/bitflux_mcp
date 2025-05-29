from mcp.server.fastmcp import Context
from typing import Any, Dict
from downloadstats.tool import download_stats_by_machine_key, download_stats_by_instance_id

base_description='''
    Output format is as follows:
      {
        // The instant when metrics were captured (ISO 8601 UTC)
        "timestamp": "2025-05-11T06:31:01.725+00:00",

        // Interval between samples in seconds
        "sample_rate": "120",

        // Total physical RAM in bytes
        "mem_total": "33565847552",

        // Total swap space in bytes
        "swap_total": "157286395904",

        // Number of logical CPU cores
        "num_cpus": "16",

        // A small sample of raw measurements at successive intervals
        "data": {
            // Bytes of unused RAM at this sample
            "free": [17377001472, 17444110336, 17326669824],
            // Bytes used by page cache/slab reclaimable
            "cached": [700448768, 503316480, 629145600],
            // Bytes of swap currently in use
            "swap_used": [17033068544, 17091788800, 17012097024],
            // Bytes of recently used swap pages still in RAM
            "swap_cached": [6870269952, 7109345280, 6857687040],
            // Bytes bitflux can reclaim, meaning it can add this to 'free'
            "reclaimable": [780140544, 855638016, 855638016],
            // Percentage of CPU time idle since last sample
            "idle_cpu": [91, 94, 95]
        }
        // Statistical aggregates over the full sample set (e.g., 682 measurements)
        "summary": {
          "free": {
            // Number of samples collected
            "count": 682,
            // Average bytes free
            "mean": 22996003530.7,
            // Minimum observed bytes free
            "min": 17326669824,
            // 90th percentile
            "90%": 24062722048,
            // 95th percentile
            "95%": 24062722048,
            // 99th percentile
            "99%": 24062722048,
            // Maximum observed bytes free
            "max": 24536678400,
            // Total free bytes summed over all samples
            "sum": 15683274407936
          }, ...
          
          ... "idle_cpu": {
            "count": 682,
            // Average idle CPU percentage
            "mean": 96.55,
            "min": 86,
            "90%": 96,
            "95%": 98,
            "99%": 98,
            "max": 98
          }
        }
      }

    A user will likely want to see a graphs of the memory and cpus over time. You can use the timestamp field as the time of the last sample, with the sample_rate being the time between samples.

    The goal is to see if we can save money with a smaller instance.  The job of this tool is to provide a 
    summary of the data that can be used to make that decision.

    Example:
      Suppose a system presents the following stats:
        "mem_total" = 64GB
        "num_cpus": "8",
        max "mem_free": 2GB,
        max "reclaimable": 40GB,
        min "idle_cpu": 91
      This system using bitflux would have adjusted free memory 2GB + 40GB = 42GB.  Meaning the "used" memory is 64GB - 42GB = 22GB.
      and the used CPU is 100 - 91 = 9%  or 0.09 * 8 = 0.72 cores.  So this workload would probably fit in an instance with 32GB of total RAM and as few as 2 cores.  Therefore we can recommend a smaller cheaper bitflux enabled instance that can statisfy these parameters

      If however "reclaimable" was only 4GB or idle_cpu was min of 20% then we would not recommend using a smaller instance.

    NOTE: You might be trained to consider swap usage as a sign that we need more memory, however so long as the adjusted free memory remains above 10% of total memory, disregard swap usage as a potential problem for the purpose of sizing EC2 instances.
    '''

class DownloadStatsByMachineKeyTool():
    name='download_stats_by_machine_key'
    description = base_description + '''
    **Parameters**:
    - `machine_key`: The machine_key from the bitflux servers for the machine to download stats for.

    NOTE: Use this tool with the machine_key if you have it.  Use download_stats_by_instance_id if you have the instance_id but not the machine_key.
    '''

    async def execute(machine_key: str, url: str, ctx: Context) -> Dict[str, Any]:
        """Download stats from bitflux daemon"""
        try:
            # Use the ec2_pricing module to fetch raw pricing entries
            stats = download_stats_by_machine_key(machine_key, url)
            return {
                'status': 'success',
                'machine_key': machine_key,
                'url': url,
                'stats': stats,
            }
        except Exception as e:
            # Log error in MCP context and return structured error
            await ctx.error(f'Failed to get stats from bitflux daemon for {machine_key} via {url}: {e}')
            return {
                'status': 'error',
                'message': str(e),
                'machine_key': machine_key,
                'url': url,
            }

class DownloadStatsByInstanceIdTool():
    name='download_stats_by_instance_id'
    description = '''
    Retrieve telemetry data from a machine when you have the AWS EC2 instance_id.

    **Parameters**:
    - `instance_id`: The AWS EC2 instance_id for the machine to download stats for.

    ''' + base_description

    async def execute(instance_id: str, url: str, ctx: Context) -> Dict[str, Any]:
        """Download stats from bitflux daemon"""
        try:
            # Use the ec2_pricing module to fetch raw pricing entries
            stats = download_stats_by_instance_id(instance_id, url)
            return {
                'status': 'success',
                'instance_id': instance_id,
                'url': url,
                'stats': stats,
            }
        except Exception as e:
            # Log error in MCP context and return structured error
            await ctx.error(f'Failed to get stats from bitflux daemon for {instance_id} via {url}: {e}')
            return {
                'status': 'error',
                'message': str(e),
                'instance_id': instance_id,
                'url': url,
            }
