# Company Research Assistant (Simple Version)

A simplified version of a company research assistant that uses LangGraph to orchestrate a workflow of AI agents to gather and analyze company information.

## Features

- Initial company research using web search
- SEC filings data extraction
- Automated report generation
- PDF report publishing

## Architecture

The project uses a simple linear workflow with four main agents:

1. **Initial Research Agent**: Gathers basic company information using web search
2. **SEC Data Agent**: Extracts relevant information from SEC filings
3. **Report Generation Agent**: Creates a comprehensive research report
4. **Publishing Agent**: Converts the report to a well-formatted PDF

## Requirements

- Python 3.9+
- OpenAI API Key
- SEC API Key

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_key
   SEC_API_KEY=your_sec_api_key
   ```

## Usage

1. Start the server:
   ```bash
   python app.py
   ```
2. Open your browser to `http://localhost:5000`
3. Enter a company name and optionally a company URL
4. Wait for the research process to complete
5. Download the generated PDF report

## Project Structure

```
company-research-simple/
├── backend/
│   ├── nodes/
│   │   ├── initial_grounding.py
│   │   ├── sec_data.py
│   │   ├── generate_report.py
│   │   └── publish.py
│   ├── classes/
│   │   └── research_state.py
│   └── graph.py
├── frontend/
│   ├── templates/
│   └── static/
├── reports/
├── app.py
├── requirements.txt
└── README.md
```

## How It Works

1. The workflow starts with basic web research about the company
2. Then it fetches recent SEC filings data
3. Combines all information to generate a comprehensive report
4. Converts the report to a professionally formatted PDF

## Contributing

Feel free to submit issues and enhancement requests! 