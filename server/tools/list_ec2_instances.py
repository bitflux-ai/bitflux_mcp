from mcp.server.fastmcp import Context
from typing import Any, Dict
from ..ec2_tools.ec2_instances import list_ec2_instances


class ListEC2InstancesTool():
  name='list_ec2_instances'

  description='''
    Retrieve a list of your Amazon EC2 instances in a specified AWS region.
      
    This tool fetches information about EC2 instances owned by the user in the specified AWS region, including instance IDs, instance types, names (if available), and their current state. It is designed to help users quickly identify and manage their EC2 resources.

    **Parameters**:
    - `region`: The AWS region code (e.g., 'us-east-1', 'eu-west-1'). This determines the region from which instance information is retrieved. Ensure the region code is valid to avoid errors.

    **When to Use**:
    - **Resource Inventory**: Use to get a complete list of EC2 instances in a specific region.
    - **Instance Management**: Identify running instances for management tasks like stopping, starting, or terminating.
    - **Resource Auditing**: Verify which instances exist in a particular region for compliance or cost management.
    - **Automation**: Integrate into workflows that need to operate on existing EC2 instances.

    **Examples**:
    - To list all EC2 instances in US East: `list_ec2_instances('us-east-1')` returns instance details for all instances in 'us-east-1'.
    - To check instances in Europe: `list_ec2_instances('eu-west-1')` returns instance details for all instances in 'eu-west-1'.

    **Output**:
    - On success, returns a dictionary with:
      - `status`: 'success'
      - `region`: The input region code
      - `instances`: A dictionary containing information about EC2 instances with the following keys:
         - `InstanceId`: A list of EC2 instance IDs (e.g., "i-1234567890abcdef0")
         - `InstanceType`: A list of EC2 instance types (e.g., "t2.micro", "m5.large")
         - `Name`: A list of instance names derived from the "Name" tag (empty string if no Name tag exists)
         - `State`: A list of instance states (e.g., "running", "stopped", "terminated")
         Note: The lists are parallel, meaning the information at index i in each list corresponds to the same EC2 instance.
    - On error, returns a dictionary with:
      - `status`: 'error'
      - `message`: The error message
      - `region`: The input region code

    **Notes**:
    - This tool requires appropriate AWS IAM permissions to describe EC2 instances.
    - The response includes all instances regardless of their state (running, stopped, etc.).
    - For regions with many instances, the response may be large.
    '''

  async def execute(region: str, ctx: Context) -> Dict[str, Any]:
      """Retrieve a list of your EC2 instances for a given region."""
      try:
          # Use the ec2_pricing module to fetch raw pricing entries
          instances = list_ec2_instances(region)
          return {
              'status': 'success',
              'region': region,
              'instances': instances,
          }
      except Exception as e:
          # Log error in MCP context and return structured error
          await ctx.error(f'Failed to get EC2 list of instances in {region}: {e}')
          return {
              'status': 'error',
              'message': str(e),
              'region': region,
          }
