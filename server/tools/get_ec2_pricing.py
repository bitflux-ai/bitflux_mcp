from mcp.server.fastmcp import Context
from typing import Any, Dict
from ..ec2_tools.ec2_pricing import get_ec2_prices_simple


class GetEC2PricingTool():
    name='get_ec2_pricing'

    description='''
    Retrieve pricing and basic parameters for an Amazon EC2 instance type in a specified AWS region.
    
    This tool fetches on-demand, hourly pricing for Linux-based EC2 instances with shared tenancy and no pre-installed software. It is designed to help users analyze costs for specific instance types or explore pricing across multiple instance types using wildcard patterns.

    **Parameters**:
    - `region`: The AWS region code (e.g., 'us-east-1', 'eu-west-1'). This determines the region for which pricing is retrieved. Ensure the region code is valid to avoid errors.
    - `instance_type`: The EC2 instance type (e.g., 't3.micro') or a wildcard pattern (e.g., 't3.*' or '*'). 
      - Use an exact instance type (e.g., 't3.micro') to retrieve pricing for that specific type.
      - Use a wildcard pattern like 't3.*' to fetch pricing for all instance types in the 't3' family (e.g., 't3.micro', 't3.small', etc.).
      - Use '*' to retrieve pricing for all available instance types in the specified region (note: this may return a large number of results, e.g., ~875 instance types in 'us-east-1').

    **When to Use**:
    - **Cost Analysis**: Use to compare pricing for specific instance types (e.g., 't3.micro' vs. 't3.small') when planning AWS deployments.
    - **Instance Family Exploration**: Use wildcard patterns (e.g., 'c5.*') to explore pricing across an instance family, ideal for selecting cost-effective options within a category (e.g., compute-optimized instances).
    - **Broad Cost Surveys**: Use '*' to retrieve all instance type prices in a region for comprehensive cost modeling or budgeting.
    - **Automation**: Integrate into workflows to dynamically fetch pricing for infrastructure provisioning or cost optimization scripts.

    **Examples**:
    - To get pricing for a specific instance: `get_ec2_pricing('us-east-1', 't3.micro')` returns pricing details for 't3.micro' in 'us-east-1'.
    - To explore a family: `get_ec2_pricing('us-east-1', 't3.*')` returns pricing for all 't3' instance types (e.g., 't3.micro', 't3.small', etc.).
    - To get all prices: `get_ec2_pricing('us-east-1', '*')` retrieves pricing for every available instance type in 'us-east-1'.

    **Output**:
    - On success, returns a dictionary with:
      - `status`: 'success'
      - `region`: The input region code
      - `instance_type`: The input instance type or pattern
      - `prices`: A list of pricing entries, each containing details like 'instanceType', 'pricePerUnit', 'priceUnit', etc.
    - On error, returns a dictionary with:
      - `status`: 'error'
      - `message`: The error message
      - `region`: The input region code
      - `instance_type`: The input instance type or pattern

    **Notes**:
    - Wildcard queries (e.g., 't3.*' or '*') may return multiple pricing entries, so ensure your application can handle lists of results.
    - Pricing is region-specific and reflects on-demand, hourly rates for Linux instances. Other operating systems or pricing models (e.g., Reserved Instances) are not supported.
    - Invalid region codes or instance types will result in an error response with a descriptive message.
    - The tool uses the AWS Pricing API, which may have rate limits or require appropriate IAM permissions.
    '''

    async def execute(region: str, instance_type: str, ctx: Context) -> Dict[str, Any]:
        """Retrieve pricing information and parameters for the specified EC2 instance type and region."""
        try:
            # Use the ec2_pricing module to fetch raw pricing entries
            prices = get_ec2_prices_simple(region, instance_type)
            return {
                'status': 'success',
                'region': region,
                'instance_type': instance_type,
                'prices': prices,
            }
        except Exception as e:
            # Log error in MCP context and return structured error
            await ctx.error(f'Failed to get EC2 pricing for {instance_type} in {region}: {e}')
            return {
                'status': 'error',
                'message': str(e),
                'region': region,
                'instance_type': instance_type,
            }
