"""
Shop API Example with SQLite Database

This example demonstrates using EnrichMCP with a real SQLite database,
showing how to use context injection and lifespan management.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite
from pydantic import Field

from enrichmcp import CursorResult, EnrichContext, EnrichMCP, EnrichModel, Relationship


# Database helper class
class Database:
    """Simple async wrapper for SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        """Connect to the database."""
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self.init_schema()

    async def close(self):
        """Close the database connection."""
        if self.conn:
            await self.conn.close()

    async def init_schema(self):
        """Initialize the database schema."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.cursor()

        # Create tables
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_verified BOOLEAN DEFAULT 0,
                risk_score REAL DEFAULT 0.0
            )
            """
        )

        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                fraud_risk TEXT DEFAULT 'low'
            )
            """
        )

        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                order_number TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                total_amount REAL NOT NULL,
                risk_score REAL DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )

        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS order_products (
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                PRIMARY KEY (order_id, product_id),
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            """
        )

        await self.conn.commit()

        # Insert sample data if tables are empty
        await cursor.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        if row[0] == 0:
            await self._insert_sample_data()

    async def _insert_sample_data(self):
        """Insert sample data into the database."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.cursor()

        # Insert users
        users = [
            ("john_doe", "john@example.com", "John Doe", 1, 0.1),
            ("jane_smith", "jane@example.com", "Jane Smith", 1, 0.05),
            ("suspicious_user", "suspicious@example.com", "Suspicious User", 0, 0.85),
        ]
        await cursor.executemany(
            "INSERT INTO users (username, email, full_name, is_verified, risk_score) "
            "VALUES (?, ?, ?, ?, ?)",
            users,
        )

        # Insert products
        products = [
            ("PHONE-001", "Smartphone Pro", "Latest smartphone", 999.99, 45, "high"),
            ("LAPTOP-001", "Business Laptop", "Professional laptop", 1299.99, 23, "high"),
            ("HDPHONE-001", "Wireless Headphones", "Noise-canceling", 299.99, 67, "medium"),
        ]
        await cursor.executemany(
            "INSERT INTO products (sku, name, description, price, stock, fraud_risk) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            products,
        )

        # Insert orders
        orders = [
            ("ORD-2023-1001", 1, "delivered", 329.98, 0.1),
            ("ORD-2023-1002", 2, "delivered", 1449.98, 0.05),
            ("ORD-2024-1003", 3, "flagged", 4299.99, 0.95),
        ]
        await cursor.executemany(
            "INSERT INTO orders (order_number, user_id, status, total_amount, risk_score) "
            "VALUES (?, ?, ?, ?, ?)",
            orders,
        )

        # Insert order products
        order_products = [
            (1, 3, 1),  # Order 1: headphones
            (2, 2, 1),  # Order 2: laptop
            (3, 1, 1),  # Order 3: phone
            (3, 2, 1),  # Order 3: laptop
        ]
        await cursor.executemany(
            "INSERT INTO order_products (order_id, product_id, quantity) VALUES (?, ?, ?)",
            order_products,
        )

        await self.conn.commit()

    async def get_user(self, user_id: int) -> dict | None:
        """Get a user by ID."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all_users(self) -> list[dict]:
        """Get all users."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.execute("SELECT * FROM users")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_user_orders(self, user_id: int) -> list[dict]:
        """Get all orders for a user."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_order_user(self, order_id: int) -> dict | None:
        """Get the user who placed an order."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.execute(
            """
            SELECT u.* FROM users u
            JOIN orders o ON u.id = o.user_id
            WHERE o.id = ?
        """,
            (order_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_order_products(self, order_id: int) -> list[dict]:
        """Get all products in an order."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.execute(
            """
            SELECT p.* FROM products p
            JOIN order_products op ON p.id = op.product_id
            WHERE op.order_id = ?
        """,
            (order_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_all_products(self) -> list[dict]:
        """Get all products."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = await self.conn.execute("SELECT * FROM products")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_all_orders(
        self, status: str | None = None, cursor: str | None = None, limit: int = 50
    ) -> tuple[list[dict], str | None]:
        """Get orders with cursor pagination, optionally filtered by status."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        db_cursor = await self.conn.cursor()

        if cursor is None:
            # First page
            if status:
                await db_cursor.execute(
                    """SELECT * FROM orders WHERE status = ?
                       ORDER BY created_at DESC, id DESC LIMIT ?""",
                    (status, limit + 1),
                )
            else:
                await db_cursor.execute(
                    "SELECT * FROM orders ORDER BY created_at DESC, id DESC LIMIT ?", (limit + 1,)
                )
        else:
            # Parse cursor (timestamp:id format)
            try:
                timestamp, last_id = cursor.split(":")
                if status:
                    await db_cursor.execute(
                        """SELECT * FROM orders
                           WHERE status = ? AND (created_at, id) < (?, ?)
                           ORDER BY created_at DESC, id DESC
                           LIMIT ?""",
                        (status, timestamp, int(last_id), limit + 1),
                    )
                else:
                    await db_cursor.execute(
                        """SELECT * FROM orders
                           WHERE (created_at, id) < (?, ?)
                           ORDER BY created_at DESC, id DESC
                           LIMIT ?""",
                        (timestamp, int(last_id), limit + 1),
                    )
            except (ValueError, IndexError):
                return [], None

        rows = await db_cursor.fetchall()
        orders = [dict(row) for row in rows]

        # Check if there are more results
        has_more = len(orders) > limit
        if has_more:
            orders = orders[:-1]  # Remove the extra item
            last_order = orders[-1]
            next_cursor = f"{last_order['created_at']}:{last_order['id']}"
        else:
            next_cursor = None

        return orders, next_cursor


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: EnrichMCP) -> AsyncIterator[dict[str, Any]]:
    """Manage database connection lifecycle."""
    # Setup
    db_path = Path(__file__).parent / "shop.db"
    db = Database(str(db_path))
    await db.connect()
    print(f"✅ Connected to SQLite database: {db_path}")

    try:
        # Yield the context that will be available in handlers
        yield {"db": db}
    finally:
        # Cleanup
        await db.close()
        print("🔒 Closed database connection")

        # Delete the database file to keep examples clean
        if db_path.exists():
            db_path.unlink()
            print("🗑️  Deleted temporary database file")


