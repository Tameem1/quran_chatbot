#!/usr/bin/env python3
"""
Test script for the Quran Chatbot API.

This script demonstrates how to interact with the API endpoints.
Make sure the API server is running before executing this script.
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        print()

def test_capabilities():
    """Test the capabilities endpoint."""
    print("🔍 Testing capabilities endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/capabilities")
        print(f"Status: {response.status_code}")
        capabilities = response.json()
        print(f"Supported languages: {capabilities['supported_languages']}")
        print(f"Question types: {capabilities['question_types']}")
        print(f"Features: {capabilities['features']}")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        print()

def test_examples():
    """Test the examples endpoint."""
    print("🔍 Testing examples endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/examples")
        print(f"Status: {response.status_code}")
        examples = response.json()
        print(f"Found {examples['total']} example questions:")
        for i, example in enumerate(examples['examples'], 1):
            print(f"  {i}. {example['arabic']} ({example['english']})")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        print()

def test_ask_question(question: str, verbose: bool = False):
    """Test asking a question to the chatbot."""
    print(f"🔍 Testing ask endpoint with question: {question}")
    try:
        payload = {
            "question": question,
            "verbose": verbose
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/ask", json=payload)
        end_time = time.time()
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Answer: {result['answer']}")
            if result.get('processing_time'):
                print(f"Processing time: {result['processing_time']}s")
            if result.get('question_type'):
                print(f"Question type: {result['question_type']}")
        else:
            print(f"Error: {response.text}")
        
        print(f"Total request time: {end_time - start_time:.3f}s")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()

def test_stream_question(question: str):
    """Test asking a question with streaming status updates."""
    print(f"🔍 Testing streaming ask endpoint with question: {question}")
    try:
        payload = {
            "question": question,
            "verbose": False
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/ask/stream", json=payload)
        end_time = time.time()
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Answer: {result['answer']}")
            print(f"Total stages: {result['total_stages']}")
            print("Status updates:")
            for i, update in enumerate(result['status_updates'], 1):
                print(f"  {i}. {update}")
        else:
            print(f"Error: {response.text}")
        
        print(f"Total request time: {end_time - start_time:.3f}s")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()

def main():
    """Run all tests."""
    print("🚀 Starting Quran Chatbot API Tests")
    print("=" * 50)
    
    # Test basic endpoints
    test_health()
    test_capabilities()
    test_examples()
    
    # Test question asking
    test_questions = [
        "ما معنى كلمة غفر؟",
        "كم مرة ورد جذر سجد في القرآن؟",
        "ما الفرق بين كلمة عقل وكلمة فهم؟"
    ]
    
    for question in test_questions:
        test_ask_question(question)
        time.sleep(1)  # Small delay between requests
    
    # Test streaming with one question
    test_stream_question("استخرج جميع الآيات التي تحتوي على جذر كتب")
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    main()
