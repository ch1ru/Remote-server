import boto3
from botocore.exceptions import ClientError

# Create DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Reference your table
table = dynamodb.Table('Commands')

table = None