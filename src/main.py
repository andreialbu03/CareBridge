from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
from services.upload_aws import upload_file_to_s3
from services.textract_service import start_textract_job, poll_textract_job_status
from services.gpt_service import generate_gpt_explanation
from openai import OpenAI
from time import sleep
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Request,
    HTTPException,
    responses,
    staticfiles,
    templating,
)
import logging
import boto3
import os


# Aliases for clarity
HTMLResponse = responses.HTMLResponse
RedirectResponse = responses.RedirectResponse
StaticFiles = staticfiles.StaticFiles
Jinja2Templates = templating.Jinja2Templates

# Load environment variables and initialize logging
load_dotenv()
logging.basicConfig(level=logging.INFO)

# Environment variables
GPT_API_KEY = os.getenv("GPT_API_KEY")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")

# Initialize FastAPI app
app = FastAPI()
openai_client = OpenAI(api_key=GPT_API_KEY)

# Initialize AWS Textract client
textract_client = boto3.client(
    "textract",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

# Serve static files (CSS, JS, etc.) and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Route to render the homepage
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/test", tags=["Root"])
async def read_root():
    return {"status": "ok"}


# Route to handle file uploads
@app.post("/upload")
async def create_upload_file(file: UploadFile = File(...)):
    # Upload the file to S3
    success = upload_file_to_s3(
        file, AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, S3_BUCKET
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload file to S3")

    # Use AWS Textract to extract text from the file
    job_id = start_textract_job(textract_client, S3_BUCKET, file.filename)

    # Construct the URL for the result page
    result_page_url = f"/result/{job_id}"
    logging.info(f"Result page URL: {result_page_url}")

    # Poll Textract job status
    job_status, redirect_url = poll_textract_job_status(
        textract_client, job_id, result_page_url
    )
    if job_status == "SUCCEEDED":
        return RedirectResponse(url=redirect_url)
    elif job_status == "FAILED":
        return {"error": "Textract job failed"}
    else:
        return {
            "error": "Failed to retrieve Textract results after multiple polling retries"
        }


# Route to render the result page
@app.get("/result/{job_id}", response_class=HTMLResponse)
@app.post("/result/{job_id}", response_class=HTMLResponse)
async def get_result(request: Request, job_id: str):
    try:
        # Get the results from Textract
        response = textract_client.get_document_text_detection(JobId=job_id)

        # Check again if the Textract job is complete
        job_status = response["JobStatus"]
        if job_status != "SUCCEEDED":
            raise HTTPException(
                status_code=500, detail=f"Textract job status: {job_status}"
            )
        logging.info(f"Textract Response: {response['JobStatus']}")

        # Extract the text from the response
        blocks = response["Blocks"]
        extracted_text = "".join(
            [
                block["Text"]
                if "Text" in block and isinstance(block["Text"], str)
                else ""
                for block in blocks
            ]
        )
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not available")
    except Exception as e:
        logging.error("Error processing Textract response: %s", str(e))
        raise HTTPException(
            status_code=500, detail="Error processing Textract response"
        )

    # Generate user-friendly explanation using GPT-3
    explanation = generate_gpt_explanation(openai_client, extracted_text)

    return templates.TemplateResponse(
        "result.html", {"request": request, "extracted_text": explanation}
    )


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app using Uvicorn server
    uvicorn.run(app, host="127.0.0.1", port=8000)