# Create the application with lifespan
app = EnrichMCP(
    title="E-Commerce Shop API (SQLite)",
    description="E-commerce API with SQLite database backend.",
    lifespan=lifespan,
)


# Define entities
@app.entity
class User(EnrichModel):
    """Customer account in the e-commerce system."""

    id: int = Field(description="Unique user identifier")
    username: str = Field(description="Unique username for login")
    email: str = Field(description="Email address for communications")
    full_name: str = Field(description="Customer's full name")
    created_at: datetime = Field(description="Account creation timestamp")
    is_verified: bool = Field(description="Whether email is verified")
    risk_score: float = Field(description="Risk score from 0.0 to 1.0")

    # Relationships
    orders: list["Order"] = Relationship(description="All orders placed by this user")


@app.entity
class Product(EnrichModel):
    """Product available for purchase in the store."""

    id: int = Field(description="Unique product identifier")
    sku: str = Field(description="Stock keeping unit for inventory")
    name: str = Field(description="Product display name")
    description: str = Field(description="Detailed product description")
    price: float = Field(description="Current price in USD")
    stock: int = Field(description="Available inventory count")
    fraud_risk: str = Field(description="Fraud risk level: low, medium, or high")


@app.entity
class Order(EnrichModel):
    """Customer order containing one or more products."""

    id: int = Field(description="Unique order identifier")
    order_number: str = Field(description="Human-readable order number")
    user_id: int = Field(description="Customer who placed the order")
    created_at: datetime = Field(description="Order placement timestamp")
    status: str = Field(
        description="Order status: pending, shipped, delivered, cancelled, or flagged"
    )
    total_amount: float = Field(description="Total order value in USD")
    risk_score: float = Field(description="Calculated risk score from 0.0 to 1.0")

    # Relationships
    user: User = Relationship(description="Customer who placed this order")
    products: list[Product] = Relationship(description="Products included in this order")


