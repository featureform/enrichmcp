# Shop API Example

This example demonstrates how to create a more complex data model with multiple entities and relationships for an e-commerce shop using EnrichMCP.

## Features

- Multiple entity types: User, Item, and Order
- Bidirectional relationships between entities
- Custom resolvers for each relationship
- Root resource endpoints for retrieving entities
- Specialty endpoints for common operations
- Sample test data

## Entity Relationships

- **User.orders**: A user can have multiple orders
- **Item.orders**: An item can be included in multiple orders
- **Order.user**: An order belongs to a single user
- **Order.items**: An order can contain multiple items

## Available Endpoints

The API exposes the following endpoints:

### Entity Endpoints

- `/get_users`: Get all users or a specific user by ID
- `/get_items`: Get all items or a specific item by ID
- `/get_orders`: Get all orders or a specific order by ID

### Relationship Endpoints (automatically generated)

- `/get_user_orders`: Get all orders for a specific user
- `/get_item_orders`: Get all orders that include a specific item
- `/get_order_user`: Get the user who placed a specific order
- `/get_order_items`: Get all items included in a specific order

### Specialty Endpoints

- `/search_items`: Search for items by category or name
- `/get_user_order_history`: Get a user's complete order history with all item details

## Running the Example

```bash
cd examples/shop_api
python app.py
```

Access the API at `http://localhost:8000` and the interactive API documentation at `http://localhost:8000/docs`.

## Data Model Description

Access a complete description of the data model at `/describe_model`.
