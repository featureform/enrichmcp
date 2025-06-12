"""
SQLAlchemy Shop API Example

This example demonstrates how to use EnrichMCP with SQLAlchemy models.
It's based on the shop_api_sqlite example but uses SQLAlchemy ORM.

Note: The resolvers and auto-generated resources are not yet implemented,
so this example shows the model setup and basic structure.
"""

import os
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, func, select
<<<<<<< HEAD
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from enrichmcp import CursorResult, EnrichContext, EnrichMCP, PageResult
from enrichmcp.sqlalchemy import EnrichSQLAlchemyMixin, sqlalchemy_lifespan
=======
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from enrichmcp import CursorResult, EnrichContext, EnrichMCP, PageResult
from enrichmcp.sqlalchemy import EnrichSQLAlchemyMixin
>>>>>>> feature/sqlalchemy-support/simba


# Create base class with our mixin
class Base(DeclarativeBase, EnrichSQLAlchemyMixin):
    pass


# Define SQLAlchemy models
class User(Base):
    """User account in the shop system."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
<<<<<<< HEAD
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
=======
        primary_key=True,
        info={"description": "Unique user identifier"},
    )
    username: Mapped[str] = mapped_column(
        unique=True,
        info={"description": "User's unique username"},
    )
    email: Mapped[str] = mapped_column(
        unique=True,
        info={"description": "User's email address"},
    )
    full_name: Mapped[str] = mapped_column(
        info={"description": "User's full name"},
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        info={"description": "Whether the user account is active"},
    )
    created_at: Mapped[datetime] = mapped_column(
        info={"description": "When the user account was created"},
>>>>>>> feature/sqlalchemy-support/simba
    )

    # Relationships
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", info={"description": "All orders placed by this user"}
    )


class Product(Base):
    """Product available in the shop."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
<<<<<<< HEAD
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
=======
        primary_key=True,
        info={"description": "Unique product identifier"},
    )
    name: Mapped[str] = mapped_column(
        info={"description": "Product name"},
    )
    description: Mapped[str | None] = mapped_column(
        nullable=True,
        info={"description": "Product description"},
    )
    price: Mapped[float] = mapped_column(
        info={"description": "Product price in USD"},
    )
    stock_quantity: Mapped[int] = mapped_column(
        default=0,
        info={"description": "Current stock level"},
    )
    category: Mapped[str] = mapped_column(
        info={"description": "Product category"},
    )
    created_at: Mapped[datetime] = mapped_column(
        info={"description": "When the product was added"},
    )
>>>>>>> feature/sqlalchemy-support/simba

    # Relationships
    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="product", info={"description": "Order items containing this product"}
    )


class Order(Base):
    """Customer order."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
<<<<<<< HEAD
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
=======
        primary_key=True,
        info={"description": "Unique order identifier"},
    )
    order_number: Mapped[str] = mapped_column(
        unique=True,
        info={"description": "Human-readable order number"},
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        info={"description": "ID of the user who placed the order"},
    )
    status: Mapped[str] = mapped_column(
        info={"description": "Order status (pending, processing, shipped, delivered, cancelled)"},
    )
    total_amount: Mapped[float] = mapped_column(
        info={"description": "Total order amount in USD"},
    )
    created_at: Mapped[datetime] = mapped_column(
        info={"description": "When the order was placed"},
    )
    updated_at: Mapped[datetime] = mapped_column(
        info={"description": "When the order was last updated"},
>>>>>>> feature/sqlalchemy-support/simba
    )

    # Additional fields
    shipping_address: Mapped[str | None] = mapped_column(
<<<<<<< HEAD
        nullable=True, info={"description": "Shipping address"}
    )
    notes: Mapped[str | None] = mapped_column(nullable=True, info={"description": "Order notes"})
=======
        nullable=True,
        info={"description": "Shipping address"},
    )
    notes: Mapped[str | None] = mapped_column(
        nullable=True,
        info={"description": "Order notes"},
    )
>>>>>>> feature/sqlalchemy-support/simba

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
<<<<<<< HEAD
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
=======
        primary_key=True,
        info={"description": "Unique order item identifier"},
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        info={"description": "ID of the parent order"},
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        info={"description": "ID of the product"},
    )
    quantity: Mapped[int] = mapped_column(
        info={"description": "Quantity ordered"},
    )
    unit_price: Mapped[float] = mapped_column(
        info={"description": "Price per unit at time of order"},
    )
    total_price: Mapped[float] = mapped_column(
        info={"description": "Total price for this line item"},
>>>>>>> feature/sqlalchemy-support/simba
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


<<<<<<< HEAD
# Seed database with sample data
async def seed_database(session: AsyncSession) -> None:
    """Populate the database with example data."""
=======
# Create EnrichMCP app
@asynccontextmanager
async def lifespan(app: EnrichMCP):
    """Initialize database and provide session in context."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed some data if needed
    async with AsyncSessionMaker() as session:
        # Check if we have any users
        result = await session.execute(select(User).limit(1))
        if not result.scalar():
            # Add sample data
            await seed_database(session)
            await session.commit()

    # Provide session factory in context
    yield {"session_factory": AsyncSessionMaker}
