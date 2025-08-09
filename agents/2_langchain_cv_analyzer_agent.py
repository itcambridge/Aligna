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
from langchain_core.tools import tool
from dotenv import load_dotenv
from anyio import ClosedResourceError
import urllib.parse

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.job_breakdown.job_analyzer import JobAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

base_url = "http://localhost:5555/devmode/exampleApplication/privkey/session1/sse"
params = {
    "waitForAgents": 2,
    "agentId": "cv_analyzer_agent",
    "agentDescription": "You are cv_analyzer_agent, responsible for analyzing job descriptions and extracting structured requirements using LangChain JobAnalyzer"
}
query_string = urllib.parse.urlencode(params)
MCP_SERVER_URL = f"{base_url}?{query_string}"

AGENT_NAME = "cv_analyzer_agent"

# Validate API keys
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables.")

def get_tools_description(tools):
    return "\n".join(
        f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
        for tool in tools
    )

@tool
def AnalyzeJobDescriptionTool(job_description: str, job_title: str = "", company: str = ""):
    """
    Analyze a job description and extract structured requirements.

    Args:
        job_description: The full job description text to analyze
        job_title: Optional job title for context
        company: Optional company name for context

    Returns:
        dict: Contains structured job requirements including skills, experience, qualifications
    """
    logger.info(f"Analyzing job description for: {job_title} at {company}")
    
    try:
        # Initialize the JobAnalyzer
        job_analyzer = JobAnalyzer()
        
        # Analyze the job description
        job_requirements = job_analyzer.analyze_job_description(job_description)
        
        # Generate job summary
        job_summary = job_analyzer.generate_job_summary(job_requirements)
        
        # Convert to dict for JSON serialization
        result = {
            "job_requirements": job_requirements.dict(),
            "job_summary": job_summary,
            "job_title": job_title,
            "company": company,
            "analysis_status": "success"
        }
        
        logger.info(f"Successfully analyzed job description. Found {len(job_requirements.skills_required)} required skills")
        return {"result": json.dumps(result, indent=2)}
        
    except Exception as e:
        logger.error(f"Error analyzing job description: {str(e)}")
        return {
            "result": json.dumps({
                "analysis_status": "error",
                "error": str(e),
                "job_title": job_title,
                "company": company
            }, indent=2)
        }

async def create_cv_analyzer_agent(client, tools, agent_tool):
    tools_description = get_tools_description(tools)
    agent_tools_description = get_tools_description(agent_tool)
    
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""You are an agent specialized in analyzing job descriptions and extracting structured requirements. You work with Coral Server tools and have your own job analysis capabilities.

            When you receive a mention with a job description:
            1. Extract the job description from the message content or payload.
            2. Use your AnalyzeJobDescriptionTool to analyze the job description and extract:
               - Required skills
               - Preferred skills  
               - Experience requirements
               - Qualifications
               - Industry and level information
            3. Format the analysis results as a clear, structured response.
            4. Use `send_message` from coral tools to send the analysis results back to the sender in the same thread.
            5. If any error occurs, send an error message with details to the sender.
            6. Always respond back to the sender agent even if analysis fails.

            Your job analysis tool: {agent_tools_description}
            All available tools: {tools_description}
            
            Remember: You are focused on job analysis only. Extract structured requirements that can be used for CV matching."""
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
            tools = coral_tools + [AnalyzeJobDescriptionTool]
            agent_tool = [AnalyzeJobDescriptionTool]
            
            agent_executor = await create_cv_analyzer_agent(client, tools, agent_tool)
            
            # Get the wait_for_mentions tool directly
            wait_for_mentions_tool = None
            for tool in coral_tools:
                if tool.name == "wait_for_mentions":
                    wait_for_mentions_tool = tool
                    break
            
            if not wait_for_mentions_tool:
                logger.error("wait_for_mentions tool not found in coral tools")
                raise Exception("Required coral tool 'wait_for_mentions' not available")
            
            logger.info("CV Analyzer Agent: Ready and waiting for mentions...")
            
            while True:
                try:
                    # Wait for mentions without making OpenAI calls
                    logger.info("Waiting for mentions...")
                    mentions_result = await wait_for_mentions_tool.acall({"timeoutMs": 8000})
                    
                    if mentions_result and mentions_result.get("mentions"):
                        logger.info(f"Received {len(mentions_result['mentions'])} mentions, processing...")
                        # Only invoke agent executor when we have actual work
                        await agent_executor.ainvoke({"mentions": mentions_result})
                        logger.info("Completed job analysis")
                    else:
                        logger.debug("No mentions received, continuing to wait...")
                    
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error in agent loop: {str(e)}")
                    await asyncio.sleep(5)
                        
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