# Define relationship resolvers that use the database
@User.orders.resolver
async def by_user_id(user_id: int, ctx: EnrichContext) -> list["Order"]:
    """Get all orders for a specific user from the database."""
    # Access the database from the lifespan context
    db: Database = ctx.request_context.lifespan_context["db"]

    # Query the database
    order_rows = await db.get_user_orders(user_id)

    # Convert to Order models
    orders = []
    for row in order_rows:
        orders.append(
            Order(
                id=row["id"],
                order_number=row["order_number"],
                user_id=row["user_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                status=row["status"],
                total_amount=row["total_amount"],
                risk_score=row["risk_score"],
            )
        )

    return orders


@Order.user.resolver
async def by_order_id(order_id: int, ctx: EnrichContext) -> User:
    """Get the user who placed a specific order."""
    db: Database = ctx.request_context.lifespan_context["db"]

    user_row = await db.get_order_user(order_id)
    if not user_row:
        # Return a placeholder user
        return User(
            id=-1,
            username="unknown",
            email="unknown@example.com",
            full_name="Unknown User",
            created_at=datetime.now(),
            is_verified=False,
            risk_score=0.0,
        )

    return User(
        id=user_row["id"],
        username=user_row["username"],
        email=user_row["email"],
        full_name=user_row["full_name"],
        created_at=datetime.fromisoformat(user_row["created_at"]),
        is_verified=bool(user_row["is_verified"]),
        risk_score=user_row["risk_score"],
    )


@Order.products.resolver
async def by_order_id_products(order_id: int, ctx: EnrichContext) -> list[Product]:
    """Get all products included in a specific order."""
    db: Database = ctx.request_context.lifespan_context["db"]

    product_rows = await db.get_order_products(order_id)

    products = []
    for row in product_rows:
        products.append(
            Product(
                id=row["id"],
                sku=row["sku"],
                name=row["name"],
                description=row["description"],
                price=row["price"],
                stock=row["stock"],
                fraud_risk=row["fraud_risk"],
            )
        )

    return products


# Define root resources
@app.retrieve
async def list_users(ctx: EnrichContext) -> list[User]:
    """List all users in the system."""
    db: Database = ctx.request_context.lifespan_context["db"]

    user_rows = await db.get_all_users()

    users = []
    for row in user_rows:
        users.append(
            User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                full_name=row["full_name"],
                created_at=datetime.fromisoformat(row["created_at"]),
                is_verified=bool(row["is_verified"]),
                risk_score=row["risk_score"],
            )
        )

    return users


@app.retrieve
async def get_user(user_id: int, ctx: EnrichContext) -> User:
    """Get a specific user by ID."""
    db: Database = ctx.request_context.lifespan_context["db"]

    user_row = await db.get_user(user_id)
    if not user_row:
        return User(
            id=-1,
            username="not_found",
            email="notfound@example.com",
            full_name="User Not Found",
            created_at=datetime.now(),
            is_verified=False,
            risk_score=0.0,
        )

    return User(
        id=user_row["id"],
        username=user_row["username"],
        email=user_row["email"],
        full_name=user_row["full_name"],
        created_at=datetime.fromisoformat(user_row["created_at"]),
        is_verified=bool(user_row["is_verified"]),
        risk_score=user_row["risk_score"],
    )


@app.retrieve
async def list_products(ctx: EnrichContext) -> list[Product]:
    """List all products in the catalog."""
    db: Database = ctx.request_context.lifespan_context["db"]

    product_rows = await db.get_all_products()

    products = []
    for row in product_rows:
        products.append(
            Product(
                id=row["id"],
                sku=row["sku"],
                name=row["name"],
                description=row["description"],
                price=row["price"],
                stock=row["stock"],
                fraud_risk=row["fraud_risk"],
            )
        )

    return products


@app.retrieve
async def list_orders(
    ctx: EnrichContext, status: str | None = None, cursor: str | None = None, limit: int = 10
) -> CursorResult[Order]:
    """List orders, optionally filtered by status."""
    db: Database = ctx.request_context.lifespan_context["db"]

    order_rows, next_cursor = await db.get_all_orders(status, cursor, limit)

    orders = []
    for row in order_rows:
        orders.append(
            Order(
                id=row["id"],
                order_number=row["order_number"],
                user_id=row["user_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                status=row["status"],
                total_amount=row["total_amount"],
                risk_score=row["risk_score"],
            )
        )

    return CursorResult.create(items=orders, next_cursor=next_cursor, page_size=limit)


# Run the server
if __name__ == "__main__":
    print("Starting E-Commerce Shop API with SQLite...")
    app.run()
