from typing import Dict, List, Optional
from pydantic import BaseModel
from langchain_core.messages import BaseMessage

class InputState(BaseModel):
    """Input state for the research workflow."""
    company: str

class OutputState(BaseModel):
    """Output state for the research workflow."""
    report_path: Optional[str] = None

class ResearchState(BaseModel):
    """State for the research workflow."""
    company: str
    initial_research: Optional[Dict] = None
    sec_data: Optional[Dict] = None
    report_content: Optional[str] = None
    report_path: Optional[str] = None
    messages: List[BaseMessage] = []
    
    def dict(self, *args, **kwargs) -> Dict:
        """Convert state to dictionary, handling BaseMessage objects."""
        d = super().dict(*args, **kwargs)
        # Convert BaseMessage objects to their content strings
        if "messages" in d:
            d["messages"] = [
                str(m.content) if isinstance(m, BaseMessage) else str(m)
                for m in d["messages"]
            ]
        return d 