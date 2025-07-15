import os
import json
import logging
from pathlib import Path
import numpy as np
import faiss
from openai import OpenAI
import tiktoken
from typing import List, Dict, Any, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectSearch:
    def __init__(self, project_name: str, content_folder: str, openai_api_key: str):
        """
        Initialize the project search system
        
        Args:
            project_name: Name of the project to search
            content_folder: Path to the content folder
            openai_api_key: OpenAI API key for query embeddings
        """
        self.project_name = project_name
        self.content_folder = Path(content_folder)
        self.embeddings_folder = self.content_folder / project_name / "embeddings"
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=openai_api_key)
        
        # Load the FAISS index and metadata
        self._load_index_and_metadata()

    def _load_index_and_metadata(self):
        """Load the FAISS index and chunk metadata"""
        try:
            # Load FAISS index
            index_path = self.embeddings_folder / "embeddings.index"
            if not index_path.exists():
                raise FileNotFoundError(f"No embeddings index found at: {index_path}")
            
            self.index = faiss.read_index(str(index_path))
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            
            # Load chunks metadata
            metadata_path = self.embeddings_folder / "chunks_metadata.json"
            if not metadata_path.exists():
                raise FileNotFoundError(f"No metadata found at: {metadata_path}")
            
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            
            self.chunks = self.metadata['chunks']
            logger.info(f"Loaded metadata for {len(self.chunks)} chunks")
            
            # Load vectorization info
            info_path = self.embeddings_folder / "vectorization_info.json"
            if info_path.exists():
                with open(info_path, 'r') as f:
                    self.vectorization_info = json.load(f)
            else:
                self.vectorization_info = {}
                
        except Exception as e:
            logger.error(f"Error loading index and metadata: {e}")
            raise

    def create_query_embedding(self, query: str) -> np.ndarray:
        """Create embedding for a search query"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=[query]
            )
            
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            # Normalize for cosine similarity
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error creating query embedding: {e}")
            raise

    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks based on a query
        
        Args:
            query: Search query
            top_k: Number of top results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of relevant chunks with metadata and scores
        """
        try:
            # Create query embedding
            query_embedding = self.create_query_embedding(query)
            
            # Search the index
            scores, indices = self.index.search(query_embedding.reshape(1, -1), top_k)
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if score < score_threshold:
                    continue
                    
                if idx < len(self.chunks):
                    chunk = self.chunks[idx].copy()
                    chunk['similarity_score'] = float(score)
                    chunk['rank'] = i + 1
                    results.append(chunk)
            
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise

    def search_by_file_extension(self, query: str, file_extensions: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search within specific file types"""
        all_results = self.search(query, top_k * 3)  # Get more results to filter
        
        filtered_results = []
        for result in all_results:
            file_path = result['file_path']
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in file_extensions:
                filtered_results.append(result)
                
            if len(filtered_results) >= top_k:
                break
                
        return filtered_results

    def get_project_summary(self) -> Dict[str, Any]:
        """Get a summary of the vectorized project"""
        return {
            'project_name': self.project_name,
            'total_chunks': len(self.chunks),
            'total_vectors': self.index.ntotal,
            'embedding_dimension': self.index.d,
            'vectorization_info': self.vectorization_info,
            'files_by_extension': self._get_files_by_extension()
        }

    def _get_files_by_extension(self) -> Dict[str, int]:
        """Get count of files by extension"""
        extension_counts = {}
        processed_files = set()
        
        for chunk in self.chunks:
            file_path = chunk['file_path']
            if file_path not in processed_files:
                processed_files.add(file_path)
                ext = Path(file_path).suffix.lower()
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
                
        return extension_counts

    def get_file_chunks(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific file"""
        return [chunk for chunk in self.chunks if chunk['file_path'] == file_path]


def search_similar_content(query: str, embeddings_path: str, k: int = 5, openai_api_key: str = None) -> List[Dict[str, Any]]:
    """
    Standalone function to search for similar content using the embeddings
    
    Args:
        query: Search query
        embeddings_path: Path to the embeddings folder 
        k: Number of results to return
        openai_api_key: OpenAI API key (if not provided, will try to get from environment)
        
    Returns:
        List of search results
    """
    try:
        # Get OpenAI API key from environment if not provided
        if openai_api_key is None:
            openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_api_key:
            raise ValueError("OpenAI API key not provided and not found in environment variables")
        
        # Extract project name and content folder from embeddings path
        embeddings_path = Path(embeddings_path)
        project_name = embeddings_path.parent.name
        content_folder = embeddings_path.parent.parent
        
        # Create searcher instance and perform search
        searcher = ProjectSearch(
            project_name=project_name,
            content_folder=str(content_folder),
            openai_api_key=openai_api_key
        )
        
        return searcher.search(query, top_k=k)
        
    except Exception as e:
        logger.error(f"Error in search_similar_content: {e}")
        return []


def main():
    """Main function for command line usage"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Search through vectorized project")
    parser.add_argument("project_name", help="Name of the project to search")
    parser.add_argument("content_folder", help="Path to the content folder")
    parser.add_argument("openai_api_key", help="OpenAI API key")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--threshold", type=float, default=0.0, help="Minimum similarity score")
    
    args = parser.parse_args()
    
    try:
        searcher = ProjectSearch(
            project_name=args.project_name,
            content_folder=args.content_folder,
            openai_api_key=args.openai_api_key
        )
        
        results = searcher.search(args.query, args.top_k, args.threshold)
        
        output = {
            "query": args.query,
            "results": results,
            "total_results": len(results)
        }
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main() 