>>>>>>> feature/sqlalchemy-support/simba

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

lifespan = sqlalchemy_lifespan(Base, engine, seed=seed_database)

app = EnrichMCP(
    title="Shop API (SQLAlchemy)",
    description="E-commerce shop API using SQLAlchemy models",
    lifespan=lifespan,
)


# Register entities - convert SQLAlchemy models to EnrichModels
# Use the expected naming convention: <ModelName>EnrichModel
@app.entity
class UserEnrichModel(User.__enrich_model__()):
    """User entity based on SQLAlchemy model."""

    pass


@app.entity
class ProductEnrichModel(Product.__enrich_model__()):
    """Product entity based on SQLAlchemy model."""

    pass


@app.entity
class OrderEnrichModel(Order.__enrich_model__()):
    """Order entity based on SQLAlchemy model."""

    pass


@app.entity
class OrderItemEnrichModel(OrderItem.__enrich_model__()):
    """Order item entity based on SQLAlchemy model."""

    pass


# Manual resources for now (until auto-generation is implemented)
@app.resource
async def list_users(ctx: EnrichContext) -> list[UserEnrichModel]:
    """List all users in the system."""
    session_factory = ctx.request_context.lifespan_context["session_factory"]
    async with session_factory() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        return [
            UserEnrichModel(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at,
            )
            for user in users
        ]


@app.resource
async def get_user(user_id: int, ctx: EnrichContext) -> UserEnrichModel | None:
    """Get a specific user by ID."""
    session_factory = ctx.request_context.lifespan_context["session_factory"]
    async with session_factory() as session:
        user = await session.get(User, user_id)
        if not user:
            return None

        return UserEnrichModel(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
        )


@app.resource
async def list_products(
    ctx: EnrichContext, category: str | None = None, page: int = 1, page_size: int = 20
) -> PageResult[ProductEnrichModel]:
    """List products with optional filtering by category."""
    session_factory = ctx.request_context.lifespan_context["session_factory"]
    async with session_factory() as session:
        # Build query
        query = select(Product)
        if category:
            query = query.where(Product.category == category)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query)

        # Get paginated results
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(query)
        products = result.scalars().all()

        items = [
            ProductEnrichModel(
                id=product.id,
                name=product.name,
                description=product.description,
                price=product.price,
                stock_quantity=product.stock_quantity,
                category=product.category,
                created_at=product.created_at,
            )
            for product in products
        ]

        return PageResult.create(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total,
            has_next=page * page_size < total,
        )


@app.resource
async def list_orders(
    ctx: EnrichContext, status: str | None = None, cursor: str | None = None, limit: int = 10
) -> CursorResult[OrderEnrichModel]:
    """List orders with cursor-based pagination."""
    session_factory = ctx.request_context.lifespan_context["session_factory"]
    async with session_factory() as session:
        # Build query
        query = select(Order)

        # Apply status filter
        if status:
            query = query.where(Order.status == status)

        # Apply cursor (assuming cursor is the last order ID seen)
        if cursor:
            query = query.where(Order.id > int(cursor))

        # Order by ID for consistent cursor pagination
        query = query.order_by(Order.id).limit(limit + 1)

        result = await session.execute(query)
        orders = result.scalars().all()

        # Check if there are more results
        has_next = len(orders) > limit
        if has_next:
            orders = orders[:-1]  # Remove the extra item

        items = [
            OrderEnrichModel(
                id=order.id,
                order_number=order.order_number,
                user_id=order.user_id,
                status=order.status,
                total_amount=order.total_amount,
                created_at=order.created_at,
                updated_at=order.updated_at,
                shipping_address=order.shipping_address,
                notes=order.notes,
            )
            for order in orders
        ]

        next_cursor = str(orders[-1].id) if orders else None

        return CursorResult(
            items=items, next_cursor=next_cursor, page_size=limit, has_next=has_next
        )


