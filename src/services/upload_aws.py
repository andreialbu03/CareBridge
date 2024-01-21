import boto3
from botocore.exceptions import NoCredentialsError
import logging


def upload_file_to_s3(file, aws_access_key, aws_secret_key, aws_region, s3_bucket):
    # Upload the file to S3
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region,
    )

    try:
        s3_client.upload_fileobj(file.file, s3_bucket, file.filename)
        logging.info(f"Successfully uploaded file to S3: {file.filename}")
        return True
    except NoCredentialsError as e:
        logging.error(f"AWS credentials not available: {e}")
        return False
