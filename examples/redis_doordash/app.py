"""Redis DoorDash Support Agent Example for EnrichMCP.

This example demonstrates a comprehensive DoorDash support system with:
- Complete ecosystem entities (customers, orders, dashers, restaurants, tickets)
- Vector-indexed policies for intelligent support assistance
- Rich relationships for complex investigations
- Realistic sample data covering common support scenarios
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src directory to path for imports when running as standalone script
if __name__ == "__main__":
    src_path = Path(__file__).resolve().parents[2] / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

# Import the Redis integration
from enrichmcp.redis import EnrichMCP, EnrichModel, Field, Relationship

# Create Redis-enabled app
app = EnrichMCP(
    title="DoorDash Support Agent API",
    instructions=(
        "Comprehensive DoorDash support system with vector-indexed policies "
        "and intelligent assistance."
    ),
    redis_url="redis://localhost:6379",
)


# ============================================================================
# CORE BUSINESS ENTITIES
# ============================================================================


@app.entity()
class Customer(EnrichModel):
    """DoorDash customer account with comprehensive profile."""

    id: int = Field(description="Unique customer ID", index="primary")

    # Searchable fields
    email: str = Field(description="Customer email address", index="text")
    phone: str = Field(description="Customer phone number", index="text")
    full_name: str = Field(description="Customer full name", index="text")
    account_status: str = Field(description="active, suspended, banned, flagged", index="tag")
    customer_tier: str = Field(description="regular, premium, dashpass", index="tag")
    city: str = Field(description="Primary city for orders", index="tag")

    # Regular fields
    created_at: datetime = Field(description="Account creation timestamp")
    total_orders: int = Field(description="Total number of orders placed")
    lifetime_value: float = Field(description="Total amount spent by customer")
    preferred_address: str = Field(description="Customer's preferred delivery address")
    payment_methods_ids: list[int] = Field(
        description="Available payment method IDs", default=..., default_factory=list
    )
    last_order_date: datetime | None = Field(description="Date of most recent order", default=None)

    # Note: Reverse relationships (Customer -> Orders) are not supported in Redis version
    # Use forward relationships from Order -> Customer instead via get_order_customer tool


@app.entity()
class Restaurant(EnrichModel):
    """Restaurant/merchant information and performance metrics."""

    id: int = Field(description="Unique restaurant ID", index="primary")

    # Searchable fields
    name: str = Field(description="Restaurant name", index="text")
    cuisine_type: str = Field(description="Cuisine category", index="tag")
    rating: float = Field(description="Average customer rating", index="numeric")
    status: str = Field(description="active, inactive, suspended, closed", index="tag")
    city: str = Field(description="Restaurant city location", index="tag")

    # Regular fields
    address: str = Field(description="Restaurant physical address")
    phone: str = Field(description="Restaurant contact phone number")
    hours: dict[str, str] = Field(description="Operating hours by day of week")
    delivery_fee: float = Field(description="Base delivery fee charged")
    minimum_order: float = Field(description="Minimum order amount required")
    avg_prep_time: int = Field(description="Average food preparation time in minutes")
    total_orders: int = Field(description="Total orders fulfilled by restaurant")

    # Note: Reverse relationships (Restaurant -> Orders) are not supported in Redis version
    # Use forward relationships from Order -> Restaurant instead via get_order_restaurant tool


@app.entity()
class Dasher(EnrichModel):
    """DoorDash delivery driver profile and performance."""

    id: int = Field(description="Unique dasher ID", index="primary")

    # Searchable fields
    email: str = Field(description="Dasher email address", index="text")
    phone: str = Field(description="Dasher phone number", index="text")
    full_name: str = Field(description="Dasher full name", index="text")
    status: str = Field(description="active, inactive, suspended, deactivated", index="tag")
    city: str = Field(description="Primary delivery city", index="tag")
    rating: float = Field(description="Average customer rating", index="numeric")
    completion_rate: float = Field(description="Order completion rate percentage", index="numeric")

    # Regular fields
    created_at: datetime = Field(description="Dasher account creation date")
    vehicle_type: str = Field(description="Delivery vehicle type: car, bike, scooter, walking")
    background_check_status: str = Field(description="Background check status")
    total_deliveries: int = Field(description="Total number of deliveries completed")
    earnings_last_30_days: float = Field(description="Earnings in the last 30 days")
    last_active: datetime = Field(description="Last time dasher was active")

    # Note: Reverse relationships (Dasher -> Orders) are not supported in Redis version
    # Use forward relationships from Order -> Dasher instead via get_order_dasher tool


@app.entity()
class Order(EnrichModel):
    """DoorDash order with complete lifecycle tracking."""

    id: int = Field(description="Unique order ID", index="primary")

    # Searchable fields
    customer_id: int = Field(description="Customer ID who placed order", index="tag")
    restaurant_id: int = Field(description="Restaurant fulfilling order", index="tag")
    dasher_id: int = Field(description="Dasher delivering order", index="tag")
    status: str = Field(description="Order status", index="tag")
    order_total: float = Field(description="Total order amount", index="numeric")
    created_date: str = Field(description="Order date YYYY-MM-DD", index="tag")

    # Regular fields
    order_number: str = Field(description="Human-readable order number")
    created_at: datetime = Field(description="Order creation timestamp")
    estimated_delivery: datetime = Field(description="Estimated delivery time")
    actual_delivery: datetime | None = Field(description="Actual delivery time", default=None)
    items: list[dict[str, Any]] = Field(
        description="Order items with details", default=..., default_factory=list
    )
    delivery_address: str = Field(description="Customer delivery address")
    special_instructions: str = Field(description="Special delivery instructions")
    tip_amount: float = Field(description="Customer tip amount")
    delivery_fee: float = Field(description="Delivery service fee")
    taxes: float = Field(description="Tax amount")
    refund_amount: float = Field(description="Total refund amount", default=0.0)

    # Relationships
    customer: Customer = Relationship(
        description="Customer who placed order", source_field="customer_id"
    )
    restaurant: Restaurant = Relationship(
        description="Restaurant fulfilling order", source_field="restaurant_id"
    )
    dasher: Dasher = Relationship(description="Dasher delivering order", source_field="dasher_id")
    # Note: Reverse relationships (Order -> Tickets/Refunds) are not supported in Redis version
    # Use forward relationships from SupportTicket -> Order and Refund -> Order instead


# ============================================================================
# SUPPORT SYSTEM ENTITIES
# ============================================================================


@app.entity()
class Agent(EnrichModel):
    """Support agent profile and specializations."""

    id: int = Field(description="Unique agent ID", index="primary")

    # Searchable fields
    email: str = Field(description="Agent email address", index="text")
    full_name: str = Field(description="Agent full name", index="text")
    team: str = Field(description="Support team name", index="tag")
    tier: str = Field(description="tier1, tier2, supervisor, specialist", index="tag")
    status: str = Field(description="active, offline, break, training", index="tag")

    # Regular fields
    employee_id: str = Field(description="Internal employee identifier")
    hire_date: datetime = Field(description="Agent hire date")
    specializations: list[str] = Field(
        description="Agent specializations: refunds, technical, escalations",
        default=...,
        default_factory=list,
    )
    languages: list[str] = Field(
        description="Languages spoken by agent", default=..., default_factory=list
    )
    current_ticket_count: int = Field(description="Current number of assigned tickets")
    avg_resolution_time: float = Field(description="Average ticket resolution time in minutes")
    customer_satisfaction: float = Field(description="Average customer satisfaction rating")


@app.entity()
class SupportTicket(EnrichModel):
    """Customer support ticket with categorization and tracking."""

    id: int = Field(description="Unique support ticket ID", index="primary")

    # Searchable fields
    customer_id: int = Field(description="Customer who created ticket", index="tag")
    order_id: int = Field(description="Related order ID if applicable", index="tag")
    restaurant_id: int = Field(description="Related restaurant ID if applicable", index="tag")
    dasher_id: int = Field(description="Related dasher ID if applicable", index="tag")
    category: str = Field(description="Issue category", index="tag")
    priority: str = Field(description="low, medium, high, urgent", index="tag")
    status: str = Field(description="open, in_progress, resolved, closed", index="tag")
    agent_id: int = Field(description="Assigned agent ID", index="tag")

    # Regular fields
    subject: str = Field(description="Ticket subject line")
    description: str = Field(description="Detailed ticket description")
    created_at: datetime = Field(description="Ticket creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    resolution: str | None = Field(description="Ticket resolution details", default=None)
    customer_satisfaction: int | None = Field(
        description="Customer satisfaction rating 1-5", default=None
    )
    escalated: bool = Field(description="Whether ticket has been escalated", default=False)

    # Relationships
    customer: Customer = Relationship(
        description="Customer who created ticket", source_field="customer_id"
    )
    order: Order = Relationship(description="Related order if applicable", source_field="order_id")
    restaurant: Restaurant = Relationship(
        description="Related restaurant if applicable", source_field="restaurant_id"
    )
    dasher: Dasher = Relationship(
        description="Related dasher if applicable", source_field="dasher_id"
    )
    agent: Agent = Relationship(description="Assigned support agent", source_field="agent_id")
    # Note: Reverse relationships (SupportTicket -> Escalations/Refunds) are not supported
    # in Redis version
    # Use forward relationships from Escalation -> SupportTicket and Refund -> SupportTicket instead


@app.entity()
class Policy(EnrichModel):
    """Support policy with vector search capabilities for intelligent assistance."""

    id: int = Field(description="Unique policy ID", index="primary")

    # Searchable fields
    category: str = Field(description="Policy category", index="tag")
    subcategory: str = Field(description="Policy subcategory", index="tag")
    priority: str = Field(description="low, medium, high, critical", index="tag")
    active: bool = Field(description="Whether policy is currently active", index="tag")

    # Vector search field for semantic similarity
    content_embedding: list[float] = Field(
        description="Vector embedding of policy content for semantic search",
        index="vector",
        vector_dim=1536,  # OpenAI embedding dimension
    )

    # Regular fields
    title: str = Field(description="Policy title")
    content: str = Field(description="Full policy text content")
    examples: list[str] = Field(
        description="Example scenarios for policy", default=..., default_factory=list
    )
    exceptions: list[str] = Field(
        description="Policy exceptions and edge cases", default=..., default_factory=list
    )
    created_at: datetime = Field(description="Policy creation timestamp")
    updated_at: datetime = Field(description="Last policy update timestamp")
    version: str = Field(description="Policy version number")
    approved_by: str = Field(description="Policy approver name")
    usage_count: int = Field(description="Number of times policy was referenced", default=0)


# ============================================================================
# ADDITIONAL SUPPORT ENTITIES
# ============================================================================


@app.entity()
class Refund(EnrichModel):
    """Refund and credit transactions."""

    id: int = Field(description="Unique refund ID", index="primary")

    # Searchable fields
    customer_id: int = Field(description="Customer receiving refund", index="tag")
    order_id: int = Field(description="Related order ID", index="tag")
    ticket_id: int = Field(description="Related support ticket", index="tag")
    refund_type: str = Field(description="full, partial, credit, promotional", index="tag")
    reason: str = Field(description="Refund reason category", index="tag")
    amount: float = Field(description="Refund amount in dollars", index="numeric")
    processed_date: str = Field(description="Date processed YYYY-MM-DD", index="tag")

    # Regular fields
    created_at: datetime = Field(description="Refund request creation timestamp")
    processed_at: datetime | None = Field(description="Refund processing timestamp", default=None)
    status: str = Field(description="Refund status: pending, approved, processed, failed")
    agent_id: int = Field(description="Agent who processed the refund")
    notes: str = Field(description="Internal refund processing notes")
    payment_method: str = Field(
        description="Refund method: original_payment, doordash_credit, bank_transfer"
    )

    # Relationships
    customer: Customer = Relationship(
        description="Customer receiving refund", source_field="customer_id"
    )
    order: Order = Relationship(description="Related order", source_field="order_id")
    ticket: SupportTicket = Relationship(
        description="Related support ticket", source_field="ticket_id"
    )


@app.entity()
class Escalation(EnrichModel):
    """Ticket escalation tracking and management."""

    id: int = Field(description="Unique escalation ID", index="primary")

    # Searchable fields
    ticket_id: int = Field(description="Original ticket ID", index="tag")
    from_agent_id: int = Field(description="Agent who escalated", index="tag")
    to_agent_id: int = Field(description="Agent receiving escalation", index="tag")
    escalation_type: str = Field(
        description="supervisor, specialist, legal, executive", index="tag"
    )
    priority: str = Field(description="normal, urgent, emergency", index="tag")

    # Regular fields
    reason: str = Field(description="Reason for escalation")
    notes: str = Field(description="Escalation notes and context")
    created_at: datetime = Field(description="Escalation creation timestamp")
    resolved_at: datetime | None = Field(
        description="Escalation resolution timestamp", default=None
    )
    resolution: str | None = Field(description="Escalation resolution details", default=None)

    # Relationships
    ticket: SupportTicket = Relationship(
        description="Original support ticket", source_field="ticket_id"
    )
    from_agent: Agent = Relationship(
        description="Agent who escalated", source_field="from_agent_id"
    )
    to_agent: Agent = Relationship(
        description="Agent receiving escalation", source_field="to_agent_id"
    )


@app.entity()
class Incident(EnrichModel):
    """System incidents affecting service delivery."""

    id: int = Field(description="Unique incident ID", index="primary")

    # Searchable fields
    incident_type: str = Field(
        description="outage, weather, restaurant_issue, dasher_shortage", index="tag"
    )
    severity: str = Field(description="low, medium, high, critical", index="tag")
    status: str = Field(description="investigating, identified, resolved", index="tag")
    affected_region: str = Field(description="Geographic region affected", index="tag")
    start_date: str = Field(description="Incident start date YYYY-MM-DD", index="tag")

    # Regular fields
    title: str = Field(description="Incident title")
    description: str = Field(description="Detailed incident description")
    started_at: datetime = Field(description="Incident start timestamp")
    resolved_at: datetime | None = Field(description="Incident resolution timestamp", default=None)
    affected_customers: int = Field(description="Number of customers affected")
    affected_orders: list[int] = Field(
        description="List of affected order IDs", default=..., default_factory=list
    )
    root_cause: str | None = Field(description="Identified root cause", default=None)
    resolution_notes: str | None = Field(
        description="Resolution notes and actions taken", default=None
    )


# ============================================================================
# SAMPLE DATA
# ============================================================================

# Sample customers with diverse profiles
SAMPLE_CUSTOMERS = [
    {
        "id": 1,
        "email": "john.doe@email.com",
        "phone": "+1-555-0123",
        "full_name": "John Doe",
        "account_status": "active",
        "customer_tier": "dashpass",
        "city": "San Francisco",
        "created_at": datetime(2022, 3, 15),
        "total_orders": 127,
        "lifetime_value": 2847.93,
        "preferred_address": "123 Market St, San Francisco, CA 94105",
        "payment_methods_ids": [1, 2],
        "last_order_date": datetime(2024, 12, 10),
    },
    {
        "id": 2,
        "email": "sarah.wilson@gmail.com",
        "phone": "+1-555-0124",
        "full_name": "Sarah Wilson",
        "account_status": "active",
        "customer_tier": "premium",
        "city": "New York",
        "created_at": datetime(2021, 8, 22),
        "total_orders": 203,
        "lifetime_value": 4532.17,
        "preferred_address": "456 Broadway, New York, NY 10013",
        "payment_methods_ids": [3],
        "last_order_date": datetime(2024, 12, 11),
    },
    {
        "id": 3,
        "email": "temp.user@protonmail.com",
        "phone": "+1-555-9999",
        "full_name": "Alex Johnson",
        "account_status": "flagged",
        "customer_tier": "regular",
        "city": "Newark",
        "created_at": datetime(2024, 11, 5),
        "total_orders": 8,
        "lifetime_value": 1299.99,
        "preferred_address": "789 Suspicious Lane, Newark, NJ 07101",
        "payment_methods_ids": [4],
        "last_order_date": datetime(2024, 12, 8),
    },
    {
        "id": 4,
        "email": "maria.garcia@yahoo.com",
        "phone": "+1-555-0125",
        "full_name": "Maria Garcia",
        "account_status": "active",
        "customer_tier": "regular",
        "city": "Los Angeles",
        "created_at": datetime(2023, 1, 10),
        "total_orders": 45,
        "lifetime_value": 892.45,
        "preferred_address": "321 Sunset Blvd, Los Angeles, CA 90028",
        "payment_methods_ids": [5],
        "last_order_date": datetime(2024, 12, 9),
    },
    {
        "id": 5,
        "email": "david.chen@outlook.com",
        "phone": "+1-555-0126",
        "full_name": "David Chen",
        "account_status": "suspended",
        "customer_tier": "regular",
        "city": "Chicago",
        "created_at": datetime(2023, 6, 18),
        "total_orders": 23,
        "lifetime_value": 456.78,
        "preferred_address": "654 Michigan Ave, Chicago, IL 60611",
        "payment_methods_ids": [6],
        "last_order_date": datetime(2024, 11, 15),
    },
]

# Sample restaurants
SAMPLE_RESTAURANTS = [
    {
        "id": 101,
        "name": "Tony's Pizza Palace",
        "cuisine_type": "Italian",
        "rating": 4.2,
        "status": "active",
        "city": "San Francisco",
        "address": "789 Columbus Ave, San Francisco, CA 94133",
        "phone": "+1-415-555-0101",
        "hours": {"mon-fri": "11:00-23:00", "sat-sun": "12:00-24:00"},
        "delivery_fee": 2.99,
        "minimum_order": 15.00,
        "avg_prep_time": 25,
        "total_orders": 1247,
    },
    {
        "id": 102,
        "name": "Burger Junction",
        "cuisine_type": "American",
        "rating": 3.8,
        "status": "active",
        "city": "New York",
        "address": "234 5th Ave, New York, NY 10001",
        "phone": "+1-212-555-0102",
        "hours": {"daily": "10:00-22:00"},
        "delivery_fee": 1.99,
        "minimum_order": 12.00,
        "avg_prep_time": 15,
        "total_orders": 2156,
    },
    {
        "id": 103,
        "name": "Sushi Zen",
        "cuisine_type": "Japanese",
        "rating": 4.7,
        "status": "active",
        "city": "Los Angeles",
        "address": "567 Melrose Ave, Los Angeles, CA 90038",
        "phone": "+1-323-555-0103",
        "hours": {"tue-sun": "17:00-22:00"},
        "delivery_fee": 3.99,
        "minimum_order": 25.00,
        "avg_prep_time": 35,
        "total_orders": 892,
    },
    {
        "id": 104,
        "name": "Slow Kitchen",
        "cuisine_type": "American",
        "rating": 2.1,
        "status": "suspended",
        "city": "Chicago",
        "address": "890 State St, Chicago, IL 60605",
        "phone": "+1-312-555-0104",
        "hours": {"daily": "11:00-21:00"},
        "delivery_fee": 2.49,
        "minimum_order": 20.00,
        "avg_prep_time": 65,  # Very slow
        "total_orders": 234,
    },
]

# Sample dashers
SAMPLE_DASHERS = [
    {
        "id": 201,
        "email": "mike.driver@doordash.com",
        "phone": "+1-555-0201",
        "full_name": "Mike Rodriguez",
        "status": "active",
        "city": "San Francisco",
        "rating": 4.8,
        "completion_rate": 96.5,
        "created_at": datetime(2023, 2, 1),
        "vehicle_type": "car",
        "background_check_status": "approved",
        "total_deliveries": 1456,
        "earnings_last_30_days": 2847.50,
        "last_active": datetime(2024, 12, 12, 14, 30),
    },
    {
        "id": 202,
        "email": "jenny.bike@doordash.com",
        "phone": "+1-555-0202",
        "full_name": "Jenny Park",
        "status": "active",
        "city": "New York",
        "rating": 4.9,
        "completion_rate": 98.2,
        "created_at": datetime(2022, 9, 15),
        "vehicle_type": "bike",
        "background_check_status": "approved",
        "total_deliveries": 2103,
        "earnings_last_30_days": 3124.75,
        "last_active": datetime(2024, 12, 12, 15, 45),
    },
    {
        "id": 203,
        "email": "problem.dasher@doordash.com",
        "phone": "+1-555-0203",
        "full_name": "Rick Thompson",
        "status": "suspended",
        "city": "Los Angeles",
        "rating": 3.2,
        "completion_rate": 78.5,
        "created_at": datetime(2024, 5, 10),
        "vehicle_type": "car",
        "background_check_status": "approved",
        "total_deliveries": 89,
        "earnings_last_30_days": 234.50,
        "last_active": datetime(2024, 11, 28, 19, 15),
    },
]

# Sample agents
SAMPLE_AGENTS = [
    {
        "id": 301,
        "email": "lisa.support@doordash.com",
        "full_name": "Lisa Chen",
        "team": "general_support",
        "tier": "tier1",
        "status": "active",
        "employee_id": "DD-301",
        "hire_date": datetime(2023, 4, 1),
        "specializations": ["refunds", "delivery_issues"],
        "languages": ["english", "spanish"],
        "current_ticket_count": 12,
        "avg_resolution_time": 18.5,
        "customer_satisfaction": 4.3,
    },
    {
        "id": 302,
        "email": "james.escalation@doordash.com",
        "full_name": "James Wilson",
        "team": "escalations",
        "tier": "supervisor",
        "status": "active",
        "employee_id": "DD-302",
        "hire_date": datetime(2022, 1, 15),
        "specializations": ["escalations", "legal", "complex_issues"],
        "languages": ["english"],
        "current_ticket_count": 8,
        "avg_resolution_time": 45.2,
        "customer_satisfaction": 4.7,
    },
    {
        "id": 303,
        "email": "anna.fraud@doordash.com",
        "full_name": "Anna Martinez",
        "team": "quality_assurance",
        "tier": "specialist",
        "status": "active",
        "employee_id": "DD-303",
        "hire_date": datetime(2023, 8, 20),
        "specializations": ["quality_control", "restaurant_relations", "investigations"],
        "languages": ["english", "spanish", "portuguese"],
        "current_ticket_count": 6,
        "avg_resolution_time": 72.8,
        "customer_satisfaction": 4.5,
    },
]

# Sample orders with realistic scenarios
SAMPLE_ORDERS = [
    {
        "id": 1001,
        "customer_id": 1,
        "restaurant_id": 101,
        "dasher_id": 201,
        "status": "delivered",
        "order_total": 45.99,
        "created_date": "2024-12-10",
        "order_number": "DD-2024-1001",
        "created_at": datetime(2024, 12, 10, 18, 30),
        "estimated_delivery": datetime(2024, 12, 10, 19, 15),
        "actual_delivery": datetime(2024, 12, 10, 19, 12),
        "items": [
            {"name": "Margherita Pizza", "quantity": 1, "price": 18.99},
            {"name": "Caesar Salad", "quantity": 1, "price": 12.99},
            {"name": "Garlic Bread", "quantity": 2, "price": 6.99},
        ],
        "delivery_address": "123 Market St, San Francisco, CA 94105",
        "special_instructions": "Ring doorbell twice",
        "tip_amount": 8.00,
        "delivery_fee": 2.99,
        "taxes": 3.68,
        "refund_amount": 0.0,
    },
    {
        "id": 1002,
        "customer_id": 2,
        "restaurant_id": 102,
        "dasher_id": 202,
        "status": "delivered",
        "order_total": 28.47,
        "created_date": "2024-12-11",
        "order_number": "DD-2024-1002",
        "created_at": datetime(2024, 12, 11, 12, 15),
        "estimated_delivery": datetime(2024, 12, 11, 12, 45),
        "actual_delivery": datetime(2024, 12, 11, 13, 20),  # Late delivery
        "items": [
            {"name": "Classic Burger", "quantity": 1, "price": 14.99},
            {"name": "French Fries", "quantity": 1, "price": 4.99},
            {"name": "Coke", "quantity": 1, "price": 2.99},
        ],
        "delivery_address": "456 Broadway, New York, NY 10013",
        "special_instructions": "Leave at door",
        "tip_amount": 4.00,
        "delivery_fee": 1.99,
        "taxes": 2.25,
        "refund_amount": 0.0,
    },
    {
        "id": 1003,
        "customer_id": 3,
        "restaurant_id": 103,
        "dasher_id": 203,
        "status": "cancelled",
        "order_total": 89.95,
        "created_date": "2024-12-08",
        "order_number": "DD-2024-1003",
        "created_at": datetime(2024, 12, 8, 19, 45),
        "estimated_delivery": datetime(2024, 12, 8, 20, 45),
        "actual_delivery": None,
        "items": [
            {"name": "Sashimi Platter", "quantity": 1, "price": 45.99},
            {"name": "Dragon Roll", "quantity": 2, "price": 16.99},
            {"name": "Miso Soup", "quantity": 2, "price": 4.99},
        ],
        "delivery_address": "789 Suspicious Lane, Newark, NJ 07101",
        "special_instructions": "Call when arriving",
        "tip_amount": 15.00,
        "delivery_fee": 3.99,
        "taxes": 7.18,
        "refund_amount": 89.95,
    },
    {
        "id": 1004,
        "customer_id": 4,
        "restaurant_id": 103,
        "dasher_id": 202,
        "status": "delivered",
        "order_total": 67.43,
        "created_date": "2024-12-09",
        "order_number": "DD-2024-1004",
        "created_at": datetime(2024, 12, 9, 20, 10),
        "estimated_delivery": datetime(2024, 12, 9, 21, 15),
        "actual_delivery": datetime(2024, 12, 9, 21, 45),  # Slightly late
        "items": [
            {"name": "Chirashi Bowl", "quantity": 1, "price": 32.99},
            {"name": "California Roll", "quantity": 2, "price": 12.99},
            {"name": "Edamame", "quantity": 1, "price": 5.99},
        ],
        "delivery_address": "321 Sunset Blvd, Los Angeles, CA 90028",
        "special_instructions": "Apartment 4B",
        "tip_amount": 10.00,
        "delivery_fee": 3.99,
        "taxes": 5.39,
        "refund_amount": 0.0,
    },
    {
        "id": 1005,
        "customer_id": 5,
        "restaurant_id": 104,
        "dasher_id": 203,
        "status": "cancelled",
        "order_total": 34.56,
        "created_date": "2024-11-15",
        "order_number": "DD-2024-1005",
        "created_at": datetime(2024, 11, 15, 19, 00),
        "estimated_delivery": datetime(2024, 11, 15, 20, 30),
        "actual_delivery": None,
        "items": [
            {"name": "Chicken Sandwich", "quantity": 1, "price": 13.99},
            {"name": "Onion Rings", "quantity": 1, "price": 6.99},
            {"name": "Milkshake", "quantity": 1, "price": 7.99},
        ],
        "delivery_address": "654 Michigan Ave, Chicago, IL 60611",
        "special_instructions": "Buzz apartment 12",
        "tip_amount": 3.00,
        "delivery_fee": 2.49,
        "taxes": 2.76,
        "refund_amount": 34.56,
    },
    {
        "id": 1006,
        "customer_id": 1,
        "restaurant_id": 102,
        "dasher_id": 201,
        "status": "in_transit",
        "order_total": 23.47,
        "created_date": "2024-12-12",
        "order_number": "DD-2024-1006",
        "created_at": datetime(2024, 12, 12, 13, 45),
        "estimated_delivery": datetime(2024, 12, 12, 14, 30),
        "actual_delivery": None,
        "items": [
            {"name": "Fish Sandwich", "quantity": 1, "price": 11.99},
            {"name": "Sweet Potato Fries", "quantity": 1, "price": 5.99},
        ],
        "delivery_address": "123 Market St, San Francisco, CA 94105",
        "special_instructions": "Ring doorbell twice",
        "tip_amount": 3.50,
        "delivery_fee": 1.99,
        "taxes": 1.87,
        "refund_amount": 0.0,
    },
    {
        "id": 1007,
        "customer_id": 2,
        "restaurant_id": 101,
        "dasher_id": 202,
        "status": "preparing",
        "order_total": 52.34,
        "created_date": "2024-12-12",
        "order_number": "DD-2024-1007",
        "created_at": datetime(2024, 12, 12, 14, 15),
        "estimated_delivery": datetime(2024, 12, 12, 15, 30),
        "actual_delivery": None,
        "items": [
            {"name": "Pepperoni Pizza", "quantity": 1, "price": 21.99},
            {"name": "Buffalo Wings", "quantity": 12, "price": 16.99},
            {"name": "Tiramisu", "quantity": 1, "price": 7.99},
        ],
        "delivery_address": "456 Broadway, New York, NY 10013",
        "special_instructions": "Extra napkins please",
        "tip_amount": 7.00,
        "delivery_fee": 2.99,
        "taxes": 4.17,
        "refund_amount": 0.0,
    },
    {
        "id": 1008,
        "customer_id": 4,
        "restaurant_id": 104,
        "dasher_id": 203,
        "status": "delivered",
        "order_total": 41.23,
        "created_date": "2024-12-11",
        "order_number": "DD-2024-1008",
        "created_at": datetime(2024, 12, 11, 18, 00),
        "estimated_delivery": datetime(2024, 12, 11, 19, 30),
        "actual_delivery": datetime(2024, 12, 11, 20, 45),  # Very late
        "items": [
            {"name": "BBQ Ribs", "quantity": 1, "price": 24.99},
            {"name": "Mac and Cheese", "quantity": 1, "price": 8.99},
        ],
        "delivery_address": "321 Sunset Blvd, Los Angeles, CA 90028",
        "special_instructions": "Call when arriving",
        "tip_amount": 5.00,
        "delivery_fee": 2.49,
        "taxes": 3.29,
        "refund_amount": 0.0,
    },
]

# Sample support tickets covering common scenarios
SAMPLE_TICKETS = [
    {
        "id": 2001,
        "customer_id": 2,
        "order_id": 1002,
        "restaurant_id": 102,
        "dasher_id": 202,
        "category": "delivery_issue",
        "priority": "medium",
        "status": "resolved",
        "agent_id": 301,
        "subject": "Order delivered 35 minutes late",
        "description": (
            "My order was supposed to arrive at 12:45 PM but didn't arrive until 1:20 PM. "
            "I was waiting for lunch and this made me late for my meeting."
        ),
        "created_at": datetime(2024, 12, 11, 13, 25),
        "updated_at": datetime(2024, 12, 11, 14, 10),
        "resolution": (
            "Apologized for delay, issued $5 DoorDash credit for future order. "
            "Delay was due to restaurant prep time."
        ),
        "customer_satisfaction": 4,
        "escalated": False,
    },
    {
        "id": 2002,
        "customer_id": 3,
        "order_id": 1003,
        "restaurant_id": 103,
        "dasher_id": 203,
        "category": "missing_order",
        "priority": "high",
        "status": "resolved",
        "agent_id": 302,
        "subject": "Order never delivered - dasher marked as delivered",
        "description": (
            "I ordered sushi for $89.95 and the dasher marked it as delivered "
            "but I never received it. "
            ""
            "I was home the whole time and no one came to my door."
        ),
        "created_at": datetime(2024, 12, 8, 21, 15),
        "updated_at": datetime(2024, 12, 8, 22, 30),
        "resolution": (
            "Investigated with dasher and GPS data. Dasher admitted to keeping order. "
            "Full refund issued, dasher suspended."
        ),
        "customer_satisfaction": 3,
        "escalated": True,
    },
    {
        "id": 2003,
        "customer_id": 4,
        "order_id": 1004,
        "restaurant_id": 103,
        "dasher_id": 202,
        "category": "food_quality",
        "priority": "low",
        "status": "resolved",
        "agent_id": 301,
        "subject": "Sushi was not fresh",
        "description": (
            "The sashimi in my chirashi bowl tasted off and the rice was hard. "
            "I'm concerned about food safety."
        ),
        "created_at": datetime(2024, 12, 9, 22, 30),
        "updated_at": datetime(2024, 12, 10, 9, 15),
        "resolution": (
            "Contacted restaurant about food quality. Issued partial refund of $20 "
            "for the sashimi portion. "
            "Restaurant will review food handling."
        ),
        "customer_satisfaction": 4,
        "escalated": False,
    },
    {
        "id": 2004,
        "customer_id": 5,
        "order_id": 1005,
        "restaurant_id": 104,
        "dasher_id": 203,
        "category": "restaurant_issue",
        "priority": "medium",
        "status": "resolved",
        "agent_id": 301,
        "subject": "Restaurant cancelled order after 1 hour wait",
        "description": (
            "I waited over an hour for my order and then the restaurant cancelled it "
            "saying they were out of ingredients. "
            "Very frustrating."
        ),
        "created_at": datetime(2024, 11, 15, 20, 45),
        "updated_at": datetime(2024, 11, 15, 21, 20),
        "resolution": (
            "Full refund issued. Restaurant has been flagged for frequent cancellations. "
            "Offered $10 credit for inconvenience."
        ),
        "customer_satisfaction": 2,
        "escalated": False,
    },
    {
        "id": 2005,
        "customer_id": 1,
        "order_id": 1001,
        "restaurant_id": 101,
        "dasher_id": 201,
        "category": "missing_items",
        "priority": "medium",
        "status": "open",
        "agent_id": 301,
        "subject": "Missing garlic bread from order",
        "description": (
            "I ordered 2 garlic breads but only received 1. The rest of the order was correct."
        ),
        "created_at": datetime(2024, 12, 10, 20, 30),
        "updated_at": datetime(2024, 12, 10, 20, 30),
        "resolution": None,
        "customer_satisfaction": None,
        "escalated": False,
    },
    {
        "id": 2006,
        "customer_id": 4,
        "order_id": 1008,
        "restaurant_id": 104,
        "dasher_id": 203,
        "category": "delivery_issue",
        "priority": "high",
        "status": "escalated",
        "agent_id": 301,
        "subject": "Order extremely late and food was cold",
        "description": (
            "Order was over 1 hour late and the food was completely cold when it arrived. "
            "This is the second time this has happened with this restaurant."
        ),
        "created_at": datetime(2024, 12, 11, 21, 00),
        "updated_at": datetime(2024, 12, 12, 9, 00),
        "resolution": None,
        "customer_satisfaction": None,
        "escalated": True,
    },
]

# Sample policies with vector embeddings for semantic search
# Note: In a real implementation, these embeddings would be generated using OpenAI's API
# For this example, we'll use placeholder vectors that would be replaced with actual embeddings
SAMPLE_POLICIES = [
    {
        "id": 3001,
        "category": "refunds",
        "subcategory": "late_delivery",
        "priority": "medium",
        "active": True,
        "content_embedding": [0.1] * 1536,  # Placeholder - would be actual OpenAI embedding
        "title": "Late Delivery Refund Policy",
        "content": (
            "When an order is delivered more than 30 minutes late from the "
            "estimated delivery time, "
            "customers are eligible for a partial refund or credit. For delays over 60 minutes, "
            "full refunds may be issued at agent discretion."
        ),
        "examples": [
            "Order estimated at 7:00 PM, delivered at 7:45 PM - offer $5 credit",
            "Order estimated at 12:30 PM, delivered at 1:45 PM - offer full refund",
        ],
        "exceptions": [
            "Weather-related delays during severe conditions",
            "Restaurant delays due to large orders (over $100)",
        ],
        "created_at": datetime(2024, 1, 15),
        "updated_at": datetime(2024, 6, 20),
        "version": "2.1",
        "approved_by": "Policy Team",
        "usage_count": 1247,
    },
    {
        "id": 3002,
        "category": "refunds",
        "subcategory": "missing_items",
        "priority": "high",
        "active": True,
        "content_embedding": [0.2] * 1536,  # Placeholder
        "title": "Missing Items Refund Policy",
        "content": (
            "When items are missing from an order, customers should receive a refund "
            "for the missing items "
            "plus applicable taxes and fees. If the missing item represents more than "
            "50% of the order value, "
            "offer a full refund."
        ),
        "examples": [
            "Missing $8 side dish from $25 order - refund $8 + tax",
            "Missing $15 entree from $20 order - offer full refund",
        ],
        "exceptions": [
            "Items marked as 'out of stock' by restaurant before preparation",
            "Customer-requested substitutions",
        ],
        "created_at": datetime(2024, 2, 1),
        "updated_at": datetime(2024, 8, 10),
        "version": "1.3",
        "approved_by": "Policy Team",
        "usage_count": 892,
    },
    {
        "id": 3004,
        "category": "escalation",
        "subcategory": "supervisor_escalation",
        "priority": "high",
        "active": True,
        "content_embedding": [0.4] * 1536,  # Placeholder
        "title": "Supervisor Escalation Guidelines",
        "content": (
            "Escalate to supervisor when: customer requests supervisor, refund amount exceeds $50, "
            "customer is abusive/threatening, or issue involves potential legal implications. "
            "Always document escalation reason and attempted resolutions."
        ),
        "examples": [
            "Customer demands $75 refund for cold food - escalate due to amount",
            "Customer using profanity and threats - escalate for abusive behavior",
        ],
        "exceptions": [
            "Routine refunds under $50 that follow standard policies",
            "Technical questions that can be resolved with documentation",
        ],
        "created_at": datetime(2024, 1, 20),
        "updated_at": datetime(2024, 9, 15),
        "version": "2.2",
        "approved_by": "Operations Team",
        "usage_count": 567,
    },
    {
        "id": 3005,
        "category": "quality",
        "subcategory": "food_safety",
        "priority": "critical",
        "active": True,
        "content_embedding": [0.5] * 1536,  # Placeholder
        "title": "Food Safety Incident Response",
        "content": (
            "For food safety complaints (food poisoning, foreign objects, spoiled food), "
            "immediately issue full refund, "
            "document incident details, and escalate to restaurant relations team. "
            "Follow up with customer within 24 hours."
        ),
        "examples": [
            "Customer reports food poisoning - full refund + escalate to restaurant team",
            "Foreign object found in food - full refund + incident report",
        ],
        "exceptions": [
            "Subjective taste preferences (too salty, too spicy)",
            "Temperature complaints without safety concerns",
        ],
        "created_at": datetime(2024, 2, 15),
        "updated_at": datetime(2024, 10, 1),
        "version": "1.5",
        "approved_by": "Safety Team",
        "usage_count": 89,
    },
]

# Sample refunds
SAMPLE_REFUNDS = [
    {
        "id": 4001,
        "customer_id": 2,
        "order_id": 1002,
        "ticket_id": 2001,
        "refund_type": "credit",
        "reason": "late_delivery",
        "amount": 5.00,
        "processed_date": "2024-12-11",
        "created_at": datetime(2024, 12, 11, 14, 10),
        "processed_at": datetime(2024, 12, 11, 14, 15),
        "status": "processed",
        "agent_id": 301,
        "notes": "Issued $5 DoorDash credit for 35-minute delivery delay",
        "payment_method": "doordash_credit",
    },
    {
        "id": 4002,
        "customer_id": 3,
        "order_id": 1003,
        "ticket_id": 2002,
        "refund_type": "full",
        "reason": "missing_order",
        "amount": 89.95,
        "processed_date": "2024-12-08",
        "created_at": datetime(2024, 12, 8, 22, 30),
        "processed_at": datetime(2024, 12, 8, 22, 35),
        "status": "processed",
        "agent_id": 302,
        "notes": "Full refund for order never delivered - dasher theft confirmed",
        "payment_method": "original_payment",
    },
    {
        "id": 4003,
        "customer_id": 4,
        "order_id": 1004,
        "ticket_id": 2003,
        "refund_type": "partial",
        "reason": "food_quality",
        "amount": 20.00,
        "processed_date": "2024-12-10",
        "created_at": datetime(2024, 12, 10, 9, 15),
        "processed_at": datetime(2024, 12, 10, 9, 20),
        "status": "processed",
        "agent_id": 301,
        "notes": "Partial refund for sashimi quality issue",
        "payment_method": "original_payment",
    },
    {
        "id": 4004,
        "customer_id": 5,
        "order_id": 1005,
        "ticket_id": 2004,
        "refund_type": "full",
        "reason": "restaurant_cancellation",
        "amount": 34.56,
        "processed_date": "2024-11-15",
        "created_at": datetime(2024, 11, 15, 21, 20),
        "processed_at": datetime(2024, 11, 15, 21, 25),
        "status": "processed",
        "agent_id": 301,
        "notes": "Full refund for restaurant cancellation after 1 hour wait",
        "payment_method": "original_payment",
    },
]

# Sample escalations
SAMPLE_ESCALATIONS = [
    {
        "id": 5001,
        "ticket_id": 2002,
        "from_agent_id": 301,
        "to_agent_id": 302,
        "escalation_type": "supervisor",
        "priority": "urgent",
        "reason": "High-value order theft, requires investigation",
        "notes": (
            "Customer claims $89.95 sushi order was never delivered but dasher "
            "marked as delivered. "
            "Need to review GPS data and contact dasher."
        ),
        "created_at": datetime(2024, 12, 8, 21, 45),
        "resolved_at": datetime(2024, 12, 8, 22, 30),
        "resolution": (
            "Confirmed dasher theft through GPS analysis and dasher admission. "
            "Full refund issued, dasher suspended."
        ),
    },
    {
        "id": 5002,
        "ticket_id": 2006,
        "from_agent_id": 301,
        "to_agent_id": 302,
        "escalation_type": "supervisor",
        "priority": "normal",
        "reason": "Repeat customer complaint about same restaurant",
        "notes": (
            "Customer has now had 2 bad experiences with Slow Kitchen restaurant. "
            "Both orders were extremely late and food was cold."
        ),
        "created_at": datetime(2024, 12, 12, 9, 00),
        "resolved_at": None,
        "resolution": None,
    },
]


# Sample incidents
SAMPLE_INCIDENTS = [
    {
        "id": 7001,
        "incident_type": "weather",
        "severity": "high",
        "status": "resolved",
        "affected_region": "Chicago",
        "start_date": "2024-11-15",
        "title": "Severe Snowstorm - Chicago Area",
        "description": (
            "Heavy snowfall causing widespread delivery delays and cancellations "
            "across Chicago metropolitan area."
        ),
        "started_at": datetime(2024, 11, 15, 14, 00),
        "resolved_at": datetime(2024, 11, 16, 10, 00),
        "affected_customers": 2847,
        "affected_orders": [1005, 1009, 1010, 1011],  # Sample order IDs
        "root_cause": "Severe weather conditions making roads impassable",
        "resolution_notes": (
            "Weather cleared, normal operations resumed. Proactive credits issued "
            "to affected customers."
        ),
    },
    {
        "id": 7002,
        "incident_type": "restaurant_issue",
        "severity": "medium",
        "status": "investigating",
        "affected_region": "Los Angeles",
        "start_date": "2024-12-11",
        "title": "Slow Kitchen - Consistent Delays",
        "description": (
            "Multiple customer complaints about extremely long preparation times "
            "and cold food from Slow Kitchen restaurant."
        ),
        "started_at": datetime(2024, 12, 11, 18, 00),
        "resolved_at": None,
        "affected_customers": 23,
        "affected_orders": [1008, 1012, 1013],  # Sample order IDs
        "root_cause": None,
        "resolution_notes": None,
    },
]


# ============================================================================
# DATA POPULATION AND STARTUP
# ============================================================================


async def setup_sample_data():
    """Set up Redis indices and populate sample data."""
    print("🚀 Starting DoorDash Support Agent API...")
    print(f"📡 Connecting to Redis at {app.redis_backend.redis_url}")
    print("💡 Make sure Redis Stack is running: docker-compose up -d")
    print()

    # Prepare sample data
    sample_data = {
        "customers": SAMPLE_CUSTOMERS,
        "restaurants": SAMPLE_RESTAURANTS,
        "dashers": SAMPLE_DASHERS,
        "orders": SAMPLE_ORDERS,
        "agents": SAMPLE_AGENTS,
        "supporttickets": SAMPLE_TICKETS,  # Note: using class name
        "policies": SAMPLE_POLICIES,
        "refunds": SAMPLE_REFUNDS,
        "escalations": SAMPLE_ESCALATIONS,
        "incidents": SAMPLE_INCIDENTS,
    }

    # Use the apply method to set up indices and populate data
    await app.apply(sample_data)

    print("💾 Sample data loaded successfully!")
    print()
    print("🎯 MCP server ready! Connect your AI agent to start searching.")
    print()
    print("📊 Available Tools:")
    print("• Text search: search_customer_by_text, search_restaurant_by_text")
    print("• Tag filters: filter_customer_by_account_status, filter_order_by_status")
    print("• Numeric ranges: find_order_by_order_total_range, find_restaurant_by_rating_range")
    print("• Vector search: search_policy_by_similarity (semantic policy search)")
    print(
        "• Relationships: get_order_customer, get_order_restaurant, "
        "get_ticket_order, get_refund_customer"
    )
    print("• And many more auto-generated tools for comprehensive support!")


@app.retrieve()
async def get_customer_summary(customer_id: int) -> dict[str, Any]:
    """Get comprehensive customer summary for support agents."""
    customer = await Customer.get(customer_id)
    if not customer:
        return {"error": "Customer not found"}

    # Get related data
    orders = [Order(**order) for order in SAMPLE_ORDERS if order["customer_id"] == customer_id]
    tickets = [
        SupportTicket(**ticket) for ticket in SAMPLE_TICKETS if ticket["customer_id"] == customer_id
    ]
    refunds = [
        Refund(**refund) for refund in SAMPLE_REFUNDS if refund["customer_id"] == customer_id
    ]

    return {
        "customer": customer.model_dump(),
        "order_count": len(orders),
        "recent_orders": [o.model_dump() for o in orders[-5:]],  # Last 5 orders
        "open_tickets": [t.model_dump() for t in tickets if t.status in ["open", "in_progress"]],
        "total_refunds": sum(r.amount for r in refunds),
        "account_health": "flagged"
        if customer.account_status == "flagged"
        else "suspended"
        if customer.account_status == "suspended"
        else "good",
        "satisfaction_trend": "declining"
        if any(t.customer_satisfaction and t.customer_satisfaction < 3 for t in tickets)
        else "stable",
    }


@app.retrieve()
async def search_policies_by_similarity(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search policies using vector similarity for intelligent support assistance."""
    # In a real implementation, this would:
    # 1. Generate embedding for the query using OpenAI API
    # 2. Perform vector similarity search in Redis
    # 3. Return the most relevant policies

    # For this example, we'll do simple text matching
    matching_policies = []
    query_lower = query.lower()

    for policy_data in SAMPLE_POLICIES:
        policy = Policy(**policy_data)
        content_lower = policy.content.lower()
        title_lower = policy.title.lower()

        # Simple relevance scoring based on keyword matches
        score = 0
        if query_lower in title_lower:
            score += 10
        if query_lower in content_lower:
            score += 5
        for example in policy.examples:
            if query_lower in example.lower():
                score += 3

        if score > 0:
            policy_dict = policy.model_dump()
            policy_dict["relevance_score"] = score
            matching_policies.append(policy_dict)

    # Sort by relevance and return top results
    matching_policies.sort(key=lambda x: x["relevance_score"], reverse=True)
    return matching_policies[:limit]


if __name__ == "__main__":
    import asyncio

    async def main():
        # Set up Redis indices and populate sample data
        await setup_sample_data()

        print("\n🎯 DoorDash Support Agent API is ready!")
        print(
            "🔍 Use the explore_doordash_support_agent_api_data_model tool to see "
            "all available entities and tools"
        )
        print(
            "💡 Try searching for policies with: "
            "search_policy_by_similarity('customer wants refund for late delivery')"
        )
        print("📊 Get customer insights with: get_customer_summary(customer_id=1)")

    # Set up data first
    asyncio.run(main())

    # Run the MCP server (synchronous)
    app.run()
