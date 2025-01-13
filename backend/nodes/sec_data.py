import os
from typing import Dict, Any
from langchain_core.messages import AIMessage
from sec_api import QueryApi
from datetime import datetime, timedelta
from backend.classes.research_state import ResearchState
import logging

logger = logging.getLogger(__name__)

class SECDataExtractorNode:
    """Node for extracting basic SEC filing data."""
    
    def __init__(self):
        self.api_key = os.getenv("SEC_API_KEY")
        if not self.api_key:
            raise ValueError("SEC_API_KEY environment variable not set")
        self.queryApi = QueryApi(api_key=self.api_key)

    async def run(self, state: ResearchState) -> ResearchState:
        """Extract recent SEC filings data for the company."""
        company = state.company
        
        logger.info(f"Starting SEC data extraction for {company}")
        
        # Calculate date range (last 1 year)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        try:
            # Query SEC filings
            query = {
                "query": {
                    "query_string": {
                        "query": f"companyName:\"{company}\" AND formType:\"10-K\""
                    }
                },
                "from": "0",
                "size": "10",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            logger.info(f"Querying SEC API for {company}")
            response = self.queryApi.get_filings(query)
            logger.info("Successfully received SEC API response")
            
            # Process and store relevant data
            filings = response.get("filings", [])
            
            if not filings:
                logger.warning(f"No 10-K filings found for {company}")
                state.sec_data = {
                    "status": "no_data",
                    "message": f"No recent 10-K filings found for {company}"
                }
            else:
                latest_filing = filings[0]
                logger.info(f"Found {len(filings)} filings, using most recent from {latest_filing.get('filedAt')}")
                state.sec_data = {
                    "status": "success",
                    "latest_10k": {
                        "filing_date": latest_filing.get("filedAt"),
                        "filing_url": latest_filing.get("linkToFilingDetails"),
                        "company_name": latest_filing.get("companyName"),
                        "cik": latest_filing.get("cik")
                    },
                    "total_filings": len(filings)
                }
            
            # Add message about completion
            state.messages.append(
                AIMessage(content=f"Retrieved SEC filing data for {company}")
            )
            
        except Exception as e:
            error_msg = f"Error retrieving SEC data: {str(e)}"
            logger.error(error_msg)
            state.sec_data = {
                "status": "error",
                "message": str(e)
            }
            state.messages.append(
                AIMessage(content=f"⚠️ {error_msg}")
            )
        
        return state 