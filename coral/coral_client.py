"""
Coral Protocol HTTP client for thread-based agent communication.
"""

import os
import uuid
import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CoralClient:
    """HTTP client for Coral Protocol server communication."""
    
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize Coral client."""
        self.url = url or os.getenv("CORAL_URL", "http://localhost:8009")
        self.api_key = api_key or os.getenv("CORAL_API_KEY")
        
        # Remove trailing slash
        self.url = self.url.rstrip('/')
        
        # Setup session with headers
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Coral server is healthy."""
        try:
            response = self.session.get(f"{self.url}/health")
            response.raise_for_status()
            return {
                "status": "healthy",
                "server_url": self.url,
                "response": response.json() if response.content else {}
            }
        except Exception as e:
            logger.error(f"Coral health check failed: {e}")
            return {
                "status": "unhealthy",
                "server_url": self.url,
                "error": str(e)
            }
    
    def create_thread(self, title: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new thread for agent communication.
        
        Args:
            title: Thread title
            metadata: Optional metadata for the thread
            
        Returns:
            Thread creation response with thread_id
        """
        try:
            payload = {
                "title": title,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{self.url}/threads", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created thread: {result.get('thread_id', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            return {
                "error": str(e),
                "thread_id": None
            }
    
    def send_message(
        self,
        thread_id: str,
        content: str,
        agent_name: str,
        message_type: str = "message",
        payload: Optional[Dict[str, Any]] = None,
        mentions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a thread.
        
        Args:
            thread_id: Target thread ID
            content: Message content
            agent_name: Name of the sending agent
            message_type: Type of message (message, request, response, etc.)
            payload: Optional structured payload
            mentions: List of agent names to mention
            
        Returns:
            Message sending response
        """
        try:
            message_payload = {
                "thread_id": thread_id,
                "content": content,
                "agent_name": agent_name,
                "message_type": message_type,
                "payload": payload or {},
                "mentions": mentions or [],
                "timestamp": datetime.now().isoformat(),
                "message_id": str(uuid.uuid4())
            }
            
            response = self.session.post(
                f"{self.url}/threads/{thread_id}/messages",
                json=message_payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Sent message to thread {thread_id}: {content[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send message to thread {thread_id}: {e}")
            return {
                "error": str(e),
                "message_id": None
            }
    
    def get_thread_messages(
        self,
        thread_id: str,
        limit: int = 50,
        since: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get messages from a thread.
        
        Args:
            thread_id: Thread ID to fetch messages from
            limit: Maximum number of messages to return
            since: ISO timestamp to fetch messages since
            
        Returns:
            Thread messages response
        """
        try:
            params = {"limit": limit}
            if since:
                params["since"] = since
            
            response = self.session.get(
                f"{self.url}/threads/{thread_id}/messages",
                params=params
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Retrieved {len(result.get('messages', []))} messages from thread {thread_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get messages from thread {thread_id}: {e}")
            return {
                "error": str(e),
                "messages": []
            }
    
    def mention_agent(
        self,
        thread_id: str,
        agent_name: str,
        content: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Mention a specific agent in a thread.
        
        Args:
            thread_id: Thread ID
            agent_name: Agent to mention
            content: Message content
            payload: Optional structured payload for the agent
            
        Returns:
            Mention response
        """
        return self.send_message(
            thread_id=thread_id,
            content=f"@{agent_name} {content}",
            agent_name="system",
            message_type="mention",
            payload=payload,
            mentions=[agent_name]
        )
    
    def register_agent(
        self,
        agent_name: str,
        capabilities: List[str],
        endpoint: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register an agent with the Coral server.
        
        Args:
            agent_name: Unique agent name
            capabilities: List of agent capabilities
            endpoint: HTTP endpoint for the agent
            description: Optional agent description
            
        Returns:
            Registration response
        """
        try:
            payload = {
                "agent_name": agent_name,
                "capabilities": capabilities,
                "endpoint": endpoint,
                "description": description or f"Agent: {agent_name}",
                "registered_at": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{self.url}/agents/register", json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Registered agent: {agent_name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_name}: {e}")
            return {
                "error": str(e),
                "registered": False
            }
    
    def get_registered_agents(self) -> Dict[str, Any]:
        """Get list of registered agents."""
        try:
            response = self.session.get(f"{self.url}/agents")
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Retrieved {len(result.get('agents', []))} registered agents")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get registered agents: {e}")
            return {
                "error": str(e),
                "agents": []
            }
    
    def wait_for_response(
        self,
        thread_id: str,
        timeout: int = 30,
        expected_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Wait for a response in a thread (polling-based).
        
        Args:
            thread_id: Thread to monitor
            timeout: Timeout in seconds
            expected_agent: Optional specific agent to wait for
            
        Returns:
            Response message or timeout
        """
        import time
        
        start_time = time.time()
        last_check = datetime.now().isoformat()
        
        while time.time() - start_time < timeout:
            messages = self.get_thread_messages(thread_id, limit=10, since=last_check)
            
            if messages.get("error"):
                return messages
            
            for message in messages.get("messages", []):
                if expected_agent and message.get("agent_name") != expected_agent:
                    continue
                
                if message.get("message_type") in ["response", "result"]:
                    return {
                        "status": "received",
                        "message": message
                    }
            
            time.sleep(1)  # Poll every second
        
        return {
            "status": "timeout",
            "message": f"No response received within {timeout} seconds"
        }
