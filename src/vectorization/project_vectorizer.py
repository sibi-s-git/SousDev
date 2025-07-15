import os
import json
import logging
from pathlib import Path
import numpy as np
import faiss
from openai import OpenAI
import tiktoken
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectVectorizer:
    def __init__(self, project_path: str, content_folder: str, openai_api_key: str):
        """
        Initialize the project vectorizer
        
        Args:
            project_path: Path to the project to vectorize
            content_folder: Path to the content folder where embeddings will be stored
            openai_api_key: OpenAI API key for embeddings
        """
        self.project_path = Path(project_path)
        self.content_folder = Path(content_folder)
        self.project_name = self.project_path.name
        self.embeddings_folder = self.content_folder / self.project_name / "embeddings"
        
        # Create embeddings folder if it doesn't exist
        self.embeddings_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=openai_api_key)
        
        # Initialize tokenizer for chunk splitting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Chunk settings
        self.chunk_size = 1000  # tokens
        self.chunk_overlap = 200  # tokens
        
        # File extensions to process
        self.text_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.scss', '.sass',
            '.json', '.md', '.txt', '.yml', '.yaml', '.xml', '.sql', '.sh', '.bat',
            '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs',
            '.swift', '.kt', '.scala', '.r', '.m', '.mm', '.dart', '.vue', '.svelte'
        }
        
        # Directories to ignore
        self.ignore_dirs = {
            'node_modules', '.git', '.svn', '.hg', '__pycache__', '.pytest_cache',
            'dist', 'build', 'target', 'bin', 'obj', '.next', '.nuxt', 'coverage',
            '.vscode', '.idea', 'logs', 'temp', 'tmp', '.DS_Store', 'Thumbs.db'
        }
        
        # Files to ignore
        self.ignore_files = {
            '.gitignore', '.gitattributes', '.env', '.env.local', '.env.production',
            'package-lock.json', 'yarn.lock', 'Pipfile.lock', 'poetry.lock'
        }

    def should_process_file(self, file_path: Path) -> bool:
        """Check if a file should be processed"""
        # Check if file extension is supported
        if file_path.suffix.lower() not in self.text_extensions:
            return False
            
        # Check if file is in ignore list
        if file_path.name in self.ignore_files:
            return False
            
        # Check if any parent directory is in ignore list
        for parent in file_path.parents:
            if parent.name in self.ignore_dirs:
                return False
                
        return True

    def read_file_content(self, file_path: Path) -> Optional[str]:
        """Read and return file content"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
                    
            logger.warning(f"Could not decode file: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None

    def split_text_into_chunks(self, text: str, file_path: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks"""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        start = 0
        chunk_id = 0
        
        while start < len(tokens):
            # Calculate end position
            end = min(start + self.chunk_size, len(tokens))
            
            # Get chunk tokens
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            # Create chunk metadata
            chunk = {
                'id': f"{file_path}_{chunk_id}",
                'file_path': file_path,
                'chunk_id': chunk_id,
                'text': chunk_text,
                'start_token': start,
                'end_token': end,
                'token_count': len(chunk_tokens)
            }
            
            chunks.append(chunk)
            chunk_id += 1
            
            # Move start position for next chunk (with overlap)
            start = end - self.chunk_overlap
            
            # If we're at the end, break
            if end >= len(tokens):
                break
                
        return chunks

    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for a list of texts"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            
            embeddings = []
            for data in response.data:
                embeddings.append(data.embedding)
                
            return np.array(embeddings, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            raise

    def vectorize_project(self) -> Dict[str, Any]:
        """Vectorize the entire project"""
        logger.info(f"Starting vectorization of project: {self.project_path}")
        
        # Collect all files to process
        all_chunks = []
        file_stats = {}
        
        # Walk through project directory
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and self.should_process_file(file_path):
                relative_path = str(file_path.relative_to(self.project_path))
                
                # Read file content
                content = self.read_file_content(file_path)
                if content is None:
                    continue
                    
                # Split into chunks
                chunks = self.split_text_into_chunks(content, relative_path)
                all_chunks.extend(chunks)
                
                file_stats[relative_path] = {
                    'size_bytes': file_path.stat().st_size,
                    'chunk_count': len(chunks),
                    'extension': file_path.suffix
                }
                
                logger.info(f"Processed {relative_path}: {len(chunks)} chunks")
        
        if not all_chunks:
            logger.warning("No files found to vectorize")
            return {"status": "no_files", "message": "No supported files found in project"}
        
        logger.info(f"Total chunks to embed: {len(all_chunks)}")
        
        # Create embeddings in batches
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i:i + batch_size]
            batch_texts = [chunk['text'] for chunk in batch_chunks]
            
            logger.info(f"Creating embeddings for batch {i//batch_size + 1}/{(len(all_chunks) + batch_size - 1)//batch_size}")
            batch_embeddings = self.create_embeddings(batch_texts)
            all_embeddings.append(batch_embeddings)
        
        # Combine all embeddings
        embeddings_matrix = np.vstack(all_embeddings)
        
        # Create FAISS index
        dimension = embeddings_matrix.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings_matrix)
        
        # Add embeddings to index
        index.add(embeddings_matrix)
        
        # Save FAISS index
        index_path = self.embeddings_folder / "embeddings.index"
        faiss.write_index(index, str(index_path))
        
        # Save chunks metadata
        chunks_metadata = {
            'chunks': all_chunks,
            'total_chunks': len(all_chunks),
            'embedding_dimension': dimension,
            'project_path': str(self.project_path),
            'project_name': self.project_name
        }
        
        metadata_path = self.embeddings_folder / "chunks_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(chunks_metadata, f, indent=2)
        
        # Save file statistics
        stats_path = self.embeddings_folder / "file_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(file_stats, f, indent=2)
        
        # Save vectorization info
        vectorization_info = {
            'status': 'completed',
            'total_files': len(file_stats),
            'total_chunks': len(all_chunks),
            'embedding_dimension': dimension,
            'model': 'text-embedding-3-small',
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'embeddings_path': str(index_path),
            'metadata_path': str(metadata_path),
            'stats_path': str(stats_path)
        }
        
        info_path = self.embeddings_folder / "vectorization_info.json"
        with open(info_path, 'w') as f:
            json.dump(vectorization_info, f, indent=2)
        
        logger.info(f"Vectorization completed successfully!")
        logger.info(f"Processed {len(file_stats)} files into {len(all_chunks)} chunks")
        logger.info(f"Embeddings saved to: {index_path}")
        
        return vectorization_info


def main():
    """Main function to run vectorization from command line"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Vectorize a project directory")
    parser.add_argument("project_path", help="Path to the project directory")
    parser.add_argument("content_folder", help="Path to the content folder")
    parser.add_argument("openai_api_key", help="OpenAI API key")
    
    args = parser.parse_args()
    
    try:
        vectorizer = ProjectVectorizer(
            project_path=args.project_path,
            content_folder=args.content_folder,
            openai_api_key=args.openai_api_key
        )
        
        result = vectorizer.vectorize_project()
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main() 