# GHC Digital Twin - LangGraph Cloud Deployment

This is the Digital Twin application for Green Hill Canarias (GHC) deployed on LangGraph Cloud.

## ?? Live Site

Visit the Digital Twin interface at: [https://zakibaydoun.github.io/GHC-DT](https://zakibaydoun.github.io/GHC-DT)

## ?? API Endpoints

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

## ?? GitHub Action Workflow

This repository provides a reusable GitHub Action workflow that any repository can use to ingest documents into the Digital Twin.

### Using the Workflow

Add this to your repository's `.github/workflows/ingest-to-twin.yml`:

```yaml
name: Ingest Documents to GHC Digital Twin

on:
  push:
    branches: [ main ]
    paths: 
      - 'docs/**'
      - 'content/**'
      - '**/*.md'

jobs:
  ingest:
    uses: ZAKIBAYDOUN/GHC-DT/.github/workflows/ghc-global-ingest.yml@main
    with:
      source_globs: 'docs/**/*.md content/**/*.md **/*.md **/*.txt **/*.pdf'
      source_type: 'public'
      chunk_size: 4000
      batch_size: 10
    secrets:
      TWIN_API_URL: ${{ secrets.TWIN_API_URL }}
      INGEST_TOKEN: ${{ secrets.INGEST_TOKEN }}
```

### Required Secrets

Set these secrets in your repository settings:

- `TWIN_API_URL`: The base URL of your Digital Twin API (e.g., `https://digitalroots-bf3899aefd705f6789c2466e0c9b974d.us.langgraph.app`)
- `INGEST_TOKEN`: Authentication token for document ingestion (optional, matches server's `INGEST_AUTH_TOKEN`)

### Workflow Inputs

- `source_globs`: File patterns to ingest (default: `docs/**/*.md content/**/*.md **/*.md **/*.txt **/*.pdf`)
- `source_type`: Type of source documents (default: `public`)
- `chunk_size`: Maximum size of text chunks in characters (default: 4000)
- `batch_size`: Number of chunks per API request (default: 10)

## ?? Web Interface

The repository includes a complete web interface at `index.html` with:

- **Query Interface**: Ask questions directly to the Digital Twin
- **Health Monitor**: Real-time API health checking
- **Example Questions**: Pre-built queries to get started
- **Responsive Design**: Works on desktop and mobile devices

### JavaScript API

Use the JavaScript API in your own sites:

```html
<script src="https://zakibaydoun.github.io/GHC-DT/assets/ask.js"></script>
<script>
// Simple query
askDigitalTwin("What is Green Hill Canarias?", "answer-div");

// Advanced usage
window.twinAPI.query("Your question").then(result => {
    console.log(result.answer);
});

// Health check
checkTwinHealth().then(isHealthy => {
    console.log("API is", isHealthy ? "healthy" : "down");
});
</script>
```

## ?? Environment Variables

The following environment variables need to be set in LangSmith:

- `OPENAI_API_KEY`: Your OpenAI API key
- `VECTOR_STORE_DIR`: Directory for vector store (default: "vector_store")
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins (must include `https://zakibaydoun.github.io`)
- `INGEST_AUTH_TOKEN`: Token required for document ingestion

## ?? Testing the Deployment

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

## ??? Architecture

- **LangGraph**: Manages the conversation flow and state
- **ChromaDB**: Vector database for document storage and retrieval  
- **OpenAI GPT-4**: Language model for generating responses
- **FastAPI**: Web framework for REST API endpoints
- **GitHub Actions**: Automated document ingestion workflow
- **GitHub Pages**: Static site hosting for the web interface

## ?? Deployment

1. **LangGraph Cloud**: The main API is deployed automatically from the `digital-roots` repository
2. **GitHub Pages**: The web interface is deployed from this repository to `https://zakibaydoun.github.io/GHC-DT`
3. **Workflow**: The reusable GitHub Action can be called by any repository

## ?? Security

- All API calls use HTTPS
- Document ingestion requires authentication via `X-INGEST-TOKEN` header
- CORS is configured to allow only specified origins
- No secrets are stored in code - all configuration via environment variables