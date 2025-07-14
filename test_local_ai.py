#!/usr/bin/env python3
"""
Test script for the Local AI Assistant functionality.
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.abspath('src'))

from ai_assistant.local_ai import LocalAIAssistant
from ai_assistant.action_executor import ActionExecutor

def test_basic_commands():
    """Test basic voice command recognition."""
    print("=" * 50)
    print("Testing Basic Voice Commands")
    print("=" * 50)
    
    # Initialize AI assistant
    ai = LocalAIAssistant()
    executor = ActionExecutor()
    
    # Test commands
    test_commands = [
        "take a screenshot",
        "screenshot this page",
        "run the main program",
        "execute this",
        "help me with this file",
        "in this file I need to understand",
        "ask claude about this code",
        "send this to claude"
    ]
    
    for command in test_commands:
        print(f"\n🎤 Voice Command: '{command}'")
        
        # Understand intent
        intent_result = ai.understand_intent(command)
        print(f"💭 Intent: {intent_result['intent']} (confidence: {intent_result['confidence']:.2f})")
        
        # Execute action
        if intent_result['confidence'] > 0.5:
            execution_result = executor.execute_intent(intent_result, command)
            print(f"⚡ Action: {execution_result['message']}")
            
            if execution_result.get('suggested_commands'):
                print(f"🔧 Suggestions: {execution_result['suggested_commands']}")
        else:
            print("❌ Confidence too low for execution")

def test_file_context_extraction():
    """Test extracting context from files."""
    print("\n" + "=" * 50)
    print("Testing File Context Extraction")
    print("=" * 50)
    
    ai = LocalAIAssistant()
    
    # Test with main.py file
    print(f"\n📄 Extracting context from main.py...")
    context = ai.extract_file_context("main.py", "voice recognition")
    print(f"📋 Context length: {len(context)} characters")
    print(f"🔍 First 300 chars:\n{context[:300]}...")

def test_claude_prompt_generation():
    """Test generating Claude prompts."""
    print("\n" + "=" * 50)
    print("Testing Claude Prompt Generation")
    print("=" * 50)
    
    ai = LocalAIAssistant()
    executor = ActionExecutor()
    
    # Simulate scenarios
    scenarios = [
        {
            "command": "help me understand this code in main.py",
            "file": "main.py"
        },
        {
            "command": "take screenshot and analyze it",
            "file": None
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🎯 Scenario: {scenario['command']}")
        
        # Get intent
        intent_result = ai.understand_intent(scenario['command'])
        
        # Get file context if needed
        context = ""
        if scenario['file'] and intent_result['intent'] == 'file_help':
            context = ai.extract_file_context(scenario['file'])
        elif intent_result['intent'] == 'screenshot':
            # Simulate having taken a screenshot
            context = "Screenshot taken of the current application"
        
        # Generate Claude prompt
        claude_prompt = ai.create_claude_prompt(intent_result, context)
        print(f"🤖 Claude Prompt:\n{claude_prompt[:500]}...")

def test_integration_workflow():
    """Test a complete workflow integration."""
    print("\n" + "=" * 50)
    print("Testing Complete Integration Workflow")
    print("=" * 50)
    
    ai = LocalAIAssistant()
    executor = ActionExecutor()
    
    # Simulate a complete voice-to-action workflow
    voice_command = "take a screenshot and help me understand the main.py file"
    
    print(f"🎤 Voice Input: '{voice_command}'")
    
    # Step 1: Understand intent
    intent_result = ai.understand_intent(voice_command)
    print(f"💭 Primary Intent: {intent_result['intent']}")
    
    # Step 2: Execute primary action (screenshot)
    if 'screenshot' in voice_command.lower():
        screenshot_result = executor._take_screenshot()
        print(f"📸 Screenshot: {screenshot_result['message']}")
    
    # Step 3: Handle file help
    if 'file' in voice_command.lower():
        file_context = ai.extract_file_context("main.py", "voice recognition and pygame")
        claude_prompt = ai.create_claude_prompt(
            {"intent": "file_help", "confidence": 0.9}, 
            file_context
        )
        print(f"📋 Generated Claude prompt with file context")
        print(f"🔍 Prompt preview: {claude_prompt[:200]}...")

def main():
    """Main test function."""
    print("🤖 Local AI Assistant Test Suite")
    print("This tests voice command recognition and action execution")
    
    try:
        # Test basic functionality
        test_basic_commands()
        
        # Test file operations
        test_file_context_extraction()
        
        # Test Claude prompt generation
        test_claude_prompt_generation()
        
        # Test complete workflow
        test_integration_workflow()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("=" * 50)
        
        # Show setup instructions
        print("\n🚀 Setup Instructions:")
        print("1. Install Ollama: https://ollama.ai")
        print("2. Run: ollama pull llama3.2:1b")
        print("3. The AI will work with or without Ollama (fallback to patterns)")
        print("\n💡 Integration with your voice app:")
        print("- Add LocalAIAssistant to your main.py voice callback")
        print("- Use ActionExecutor to perform the recognized actions")
        print("- Send generated prompts to Claude for assistance")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 