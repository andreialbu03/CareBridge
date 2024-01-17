from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import boto3
from botocore.exceptions import NoCredentialsError
import logging
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from time import sleep
import re

load_dotenv()
logging.basicConfig(level=logging.INFO)

GPT_API_KEY = os.getenv("GPT_API_KEY")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")

app = FastAPI()
openai_client = OpenAI(
    api_key=GPT_API_KEY
)

# Initialize AWS Textract client
textract_client = boto3.client('textract', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)

# Serve static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Route to render the homepage
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Define a function to check the status of the Textract job
def check_textract_status(job_id):
    response = textract_client.get_document_text_detection(JobId=job_id)
    logging.info(f"Textract Status: {response['JobStatus']}")
    return response['JobStatus']

# Route to handle file uploads
@app.post("/upload")
async def create_upload_file(file: UploadFile = File(...)):
    # Upload the file to S3
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)
    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET, file.filename)
        logging.info(f"Successfully uploaded file to S3: {file.filename}")
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    
    # Use AWS Textract to extract text
    response = textract_client.start_document_text_detection(
        DocumentLocation={'S3Object': {'Bucket': S3_BUCKET, 'Name': file.filename}}
    )

    logging.info(f"Textract Response: {response}")

    # Get the Textract job ID
    job_id = response['JobId']

    # Construct the URL for the result page
    result_page_url = f"/result/{job_id}"

    logging.info(f"Result page URL: {result_page_url}")

    # Maximum number of polling retries
    max_polling_retries = 20

    # Initialize the polling retry count
    polling_retry_count = 0

    while polling_retry_count < max_polling_retries:
        # Check the status of the Textract job
        job_status = check_textract_status(job_id)

        if job_status == 'SUCCEEDED':
            # Textract job is complete, redirect to the result page
            redirect_response = RedirectResponse(url=result_page_url)
            return redirect_response
        elif job_status == 'FAILED':
            # Handle the case where the Textract job failed (optional)
            return {"error": "Textract job failed"}
        else:
            # Textract job is still in progress, wait for a while and then poll again
            polling_retry_count += 1
            sleep(5)  # Wait for 5 seconds before polling again

    # If all polling retries fail, you can handle the error or return a specific response
    return {"error": "Failed to retrieve Textract results after multiple polling retries"}


    # return RedirectResponse(url=result_page_url)

@app.get("/result/{job_id}", response_class=HTMLResponse)
@app.post("/result/{job_id}", response_class=HTMLResponse)
async def get_result(request: Request, job_id: str):
    try:
        # Get the results from Textract
        response = textract_client.get_document_text_detection(JobId=job_id)
        
        # Check if the Textract job is complete
        job_status = response['JobStatus']
        if job_status != 'SUCCEEDED':
            raise HTTPException(status_code=500, detail=f"Textract job status: {job_status}")
        
        logging.info(f"Textract Response: {response['JobStatus']}")

        # Extract and display text
        blocks = response['Blocks']
        # Save extracted text to a file
        block_path = 'textract_blocks.json'
        with open(block_path, 'w') as output_file2:
            json.dump(blocks, output_file2, indent=2)

        # extracted_text = ''.join([block['Text'] for block in blocks if block['BlockType'] == 'LINE'])
        extracted_text = ''.join([block['Text'] if 'Text' in block and isinstance(block['Text'], str) else '' for block in blocks])
        
        # Save extracted text to a file
        output_file_path = 'extracted_text.txt'
        with open(output_file_path, 'w') as output_file:
            output_file.write(extracted_text)


    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    except Exception as e:
        logging.error("Error processing Textract response: %s", str(e))
        raise HTTPException(status_code=500, detail="Error processing Textract response")
    

    #####
    # medical_entities = comprehend_medical(extracted_text)
    # # Extract conditions, medications, anatomy, procedures, and other entities
    # conditions = [entity['Text'] for entity in medical_entities if entity['Type'] == 'MEDICAL_CONDITION']
    # medications = [entity['Text'] for entity in medical_entities if entity['Type'] == 'MEDICATION']
    # anatomy = [entity['Text'] for entity in medical_entities if entity['Type'] == 'ANATOMY']
    # procedures = [entity['Text'] for entity in medical_entities if entity['Type'] == 'TEST_TREATMENT_PROCEDURE']
    # # Combine extracted entities into a summary
    # summary = f"Conditions: {', '.join(conditions)}\nMedications: {', '.join(medications)}\nAnatomy: {', '.join(anatomy)}\nProcedures: {', '.join(procedures)}"
    # print(medical_entities)

    # Generate user-friendly explanation using GPT-3
    explanation = generate_explanation(extracted_text)


    return templates.TemplateResponse("result.html", {"request": request, "extracted_text": explanation})
    # return templates.TemplateResponse("result.html", {"request": request, "extracted_text": explanation})


# Function to extract medical entities using Comprehend Medical
def comprehend_medical(text):
    comprehend_medical = boto3.client('comprehendmedical', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    response = comprehend_medical.detect_entities(Text=text)
    medical_entities = response['Entities']
    logging.info(f"Comprehend Medical Response Successful")

    # Specify the file path where you want to save the output
    output_file_path = 'comprehend_output.json'

    # Open the file in write mode and write the extracted medical entities
    with open(output_file_path, 'w') as output_file:
        json.dump(medical_entities, output_file, indent=2)
    
    logging.info(f"Comprehend Medical output saved to {output_file_path}")

    return medical_entities


# Function to generate user-friendly explanations using GPT-3
def generate_explanation(text):
    prompt = (
        "Hi there, I am a patient and just had a doctor's visit. My doctor just gave me a note with this information, but I don't understand it. Below is the text that is on the note, can you try your best to explain to me what it says in a way that I can easily understand and also provide me with online resources regarding what it talks about? Ignore anything that does not make sense.\n\n"
        "Note:\n" + text
    )
    logging.info("Sending prompt to GPT-3")
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    explanation = response.choices[0].message.content

    output_path = 'gpt_response.txt'
    with open(output_path, 'w') as output_file:
        output_file.write(explanation)

    return explanation


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app using Uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
