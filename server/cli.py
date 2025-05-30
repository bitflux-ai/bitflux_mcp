# Copyright 2025 Bitflux
# SPDX-License-Identifier: MIT

import argparse
from mcp.server.fastmcp import Context, FastMCP
from typing import Any, Dict, List, Optional
from server.tools.get_ec2_pricing import GetEC2PricingTool
from server.tools.list_ec2_instances import ListEC2InstancesTool
from server.tools.downloadstats import DownloadStatsByMachineKeyTool, DownloadStatsByInstanceIdTool
from server.tools.machine_lookup import MachineLookupByInstanceIdTool, MachineLookupByAccountIdTool, ListMachinesByRegionTool


def main():
    """Run the MCP server with CLI argument support."""
    parser = argparse.ArgumentParser(description='MCP server to analyze memory usage of EC2 instances with bitflux and suggest instance sizes')
    parser.add_argument('--full', action='store_true', help='Enable full toolset')
    parser.add_argument('--sse', action='store_true', help='Use SSE transport')
    parser.add_argument('--port', type=int, default=8888, help='Port to run the server on')
    parser.add_argument('--bitflux_url', type=str, default="https://catcher.bitflux.ai", help='Bitflux URL')

    args = parser.parse_args()

    mcp = FastMCP(name="bitflux",)

    @mcp.tool(name=GetEC2PricingTool.name, description=GetEC2PricingTool.description)
    async def get_ec2_pricing(region: str, instance_type: str, ctx: Context) -> Dict[str, Any]:
        return await GetEC2PricingTool.execute(region, instance_type, ctx)

    @mcp.tool(name=DownloadStatsByMachineKeyTool.name, description=DownloadStatsByMachineKeyTool.description)
    async def download_stats_by_machine_key(machine_key: str, ctx: Context) -> Dict[str, Any]:
        return await DownloadStatsByMachineKeyTool.execute(machine_key, args.bitflux_url, ctx)

    @mcp.tool(name=DownloadStatsByInstanceIdTool.name, description=DownloadStatsByInstanceIdTool.description)
    async def download_stats_by_instance_id(instance_id: str, ctx: Context) -> Dict[str, Any]:
        return await DownloadStatsByInstanceIdTool.execute(instance_id, args.bitflux_url, ctx)

    @mcp.tool(name=ListMachinesByRegionTool.name, description=ListMachinesByRegionTool.description)
    async def list_machines_by_region(region: str, ctx: Context) -> Dict[str, Any]:
        return await ListMachinesByRegionTool.execute(region, args.bitflux_url, ctx)

    if args.full:
        @mcp.tool(name=MachineLookupByInstanceIdTool.name, description=MachineLookupByInstanceIdTool.description)
        async def machine_lookup_by_instance_id(instance_id: str, ctx: Context) -> Dict[str, Any]:
            return await MachineLookupByInstanceIdTool.execute(instance_id, args.bitflux_url, ctx)

        @mcp.tool(name=MachineLookupByAccountIdTool.name, description=MachineLookupByAccountIdTool.description)
        async def machine_lookup_by_account_id(account_id: str, ctx: Context) -> Dict[str, Any]:
            return await MachineLookupByAccountIdTool.execute(account_id, args.bitflux_url, ctx)

        @mcp.tool(name=ListEC2InstancesTool.name, description=ListEC2InstancesTool.description)
        async def list_ec2_instances(region: str, ctx: Context) -> Dict[str, Any]:
            return await ListEC2InstancesTool.execute(region, ctx)

    # Run server with appropriate transport
    if args.sse:
        mcp.settings.port = args.port
        mcp.run(transport='sse')
    else:
        mcp.run()

def hello():
    print("Hello from mcp_server!")

if __name__ == '__main__':
    main()
