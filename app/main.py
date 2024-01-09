from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

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
    # Access information about the uploaded file
    filename = file.filename
    content_type = file.content_type
    
    return {"filename": filename, "content_type": content_type}

if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI app using Uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
