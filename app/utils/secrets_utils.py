from app.constants import SECRET_NAME
from app.constants import REGION_NAME
import json

import boto3
from botocore.exceptions import ClientError


def get_jwt_secret():

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=REGION_NAME
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=SECRET_NAME
        )
    except ClientError as e:
        raise e

    secret = json.loads(get_secret_value_response['SecretString'])
    return secret['JWT_SECRET']
