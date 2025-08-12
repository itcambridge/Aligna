from export.cv_exporter import CVExporter
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create exports directory
os.makedirs("exports", exist_ok=True)

# Create a simple CV data structure
cv_data = {
    "contact_info": {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "123-456-7890",
        "location": "Test City"
    },
    "summary": {
        "content": "This is a test summary."
    },
    "experience": {
        "content": "• Test experience 1\n• Test experience 2"
    },
    "skills": {
        "content": "• Test skill 1\n• Test skill 2"
    },
    "education": {
        "content": "• Test education"
    }
}

# Create exporter
exporter = CVExporter()

# Export as DOCX
docx_result = exporter.export_cv(
    cv_data=cv_data,
    template_id="classic",
    output_format="docx"
)

print(f"DOCX Export result: {docx_result}")
print(f"DOCX File path: {docx_result.get('file_path')}")

# Export as PDF
pdf_result = exporter.export_cv(
    cv_data=cv_data,
    template_id="classic",
    output_format="pdf"
)

print(f"PDF Export result: {pdf_result}")
print(f"PDF File path: {pdf_result.get('file_path')}")

# Export as Text
text_result = exporter.export_cv(
    cv_data=cv_data,
    template_id="classic",
    output_format="text"
)

print(f"Text Export result: {text_result}")
print(f"Text File path: {text_result.get('file_path')}")

# Check if files were created
for result in [docx_result, pdf_result, text_result]:
    file_path = result.get('file_path')
    if file_path and os.path.exists(file_path):
        print(f"File exists: {file_path}")
        print(f"File size: {os.path.getsize(file_path)} bytes")
    else:
        print(f"File does not exist: {file_path}")
