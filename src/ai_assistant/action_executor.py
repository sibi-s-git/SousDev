import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Add src directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from external_data.screenshot_manager import ScreenshotManager

class ActionExecutor:
    """
    Executes actions based on recognized intents from the AI assistant.
    """
    
    def __init__(self):
        """Initialize the action executor."""
        self.screenshot_manager = ScreenshotManager()
        self.current_directory = Path.cwd()
        
    def execute_intent(self, intent_result: Dict, context: str = "") -> Dict[str, Any]:
        """
        Execute an action based on the recognized intent.
        
        Args:
            intent_result: Result from LocalAIAssistant.understand_intent()
            context: Optional context information
            
        Returns:
            Dict with execution result and any output
        """
        intent = intent_result.get("intent", "unknown")
        confidence = intent_result.get("confidence", 0.0)
        
        print(f"Executing intent: {intent} (confidence: {confidence:.2f})")
        
        # Only execute if confidence is high enough
        if confidence < 0.5:
            return {
                "success": False,
                "message": f"Confidence too low ({confidence:.2f}) for automatic execution",
                "intent": intent
            }
        
        try:
            if intent == "screenshot":
                return self._take_screenshot()
            elif intent == "run":
                return self._execute_run_command(context)
            elif intent == "file_help":
                return self._prepare_file_help(context)
            elif intent == "claude_prompt":
                return self._prepare_claude_prompt(intent_result, context)
            else:
                return {
                    "success": False,
                    "message": f"Unknown intent: {intent}",
                    "intent": intent
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error executing {intent}: {e}",
                "intent": intent,
                "error": str(e)
            }
    
    def _take_screenshot(self) -> Dict[str, Any]:
        """Take a screenshot."""
        try:
            screenshot, file_path = self.screenshot_manager.capture_screenshot()
            
            if screenshot and file_path:
                return {
                    "success": True,
                    "message": f"Screenshot saved to {file_path}",
                    "file_path": str(file_path),
                    "action": "screenshot"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to capture screenshot",
                    "action": "screenshot"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Screenshot error: {e}",
                "action": "screenshot",
                "error": str(e)
            }
    
    def _execute_run_command(self, context: str) -> Dict[str, Any]:
        """Execute a run command - for safety, this just prepares the command."""
        # For security, we don't automatically execute arbitrary commands
        # Instead, we prepare suggestions
        
        common_commands = {
            "main": "python main.py",
            "test": "python test_screenshot.py", 
            "speech test": "python test_speech_only.py",
            "install": "pip install -r requirements.txt",
            "model": "python download_model.py"
        }
        
        suggested_commands = []
        for key, cmd in common_commands.items():
            if key in context.lower():
                suggested_commands.append(cmd)
        
        if not suggested_commands:
            # Default suggestions
            suggested_commands = [
                "python main.py",
                "python test_screenshot.py"
            ]
        
        return {
            "success": True,
            "message": "Run command prepared (manual execution required for security)",
            "suggested_commands": suggested_commands,
            "action": "run",
            "note": "Commands are suggested but not automatically executed for security reasons"
        }
    
    def _prepare_file_help(self, context: str) -> Dict[str, Any]:
        """Prepare file help by finding relevant files."""
        try:
            # Try to find files mentioned in context or current directory
            relevant_files = []
            
            # Look for file extensions in context
            file_patterns = ['.py', '.txt', '.md', '.json', '.yml', '.yaml']
            words = context.lower().split()
            
            for word in words:
                for pattern in file_patterns:
                    if pattern in word:
                        # Try to find this file
                        potential_file = Path(word)
                        if potential_file.exists():
                            relevant_files.append(str(potential_file))
            
            # If no specific files found, list current directory Python files
            if not relevant_files:
                for py_file in self.current_directory.glob("*.py"):
                    relevant_files.append(str(py_file))
                    
                # Also check src directory
                src_dir = self.current_directory / "src"
                if src_dir.exists():
                    for py_file in src_dir.rglob("*.py"):
                        relevant_files.append(str(py_file))
            
            return {
                "success": True,
                "message": f"Found {len(relevant_files)} relevant files",
                "relevant_files": relevant_files[:10],  # Limit to first 10
                "action": "file_help"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error finding files: {e}",
                "action": "file_help",
                "error": str(e)
            }
    
    def _prepare_claude_prompt(self, intent_result: Dict, context: str) -> Dict[str, Any]:
        """Prepare a Claude prompt."""
        return {
            "success": True,
            "message": "Claude prompt prepared",
            "claude_prompt": f"User intent: {intent_result}\nContext: {context}",
            "action": "claude_prompt"
        }
    
    def get_current_file_context(self, max_files: int = 3) -> str:
        """Get context from current working directory files."""
        try:
            context_parts = [f"Current directory: {self.current_directory}\n"]
            
            # Get Python files in current directory
            py_files = list(self.current_directory.glob("*.py"))[:max_files]
            
            for py_file in py_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content) > 1000:
                            content = content[:1000] + "..."
                        context_parts.append(f"\n--- {py_file.name} ---\n{content}")
                except Exception as e:
                    context_parts.append(f"\n--- {py_file.name} ---\nError reading: {e}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            return f"Error getting file context: {e}"
    
    def safe_execute_command(self, command: str, confirm: bool = True) -> Dict[str, Any]:
        """
        Safely execute a command with user confirmation.
        
        Args:
            command: Command to execute
            confirm: Whether to ask for confirmation
            
        Returns:
            Execution result
        """
        if confirm:
            response = input(f"Execute command '{command}'? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                return {
                    "success": False,
                    "message": "Command execution cancelled by user",
                    "command": command
                }
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            return {
                "success": result.returncode == 0,
                "message": f"Command executed (exit code: {result.returncode})",
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Command timed out after 30 seconds",
                "command": command,
                "error": "timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error executing command: {e}",
                "command": command,
                "error": str(e)
            } 