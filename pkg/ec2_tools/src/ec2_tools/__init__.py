from ec2_tools.ec2_instances import list_ec2_instances
from ec2_tools.ec2_account import get_aws_account_id
from ec2_tools.ec2_pricing import get_ec2_prices
# for sanity checking the import structure
def hello() -> None:
    print("hello from ec2tools")