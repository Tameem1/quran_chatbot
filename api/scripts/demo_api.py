#!/usr/bin/env python3
"""
Demo script showing how to use the Quran Chatbot API.

This script demonstrates various ways to interact with the API.
Make sure the API server is running before executing this script.
"""

import requests
import json
import time
from typing import Dict, Any

class QuranChatbotAPI:
    """Client class for interacting with the Quran Chatbot API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about what the chatbot can do."""
        response = self.session.get(f"{self.base_url}/capabilities")
        response.raise_for_status()
        return response.json()
    
    def get_examples(self) -> Dict[str, Any]:
        """Get example questions."""
        response = self.session.get(f"{self.base_url}/examples")
        response.raise_for_status()
        return response.json()
    
    def ask_question(self, question: str, verbose: bool = False) -> Dict[str, Any]:
        """Ask a question to the chatbot."""
        payload = {
            "question": question,
            "verbose": verbose
        }
        
        start_time = time.time()
        response = self.session.post(f"{self.base_url}/ask", json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Add request timing
        result["request_time"] = time.time() - start_time
        return result
    
    def ask_question_stream(self, question: str) -> Dict[str, Any]:
        """Ask a question with streaming status updates."""
        payload = {
            "question": question,
            "verbose": False
        }
        
        start_time = time.time()
        response = self.session.post(f"{self.base_url}/ask/stream", json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Add request timing
        result["request_time"] = time.time() - start_time
        return result

def print_separator(title: str):
    """Print a formatted separator."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_question_result(result: Dict[str, Any], question: str):
    """Print the result of a question in a formatted way."""
    print(f"\n❓ Question: {question}")
    print(f"⏱️  Processing time: {result.get('processing_time', 'N/A')}s")
    print(f"⏱️  Request time: {result.get('request_time', 'N/A'):.3f}s")
    
    if result.get('question_type'):
        print(f"🔍 Question type: {result['question_type']}")
    if result.get('target_entity'):
        print(f"🎯 Target entity: {result['target_entity']}")
    if result.get('surah_filter'):
        print(f"📖 Surah filter: {result['surah_filter']}")
    
    print(f"\n💬 Answer:")
    print(f"   {result['answer']}")

def main():
    """Main demo function."""
    print("🚀 Quran Chatbot API Demo")
    print("Make sure the API server is running on http://localhost:8000")
    
    # Initialize API client
    api = QuranChatbotAPI()
    
    try:
        # Test health check
        print_separator("Health Check")
        health = api.health_check()
        print(f"✅ Status: {health['status']}")
        print(f"📝 Message: {health['message']}")
        
        # Get capabilities
        print_separator("API Capabilities")
        capabilities = api.get_capabilities()
        print(f"🌍 Supported languages: {', '.join(capabilities['supported_languages'])}")
        print(f"🔍 Question types: {', '.join(capabilities['question_types'])}")
        print(f"✨ Features: {', '.join(capabilities['features'])}")
        
        # Get examples
        print_separator("Example Questions")
        examples = api.get_examples()
        print(f"📚 Found {examples['total']} example questions:")
        for i, example in enumerate(examples['examples'], 1):
            print(f"   {i}. {example['arabic']}")
            print(f"      ({example['english']})")
            print(f"      Type: {example['type']}")
        
        # Test different types of questions
        test_questions = [
            "ما معنى كلمة غفر؟",
            "كم مرة ورد جذر سجد في القرآن؟",
            "ما الفرق بين كلمة عقل وكلمة فهم؟"
        ]
        
        print_separator("Testing Questions")
        for question in test_questions:
            try:
                result = api.ask_question(question)
                print_question_result(result, question)
                time.sleep(1)  # Small delay between requests
            except Exception as e:
                print(f"❌ Error with question '{question}': {e}")
        
        # Test streaming endpoint
        print_separator("Testing Streaming Endpoint")
        try:
            stream_result = api.ask_question_stream("استخرج جميع الآيات التي تحتوي على جذر كتب")
            print(f"❓ Question: استخرج جميع الآيات التي تحتوي على جذر كتب")
            print(f"⏱️  Request time: {stream_result['request_time']:.3f}s")
            print(f"📊 Total stages: {stream_result['total_stages']}")
            print(f"\n💬 Answer:")
            print(f"   {stream_result['answer']}")
            print(f"\n📋 Status updates:")
            for i, update in enumerate(stream_result['status_updates'], 1):
                print(f"   {i}. {update}")
        except Exception as e:
            print(f"❌ Error with streaming: {e}")
        
        print_separator("Demo Completed")
        print("✅ All tests completed successfully!")
        print("\n🌐 You can also access the API documentation at:")
        print("   - Swagger UI: http://localhost:8000/docs")
        print("   - ReDoc: http://localhost:8000/redoc")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server.")
        print("   Make sure the server is running with: python api.py")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
