# Shop API Gateway Example

This example demonstrates how to use **EnrichMCP** as a lightweight API gateway
in front of an existing FastAPI service. The gateway exposes the same shop data
model as other examples but forwards all requests to a separate backend running
on `http://localhost:8001`.

## Running the Example

1. Start the backend FastAPI server:
   ```bash
   uvicorn server:app --port 8001
   ```

2. In another terminal, run the EnrichMCP gateway:
   ```bash
   python app.py
   ```

The gateway will be available on `http://localhost:8000` and acts as an
agent-friendly layer over the backend service.

## How It Works

- `server.py` contains a normal FastAPI application with REST endpoints for
  users, products and orders.
- `app.py` defines the same data model using EnrichMCP. Each resolver makes
  HTTP requests to `server.py`, effectively proxying calls.

This pattern lets you keep your existing APIs while providing a schema-driven
interface that AI agents can understand.
