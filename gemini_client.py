import os
from dotenv import load_dotenv
import google.generativeai as genai

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate

# Load environment variables

load_dotenv()

# Retrieve API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("Gemini API Key not found in environment variables. Ensure it is set in the .env file.")

genai.configure(api_key=GOOGLE_API_KEY)



def get_conversational_chain():
    prompt_template=""" Answer the question as requested by the user (detailed, shortly, with giving metrics etc.) from the given context. If the answer
    is not in the provided context just say "Answer is not available in the context." do not provide the answer. If answer is partly available only give the
    available information.

    Context:\n{context}\n
    Question: \n{question}\n
    """
    #model = genai.GenerativeModel("gemini-1.5-flash", temperature=0.3)
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain
