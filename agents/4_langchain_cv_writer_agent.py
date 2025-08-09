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

from agents.cv_writer.cv_writer import CVWriter
from agents.job_breakdown.job_analyzer import JobRequirements

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

base_url = "http://localhost:5555/devmode/exampleApplication/privkey/session1/sse"
params = {
    "waitForAgents": 2,
    "agentId": "cv_writer_agent",
    "agentDescription": "You are cv_writer_agent, responsible for generating grounded CV content using only evidence from CV matching results"
}
query_string = urllib.parse.urlencode(params)
MCP_SERVER_URL = f"{base_url}?{query_string}"

AGENT_NAME = "cv_writer_agent"

# Validate API keys
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in environment variables.")

def get_tools_description(tools):
    return "\n".join(
        f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
        for tool in tools
    )

@tool
def GenerateGroundedCVTool(
    job_requirements: str,
    cv_matches: str,
    contact_info: str = "{}",
    cv_id: str = "",
    user_id: str = ""
):
    """
    Generate a grounded CV using only evidence from CV matching results.

    Args:
        job_requirements: JSON string of structured job requirements
        cv_matches: JSON string of CV matching results with evidence
        contact_info: JSON string of contact information (default: empty)
        cv_id: CV identifier for reference
        user_id: User identifier for reference

    Returns:
        dict: Contains generated CV text, evidence report, and grounding information
    """
    logger.info(f"Generating grounded CV for user {user_id}, CV {cv_id}")
    
    try:
        # Parse input data
        requirements_data = json.loads(job_requirements)
        job_requirements_obj = JobRequirements(**requirements_data)
        
        matches_data = json.loads(cv_matches)
        contact_data = json.loads(contact_info) if contact_info else {}
        
        # Initialize the CV Writer
        cv_writer = CVWriter()
        
        # Generate the grounded CV
        generated_cv = cv_writer.generate_cv(
            job_requirements=job_requirements_obj,
            cv_matches=matches_data,
            contact_info=contact_data,
            cv_id=cv_id,
            user_id=user_id
        )
        
        # Generate text versions
        cv_text = cv_writer.generate_cv_text(generated_cv)
        evidence_report = cv_writer.generate_cv_with_evidence_report(generated_cv)
        
        # Calculate grounding statistics
        total_sections = len(generated_cv.sections)
        grounded_sections = sum(1 for section in generated_cv.sections if section.grounded)
        grounding_score = grounded_sections / total_sections if total_sections > 0 else 0
        
        result = {
            "cv_generation_status": "success",
            "cv_id": cv_id,
            "user_id": user_id,
            "generated_cv": generated_cv.dict(),
            "cv_text": cv_text,
            "evidence_report": evidence_report,
            "grounding_statistics": {
                "total_sections": total_sections,
                "grounded_sections": grounded_sections,
                "grounding_score": grounding_score,
                "ungrounded_sections": total_sections - grounded_sections
            },
            "generated_at": generated_cv.generated_at.isoformat()
        }
        
        logger.info(f"CV generation completed: {grounded_sections}/{total_sections} sections grounded ({grounding_score:.2%})")
        
        return {"result": json.dumps(result, indent=2, default=str)}
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input data: {str(e)}")
        return {
            "result": json.dumps({
                "cv_generation_status": "error",
                "error": f"Invalid input JSON: {str(e)}",
                "cv_id": cv_id,
                "user_id": user_id
            }, indent=2)
        }
    except Exception as e:
        logger.error(f"Error generating grounded CV: {str(e)}")
        return {
            "result": json.dumps({
                "cv_generation_status": "error",
                "error": str(e),
                "cv_id": cv_id,
                "user_id": user_id
            }, indent=2)
        }

async def create_cv_writer_agent(client, tools, agent_tool):
    tools_description = get_tools_description(tools)
    agent_tools_description = get_tools_description(agent_tool)
    
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""You are an agent specialized in generating grounded, truthful CV content using only evidence from CV matching results. You work with Coral Server tools and have your own CV generation capabilities.

            When you receive a mention with job requirements and CV matching results:
            1. Extract the following from the message content or payload:
               - Job requirements (structured JSON)
               - CV matching results with evidence
               - Contact information (optional)
               - CV ID and User ID
            2. Use your GenerateGroundedCVTool to create a grounded CV:
               - Generate CV sections using ONLY retrieved evidence
               - Ensure every claim is supported by actual CV content
               - Create evidence report with full traceability
               - Calculate grounding score and statistics
               - Never fabricate or embellish information
            3. Format the CV generation results including:
               - Complete CV text ready for use
               - Evidence report with source attribution
               - Grounding statistics and quality metrics
               - Sections that couldn't be grounded (if any)
            4. Use `send_message` from coral tools to send the generated CV back to the sender in the same thread.
            5. If any error occurs, send an error message with details to the sender.
            6. Always respond back to the sender agent even if generation fails.

            Your CV generation tool: {agent_tools_description}
            All available tools: {tools_description}
            
            CRITICAL: You must NEVER fabricate information. Only use evidence from the CV matching results. If no evidence exists for a requirement, clearly mark it as ungrounded or use a placeholder."""
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
            tools = coral_tools + [GenerateGroundedCVTool]
            agent_tool = [GenerateGroundedCVTool]
            
            agent_executor = await create_cv_writer_agent(client, tools, agent_tool)
            
            # Get the wait_for_mentions tool directly
            wait_for_mentions_tool = None
            for tool in coral_tools:
                if tool.name == "wait_for_mentions":
                    wait_for_mentions_tool = tool
                    break
            
            if not wait_for_mentions_tool:
                logger.error("wait_for_mentions tool not found in coral tools")
                raise Exception("Required coral tool 'wait_for_mentions' not available")
            
            logger.info("CV Writer Agent: Ready and waiting for mentions...")
            
            while True:
                try:
                    # Wait for mentions without making OpenAI calls
                    logger.info("Waiting for mentions...")
                    mentions_result = await wait_for_mentions_tool.acall({"timeoutMs": 8000})
                    
                    if mentions_result and mentions_result.get("mentions"):
                        logger.info(f"Received {len(mentions_result['mentions'])} mentions, processing...")
                        # Only invoke agent executor when we have actual work
                        await agent_executor.ainvoke({"mentions": mentions_result})
                        logger.info("Completed CV generation")
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
