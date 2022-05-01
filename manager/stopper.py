from __init__ import ecs_execute, redirect_to, show_loading
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

ecs = boto3.client('ecs')

def check_task_already_exists():
    response = ecs.list_tasks(
        cluster = CLUSTER,
        startedBy = f'AWS_LAMBDA_{SERNAME}'
    )
    task_arn = response['taskArns'][0]
    return task_arn

def ecs_stop_task(task_arn):
    response = ecs.stop_task(
        cluster = CLUSTER,
        task = task_arn,
        reason = 'Inactivity.'
    )
    return response
 
def lambda_handler(event, context):
    task_arn = check_task_already_exists()
    return ecs_stop_task(task_arn)