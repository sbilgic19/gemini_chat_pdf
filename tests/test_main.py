import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os
from io import BytesIO


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import app, MAX_FILE_SIZE

client = TestClient(app)

@pytest.fixture
def mock_pdf_file():
    """Fixture to simulate a PDF file upload."""
    from fastapi.datastructures import UploadFile
    from io import BytesIO

    file_content = b"%PDF-1.4\n%Mock PDF Content\n"
    mock_file = UploadFile(
        filename="test.pdf",
        file=BytesIO(file_content)
    )
    return mock_file

@patch("main.process_pdf")
@patch("main.get_vector_store")
def test_upload_pdf_success(mock_get_vector_store, mock_process_pdf, mock_pdf_file):
    """Test successful PDF upload."""
    # Mock the behavior of process_pdf
    mock_process_pdf.return_value = {
        "text": "Mocked PDF text content",
        "metadata": {"author": "Test Author"}
    }

    # Mock get_vector_store to avoid unnecessary processing
    mock_get_vector_store.return_value = None

    # Send the request
    response = client.post(
        "/v1/pdf",
        files={"file": ("test.pdf", mock_pdf_file.file, "application/pdf")}
    )

    # Assert successful response
    assert response.status_code == 200
    response_data = response.json()
    assert "pdf_id" in response_data

    # Assert mocks were called
    mock_process_pdf.assert_called_once()
    mock_get_vector_store.assert_called_once_with(content="Mocked PDF text content", pdf_id=response_data["pdf_id"])

@patch("main.process_pdf")
def test_upload_pdf_unsupported_file_type(mock_process_pdf):
    """Test upload with an unsupported file type."""
    response = client.post(
        "/v1/pdf",
        files={"file": ("test.txt", BytesIO(b"Some text content"), "text/plain")}
    )
    assert response.status_code == 415
    assert response.json() == {"detail": "Unsupported file type. Only PDFs are allowed."}
    mock_process_pdf.assert_not_called()

def test_upload_pdf_file_size_exceeded():
    """Test upload with a file size exceeding the limit."""
    large_file = BytesIO(b"A" * (MAX_FILE_SIZE + 1))  # Create a large file
    response = client.post(
        "/v1/pdf",
        files={"file": ("large_test.pdf", large_file, "application/pdf")}
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "File size exceeds the 100 MB limit."}


@patch("main.process_pdf")
def test_upload_pdf_password_protected(mock_process_pdf, mock_pdf_file):
    """Test upload with a password-protected PDF."""
    from main import PDFPasswordProtectedError

    # Mock process_pdf to raise a password-protected exception
    mock_process_pdf.side_effect = PDFPasswordProtectedError("Password-protected PDF")

    response = client.post(
        "/v1/pdf",
        files={"file": ("protected.pdf", mock_pdf_file.file, "application/pdf")}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Password-protected PDF"}
