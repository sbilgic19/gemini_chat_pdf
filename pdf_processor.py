import re
#from PyPDF2 import PdfReader
from pypdf import PdfReader
import json
from pdf2image import convert_from_bytes
import pytesseract
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

class PDFPasswordProtectedError(Exception):
    """Exception raised for password-protected PDFs."""
    def __init__(self, message="PDF is password protected and cannot be accessed without the correct password."):
        self.message = message
        super().__init__(self.message)

def preprocess_text(text: str) -> str:
    """
    Clean and preprocess extracted text.
    """
    # Remove extra whitespace
    text = re.sub(r'^\s*\w{1,2}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text, flags=re.MULTILINE)
    return text.strip()

def process_metadata(metadata):
    """
    Process and convert PDF metadata to a JSON string.
    """
    if metadata:
        # Convert metadata to a JSON string
        return json.dumps({k: str(v) if v else "" for k, v in metadata.items()}, indent=4)
    return "{}"  # Return empty JSON string if no metadata

def extract_text_with_ocr(pdf_file_stream):
    """
    Extract text from a PDF file stream using OCR.
    """
    # Move to the beginning of the file stream
    pdf_file_stream.seek(0)
    # Read the entire file into a bytes object
    pdf_bytes = pdf_file_stream.read()

    # Convert PDF bytes to images
    images = convert_from_bytes(pdf_bytes)

    # Extract text from each image using pytesseract
    text = ''
    for image in images:
        text += pytesseract.image_to_string(image, lang='tur+eng')

    return text

def process_pdf(pdf_file) -> dict:
    """
    Extract and preprocess text and metadata from a PDF file.
    """
    try:
        logger.info("Starting PDF processing")
        reader = PdfReader(pdf_file)
        logger.info("PDF processed successfully")
        text_content = ""

        # Check if the PDF is encrypted
        if reader.is_encrypted:
            # If the PDF is encrypted and we cannot decrypt it (i.e., no password or wrong password provided)
            if not reader.decrypt(''):  # You can replace '' with a password variable if needed
                logger.error(f"Password-protected PDF error")
                raise PDFPasswordProtectedError()

        for page in reader.pages:
            raw_text = page.extract_text()
            if raw_text:
                text_content += preprocess_text(raw_text)
        
        if not text_content:
            # Attempt OCR if no text extracted
            text_content = extract_text_with_ocr(pdf_file)

        metadata = reader.metadata or {}


        return {
            "text": text_content,
            "metadata": metadata
        }
    except PDFPasswordProtectedError:
        raise
    except Exception as e:
        print("Error processing the PDF")
        logger.error(f"Error processing PDF: {e}")
        raise RuntimeError(f"Error processing PDF: {e}")

def get_text_chunks(text: str):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(content: str, pdf_id: str):
    text_chunks = get_text_chunks(content)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local(pdf_id)    