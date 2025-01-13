from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from backend.graph import Graph
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add Pydantic model for company research request
class CompanyRequest(BaseModel):
    company_name: str
    company_url: str = None
    output_format: str = "pdf"

app = FastAPI()

# Ensure reports directory exists
if not os.path.exists("reports"):
    os.makedirs("reports")
    logger.info("Created reports directory")

# Mount static directories
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/reports", StaticFiles(directory="reports"), name="reports")
logger.info("Static directories mounted")

templates = Jinja2Templates(directory="frontend/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    try:
        # Receive initial data from the WebSocket client
        data = await websocket.receive_json()
        company_name = data.get("companyName")
        company_url = data.get("companyUrl")
        output_format = data.get("outputFormat", "pdf")
        logger.info(f"Received research request for company: {company_name}")
        
        # Initialize the Graph with company info
        graph = Graph(
            company=company_name,
            url=company_url,
            output_format=output_format,
            websocket=websocket
        )
        
        # Progress callback to send messages back to the client
        async def progress_callback(message):
            await websocket.send_text(message)
            logger.info(f"Progress update: {message}")

        # Run the graph process
        logger.info("Starting graph execution")
        result = await graph.run(progress_callback=progress_callback)
        logger.info("Graph execution completed")

        await websocket.send_text("Disconnected to research service")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        error_msg = f"Error in websocket: {str(e)}"
        logger.error(error_msg)
        await websocket.send_text(f"❌ Error: {str(e)}")
    finally:
        await websocket.close()
        logger.info("WebSocket connection closed")

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=5000,
        reload=True
    ) 