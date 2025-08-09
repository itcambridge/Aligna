# Coral Protocol Integration for Aligna

This directory contains the Coral Protocol integration for Aligna's multi-agent CV generation system. Coral provides thread-based messaging and agent orchestration capabilities that complement the existing LangChain-based agents.

## 🎯 Overview

The Coral integration allows Aligna to use **Coral Protocol** for multi-agent orchestration while keeping the existing LangChain agents for business logic. This provides:

- **Thread-based Communication**: Agents communicate through structured threads
- **Agent Registration**: Agents register their capabilities with the Coral server
- **Message Routing**: Intelligent routing of requests between agents
- **Evidence Traceability**: Full audit trail of agent interactions
- **Scalable Architecture**: Easy to add new agents and capabilities

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Request  │───▶│  Coral Server   │───▶│ Interface Agent │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Thread      │    │  LinkedIn Agent │
                       │   Management    │    │   (MCP Server)  │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Agent Adapters  │    │ Job Analyzer    │
                       │   (FastAPI)     │    │    Agent        │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  CV Matcher     │    │   CV Writer     │
                       │     Agent       │    │     Agent       │
                       └─────────────────┘    └─────────────────┘
```

## 📁 Directory Structure

```
coral/
├── __init__.py              # Package initialization
├── README.md               # This file
├── coral_client.py         # HTTP client for Coral server
├── schemas.py              # Pydantic message contracts
├── registry.json           # Agent registry configuration
└── adapters/               # Agent adapters (to be created)
    ├── job_analyzer_adapter.py
    ├── cv_matcher_adapter.py
    ├── cv_writer_adapter.py
    └── interface_adapter.py
```

## 🔧 Components

### 1. CoralClient (`coral_client.py`)

HTTP client for communicating with the Coral Protocol server.

**Key Methods**:
- `health_check()` - Check server health
- `create_thread()` - Create new communication thread
- `send_message()` - Send message to thread
- `mention_agent()` - Mention specific agent
- `register_agent()` - Register agent with server
- `wait_for_response()` - Wait for agent responses

### 2. Message Schemas (`schemas.py`)

Pydantic models for structured communication between agents.

**Key Schemas**:
- `ThreadMessage` - Base message structure
- `JobRequirements` - Structured job requirements
- `CVMatchResponse` - CV matching results with evidence
- `CVDraft` - Generated CV with traceability
- `AgentHandleRequest/Response` - Agent adapter contracts

### 3. Agent Registry (`registry.json`)

Configuration file defining all agents, their capabilities, and workflows.

**Registered Agents**:
- **job_analyzer** - Extracts structured requirements from job descriptions
- **cv_matcher** - Matches CV content against job requirements using RAG
- **cv_writer** - Generates grounded CV sections with evidence
- **linkedin_agent** - Searches jobs via LinkedIn MCP server
- **interface_agent** - Routes requests and coordinates workflow

## 🚀 Getting Started

### 1. Environment Setup

Ensure your `.env` file includes Coral configuration:

```bash
# Orchestration Configuration
ORCHESTRATOR=coral  # Switch to coral mode

# Coral Protocol Configuration
CORAL_URL=http://localhost:8009
CORAL_API_KEY=your_coral_api_key_here

# LinkedIn MCP Configuration
LINKEDIN_MCP_URL=your_linkedin_mcp_url_here
LINKEDIN_MCP_TOKEN=your_linkedin_mcp_token_here
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Smoke Tests

Test the Coral integration:

```bash
python scripts/smoke_coral.py
```

This will test:
- ✅ Coral server health check
- ✅ Thread creation and management
- ✅ Message sending and retrieval
- ✅ Agent mentions and registration
- ✅ Basic communication flow

## 🔄 Workflow

### Complete CV Generation Flow

1. **User Request** → Interface Agent creates thread
2. **Job Search** → LinkedIn Agent fetches job description
3. **Job Analysis** → Job Analyzer extracts structured requirements
4. **CV Matching** → CV Matcher finds evidence using RAG (Qdrant)
5. **CV Generation** → CV Writer creates grounded CV with evidence
6. **Result Return** → Interface Agent returns CV and evidence report

