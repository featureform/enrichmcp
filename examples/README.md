# EnrichMCP Examples

This directory contains examples demonstrating how to use EnrichMCP.

## Hello World

The simplest possible EnrichMCP application with a single resource that returns "Hello, World!".

To run this example:

```bash
cd hello_world
python app.py
```

## Shop API

A more complex example demonstrating an e-commerce shop API with multiple entities (users, orders, items) and relationships between them.

To run this example:

```bash
cd shop_api
python app.py
```

This example demonstrates:
- Creating multiple entity models
- Defining relationships between entities
- Automatically generating a data model description (available at the `/describe_model` resource)
