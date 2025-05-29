#!/usr/bin/env python3
import boto3
import json

# Map AWS region codes (e.g., 'us-east-1') to the pricing API location strings (e.g., 'US East (N. Virginia)').
def _get_location_for_region(region_code, pricing_region='us-east-1'):
    """
    Resolve AWS Pricing API location name for a given AWS region code.
    Uses the AWS Price List API to map the region code to the location string expected by the EC2 pricing service.
    """
    pricing_client = boto3.client('pricing', region_name=pricing_region)
    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=[{'Type': 'TERM_MATCH', 'Field': 'regionCode', 'Value': region_code}],
        MaxResults=1,
    )
    price_list = response.get('PriceList', [])
    if not price_list:
        raise ValueError(f"No pricing products found for region code {region_code}")
    pi = json.loads(price_list[0])
    attributes = pi.get('product', {}).get('attributes', {})
    location = attributes.get('location')
    if not location:
        raise ValueError(f"Unable to resolve location for region code {region_code}")
    return location


def get_page_iterator(region_name, instance_type, location):
    """
    Return a paginator for EC2 pricing products, optionally filtered by instance_type and location.
    region_name: AWS region for the pricing API endpoint (e.g., 'us-east-1').
    instance_type: EC2 instance type to filter (e.g., 't3.micro').
    location: AWS region location string in the pricing API (e.g., 'US East (N. Virginia)').
    """
    pricing_client = boto3.client('pricing', region_name=region_name)
    # Determine if instance_type contains wildcard; AWS API TERM_MATCH doesn't support wildcards,
    # so skip the instanceType filter if a wildcard is used.
    wildcard = '*' in instance_type
    filters = []
    if not wildcard:
        filters.append({'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type})
    # Required filters for location, OS, tenancy, etc.
    filters += [
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
        {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
        {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
        {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
        {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},
    ]
    paginator = pricing_client.get_paginator('get_products')
    page_iterator = paginator.paginate(
        ServiceCode='AmazonEC2',
        Filters=filters,
        PaginationConfig={
            'PageSize': 100,
            'MaxItems': None
        }
    )
    return page_iterator

def add_to_output(output, k, v, kchain=[]):
    if k in output:
        if output[k] != v:
            raise BaseException(f"Warning: duplicate key {k} has different values: {output[k]} and {v} at {kchain}")
    else:
        output[k] = v

def flatten_dict(output, d, kchain=[]):
    for k,v in d.items():
        if isinstance(v, dict):
            flatten_dict(output, v, kchain=kchain+[k])
        elif isinstance(v, str):
            add_to_output(output, k, v, kchain=kchain+[k])
        elif isinstance(v, list):
            if len(v) != 0:
                raise BaseException(f"Unexpected list {k} in {kchain}")
        else:
            raise BaseException(f"Unexpected type {type(v)} for {k} in {kchain}")

def process_dimensions(outputs, boutput, d, kchain=[]):
    #print(f"process_dimensions {kchain}")
    output = json.loads(json.dumps(boutput))
    for k,v in d.items():
        if isinstance(v, dict): continue
        elif isinstance(v, str):
            add_to_output(output, k, v, kchain=kchain+[k])
        elif isinstance(v, list):
            if len(v) != 0:
                raise BaseException(f"Unexpected list {k} in {kchain}")
        else:
            raise BaseException(f"Unexpected type {type(v)} for {k} in {kchain}")
    for k,v in d.items():
        if not isinstance(v, dict): continue
        if k == 'pricePerUnit': continue
        flatten_dict(output, v, kchain=kchain+[k])
    for k,v in d.items():
        if not isinstance(v, dict): continue
        if k != 'pricePerUnit': continue
        for k1,v1 in v.items():
            add_to_output(output, k, v1, kchain=kchain+[k,k1])
            add_to_output(output, 'priceUnit', k1, kchain=kchain+[k,k1])
    # print(f"kchain: {kchain}")
    # print(f"Adding {json.dumps(output, indent=2)}")
    outputs.append(output)


def process_terms(outputs, boutput, d, kchain=[]):
    # print(f"process_terms {kchain}")
    # print(f"input {json.dumps(boutput, indent=2)}")
    output = json.loads(json.dumps(boutput))
    for k,v in d.items():
        if isinstance(v, dict): continue
        elif isinstance(v, str):
            add_to_output(output, k, v, kchain=kchain+[k])
        elif isinstance(v, list):
            if len(v) != 0:
                raise BaseException(f"Unexpected list {k} in {kchain}")
        else:
            raise BaseException(f"Unexpected type {type(v)} for {k} in {kchain}")
    for k,v in d.items():
        if not isinstance(v, dict): continue
        if k == 'priceDimensions': continue
        #if 'priceDimensions' in kchain+[k]: continue
        flatten_dict(output, v, kchain=kchain+[k])
    for k,v in d.items():
        if not isinstance(v, dict): continue
        if k != 'priceDimensions': continue
        #if len(v) == 0: continue # empty dicts can add an extra row
        for k1,v1 in v.items():
            process_dimensions(outputs, output, v1, kchain=kchain+[k,k1])

def get_prices_per_price_item(pi):
    outputs = []
    # make a baseoutput template with all the relevant keys
    baseoutput = {}
    for k,v in pi.items():
        # terms will make multiple rows, so first we collect the baseoutput values
        if k == 'terms': continue
        elif isinstance(v, dict): continue
        elif isinstance(v, str):
            add_to_output(baseoutput, k, v, kchain=[k])
        else:
            raise BaseException(f"Unexpected type {type(v)} for {k}")
    # doing dicts second as a pattern, it doesn't matter here.
    for k,v in pi.items():
        if k == 'terms': continue
        elif isinstance(v, dict):
            # only works for some cases, where the structure works
            flatten_dict(baseoutput, v, kchain=[k])
    # now we have the baseoutput, so we can iterate over the terms, clone the baseoutput for each term, and add the term to the output
    for k,v in pi['terms'].items():
        if not k in ['OnDemand', 'Reserved']:
            raise BaseException(f"Unexpected key {k}")
        baseoutput2 = baseoutput.copy()
        baseoutput2['term_type'] = k
        for k1,v1 in v.items():
            process_terms(outputs, baseoutput2, v1, kchain=['terms', k , k1])
    return outputs

def get_prices_per_page(page):
    prices = []
    for price_item in page['PriceList']:
        pi = json.loads(price_item)
        o = get_prices_per_price_item(pi)
        # print("1"*80)
        # print(o)
        prices += o
    return prices

def get_ec2_prices_full(region_name, instance_type):
    """
    Retrieve EC2 pricing entries.
    region_name: AWS region code (e.g., 'us-east-1').
    instance_type: EC2 instance type to filter (e.g., 't3.micro').
    """
    # Resolve the AWS Pricing API location string for the given region
    location = _get_location_for_region(region_name)
    page_iterator = get_page_iterator(region_name, instance_type, location)
    prices = []
    for page in page_iterator:
        prices += get_prices_per_page(page)
    return prices

def get_ec2_prices_filtered(region_name, instance_type):
    """
    Retrieve EC2 pricing entries filter for hourly usage and limiting the
    fields returned to the ones we need.
    region_name: AWS region code (e.g., 'us-east-1').
    instance_type: EC2 instance type to filter (e.g., 't3.micro').
    """
    # Resolve the AWS Pricing API location string for the given region
    fullprices = get_ec2_prices_full(region_name, instance_type)
    prices = []
    for p in fullprices:
        if p['unit'] != 'Hrs':
            continue
        elif p['term_type'] != 'OnDemand':
            continue
        prices.append(p)
    return prices
 
def get_ec2_prices(region_name, instance_type):
    """
    Retrieve EC2 pricing entries, supporting wildcard instance types.
    region_name: AWS region code (e.g., 'us-east-1').
    instance_type: EC2 instance type or pattern suffix wildcard (e.g., 't3.micro', 't3.*', or '*').
    """
    # Get on-demand hourly prices
    results = get_ec2_prices_filtered(region_name, instance_type)
    # If wildcard present, filter by prefix before '*' character
    if '*' in instance_type:
        prefix = instance_type.split('*', 1)[0]
        # If prefix is empty (pattern '*' alone), return all results
        if not prefix:
            return results
        # Otherwise filter entries whose instanceType starts with the prefix
        return [p for p in results if p.get('instanceType', '').startswith(prefix)]
    # No wildcard: exact match enforcement
    return [p for p in results if p.get('instanceType') == instance_type]


# if run as a script, print the results and write a file
if __name__ == '__main__':
    import polars as pl

    prices = get_ec2_prices('us-east-1', 't3.*')

    #print(prices)
    for p in prices:
        print(f"{p['instanceType']}: {p['pricePerUnit']}")
        #print(p)
    df = pl.DataFrame(prices)
    print(df)
    print(df.columns)

    df = df.with_columns(pl.col("instanceType").str.split(".").list.first().alias("instanceClass"))

    # save to parquet
    df.write_parquet('prices.parquet')

    print(len(get_ec2_prices('us-east-1', '*')))
    print(len(get_ec2_prices('us-east-1', 't3.*')))
    print(len(get_ec2_prices('us-east-1', 't3.micro')))
