#!/usr/bin/env python3
import boto3
import os
from mcp.server.fastmcp import Context

def get_generic_ami_id() -> str:
    """
    Get the latest Ubuntu Noble AMI ID for the current region.

    Returns:
        AMI ID string
    """
    ec2_client = boto3.client('ec2')

    response = ec2_client.describe_images(
        Owners=['099720109477'],  # Canonical's AWS account ID
        Filters=[
            {
                'Name': 'name',
                'Values': ['ubuntu/images/hvm-ssd-gp3/ubuntu-noble-*-amd64-server-*']
            }
        ]
    )

    # Sort images by creation date (newest first)
    images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)

    # Return the ImageId of the most recent AMI
    return images[0]['ImageId']


def get_bitflux_ami_id() -> str:
    """
    Get the latest Bitflux AMI ID for the current region.

    Returns:
        AMI ID string
    """
    ec2_client = boto3.client('ec2')

    response = ec2_client.describe_images(
        Filters=[
            {
                'Name': 'name',
                'Values': ['bitflux_aws*']
            },
            {
                'Name': 'owner-id',
                'Values': ['679593333241']
            },
            {
                'Name': 'product-code',
                'Values': ['7wppk9vopci3tbz5ttx1g1nr']
            },
            {
                'Name': 'is-public',
                'Values': ['true']
            }
        ]
    )

    # override for internal debugging
    if os.environ.get('PRIVATE_AMI_CATALOG', None) is not None:
        response = ec2_client.describe_images(
            Owners=['self'],
            Filters=[
                {
                    'Name': 'name',
                    'Values': ['bitflux_aws*']
                },{
                    'Name': 'is-public',
                    'Values': ['false']
                }
            ])

    # Sort images by creation date (newest first)
    images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)

    # Return the ImageId of the most recent AMI
    return images[0]['ImageId']

def manual():
    print(f"generic_ami_id: {get_generic_ami_id()}")
    print(f"bitflux_ami_id: {get_bitflux_ami_id()}")

class AmiIdTool:
    name = "get_ami_id"
    description = """
    Get the latest AMI ID of a generic or bitflux AMI that can be used to create an EC2 instance.
    Takes an argument:
        * target - The target type of AMI to return.  Can be 'generic' or 'bitflux'.
    """
    async def execute(target: str, ctx: Context) -> str:
        if target == "generic":
            return get_generic_ami_id()
        elif target == "bitflux":
            return get_bitflux_ami_id()
        else:
            raise ValueError("Invalid target. Must be 'generic' or 'bitflux'.")
