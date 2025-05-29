#!/usr/bin/env python3
"""
Module to list EC2 instances by instance ID in a given AWS region.
"""
import boto3
import json
from typing import Any, Dict, List, Optional


def list_ec2_instances(region_name: str) -> Dict[str, List[str]]:
    """
    Retrieve all EC2 instances owned by user in the specified AWS region.

    Args:
        region_name: AWS region code (e.g., 'us-east-1').

    Returns:
        A dictionary of instances information.
    """
    ec2 = boto3.client('ec2', region_name=region_name)
    paginator = ec2.get_paginator('describe_instances')
    instances: dict[str, str] = {"Name": [], "InstanceId": [], "InstanceType": [], "State": []}
    for page in paginator.paginate():
        for reservation in page.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instances["InstanceId"].append(instance.get('InstanceId'))
                instances["InstanceType"].append(instance.get('InstanceType'))
                instance_name = ""
                for tag in instance.get('Tags', [{}]):
                    if tag.get('Key') != 'Name':
                        continue
                    instance_name = tag.get('Value')
                    break
                instances["Name"].append(instance_name)
                instances["State"].append(instance.get('State', {}).get('Name', 'unknown'))
    return instances

def manual() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description='List EC2 instance IDs in a region.'
    )
    parser.add_argument(
        '--region',
        required=True,
        help='AWS region code (e.g., us-east-1)'
    )
    args = parser.parse_args()
    instances = list_ec2_instances(args.region)
    print(json.dumps(instances, indent=2, default=str))

if __name__ == '__main__':
    manual()
