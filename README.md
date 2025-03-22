# Multi-Agent Project Generator

## Project Overview

This project implements a sophisticated multi-agent system that can generate and manage web applications. The system consists of three main components:

- A modern React frontend application
- A FastAPI backend service
- An agent system for project generation and management

The system allows users to interact with AI agents that can generate, modify, and manage web applications through natural language commands.

## Technologies Used

### Frontend (app/)

- React 19
- TypeScript
- Vite
- TailwindCSS
- ESLint

### Backend (backend/)

- FastAPI
- Uvicorn
- WebSockets
- Pydantic

### Agent System (agent/)

- Pydantic AI
- Python dotenv
- Custom agent tools and utilities

## Installation Instructions

### Frontend Setup

1. Navigate to the `app` directory:

   ```bash
   cd app
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

### Backend Setup

1. Navigate to the `backend` directory:

   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the backend directory with the following variables:

   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

5. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```

The backend API will be available at `http://localhost:8000`

## Usage Guide

1. Start both the frontend and backend servers as described in the installation instructions.

2. Open your browser and navigate to `http://localhost:5173`

3. Use the web interface to create a Next.js project and run view it

## Team Contributions

## Project Structure

```
.
├── app/                 # Frontend React application
├── backend/            # FastAPI backend service
└── agent/             # AI agent system
    ├── agents/        # Agent implementations
    ├── tools/         # Agent tools and utilities
    └── utils/         # Helper utilities
```
