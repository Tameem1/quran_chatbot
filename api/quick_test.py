#!/usr/bin/env python3
"""
Quick test to verify the Quran Chatbot API is working.
"""

import requests
import json

def test_api():
    """Test basic API functionality."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Quran Chatbot API...")
    print("=" * 50)
    
    try:
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ Health check passed")
            print(f"   📝 Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
        
        # Test capabilities endpoint
        print("\n2. Testing capabilities endpoint...")
        response = requests.get(f"{base_url}/capabilities")
        if response.status_code == 200:
            print("   ✅ Capabilities endpoint working")
            capabilities = response.json()
            print(f"   🌍 Supported languages: {capabilities['supported_languages']}")
            print(f"   🔍 Question types: {len(capabilities['question_types'])} types")
        else:
            print(f"   ❌ Capabilities failed: {response.status_code}")
            return False
        
        # Test examples endpoint
        print("\n3. Testing examples endpoint...")
        response = requests.get(f"{base_url}/examples")
        if response.status_code == 200:
            print("   ✅ Examples endpoint working")
            examples = response.json()
            print(f"   📚 Found {examples['total']} example questions")
        else:
            print(f"   ❌ Examples failed: {response.status_code}")
            return False
        
        # Test ask endpoint with a simple question
        print("\n4. Testing ask endpoint...")
        payload = {"question": "ما معنى كلمة غفر؟"}
        response = requests.post(f"{base_url}/ask", json=payload)
        if response.status_code == 200:
            print("   ✅ Ask endpoint working")
            result = response.json()
            print(f"   ⏱️  Processing time: {result.get('processing_time', 'N/A')}s")
            print(f"   💬 Answer length: {len(result['answer'])} characters")
        else:
            print(f"   ❌ Ask endpoint failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
            return False
        
        print("\n🎉 All tests passed! The API is working correctly.")
        print(f"\n🌐 You can access:")
        print(f"   - API: {base_url}")
        print(f"   - Documentation: {base_url}/docs")
        print(f"   - Alternative docs: {base_url}/redoc")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server.")
        print("   Make sure the server is running with: python simple_api.py")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    exit(0 if success else 1)
