"""
Shop API Example for EnrichMCP

This example demonstrates the EnrichMCP framework with a simple e-commerce API
that includes fraud detection patterns. It showcases entity relationships,
data modeling, and how AI agents can navigate structured data.
"""

from datetime import datetime

from pydantic import Field

from enrichmcp import EnrichMCP, EnrichModel, PageResult, Relationship

# Create the application
app = EnrichMCP(
    title="E-Commerce Shop API",
    description=(
        "An e-commerce API with users, products, and orders including fraud detection patterns."
    ),
)


# Define entities
@app.entity
class User(EnrichModel):
    """Customer account in the e-commerce system.

    Represents users who can browse products and place orders. Includes
    risk indicators for fraud detection such as account age and verification status.
    """

    id: int = Field(description="Unique user identifier")
    username: str = Field(description="Unique username for login")
    email: str = Field(description="Email address for communications")
    full_name: str = Field(description="Customer's full name")
    phone: str = Field(description="Contact phone number")
    created_at: datetime = Field(description="Account creation timestamp")
    last_login: datetime = Field(description="Most recent login time")
    is_verified: bool = Field(description="Whether email is verified")
    total_spent: float = Field(description="Lifetime purchase amount in USD")
    billing_address: str = Field(description="Default billing address")
    shipping_address: str = Field(description="Default shipping address")
    risk_score: float = Field(description="Risk score from 0.0 to 1.0 based on behavior")
    account_status: str = Field(description="Status: active, suspended, or flagged")

    # Relationships
    orders: list["Order"] = Relationship(description="All orders placed by this user")


@app.entity
class Product(EnrichModel):
    """Product available for purchase in the store.

    Items that customers can order. Includes pricing, inventory, and
    fraud risk indicators based on how often the product is involved
    in fraudulent transactions.
    """

    id: int = Field(description="Unique product identifier")
    sku: str = Field(description="Stock keeping unit for inventory")
    name: str = Field(description="Product display name")
    description: str = Field(description="Detailed product description")
    category: str = Field(description="Product category")
    price: float = Field(description="Current price in USD")
    cost: float = Field(description="Wholesale cost to business")
    stock: int = Field(description="Available inventory count")
    is_active: bool = Field(description="Whether product is available for sale")
    created_at: datetime = Field(description="When product was added to catalog")
    fraud_risk: str = Field(description="Fraud risk level: low, medium, or high")


@app.entity
class Order(EnrichModel):
    """Customer order containing one or more products.

    Represents a complete purchase transaction. Includes comprehensive
    fraud detection signals such as shipping details, payment verification,
    and behavioral risk factors.
    """

    id: int = Field(description="Unique order identifier")
    order_number: str = Field(description="Human-readable order number")
    user_id: int = Field(description="Customer who placed the order")
    created_at: datetime = Field(description="Order placement timestamp")
    status: str = Field(
        description="Order status: pending, shipped, delivered, cancelled, or flagged"
    )
    payment_method: str = Field(description="Payment type: credit_card, paypal, etc")
    total_amount: float = Field(description="Total order value in USD")
    shipping_amount: float = Field(description="Shipping cost")
    tax_amount: float = Field(description="Sales tax amount")

    # Addresses
    billing_address: str = Field(description="Billing address for payment")
    shipping_address: str = Field(description="Delivery address")
    billing_shipping_match: bool = Field(description="Whether billing and shipping addresses match")

    # Fraud indicators
    risk_score: float = Field(description="Calculated risk score from 0.0 to 1.0")
    is_first_order: bool = Field(description="Whether this is user's first order")
    expedited_shipping: bool = Field(description="Whether rush shipping was requested")
    high_value_order: bool = Field(description="Whether order exceeds $1000")
    flagged_reason: str | None = Field(
        description="Detailed reason if order was flagged for review"
    )
    customer_ip: str = Field(description="IP address of order placement")

    # Relationships
    user: User = Relationship(description="Customer who placed this order")
    products: list[Product] = Relationship(description="Products included in this order")


