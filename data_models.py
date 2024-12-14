from pydantic import BaseModel
class PDF_File(BaseModel):
    pdf_id: str
    file_name: str
    size: int
    content: str
    metadata: str
    page_count: int

class Query(BaseModel):
    message: str

