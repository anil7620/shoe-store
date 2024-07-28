import boto3
import os

import time

# Initialize boto3 clients
ec2 = boto3.client('ec2')
ecr = boto3.client('ecr')
ecs = boto3.client('ecs')
elb = boto3.client('elbv2')
wafv2 = boto3.client('wafv2')

# Prompt user for inputs
aws_access_key = input("Enter your AWS Access Key: ")
aws_secret_key = input("Enter your AWS Secret Key: ")

vpc_name = input("Enter VPC name: ")
subnet_name = input("Enter Subnet name: ")
key_pair_name = input("Enter EC2 Key Pair name: ")
ec2_instance_name = input("Enter EC2 Instance name: ")
mongo_user = input("Enter MongoDB root username: ")
mongo_pass = input("Enter MongoDB root password: ")

# Function to create a VPC and subnet
def create_vpc_subnet():
    vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
    vpc_id = vpc['Vpc']['VpcId']
    ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': vpc_name}])
    
    subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock='10.0.1.0/24')
    subnet_id = subnet['Subnet']['SubnetId']
    ec2.create_tags(Resources=[subnet_id], Tags=[{'Key': 'Name', 'Value': subnet_name}])
    
    return vpc_id, subnet_id

# Function to create an EC2 instance and install MongoDB
def create_ec2_instance(subnet_id, key_pair_name):
    ec2.create_key_pair(KeyName=key_pair_name)
    
    sg = ec2.create_security_group(GroupName=f"{ec2_instance_name}-sg", Description=f"SG for {ec2_instance_name}", VpcId=subnet_id)
    sg_id = sg['GroupId']
    ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[
        {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'tcp', 'FromPort': 27017, 'ToPort': 27017, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
    ])
    
    instance = ec2.run_instances(
        ImageId='ami-0abcdef1234567890',  # Replace with a valid AMI ID
        InstanceType='t2.micro',
        KeyName=key_pair_name,
        SecurityGroupIds=[sg_id],
        SubnetId=subnet_id,
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': ec2_instance_name}]}]
    )
    
    instance_id = instance['Instances'][0]['InstanceId']
    
    ec2.get_waiter('instance_running').wait(InstanceIds=[instance_id])
    
    instance_description = ec2.describe_instances(InstanceIds=[instance_id])
    public_ip = instance_description['Reservations'][0]['Instances'][0]['PublicIpAddress']
    
    return instance_id, public_ip

# Function to install MongoDB on EC2 instance
def install_mongodb(public_ip, key_pair_name, mongo_user, mongo_pass):
    commands = f"""
    #!/bin/bash
    sudo yum update -y
    sudo yum install -y mongodb-org
    sudo systemctl start mongod
    sudo systemctl enable mongod
    mongo <<EOF
    use admin
    db.createUser({{user: '{mongo_user}', pwd: '{mongo_pass}', roles:[{{role:'root',db:'admin'}}]}})
    EOF
    """
    
    with open('setup_mongo.sh', 'w') as file:
        file.write(commands)
    
    ec2_instance_script = f"scp -i {key_pair_name}.pem setup_mongo.sh ec2-user@{public_ip}:/home/ec2-user/"
    os.system(ec2_instance_script)
    
    ec2_instance_script = f"ssh -i {key_pair_name}.pem ec2-user@{public_ip} 'chmod +x /home/ec2-user/setup_mongo.sh && /home/ec2-user/setup_mongo.sh'"
    os.system(ec2_instance_script)

# Function to create an ECR repository
def create_ecr_repository():
    repo = ecr.create_repository(repositoryName=ecr_repo_name)
    ecr_uri = repo['repository']['repositoryUri']
    return ecr_uri

# Function to create ECS cluster, task definition, and service
def create_ecs_resources(subnet_id, sg_id, ecr_uri):
    ecs.create_cluster(clusterName=ecs_cluster_name)
    
    task_definition = {
        'family': ecs_task_definition_name,
        'networkMode': 'awsvpc',
        'containerDefinitions': [
            {
                'name': f"{ecs_task_definition_name}-container",
                'image': docker_image_uri,
                'memory': 512,
                'cpu': 256,
                'essential': True,
                'portMappings': [{'containerPort': 5000, 'hostPort': 5000}]
            }
        ],
        'requiresCompatibilities': ['FARGATE'],
        'cpu': '256',
        'memory': '512'
    }
    ecs.register_task_definition(**task_definition)
    
    service_definition = {
        'serviceName': ecs_service_name,
        'taskDefinition': ecs_task_definition_name,
        'desiredCount': 1,
        'launchType': 'FARGATE',
        'networkConfiguration': {
            'awsvpcConfiguration': {
                'subnets': [subnet_id],
                'securityGroups': [sg_id],
                'assignPublicIp': 'ENABLED'
            }
        }
    }
    ecs.create_service(cluster=ecs_cluster_name, **service_definition)

