import asyncio
import os
import json
import logging
import sys
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import Tool
from dotenv import load_dotenv
from anyio import ClosedResourceError
import urllib.parse

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.cv_ingestion.cv_processor import CVProcessor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

base_url = "http://localhost:5555/devmode/exampleApplication/privkey/session1/sse"
params = {
    "waitForAgents": 5,  # Wait for all CV agents
    "agentId": "cv_interface_agent",
    "agentDescription": "You are cv_interface_agent, responsible for coordinating CV generation workflows and managing user interactions for the Aligna CV system"
}
query_string = urllib.parse.urlencode(params)
MCP_SERVER_URL = f"{base_url}?{query_string}"

AGENT_NAME = "cv_interface_agent"

def get_tools_description(tools):
    return "\n".join(
        f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
        for tool in tools
    )

async def ask_human_tool(question: str) -> str:
    print(f"CV Interface Agent asks: {question}")
    return input("Your response: ")

async def process_cv_upload_tool(file_path: str, user_id: str) -> str:
    """Process CV upload and return CV ID."""
    try:
        cv_processor = CVProcessor()
        result = cv_processor.process_cv(file_path, user_id)
        
        if result["status"] == "success":
            return json.dumps({
                "status": "success",
                "cv_id": result["cv_id"],
                "user_id": user_id,
                "total_chunks": result["total_chunks"],
                "contact_info": result.get("contact_info", {}),
                "message": f"CV processed successfully with {result['total_chunks']} chunks"
            })
        else:
            return json.dumps({
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "user_id": user_id
            })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "user_id": user_id
        })

async def create_cv_interface_agent(client, tools):
    tools_description = get_tools_description(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""You are the CV Interface Agent for Aligna, a sophisticated CV generation system. You coordinate multi-agent workflows to generate grounded, truthful CVs based on job requirements and actual candidate experience.

            AVAILABLE AGENTS:
            - cv_analyzer_agent: Analyzes job descriptions and extracts structured requirements
            - cv_matcher_agent: Matches CV content against job requirements using RAG
            - cv_writer_agent: Generates grounded CV content using only evidence
            - world_news_agent: Provides news information (example agent)

            CV GENERATION WORKFLOW:
            1. Use `list_agents` to see all connected agents
            2. Use `ask_human` to ask "How can I assist you with CV generation today?"
            3. If user wants CV generation:
               a. Ask for CV file path and job description
               b. Process CV upload using process_cv_upload
               c. Create thread for CV generation workflow
               d. Mention cv_analyzer_agent with job description
               e. Wait for job analysis results
               f. Mention cv_matcher_agent with job requirements + CV info
               g. Wait for matching results with evidence
               h. Mention cv_writer_agent with requirements + matches
               i. Wait for final grounded CV
               j. Present complete results to user
            4. If user asks about other topics, route to appropriate agent
            5. Always show the complete conversation thread to the user
            6. Ask if they need anything else and repeat

            SAFETY RULES:
            - Only use evidence-based CV generation
            - Never fabricate CV content
            - Always provide traceability for generated content
            - Ensure grounding scores are reported
            - Handle errors gracefully

            Available tools: {tools_description}
            
            Remember: You are the orchestrator. Guide users through the CV generation process step by step."""
        ),
        ("placeholder", "{agent_scratchpad}")
    ])

    model = init_chat_model(
        model="gpt-4o-mini",
        model_provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
        max_tokens=16000
    )

    agent = create_tool_calling_agent(model, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

async def main():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Create client without context manager (new API)
            client = MultiServerMCPClient(
                connections={
                    "coral": {
                        "transport": "sse",
                        "url": MCP_SERVER_URL,
                        "timeout": 300,
                        "sse_read_timeout": 300,
                    }
                }
            )
            logger.info(f"Connected to MCP server at {MCP_SERVER_URL}")
            
            # Get tools using await (new API)
            coral_tools = await client.get_tools()
            
            # Add custom tools for CV processing
            tools = coral_tools + [
                Tool(
                    name="ask_human",
                    func=None,
                    coroutine=ask_human_tool,
                    description="Ask the user a question and wait for a response."
                ),
                Tool(
                    name="process_cv_upload",
                    func=None,
                    coroutine=process_cv_upload_tool,
                    description="Process CV file upload and return CV ID and metadata."
                )
            ]
            
            logger.info("CV Interface Agent: Starting CV generation coordination system...")
            await (await create_cv_interface_agent(client, tools)).ainvoke({})
                
        except ClosedResourceError as e:
            logger.error(f"ClosedResourceError on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info("Retrying in 5 seconds...")
                await asyncio.sleep(5)
                continue
            else:
                logger.error("Max retries reached. Exiting.")
                raise
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info("Retrying in 5 seconds...")
                await asyncio.sleep(5)
                continue
            else:
                logger.error("Max retries reached. Exiting.")
                raise

if __name__ == "__main__":
    asyncio.run(main())
