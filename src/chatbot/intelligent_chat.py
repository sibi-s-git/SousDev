#!/usr/bin/env python3
"""
Intelligent Chat System for SousDev
Uses Claude Haiku 3.5 to analyze user queries and search for relevant code
"""

import os
import sys
import json
import base64
from datetime import datetime
import anthropic
from dotenv import load_dotenv

# Add the parent directory to sys.path so we can import from vectorization
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vectorization.project_search import search_similar_content

# Load environment variables
load_dotenv()

class IntelligentChat:
    def __init__(self, anthropic_api_key):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        
    def process_chat(self, user_message, images, project_path, content_path):
        """Main chat processing pipeline"""
        try:
            print("\n" + "🚀 " + "="*78, file=sys.stderr)
            print("🤖 SOUSDEV INTELLIGENT CHAT PROCESSING STARTED", file=sys.stderr)
            print("="*80, file=sys.stderr)
            print(f"📁 Project Path: {project_path}", file=sys.stderr)
            print(f"📂 Content Path: {content_path}", file=sys.stderr)
            print(f"💬 User Message: {user_message[:100]}{'...' if len(user_message) > 100 else ''}", file=sys.stderr)
            print(f"🖼️  Images: {len(images) if images else 0}", file=sys.stderr)
            print("="*80, file=sys.stderr)
            
            # Step 1: Load project intelligence
            print("\n📊 STEP 1: Loading project intelligence...", file=sys.stderr)
            project_intelligence = self.load_project_intelligence(content_path)
            if not project_intelligence:
                print("❌ Project intelligence not found!", file=sys.stderr)
                return {"error": "Project intelligence not found. Please run project analysis first."}
            print(f"✅ Project intelligence loaded: {len(project_intelligence)} keys", file=sys.stderr)
            
            # Step 2: Use Claude Haiku to analyze what we need to search for
            print("\n🧠 STEP 2: Generating search strategy with Claude...", file=sys.stderr)
            search_strategy = self.generate_search_strategy(
                user_message, 
                images, 
                project_intelligence
            )
            
            if "error" in search_strategy:
                print("❌ Failed to generate search strategy!", file=sys.stderr)
                return search_strategy
            
            # Step 3: Execute vector searches based on Claude's recommendations
            print("\n🔍 STEP 3: Executing vector searches...", file=sys.stderr)
            search_results = self.execute_searches(search_strategy["searches"], content_path)
            
            # Step 4: Use Claude Haiku to analyze everything together (with caching)
            print("\n💡 STEP 4: Generating final intelligent response...", file=sys.stderr)
            final_response = self.generate_final_response(
                user_message,
                images,
                project_intelligence,
                search_strategy,
                search_results
            )
            
            print("\n🎉 INTELLIGENT CHAT PROCESSING COMPLETED!", file=sys.stderr)
            print("="*80, file=sys.stderr)
            print(f"📊 Search Queries Used: {len(search_strategy.get('searches', []))}", file=sys.stderr)
            print(f"📚 Code Snippets Found: {len(search_results)}", file=sys.stderr)
            print(f"📝 Response Length: {len(final_response)} characters", file=sys.stderr)
            print("🚀 Sending response to chat visualizer...", file=sys.stderr)
            print("="*80 + "\n", file=sys.stderr)
            
            return {
                "success": True,
                "response": final_response,
                "search_strategy": search_strategy,
                "search_results_count": len(search_results),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"\n❌ ERROR IN INTELLIGENT CHAT: {str(e)}", file=sys.stderr)
            print("="*80 + "\n", file=sys.stderr)
            return {"error": str(e)}
    
    def load_project_intelligence(self, content_path):
        """Load the project intelligence data"""
        try:
            intelligence_path = os.path.join(content_path, "project_intelligence", "full_analysis.json")
            if not os.path.exists(intelligence_path):
                print(f"Project intelligence not found at: {intelligence_path}", file=sys.stderr)
                return None
                
            with open(intelligence_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading project intelligence: {str(e)}", file=sys.stderr)
            return None
    
    def generate_search_strategy(self, user_message, images, project_intelligence):
        """Use Claude Haiku to determine what to search for"""
        
        # Prepare the system prompt with project context
        system_prompt = f"""You are an intelligent code assistant analyzing a user's request.

PROJECT CONTEXT:
{json.dumps(project_intelligence, indent=2)[:3000]}  

Your task is to analyze the user's message and determine what specific code files/snippets would be most relevant to help answer their question or complete their request.

IMPORTANT: Only suggest 3-5 specific search queries. Be precise and focused - we don't want to overload with too many results.

Return your response as a JSON object with this exact structure:
{{
  "searches": [
    "specific search query 1",
    "specific search query 2", 
    "specific search query 3"
  ],
  "reasoning": "Brief explanation of why these searches are relevant"
}}

Focus on finding the most essential files/code patterns needed for this specific request."""

        # Prepare user content
        user_content = []
        user_content.append({
            "type": "text",
            "text": f"User request: {user_message}"
        })
        
        # Add images if present
        if images:
            for i, image_data in enumerate(images):
                # Convert image data to base64 if needed
                if isinstance(image_data, str) and image_data.startswith('data:image'):
                    # Extract base64 data
                    image_base64 = image_data.split(',')[1]
                    image_type = image_data.split(';')[0].split(':')[1]
                else:
                    image_base64 = image_data
                    image_type = "image/jpeg"  # default
                
                user_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_type,
                        "data": image_base64
                    }
                })
        
        try:
            print("\n" + "="*80, file=sys.stderr)
            print("🔍 GENERATING SEARCH STRATEGY", file=sys.stderr)
            print("="*80, file=sys.stderr)
            print(f"SYSTEM PROMPT:\n{system_prompt}", file=sys.stderr)
            print(f"\nUSER MESSAGE: {user_message}", file=sys.stderr)
            if images:
                print(f"IMAGES ATTACHED: {len(images)}", file=sys.stderr)
            print("\n" + "-"*50, file=sys.stderr)
            
            # Call Claude Haiku 3.5 for search strategy
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1000,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_content
                }]
            )
            
            # Parse the JSON response
            response_text = response.content[0].text
            
            print(f"CLAUDE SEARCH STRATEGY RESPONSE:\n{response_text}", file=sys.stderr)
            print("="*80 + "\n", file=sys.stderr)
            
            search_strategy = self.parse_json_response(response_text)
            
            if search_strategy and "searches" in search_strategy:
                print(f"✅ Generated search strategy: {search_strategy['searches']}", file=sys.stderr)
                return search_strategy
            else:
                return {"error": "Failed to generate valid search strategy"}
                
        except Exception as e:
            print(f"Error generating search strategy: {str(e)}", file=sys.stderr)
            return {"error": f"Search strategy generation failed: {str(e)}"}
    
    def execute_searches(self, search_queries, content_path):
        """Execute multiple vector searches and combine results"""
        all_results = []
        embeddings_path = os.path.join(content_path, "embeddings")
        
        if not os.path.exists(embeddings_path):
            print(f"Embeddings not found at: {embeddings_path}", file=sys.stderr)
            return []
        
        print("\n" + "="*80, file=sys.stderr)
        print("🔎 EXECUTING VECTOR SEARCHES", file=sys.stderr)
        print("="*80, file=sys.stderr)
        
        for query in search_queries:
            try:
                print(f"\n🔍 Searching for: '{query}'", file=sys.stderr)
                results = search_similar_content(query, embeddings_path, k=3)  # Get top 3 for each search
                
                print(f"   Found {len(results)} results:", file=sys.stderr)
                for i, result in enumerate(results, 1):
                    print(f"   {i}. {result.get('file_path', 'unknown file')} (score: {result.get('similarity_score', 0):.3f})", file=sys.stderr)
                    print(f"      Content preview: {result.get('content', '')[:100]}...", file=sys.stderr)
                
                for result in results:
                    # Add search query context to each result
                    result["search_query"] = query
                    all_results.append(result)
                    
            except Exception as e:
                print(f"❌ Error searching for '{query}': {str(e)}", file=sys.stderr)
                continue
        
        print(f"\n✅ Total results found: {len(all_results)}", file=sys.stderr)
        print("="*80 + "\n", file=sys.stderr)
        
        # Remove duplicates based on file path and content similarity
        unique_results = self.deduplicate_results(all_results)
        
        # Limit to top 10 results to avoid overloading
        return unique_results[:10]
    
    def deduplicate_results(self, results):
        """Remove duplicate search results"""
        seen_content = set()
        unique_results = []
        
        for result in results:
            # Create a simple hash of the content
            content_hash = hash(result.get("content", "")[:200])  # Use first 200 chars
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def generate_final_response(self, user_message, images, project_intelligence, search_strategy, search_results):
        """Generate the final response using all gathered information"""
        
        # Prepare cached system context
        system_context = f"""You are SousDev, an intelligent coding assistant with deep understanding of this specific project.

PROJECT INTELLIGENCE:
{json.dumps(project_intelligence, indent=2)[:2000]}

SEARCH STRATEGY USED:
{json.dumps(search_strategy, indent=2)}

RELEVANT CODE FOUND:
{self.format_search_results(search_results)}

Provide a comprehensive, helpful response to the user's request. Reference specific files and code when relevant. Be practical and actionable."""

        # Prepare user content for final analysis
        user_content = []
        user_content.append({
            "type": "text", 
            "text": f"Original request: {user_message}\n\nPlease provide a detailed analysis and response based on the project context and code found."
        })
        
        # Add images if present
        if images:
            for image_data in images:
                if isinstance(image_data, str) and image_data.startswith('data:image'):
                    image_base64 = image_data.split(',')[1]
                    image_type = image_data.split(';')[0].split(':')[1]
                else:
                    image_base64 = image_data
                    image_type = "image/jpeg"
                
                user_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_type, 
                        "data": image_base64
                    }
                })
        
        try:
            print("\n" + "="*80, file=sys.stderr)
            print("💬 GENERATING FINAL RESPONSE", file=sys.stderr)
            print("="*80, file=sys.stderr)
            print(f"SYSTEM CONTEXT:\n{system_context}", file=sys.stderr)
            print(f"\nFINAL USER REQUEST: {user_message}", file=sys.stderr)
            if images:
                print(f"IMAGES ATTACHED: {len(images)}", file=sys.stderr)
            print("\n" + "-"*50, file=sys.stderr)
            
            # Call Claude Haiku with caching for final response
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=3000,
                system=[{
                    "type": "text",
                    "text": system_context,
                    "cache_control": {"type": "ephemeral"}  # Cache the project context
                }],
                messages=[{
                    "role": "user",
                    "content": user_content
                }]
            )
            
            final_response = response.content[0].text
            
            print(f"CLAUDE FINAL RESPONSE:\n{final_response}", file=sys.stderr)
            print("="*80 + "\n", file=sys.stderr)
            print("✅ Response generated successfully! Sending to chat visualizer...", file=sys.stderr)
            
            return final_response
            
        except Exception as e:
            print(f"Error generating final response: {str(e)}", file=sys.stderr)
            return f"I found relevant code for your request, but encountered an error generating the response: {str(e)}"
    
    def format_search_results(self, search_results):
        """Format search results for Claude's context"""
        formatted = ""
        for i, result in enumerate(search_results, 1):
            formatted += f"\n--- RESULT {i} (Query: {result.get('search_query', 'unknown')}) ---\n"
            formatted += f"File: {result.get('file_path', 'unknown')}\n"
            formatted += f"Content: {result.get('content', '')[:500]}...\n"  # Limit content length
        
        return formatted[:4000]  # Limit total context length
    
    def parse_json_response(self, response_text):
        """Parse JSON from Claude's response"""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return None
                
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {str(e)}", file=sys.stderr)
            return None

def main():
    if len(sys.argv) != 6:
        print("Usage: python intelligent_chat.py <user_message> <images_json> <project_path> <content_path> <anthropic_api_key>", file=sys.stderr)
        sys.exit(1)
    
    user_message = sys.argv[1]
    images_json = sys.argv[2]
    project_path = sys.argv[3]
    content_path = sys.argv[4]
    anthropic_api_key = sys.argv[5]
    
    # Parse images
    try:
        images = json.loads(images_json) if images_json and images_json != "null" else []
    except:
        images = []
    
    chat_processor = IntelligentChat(anthropic_api_key)
    result = chat_processor.process_chat(user_message, images, project_path, content_path)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 