# Redis DoorDash Support Agent Example

This example demonstrates a comprehensive DoorDash support agent using EnrichMCP with Redis search capabilities, including vector-indexed policies for intelligent support assistance.

## Features

- **Complete DoorDash Ecosystem**: Customers, Orders, Dashers, Restaurants, Support Tickets, Policies
- **Vector-Indexed Policies**: Semantic search for support policies using embeddings
- **Redis Search Integration**: Full-text search, tag filtering, numeric ranges, and vector similarity
- **Rich Relationships**: Complex entity relationships for comprehensive support investigations
- **Auto-Generated Resources**: 50+ MCP tools created automatically from entity metadata
- **Real Support Scenarios**: Sample data representing realistic DoorDash support cases

## Entities

### Core Business Entities
- **Customer**: Account info, tier status, and preferences
- **Order**: Full order lifecycle with delivery tracking
- **Restaurant**: Merchant information and performance metrics
- **Dasher**: Driver profiles, ratings, and performance data

### Support System Entities
- **SupportTicket**: Customer issues with categorization and priority
- **Agent**: Support agent profiles and specializations
- **Policy**: Vector-indexed support policies for intelligent assistance
- **Refund**: Refund transactions and credits
- **Escalation**: Ticket escalation tracking
- **Incident**: System-wide incidents affecting service



## Quick Start

1. **Start Redis Stack:**
   ```bash
   cd examples/redis_doordash
   docker-compose up -d
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the example:**
   ```bash
   python app.py
   ```

4. **Access RedisInsight** (optional):
   - Open http://localhost:8001 in your browser
   - Connect to `localhost:6379` to explore the data

## What Gets Created

### Redis Indices
- **Text Search**: Customer names/emails, restaurant names, dasher info
- **Tag Filtering**: Order status, ticket categories, account status, regions
- **Numeric Ranges**: Order totals, ratings, refund amounts
- **Vector Search**: Policy content embeddings for semantic similarity

### Auto-Generated MCP Resources (50+ tools)

#### Customer Management
- `search_customer_by_text(query)` - Find customers by name, email, phone
- `filter_customer_by_account_status(status)` - Find customers by status
- `filter_customer_by_tier(tier)` - Find DashPass/premium customers

#### Order Investigation
- `search_order_by_customer_id(customer_id)` - Customer's order history
- `filter_order_by_status(status)` - Orders by delivery status
- `find_order_by_total_range(min, max)` - Orders by value
- `filter_order_by_date(date)` - Orders by specific date

#### Support Operations
- `filter_ticket_by_status(status)` - Open/resolved tickets
- `filter_ticket_by_category(category)` - Tickets by issue type
- `filter_ticket_by_priority(priority)` - High priority tickets
- `search_agent_by_text(query)` - Find agents by name/specialization

#### Intelligent Policy Search (Vector-Powered)
- `search_policies_by_similarity(query, threshold)` - Semantic policy search
- `get_policy_recommendations(ticket_id)` - AI-suggested policies for tickets
- `find_similar_cases(description)` - Find similar historical cases

#### Escalation Management
- `filter_escalation_by_type(type)` - Escalations by category
- `filter_escalation_by_priority(priority)` - High priority escalations
- `get_escalation_patterns()` - Escalation trend analysis

#### Relationship Resolvers (20+ tools)
- `get_customer_orders(customer)` - Customer's complete order history
- `get_order_tickets(order)` - Support tickets for specific orders
- `get_ticket_related_policies(ticket)` - Applicable policies for tickets
- `get_restaurant_recent_issues(restaurant)` - Restaurant problem patterns
- `get_dasher_performance_issues(dasher)` - Driver-related complaints

## Sample Data

### Customers
- 5 customers including premium DashPass members and flagged accounts
- Realistic spending patterns and order history
- Various account statuses and geographic locations

### Orders
- 8 orders covering different scenarios: successful deliveries, cancellations, issues
- Range of order values from $15 to $200+
- Different restaurants, dashers, and delivery outcomes

### Support Tickets
- 6 realistic support scenarios: missing items, late delivery, refund requests
- Various priorities and categories
- Different resolution states and agent assignments

### Policies (Vector-Indexed)
- 4 comprehensive support policies covering common scenarios
- Embedded using OpenAI embeddings for semantic search
- Categories: refunds, delivery issues, escalations, food safety

### Sample Scenarios
- **High-Value Customer Issue**: Premium customer with late delivery complaint
- **Restaurant Problems**: Multiple complaints about same restaurant
- **Dasher Performance**: Driver with multiple delivery issues
- **System Incident**: Weather-related delivery delays affecting region
- **Escalation Management**: Complex issues requiring supervisor intervention

## Advanced Use Cases

### Intelligent Support Assistance
```python
# Agent types: "customer says food never arrived"
# System finds relevant policies automatically:
policies = await search_policies_by_similarity(
    "customer says food never arrived",
    similarity_threshold=0.8
)
# Returns: "Missing Delivery Policy", "GPS Verification Process", etc.
```

### Complex Investigations
```python
# Multi-entity investigation
customer = await get_customer_by_id(123)
recent_orders = await get_customer_orders(customer)
open_tickets = await get_customer_tickets(customer, status="open")
refund_history = await get_customer_refunds(customer)

# Pattern detection
refund_patterns = await find_customers_with_multiple_refunds(days=30, min_refunds=3)
```

### Proactive Support
```python
# Find customers affected by incidents who haven't been contacted
incident = await get_incident_by_id(456)
affected_customers = await get_incident_affected_customers(incident)
uncontacted = [c for c in affected_customers if not c.recent_tickets]
```

## Vector Search Technology

The policy system uses OpenAI embeddings (1536 dimensions) stored in Redis Vector Search:

- **Semantic Understanding**: "food was cold" matches "poor quality meal" policies
- **Context Awareness**: Considers order value, customer tier, incident context
- **Learning System**: Tracks policy usage to improve recommendations
- **Consistency**: All agents get same policy suggestions for similar issues

## Redis Storage Structure

```
customer:1 -> {"full_name": "John Doe", "email": "john@example.com", ...}
order:1001 -> {"customer_id": 1, "status": "delivered", "total": 45.99, ...}
ticket:2001 -> {"customer_id": 1, "category": "missing_items", ...}
policy:1 -> {"title": "Missing Items Policy", "embedding": [0.1, -0.3, ...], ...}
```

## Cleanup

```bash
docker-compose down -v  # Removes containers and volumes
```

This example demonstrates how EnrichMCP can power sophisticated support systems with AI-enhanced policy recommendations and comprehensive relationship tracking.
