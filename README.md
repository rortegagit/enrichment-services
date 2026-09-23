# Enrichment Services

This repository provides a **Research Object (RO) analysis and recommendation API**, built with Flask, Gunicorn, Celery, and Redis, packaged in Docker for easy deployment.

---

## Features

- **/ro_analysis** – Accepts a POST request with a Research Object URI, callback URL, and nonce. Processes asynchronously via Celery and posts results to the callback.  
- **/ro_recommendation** – Provides recommendations based on ROs and authors.  
- **/ro_recommendation_dev** – Development endpoint for testing.  
- **/ro_claim_extraction** – Provides a list of extracted claims from the title and description of an RO.
- **/ro_claim_extraction_dev** – Development endpoint for testing.
- **/ro_claim_analysis** – Provides a list of extracted claims from the title and description of an RO, and assess them with literature articles.
- **/ro_claim_analysis_dev** – Development endpoint for testing.
- **Asynchronous processing** – Celery + Redis ensures tasks run in the background and can be retried on failure.  
- **Dockerized** – Easy to run locally or deploy in production with environment variable configuration.

---

## Table of Contents

- [How the Enrichment Service Works](#how-the-enrichment-service-works)
- [Requirements](#requirements)
- [Environment Variables](#environment-variables)
- [Docker Setup](#docker-setup)
- [Running the Services](#running-the-services)
- [API Endpoints](#api-endpoints)
- [Development Notes](#development-notes)
- [Authors and Acknowledgements](#authors-and-acknowledgements)

---
## How the Enrichment Service Works

The enrichment service processes a Research Object (RO) and produces a consolidated enrichment report. The workflow is as follows:

1. Input RO

The service receives a RO in JSON format that contains multiple resources. Supported resource formats include: .docx, .pptx, .pdf, .txt, .md, .ipynb. The service also processes the title and the description of the RO as a txt file, which will be called as {ro_id}_titledesc.txt.

2. Download Resources

Each valid resource in the RO is downloaded locally for processing.

3. Document Annotation

Each resource is sent to the DOCUMENT_ANNOTATION_ENDPOINT. This endpoint returns an enrichment report for the individual resource, extracting key entities, concepts, topics, and other metadata.

4. Aggregation

The enrichment reports from all resources are wisely aggregated to produce a single, consolidated enrichment result for the entire RO.

5. Callback

The final aggregated enrichment report is sent via a POST request to the callback URL provided in the request, along with the nonce, the ro_uri and a summary of the analyzed resources.

---

## Requirements

- Docker >= 23.0  
- Docker Compose >= 2.0  
- Python 3.11+ (only for local development)

---

## Environment Variables

All sensitive values and configuration are managed via environment variables, either in a `.env` file (ignored in Git) or passed at runtime.

Example `.env`:
```
PORT=8080
DOC_ENRICHMENT_ENDPOINT=https://fair2adapt.expertcustomers.ai/services/enrich
CLAIM_EXTRACTION_ENDPOINT=https://fair2adapt.expertcustomers.ai/services/claim_extraction
CLAIM_ANALYSIS_ENDPOINT=https://fair2adapt.expertcustomers.ai/services/claim_analysis
VERIFICATION_INDEX_NAME=fc60kcorpus
API_USER=user
API_PASSWORD=pwd
API_PASSWORD_DEV=pwddev
```
Where API_USER is the username for the enrichment service in RoHub and the API_PASSWORD and API_PASSWORD_DEV are the passwords for the prod and dev environments.

---

## Docker Setup

**Dockerfile** uses `Gunicorn` to serve the Flask app.  
**Celery** is run as a separate service using the same image.  
**Redis** acts as the Celery broker.

### docker-compose.yml
```
services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"

  web:
    build: .
    env_file:
      - .env
    ports:
      - "${PORT}:${PORT}"
    depends_on:
      - redis

  celery:
    build: .
    env_file:
      - .env
    command: celery -A ro_aggregator.tasks worker --loglevel=info
    depends_on:
      - redis
```

---

## Running the Services

1. Create an .env file and fill in credentials, endpoints and ports.

2. Build and start the services:

```
docker-compose up --build
```

- Flask/Gunicorn web service will run on http://localhost:${PORT}
- Celery worker will process background tasks
- Redis runs on localhost:6379

3. Stop services:

```
docker-compose down
```

---

## API Endpoints

1. /ro_analysis (POST)

Accepts JSON:

```
{
  "ro_uri": "https://w3id.org/ro-id/123",
  "callback": "http://example.com/callback",
  "nonce": "unique-task-id"
}
```


Response:

```
{
  "status": "queued",
  "ro_uri": "https://w3id.org/ro-id/123",
  "callback": "http://example.com/callback",
  "nonce": "unique-task-id"
}
```

The task is processed asynchronously via Celery. The output is sent via POST call to callback

Callback call:

```
{
  "results": {
    "entity_datacubes": [
      {
        "entity": "string",                // datacube_id
      }
    ],
    "entity_locations": [
      {
        "entity": "string",                // name of location
        "geonames": "string (URL)",        // optional URL
        "wikidata": "string (URL)"         // optional URL
      }
    ],
    "entity_organizations": [
      {
        "entity": "string",                // organization name
        "wikidata": "string (URL)"         // optional
      }
    ],
    "entity_people": [
      {
        "entity": "string"                 // person name
      }
    ],
    "entity_timerefs": [
      {
        "entity": "string"                 // time reference, e.g., "in 2021"
      }
    ],
    "ke_concepts": [
      {
        "key_element": "string",           // concept name
        "score": "float",                  // raw score
        "normScore": "float"               // normalized score
      }
    ],
    "ke_lemmas": [
      {
        "key_element": "string",           // lemma
        "score": "float",
        "normScore": "float"
      }
    ],
    "ke_phrases": [
      {
        "key_element": "string",           // phrase
        "score": "float",
        "normScore": "float"
      }
    ],
    "ke_sentences": [
      {
        "key_element": "string",           // sentence text
        "score": "float",
        "normScore": "float"
      }
    ],
    "topic_domains": [
      {
        "topic": "string",                 // domain/topic name
        "score": "float",
        "normScore": "float"
      }
    ],
    "topic_fors": [
      {
        "topic": "string",                 // fields of research category
        "subtopics": ["strings"],          // fields of research subcategory
      }
    ],
    "topic_iptcs": [
      {
        "path": "string",                  // hierarchical path
        "topic": "string"                  // topic name
      }
    ],
    "topic_nasa": [
      {
        "topic": "string",                 // NASA NTRS category
        "subtopics": ["strings"],          // NASA NTRS subcategory
      }
    ],
    "tags_fcid": [
      {
        "tag": "string",                   // Metadata tag from FC_ID taxonomy
        "values": ["strings"],             // Metadata values from FC_ID taxonomy
      }
    ],  
    "processed_resources": [
    {
      "filename": "string",                 // name of processed file
      "status_code": "integer"              // processing status
    }
  ],
  "ro_uri": "string (URL)",                 // URI of the Research Object
  "nonce": "string"                         // unique task identifier
  "processed_resources": [ // Summary of the processed resources
    {"filename": "example_titledesc.txt", "status_code": 200}
  ],
}
```

2. /ro_recommendation (POST)

Accepts JSON:

```
{
  "ros": ["https://w3id.org/ro-id/123"],
  "scientists": ["username123", "username124"]
}
```

Output:
```
[
    "https://w3id.org/ro-id/42", 
    (...)
]
```


Returns recommendations based on concepts and places extracted from ROs.

3. /ro_recommendation_dev (POST)

Same as /ro_recommendation, but uses the development ROHub endpoint.

4. /ro_claim_extraction (POST)

Accepts JSON:

```
{
  "ro_uri": ["https://w3id.org/ro-id/123"],
}
```

Output:
```
[
    "Claim", 
    (...)
]
```


Returns a list of claims extracted from the title and description of the RO.

5. /ro_claim_extraction_dev (POST)

Same as /ro_claim_extraction, but uses the development ROHub endpoint.

6. /ro_claim_analysis (POST)

Accepts JSON:

```
{
  "ro_uri": ["https://w3id.org/ro-id/123"],
}
```

Output:
```
[
    {
        "claim": "string",
        "claim_analysis": [
            {
                "abstract": "string",
                "doc_id": "int",                //internal id
                "original_id": "string",        //doi
                "rank": "int",                  //rank in the retrieval system
                "report": {
                    "evidence": ["strings"],    //most relevant sentences from evidence
                    "rationale": "string",      //solution explanation
                    "response": "SUPPORT|REFUTE"
                },
                "score": "float",               //score given by the system
                "title": "string"
            }
        ]
        "claim_type": "string",
        "id": "int",
        "llms_used": ["strings"]
    }
]
```


Returns a list of claims extracted from the title and description of the RO, and assess them using a database of literature articles.

7. /ro_claim_analysis_dev (POST)

Same as /ro_claim_analysis, but uses the development ROHub endpoint.

---

## Development Notes

- Environment variables are accessible via os.environ.get("VAR_NAME").
- For Celery retries, the task uses max_retries and default_retry_delay.
- Logs are written to stdout/stderr (--access-logfile - --error-logfile -) for containerized logging.

---

## Authors and Acknowledgements

This repository is developed and maintained by Raúl Ortega (rortega@expert.ai) as part of the FAIR2Adapt project (Grant number: 101188256).
