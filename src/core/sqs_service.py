import boto3
from django.conf import settings

def send_message_to_sqs(body):
    # Create an SQS client

    sqs = boto3.client(
        'sqs',
        endpoint_url=settings.LOCALSTACK_ENDPOINT,
        region_name=settings.AWS_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    queue = sqs.create_queue(QueueName='first-queue-sqs')
    queue_url = queue['QueueUrl']

    return sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=body
    )