import vpc_subnet
import ec2_instance
import ecr_repository
import ecs_resources
import load_balancer
import waf_configuration

# Prompt user for inputs
aws_access_key = input("Enter your AWS Access Key: ")
aws_secret_key = input("Enter your AWS Secret Key: ")

vpc_name = input("Enter VPC name: ")
subnet_name = input("Enter Subnet name: ")
key_pair_name = input("Enter EC2 Key Pair name: ")
ec2_instance_name = input("Enter EC2 Instance name: ")
mongo_user = input("Enter MongoDB root username: ")
mongo_pass = input("Enter MongoDB root password: ")

# Main execution flow
vpc_id, subnet_id = vpc_subnet.create_vpc_subnet(vpc_name, subnet_name)
instance_id, public_ip = ec2_instance.create_ec2_instance(subnet_id, key_pair_name, ec2_instance_name)
ec2_instance.install_mongodb(public_ip, key_pair_name, mongo_user, mongo_pass)

# ecr_repo_name = input("Enter ECR Repository name: ")
# ecr_uri = ecr_repository.create_ecr_repository(ecr_repo_name)

# ecs_cluster_name = input("Enter ECS Cluster name: ")
# ecs_task_definition_name = input("Enter ECS Task Definition name: ")
# docker_image_uri = input("Enter Docker Image URI for Task Definition: ")
# ecs_service_name = input("Enter ECS Service name: ")
# ecs_resources.create_ecs_resources(subnet_id, sg_id, ecr_uri, ecs_cluster_name, ecs_task_definition_name, docker_image_uri, ecs_service_name)

# lb_name = input("Enter Load Balancer name: ")
# lb_dns, lb_arn = load_balancer.create_load_balancer(subnet_id, sg_id, lb_name, vpc_id, instance_id)

# waf_configuration.configure_waf(lb_arn, lb_name)

# Output application URL
print(f"Application URL: http://{lb_dns}")

# Output results
print(f"VPC ID: {vpc_id}")
print(f"Subnet ID: {subnet_id}")
print(f"EC2 Instance ID: {instance_id}")
print(f"Public IP: {public_ip}")
# print(f"ECR URI: {ecr_uri}")
# print(f"ECS Cluster Name: {ecs_cluster_name}")
# print(f"ECS Task Definition Name: {ecs_task_definition_name}")
# print(f"Load Balancer DNS: {lb_dns}")
