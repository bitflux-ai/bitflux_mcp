from mcp.server.fastmcp import Context
from typing import Any, Dict
from machine_lookup.tool import machine_lookup
from machine_lookup.tool import lookup_machines_by_region

class MachineLookupByInstanceIdTool():
    name = 'machine_key_by_instance_id'

    description = '''
    Lookup machines machine_key by AWS EC2 instance_id.

    This returns a machine_key string that can be used with download_stats.

    **Parameters**:
    - `instance_id`: The AWS instance ID.
    - `url`: The API base URL for the service.

    **Output**:
    - On success, returns a dictionary with:
      - `status`: 'success'
      - `instance_id`: The input instance ID
      - `url`: The API base URL
      - `machine_key`: The machine key
    - On error, returns a dictionary with:
      - `status`: 'error'
      - `message`: The error message
      - `instance_id`:, `url` for context
    '''

    async def execute(instance_id: str, url: str, ctx: Context) -> Dict[str, Any]:
        """Lookup machine information by instance IDs via API"""
        try:
            result = machine_lookup(instance_id, "", url)
            machines = []
            for machine in result.get('machines', []):
                machines.append(machine['machineKey'])
            if len(machines) == 0:
                raise Exception(f"No machine found for instance_id {instance_id}")
            return {
                'status': 'success',
                'instance_id': instance_id,
                'url': url,
                'machine_key': machines[0],
            }
        except Exception as e:
            await ctx.error(f'Failed to lookup machine for {instance_id} via {url}: {e}')
            return {
                'status': 'error',
                'message': str(e),
                'instance_id': instance_id,
                'url': url,
            }


class MachineLookupByAccountIdTool():
    name = 'machine_keys_by_account_id'

    description = '''
    Lookup list of machine_keys for machines by AWS EC2 account_id.

    This returns a list of machine_key strings that can be used with download_stats.

    **Parameters**:
    - `account_id`: The AWS account ID.
    - `url`: The API base URL for the service.

    **Output**:
    - On success, returns a dictionary with:
      - `status`: 'success'
      - `account_id`: The input account ID
      - `url`: The API base URL
      - `machine_keys`: A list of machine keys
    - On error, returns a dictionary with:
      - `status`: 'error'
      - `message`: The error message
      - `account_id`, `url` for context
    '''

    async def execute(account_id: str, url: str, ctx: Context) -> Dict[str, Any]:
        """Lookup machine information by account ID via API"""
        try:
            result = machine_lookup("", account_id, url)
            machines = []
            for machine in result.get('machines', []):
                machines.append(machine['machineKey'])
            return {
                'status': 'success',
                'account_id': account_id,
                'url': url,
                'machine_keys': machines,
            }
        except Exception as e:
            await ctx.error(f'Failed to lookup machines for {account_id} via {url}: {e}')
            return {
                'status': 'error',
                'message': str(e),
                'account_id': account_id,
                'url': url,
            }


class ListMachinesByRegionTool():
    name = 'list_machines_by_region'

    description = '''
    Lookup machines bitflux has in the database for EC2 region.

    Use this to find machines unless the user gives you an account ID or instance ID.
    This returns a list of machines in the database for the region with this format:
        {
            "Name": [
                "CatcherInstance1"
            ],
            "InstanceType": [
                "t3a.nano"
            ],
            "InstanceId": [
                "i-fffffffffaaaaaaa1"
            ],
            "machineKey": [
                "55555555-4444-3333-2222-111111111111"
            ]
        }
    **Parameters**:
    - `region`: The AWS region to search.
    - `url`: The API base URL for the service.

    **Output**:
    - On success, returns a dictionary with:
      - `status`: 'success'
      - `region`: The input region
      - `url`: The API base URL
      - `machine_list`: A list of machines data
    - On error, returns a dictionary with:
      - `status`: 'error'
      - `message`: The error message
      - `region`: The input region
      - `url`: The API base URL
    '''

    async def execute(region: str, url: str, ctx: Context) -> Dict[str, Any]:
        """Lookup machines by region via API"""
        try:
            result = lookup_machines_by_region(region, url)
            return {
                'status': 'success',
                'region': region,
                'url': url,
                'machine_list': result,
            }
        except Exception as e:
            await ctx.error(f'Failed to lookup machines for {region} via {url}: {e}')
            return {
                'status': 'error',
                'message': str(e),
                'region': region,
                'url': url,
            }