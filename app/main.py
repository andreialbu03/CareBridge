from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import boto3
from botocore.exceptions import NoCredentialsError
import logging
import os
from dotenv import load_dotenv

load_dotenv()
# logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")

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

# Route to handle file uploads
@app.post("/upload")
async def create_upload_file(file: UploadFile = File(...)):
    # Upload the file to S3
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)
    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET, file.filename)
        logging.debug(f"Successfully uploaded file to S3: {file.filename}")
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    
    # Use AWS Textract to extract text
    response = textract_client.start_document_text_detection(
        DocumentLocation={'S3Object': {'Bucket': S3_BUCKET, 'Name': file.filename}}
    )

    logging.debug(f"Textract Response: {response}")

    # Get the Textract job ID
    job_id = response['JobId']

    # Construct the URL for the result page
    result_page_url = f"/result/{job_id}"

    return {"filename": file.filename, "job_id": job_id, "result_page_url": result_page_url}

@app.get("/result/{job_id}", response_class=HTMLResponse)
async def get_result(request: Request, job_id: str):
    try:
        # Get the results from Textract
        response = textract_client.get_document_text_detection(JobId=job_id)
        logging.debug("Textract Response: %s", response)
        
        # Check if the Textract job is complete
        job_status = response['JobStatus']
        if job_status != 'SUCCEEDED':
            raise HTTPException(status_code=500, detail=f"Textract job status: {job_status}")

        # Extract and display text
        blocks = response['Blocks']
        extracted_text = ''.join([block['Text'] for block in blocks if block['BlockType'] == 'LINE'])
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    except Exception as e:
        logging.error("Error processing Textract response: %s", str(e))
        raise HTTPException(status_code=500, detail="Error processing Textract response")

    return templates.TemplateResponse("result.html", {"request": request, "extracted_text": extracted_text})

if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app using Uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
