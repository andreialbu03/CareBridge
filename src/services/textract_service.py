import logging
from time import sleep
from botocore.exceptions import NoCredentialsError
from fastapi import HTTPException


# Function to start a Textract job
def start_textract_job(textract_client, bucket, filename):
    try:
        response = textract_client.start_document_text_detection(
            DocumentLocation={"S3Object": {"Bucket": bucket, "Name": filename}}
        )
        logging.info(f"Textract Response: {response}")
        return response["JobId"]
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")


# Function to poll Textract job status
def poll_textract_job_status(
    textract_client, job_id, result_page_url, max_polling_retries=20
):
    polling_retry_count = 0
    while polling_retry_count < max_polling_retries:
        job_status = check_textract_status(textract_client, job_id)
        if job_status == "SUCCEEDED":
            return "SUCCEEDED", result_page_url
        elif job_status == "FAILED":
            return "FAILED", None
        else:
            polling_retry_count += 1

            # Delay between retries
            sleep(5)
    return "TIMEOUT", None


# Function to check Textract job status
def check_textract_status(textract_client, job_id):
    response = textract_client.get_document_text_detection(JobId=job_id)
    logging.info(f"Textract Status: {response['JobStatus']}")
    return response["JobStatus"]
