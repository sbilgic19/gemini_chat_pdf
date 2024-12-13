from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, HTTPException, Path, Body
import uuid
from pdf_processor import process_pdf, process_metadata, PDFPasswordProtectedError, get_vector_store
from pydantic import BaseModel, Field
from typing import Any
from gemini_client import get_conversational_chain
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import google.generativeai as genai
import os

load_dotenv()


# Retrieve API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
app = FastAPI()

# Global storage for PDFs (in-memory)
pdf_storage = {}

class PDF_File(BaseModel):
    pdf_id: str
    file_name: str
    size: int
    content: str
    metadata: str
    page_count: int

class Query(BaseModel):
    message: str

# Maximum file size limit (100 MB)
MAX_FILE_SIZE = 100 * 1024 * 1024

@app.post("/v1/pdf")
async def upload_pdf(file: UploadFile):
    """
    Endpoint for uploading and registering a PDF.
    """
    try:
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=415, detail="Unsupported file type. Only PDFs are allowed.")

        # Check file size
        file_size = file.file.seek(0, 2)  # Move to the end of the file
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds the 100 MB limit.")
        file.file.seek(0)  # Reset file pointer to the beginning

        # Generate a unique PDF ID
        pdf_id = str(uuid.uuid4())

        # Process the PDF
        pdf_data = process_pdf(file.file)

        pdf_file = PDF_File(
            pdf_id = pdf_id,
            file_name= file.filename,
            size= file_size,
            content= pdf_data["text"],
            metadata= process_metadata(pdf_data["metadata"]),
            page_count= len(pdf_data["text"].split("\f")) - 1
        )
        get_vector_store(content=pdf_file.content, pdf_id=pdf_id)
        pdf_storage[pdf_id] = pdf_file
        return {"pdf_id": pdf_id}
    
    except PDFPasswordProtectedError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")

@app.post("/v1/chat/{pdf_id}")
async def chat_with_pdf(pdf_id: str = Path(..., description="The unique identifier for the PDF"), query: Query = Body(...)):
    # Validate the pdf_id and retrieve the associated PDF content
    pdf_file = pdf_storage.get(pdf_id)
    if not pdf_file:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    #pdf_content = pdf_storage[pdf_id]["content"]
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.load_local(pdf_id, embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(query.message)
    chain = get_conversational_chain()

    response = chain({"input_documents": docs, "question": query.message}, return_only_outputs=True)
    print(response)
    # Use the Gemini API to generate a response based on the PDF content and user query
    #response_text = query_gemini_api(pdf_content, query.message)
    
    #return Response(response=response_text)
    return response