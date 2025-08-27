# How to Use GHC Digital Twin Ingestion Workflow

This document explains how to set up automatic document ingestion from your repository to the GHC Digital Twin.

## Quick Setup

1. **Add the workflow file** to your repository at `.github/workflows/ingest-to-twin.yml`:

```yaml
name: Ingest Documents to GHC Digital Twin

on:
  push:
    branches: [ main ]
    paths: 
      - 'docs/**'
      - 'content/**'
      - '**/*.md'
  workflow_dispatch: # Allow manual trigger

jobs:
  ingest-docs:
    name: Ingest Documents
    uses: ZAKIBAYDOUN/GHC-DT/.github/workflows/ghc-global-ingest.yml@main
    with:
      source_globs: 'docs/**/*.md content/**/*.md **/*.md **/*.txt **/*.pdf'
      source_type: 'digital-roots'
      chunk_size: 4000
      batch_size: 10
    secrets:
      TWIN_API_URL: ${{ secrets.TWIN_API_URL }}
      INGEST_TOKEN: ${{ secrets.INGEST_TOKEN }}
```

2. **Add required secrets** in your repository settings (`Settings > Secrets and variables > Actions`):

   - `TWIN_API_URL`: `https://digitalroots-bf3899aefd705f6789c2466e0c9b974d.us.langgraph.app`
   - `INGEST_TOKEN`: Your ingestion authentication token (ask Agent A for this)

3. **Test the workflow**:
   - Push changes to any markdown file
   - Or manually trigger via Actions tab > "Ingest Documents to GHC Digital Twin" > "Run workflow"

## Configuration Options

### File Patterns (`source_globs`)
Customize which files to ingest:
```yaml
# Default - all markdown, text, and PDF files
source_globs: 'docs/**/*.md content/**/*.md **/*.md **/*.txt **/*.pdf'

# Only documentation folder
source_globs: 'docs/**/*.md'

# Specific folders
source_globs: 'documentation/**/*.md api/**/*.md guides/**/*.md'
```

### Source Type (`source_type`)
Tag your documents with a source type:
```yaml
source_type: 'digital-roots'     # Default for digital-roots repo
source_type: 'api-docs'          # For API documentation
source_type: 'user-guides'       # For user guides
```

### Processing Settings
```yaml
chunk_size: 4000    # Maximum characters per chunk
batch_size: 10      # Chunks per API request
```

## Troubleshooting

### 401 Unauthorized Error
- Check that `INGEST_TOKEN` secret is set correctly
- Verify the token matches the one configured in the Digital Twin API

### 404 Not Found Error  
- Verify `TWIN_API_URL` secret is correct
- Check that the Digital Twin API is deployed and running

### CORS Errors (from web interface)
- The Digital Twin's `ALLOWED_ORIGINS` must include `https://zakibaydoun.github.io`
- Ask Agent A to verify CORS configuration

### No Files Found
- Check your `source_globs` pattern
- Ensure files exist in the specified paths
- Files must have content (empty files are skipped)

## Workflow Details

The workflow will:
1. ? Checkout your repository
2. ? Install Python dependencies (`requests`, `pypdf`, `python-frontmatter`)
3. ? Find files matching your glob patterns
4. ? Read and process content (handles markdown frontmatter, PDF extraction)
5. ? Split content into chunks (~4000 characters with overlap)
6. ? Send batches to the Digital Twin API
7. ? Report success/failure with detailed logs

## Manual Testing

Test individual components:

```bash
# Test API health
curl https://digitalroots-bf3899aefd705f6789c2466e0c9b974d.us.langgraph.app/health

# Test query (no auth needed)
curl -X POST https://digitalroots-bf3899aefd705f6789c2466e0c9b974d.us.langgraph.app/api/twin/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this project about?"}'

# Test ingestion (auth required)
curl -X POST https://digitalroots-bf3899aefd705f6789c2466e0c9b974d.us.langgraph.app/api/twin/ingest_texts \
  -H "Content-Type: application/json" \
  -H "X-INGEST-TOKEN: your-token-here" \
  -d '{"texts": ["Test document content"]}'
```

## Example Use Cases

### Documentation Updates
Every time you update documentation, it gets automatically ingested:
```yaml
on:
  push:
    branches: [ main ]
    paths: [ 'docs/**' ]
```

### Release Documentation
Ingest documentation only on releases:
```yaml
on:
  release:
    types: [published]
```

### Manual Control
Only run when manually triggered:
```yaml
on:
  workflow_dispatch:
    inputs:
      force_update:
        description: 'Force update all documents'
        type: boolean
        default: false
```

## Support

If you encounter issues:
1. Check the workflow logs in the Actions tab
2. Verify all secrets are correctly set
3. Test API endpoints manually
4. Contact Agent A for Digital Twin configuration issues
5. Contact Agent B for workflow issues