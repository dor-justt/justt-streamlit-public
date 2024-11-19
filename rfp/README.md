# RFP Processing Application

## Table of Contents
- [Getting Started](#getting-started)
  - [Running the Streamlit App](#running-the-streamlit-app)
  - [Running the Local Server](#running-the-local-server)
- [Docker Setup](#docker-setup)
  - [Building the Image](#building-the-image)
  - [Running the Container](#running-the-container)
- [Model Training](#model-training)

## Getting Started

### Running the Streamlit App
To launch the interactive web interface:
```bash
PYTHONPATH=$PYTHONPATH:. streamlit run rfp/rfp_app.py
```

### Running the Local Server
To start the server on your local machine:
```bash
python rfp_http_server.py
```

## Docker Setup

### Building the Image
Create a Docker image named `rfp-server` from the current directory:
```bash
docker build -t rfp-server .
```

### Running the Container
Launch the Docker container with required environment variables:
```bash
docker run -p 5000:5000 \
  -e OPENAI_API_KEY=your-key \
  -e PINECONE_API_KEY=your-key \
  -e PINECONE_RFP_INDEX=your-key \
  -e RFP_SERVER_API_KEY=your-key \
  rfp-server
```

## Model Training
To retrain the sparse vectors and update all question embeddings:
```bash
python rfp_pinecone_embedder.py --train_sparse_model --update_pinecone_embedding
```

## Environment Variables
The following environment variables are required:
- `OPENAI_API_KEY`: Your OpenAI API key
- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_RFP_INDEX`: Your Pinecone index name
- `RFP_SERVER_API_KEY`: Your server API key

## Notes
- Ensure all required environment variables are set before running the application
- The server runs on port 5000 by default
- Make sure to replace `your-key` with actual API keys when running the Docker container


