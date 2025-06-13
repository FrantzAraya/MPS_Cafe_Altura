# Café de Altura Production Planning

This project contains a small planning system for **Café de Altura**. It is split
into a FastAPI backend and a Streamlit frontend. The backend exposes the API and
stores the data, while the frontend provides an easy to use interface for the
planner.

These instructions assume you are starting from a clean machine with Python
installed. Python 3.10 or newer is recommended.

## Installation

1. **Clone the repository** (if you have not already) and navigate to its root.
2. **Create and activate a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. **Install the dependencies** for both the backend and the frontend:

 ```bash
  pip install -r server/requirements.txt -r client/requirements.txt
  ```
   This installs all required packages, including
   `pydantic-settings` which is needed for the configuration
   classes in the backend.
4. **Create environment files** from the provided examples:

   ```bash
   cp server/.env.example server/.env
   cp client/.env.example client/.env
   ```
   Adjust the values if you need to use a different database location, API port
   or URL.

The default configuration uses SQLite and will create a file called `app.db` when
the server starts for the first time.

## Running the backend

From the repository root, launch the API using Uvicorn:

```bash
cd server
uvicorn app.main:app --reload
```

The API will start on `http://localhost:8000/` by default. Interactive
documentation is available at `http://localhost:8000/docs`.

## Running the frontend

In a new terminal (with the virtual environment still activated) start the
Streamlit app:

```bash
cd client
streamlit run main.py
```

Streamlit will serve the interface on `http://localhost:8501/`. Make sure the
backend is running so the client can fetch data.

## Development notes

- The backend database tables are created automatically on startup.
- Example environment variable files are provided in both the `server` and
  `client` directories for quick setup.

With both services running you can begin using the planning system through your
web browser.
