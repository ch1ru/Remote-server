import boto3
from botocore.exceptions import ClientError

# Create DynamoDB client
#dynamodb = boto3.resource('dynamodb', region_name='your_region')

# Reference your table
#table = dynamodb.Table('Commands')

table = None