### Message Flow Example

```python
# 1. Create thread
thread = coral_client.create_thread("Generate CV for Software Engineer")

# 2. Send initial request
coral_client.send_message(
    thread_id=thread["thread_id"],
    content="Generate CV for Software Engineer in San Francisco",
    agent_name="user",
    payload={
        "user_id": "user_123",
        "job_title": "Software Engineer",
        "location": "San Francisco, CA"
    }
)

# 3. Mention interface agent to start workflow
coral_client.mention_agent(
    thread_id=thread["thread_id"],
    agent_name="interface_agent",
    content="Please coordinate CV generation workflow",
    payload={"intent": "generate_cv"}
)
```

## 🧪 Testing

### Smoke Tests

Run basic connectivity and functionality tests:

```bash
python scripts/smoke_coral.py
```

### Integration Tests (Planned)

- End-to-end workflow testing
- Agent adapter testing
- Message contract validation
- Error handling and recovery

## 🔧 Configuration

### Agent Registration

Agents are automatically registered using the `registry.json` configuration. Each agent specifies:

- **Capabilities**: What the agent can do
- **Endpoint**: HTTP endpoint for the agent adapter
- **Intents**: Specific actions the agent handles
- **Description**: Human-readable description

### Message Types

- **REQUEST**: Initial request from user or system
- **MENTION**: Direct mention of specific agent
- **RESPONSE**: Response to a request or mention
- **RESULT**: Final result or artifact
- **ERROR**: Error message with details
- **SYSTEM**: System-level message

## 🔍 Key Features

### ✅ Implemented (Milestone 0-1)

- **Feature Flag Support**: `ORCHESTRATOR=langchain|coral`
- **Coral Client**: Full HTTP client for Coral server
- **Message Schemas**: Complete Pydantic contracts
- **Agent Registry**: Configuration-driven agent management
- **Smoke Tests**: Comprehensive connectivity testing
- **Backward Compatibility**: Existing LangChain workflow preserved

### 🚧 In Progress (Milestone 2-3)

- **Agent Adapters**: FastAPI adapters for existing agents
- **LinkedIn MCP Integration**: Real job search via MCP server
- **Interface Agent**: Workflow coordination agent

### 📋 Planned (Milestone 4-7)

- **Evidence Validation**: Grounding and safety guards
- **Supabase Integration**: Thread and workflow persistence
- **Comprehensive Testing**: Unit, integration, and E2E tests
- **Production Deployment**: Docker and monitoring setup

## 🛡️ Safety & Grounding

### Evidence Requirements

- **CV Writer** must require evidence for all generated content
- **No Fabrication**: Placeholders used when evidence is missing
- **Traceability**: Full source attribution with `cv_id`, `chunk_index`, `score`
- **Validation**: Contract validation prevents ungrounded generation

### Error Handling

- **Graceful Degradation**: Falls back to LangChain mode on Coral failure
- **Timeout Handling**: Configurable timeouts for agent responses
- **Retry Logic**: Automatic retry for transient failures
- **Error Reporting**: Structured error messages with context

## 🔮 Future Enhancements

### Post-MVP Features

- **Real-time Notifications**: WebSocket support for live updates
- **Agent Scaling**: Horizontal scaling of agent adapters
- **Workflow Templates**: Configurable workflow definitions
- **Performance Monitoring**: Agent latency and success metrics
- **Advanced Routing**: Intelligent agent selection based on capabilities

### Integration Opportunities

- **Coral Payments**: Integration with Coral's payment primitives
- **Multi-tenant Support**: User isolation and resource management
- **API Gateway**: Centralized API management and rate limiting
- **Analytics Dashboard**: Workflow analytics and optimization insights

## 📚 References

- [Coral Protocol Documentation](https://github.com/coral-protocol/coral)
- [LinkedIn MCP Server](https://github.com/felipfr/linkedin-mcpserver)
- [Aligna Main Documentation](../README.md)
- [New Roadmap](../New-Roadmap.md)

---

*This Coral integration maintains full backward compatibility while providing a path to modern multi-agent orchestration. The system can operate in either `langchain` or `coral` mode based on the `ORCHESTRATOR` environment variable.*
