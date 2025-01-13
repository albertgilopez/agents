from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

# Import research state class
from backend.classes.research_state import ResearchState, InputState, OutputState

# Import node classes
from backend.nodes.initial_grounding import InitialGroundingNode
from backend.nodes.sec_data import SECDataExtractorNode
from backend.nodes.generate_report import GenerateNode
from backend.nodes.publish import PublishNode

class Graph:
    def __init__(self, company=None, url=None, output_format="pdf", websocket=None):
        # Initial setup of ResearchState and messages
        self.messages = [
            SystemMessage(content="You are an expert researcher ready to begin the information gathering process.")
        ]

        # Initialize ResearchState
        self.state = ResearchState(
            company=company,
            company_url=url,
            output_format=output_format,
            messages=self.messages
        )
        
        # Initialize nodes
        self.initial_search_node = InitialGroundingNode()
        self.sec_data_node = SECDataExtractorNode()
        self.generate_node = GenerateNode()
        self.publish_node = PublishNode()

        # Initialize workflow for the graph
        self.workflow = StateGraph(ResearchState, input=InputState, output=OutputState)

        # Add nodes to the workflow
        self.workflow.add_node("initial_grounding", self.initial_search_node.run)
        self.workflow.add_node("extract_sec_data", self.sec_data_node.run)
        self.workflow.add_node("generate_report", self.curried_node(self.generate_node.run))
        self.workflow.add_node("publish", self.publish_node.run)

        # Add edges to create a linear workflow
        self.workflow.add_edge("initial_grounding", "extract_sec_data")
        self.workflow.add_edge("extract_sec_data", "generate_report")
        self.workflow.add_edge("generate_report", "publish")

        # Set start and end nodes
        self.workflow.set_entry_point("initial_grounding")
        self.workflow.set_finish_point("publish")

        self.memory = MemorySaver()
        self.websocket = websocket

    async def run(self, progress_callback=None):
        """Run the research workflow."""
        try:
            # Compile the graph
            graph = self.workflow.compile(checkpointer=self.memory)
            thread = {"configurable": {"thread_id": "2"}}
            
            final_state = None
            # Execute the graph asynchronously and send progress updates
            async for s in graph.astream(self.state, thread, stream_mode="values"):
                if "messages" in s and s["messages"]:
                    message = s["messages"][-1]
                    output_message = message.content if hasattr(message, "content") else str(message)
                    if progress_callback:
                        await progress_callback(output_message)
                final_state = s
                
            return final_state
            
        except Exception as e:
            print(f"Error running workflow: {str(e)}")
            if progress_callback:
                await progress_callback(f"❌ Error: {str(e)}")
            return None

    def curried_node(self, node_run_method):
        # Curried wrapper for handling websocket
        async def wrapper(state):
            return await node_run_method(state, self.websocket)
        return wrapper 