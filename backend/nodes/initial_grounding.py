from typing import Dict, Any
from langchain_core.messages import AIMessage
from backend.classes.research_state import ResearchState
from tavily import AsyncTavilyClient
import logging
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class InitialGroundingNode:
    """Node for initial company research using web search."""
    
    def __init__(self):
        logger.info("Initializing InitialGroundingNode")
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
        self.tavily_client = AsyncTavilyClient(api_key=tavily_api_key)
        logger.info("Tavily client initialized")

    async def run(self, state: ResearchState) -> ResearchState:
        """Execute initial research using Tavily."""
        company = state.company
        
        try:
            logger.info(f"Starting initial research for {company}")
            
            # Create search query
            query = f"{company} company overview business model revenue"
            
            # Execute search with Tavily
            search_results = await self.tavily_client.search(
                query=query,
                search_depth="advanced",
                include_answer=True,
                include_raw_content=True,
                max_results=5
            )
            
            # Format results message
            ai_summary = search_results.get("answer", "")
            results = search_results.get("results", [])
            response_time = search_results.get("response_time", 0)
            
            # Store complete results in state
            state.initial_research = {
                "search_results": results,
                "ai_summary": ai_summary,
                "response_time": response_time,
                "query": query
            }
            
            # Format message for frontend
            message = f"""### Initial Research Results for {company}

**AI Summary**: {ai_summary}

**Sources Consulted** (Response Time: {response_time:.2f}s):

"""
            # Add formatted sources
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                url = result.get("url", "#")
                content = result.get("content", "").strip()[:300] + "..."
                score = result.get("score", 0)
                
                message += f"""<details>
<summary>Source {i}: {title} (Relevance: {score:.0%})</summary>

- **URL**: [{url}]({url})
- **Content Preview**: 
  {content}
</details>

"""
            
            state.messages.append(
                AIMessage(content=message)
            )
            
            logger.info("Successfully completed initial research")
            
        except Exception as e:
            error_msg = f"Error during initial research: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state.messages.append(
                AIMessage(content=f"⚠️ {error_msg}")
            )
            # Set error state
            state.initial_research = {
                "status": "error",
                "error": str(e),
                "search_results": []
            }
        
        return state 