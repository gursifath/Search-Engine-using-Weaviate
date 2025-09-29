# Backend Setup Guide

This guide will help you set up the FastAPI backend with ChatGPT integration for your search engine.

## Prerequisites

- Python 3.8 or higher
- OpenAI API key

## Setup Steps

### 1. Install Dependencies

Navigate to the backend directory and install the required packages:

```bash
cd SearchEngineApplication/backend
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the backend directory:

```bash
cp .env.example .env
```

Edit the `.env` file and add your OpenAI API key:

```
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 3. Run the Backend Server

Start the FastAPI server:

```bash
python run_server.py
```

Or alternatively:

```bash
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`

### 4. Run the Frontend

In a new terminal, navigate to the main application directory and run Streamlit:

```bash
cd SearchEngineApplication
streamlit run app.py
```

## API Endpoints

The backend provides the following endpoints:

### Health Check
- **GET** `/` - Check if the API is running

### Chat Endpoints
- **POST** `/chat/start` - Start a new chat session
- **POST** `/chat/message` - Send a message in an existing chat session
- **GET** `/chat/{session_id}` - Get chat session details
- **DELETE** `/chat/{session_id}` - Delete a chat session
- **GET** `/chat/sessions/list` - List all chat sessions

### API Documentation

Once the server is running, you can view the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Features

- ✅ Real-time ChatGPT integration
- ✅ Session-based chat management
- ✅ CORS configuration for frontend
- ✅ Error handling and fallbacks
- ✅ Conversation history management
- ✅ Async API for better performance

## Troubleshooting

1. **Backend connection error**: Make sure the FastAPI server is running on port 8000
2. **OpenAI API error**: Verify your API key is correctly set in the `.env` file
3. **CORS issues**: The backend is configured to allow connections from Streamlit (port 8501)

## Development

For development with auto-reload:
```bash
python run_server.py
```

The server will automatically restart when you make changes to the code.