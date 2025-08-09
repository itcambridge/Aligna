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

from agents.cv_matcher.cv_matcher import CVMatcher
from agents.job_breakdown.job_analyzer import JobRequirements

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

base_url = "http://localhost:5555/devmode/exampleApplication/privkey/session1/sse"
params = {
    "waitForAgents": 2,
    "agentId": "cv_matcher_agent",
    "agentDescription": "You are cv_matcher_agent, responsible for matching CV content against job requirements using RAG and Qdrant vector search"
}
query_string = urllib.parse.urlencode(params)
MCP_SERVER_URL = f"{base_url}?{query_string}"

AGENT_NAME = "cv_matcher_agent"

# Validate API keys
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables.")

def get_tools_description(tools):
    return "\n".join(
        f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
        for tool in tools
    )

@tool
def MatchCVToJobTool(
    job_requirements: str,
    user_id: str,
    cv_id: str,
    top_k: int = 5,
    similarity_threshold: float = 0.7
):
    """
    Match CV content against job requirements using RAG and Qdrant vector search.

    Args:
        job_requirements: JSON string of structured job requirements
        user_id: User identifier for CV filtering
        cv_id: CV identifier for specific CV matching
        top_k: Number of top matches to return per requirement (default: 5)
        similarity_threshold: Minimum similarity score for matches (default: 0.7)

    Returns:
        dict: Contains matching results with evidence, scores, and match rate
    """
    logger.info(f"Matching CV {cv_id} for user {user_id} against job requirements")
    
    try:
        # Parse job requirements from JSON
        requirements_data = json.loads(job_requirements)
        job_requirements_obj = JobRequirements(**requirements_data)
        
        # Initialize the CV Matcher
        cv_matcher = CVMatcher()
        
        # Perform the matching
        matches = cv_matcher.match_job_requirements(
            job_requirements=job_requirements_obj,
            cv_id=cv_id,
            user_id=user_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        # Add metadata
        matches["matching_parameters"] = {
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "cv_id": cv_id,
            "user_id": user_id
        }
        
        match_rate = matches.get("summary", {}).get("match_rate", 0)
        total_requirements = matches.get("summary", {}).get("total_requirements", 0)
        matched_requirements = matches.get("summary", {}).get("matched_requirements", 0)
        
        logger.info(f"CV matching completed: {matched_requirements}/{total_requirements} requirements matched ({match_rate:.2%})")
        
        return {"result": json.dumps(matches, indent=2, default=str)}
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in job_requirements: {str(e)}")
        return {
            "result": json.dumps({
                "matching_status": "error",
                "error": f"Invalid job requirements JSON: {str(e)}",
                "cv_id": cv_id,
                "user_id": user_id
            }, indent=2)
        }
    except Exception as e:
        logger.error(f"Error matching CV to job: {str(e)}")
        return {
            "result": json.dumps({
                "matching_status": "error",
                "error": str(e),
                "cv_id": cv_id,
                "user_id": user_id
            }, indent=2)
        }

async def create_cv_matcher_agent(client, tools, agent_tool):
    tools_description = get_tools_description(tools)
    agent_tools_description = get_tools_description(agent_tool)
    
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""You are an agent specialized in matching CV content against job requirements using RAG (Retrieval-Augmented Generation) and Qdrant vector search. You work with Coral Server tools and have your own CV matching capabilities.

            When you receive a mention with job requirements and CV information:
            1. Extract the following from the message content or payload:
               - Job requirements (structured JSON)
               - User ID
               - CV ID
               - Optional: top_k and similarity_threshold parameters
            2. Use your MatchCVToJobTool to perform RAG-based matching:
               - Search Qdrant vector database for relevant CV chunks
               - Calculate similarity scores for each requirement
               - Collect evidence with source attribution
               - Generate match rate and coverage analysis
            3. Format the matching results including:
               - Match scores for each requirement
               - Supporting evidence from CV with chunk references
               - Overall match rate and statistics
               - Unmatched requirements (if any)
            4. Use `send_message` from coral tools to send the matching results back to the sender in the same thread.
            5. If any error occurs, send an error message with details to the sender.
            6. Always respond back to the sender agent even if matching fails.

            Your CV matching tool: {agent_tools_description}
            All available tools: {tools_description}
            
            Remember: You provide evidence-based matching using RAG. Every match must include source attribution (cv_id, chunk_index, similarity_score) for traceability."""
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
            tools = coral_tools + [MatchCVToJobTool]
            agent_tool = [MatchCVToJobTool]
            
            agent_executor = await create_cv_matcher_agent(client, tools, agent_tool)
            
            # Get the wait_for_mentions tool directly
            wait_for_mentions_tool = None
            for tool in coral_tools:
                if tool.name == "wait_for_mentions":
                    wait_for_mentions_tool = tool
                    break
            
            if not wait_for_mentions_tool:
                logger.error("wait_for_mentions tool not found in coral tools")
                raise Exception("Required coral tool 'wait_for_mentions' not available")
            
            logger.info("CV Matcher Agent: Ready and waiting for mentions...")
            
            while True:
                try:
                    # Wait for mentions without making OpenAI calls
                    logger.info("Waiting for mentions...")
                    mentions_result = await wait_for_mentions_tool.acall({"timeoutMs": 8000})
                    
                    if mentions_result and mentions_result.get("mentions"):
                        logger.info(f"Received {len(mentions_result['mentions'])} mentions, processing...")
                        # Only invoke agent executor when we have actual work
                        await agent_executor.ainvoke({"mentions": mentions_result})
                        logger.info("Completed CV matching")
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
