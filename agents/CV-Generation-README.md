# Aligna CV Generation with Coral Protocol

This guide explains how to use the integrated Aligna CV generation system with Coral Protocol agents for grounded, evidence-based CV creation.

## 🎯 Overview

The Aligna CV generation system now includes specialized Coral Protocol agents that work together to create truthful, grounded CVs based on actual candidate experience and job requirements.

### Agent Architecture

```
User Request → CV Interface Agent → Coral Server
                     ↓
    ┌─────────────────┼─────────────────┐
    ↓                 ↓                 ↓
CV Analyzer      CV Matcher       CV Writer
    ↓                 ↓                 ↓
Job Analysis     RAG Evidence    Grounded CV
```

## 🤖 Available Agents

### 1. CV Interface Agent (`5_langchain_cv_interface_agent.py`)
- **Role**: Orchestrates the complete CV generation workflow
- **Capabilities**: User interaction, CV upload processing, workflow coordination
- **Tools**: CV processing, human interaction, agent coordination

### 2. CV Analyzer Agent (`2_langchain_cv_analyzer_agent.py`)
- **Role**: Analyzes job descriptions and extracts structured requirements
- **Capabilities**: Job requirement extraction, skills analysis, industry detection
- **Tools**: LangChain JobAnalyzer integration

### 3. CV Matcher Agent (`3_langchain_cv_matcher_agent.py`)
- **Role**: Matches CV content against job requirements using RAG
- **Capabilities**: Qdrant vector search, similarity scoring, evidence collection
- **Tools**: RAG-based matching with full traceability

### 4. CV Writer Agent (`4_langchain_cv_writer_agent.py`)
- **Role**: Generates grounded CV content using only retrieved evidence
- **Capabilities**: Evidence-based generation, grounding validation, traceability
- **Tools**: Template-based CV generation with safety guards

## 🚀 Getting Started

### Prerequisites

1. **Coral Server Running**:
   ```bash
   ./gradlew run
   ```

2. **Environment Variables Set**:
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   QDRANT_URL=http://qdrant.marvn.club:6333/
   WORLD_NEWS_API_KEY=your_world_news_api_key  # Optional
   ```

3. **Dependencies Installed**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the CV Generation System

#### Step 1: Start All Agents (in separate terminals)

```bash
# Terminal 1: CV Interface Agent (Main coordinator)
python agents/5_langchain_cv_interface_agent.py

# Terminal 2: CV Analyzer Agent
python agents/2_langchain_cv_analyzer_agent.py

# Terminal 3: CV Matcher Agent
python agents/3_langchain_cv_matcher_agent.py

# Terminal 4: CV Writer Agent
python agents/4_langchain_cv_writer_agent.py

# Terminal 5: World News Agent (Optional - for testing)
python agents/1_langchain_world_news_agent.py
```

#### Step 2: Interact with the System

The CV Interface Agent will prompt you:

```
CV Interface Agent asks: How can I assist you with CV generation today?
```

## 📋 Complete CV Generation Workflow

### Example Interaction

1. **Initial Request**:
   ```
   User: I need to generate a CV for a Software Engineer position
   ```

2. **CV Upload**:
   ```
   Agent: Please provide the path to your CV file
   User: /path/to/your/cv.pdf
   ```

3. **Job Description**:
   ```
   Agent: Please provide the job description or job requirements
   User: [Paste job description here]
   ```

4. **Automated Workflow**:
   - ✅ CV processed and indexed in Qdrant
   - ✅ Job description analyzed for requirements
   - ✅ CV content matched against requirements using RAG
   - ✅ Grounded CV generated with evidence
   - ✅ Results presented with traceability

### Sample Output

```json
{
  "cv_generation_status": "success",
  "cv_id": "uuid-here",
  "user_id": "user_123",
  "cv_text": "Generated CV content...",
  "evidence_report": "Evidence traceability report...",
  "grounding_statistics": {
    "total_sections": 5,
    "grounded_sections": 4,
    "grounding_score": 0.8,
    "ungrounded_sections": 1
  }
}
```

## 🔍 Key Features

### Evidence-Based Generation
- **No Fabrication**: Only uses actual CV content
- **Full Traceability**: Every claim linked to source
- **Grounding Scores**: Quality metrics for generated content

### RAG-Powered Matching
- **Vector Search**: Semantic similarity in Qdrant
- **Relevance Scoring**: Confidence metrics for matches
- **Context Preservation**: Maintains source attribution

### Multi-Agent Coordination
- **Thread-Based Communication**: Structured agent interactions
- **Mention System**: Targeted agent activation
- **Error Handling**: Graceful failure recovery

## 🛡️ Safety & Quality

### Grounding Validation
- **Evidence Requirements**: All content must have supporting evidence
- **Similarity Thresholds**: Configurable quality gates
- **Ungrounded Handling**: Clear marking of unsupported claims

### Quality Metrics
- **Match Rates**: Percentage of requirements matched
- **Grounding Scores**: Evidence coverage metrics
- **Source Attribution**: Full audit trail

## 🔧 Configuration

### Agent Parameters

Each agent can be configured via environment variables or parameters:

```python
# CV Matcher Agent
top_k = 5  # Number of evidence chunks per requirement
similarity_threshold = 0.7  # Minimum similarity score