# Sample data
USERS = [
    {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "phone": "+1-555-0123",
        "created_at": datetime(2022, 1, 15),
        "last_login": datetime(2024, 1, 10),
        "is_verified": True,
        "total_spent": 2547.93,
        "billing_address": "123 Main St, Anytown, NY 12345",
        "shipping_address": "123 Main St, Anytown, NY 12345",
        "risk_score": 0.1,
        "account_status": "active",
    },
    {
        "id": 2,
        "username": "jane_smith",
        "email": "jane@example.com",
        "full_name": "Jane Smith",
        "phone": "+1-555-0124",
        "created_at": datetime(2021, 6, 20),
        "last_login": datetime(2024, 1, 12),
        "is_verified": True,
        "total_spent": 5832.17,
        "billing_address": "456 Oak Ave, Somewhere, CA 90210",
        "shipping_address": "456 Oak Ave, Somewhere, CA 90210",
        "risk_score": 0.05,
        "account_status": "active",
    },
    # Suspicious user - new account with risky behavior
    {
        "id": 3,
        "username": "quick_buyer_2024",
        "email": "tempmail@protonmail.com",
        "full_name": "Alex Johnson",
        "phone": "+1-555-9999",
        "created_at": datetime(2024, 1, 5),  # Very new account
        "last_login": datetime(2024, 1, 6),
        "is_verified": False,  # Unverified
        "total_spent": 4299.99,  # High spending for new account
        "billing_address": "789 Suspicious Lane, Newark, NJ 07101",
        "shipping_address": "555 Different St, Miami, FL 33101",  # Different from billing
        "risk_score": 0.85,
        "account_status": "flagged",
    },
]

PRODUCTS = [
    {
        "id": 101,
        "sku": "PHONE-001",
        "name": "Smartphone Pro",
        "description": "Latest model smartphone with 256GB storage",
        "category": "Electronics",
        "price": 999.99,
        "cost": 650.00,
        "stock": 45,
        "is_active": True,
        "created_at": datetime(2023, 9, 1),
        "fraud_risk": "high",  # Often purchased with stolen cards
    },
    {
        "id": 102,
        "sku": "LAPTOP-001",
        "name": "Business Laptop",
        "description": "Professional laptop with 16GB RAM",
        "category": "Electronics",
        "price": 1299.99,
        "cost": 900.00,
        "stock": 23,
        "is_active": True,
        "created_at": datetime(2023, 8, 15),
        "fraud_risk": "high",
    },
    {
        "id": 103,
        "sku": "HDPHONE-001",
        "name": "Wireless Headphones",
        "description": "Noise-canceling bluetooth headphones",
        "category": "Audio",
        "price": 299.99,
        "cost": 150.00,
        "stock": 67,
        "is_active": True,
        "created_at": datetime(2023, 7, 1),
        "fraud_risk": "medium",
    },
    {
        "id": 104,
        "sku": "SHOE-001",
        "name": "Running Shoes",
        "description": "Professional running shoes with advanced cushioning",
        "category": "Footwear",
        "price": 149.99,
        "cost": 75.00,
        "stock": 120,
        "is_active": True,
        "created_at": datetime(2023, 6, 1),
        "fraud_risk": "low",
    },
    {
        "id": 105,
        "sku": "GIFTCARD-500",
        "name": "$500 Gift Card",
        "description": "Digital gift card redeemable online",
        "category": "Gift Cards",
        "price": 500.00,
        "cost": 500.00,
        "stock": 999,
        "is_active": True,
        "created_at": datetime(2023, 1, 1),
        "fraud_risk": "high",  # Very high fraud risk
    },
]

