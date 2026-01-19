import logging
from typing import Dict, Any
from langchain_groq import ChatGroq
from services.rag_service import rag_service
from graph.state import OpsState

logger = logging.getLogger("backend.graph.rag_agent")

# Initialize LLM for RAG responses
try:
    rag_llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
    )
except Exception as e:
    logger.error(f"Failed to initialize RAG LLM: {e}")
    rag_llm = None


def rag_agent(state: OpsState) -> Dict[str, Any]:
    """
    RAG Agent: Search company documents first before using web search.
    
    This agent:
    1. Searches the vector database for relevant company documents
    2. If found, uses LLM to generate answer from company docs
    3. If not found or insufficient, returns None to trigger RFI agent
    """
    ticket_id = state.ticket_id or "unknown"
    description = state.description or ""
    
    logger.info(f"RAG Agent processing ticket {ticket_id}: {description}")
    
    try:
        # Search vector database
        search_results = rag_service.search(description, k=3)
        
        if not search_results:
            logger.info(f"No relevant documents found for ticket {ticket_id}")
            return {
                **state.dict(),
                "rag_found": False,
                "rag_results": None,
            }
        
        # Check if results are relevant enough (score threshold)
        # Lower score is better for FAISS L2 distance
        relevant_results = [r for r in search_results if r["score"] < 1.5]
        
        if not relevant_results:
            logger.info(f"No highly relevant documents for ticket {ticket_id}")
            return {
                **state.dict(),
                "rag_found": False,
                "rag_results": None,
            }
        
        # Format context from retrieved documents
        context = "\n\n".join([
            f"Document: {r['metadata'].get('filename', 'unknown')}\n{r['content']}"
            for r in relevant_results
        ])
        
        # Generate answer using LLM
        if rag_llm:
            prompt = f"""Based on the following company documents, provide a clear and concise answer to the question.
If the documents don't contain enough information to answer, say so.

Question: {description}

Company Documents:
{context}

Answer:"""
            
            response = rag_llm.invoke(prompt)
            answer = response.content
            
            # Check if LLM indicated insufficient information
            insufficient_indicators = [
                "don't contain enough",
                "do not contain enough",
                "not enough information",
                "cannot find",
                "unable to answer",
                "insufficient",
                "does not mention",
                "do not mention",
            ]
            
            if any(indicator in answer.lower() for indicator in insufficient_indicators):
                logger.info(f"RAG answer insufficient for ticket {ticket_id}, will fallback to RFI agent")
                return {
                    **state.dict(),
                    "rag_found": False,
                    "rag_results": None,
                }
            
            # Format sources
            sources = [
                f"- {r['metadata'].get('filename', 'unknown')}"
                for r in relevant_results
            ]
            
            work_comments = f"{answer}\n\nSources:\n" + "\n".join(sources)
            
            logger.info(f"RAG Agent successfully answered ticket {ticket_id}")
            
            return {
                **state.dict(),
                "rag_found": True,
                "assigned_to": "RAG Agent",
                "work_comments": work_comments,
                "result": "RFI answered from company documents",
                "closed": True,
            }
        else:
            # No LLM available, just return the raw context
            logger.warning("RAG LLM not available, returning raw context")
            sources = [f"- {r['metadata'].get('filename', 'unknown')}" for r in relevant_results]
            work_comments = f"Relevant information found:\n\n{context}\n\nSources:\n" + "\n".join(sources)
            
            return {
                **state.dict(),
                "rag_found": True,
                "assigned_to": "RAG Agent",
                "work_comments": work_comments,
                "result": "RFI answered from company documents",
                "closed": True,
            }
            
    except Exception as e:
        logger.error(f"RAG Agent failed for ticket {ticket_id}: {e}", exc_info=True)
        # On error, return state unchanged to allow fallback to RFI agent
        return {
            **state.dict(),
            "rag_found": False,
            "rag_results": None,
        }
