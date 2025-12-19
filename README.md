# search-to-sheets
Automates company research using LLM based summarization with Google Sheets integration

The application gathers company information from multiple sources, summarizes it using an LLM, and writes the results directly to a Google Spreadsheet.


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


### Input/Output Format Spreadsheet

**Input Sheet:**
```
| Company Name |
|-------------|
| Apple Inc   |
| Tesla       |
```

**Output Sheet:**
```
| Company   | Summary                                    |
|-----------|-------------------------------------------|  
| Apple Inc | **Company Overview**: Apple Inc is a...   |
| Tesla     | **Company Overview**: Tesla Inc is...     |
```


## Running with Debugging and Troubleshoot
### run with langgraph server and langsmith
#### Prerequisites
description what it means ()
- docker and docker compose installed


```bash
# Clone the repository
git clone <repository-url>
cd search-to-sheets

```
image of langgraph studio, show the trace is tracked and can be re run, and visualization graph


## Design Documentation
Detailed design rationale, workflow structure, and development-time observability notes are documented in:

👉 [DESIGN.md](./docs/DESIGN.md)

