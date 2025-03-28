import json
import logging

import boto3

logger = logging.getLogger(__name__)

secrets_client = boto3.client("secretsmanager")


def get_api_key(api_secret_arn):
    """
    Get the API key from AWS Secrets Manager.
    Args:
        api_secret_arn (str): The ARN of the secret in AWS Secrets Manager containing the API key.
    Returns:
        str: The API key.
    """
    try:
        secret_response = secrets_client.get_secret_value(
            SecretId=api_secret_arn
        )
        if "SecretString" in secret_response:
            secret_data = json.loads(secret_response["SecretString"])
            api_key = secret_data.get("key")
            logger.info(
                f"Successfully retrieved API key from secret ARN: {api_secret_arn}"
            )
            return api_key
    except Exception as e:
        logger.error(f"Error retrieving secret ARN {api_secret_arn}: {str(e)}")
        raise
    return None
