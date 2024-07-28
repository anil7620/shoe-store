#!/bin/bash

# Prompt user for AWS credentials
read -p "Enter your AWS Access Key: " AWS_ACCESS_KEY
read -p "Enter your AWS Secret Key: " AWS_SECRET_KEY



# Export AWS credentials for the session
export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_KEY

# Get user input for VPC, Subnet, and other names
read -p "Enter VPC name: " VPC_NAME
read -p "Enter Subnet name: " SUBNET_NAME
read -p "Enter EC2 Key Pair name: " KEY_PAIR_NAME
read -p "Enter EC2 Instance name: " EC2_INSTANCE_NAME
read -p "Enter MongoDB root username: " MONGO_USER
read -sp "Enter MongoDB root password: " MONGO_PASS
echo ""

# Create VPC and Subnets
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text)
aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=$VPC_NAME

SUBNET_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --query 'Subnet.SubnetId' --output text)
aws ec2 create-tags --resources $SUBNET_ID --tags Key=Name,Value=$SUBNET_NAME

# Create and configure EC2 instance
aws ec2 create-key-pair --key-name $KEY_PAIR_NAME --query 'KeyMaterial' --output text > $KEY_PAIR_NAME.pem
chmod 400 $KEY_PAIR_NAME.pem

SG_ID=$(aws ec2 create-security-group --group-name $EC2_INSTANCE_NAME-sg --description "Security group for $EC2_INSTANCE_NAME" --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 27017 --cidr 0.0.0.0/0

INSTANCE_ID=$(aws ec2 run-instances --image-id ami-0abcdef1234567890 --count 1 --instance-type t2.micro --key-name $KEY_PAIR_NAME --security-group-ids $SG_ID --subnet-id $SUBNET_ID --query 'Instances[0].InstanceId' --output text)
aws ec2 create-tags --resources $INSTANCE_ID --tags Key=Name,Value=$EC2_INSTANCE_NAME

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

# Install MongoDB on EC2 instance
scp -i $KEY_PAIR_NAME.pem <<EOF ec2-user@$PUBLIC_IP:/home/ec2-user/setup_mongo.sh
#!/bin/bash
sudo yum update -y
sudo yum install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
mongo <<MONGO
use admin
db.createUser({user: '$MONGO_USER', pwd: '$MONGO_PASS', roles:[{role:'root',db:'admin'}]})
MONGO
EOF

ssh -i $KEY_PAIR_NAME.pem ec2-user@$PUBLIC_IP 'chmod +x /home/ec2-user/setup_mongo.sh && /home/ec2-user/setup_mongo.sh'

echo "MongoDB setup complete. Access MongoDB at $PUBLIC_IP:27017"

# Create ECR repository
read -p "Enter ECR Repository name: " ECR_REPO_NAME
ECR_URI=$(aws ecr create-repository --repository-name $ECR_REPO_NAME --query 'repository.repositoryUri' --output text)

echo "ECR Repository created: $ECR_URI"

# Create ECS cluster and task definition
read -p "Enter ECS Cluster name: " ECS_CLUSTER_NAME
aws ecs create-cluster --cluster-name $ECS_CLUSTER_NAME

read -p "Enter ECS Task Definition name: " ECS_TASK_DEFINITION_NAME
read -p "Enter Docker Image URI for Task Definition: " DOCKER_IMAGE_URI

TASK_DEF=$(cat <<EOF
{
  "family": "$ECS_TASK_DEFINITION_NAME",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "$ECS_TASK_DEFINITION_NAME-container",
      "image": "$DOCKER_IMAGE_URI",
      "memory": 512,
      "cpu": 256,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 5000,
          "hostPort": 5000
        }
      ]
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512"
}
EOF
)

aws ecs register-task-definition --cli-input-json "$TASK_DEF"

# Create ECS service
read -p "Enter ECS Service name: " ECS_SERVICE_NAME
SERVICE_DEF=$(cat <<EOF
{
  "serviceName": "$ECS_SERVICE_NAME",
  "taskDefinition": "$ECS_TASK_DEFINITION_NAME",
  "desiredCount": 1,
  "launchType": "FARGATE",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": ["$SUBNET_ID"],
      "securityGroups": ["$SG_ID"],
      "assignPublicIp": "ENABLED"
    }
  }
}
EOF
)

