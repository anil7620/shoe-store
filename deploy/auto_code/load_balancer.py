import boto3

elb = boto3.client('elbv2')

def create_load_balancer(subnet_id, sg_id, lb_name, vpc_id, instance_id):
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
    return lb_dns, lb_arn
