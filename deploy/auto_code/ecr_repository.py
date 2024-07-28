import boto3

ecr = boto3.client('ecr')

def create_ecr_repository(ecr_repo_name):
    repo = ecr.create_repository(repositoryName=ecr_repo_name)
    ecr_uri = repo['repository']['repositoryUri']
    return ecr_uri
