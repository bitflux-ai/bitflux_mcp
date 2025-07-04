import hashlib
import argparse


parser = argparse.ArgumentParser(description='Hash an instance ID using SHA256')
parser.add_argument('instance_id', help='Instance ID to hash')
args = parser.parse_args()
print(hashlib.sha256(args.instance_id.encode()).hexdigest())
