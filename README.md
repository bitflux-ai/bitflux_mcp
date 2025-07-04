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


{
  "mcpServers": {
    "bitflux_mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/home/jared/repos/bitflux-ai/bitflux2_mr/apps/mcp/bitflux_mcp",
        "python",
        "-m",
        "main.py"
      ],
      "disabled": false,
      "alwaysAllow": []
    }
  }
}

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



{
  "status": "success",
  "region": "us-east-1",
  "instance_type": "t3a.*",
  "prices": {
    "instanceType": [
      "t3a.nano",
      "t3a.small",
      "t3a.medium",
      "t3a.xlarge",
      "t3a.micro",
      "t3a.large",
      "t3a.2xlarge"
    ],
    "memory": [
      "0.5 GiB",
      "2 GiB",
      "4 GiB",
      "16 GiB",
      "1 GiB",
      "8 GiB",
      "32 GiB"
    ],
    "vcpu": [
      "2",
      "2",
      "2",
      "4",
      "2",
      "2",
      "8"
    ],
    "pricePerHour": [
      "0.0047000000",
      "0.0188000000",
      "0.0376000000",
      "0.1504000000",
      "0.0094000000",
      "0.0752000000",
      "0.3008000000"
    ]
  }
}



f1637f36-bbc1-4b80-af12-8b86b43f0c5f



{
  "status": "success",
  "machine_key": "f1637f36-bbc1-4b80-af12-8b86b43f0c5f",
  "url": "https://catcher.bitflux.ai",
  "stats": {
    "timestamp": "2025-06-06T23:27:29.812+00:00",
    "sample_rate": "120",
    "mem_total": "33565847552",
    "swap_total": "157286395904",
    "num_cpus": "16",
    "instance_type": "",
    "data": {
      "free": [
        4542431232,
        4706009088,
        4538236928,
        5645533184,
        5205131264,
        5356126208,
        6174015488,
        5041553408,
        2596274176,
        2579496960,
        2529165312,
        2097152000,
        2541748224,
        1514143744,
        18438160384,
        18505269248,
        18383634432,
        18769510400,
        18966642688,
        17087594496,
        16018046976,
        17246978048,
        17561550848,
        17498636288,
        16634609664
      ],
      "cached": [
        1468006400,
        1455423488,
        1346371584,
        1291845632,
        1606418432,
        1484783616,
        1388314624,
        1568669696,
        1778384896,
        1870659584,
        1619001344,
        1778384896,
        1480589312,
        1396703232,
        2575302656,
        2055208960,
        1941962752,
        1652555776,
        1778384896,
        1694498816,
        2017460224,
        1619001344,
        1602224128,
        1602224128,
        1560281088
      ],
      "swap_used": [
        44451233792,
        44656754688,
        44656754688,
        44941967360,
        44803555328,
        44551897088,
        44757417984,
        42513465344,
        42316333056,
        42144366592,
        42245029888,
        42345693184,
        42471522304,
        40865103872,
        13878951936,
        13967032320,
        14000586752,
        14285799424,
        15338569728,
        15397289984,
        15158214656,
        15535702016,
        16051601408,
        17284726784,
        18077450240
      ],
      "swap_cached": [
        17431527424,
        17507024896,
        17314086912,
        16919822336,
        16831741952,
        16760438784,
        16500391936,
        16848519168,
        17741905920,
        18077450240,
        18064867328,
        18182307840,
        18119393280,
        19700645888,
        3846176768,
        3846176768,
        3531603968,
        3233808384,
        4001366016,
        5280628736,
        5402263552,
        4764729344,
        4928307200,
        5888802816,
        6337593344
      ],
      "reclaimable": [
        2109734912,
        956301312,
        826277888,
        1665138688,
        1111490560,
        1207959552,
        1145044992,
        553648128,
        767557632,
        859832320,
        859832320,
        2654994432,
        2403336192,
        1619001344,
        532676608,
        1325400064,
        671088640,
        1329594368,
        2285895680,
        708837376,
        314572800,
        1862270976,
        1044381696,
        2239758336,
        1405091840
      ],
      "idle_cpu": [
        65,
        65,
        67,
        66,
        64,
        64,
        65,
        62,
        64,
        66,
        67,
        64,
        68,
        57,
        55,
        75,
        77,
        76,
        77,
        79,
        79,
        78,
        78,
        76,
        77
      ],
      "used": [
        26913681408,
        27903537152,
        28201332736,
        26255175680,
        27249225728,
        27001761792,
        26246787072,
        27970646016,
        30202015744,
        30126518272,
        30176849920,
        28813701120,
        28620763136,
        30432702464,
        14595010560,
        13735178240,
        14511124480,
        13466742784,
        12313309184,
        15769415680,
        17233227776,
        14456598528,
        14959915008,
        13827452928,
        15526146048
      ]
    },
    "summary": {
      "free": {
        "count": 696,
        "null_count": 0,
        "mean": 6678151544.643678,
        "std": 2318089598.9950314,
        "min": 788529152,
        "90%": 8795455488,
        "95%": 9240051712,
        "99%": 17246978048,
        "max": 18966642688,
        "median": 6719275008,
        "sum": 4647993475072
      },
      "cached": {
        "count": 696,
        "null_count": 0,
        "mean": 794989344.3678161,
        "std": 392239615.07260376,
        "min": 440401920,
        "90%": 1459617792,
        "95%": 1602224128,
        "99%": 1941962752,
        "max": 2575302656,
        "median": 612368384,
        "sum": 553312583680
      },
      "swap_used": {
        "count": 696,
        "null_count": 0,
        "mean": 42708807821.24138,
        "std": 3764981440.947436,
        "min": 13878951936,
        "90%": 44736446464,
        "95%": 44883247104,
        "99%": 45126516736,
        "max": 45474643968,
        "median": 43461378048,
        "sum": 29725330243584
      },
      "swap_cached": {
        "count": 696,
        "null_count": 0,
        "mean": 16294292515.310345,
        "std": 1826745429.1986234,
        "min": 3233808384,
        "90%": 17888706560,
        "95%": 18383634432,
        "99%": 19297992704,
        "max": 19700645888,
        "median": 16395534336,
        "sum": 11340827590656
      },
      "reclaimable": {
        "count": 696,
        "null_count": 0,
        "mean": 1148733086.8965516,
        "std": 660083363.9267163,
        "min": 0,
        "90%": 2101346304,
        "95%": 2399141888,
        "99%": 2961178624,
        "max": 3519021056,
        "median": 1038090240,
        "sum": 799518228480
      },
      "idle_cpu": {
        "count": 696,
        "null_count": 0,
        "mean": 83.82902298850574,
        "std": 8.440963303445775,
        "min": 18,
        "90%": 91,
        "95%": 91,
        "99%": 91,
        "max": 92,
        "median": 86
      },
      "used": {
        "count": 696,
        "null_count": 0,
        "mean": 25738962920.45977,
        "std": 2315159476.6989856,
        "min": 12313309184,
        "90%": 28272635904,
        "95%": 29216354304,
        "99%": 30629834752,
        "max": 31959429120,
        "median": 25695236096,
        "sum": 17914318192640
      }
    },
    "summary_requirements": {
      "used_memory": "24 GiB",
      "vcpu_usage": 1.44
    }
  }
}