ORDERS = [
    # Normal orders
    {
        "id": 1001,
        "order_number": "ORD-2023-1001",
        "user_id": 1,
        "created_at": datetime(2023, 10, 15, 14, 30),
        "status": "delivered",
        "payment_method": "credit_card",
        "total_amount": 329.98,
        "shipping_amount": 9.99,
        "tax_amount": 20.00,
        "billing_address": "123 Main St, Anytown, NY 12345",
        "shipping_address": "123 Main St, Anytown, NY 12345",
        "billing_shipping_match": True,
        "risk_score": 0.1,
        "is_first_order": False,
        "expedited_shipping": False,
        "high_value_order": False,
        "flagged_reason": None,
        "customer_ip": "192.168.1.100",
        "product_ids": [103],  # Just headphones
    },
    {
        "id": 1002,
        "order_number": "ORD-2023-1002",
        "user_id": 2,
        "created_at": datetime(2023, 11, 20, 11, 15),
        "status": "delivered",
        "payment_method": "paypal",
        "total_amount": 1449.98,
        "shipping_amount": 0.00,  # Free shipping
        "tax_amount": 100.00,
        "billing_address": "456 Oak Ave, Somewhere, CA 90210",
        "shipping_address": "456 Oak Ave, Somewhere, CA 90210",
        "billing_shipping_match": True,
        "risk_score": 0.05,
        "is_first_order": False,
        "expedited_shipping": False,
        "high_value_order": True,
        "flagged_reason": None,
        "customer_ip": "10.0.0.50",
        "product_ids": [102, 104],  # Laptop and shoes
    },
    # Fraudulent order
    {
        "id": 1003,
        "order_number": "ORD-2024-1003",
        "user_id": 3,  # Suspicious user
        "created_at": datetime(2024, 1, 6, 2, 45),  # 2:45 AM
        "status": "flagged",
        "payment_method": "credit_card",
        "total_amount": 4299.99,
        "shipping_amount": 99.99,  # Expensive rush shipping
        "tax_amount": 0.00,  # No tax calculated (suspicious)
        "billing_address": "789 Suspicious Lane, Newark, NJ 07101",
        "shipping_address": "555 Different St, Miami, FL 33101",
        "billing_shipping_match": False,
        "risk_score": 0.95,
        "is_first_order": True,
        "expedited_shipping": True,
        "high_value_order": True,
        "flagged_reason": (
            "Multiple risk factors: New unverified account, high-value first order, "
            "mismatched addresses, overnight shipping to different state, order placed "
            "at unusual hour, multiple high-risk items including gift cards"
        ),
        "customer_ip": "185.220.101.45",  # TOR exit node
        "product_ids": [101, 102, 105, 105],  # Phone, laptop, 2x gift cards
    },
    # More normal orders
    {
        "id": 1004,
        "order_number": "ORD-2024-1004",
        "user_id": 1,
        "created_at": datetime(2024, 1, 8, 15, 20),
        "status": "shipped",
        "payment_method": "credit_card",
        "total_amount": 169.98,
        "shipping_amount": 5.99,
        "tax_amount": 14.00,
        "billing_address": "123 Main St, Anytown, NY 12345",
        "shipping_address": "123 Main St, Anytown, NY 12345",
        "billing_shipping_match": True,
        "risk_score": 0.08,
        "is_first_order": False,
        "expedited_shipping": False,
        "high_value_order": False,
        "flagged_reason": None,
        "customer_ip": "192.168.1.100",
        "product_ids": [104],  # Running shoes
    },
]


# Define relationship resolvers
@User.orders.resolver
async def by_user_id(user_id: int) -> list["Order"]:
    """Get all orders for a specific user.

    Returns a list of orders placed by the user, including
    cancelled and flagged orders. Orders are returned in
    chronological order.

    Args:
        user_id: The ID of the user whose orders to retrieve

    Returns:
        List of Order objects for the specified user
    """
    user_orders = []
    for order_data in ORDERS:
        if order_data["user_id"] == user_id:
            # Create Order object without product_ids
            order_dict = {k: v for k, v in order_data.items() if k != "product_ids"}
            user_orders.append(Order(**order_dict))
    return user_orders