# CV Writer Agent
grounding_required = True  # Require evidence for all content
template_style = "professional"  # CV template style
```

### Coral Server Settings

```python
base_url = "http://localhost:5555/devmode/exampleApplication/privkey/session1/sse"
waitForAgents = 5  # Wait for all CV agents to be ready
timeout = 300  # Connection timeout in seconds
```

## 🧪 Testing

### Individual Agent Testing

Test each agent independently:

```bash
# Test CV Analyzer
python -c "
from agents.job_breakdown.job_analyzer import JobAnalyzer
analyzer = JobAnalyzer()
result = analyzer.analyze_job_description('Software Engineer job...')
print(result.dict())
"

# Test CV Matcher
python -c "
from agents.cv_matcher.cv_matcher import CVMatcher
matcher = CVMatcher()
# ... test matching logic
"
```

### End-to-End Testing

1. Start all agents
2. Use the CV Interface Agent
3. Provide test CV and job description
4. Verify complete workflow execution

## 🚨 Troubleshooting

### Common Issues

1. **Agent Connection Failures**:
   - Ensure Coral server is running
   - Check network connectivity
   - Verify agent registration

2. **CV Processing Errors**:
   - Validate CV file format (PDF/DOCX)
   - Check Qdrant connectivity
   - Verify OpenAI API key

3. **Low Grounding Scores**:
   - Review CV content quality
   - Adjust similarity thresholds
   - Check job requirement specificity

### Debug Mode

Enable verbose logging:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Performance Metrics

### Expected Performance
- **CV Processing**: 30-60 seconds for typical CV
- **Job Analysis**: 10-20 seconds for job description
- **CV Matching**: 20-40 seconds for RAG search
- **CV Generation**: 30-60 seconds for complete CV

### Optimization Tips
- Use local Qdrant instance for faster vector search
- Cache embeddings for repeated job requirements
- Batch process multiple CVs for efficiency

## 🔮 Future Enhancements

### Planned Features
- **LinkedIn Integration**: Real job search via LinkedIn MCP
- **Multi-language Support**: CV generation in multiple languages
- **Industry Templates**: Specialized CV formats
- **Batch Processing**: Multiple CV generation
- **Analytics Dashboard**: Usage metrics and insights

### Integration Opportunities
- **Web Interface**: Streamlit integration with Coral agents
- **API Gateway**: RESTful API for external integrations
- **Workflow Templates**: Configurable generation workflows

## 📚 Additional Resources

- [Coral Protocol Documentation](https://github.com/coral-protocol/coral)
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
- [Aligna Main Documentation](../README.md)
- [Agent Implementation Guide](Agent-README.md)

---

*This CV generation system represents a sophisticated approach to evidence-based CV creation, ensuring truthfulness and traceability while leveraging the power of multi-agent coordination through Coral Protocol.*
