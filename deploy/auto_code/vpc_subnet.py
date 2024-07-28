import boto3

ec2 = boto3.client('ec2')

def create_vpc_subnet(vpc_name, subnet_name):
    vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
    vpc_id = vpc['Vpc']['VpcId']
    ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': vpc_name}])
    
    subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock='10.0.1.0/24')
    subnet_id = subnet['Subnet']['SubnetId']
    ec2.create_tags(Resources=[subnet_id], Tags=[{'Key': 'Name', 'Value': subnet_name}])
    
    return vpc_id, subnet_id
