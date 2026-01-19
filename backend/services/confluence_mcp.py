import logging
import os
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger("backend.services.confluence_mcp")

# Confluence MCP configuration
CONFLUENCE_MCP_URL = os.getenv("CONFLUENCE_MCP_URL", "http://localhost:3001")
CONFLUENCE_ENABLED = os.getenv("CONFLUENCE_ENABLED", "true").lower() == "true"


class ConfluenceMCPClient:
    """Client for interacting with Confluence MCP server."""
    
    def __init__(self):
        self.enabled = CONFLUENCE_ENABLED
        self.base_url = CONFLUENCE_MCP_URL
        
        if not self.enabled:
            logger.warning("Confluence MCP is disabled. Set CONFLUENCE_ENABLED=true to enable.")
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search Confluence for relevant pages via MCP server.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, content, and URL
        """
        if not self.enabled:
            logger.info("Confluence MCP disabled, returning empty results")
            return []
        
        try:
            logger.info(f"Searching Confluence MCP server for: {query}")
            
            # MCP server endpoint for search
            url = f"{self.base_url}/search"
            
            # Prepare request payload
            payload = {
                "query": query,
                "max_results": max_results
            }
            
            # Make request to MCP server
            response = requests.post(
                url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                # Transform MCP response to standard format
                formatted_results = []
                for item in results:
                    formatted_results.append({
                        "title": item.get("title", ""),
                        "content": item.get("content", item.get("excerpt", "")),
                        "url": item.get("url", ""),
                        "space": item.get("space", {}).get("key", "Unknown") if isinstance(item.get("space"), dict) else item.get("space", "Unknown"),
                        "relevance_score": item.get("relevance_score", item.get("score", 0.5))
                    })
                
                logger.info(f"Found {len(formatted_results)} results from Confluence MCP")
                return formatted_results
            else:
                logger.warning(f"Confluence MCP search returned status {response.status_code}: {response.text}")
                return []
            
        except requests.exceptions.Timeout:
            logger.error("Confluence MCP search timed out")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Confluence MCP server at {self.base_url}")
            return []
        except Exception as e:
            logger.error(f"Confluence search failed: {e}", exc_info=True)
            return []
    
    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific Confluence page by ID via MCP server.
        
        Args:
            page_id: Confluence page ID
            
        Returns:
            Page data with title, content, and metadata
        """
        if not self.enabled:
            return None
        
        try:
            logger.info(f"Fetching Confluence page from MCP server: {page_id}")
            
            # MCP server endpoint for getting page
            url = f"{self.base_url}/page/{page_id}"
            
            # Make request to MCP server
            response = requests.get(
                url,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Transform MCP response to standard format
                page = {
                    "id": data.get("id", page_id),
                    "title": data.get("title", ""),
                    "content": data.get("content", data.get("body", "")),
                    "url": data.get("url", ""),
                    "space": data.get("space", {}).get("key", "Unknown") if isinstance(data.get("space"), dict) else data.get("space", "Unknown")
                }
                
                logger.info(f"Successfully fetched page: {page['title']}")
                return page
            else:
                logger.warning(f"Confluence MCP get_page returned status {response.status_code}")
                return None
            
        except requests.exceptions.Timeout:
            logger.error("Confluence MCP get_page timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Confluence MCP server at {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch Confluence page {page_id}: {e}", exc_info=True)
            return None


# Singleton instance
confluence_client = ConfluenceMCPClient()
