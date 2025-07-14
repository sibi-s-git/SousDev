import re
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Ollama not available. Install with: pip install ollama")

class LocalAIAssistant:
    """
    Local AI assistant for intent recognition and context extraction.
    """
    
    def __init__(self, model_name="llama3.2:1b"):
        """
        Initialize the local AI assistant.
        
        Args:
            model_name: Ollama model to use (llama3.2:1b, phi3:mini, etc.)
        """
        self.model_name = model_name
        self.ollama_available = OLLAMA_AVAILABLE
        
        # Intent patterns for fallback (if Ollama not available)
        self.intent_patterns = {
            'screenshot': [
                r'\b(take|capture|grab|get)\s+(a\s+)?(screenshot|screen\s*shot|picture|image)\b',
                r'\bscreenshot\b',
                r'\bscreen\s*cap\b',
                r'\bcapture\s+(screen|display)\b'
            ],
            'run': [
                r'\b(run|execute|start|launch)\b',
                r'\bgo\b',
                r'\bdo\s+it\b',
                r'\bexecute\s+(this|that|it)\b'
            ],
            'file_help': [
                r'\bin\s+this\s+file\b',
                r'\bwith\s+this\s+file\b',
                r'\bopen\s+file\b',
                r'\bread\s+(this\s+)?file\b',
                r'\bfile\s+context\b',
                r'\bfrom\s+(this\s+)?file\b'
            ],
            'claude_prompt': [
                r'\bask\s+claude\b',
                r'\bclaude\s+(prompt|help|question)\b',
                r'\bprompt\s+claude\b',
                r'\bsend\s+to\s+claude\b'
            ]
        }
        
        # Check if Ollama is running
        if self.ollama_available:
            self._check_ollama_service()
    
    def _check_ollama_service(self):
        """Check if Ollama service is running and model is available."""
        try:
            # Test connection
            response = ollama.list()
            print(f"Ollama connected. Available models: {[m['name'] for m in response['models']]}")
            
            # Check if our model is available
            model_names = [m['name'] for m in response['models']]
            if self.model_name not in model_names:
                print(f"Model {self.model_name} not found. Pulling...")
                ollama.pull(self.model_name)
                
        except Exception as e:
            print(f"Ollama service not available: {e}")
            print("Install Ollama from https://ollama.ai or use fallback pattern matching")
            self.ollama_available = False
    
    def understand_intent(self, text: str) -> Dict:
        """
        Understand the intent of spoken text.
        
        Args:
            text: Spoken text from voice recognition
            
        Returns:
            Dict with intent, confidence, and extracted parameters
        """
        text = text.lower().strip()
        
        if self.ollama_available:
            return self._understand_with_ollama(text)
        else:
            return self._understand_with_patterns(text)
    
    def _understand_with_ollama(self, text: str) -> Dict:
        """Use Ollama for intent recognition."""
        try:
            prompt = f"""
Analyze this voice command and return ONLY a JSON response:

Command: "{text}"

Determine the intent from these options:
- screenshot: taking a screenshot/screen capture
- run: running/executing something  
- file_help: needs help with a file or file context
- claude_prompt: wants to send something to Claude AI
- unknown: none of the above

Return JSON format:
{{"intent": "intent_name", "confidence": 0.95, "parameters": {{"action": "description"}}}}

JSON:"""

            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={"temperature": 0.1, "max_tokens": 100}
            )
            
            # Extract JSON from response
            response_text = response['response'].strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                # Fallback to pattern matching if JSON parsing fails
                return self._understand_with_patterns(text)
                
        except Exception as e:
            print(f"Ollama error: {e}")
            return self._understand_with_patterns(text)
    
    def _understand_with_patterns(self, text: str) -> Dict:
        """Fallback pattern-based intent recognition."""
        best_intent = "unknown"
        best_confidence = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    confidence = 0.8  # High confidence for exact pattern match
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
        
        return {
            "intent": best_intent,
            "confidence": best_confidence,
            "parameters": {"matched_text": text}
        }
    
    def extract_file_context(self, file_path: str, query: str = "") -> str:
        """
        Extract relevant context from a file for Claude prompts.
        
        Args:
            file_path: Path to the file
            query: Optional query to focus extraction
            
        Returns:
            Formatted context string
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return f"File not found: {file_path}"
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except:
                    return f"Could not read file: {file_path} (binary file?)"
            
            # If file is very large, extract relevant sections
            if len(content) > 10000:  # If file is larger than 10k chars
                if query and self.ollama_available:
                    return self._extract_relevant_sections(content, query, file_path)
                else:
                    # Simple truncation with context
                    lines = content.split('\n')
                    if len(lines) > 200:
                        context = (
                            f"File: {file_path}\n"
                            f"Total lines: {len(lines)}\n"
                            f"First 100 lines:\n" + '\n'.join(lines[:100]) + "\n\n" +
                            f"Last 100 lines:\n" + '\n'.join(lines[-100:])
                        )
                    else:
                        context = f"File: {file_path}\n{content}"
            else:
                context = f"File: {file_path}\n{content}"
            
            return context
            
        except Exception as e:
            return f"Error reading file {file_path}: {e}"
    
    def _extract_relevant_sections(self, content: str, query: str, file_path: Path) -> str:
        """Use Ollama to extract relevant sections from large files."""
        try:
            # Split content into chunks
            lines = content.split('\n')
            chunk_size = 50
            chunks = [lines[i:i+chunk_size] for i in range(0, len(lines), chunk_size)]
            
            relevant_chunks = []
            
            for i, chunk in enumerate(chunks):
                chunk_text = '\n'.join(chunk)
                
                prompt = f"""
