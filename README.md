# search-to-sheets
Automates company research using LLM based summarization with Google Sheets integration

The application gathers company information from multiple sources, summarizes it using an LLM, and writes the results directly to a Google Spreadsheet.

## Features

![Langgraph Node](assets/main-graph.png)
- Multi-source company data collection
- LLM-based summarization
- Direct Google Sheets read/write integration
- CLI-based execution
- Optional observability with LangSmith and LangGraph

## Installation

### Prerequisites
- Python ≥ 3.12
- Google Sheets API credentials  
- OpenAI API key
- Tavily API key
- Serper API key
- [`uv`](https://github.com/astral-sh/uv) Python package manager

**Optional**
- LangSmith API key (for tracing and debugging)


### Setup

```bash
# Clone the repository
git clone <repository-url>
cd search-to-sheets

# (Optional) Ensure you are on the main branch
git checkout main

# Configure environment variables
cp .env.sample .env
# Edit .env and add your API keys

# Install dependencies and the project
uv sync
```


## Running the Application
```bash
# run the app using the CLI entry point
uv run searchapp

# Example

# Show help
uv run searchapp --help
# Run with a Google Spreadsheet ID
uv run searchapp <spreadsheet_id>
```

#### for direct python usage
```bash
# Show help
uv run src/main.py --help
# Run with a Google Spreadsheet ID
uv run src/main.py <spreadsheet_id>
```


### Google Spreadsheet Format

**Input Sheet:**
The application expects a sheet containing a single column named Company Name.
```
| Company Name|
|-------------|
| Traveloka   |
| Gojek       |
```

**Output Sheet:**
The tool writes summarized company information into a separate output sheet.
```
| Company   | Summary                                 |
|-----------|-----------------------------------------|  
| Traveloka | **Company Overview**: Traveloka is ...  |
| Gojek     | **Company Overview**: Gojek is ...      |
```


## Debugging and Observability
### Running with LangGraph Server and LangSmith
#### Prerequisites
This mode enables execution tracing, graph visualization, and replayable runs using local LangSmith Studio.

Prerequisites
- Docker
- Docker Compose
- LangSmith and LangChain environment variables configured in .env

```bash
# Clone the repository
git clone <repository-url>
cd search-to-sheets

# Configure environment variables
cp .env.sample .env
# Ensure LangSmith and LangChain keys are set

# Build and start services
docker compose up --build
```

Once running, open LangSmith Studio in your browser:
```
https://smith.langchain.com/studio/?baseUrl=http://0.0.0.0:1024

```
All application traces will be captured and can be:
- Inspected step-by-step
- Re-run for debugging
- Visualized as execution graphs

![LangGraph Studio – Execution Traces](assets/langgraph-vis1.png)


## Design Documentation
Detailed design rationale, workflow structure, and observability considerations are documented in:

👉 [DESIGN.md](./docs/DESIGN.md)

