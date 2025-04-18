# InterviewGraph: Interview Prep Multi-Agent System

## Summary

Interview preparation process is very intimidating and daunting, particularly for candidates who are aiming for roles in highly competitive companies like big tech (MAANG). This project aims to streamline and personalize the whole process of interview preparation using advanced AI tools, with a focus on deep research, contextual relevance and realistic mock interview simulation.

## Documentation

- Codelabs URL: (https://codelabs-preview.appspot.com/?file_id=1AbMe_4jxEPx0P9NO9eErGrNsStrpEOpLfezefqXEHdc#0)
- GitHub Projects URL: (https://github.com/orgs/DAMG7245-Team-2/projects/1/views/1)

## Deployments

- Backend URL: (https://ig-service-642366140190.us-east4.run.app)
- Frontend URL: (interview-graph.vercel.app)
- Airflow URL: (http://34.41.132.26:8080)

## Architecture

![System Architecture](https://www.mermaidchart.com/raw/2b4265e0-286e-4746-81a9-83a535129890?theme=light&version=v0.1&format=svg)

The system consists of multiple AI agents working together:

- **Interview Agent**: Conducts mock interviews and provides feedback
- **Prep Agent**: Helps with interview preparation and research
- **Backend API**: FastAPI-based service handling agent interactions
- **Frontend**: Streamlit-based user interface
- **MCP**: MCP service to access snowflake DB

## How to Run

### Prerequisites

- Python 3.12
- Poetry (Python package manager)
- Snowflake account credentials

### Installation

1. Clone the repository:

```bash
git clone https://github.com/DAMG7245-Team-2/InterviewGraph.git
cd InterviewGraph
```

2. Set up environment variables:
   Create a `.env` file with your Snowflake credentials:

```env
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
SNOWFLAKE_ROLE=your_role

OPENAI_API_KEY=your_api_key
ELEVEN_LABS_API_KEY=your_api_key
PINECONE_API_KEY=your_api_key
PINECONE_HOST=your_host_url
```

### Running the Application

1. Start the backend API:

```bash
docker build . -t "interview-graph"
docker run -p 8000:8000 --env-file .env "interview-graph"
```

2. Start the frontend:

```bash
cd frontend
npm i
npm run dev
```

## Project Structure

```
InterviewGraph/
├── airflow/                   # Airflow pipelines
├── backend/
│   ├── api.py                 # FastAPI application
│   ├── interview_agent/       # Interview agent implementation
│   │   ├── src/
│   │   │   └── interview_agent/
│   │   │       ├── graph.py   # Interview workflow
│   │   │       └── ...
│   ├── prep_agent/            # Prep agent implementation
│   │   ├── src/
│   │   │   └── prep_agent/
│   │   │       ├── graph.py   # Prep workflow
│   │   │       └── ...
│   └── sql_mcp.py             # MCP server
├── frontend/                  # React frontend
│
├── .github/
│   └── workflows/            # CI/CD configurations
├── pyproject.toml            # Project dependencies
└── README.md                 # This file
```