# Manual relationship resolvers (until auto-generation is implemented)
@UserEnrichModel.orders.resolver
async def get_user_orders(user_id: int, ctx: EnrichContext) -> list["OrderEnrichModel"]:
    """Get all orders for a specific user."""
    session_factory = ctx.request_context.lifespan_context["session_factory"]
    async with session_factory() as session:
        result = await session.execute(
            select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

        return [
            OrderEnrichModel(
                id=order.id,
                order_number=order.order_number,
                user_id=order.user_id,
                status=order.status,
                total_amount=order.total_amount,
                created_at=order.created_at,
                updated_at=order.updated_at,
                shipping_address=order.shipping_address,
                notes=order.notes,
            )
            for order in orders
        ]


@OrderEnrichModel.user.resolver
async def get_order_user(order_id: int, ctx: EnrichContext) -> UserEnrichModel | None:
    """Get the user who placed a specific order."""
    session_factory = ctx.request_context.lifespan_context["session_factory"]
    async with session_factory() as session:
        order = await session.get(Order, order_id)
        if not order:
            return None

        # Load the user (SQLAlchemy will handle the join)
        await session.refresh(order, ["user"])
        user = order.user

        return UserEnrichModel(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
        )


@OrderEnrichModel.items.resolver
async def get_order_items(order_id: int, ctx: EnrichContext) -> list["OrderItemEnrichModel"]:
    """Get all items in a specific order."""
    session_factory = ctx.request_context.lifespan_context["session_factory"]
    async with session_factory() as session:
        result = await session.execute(select(OrderItem).where(OrderItem.order_id == order_id))
        items = result.scalars().all()

        return [
            OrderItemEnrichModel(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
            )
            for item in items
        ]


# Add missing resolvers for Product and OrderItem relationships
@ProductEnrichModel.order_items.resolver
async def get_product_order_items(
    product_id: int, ctx: EnrichContext
) -> list["OrderItemEnrichModel"]:
    """Get all order items for a specific product."""
    session_factory = ctx.request_context.lifespan_context["session_factory"]
    async with session_factory() as session:
        result = await session.execute(select(OrderItem).where(OrderItem.product_id == product_id))
        items = result.scalars().all()

        return [
            OrderItemEnrichModel(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
            )
            for item in items
        ]


@OrderItemEnrichModel.order.resolver
async def get_order_item_order(
    order_item_id: int, ctx: EnrichContext
) -> Optional["OrderEnrichModel"]:
    """Get the order for a specific order item."""
    session_factory = ctx.request_context.lifespan_context["session_factory"]
    async with session_factory() as session:
        item = await session.get(OrderItem, order_item_id)
        if not item:
            return None

        # Load the order
        await session.refresh(item, ["order"])
        order = item.order

        return OrderEnrichModel(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            status=order.status,
            total_amount=order.total_amount,
            created_at=order.created_at,
            updated_at=order.updated_at,
            shipping_address=order.shipping_address,
            notes=order.notes,
        )


@OrderItemEnrichModel.product.resolver
async def get_order_item_product(
    order_item_id: int, ctx: EnrichContext
) -> Optional["ProductEnrichModel"]:
    """Get the product for a specific order item."""
    session_factory = ctx.request_context.lifespan_context["session_factory"]
    async with session_factory() as session:
        item = await session.get(OrderItem, order_item_id)
        if not item:
            return None

        # Load the product
        await session.refresh(item, ["product"])
        product = item.product

        return ProductEnrichModel(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            stock_quantity=product.stock_quantity,
            category=product.category,
            created_at=product.created_at,
        )


<<<<<<< HEAD
=======
async def seed_database(session: AsyncSession):
    """Seed the database with sample data."""
    # Create users
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

    # Create products
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

    # Flush to get IDs
    await session.flush()

    # Create orders
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

    # Create order items
    items = [
        OrderItem(
            order_id=order1.id,
            product_id=products[0].id,  # Laptop
            quantity=1,
            unit_price=999.99,
            total_price=999.99,
        ),
        OrderItem(
            order_id=order1.id,
            product_id=products[1].id,  # Mouse
            quantity=1,
            unit_price=29.99,
            total_price=29.99,
        ),
        OrderItem(
            order_id=order2.id,
            product_id=products[3].id,  # Coffee Maker
            quantity=1,
            unit_price=79.99,
            total_price=79.99,
        ),
        OrderItem(
            order_id=order2.id,
            product_id=products[2].id,  # USB-C Cable
            quantity=1,
            unit_price=19.99,
            total_price=19.99,
        ),
    ]
    session.add_all(items)


>>>>>>> feature/sqlalchemy-support/simba
if __name__ == "__main__":
    # Run the app
    app.run()
