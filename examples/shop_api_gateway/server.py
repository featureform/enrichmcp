"""Simple FastAPI backend for the API gateway example."""

from datetime import datetime

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Shop Backend")

USERS = [
    {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "created_at": datetime(2022, 1, 15),
    },
    {
        "id": 2,
        "username": "jane_smith",
        "email": "jane@example.com",
        "full_name": "Jane Smith",
        "created_at": datetime(2021, 6, 20),
    },
    {
        "id": 3,
        "username": "quick_buyer_2024",
        "email": "tempmail@protonmail.com",
        "full_name": "Alex Johnson",
        "created_at": datetime(2024, 1, 5),
    },
]

PRODUCTS = [
    {"id": 101, "sku": "PHONE-001", "name": "Smartphone Pro", "price": 999.99},
    {"id": 102, "sku": "LAPTOP-001", "name": "Business Laptop", "price": 1299.99},
    {
        "id": 103,
        "sku": "HDPHONE-001",
        "name": "Wireless Headphones",
        "price": 299.99,
    },
]

ORDERS = [
    {
        "id": 1001,
        "order_number": "ORD-2023-1001",
        "user_id": 1,
        "created_at": datetime(2023, 10, 15, 14, 30),
        "status": "delivered",
        "total_amount": 329.98,
        "product_ids": [103],
    },
    {
        "id": 1002,
        "order_number": "ORD-2023-1002",
        "user_id": 2,
        "created_at": datetime(2023, 11, 20, 11, 15),
        "status": "delivered",
        "total_amount": 1449.98,
        "product_ids": [102],
    },
    {
        "id": 1003,
        "order_number": "ORD-2024-1003",
        "user_id": 3,
        "created_at": datetime(2024, 1, 6, 2, 45),
        "status": "flagged",
        "total_amount": 4299.99,
        "product_ids": [101, 102, 103],
    },
]


@app.get("/users")
async def list_users():
    return USERS


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = next((u for u in USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/products")
async def list_products():
    return PRODUCTS


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/orders")
async def list_orders(user_id: int | None = None):
    orders = ORDERS
    if user_id is not None:
        orders = [o for o in ORDERS if o["user_id"] == user_id]
    return orders


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    order = next((o for o in ORDERS if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
