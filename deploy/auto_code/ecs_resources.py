import boto3

ecs = boto3.client('ecs')

def create_ecs_resources(subnet_id, sg_id, ecr_uri, ecs_cluster_name, ecs_task_definition_name, docker_image_uri, ecs_service_name):
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
