import argparse
from ..bitflux_catcher_api import DefaultApi
from ..bitflux_catcher_api import Configuration
from ..bitflux_catcher_api import ApiClient
from ..bitflux_catcher_api import MachineLookupRequest
from ..bitflux_catcher_api import downloadstats_pb2
from ..ec2_tools import list_ec2_instances
from ..ec2_tools import get_aws_account_id
from google.protobuf import json_format
from typing import Any, Dict, List
import hashlib


def machine_lookup(instance_id: str, account_id: str, url: str) -> List[Dict[str, Any]]:
    """Lookup machine information by instance and/or account hashes."""
    # Initialize API client
    configuration = Configuration(host=url)
    with ApiClient(configuration) as api_client:
        api_instance = DefaultApi(api_client)
        instance_hash = hashlib.sha256(instance_id.encode()).hexdigest() if instance_id else ""
        account_hash = hashlib.sha256(account_id.encode()).hexdigest() if account_id else ""
        body = MachineLookupRequest(instance_hash=instance_hash, account_hash=account_hash)

        try:
            response = api_instance.machine_lookup(machine_lookup_request=body)
        except Exception as e:
            print(f"Error calling machine_lookup: {e}")
            return {}

        # Parse Protobuf response
        mlist_pb = downloadstats_pb2.MachineLookupList()
        mlist_pb.ParseFromString(response)
        # Convert to dict
        result = json_format.MessageToDict(mlist_pb)
        return result['machines']

def lookup_machines_by_region(region: str, url: str) -> Dict[str, Any]:
    instances = list_ec2_instances(region)
    account_id = get_aws_account_id()
    machines = machine_lookup("", account_id, url)
    indexed_machines = {}
    for machine in machines:
        indexed_machines[machine["instanceId"]] = machine
    output = {"Name": [], "InstanceType": [], "InstanceId": [], "machineKey": []}
    for i in range(len(instances["InstanceId"])):
        instance_id = instances["InstanceId"][i]
        hashed_instance_id = hashlib.sha256(instance_id.encode()).hexdigest()
        if not hashed_instance_id in indexed_machines:
            continue
        if instances["State"][i] != "running":
            continue
        output["Name"].append(instances["Name"][i])
        output["InstanceType"].append(instances["InstanceType"][i])
        output["InstanceId"].append(instances["InstanceId"][i])
        output["machineKey"].append(indexed_machines[hashed_instance_id]["machineKey"])
    return output

def manual() -> None:
    import json
    parser = argparse.ArgumentParser(description="Bitflux machine lookup CLI")
    parser.add_argument("--account_id", default="", help="Account ID (e.g., 1234567890)")
    parser.add_argument("--instance_id", default="", help="Instance ID (e.g., i-1234567890)")
    parser.add_argument("--region", default="", help="AWS region (e.g., us-east-1)")
    parser.add_argument("--url", default="https://catcher.bitflux.ai", help="API base URL")
    args = parser.parse_args()

    if args.region != "":
        machines = lookup_machines_by_region(args.region, args.url)
        print(json.dumps(machines, indent=4))
        return
    elif args.instance_id == "" and args.account_id == "":
        print("Please provide either instance_id or account_id")
        parser.print_help()
        return
    machines = machine_lookup(args.instance_id, args.account_id, args.url)
    print(json.dumps(machines, indent=4))

if __name__ == "__main__":
    manual()
