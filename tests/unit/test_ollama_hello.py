#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple test for Ollama using client"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.llm.client import OllamaClient

def test_ollama_hello():
    """Test basic Ollama chat"""
    print("Testing Ollama connection...")
    
    client = OllamaClient()  # Auto warmup
    
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant. Always give concise, direct answers.'},
        {'role': 'user', 'content': 'Hi, please reply with just "Hello!"'}
    ]
    
    try:
        response = client.chat(messages, temperature=0.1)
        reply = response['message']['content']
        
        # Truncate at stop tokens
        for stop_token in ['<|endoftext|>', '<|im_end|>', '\nHuman:', '\nAssistant:']:
            if stop_token in reply:
                reply = reply.split(stop_token)[0]
        
        reply = reply.strip()
        print(f"\nResponse: {reply}")
        print("\n✅ Ollama test passed!")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_ollama_hello()
    sys.exit(0 if success else 1)
