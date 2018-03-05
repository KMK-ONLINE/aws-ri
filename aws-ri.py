import boto3
from collections import Counter
from prettytable import PrettyTable

ec2 = boto3.client('ec2')
elc = boto3.client('elasticache')
rds = boto3.client('rds')

def print_table(instances, reserved_instances, title):
    title = "<h3 class=pt>Reserved Instances for {}</h3>".format(title)
    pt = PrettyTable(["Instance Type", "Running Now", "Reserved Instances", "Consider To Buy"])
    pt.border = True
    pt.header = True
    for i in calculate_consider_to_buy(instances, reserved_instances):
        pt.add_row(i)
    return title + pt.get_html_string(attributes={"name": "my_table", "class": "my_table"}) + '<br /><br />'


def sendmail(args):
    style = """
    <!doctype html>
    <html>
    <head>
    <style>
    .my_table {
        border: 0.5px solid #ddd;
        border-collapse: collapse;
    }

    .my_table th, td {
        border: 0.5px solid #ddd;
        padding: 8px;
    }

    .my_table tr:nth-child(even){background-color: #f2f2f2}

    .my_table th {
        background-color: #99CCFF;
    }
    .my_table tr:last-child {
        background-color: #FF66CC;
    }

    .my_table tr {
        text-align: left;
    }
    .my_table tr {
        text-align: left;
    }

    .pt h3 {
        text-align: left;
    }
    </style>
    </head>
    <body>
    """
    msg = style + args
    client = boto3.client('ses', region_name='us-east-1')

    client.send_email(
        Source='admin@yourdomain.com',
        Destination={
            'ToAddresses': ["admin@yourdomain.com"],
        },
        Message={
            'Subject': {
                'Data': 'AWS Reserved Instance Reports'
            },
            'Body': {
                'Html': {
                    'Data': msg + '</body></html>',
                },
            }
        },
    )


def ec2_instances():
    instances = ec2.describe_instances(
        Filters=
        [
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    ec2_list = []
    for i in instances['Reservations']:
        for j in i['Instances']:
            ec2_list.append(j['InstanceType'])

    return Counter(ec2_list)


def ec2_reserved_instances():
    res_instances = ec2.describe_reserved_instances(
        Filters=[
            {'Name': 'state', 'Values': ['active']}
        ]
    )
    reserved_list = {}
    for i in res_instances['ReservedInstances']:
        if reserved_list.get(i['InstanceType']):
            reserved_list[i['InstanceType']] += i['InstanceCount']
        else:
            reserved_list[i['InstanceType']] = i['InstanceCount']
    return reserved_list

def add_total(instances):
    sum1, sum2, sum3 = 0, 0, 0
    for i in instances:
        sum1 += i[1]
        sum2 += i[2]
        sum3 += i[3]
    return instances.append(['Total', sum1, sum2 , sum3])


def calculate_consider_to_buy(instances, reserved_instances):
    instance_types = []
    for i,j in instances.items():
        consider_value = None
        reserved_number = None
        for k, l in reserved_instances.items():
            if k != i:
                continue
            reserved_number = l
            consider_value = j - l
        if consider_value is not None and reserved_number is not None:
            instance_types.append([i, j, reserved_number, consider_value])
        else:
            instance_types.append([i, j, 0, j])

    add_total(instance_types)
    return instance_types


def elc_instances():
    elc_list = []
    instances = elc.describe_cache_clusters()
    for i in instances['CacheClusters']:
        elc_list.append(i['CacheNodeType'])
    return Counter(elc_list)


def elc_reserved_instances():
    elc_reserved_list = {}
    reserved_instances = elc.describe_reserved_cache_nodes()
    for i in reserved_instances['ReservedCacheNodes']:
        if 'active' not in i['State']:
            continue
        if elc_reserved_list.get(i['CacheNodeType']):
            elc_reserved_list[i['CacheNodeType']] += i['CacheNodeCount']
        else:
            elc_reserved_list[i['CacheNodeType']] = i['CacheNodeCount']
    return Counter(elc_reserved_list)


def rds_instances():
    instances = rds.describe_db_instances()
    rds_list = []
    for i in instances['DBInstances']:
        rds_list.append(i['DBInstanceClass'])
    return Counter(rds_list)


def rds_reserved_instances():
    reserved_instances = rds.describe_reserved_db_instances()
    rds_reserved_list = {}
    for i in reserved_instances['ReservedDBInstances']:
        if i['State'] != 'active':
            continue
        if rds_reserved_list.get(i['DBInstanceClass']):
            rds_reserved_list[i['DBInstanceClass']] += i['DBInstanceCount']
        else:
            rds_reserved_list[i['DBInstanceClass']] = i['DBInstanceCount']
    return rds_reserved_list


# main program
def main(event, context):
    pretty_table = print_table(ec2_instances(), ec2_reserved_instances(), 'EC2')
    pretty_table += print_table(elc_instances(), elc_reserved_instances(), 'Elasticache')
    pretty_table += print_table(rds_instances(), rds_reserved_instances(), 'RDS')
    sendmail(pretty_table)
