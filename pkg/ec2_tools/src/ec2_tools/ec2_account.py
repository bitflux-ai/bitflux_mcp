import boto3

def get_aws_account_id():
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    return account_id
