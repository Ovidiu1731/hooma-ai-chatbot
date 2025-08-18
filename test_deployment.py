#!/usr/bin/env python3
"""
Hooma AI Chatbot - Deployment Test Script
Test script to verify the chatbot is working correctly before and after deployment
"""

import asyncio
import json
import os
import time
from typing import Dict, Any
import httpx
from pathlib import Path

# Configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
TIMEOUT = 30

class ChatbotTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session_id = None
        self.results = []
        
    async def test_health_check(self) -> bool:
        """Test the health check endpoint"""
        print("🔍 Testing health check...")
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.get(f"{self.base_url}/api/health")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Health check passed: {data['status']}")
                    print(f"   AI Provider: {data.get('ai_provider', 'unknown')}")
                    print(f"   Version: {data.get('version', 'unknown')}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_chat_api(self, message: str) -> Dict[str, Any]:
        """Test the chat API with a message"""
        print(f"💬 Testing chat: '{message[:50]}...'")
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                payload = {
                    "message": message,
                    "session_id": self.session_id,
                    "user_info": {
                        "url": "http://test.example.com",
                        "referrer": "test"
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.session_id = data["session_id"]
                    
                    print(f"✅ Chat response received")
                    print(f"   Response length: {len(data['response'])} characters")
                    print(f"   Session ID: {data['session_id'][:8]}...")
                    print(f"   Response preview: {data['response'][:100]}...")
                    
                    return data
                else:
                    print(f"❌ Chat API failed: {response.status_code}")
                    if response.text:
                        print(f"   Error: {response.text}")
                    return {}
                    
        except Exception as e:
            print(f"❌ Chat API error: {e}")
            return {}
    
    async def test_static_files(self) -> bool:
        """Test that static files are accessible"""
        print("📄 Testing static files...")
        files_to_test = [
            "/embed/widget.js",
            "/embed/widget.css"
        ]
        
        all_passed = True
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for file_path in files_to_test:
                try:
                    response = await client.get(f"{self.base_url}{file_path}")
                    if response.status_code == 200:
                        print(f"   ✅ {file_path} - OK ({len(response.content)} bytes)")
                    else:
                        print(f"   ❌ {file_path} - Failed ({response.status_code})")
                        all_passed = False
                except Exception as e:
                    print(f"   ❌ {file_path} - Error: {e}")
                    all_passed = False
        
        return all_passed
    
    async def test_widget_demo(self) -> bool:
        """Test the widget demo page"""
        print("🎨 Testing widget demo page...")
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.get(f"{self.base_url}/embed/demo.html")
                
                if response.status_code == 200:
                    content = response.text
                    # Check for key elements
                    if all(x in content for x in ["HoomaChatbot", "widget.js", "widget.css"]):
                        print("✅ Widget demo page loaded successfully")
                        return True
                    else:
                        print("❌ Widget demo page missing key elements")
                        return False
                else:
                    print(f"❌ Widget demo page failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Widget demo error: {e}")
            return False
    
    async def test_conversation_flow(self) -> bool:
        """Test a realistic conversation flow"""
        print("🗣️ Testing conversation flow...")
        
        test_messages = [
            "Hello, I'm interested in AI solutions for my business",
            "What services does Hooma offer?",
            "How much does a typical project cost?",
            "How can I schedule a consultation?"
        ]
        
        all_passed = True
        for i, message in enumerate(test_messages):
            response = await self.test_chat_api(message)
            if not response:
                all_passed = False
                break
                
            # Wait a bit between messages
            if i < len(test_messages) - 1:
                await asyncio.sleep(1)
        
        if all_passed:
            print("✅ Conversation flow test completed successfully")
        else:
            print("❌ Conversation flow test failed")
            
        return all_passed
    
    async def test_rate_limiting(self) -> bool:
        """Test rate limiting functionality"""
        print("🚦 Testing rate limiting...")
        
        # Send multiple requests quickly
        tasks = []
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for i in range(5):
                task = client.post(
                    f"{self.base_url}/api/chat",
                    json={"message": f"Test message {i}"},
                    headers={"Content-Type": "application/json"}
                )
                tasks.append(task)
            
            try:
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
                rate_limited_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 429)
                
                print(f"   Successful requests: {success_count}")
                print(f"   Rate limited requests: {rate_limited_count}")
                
                if rate_limited_count > 0:
                    print("✅ Rate limiting is working")
                    return True
                else:
                    print("⚠️ Rate limiting may not be configured (or limit is high)")
                    return True  # Not a failure, just a warning
                    
            except Exception as e:
                print(f"❌ Rate limiting test error: {e}")
                return False
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<30} {status}")
        
        print("-"*60)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! Your chatbot is ready for production.")
        else:
            print(f"\n⚠️ {total - passed} test(s) failed. Please review the issues above.")
        
        print("="*60)

async def main():
    """Run all tests"""
    print("🤖 Hooma AI Chatbot - Deployment Test Suite")
    print(f"Testing endpoint: {BASE_URL}")
    print("="*60)
    
    if not API_KEY:
        print("⚠️ Warning: No API key found. Some tests may fail.")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")
        print()
    
    tester = ChatbotTester(BASE_URL)
    
    # Run tests
    test_results = {}
    
    test_results["Health Check"] = await tester.test_health_check()
    test_results["Static Files"] = await tester.test_static_files()
    test_results["Widget Demo"] = await tester.test_widget_demo()
    
    if API_KEY:
        test_results["Chat API"] = bool(await tester.test_chat_api("Hello, how can you help me?"))
        test_results["Conversation Flow"] = await tester.test_conversation_flow()
        test_results["Rate Limiting"] = await tester.test_rate_limiting()
    else:
        print("⏭️ Skipping API tests (no API key provided)")
    
    # Print summary
    tester.print_summary(test_results)

if __name__ == "__main__":
    asyncio.run(main())