# Function to create a Load Balancer
def create_load_balancer(subnet_id, sg_id):
    lb = elb.create_load_balancer(
        Name=lb_name,
        Subnets=[subnet_id],
        SecurityGroups=[sg_id]
    )
    lb_arn = lb['LoadBalancers'][0]['LoadBalancerArn']
    
    tg = elb.create_target_group(
        Name=f"{lb_name}-tg",
        Protocol='HTTP',
        Port=5000,
        VpcId=vpc_id,
        TargetType='ip'
    )
    tg_arn = tg['TargetGroups'][0]['TargetGroupArn']
    
    elb.register_targets(TargetGroupArn=tg_arn, Targets=[{'Id': instance_id}])
    elb.create_listener(
        LoadBalancerArn=lb_arn,
        Protocol='HTTP',
        Port=80,
        DefaultActions=[{'Type': 'forward', 'TargetGroupArn': tg_arn}]
    )
    
    lb_description = elb.describe_load_balancers(LoadBalancerArns=[lb_arn])
    lb_dns = lb_description['LoadBalancers'][0]['DNSName']
    return lb_dns

# Function to configure WAF
def configure_waf(lb_arn):
    setup_waf = input("Do you want to set up WAF? (yes/no): ")
    if setup_waf.lower() == 'yes':
        print("WAF Options:")
        print("1. Rate limiting")
        print("2. Geo restriction")
        waf_option = input("Select an option (1 or 2): ")
        
        waf_acl = wafv2.create_web_acl(
            Name=f"{lb_name}-acl",
            Scope='REGIONAL',
            DefaultAction={'Allow': {}},
            VisibilityConfig={'SampledRequestsEnabled': True, 'CloudWatchMetricsEnabled': True, 'MetricName': 'WebACL'}
        )
        waf_arn = waf_acl['Summary']['ARN']
        
        if waf_option == '1':
            rate_limit = int(input("Enter rate limit (requests per 5 minutes): "))
            rate_based_rule = {
                'Name': 'RateBasedRule',
                'Priority': 1,
                'Action': {'Block': {}},
                'Statement': {'RateBasedStatement': {'Limit': rate_limit, 'AggregateKeyType': 'IP'}},
                'VisibilityConfig': {'SampledRequestsEnabled': True, 'CloudWatchMetricsEnabled': True, 'MetricName': 'RateBasedRule'}
            }
            wafv2.update_web_acl(
                Scope='REGIONAL',
                Id=waf_arn,
                LockToken=wafv2.get_web_acl(Scope='REGIONAL', Name=f"{lb_name}-acl")['LockToken'],
                DefaultAction={'Allow': {}},
                Rules=[rate_based_rule]
            )
        elif waf_option == '2':
            country_codes = input("Enter country codes (comma-separated, e.g., US,CA): ").split(',')
            geo_match_statement = {'GeoMatchStatement': {'CountryCodes': country_codes}}
            geo_based_rule = {
                'Name': 'GeoBasedRule',
                'Priority': 1,
                'Action': {'Block': {}},
                'Statement': geo_match_statement,
                'VisibilityConfig': {'SampledRequestsEnabled': True, 'CloudWatchMetricsEnabled': True, 'MetricName': 'GeoBasedRule'}
            }
            wafv2.update_web_acl(
                Scope='REGIONAL',
                Id=waf_arn,
                LockToken=wafv2.get_web_acl(Scope='REGIONAL', Name=f"{lb_name}-acl")['LockToken'],
                DefaultAction={'Allow': {}},
                Rules=[geo_based_rule]
            )
        wafv2.associate_web_acl(WebACLArn=waf_arn, ResourceArn=lb_arn)
        print("WAF setup complete.")

# Main execution flow
vpc_id, subnet_id = create_vpc_subnet()
instance_id, public_ip = create_ec2_instance(subnet_id, key_pair_name)
install_mongodb(public_ip, key_pair_name, mongo_user, mongo_pass)

ecr_repo_name = input("Enter ECR Repository name: ")
ecr_uri = create_ecr_repository()

ecs_cluster_name = input("Enter ECS Cluster name: ")
ecs_task_definition_name = input("Enter ECS Task Definition name: ")
docker_image_uri = input("Enter Docker Image URI for Task Definition: ")
ecs_service_name = input("Enter ECS Service name: ")
create_ecs_resources(subnet_id, sg_id, ecr_uri)

lb_name = input("Enter Load Balancer name: ")
lb_dns = create_load_balancer(subnet_id, sg_id)

configure_waf(lb_arn)

# Output application URL
print(f"Application URL: http://{lb_dns}")

# Output results
print(f"VPC ID: {vpc_id}")
print(f"Subnet ID: {subnet_id}")
print(f"EC2 Instance ID: {instance_id}")
print(f"Public IP: {public_ip}")
print(f"ECR URI: {ecr_uri}")
print(f"ECS Cluster Name: {ecs_cluster_name}")
print(f"ECS Task Definition Name: {ecs_task_definition_name}")
print(f"Load Balancer DNS: {lb_dns}")
