from functools import lru_cache
import json
import websocket
import uuid
import construct as c

import boto3

ecs = boto3.client('ecs')

def redirect_to(location):
    return {
        "statusCode": 302,
        "headers": {
            'Location': location,
        },
    } 

@lru_cache
def show_loading():
    with open('index.html') as f:
        lines = f.readlines()
    return {
        "statusCode": 200,
        "body": ''.join(lines),
        "headers": {
            'Content-Type': 'text/html',
        }
    }
    
def ecs_execute(task_arn, command, cluster):
    response = ecs.execute_command(
        cluster = cluster,
        command = command,
        interactive = True,
        task = task_arn
    )
    session = response['session']
    connection = websocket.create_connection(session['streamUrl'])
    try:
        init_payload = {
            "MessageSchemaVersion": "1.0",
            "RequestId": str(uuid.uuid4()),
            "TokenValue": session['tokenValue']
        }
        connection.send(json.dumps(init_payload))
        AgentMessageHeader = c.Struct(
            'HeaderLength' / c.Int32ub,
            'MessageType' / c.PaddedString(32, 'ascii'),
        )
        AgentMessagePayload = c.Struct(
            'PayloadLength' / c.Int32ub,
            'Payload' / c.PaddedString(c.this.PayloadLength, 'ascii')
        )
        while True:
            response = connection.recv()
            message = AgentMessageHeader.parse(response)
            if 'channel_closed' in message.MessageType:
                raise Exception('Channel closed before command output was received')
            if 'output_stream_data' in message.MessageType:
                break
    finally:
        connection.close()
    payload_message = AgentMessagePayload.parse(response[message.HeaderLength:])
    
    return payload_message.Payload.strip()