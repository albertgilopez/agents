from typing import Dict, Any, Optional
from langchain_core.messages import AIMessage
import os
from datetime import datetime
import logging
from backend.classes.research_state import ResearchState
import json
from fastapi import WebSocket

# Configure logging
logger = logging.getLogger(__name__)

class PublishNode:
    """Node for publishing the research report."""
    
    def __init__(self):
        # Ensure reports directory exists
        self.reports_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def _create_json_metadata(self, state: ResearchState) -> str:
        """Create JSON metadata for the report."""
        metadata = {
            "company": state.company,
            "generation_date": datetime.now().isoformat(),
            "research_sources": {
                "web_sources": len(state.initial_research.get("search_results", [])),
                "search_response_time": state.initial_research.get("response_time", 0),
                "search_query": state.initial_research.get("query", ""),
            },
            "sec_data": {
                "latest_filing_date": state.sec_data.get("latest_10k", {}).get("filing_date", "N/A"),
                "total_filings": state.sec_data.get("total_filings", 0),
                "cik": state.sec_data.get("latest_10k", {}).get("cik", "N/A")
            }
        }
        return json.dumps(metadata, indent=2)
    
    async def run(self, state: ResearchState, websocket: Optional[WebSocket] = None) -> ResearchState:
        """Save the report as Markdown and JSON metadata."""
        company = state.company
        report_content = state.report_content
        
        if not report_content:
            logger.warning("No report content found to publish")
            state.messages.append(
                AIMessage(content="⚠️ No report content found to publish")
            )
            return state
        
        try:
            logger.info(f"Starting report generation for {company}")
            
            # Generate filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{company.lower().replace(' ', '_')}_{timestamp}"
            md_filename = f"{base_name}.md"
            json_filename = f"{base_name}_metadata.json"
            
            # Full paths for file system operations
            md_path = os.path.join(self.reports_dir, md_filename)
            json_path = os.path.join(self.reports_dir, json_filename)
            
            # Web-accessible paths
            md_web_path = f"/reports/{md_filename}"
            json_web_path = f"/reports/{json_filename}"
            
            # Save markdown content
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # Save JSON metadata
            metadata = self._create_json_metadata(state)
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(metadata)
            
            logger.info(f"Successfully generated report files: {md_path}, {json_path}")
            
            # Save the report path (use web path)
            state.report_path = md_web_path
            
            # Send a message with the report links
            if websocket:
                await websocket.send_text(f"""```markdown
# Research Report Generated

Your report has been generated and saved.
```""")
            
            # Add message about completion with download links and preview
            state.messages.append(
                AIMessage(content=f"""
### Report Generated Successfully

📥 **Downloads**
- [Markdown Report]({md_web_path})
- [Report Metadata]({json_web_path})

#### Report Preview
```markdown
{report_content[:1000]}...
```

*Full report available in the downloaded files*
""")
            )
            
        except Exception as e:
            error_msg = f"Error generating report: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state.messages.append(
                AIMessage(content=f"⚠️ Error publishing report: {str(e)}")
            )
            # Ensure report paths are None on error
            state.report_path = None
        
        return state 