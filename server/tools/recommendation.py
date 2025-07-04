from mcp.server.fastmcp import Context


_inputs = """
    The 'stats' object must be the output from the bitflux_mcp tool download_stats_by_instance_id (or download_stats_by_machine_key in special situations) and should contain the following structure and content:
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

        // The instance type used to collect the stats
        "instance_type": "m6i.2xlarge",

        // Calculated Requirements
        "summary_requirements": {
          // The calculated amount of memory the workload used
          "used_memory": "500 MiB",
          // The calculated number of vCPUs the workload used
          "vcpu_usage": "1.7"
        },

        // A small sample of raw measurements at successive intervals
        "data": {
            // BitFlux calculated used memory
            "used": [16188846080, 16121737216, 16239177728],
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

    The 'ec2_instance_type_details' object must be the output of the bitflux_mcp tool get_ec2_pricing and follows the following format:
    {
        // The AWS EC2 instance type
        "instanceType": [
            "t3.micro",
            "t3.2xlarge"
        ],
        // The memory size for the instance type
        "memory": [
            "1 GiB",
            "32 GiB"
        ],
        // The number of vCPUs for the instance type
        "vcpu": [
            "2",
            "8"
        ],
        // The price per hour of the instance type in USD
        "pricePerHour": [
            "0.0104000000",
            "0.3328000000"
        ]
    }
    """

_core_prompt = """

    You are a BitFlux trained engineer tasked with recommending the minimum instance type for a workload being evaluated.  At BitFlux we are very opinionated about the calculations we use to determine these requirements because we have a custom OS image with unique memory handling requirements.
    Let me explain how our memory calculations and assumptions work in terms of fields from the 'stats' object.
    The 'used' memory is 'mem_total' - ('free' + 'reclaimable'). Assume the calculated 'used' is ~10 percent lower that the actual memory usage. What we find is that having free memory lets the system react faster than having it 'available' to be freed from a cache when the system demands it. Because we are measuring and predicting what cache is likely to be reused we don't see a downside to freeing caches that are held by default.
    Because BitFlux actively manages memory, we can safely assume memory above the calculated 'used' is unnecessary for the workload and can be freed up for expansion or not provisioned.
    If the system happens to be using swap, especially in a BitFlux managed system, the swap is not a sign a problem, so long as the 'used' memory is not too high.
    When recommending instance types, calculate 'used_memory' / 'memory' from the targeted instance type.  This should be 0.8 (80%) or less.  If 'used_memory' / 'memory' is more that 0.8 (80%) but less than 0.9 (90%), let the user know it might fit in the smaller instance but recommend the larger instance. If 'used_memory' > 'memory' for a targeted instance type, do not use this type.

    'instance_type' from the 'stats' object is the current instance type the workload data is tested on.
    The 'vcpu_usage' is calculated as the (1 - 'idle_cpu' percentage) * num_cpus.  If 'vcpu_usage' is 90 percent or higher than 'vcpu' for at target instance type then check if 'vcpu' < 'num_cpus' then recommend a larger instance type if not recommend the instance type anyway but warn the user the workload is CPU bound.

    The output should include a JSON object with the following fields:
    - 'instance_type': The recommended instance type.
    - 'savings': Savings are calculated as the cost of the recommended instance type vs the cost of the 'stats' 'instance_type' for a 30 day period. Express in dollars and percentage. If 'instance_type' is empty or missing, express the cost of the recommended instance type.
    - 'reason': A concise explanation of why the instance type was recommended and any comments or warnings.

    Optionally you can include charts and/or graphs of the memory and cpus over time. You can use the timestamp field as the time of the last sample, with the sample_rate being the time between samples.
    """


class BitfluxRecommendationPrompt():
    name= "bitflux_instance_recommendation"
    description = """
      Get a recommendation for which instance type is recommended based on two inputs:
        * the 'stats' object from 'download_stats_by_instance_id'
        * the 'ec2_instance_type_details' object from the tool 'get_ec2_pricing'
      """

    async def execute(stats: str, ec2_instance_type_details: str, ctx: Context) -> str:
      prompt = _inputs + _core_prompt + f"""
      'stats' object:
      {stats}

      'ec2_instance_type_details' object:
      {ec2_instance_type_details}
      """
      return prompt


class BitfluxRecommendationTool():
    name='bitflux_instance_recommendation_prompt'
    description = """
    Use this tool to recommend the best instance type for the given workload data and EC2 instance type details.
    """

    async def execute(ctx: Context) -> str:
        prompt = """
        Use the following data with the below prompt to recommend the best instance type for the given workload data and EC2 instance type details:
          * the 'stats' object from 'download_stats_by_instance_id'
          * the 'ec2_instance_type_details' object from the tool 'get_ec2_pricing'

        """ + _core_prompt
        return prompt