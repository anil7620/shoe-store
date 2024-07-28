import boto3
import os

ec2 = boto3.client('ec2')

def create_ec2_instance(subnet_id, key_pair_name, ec2_instance_name):
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