aws ecs create-service --cluster $ECS_CLUSTER_NAME --cli-input-json "$SERVICE_DEF"

# Create Load Balancer
read -p "Enter Load Balancer name: " LB_NAME
LB_ARN=$(aws elbv2 create-load-balancer --name $LB_NAME --subnets $SUBNET_ID --security-groups $SG_ID --query 'LoadBalancers[0].LoadBalancerArn' --output text)

TG_ARN=$(aws elbv2 create-target-group --name ${LB_NAME}-tg --protocol HTTP --port 5000 --vpc-id $VPC_ID --target-type ip --query 'TargetGroups[0].TargetGroupArn' --output text)

aws elbv2 register-targets --target-group-arn $TG_ARN --targets Id=$INSTANCE_ID

aws elbv2 create-listener --load-balancer-arn $LB_ARN --protocol HTTP --port 80 --default-actions Type=forward,TargetGroupArn=$TG_ARN

LB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $LB_ARN --query 'LoadBalancers[0].DNSName' --output text)

# Output application URL
echo "Application URL: http://$LB_DNS"

# WAF setup
read -p "Do you want to set up WAF? (yes/no): " SETUP_WAF

if [ "$SETUP_WAF" == "yes" ]; then
    echo "WAF Options:"
    echo "1. Rate limiting"
    echo "2. Geo restriction"
    read -p "Select an option (1 or 2): " WAF_OPTION

    WAF_ARN=$(aws wafv2 create-web-acl --name ${LB_NAME}-acl --scope REGIONAL --default-action Allow={} --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=WebACL --query 'Summary.ARN' --output text)

    case $WAF_OPTION in
        1)
            # Rate limiting
            read -p "Enter rate limit (requests per 5 minutes): " RATE_LIMIT
            RATE_BASED_RULE=$(cat <<EOF
{
  "Name": "RateBasedRule",
  "Priority": 1,
  "Action": {
    "Block": {}
  },
  "Statement": {
    "RateBasedStatement": {
      "Limit": $RATE_LIMIT,
      "AggregateKeyType": "IP"
    }
  },
  "VisibilityConfig": {
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "RateBasedRule"
  }
}
EOF
)
            aws wafv2 update-web-acl --scope REGIONAL --id $WAF_ARN --lock-token $(aws wafv2 get-web-acl --scope REGIONAL --name ${LB_NAME}-acl --query 'LockToken' --output text) --default-action Allow={} --rules "$RATE_BASED_RULE"
            ;;
        2)
            # Geo restriction
            echo "Select countries for geo restriction (comma-separated codes, e.g., US,CA):"
            read -p "Country codes: " COUNTRY_CODES
            IFS=',' read -ra COUNTRIES <<< "$COUNTRY_CODES"
            GEO_MATCH_STATEMENT="{\"GeoMatchStatement\":{\"CountryCodes\":[\"${COUNTRIES[*]}\"]}}"
            GEO_BASED_RULE=$(cat <<EOF
{
  "Name": "GeoBasedRule",
  "Priority": 1,
  "Action": {
    "Block": {}
  },
  "Statement": $GEO_MATCH_STATEMENT,
  "VisibilityConfig": {
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "GeoBasedRule"
  }
}
EOF
)
            aws wafv2 update-web-acl --scope REGIONAL --id $WAF_ARN --lock-token $(aws wafv2 get-web-acl --scope REGIONAL --name ${LB_NAME}-acl --query 'LockToken' --output text) --default-action Allow={} --rules "$GEO_BASED_RULE"
            ;;
        *)
            echo "Invalid option selected."
            ;;
    esac

    aws wafv2 associate-web-acl --web-acl-arn $WAF_ARN --resource-arn $LB_ARN
    echo "WAF setup complete."
fi

# Output results
echo "VPC ID: $VPC_ID"
echo "Subnet ID: $SUBNET_ID"
echo "EC2 Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "ECR URI: $ECR_URI"
echo "ECS Cluster Name: $ECS_CLUSTER_NAME"
echo "ECS Task Definition Name: $ECS_TASK_DEFINITION_NAME"
echo "Load Balancer DNS: $LB_DNS"