@Order.user.resolver
async def by_order_id(order_id: int) -> "User":
    """Get the user who placed a specific order.

    Returns the complete user object for the customer who
    placed the order. If the order doesn't exist, returns
    a placeholder user.

    Args:
        order_id: The ID of the order

    Returns:
        User object who placed the order
    """
    # Find the order
    order = next((o for o in ORDERS if o["id"] == order_id), None)
    if not order:
        return User(
            id=-1,
            username="unknown",
            email="unknown@example.com",
            full_name="Unknown User",
            phone="+1-000-0000",
            created_at=datetime.now(),
            last_login=datetime.now(),
            is_verified=False,
            total_spent=0.0,
            billing_address="Unknown",
            shipping_address="Unknown",
            risk_score=0.0,
            account_status="inactive",
        )

    # Find the user
    user_data = next((u for u in USERS if u["id"] == order["user_id"]), None)
    if not user_data:
        return User(
            id=-1,
            username="deleted_user",
            email="deleted@example.com",
            full_name="Deleted User",
            phone="+1-000-0000",
            created_at=datetime.now(),
            last_login=datetime.now(),
            is_verified=False,
            total_spent=0.0,
            billing_address="Unknown",
            shipping_address="Unknown",
            risk_score=0.0,
            account_status="deleted",
        )

    return User(**user_data)


@Order.products.resolver
async def by_order_id_products(order_id: int) -> list[Product]:
    """Get all products included in a specific order.

    Returns the list of products that were purchased in the order.
    Products are returned even if they are no longer active in
    the catalog.

    Args:
        order_id: The ID of the order

    Returns:
        List of Product objects in the order
    """
    # Find the order
    order = next((o for o in ORDERS if o["id"] == order_id), None)
    if not order:
        return []

    # Get all products in the order
    order_products = []
    for product_id in order.get("product_ids", []):
        product_data = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if product_data:
            order_products.append(Product(**product_data))

    return order_products


# Define root resources
@app.retrieve
async def list_users() -> list[User]:
    """List all users in the system.

    Returns all user accounts including active, suspended, and
    flagged users. Use this to get an overview of all customers
    or to find specific users for further investigation.

    Returns:
        List of all User objects in the system
    """
    return [User(**user_data) for user_data in USERS]


@app.retrieve
async def get_user(user_id: int) -> User:
    """Get a specific user by ID.

    Retrieves complete user information including risk scores
    and account status. Use this to investigate specific users
    or check user details.

    Args:
        user_id: The unique identifier of the user

    Returns:
        User object if found, otherwise a not-found user object
    """
    user_data = next((u for u in USERS if u["id"] == user_id), None)
    if not user_data:
        return User(
            id=-1,
            username="not_found",
            email="notfound@example.com",
            full_name="User Not Found",
            phone="+1-000-0000",
            created_at=datetime.now(),
            last_login=datetime.now(),
            is_verified=False,
            total_spent=0.0,
            billing_address="N/A",
            shipping_address="N/A",
            risk_score=0.0,
            account_status="not_found",
        )
    return User(**user_data)


@app.retrieve
async def list_products() -> list[Product]:
    """List all products in the catalog.

    Returns all products including their fraud risk levels.
    Products marked as high fraud risk are frequently used
    in fraudulent transactions.

    Returns:
        List of all Product objects in the catalog
    """
    return [Product(**product_data) for product_data in PRODUCTS]


@app.retrieve
async def list_orders(
    status: str | None = None, page: int = 1, page_size: int = 10
) -> PageResult[Order]:
    """List orders, optionally filtered by status.

    Returns orders from the system. Can be filtered by status
    to find specific types of orders (e.g., 'flagged' for
    potentially fraudulent orders).

    Args:
        status: Optional status filter (delivered, shipped, pending, cancelled, flagged)
        page: Page number (1-indexed)
        page_size: Number of orders per page

    Returns:
        PageResult with Order objects matching the criteria
    """
    # Filter by status first
    filtered_orders = []
    for order_data in ORDERS:
        if status is None or order_data["status"] == status:
            order_dict = {k: v for k, v in order_data.items() if k != "product_ids"}
            filtered_orders.append(Order(**order_dict))

    # Sort by creation date (most recent first)
    filtered_orders.sort(key=lambda x: x.created_at, reverse=True)

    # Apply pagination
    total_items = len(filtered_orders)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_orders = filtered_orders[start_idx:end_idx]

    return PageResult.create(
        items=page_orders,
        page=page,
        page_size=page_size,
        has_next=end_idx < total_items,
        total_items=total_items,
    )


# Run the server
if __name__ == "__main__":
    print("Starting E-Commerce Shop API...")
    app.run()
