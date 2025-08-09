#!/usr/bin/env python3
"""
Smoke test for Coral Protocol integration.
Tests basic thread creation, message sending, and response handling.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from coral.coral_client import CoralClient
from coral.schemas import MessageType, ThreadMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_coral_health():
    """Test Coral server health check."""
    logger.info("🔍 Testing Coral server health...")
    
    client = CoralClient()
    health = client.health_check()
    
    if health["status"] == "healthy":
        logger.info("✅ Coral server is healthy")
        logger.info(f"   Server URL: {health['server_url']}")
        return True
    else:
        logger.error("❌ Coral server health check failed")
        logger.error(f"   Error: {health.get('error', 'Unknown error')}")
        return False

def test_thread_creation():
    """Test thread creation."""
    logger.info("🧵 Testing thread creation...")
    
    client = CoralClient()
    thread_result = client.create_thread(
        title="Smoke Test Thread",
        metadata={
            "test_type": "smoke_test",
            "purpose": "coral_integration_test"
        }
    )
    
    if thread_result.get("thread_id"):
        logger.info("✅ Thread created successfully")
        logger.info(f"   Thread ID: {thread_result['thread_id']}")
        return thread_result["thread_id"]
    else:
        logger.error("❌ Thread creation failed")
        logger.error(f"   Error: {thread_result.get('error', 'Unknown error')}")
        return None

def test_message_sending(thread_id: str):
    """Test message sending to thread."""
    logger.info("💬 Testing message sending...")
    
    client = CoralClient()
    message_result = client.send_message(
        thread_id=thread_id,
        content="Hello from Aligna smoke test! This is a test message to verify Coral integration.",
        agent_name="smoke_test_agent",
        message_type=MessageType.MESSAGE,
        payload={
            "test_data": "smoke_test_payload",
            "timestamp": "2025-01-09T11:14:00Z"
        }
    )
    
    if message_result.get("message_id"):
        logger.info("✅ Message sent successfully")
        logger.info(f"   Message ID: {message_result['message_id']}")
        return True
    else:
        logger.error("❌ Message sending failed")
        logger.error(f"   Error: {message_result.get('error', 'Unknown error')}")
        return False

def test_message_retrieval(thread_id: str):
    """Test message retrieval from thread."""
    logger.info("📥 Testing message retrieval...")
    
    client = CoralClient()
    messages_result = client.get_thread_messages(thread_id, limit=10)
    
    if not messages_result.get("error"):
        messages = messages_result.get("messages", [])
        logger.info(f"✅ Retrieved {len(messages)} messages from thread")
        
        # Log message details
        for i, msg in enumerate(messages):
            logger.info(f"   Message {i+1}: {msg.get('content', '')[:50]}...")
            logger.info(f"   From: {msg.get('agent_name', 'unknown')}")
            logger.info(f"   Type: {msg.get('message_type', 'unknown')}")
        
        return True
    else:
        logger.error("❌ Message retrieval failed")
        logger.error(f"   Error: {messages_result.get('error', 'Unknown error')}")
        return False

def test_agent_mention(thread_id: str):
    """Test agent mention functionality."""
    logger.info("🏷️ Testing agent mention...")
    
    client = CoralClient()
    mention_result = client.mention_agent(
        thread_id=thread_id,
        agent_name="test_agent",
        content="Please respond to this mention test",
        payload={
            "mention_test": True,
            "expected_response": "acknowledgment"
        }
    )
    
    if mention_result.get("message_id"):
        logger.info("✅ Agent mention sent successfully")
        logger.info(f"   Mention ID: {mention_result['message_id']}")
        return True
    else:
        logger.error("❌ Agent mention failed")
        logger.error(f"   Error: {mention_result.get('error', 'Unknown error')}")
        return False

def test_agent_registration():
    """Test agent registration."""
    logger.info("📝 Testing agent registration...")
    
    client = CoralClient()
    registration_result = client.register_agent(
        agent_name="smoke_test_agent",
        capabilities=["testing", "smoke_test"],
        endpoint="http://localhost:8000/test/smoke_agent",
        description="Smoke test agent for Coral integration testing"
    )
    
    if not registration_result.get("error"):
        logger.info("✅ Agent registered successfully")
        logger.info(f"   Agent: smoke_test_agent")
        return True
    else:
        logger.error("❌ Agent registration failed")
        logger.error(f"   Error: {registration_result.get('error', 'Unknown error')}")
        return False

def test_registered_agents():
    """Test retrieving registered agents."""
    logger.info("👥 Testing registered agents retrieval...")
    
    client = CoralClient()
    agents_result = client.get_registered_agents()
    
    if not agents_result.get("error"):
        agents = agents_result.get("agents", [])
        logger.info(f"✅ Retrieved {len(agents)} registered agents")
        
        for agent in agents:
            logger.info(f"   Agent: {agent.get('agent_name', 'unknown')}")
            logger.info(f"   Capabilities: {agent.get('capabilities', [])}")
        
        return True
    else:
        logger.error("❌ Registered agents retrieval failed")
        logger.error(f"   Error: {agents_result.get('error', 'Unknown error')}")
        return False

def main():
    """Run all smoke tests."""
    logger.info("🚀 Starting Coral Protocol smoke tests...")
    logger.info("=" * 60)
    
    # Test results
    results = {}
    
    # Test 1: Health check
    results["health"] = test_coral_health()
    
    if not results["health"]:
        logger.error("❌ Coral server is not available. Skipping remaining tests.")
        logger.error("💡 Make sure Coral server is running on the configured URL")
        logger.error(f"   Expected URL: {os.getenv('CORAL_URL', 'http://localhost:8009')}")
        return False
    
    # Test 2: Thread creation
    thread_id = test_thread_creation()
    results["thread_creation"] = thread_id is not None
    
    if thread_id:
        # Test 3: Message sending
        results["message_sending"] = test_message_sending(thread_id)
        
        # Test 4: Message retrieval
        results["message_retrieval"] = test_message_retrieval(thread_id)
        
        # Test 5: Agent mention
        results["agent_mention"] = test_agent_mention(thread_id)
    else:
        results["message_sending"] = False
        results["message_retrieval"] = False
        results["agent_mention"] = False
    
    # Test 6: Agent registration
    results["agent_registration"] = test_agent_registration()
    
    # Test 7: Registered agents
    results["registered_agents"] = test_registered_agents()
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 Smoke Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
        if passed_test:
            passed += 1
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All smoke tests passed! Coral integration is working.")
        return True
    else:
        logger.error("⚠️ Some smoke tests failed. Check Coral server configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
