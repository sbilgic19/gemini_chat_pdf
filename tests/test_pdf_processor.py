import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from pypdf import PdfReader

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pdf_processor import (
    preprocess_text,
    process_metadata,
    extract_text_with_ocr,
    process_pdf,
    get_text_chunks,
    PDFPasswordProtectedError,
)



def test_preprocess_text():
    """Test text preprocessing to clean and format extracted text."""
    raw_text = "  This is a   sample   text.\n\nIt has extra spaces.  "
    expected_output = "This is a sample text. It has extra spaces."
    assert preprocess_text(raw_text) == expected_output


def test_process_metadata():
    """Test metadata processing and JSON serialization."""
    metadata = {"Author": "John Doe", "Title": "Sample PDF", "Producer": None}
    expected_output = (
        '{\n    "Author": "John Doe",\n    "Title": "Sample PDF",\n    "Producer": ""\n}'
    )
    assert process_metadata(metadata) == expected_output

    # Test empty metadata
    assert process_metadata(None) == "{}"


@patch("pdf_processor.convert_from_bytes")
@patch("pdf_processor.pytesseract.image_to_string")
def test_extract_text_with_ocr(mock_image_to_string, mock_convert_from_bytes):
    """Test text extraction using OCR."""
    mock_image_to_string.return_value = "Mock OCR text"
    mock_convert_from_bytes.return_value = [MagicMock()] * 3  # Simulate 3 pages

    pdf_stream = BytesIO(b"%PDF-1.4\n%Mock PDF Content\n")
    extracted_text = extract_text_with_ocr(pdf_stream)

    assert extracted_text == "Mock OCR textMock OCR textMock OCR text"
    mock_image_to_string.assert_called()
    mock_convert_from_bytes.assert_called_once()


@patch("pdf_processor.PdfReader")
def test_process_pdf_success(mock_pdf_reader):
    """Test successful PDF processing."""
    mock_reader_instance = MagicMock()
    mock_pdf_reader.return_value = mock_reader_instance
    mock_reader_instance.pages = [MagicMock(), MagicMock()]
    mock_reader_instance.pages[0].extract_text.return_value = "Page 1 text."
    mock_reader_instance.pages[1].extract_text.return_value = "Page 2 text."
    mock_reader_instance.metadata = {"Author": "Test Author"}

    pdf_stream = BytesIO(b"%PDF-1.4\n%Mock PDF Content\n")
    result = process_pdf(pdf_stream)

    assert result["text"] == "Page 1 text.Page 2 text."
    assert result["metadata"] == {"Author": "Test Author"}
    mock_pdf_reader.assert_called_once()


@patch("pdf_processor.PdfReader")
def test_process_pdf_password_protected(mock_pdf_reader):
    """Test handling of password-protected PDFs."""
    mock_reader_instance = MagicMock()
    mock_pdf_reader.return_value = mock_reader_instance
    mock_reader_instance.is_encrypted = True
    mock_reader_instance.decrypt.return_value = False  # Simulate failed decryption

    pdf_stream = BytesIO(b"%PDF-1.4\n%Mock PDF Content\n")

    with pytest.raises(PDFPasswordProtectedError, match="PDF is password protected"):
        process_pdf(pdf_stream)


@patch("pdf_processor.PdfReader")
@patch("pdf_processor.extract_text_with_ocr")
def test_process_pdf_ocr_fallback(mock_extract_text_with_ocr, mock_pdf_reader):
    """Test OCR fallback when text extraction fails."""
    mock_reader_instance = MagicMock()
    mock_pdf_reader.return_value = mock_reader_instance
    mock_reader_instance.pages = [MagicMock()]
    mock_reader_instance.pages[0].extract_text.return_value = None  # Simulate no text
    mock_reader_instance.metadata = None
    mock_extract_text_with_ocr.return_value = "OCR extracted text."

    pdf_stream = BytesIO(b"%PDF-1.4\n%Mock PDF Content\n")
    result = process_pdf(pdf_stream)

    assert result["text"] == "OCR extracted text."
    assert result["metadata"] == {}
    mock_extract_text_with_ocr.assert_called_once()


def test_get_text_chunks():
    """Test splitting text into chunks."""
    text = "This is a sample text. " * 100  # Create a long string
    chunks = get_text_chunks(text)

    assert len(chunks) > 1  # Ensure text is split into multiple chunks
    assert all(len(chunk) <= 1000 for chunk in chunks)  # Ensure chunk size limit
