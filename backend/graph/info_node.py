import logging
from typing import Dict, Any
from langchain_groq import ChatGroq
from services.confluence_mcp import confluence_client
from graph.state import OpsState

logger = logging.getLogger("backend.graph.info_agent")

# Initialize LLM for info validation
try:
    info_llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
    )
except Exception as e:
    logger.error(f"Failed to initialize Info Agent LLM: {e}")
    info_llm = None


def info_agent(state: OpsState) -> Dict[str, Any]:
    """
    Info Agent: Search Confluence MCP server for company information.
    
    This agent:
    1. Searches Confluence for relevant documentation
    2. Uses LLM to validate and format the information
    3. If valid information found, closes ticket with answer
    4. If no valid information, returns None for fallback
    """
    ticket_id = state.ticket_id or "unknown"
    description = state.description or ""
    
    logger.info(f"Info Agent processing ticket {ticket_id}: {description}")
    
    try:
        # Search Confluence MCP server
        search_results = confluence_client.search(description, max_results=3)
        
        if not search_results:
            logger.info(f"No Confluence results found for ticket {ticket_id}")
            return {
                **state.dict(),
                "info_found": False,
                "info_results": None,
            }
        
        # Format context from Confluence results
        context = "\n\n".join([
            f"Page: {r['title']} (Space: {r.get('space', 'Unknown')})\n{r['content']}"
            for r in search_results
        ])
        
        # Use LLM to validate and generate answer
        if info_llm:
            prompt = f"""You are a company information assistant. Based on the Confluence documentation below, provide a clear and accurate answer to the question.

IMPORTANT: 
- If the documentation contains relevant information, provide a complete answer
- If the documentation does NOT contain enough information or is not relevant, respond with exactly: "INSUFFICIENT_INFO"
- Be thorough and include specific details from the documentation

Question: {description}

Confluence Documentation:
{context}

Answer:"""
            
            response = info_llm.invoke(prompt)
            answer = response.content.strip()
            
            # Check if LLM indicated insufficient information
            if "INSUFFICIENT_INFO" in answer.upper() or answer.upper().startswith("INSUFFICIENT"):
                logger.info(f"Info Agent: Insufficient information for ticket {ticket_id}")
                return {
                    **state.dict(),
                    "info_found": False,
                    "info_results": None,
                }
            
            # Format sources
            sources = [
                f"- [{r['title']}]({r['url']}) (Space: {r.get('space', 'Unknown')})"
                for r in search_results
            ]
            
            work_comments = f"{answer}\n\n**Confluence Sources:**\n" + "\n".join(sources)
            
            logger.info(f"Info Agent successfully answered ticket {ticket_id} from Confluence")
            
            return {
                **state.dict(),
                "info_found": True,
                "assigned_to": "Info Agent",
                "work_comments": work_comments,
                "result": "Information request answered from Confluence",
                "closed": True,
            }
        else:
            # No LLM available, return raw context
            logger.warning("Info Agent LLM not available, returning raw Confluence data")
            sources = [f"- [{r['title']}]({r['url']})" for r in search_results]
            work_comments = f"Found relevant information:\n\n{context}\n\n**Sources:**\n" + "\n".join(sources)
            
            return {
                **state.dict(),
                "info_found": True,
                "assigned_to": "Info Agent",
                "work_comments": work_comments,
                "result": "Information found in Confluence",
                "closed": True,
            }
            
    except Exception as e:
        logger.error(f"Info Agent failed for ticket {ticket_id}: {e}", exc_info=True)
        # On error, return state unchanged to allow fallback
        return {
            **state.dict(),
            "info_found": False,
            "info_results": None,
        }
