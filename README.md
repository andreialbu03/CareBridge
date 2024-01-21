# CareBridge - Your Healthcare Communication Tool

Welcome to **_CareBridge_**, your web-based healthcare communication tool designed to help you understand and interpret medical documents and notes from healthcare providers.

You can access **_CareBridge_** by clicking [this link](https://carebridgeapp.com)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Development](#development)
- [Dependencies](#dependencies)

## Overview

CareBridge empowers you to better understand your health by interpreting medical jargon with a range of features:

- **Document Upload**: Easily upload your doctor's notes or medical documents securely.
- **Document Interpretation**: Receive explanations in plain English to help you understand the medical information contained in the documents.
- **Text Extraction**: The tool extracts the text from your uploaded documents for analysis.

## Features

### Document Upload

Upload and store your medical documents securely to keep track of your health records.

### Document Interpretation

Receive medical explanations in plain language to understand your health situation better.

## Dependencies

CareBridge uses the following packages:

- `fastapi`: A modern, fast (high-performance) web framework for building APIs with Python.
- `uvicorn`: An ASGI server implementation, for running the application.
- `jinja2`: A template engine for Python.
- `python-multipart`: A streaming multipart parser for Python.
- `boto3`: The Amazon Web Services (AWS) SDK for Python.
- `python-dotenv`: Reads key-value pairs from a `.env` file and sets them as environment variables.
- `openai`: The official OpenAI API client for Python.

## Running the Application Locally

### Local Installation and Setup

To set up CareBridge locally, follow these steps:

```bash
# Clone the repository
git clone https://your-repository-link.git
cd CareBridge

# Optional: Set up a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use 'venv\Scripts\activate'

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

Run the application using UVicorn within the `src` directory:

```bash
cd src
uvicorn main:app --reload
```
