import logging
from time import sleep
from botocore.exceptions import NoCredentialsError
from fastapi import HTTPException


# Function to start a Textract job
def start_textract_job(textract_client, bucket, filename):
    try:
        # Send request to AWS Textract to start document text detection
        response = textract_client.start_document_text_detection(
            DocumentLocation={"S3Object": {"Bucket": bucket, "Name": filename}}
        )

        # Log the Textract response
        logging.info(f"Textract Response: {response}")

        # Return the Textract job ID
        return response["JobId"]
    except NoCredentialsError:
        # If AWS credentials are not available, raise an HTTPException with a 500 status code
        raise HTTPException(status_code=500, detail="AWS credentials not available")


# Function to poll Textract job status
def poll_textract_job_status(
    textract_client, job_id, result_page_url, max_polling_retries=20
):
    polling_retry_count = 0
    # Continue polling until max number of retries or until job is complete
    while polling_retry_count < max_polling_retries:
        # Check the status of the Textract job
        job_status = check_textract_status(textract_client, job_id)

        # If the job is complete, return the job status and the result page URL
        if job_status == "SUCCEEDED":
            return "SUCCEEDED", result_page_url
        elif job_status == "FAILED":
            return "FAILED", None
        else:
            polling_retry_count += 1

            # Delay between retries
            sleep(3)
    return "TIMEOUT", None


# Function to check Textract job status
def check_textract_status(textract_client, job_id):
    # Send request to AWS Textract to get the status of the job
    response = textract_client.get_document_text_detection(JobId=job_id)
    logging.info(f"Textract Status: {response['JobStatus']}")
    return response["JobStatus"]
