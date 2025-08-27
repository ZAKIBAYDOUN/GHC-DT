# GHC Digital Twin - LangGraph Cloud Deployment

This is the Digital Twin application for Green Hill Canarias (GHC) deployed on LangGraph Cloud.

## API Endpoints

### Health Check
- **GET** `/health`
- Returns the health status of the API

### Query Digital Twin
- **POST** `/api/twin/query`
- **Body**: `{"question": "Your question here"}`
- Returns an AI-generated answer based on the available knowledge

### Ingest Documents
- **POST** `/api/twin/ingest_texts`
- **Headers**: `X-INGEST-TOKEN: <your-token>`
- **Body**: `{"texts": ["document text 1", "document text 2"]}`
- Ingests documents into the vector store for future queries

## Environment Variables

The following environment variables need to be set in LangSmith:

- `OPENAI_API_KEY`: Your OpenAI API key
- `VECTOR_STORE_DIR`: Directory for vector store (default: "vector_store")
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins
- `INGEST_AUTH_TOKEN`: Token required for document ingestion

## Testing the Deployment

Once deployed, you can test the endpoints:

```bash
# Health check
curl https://[deployment-url]/health

# Query the digital twin
curl -X POST https://[deployment-url]/api/twin/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Green Hill Canarias?"}'

# Ingest documents (requires auth token)
curl -X POST https://[deployment-url]/api/twin/ingest_texts \
  -H "Content-Type: application/json" \
  -H "X-INGEST-TOKEN: your-token-here" \
  -d '{"texts": ["Green Hill Canarias is a sustainable development project..."]}'
```

## Architecture

- **LangGraph**: Manages the conversation flow and state
- **ChromaDB**: Vector database for document storage and retrieval
- **OpenAI GPT-4**: Language model for generating responses
- **FastAPI**: Web framework for REST API endpoints