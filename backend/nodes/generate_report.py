from typing import Dict, Any, Optional
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os
from datetime import datetime
from backend.classes.research_state import ResearchState
import logging
import json

logger = logging.getLogger(__name__)

class GenerateNode:
    """Node for generating the research report."""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
            
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0
        )

    def _format_sec_data(self, sec_data: Dict) -> str:
        """Format SEC data for better prompt context."""
        if not sec_data or sec_data.get("status") != "success":
            return "No SEC data available"
            
        latest_10k = sec_data.get("latest_10k", {})
        total_filings = sec_data.get("total_filings", 0)
        
        formatted_data = f"""
Latest 10-K Filing Information:
- Filing Date: {latest_10k.get('filing_date', 'N/A')}
- Company CIK: {latest_10k.get('cik', 'N/A')}
- Filing URL: {latest_10k.get('filing_url', 'N/A')}
- Total Available Filings: {total_filings}
"""
        return formatted_data

    def _format_tavily_data(self, initial_research: Dict) -> str:
        """Format Tavily search results for better prompt context."""
        if not initial_research or not initial_research.get("search_results"):
            return "No initial research data available"
            
        results = initial_research.get("search_results", [])
        ai_summary = initial_research.get("ai_summary", "")
        
        formatted_data = f"""
AI Generated Summary:
{ai_summary}

Key Sources and Information:
"""
        for i, result in enumerate(results, 1):
            formatted_data += f"""
Source {i}:
- Title: {result.get('title', 'No title')}
- URL: {result.get('url', 'No link')}
- Relevance Score: {result.get('score', 'N/A'):.2%}
- Content: {result.get('content', '')[:500]}
"""
        return formatted_data

    def _format_report_content(self, company: str, content: str, initial_research: Dict, sec_data: Dict) -> str:
        """Format the report content with proper markdown and metadata."""
        # Remove any existing title as we'll add it with proper formatting
        lines = content.split('\n')
        while lines and (lines[0].startswith('# ') or not lines[0].strip()):
            lines.pop(0)
            
        formatted_content = '\n'.join(lines)
        
        # Add metadata section
        metadata = f"""# {company} Research Report

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Research Metadata
- **Data Sources**: {len(initial_research.get('search_results', []))} web sources analyzed
- **Search Response Time**: {initial_research.get('response_time', 0):.2f} seconds
- **Latest SEC Filing**: {sec_data.get('latest_10k', {}).get('filing_date', 'N/A')}
- **Total SEC Filings Available**: {sec_data.get('total_filings', 0)}

---

"""
        return metadata + formatted_content

    async def run(self, state: ResearchState, websocket: Optional[Any] = None) -> ResearchState:
        """Generate a comprehensive research report."""
        company = state.company
        initial_research = state.initial_research or {}
        sec_data = state.sec_data or {}
        
        logger.info(f"Starting report generation for {company}")
        
        # Format data sources
        formatted_sec_data = self._format_sec_data(sec_data)
        formatted_tavily_data = self._format_tavily_data(initial_research)
        
        # Create report prompt
        prompt = f"""You are a professional financial analyst. Create a comprehensive but concise research report for {company}.
        
        Available Research Data:
        1. Web Research and Analysis:
        {formatted_tavily_data}
        
        2. SEC Filing Information:
        {formatted_sec_data}
        
        Create a detailed report with the following sections. DO NOT include a title or date - these will be added automatically.
        Start directly with the Executive Summary section:
        
        ## Executive Summary
        [Provide a concise 2-3 sentence overview focusing on the latest financial performance and key business model aspects]
        
        ## Company Overview
        - Company Background
        - Industry Position
        - Market Presence
        
        ## Business Model
        - Core Products/Services
        - Revenue Streams [Include specific revenue numbers from the research]
        - Target Markets
        - Competitive Advantages
        
        ## Financial Overview
        - Latest Filing Status
        - Key Financial Metrics [Include specific numbers from research]
        - Financial Trends
        - SEC Compliance Status
        
        ## Market Analysis
        - Industry Trends
        - Competitive Landscape
        - Market Share
        - Growth Opportunities
        
        ## Risk Assessment
        - Business Risks
        - Market Risks
        - Regulatory Risks
        - Competitive Risks
        
        ## Investment Considerations
        - Strengths
        - Challenges
        - Growth Potential
        - Key Metrics to Watch
        
        ## Conclusion
        [Provide a balanced summary focusing on financial performance and future outlook]
        
        Guidelines:
        1. Use bullet points for better readability
        2. Include SPECIFIC numbers and data points from the research
        3. Maintain a professional and objective tone
        4. Focus on factual information with recent dates
        5. Highlight both opportunities and risks
        6. Use clean markdown formatting
        7. Use proper spacing between sections
        8. Format lists consistently with hyphens (-)
        """
        
        try:
            logger.info("Sending request to OpenAI")
            # Generate report
            response = await self.llm.ainvoke(
                [
                    SystemMessage(content="""You are a professional financial analyst with expertise in SEC filings and market analysis.
                    Format your response in clean Markdown with proper section hierarchy.
                    Be specific and data-driven in your analysis.
                    Include actual numbers and dates from the provided research.
                    Maintain a balanced and objective perspective.
                    Use consistent formatting and spacing throughout the document.
                    DO NOT include a title or date - these will be added separately."""),
                    AIMessage(content=prompt)
                ]
            )
            
            # Format the report content with metadata
            report_content = self._format_report_content(company, response.content, initial_research, sec_data)
            logger.info("Successfully formatted report content")
            
            # Store report content
            state.report_content = report_content
            
            # Add message about completion
            state.messages.append(
                AIMessage(content=f"Generated research report for {company}")
            )
            
        except Exception as e:
            error_msg = f"Error generating report: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state.messages.append(
                AIMessage(content=f"⚠️ {error_msg}")
            )
            # Set error state
            state.report_content = None
        
        return state 