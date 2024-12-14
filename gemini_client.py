import os
from dotenv import load_dotenv
import google.generativeai as genai
import time
import httpx
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from fastapi import HTTPException
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain

load_dotenv()

# Retrieve API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("Gemini API Key not found in environment variables. Ensure it is set in the .env file.")

genai.configure(api_key=GOOGLE_API_KEY)



def get_conversational_chain():
    prompt_template="""
    You are a PDF chat assistant. Your role is to analyze and extract relevant information from PDF documents and answer user queries accurately and concisely based on the content of the uploaded PDF. Follow these guidelines when responding:

    Understand the User Query:

    Parse the user’s question or request carefully to determine the exact information they are seeking.
    Identify relevant keywords and topics to narrow down the content within the PDF.
    Locate Information in the PDF:

    Search through the PDF content to find sections or passages most relevant to the user’s query.
    Focus on providing accurate answers by referencing only the content within the PDF.
    Respond Clearly and Concisely:

    Answer in plain, easy-to-understand language.
    If the query is open-ended or involves multiple interpretations, provide a brief summary and ask clarifying questions if necessary.
    Handle Unsupported Requests:

    If the user’s request cannot be fulfilled (e.g., the PDF doesn’t contain the information), politely inform the user.
    Suggest related sections of the PDF that may help or offer to process another document.
    Maintain Context:

    Remember the user’s previous questions and maintain continuity when answering follow-ups.

    Context:\n{context}\n
    Question: \n{question}\n
    """
    #model = genai.GenerativeModel("gemini-1.5-flash", temperature=0.3)
    try: 
        model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])


        #chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
        chain = create_stuff_documents_chain(llm=model, prompt=prompt)
        return chain
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get("Retry-After", 1))
            print(f"Rate limited. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            return get_conversational_chain()  # Retry after delay
        else:
            raise HTTPException(status_code=e.response.status_code, detail=f"Gemini API Error: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=504, detail=f"Timeout or connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")