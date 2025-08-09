# 🚀 Grounded CV Generator MVP

A sophisticated agentic system built with LangChain that generates **grounded, truthful CVs** based on job requirements and actual candidate experience. This system uses RAG (Retrieval-Augmented Generation) to ensure all generated content is supported by real evidence from the candidate's CV.

## 🎯 Overview

This MVP implements a complete workflow for generating tailored CVs that are:
- **Grounded**: Every claim is supported by actual CV content
- **Truthful**: No fabrication or embellishment
- **Relevant**: Tailored to specific job requirements
- **Traceable**: Full evidence trail for every section

## 🏗️ Architecture

### Tech Stack
- **Backend**: Python + LangChain
- **Vector DB**: Qdrant (for RAG)
- **LLM**: OpenAI GPT-4
- **Document Parsing**: pdfplumber, python-docx
- **Embeddings**: OpenAI text-embedding-3-small
- **Job Data**: LinkedIn MCP server (mock implementation)

### System Components

```
📁 Project Structure
├── 📁 modules/
│   ├── 📁 cv_ingestion/     # CV parsing and indexing
│   ├── 📁 job_search/       # Job search via LinkedIn MCP
│   └── 📁 storage/          # Supabase integration (planned)
├── 📁 agents/
│   ├── 📁 job_breakdown/    # Job requirement analysis
│   ├── 📁 cv_matcher/       # RAG-based CV matching
│   └── 📁 cv_writer/        # Grounded CV generation
├── 📁 utils/
│   ├── qdrant_client.py     # Vector DB operations
│   ├── embeddings.py        # Embedding generation
│   └── cv_parser.py         # Document parsing
└── main.py                  # Main orchestrator
```

## 🔄 Workflow

### 1. CV Upload & Indexing
- Upload CV (PDF/DOCX)
- Parse and extract text
- Chunk into semantic segments
- Generate embeddings
- Store in Qdrant vector database

### 2. Job Search & Analysis
- Search for jobs via LinkedIn MCP
- Extract job descriptions
- Analyze requirements using LangChain
- Structure into: skills, experience, qualifications

### 3. CV Matching (RAG)
- For each job requirement:
  - Generate embedding
  - Query Qdrant for relevant CV chunks
  - Return evidence with similarity scores

### 4. Grounded CV Generation
- Use only retrieved evidence
- Generate CV sections with traceable sources
- Ensure no fabrication or embellishment

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd Apps/1.Aligna

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `env.example` to `.env` and configure:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Qdrant Configuration
QDRANT_URL=your_qdrant_url_here
QDRANT_API_KEY=your_qdrant_api_key_here

# Supabase Configuration (for future use)
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

### 3. Run the System

```python
from main import GroundedCVGenerator

# Initialize the system
generator = GroundedCVGenerator()

# Run complete workflow
result = generator.run_complete_workflow(
    cv_file_path="path/to/your/cv.pdf",
    user_id="user_123",
    job_title="Software Engineer",
    location="San Francisco, CA"
)

if result["status"] == "success":
    print("Generated CV:")
    print(result["final_result"]["cv_text"])
```

## 📋 API Reference

### GroundedCVGenerator

Main orchestrator class that manages the entire workflow.

#### Methods

- `process_cv_upload(file_path, user_id, cv_id=None)`: Process CV upload
- `search_and_analyze_job(job_title, location, job_id=None)`: Search and analyze jobs
- `match_cv_to_job(cv_id, user_id, job_requirements)`: Match CV to job requirements
- `generate_grounded_cv(cv_id, user_id, job_requirements, cv_matches, contact_info)`: Generate grounded CV
- `run_complete_workflow(cv_file_path, user_id, job_title, location)`: Run complete workflow

### CVProcessor

Handles CV parsing, chunking, embedding, and storage.

### JobAnalyzer

Uses LangChain to extract structured requirements from job descriptions.

### CVMatcher

Performs RAG-based matching between job requirements and CV content.

### CVWriter

Generates grounded CVs using only evidence from the original CV.

## 🔍 Key Features

### ✅ Grounded Generation
- All CV content is supported by actual evidence
- No fabrication or embellishment
- Full traceability of sources

### ✅ RAG-Powered Matching
- Semantic similarity search in Qdrant
- Evidence-based requirement matching
- Configurable similarity thresholds

### ✅ Structured Job Analysis
- LangChain-powered requirement extraction
- Categorized skills, experience, qualifications
- Industry and level detection

### ✅ Modular Architecture
- Clean separation of concerns
- Easy to extend and modify
- Testable components

### ✅ Evidence Reporting
- Complete audit trail
- Source attribution for every claim
- Similarity scores and relevance metrics

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Test individual components
python -m pytest tests/test_cv_processor.py
python -m pytest tests/test_job_analyzer.py
python -m pytest tests/test_cv_matcher.py
```

## 🔮 Future Enhancements

### Post-MVP Features
- **User Authentication**: Supabase Auth integration
- **CV Scoring**: Feedback loop for improvement
- **Frontend Interface**: Drag-and-drop uploads
- **Multi-job Comparison**: Compare multiple positions
- **Interview Prep**: AI-powered interview preparation
- **Real LinkedIn Integration**: Replace mock job search

### Advanced Features
- **Multi-language Support**: CV parsing in multiple languages
- **Industry-specific Templates**: Tailored CV formats
- **Collaborative Editing**: Real-time CV collaboration
- **Analytics Dashboard**: Usage and performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **LangChain**: For the powerful LLM orchestration framework
- **Qdrant**: For the excellent vector database
- **OpenAI**: For the GPT models and embeddings
- **LinkedIn MCP Server**: For job data integration

---

**Note**: This is an MVP implementation. The LinkedIn MCP server integration is currently mocked for demonstration purposes. In production, you would integrate with the actual `linkedin-mcpserver` for real job data.
