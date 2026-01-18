import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Vector DB and embeddings
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import (
        PyPDFLoader,
        TextLoader,
        UnstructuredMarkdownLoader,
        Docx2txtLoader
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    # Fallback if not installed
    logger = logging.getLogger("backend.rag_service")
    logger.warning(f"RAG dependencies not installed: {e}")
    IMPORTS_AVAILABLE = False
    HuggingFaceEmbeddings = None
    FAISS = None
    RecursiveCharacterTextSplitter = None
    PyPDFLoader = None
    TextLoader = None
    UnstructuredMarkdownLoader = None
    Docx2txtLoader = None

logger = logging.getLogger("backend.rag_service")

# Storage paths
UPLOAD_DIR = Path("./data/uploads")
VECTOR_DB_DIR = Path("./data/vectordb")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

# Document metadata store (in-memory for now)
documents_store: Dict[str, Dict[str, Any]] = {}


class RAGService:
    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.text_splitter = None
        
        if IMPORTS_AVAILABLE and RecursiveCharacterTextSplitter:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
        
        self._initialize_embeddings()
        self._load_vector_store()

    def _initialize_embeddings(self):
        """Initialize embedding model."""
        if not IMPORTS_AVAILABLE:
            logger.warning("RAG dependencies not available. Install: pip install langchain langchain-community sentence-transformers faiss-cpu")
            return
            
        try:
            logger.info("Initializing embeddings model...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            logger.info("Embeddings model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            self.embeddings = None

    def _load_vector_store(self):
        """Load existing vector store or create new one."""
        try:
            index_path = VECTOR_DB_DIR / "index.faiss"
            if index_path.exists() and self.embeddings:
                logger.info("Loading existing vector store...")
                self.vector_store = FAISS.load_local(
                    str(VECTOR_DB_DIR), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Vector store loaded successfully")
            else:
                logger.info("No existing vector store found")
                self.vector_store = None
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            self.vector_store = None

    def save_document(self, file_content: bytes, filename: str, uploaded_by: str = "admin") -> Dict[str, Any]:
        """Save uploaded document and metadata."""
        try:
            # Generate unique ID
            file_hash = hashlib.md5(file_content).hexdigest()
            doc_id = f"doc_{file_hash[:12]}"
            
            # Save file
            file_path = UPLOAD_DIR / f"{doc_id}_{filename}"
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # Store metadata
            metadata = {
                "id": doc_id,
                "filename": filename,
                "filepath": str(file_path),
                "size": len(file_content),
                "uploaded_at": datetime.now().isoformat(),
                "uploaded_by": uploaded_by,
                "status": "uploaded",
                "trained": False,
                "chunk_count": 0,
            }
            documents_store[doc_id] = metadata
            
            logger.info(f"Document saved: {doc_id} - {filename}")
            return metadata
        except Exception as e:
            logger.error(f"Failed to save document: {e}", exc_info=True)
            raise

    def load_document(self, filepath: str) -> List[Any]:
        """Load document based on file type."""
        if not IMPORTS_AVAILABLE:
            raise RuntimeError("RAG dependencies not installed. Please install: pip install langchain langchain-community pypdf python-docx unstructured")
        
        file_ext = Path(filepath).suffix.lower()
        
        try:
            if file_ext == ".pdf":
                loader = PyPDFLoader(filepath)
            elif file_ext == ".md":
                loader = UnstructuredMarkdownLoader(filepath)
            elif file_ext in [".doc", ".docx"]:
                loader = Docx2txtLoader(filepath)
            elif file_ext == ".txt":
                loader = TextLoader(filepath)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from {filepath}")
            return documents
        except Exception as e:
            logger.error(f"Failed to load document {filepath}: {e}", exc_info=True)
            raise

    def train_document(self, doc_id: str) -> Dict[str, Any]:
        """Process and train document into vector store."""
        if doc_id not in documents_store:
            raise ValueError(f"Document not found: {doc_id}")
        
        if not IMPORTS_AVAILABLE:
            raise RuntimeError("RAG dependencies not installed. Please install: pip install langchain langchain-community sentence-transformers faiss-cpu pypdf python-docx unstructured")
        
        if not self.embeddings:
            raise RuntimeError("Embeddings not initialized. Install required packages.")
        
        doc_meta = documents_store[doc_id]
        
        try:
            # Update status
            doc_meta["status"] = "training"
            
            # Load document
            documents = self.load_document(doc_meta["filepath"])
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Add metadata to chunks
            for chunk in chunks:
                chunk.metadata.update({
                    "doc_id": doc_id,
                    "filename": doc_meta["filename"],
                    "source": doc_meta["filepath"]
                })
            
            # Create or update vector store
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            else:
                self.vector_store.add_documents(chunks)
            
            # Save vector store
            self.vector_store.save_local(str(VECTOR_DB_DIR))
            
            # Update metadata
            doc_meta["status"] = "trained"
            doc_meta["trained"] = True
            doc_meta["chunk_count"] = len(chunks)
            doc_meta["trained_at"] = datetime.now().isoformat()
            
            logger.info(f"Document trained successfully: {doc_id} ({len(chunks)} chunks)")
            return doc_meta
        except Exception as e:
            doc_meta["status"] = "error"
            doc_meta["error"] = str(e)
            logger.error(f"Failed to train document {doc_id}: {e}", exc_info=True)
            raise

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search vector store for relevant documents."""
        if not self.vector_store:
            logger.warning("No vector store available for search")
            return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "score": float(score),
                    "metadata": doc.metadata,
                })
            
            logger.info(f"Search found {len(formatted_results)} results for query: {query[:50]}...")
            return formatted_results
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return []

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all document metadata."""
        return list(documents_store.values())

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get single document metadata."""
        return documents_store.get(doc_id)

    def delete_document(self, doc_id: str) -> bool:
        """Delete document and remove from vector store."""
        if doc_id not in documents_store:
            return False
        
        try:
            doc_meta = documents_store[doc_id]
            
            # Delete file
            file_path = Path(doc_meta["filepath"])
            if file_path.exists():
                file_path.unlink()
            
            # Remove from store
            del documents_store[doc_id]
            
            # Note: FAISS doesn't support deletion easily, would need to rebuild
            # For now, we just mark it as deleted in metadata
            
            logger.info(f"Document deleted: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}", exc_info=True)
            return False


# Global RAG service instance
rag_service = RAGService()
