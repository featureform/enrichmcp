"""SQLAlchemy Shop API Example with automatic resolvers."""

import os
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from enrichmcp import EnrichMCP
from enrichmcp.sqlalchemy import (
    EnrichSQLAlchemyMixin,
    include_sqlalchemy_models,
    sqlalchemy_lifespan,
)


# Create base class with our mixin
class Base(DeclarativeBase, EnrichSQLAlchemyMixin):
    pass


# Define SQLAlchemy models
class User(Base):
    """User account in the shop system."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True, info={"description": "Unique user identifier"}
    )
    username: Mapped[str] = mapped_column(
        unique=True, info={"description": "User's unique username"}
    )
    email: Mapped[str] = mapped_column(unique=True, info={"description": "User's email address"})
    full_name: Mapped[str] = mapped_column(info={"description": "User's full name"})
    is_active: Mapped[bool] = mapped_column(
        default=True, info={"description": "Whether the user account is active"}
    )
    created_at: Mapped[datetime] = mapped_column(
        info={"description": "When the user account was created"}
    )

    # Relationships
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", info={"description": "All orders placed by this user"}
    )


class Product(Base):
    """Product available in the shop."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        primary_key=True, info={"description": "Unique product identifier"}
    )
    name: Mapped[str] = mapped_column(info={"description": "Product name"})
    description: Mapped[str | None] = mapped_column(
        nullable=True, info={"description": "Product description"}
    )
    price: Mapped[float] = mapped_column(info={"description": "Product price in USD"})
    stock_quantity: Mapped[int] = mapped_column(
        default=0, info={"description": "Current stock level"}
    )
    category: Mapped[str] = mapped_column(info={"description": "Product category"})
    created_at: Mapped[datetime] = mapped_column(info={"description": "When the product was added"})

    # Relationships
    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="product", info={"description": "Order items containing this product"}
    )


class Order(Base):
    """Customer order."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        primary_key=True, info={"description": "Unique order identifier"}
    )
    order_number: Mapped[str] = mapped_column(
        unique=True, info={"description": "Human-readable order number"}
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), info={"description": "ID of the user who placed the order"}
    )
    status: Mapped[str] = mapped_column(
        info={"description": "Order status (pending, processing, shipped, delivered, cancelled)"}
    )
    total_amount: Mapped[float] = mapped_column(info={"description": "Total order amount in USD"})
    created_at: Mapped[datetime] = mapped_column(info={"description": "When the order was placed"})
    updated_at: Mapped[datetime] = mapped_column(
        info={"description": "When the order was last updated"}
    )

    # Additional fields
    shipping_address: Mapped[str | None] = mapped_column(
        nullable=True, info={"description": "Shipping address"}
    )
    notes: Mapped[str | None] = mapped_column(nullable=True, info={"description": "Order notes"})

    # Relationships
    user: Mapped[User] = relationship(
        back_populates="orders", info={"description": "Customer who placed this order"}
    )
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        info={"description": "Items in this order"},
    )


class OrderItem(Base):
    """Individual item within an order."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        primary_key=True, info={"description": "Unique order item identifier"}
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), info={"description": "ID of the parent order"}
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), info={"description": "ID of the product"}
    )
    quantity: Mapped[int] = mapped_column(info={"description": "Quantity ordered"})
    unit_price: Mapped[float] = mapped_column(
        info={"description": "Price per unit at time of order"}
    )
    total_price: Mapped[float] = mapped_column(
        info={"description": "Total price for this line item"}
    )

    # Relationships
    order: Mapped[Order] = relationship(
        back_populates="items", info={"description": "Parent order"}
    )
    product: Mapped[Product] = relationship(
        back_populates="order_items", info={"description": "Product details"}
    )


# Create async engine
# Use absolute path relative to this file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shop.db")
engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")


# Seed database with sample data
async def seed_database(session: AsyncSession) -> None:
    """Populate the database with example data."""

    users = [
        User(
            username="john_doe",
            email="john@example.com",
            full_name="John Doe",
            created_at=datetime.now(),
        ),
        User(
            username="jane_smith",
            email="jane@example.com",
            full_name="Jane Smith",
            created_at=datetime.now(),
        ),
    ]
    session.add_all(users)

    products = [
        Product(
            name="Laptop",
            description="High-performance laptop",
            price=999.99,
            stock_quantity=50,
            category="Electronics",
            created_at=datetime.now(),
        ),
        Product(
            name="Wireless Mouse",
            description="Ergonomic wireless mouse",
            price=29.99,
            stock_quantity=200,
            category="Electronics",
            created_at=datetime.now(),
        ),
        Product(
            name="USB-C Cable",
            description="Fast charging USB-C cable",
            price=19.99,
            stock_quantity=500,
            category="Accessories",
            created_at=datetime.now(),
        ),
        Product(
            name="Coffee Maker",
            description="Programmable coffee maker",
            price=79.99,
            stock_quantity=30,
            category="Appliances",
            created_at=datetime.now(),
        ),
    ]
    session.add_all(products)
    await session.flush()

    order1 = Order(
        order_number="ORD-001",
        user_id=users[0].id,
        status="delivered",
        total_amount=1029.98,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        shipping_address="123 Main St, City, State 12345",
    )
    order2 = Order(
        order_number="ORD-002",
        user_id=users[1].id,
        status="processing",
        total_amount=99.98,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        shipping_address="456 Oak Ave, Town, State 67890",
    )
    session.add_all([order1, order2])
    await session.flush()

    items = [
        OrderItem(
            order_id=order1.id,
            product_id=products[0].id,
            quantity=1,
            unit_price=999.99,
            total_price=999.99,
        ),
        OrderItem(
            order_id=order1.id,
            product_id=products[1].id,
            quantity=1,
            unit_price=29.99,
            total_price=29.99,
        ),
        OrderItem(
            order_id=order2.id,
            product_id=products[3].id,
            quantity=1,
            unit_price=79.99,
            total_price=79.99,
        ),
        OrderItem(
            order_id=order2.id,
            product_id=products[2].id,
            quantity=1,
            unit_price=19.99,
            total_price=19.99,
        ),
    ]
    session.add_all(items)


# Application instance will be created after defining the lifespan

lifespan = sqlalchemy_lifespan(Base, engine, seed=seed_database, cleanup_db_file=True)


app = EnrichMCP(
    title="Shop API (SQLAlchemy)",
    description="E-commerce shop API using SQLAlchemy models",
    lifespan=lifespan,
)

# Automatically register models and default resolvers
include_sqlalchemy_models(app, Base)


if __name__ == "__main__":
    # Run the app
    app.run()