Analyze this code/text chunk and determine if it's relevant to: "{query}"

Chunk {i+1}:
{chunk_text}

Is this chunk relevant? Answer only YES or NO:"""

                response = ollama.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={"temperature": 0.1, "max_tokens": 10}
                )
                
                if "yes" in response['response'].lower():
                    relevant_chunks.append((i+1, chunk_text))
            
            if relevant_chunks:
                context = f"File: {file_path}\nRelevant sections for '{query}':\n\n"
                for chunk_num, chunk_text in relevant_chunks:
                    context += f"--- Chunk {chunk_num} ---\n{chunk_text}\n\n"
                return context
            else:
                # Return first and last chunks if nothing relevant found
                return (f"File: {file_path}\n"
                       f"No specific relevant sections found for '{query}'\n"
                       f"First section:\n{chunks[0]}\n\n"
                       f"Last section:\n{chunks[-1]}")
                
        except Exception as e:
            print(f"Error extracting relevant sections: {e}")
            return f"File: {file_path}\n{content[:5000]}..."  # Fallback to first 5k chars
    
    def create_claude_prompt(self, intent_result: Dict, context: str = "") -> str:
        """
        Create a formatted prompt for Claude based on intent and context.
        
        Args:
            intent_result: Result from understand_intent()
            context: Optional file context
            
        Returns:
            Formatted prompt for Claude
        """
        intent = intent_result.get("intent", "unknown")
        
        if intent == "file_help":
            return f"""I need help with this file:

{context}

Please analyze this file and help me understand:
1. What this code/content does
2. Key functions or sections
3. Any issues or improvements you notice
4. How I can work with this file

Please provide clear, actionable insights."""

        elif intent == "screenshot":
            return f"""I've taken a screenshot and need help analyzing it.

Context: {context}

Please help me understand what's shown in the screenshot and provide relevant insights or suggestions."""

        elif intent == "run":
            return f"""I want to run or execute something.

Context: {context}

Please help me:
1. Understand what should be executed
2. Provide the correct commands or steps
3. Warn about any potential issues
4. Suggest best practices"""

        else:
            return f"""I need assistance with the following:

Intent: {intent}
Context: {context}

Please provide helpful guidance based on this information."""

# Example usage functions
def setup_local_ai() -> LocalAIAssistant:
    """Setup and return a local AI assistant instance."""
    return LocalAIAssistant()

def test_voice_command(assistant: LocalAIAssistant, command: str):
    """Test a voice command with the assistant."""
    print(f"Testing command: '{command}'")
    
    # Understand intent
    intent_result = assistant.understand_intent(command)
    print(f"Intent: {intent_result}")
    
    # Create Claude prompt
    prompt = assistant.create_claude_prompt(intent_result)
    print(f"Claude prompt:\n{prompt}")
    
    return intent_result, prompt 