#!/usr/bin/env python3
"""
Project Analysis System for SousDev
Analyzes project structure and creates intelligent project understanding
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# File and directory exclusions
EXCLUDED_DIRS = {
    'node_modules', '.git', 'dist', 'build', '__pycache__', 
    '.next', '.vscode', '.idea', 'coverage', '.pytest_cache',
    'vendor', 'tmp', 'temp', '.cache', '.nuxt', '.output',
    '.svelte-kit', '.expo', 'logs', '.DS_Store'
}

CODE_EXTENSIONS = {
    '.js', '.jsx', '.ts', '.tsx',           # JavaScript/TypeScript
    '.py', '.pyx',                          # Python
    '.java', '.kt',                         # Java/Kotlin
    '.swift', '.m',                         # iOS
    '.cpp', '.c', '.h', '.hpp',             # C/C++
    '.cs',                                  # C#
    '.php',                                 # PHP
    '.rb',                                  # Ruby
    '.go',                                  # Go
    '.rs',                                  # Rust
    '.vue', '.svelte',                      # Frontend frameworks
    '.html', '.css', '.scss', '.sass',      # Web
    '.sql',                                 # Database
    '.yaml', '.yml', '.json', '.toml',      # Config (selective)
    '.md'                                   # Documentation
}

IMPORTANT_CONFIGS = {
    'package.json', 'requirements.txt', 'Dockerfile', 
    'docker-compose.yml', 'tsconfig.json', 'webpack.config.js',
    'next.config.js', 'vite.config.js', '.env.example',
    'pyproject.toml', 'setup.py', 'Cargo.toml', 'go.mod'
}

class ProjectAnalyzer:
    def __init__(self, anthropic_api_key):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.analysis_start_time = datetime.now()
        
    def analyze_project(self, project_path, output_path):
        """Main analysis pipeline"""
        print(f"Starting project analysis for: {project_path}")
        
        # Ensure output directory exists
        intelligence_dir = os.path.join(output_path, "project_intelligence")
        os.makedirs(intelligence_dir, exist_ok=True)
        
        try:
            # Stage 1: File Structure Analysis
            print("Stage 1: Analyzing file structure...")
            file_structure = self.analyze_file_structure(project_path)
            self.save_json(file_structure, os.path.join(intelligence_dir, "file_structure.json"))
            
            # Stage 2: Deep Claude Analysis (with caching)
            print("Stage 2: Running deep architectural analysis...")
            full_analysis = self.deep_claude_analysis(project_path, file_structure)
            self.save_json(full_analysis, os.path.join(intelligence_dir, "full_analysis.json"))
            
            # Create metadata
            metadata = {
                "analysis_timestamp": self.analysis_start_time.isoformat(),
                "project_path": project_path,
                "total_files_analyzed": len(file_structure.get('file_inventory', [])),
                "analysis_duration_seconds": (datetime.now() - self.analysis_start_time).total_seconds(),
                "claude_model": "claude-sonnet-4-20250514",  # Sonnet 4
                "cache_enabled": True
            }
            self.save_json(metadata, os.path.join(intelligence_dir, "analysis_metadata.json"))
            
            print("✅ Project analysis completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error during project analysis: {str(e)}")
            return False

    def analyze_file_structure(self, project_path):
        """Stage 1: Walk project files and create inventory"""
        file_structure = {
            "timestamp": datetime.now().isoformat(),
            "project_path": project_path,
            "project_name": os.path.basename(project_path),
            "file_tree": {},
            "file_inventory": [],
            "technology_detection": {
                "languages": set(),
                "frameworks": set(),
                "config_files": []
            }
        }
        
        code_files = []
        config_files = []
        
        for root, dirs, files in os.walk(project_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path)
                file_ext = os.path.splitext(file)[1].lower()
                
                # Skip large files
                try:
                    if os.path.getsize(file_path) > 500_000:  # Skip files > 500KB
                        continue
                except:
                    continue
                
                # Important config files
                if file in IMPORTANT_CONFIGS:
                    config_files.append(relative_path)
                    file_structure["technology_detection"]["config_files"].append(file)
                
                # Code files
                elif file_ext in CODE_EXTENSIONS:
                    code_files.append(relative_path)
                    
                    # Detect technologies
                    if file_ext in ['.js', '.jsx', '.ts', '.tsx']:
                        file_structure["technology_detection"]["languages"].add("JavaScript/TypeScript")
                        if file_ext in ['.jsx', '.tsx']:
                            file_structure["technology_detection"]["frameworks"].add("React")
                    elif file_ext in ['.py']:
                        file_structure["technology_detection"]["languages"].add("Python")
                    elif file_ext in ['.vue']:
                        file_structure["technology_detection"]["frameworks"].add("Vue")
                    elif file_ext in ['.svelte']:
                        file_structure["technology_detection"]["frameworks"].add("Svelte")
        
        # Convert sets to lists for JSON serialization
        file_structure["technology_detection"]["languages"] = list(file_structure["technology_detection"]["languages"])
        file_structure["technology_detection"]["frameworks"] = list(file_structure["technology_detection"]["frameworks"])
        
        # Analyze file contents for deeper understanding
        for file_path in code_files[:50]:  # Limit to first 50 files for analysis
            full_path = os.path.join(project_path, file_path)
            file_info = self.analyze_file_content(full_path, file_path)
            if file_info:
                file_structure["file_inventory"].append(file_info)
        
        file_structure["summary"] = {
            "total_code_files": len(code_files),
            "total_config_files": len(config_files),
            "analyzed_files": len(file_structure["file_inventory"])
        }
        
        return file_structure

    def analyze_file_content(self, file_path, relative_path):
        """Extract meaningful information from code files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            file_info = {
                "path": relative_path,
                "type": self.detect_file_type(content, file_ext),
                "size": len(content),
                "lines": len(content.split('\n')),
                "imports": self.extract_imports(content, file_ext),
                "exports": self.extract_exports(content, file_ext),
                "key_elements": self.extract_key_elements(content, file_ext)
            }
            
            return file_info
            
        except Exception as e:
            print(f"Warning: Could not analyze {file_path}: {str(e)}")
            return None

    def detect_file_type(self, content, file_ext):
        """Detect the type/purpose of a file"""
        content_lower = content.lower()
        
        if file_ext in ['.tsx', '.jsx']:
            if 'export default' in content and ('function' in content_lower or 'const' in content_lower):
                return "react_component"
            elif 'export' in content:
                return "react_module"
        elif file_ext in ['.js', '.ts']:
            if 'express' in content_lower or 'app.listen' in content_lower:
                return "express_server"
            elif 'electron' in content_lower:
                return "electron_main"
            elif 'export' in content or 'module.exports' in content:
                return "javascript_module"
        elif file_ext == '.py':
            if 'fastapi' in content_lower or 'flask' in content_lower:
                return "python_api_server"
            elif 'if __name__ == "__main__"' in content:
                return "python_script"
            elif 'class ' in content:
                return "python_class_module"
            else:
                return "python_module"
        elif file_ext in ['.css', '.scss', '.sass']:
            return "stylesheet"
        elif file_ext == '.md':
            return "documentation"
        
        return "code_file"

    def extract_imports(self, content, file_ext):
        """Extract import statements"""
        imports = []
        lines = content.split('\n')
        
        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()
            if file_ext in ['.js', '.jsx', '.ts', '.tsx']:
                if line.startswith('import ') and ' from ' in line:
                    # Extract from "import X from 'Y'" or "import { X } from 'Y'"
                    try:
                        from_part = line.split(' from ')[-1].strip().strip('\'"`;')
                        imports.append(from_part)
                    except:
                        pass
            elif file_ext == '.py':
                if line.startswith('import ') or line.startswith('from '):
                    imports.append(line)
        
        return imports[:10]  # Limit to first 10 imports

    def extract_exports(self, content, file_ext):
        """Extract export statements"""
        exports = []
        
        if file_ext in ['.js', '.jsx', '.ts', '.tsx']:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('export '):
                    exports.append(line[:100])  # Truncate long exports
        
        return exports[:5]  # Limit to first 5 exports

    def extract_key_elements(self, content, file_ext):
        """Extract key functions, classes, components, etc."""
        elements = []
        
        if file_ext in ['.js', '.jsx', '.ts', '.tsx']:
            # Look for function/component definitions
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if (line.startswith('function ') or 
                    line.startswith('const ') and '=>' in line or
                    line.startswith('export function ') or
                    line.startswith('export const ')):
                    elements.append(line[:150])  # Truncate long lines
        elif file_ext == '.py':
            # Look for function and class definitions
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('def ') or line.startswith('class '):
                    elements.append(line[:100])
        
        return elements[:10]  # Limit to first 10 elements

    def deep_claude_analysis(self, project_path, file_structure):
        """Stage 2: Deep analysis using Claude Sonnet 4 with caching"""
        
        # Prepare code content for analysis
        code_chunks = []
        for file_info in file_structure['file_inventory']:
            try:
                full_path = os.path.join(project_path, file_info['path'])
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                code_chunks.append({
                    "file_path": file_info['path'],
                    "file_type": file_info['type'],
                    "content": content[:5000]  # Limit content to 5000 chars per file
                })
            except:
                continue
        
        # Create the analysis prompt
        analysis_prompt = self.create_analysis_prompt(file_structure, code_chunks)
        
        try:
            # Call Claude Sonnet 4 with caching
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Sonnet 4
                max_tokens=8000,
                system=[{
                    "type": "text",
                    "text": analysis_prompt["system_prompt"],
                    "cache_control": {"type": "ephemeral"}  # 5-minute cache
                }],
                messages=[{
                    "role": "user",
                    "content": analysis_prompt["user_content"]
                }]
            )
            
            # Parse Claude's response
            analysis_result = self.parse_claude_response(response.content[0].text)
            
            # Add metadata about the analysis
            analysis_result["_metadata"] = {
                "model_used": "claude-sonnet-4-20250514",
                "cache_creation_tokens": getattr(response.usage, 'cache_creation_input_tokens', 0),
                "cache_read_tokens": getattr(response.usage, 'cache_read_input_tokens', 0),
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            return analysis_result
            
        except Exception as e:
            print(f"Error in Claude analysis: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def create_analysis_prompt(self, file_structure, code_chunks):
        """Create the structured prompt for Claude analysis"""
        
        system_prompt = """You are analyzing a codebase to understand its complete architecture and structure. 

Your task is to analyze the provided file structure and code content to create a comprehensive understanding of how this project works.

Please return your analysis as a valid JSON object with this EXACT structure:

{
  "project_overview": {
    "name": "project name",
    "purpose": "what this project does in 2-3 sentences",
    "architecture_pattern": "overall architecture pattern (e.g., MVC, microservices, etc.)"
  },
  "entry_points": [
    {
      "file": "path/to/entry/file",
      "type": "entry_type (e.g., react_entry, python_main, express_server)",
      "purpose": "what this entry point does",
      "how_to_run": "command to run this entry point",
      "dependencies": ["list", "of", "key", "dependencies"]
    }
  ],
  "data_flows": [
    {
      "from": "source component/module",
      "to": "destination component/module", 
      "method": "communication method (e.g., API, IPC, function call)",
      "purpose": "what data/information flows",
      "files_involved": ["list", "of", "files"]
    }
  ],
  "key_modules": [
    {
      "name": "module name",
      "file": "path/to/file",
      "purpose": "what this module does",
      "dependencies": ["other", "modules", "it", "depends", "on"],
      "interfaces": ["what", "it", "exposes", "or", "provides"]
    }
  ],
  "external_integrations": [
    {
      "service": "external service name",
      "purpose": "why it's used",
      "files": ["files", "that", "use", "this", "service"],
      "type": "integration type (API, database, etc.)"
    }
  ],
  "development_setup": {
    "install_commands": ["npm install", "pip install -r requirements.txt"],
    "run_commands": ["npm start", "python main.py"],
    "build_commands": ["npm run build"],
    "test_commands": ["npm test"]
  },
  "common_patterns": [
    "pattern 1 used throughout the codebase",
    "pattern 2 for handling X",
    "pattern 3 for organizing Y"
  ]
}

Focus on understanding:
1. How to run and develop this project
2. What the main entry points are and how they work
3. How different parts of the code communicate
4. What external services/APIs are used
5. The overall architecture and organization patterns

Be specific and accurate. If you can't determine something definitively, use "unknown" or "not_detected"."""

        # Prepare file structure summary
        file_summary = f"""
PROJECT STRUCTURE:
- Project Name: {file_structure.get('project_name', 'Unknown')}
- Total Files: {file_structure['summary']['total_code_files']} code files, {file_structure['summary']['total_config_files']} config files
- Technologies Detected: {', '.join(file_structure['technology_detection']['languages'])}
- Frameworks: {', '.join(file_structure['technology_detection']['frameworks'])}
- Config Files: {', '.join(file_structure['technology_detection']['config_files'])}

FILE INVENTORY:
"""
        
        for file_info in file_structure['file_inventory']:
            file_summary += f"""
File: {file_info['path']} ({file_info['type']})
- Size: {file_info['size']} chars, {file_info['lines']} lines
- Imports: {file_info['imports'][:3]}
- Key Elements: {file_info['key_elements'][:2]}
"""

        # Prepare code content
        code_content = "\nCODE CONTENT:\n"
        for chunk in code_chunks[:20]:  # Limit to 20 files to avoid token limits
            code_content += f"\n=== FILE: {chunk['file_path']} ({chunk['file_type']}) ===\n"
            code_content += chunk['content']
            code_content += "\n=== END FILE ===\n"

        user_content = file_summary + code_content

        return {
            "system_prompt": system_prompt,
            "user_content": user_content
        }

    def parse_claude_response(self, response_text):
        """Parse Claude's JSON response"""
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # If no JSON found, return the raw response
                return {"raw_response": response_text, "parse_error": "No JSON found"}
                
        except json.JSONDecodeError as e:
            return {"raw_response": response_text, "parse_error": str(e)}

    def save_json(self, data, file_path):
        """Save data as JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved: {file_path}")
        except Exception as e:
            print(f"❌ Error saving {file_path}: {str(e)}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python project_analyzer.py <project_path> <output_path> <anthropic_api_key>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    output_path = sys.argv[2]
    anthropic_api_key = sys.argv[3]
    
    if not os.path.exists(project_path):
        print(f"Error: Project path does not exist: {project_path}")
        sys.exit(1)
    
    analyzer = ProjectAnalyzer(anthropic_api_key)
    success = analyzer.analyze_project(project_path, output_path)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 