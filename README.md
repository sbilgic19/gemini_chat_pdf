# PDF Chat API

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
  - [1. PDF Upload Endpoint](#1-pdf-upload-endpoint)
  - [2. Chat with PDF Endpoint](#2-chat-with-pdf-endpoint)

---

## Project Overview

**PDF Chat API** is a FastAPI-based application that allows users to upload PDF documents and interact with their content through a conversational interface. Leveraging the power of Google's Gemini API and LangChain, users can ask questions about their uploaded PDFs and receive context-aware responses.

## Features

- **PDF Upload:** Users can upload PDF files, which are then processed to extract text and metadata.
- **Chat Interface:** Interact with the content of uploaded PDFs by asking questions and receiving AI-generated answers.
- **State Management:** Efficient storage and retrieval of PDFs along with their extracted content and metadata.
- **LLM Integration:** Seamless integration with Google's Gemini API for advanced natural language processing.
- **Vector Store:** Utilizes FAISS for vector-based similarity searches to enhance response relevance.

## Technologies Used

- **Python 3.10**
- **FastAPI:** Web framework for building APIs.
- **Uvicorn:** ASGI server for serving FastAPI applications.
- **Pydantic:** Data validation and settings management.
- **LangChain:** Framework for building applications with language models.
- **FAISS:** Library for efficient similarity search and clustering of dense vectors.
- **Google Generative AI (Gemini API):** For generating AI-driven responses.
- **PyPDF2 & pdf2image:** For PDF processing and OCR.
- **Pytesseract:** Optical Character Recognition (OCR) tool.
- **Dotenv:** For managing environment variables.

## Setup Instructions

### Prerequisites

- **Python 3.10** installed on your machine. You can download it from [here](https://www.python.org/downloads/release/python-3100/).
- **pip** package manager.
- **Tesseract OCR** installed for OCR functionality.
  - **Installation:**
    - **macOS:** `brew install tesseract`
    - **Ubuntu:** `sudo apt-get install tesseract-ocr`
    - **Windows:** Download the installer from [here](https://github.com/tesseract-ocr/tesseract/wiki).

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/pdf-chat-api.git
   cd pdf-chat-api
2. **Create a Virtual Environment:**

    ```bash
    python3.10 -m venv env
    source env/bin/activate  # On Windows: env\Scripts\activate
3. **Install Dependencies:**

    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
### Configuration

Create a .env file in the root directory of the project and add the following:

    ```bash
    GOOGLE_API_KEY=your_google_api_key_here


### API Endpoints

#### 1. PDF Upload Endpoint:

**Endpoint:** /v1/pdf
**Method:** POST
**Description:** Uploads a PDF file, processes it to extract text and metadata, and stores it for future interactions.

**Request:**
```bash 
curl -X POST "http://localhost:8000/v1/pdf" -F "file=@/path/to/yourpdf/file.pdf"
```

**Successful Response: 200 OK**
```bash
{
  "pdf_id": "unique_pdf_identifier"
}
```

**Password-Protected PDF: 401 Unauthorized**
```bash
{
  "detail": "PDF is password protected and cannot be accessed without the correct password."
}
```

**Unsupported File Type: 415 Unsupported Media Type**
```bash
{
  "detail": "Unsupported file type. Only PDFs are allowed."
}
```

#### 2. Chat with PDF Endpoint:**

**Endpoint:** /v1/chat/{pdf_id}
**Method:** POST
**Description:** Interacts with a specific PDF by allowing users to ask questions about its content.
**Path Parameters:** pdf_id(string) - The unique identifier of the PDF to interact with.

**Request:** application/json
**Body:**
```bash
{
  "message": "Your question here"
}
```

```bash
curl -X POST "http://localhost:8000/v1/chat/c6f9c28c-d37c-43fa-a773-b03b3fccf9c0" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is the main topic of this PDF?"}'
```

**Successful Response: 200 OK**
```bash
{
  "output_text": "The main topic of this PDF is ..."
}
```

**PDF Not Found: 404 Not Found**
```bash
{
  "detail": "PDF not found"
}
```