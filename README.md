# BitFlux MCP Server

This lets a user get data from BitFlux enabled EC2 instances to help determine what instance type is best for their workload.
It is intended to be run on your local workstation along side your AI tool such as Claude Desktop, Cursor, Windsurf, etc.  Communicates with the BitFlux cloud service and AWS APIs.


# Requirements
## AWS
The MCP server uses AWS APIs to get lists of the users EC2 instances and AWS instance pricing.  It needs to run in an environment with AWS credentials either set with environment variables or from ~/.aws see [boto3 docs](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html) for details.

## EC2 Instances
At this time the BitFlux solution requires AWS EC2 instances to take full advantage of the MCP server.  Support for other machine types is planned, contact us with requests.

To get usage data from an EC2 instance it must be running a Bitflux daemon.  There are two versions of the daemon.
### 1. bitfluxeval
* For installing on existing instances evaluation of existing workloads.
* Does not actively manage instances.  Monitors and reports only.
* Installation instructions:
```
curl --proto '=https' --tlsv1.2 -sSf https://apt.bitflux.ai/install_eval.sh | bash
```
### 2. bitfluxd
* Installed by default in BitFlux AMIs in the AWS Marketplace
* Actively manages instances.

# Installation
The MCP ecosystem is moving really fast.  I'm not confident I can really document this satisfactorily.  I'll add some examples here to help you get started.  The v0.1.0 is the release number, you can find the latest release number from the [releases page](https://github.com/bitflux-ai/bitflux_mcp/releases).

### Claude Desktop
Edit the claude_desktop_config.json which you can find from File->Settings->Developer->Edit Config to include the following:

```json
{
  "mcpServers": {
    "bitflux": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/bitflux-ai/bitflux_mcp.git@v0.1.0",
        "bitflux_mcp"
      ]
    }
  }
}
```
### Windsurf
Edit ~/.codeium/windsurg/mcp_config.json to include the following:
```json
{
  "mcpServers": {
    "bitflux_mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/bitflux-ai/bitflux_mcp.git@v0.1.0",
        "bitflux_mcp"
      ],
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```
### AMP
Edit ~/.config/amp/settings.json to include the following:
```json
{
  "amp.mcpServers": {
    "bitflux_mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/bitflux-ai/bitflux_mcp.git@v0.1.0",
        "bitflux_mcp"
      ],
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```
### Developing MCP Locally
If you want to run the MCP from the local repo without installing it, you can use the following configuration:
```json
{
  "mcpServers": {
    "bitflux_mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/home/user/repos/bitflux_mcp",
        "python",
        "-m",
        "main.py"
      ],
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

# Usage


# Testing
```
npx @modelcontextprotocol/inspector \
  uv \
  --directory $(pwd) \
  run \
  python \
  -m \
  main.py
```
# Privacy


### bitflux_instance_recommendation
This prompt has two arguments:
   * stats - The output of the download_stats_by_instance_id tool.
   * instance_types - The output of the get_ec2_pricing tool.

### bitflux://generic_ami_id
This resource returns the AMI ID of a generic AMI that can be used to create an EC2 instance.

### bitflux://bitflux_ami_id
This resource returns the AMI ID of a BitFlux AMI that can be used to create an EC2 instance.
