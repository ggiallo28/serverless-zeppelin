from __init__ import ecs_execute, redirect_to, show_loading
from functools import lru_cache
import json
import boto3
import os
import requests

CLUSTER = os.getenv('CLUSTER')
TASKDEF = os.getenv('TASKDEF')
SERNAME = os.getenv('SERNAME')
SECURITY_GROUP_ID = os.getenv('SECURITY_GROUP_ID')
DEFAULT_SUBNETS = os.getenv('DEFAULT_SUBNETS')
CONTAINER_PORT = os.getenv('CONTAINER_PORT')
CODECOMMIT_REPO = os.getenv('CODECOMMIT_REPO')
GET_IP_COMMAND = 'curl -4 icanhazip.com'

ecs = boto3.client('ecs')

def ecs_wait_task(location):
    r = requests.get(location)
    return r.status_code
    
def check_task_already_exists():
    response = ecs.list_tasks(
        cluster = CLUSTER,
        startedBy = f'AWS_LAMBDA_{SERNAME}'
    )
    if len(response['taskArns']) > 0:
        task_arn = response['taskArns'][0]
        return task_arn

def ecs_run_task():
    response = ecs.run_task(
        cluster = CLUSTER,
        launchType = 'FARGATE',
        enableExecuteCommand = True,
        networkConfiguration = {
            'awsvpcConfiguration': {
                'subnets': DEFAULT_SUBNETS.split(','),
                'securityGroups': [
                    SECURITY_GROUP_ID,
                ],
                'assignPublicIp': 'ENABLED'
            }
        },
        startedBy = f'AWS_LAMBDA_{SERNAME}',
        taskDefinition = TASKDEF
    )
    task_arn = response['tasks'][0]['taskArn']
    return task_arn

@lru_cache
def ecs_get_task_ip(task_arn):
    ip_address = ecs_execute(task_arn, GET_IP_COMMAND, CLUSTER)
    return f'http://{ip_address}:{CONTAINER_PORT}'
 
def lambda_handler(event, context):
    try:
        task_arn = check_task_already_exists()
        if not task_arn:
            task_arn = ecs_run_task()
            
        location = ecs_get_task_ip(task_arn)
        
        response_code = ecs_wait_task(location)
        if response_code == 200:
            return redirect_to(location)
    except:
        pass
    
    return show_loading()