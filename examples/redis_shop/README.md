# Redis Shop API Example

This example demonstrates EnrichMCP with Redis search capabilities for an e-commerce API.

## Features

- **Redis Search Integration**: Full-text search, tag filtering, and numeric range queries
- **Auto-Generated Resources**: MCP tools created automatically from field metadata
- **Minimal Indexing**: Only index fields you actually search
- **Docker Setup**: Redis Stack with RedisInsight web UI included

## Quick Start

1. **Start Redis Stack:**
   ```bash
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
- `user_idx`: Text search on username/email/name, tag filter on status, numeric range on risk_score
- `product_idx`: Text search on name, tag filter on category, numeric range on price
- `order_idx`: Tag filter on user_id/status, numeric range on total_amount

### Auto-Generated MCP Resources
- `search_user_by_text(query: str)` - Search users by name, username, or email
- `filter_user_by_account_status(status: str)` - Find users by status
- `find_users_by_risk_score_range(min_score: float, max_score: float)` - Risk score ranges
- `search_product_by_text(query: str)` - Search products by name
- `filter_product_by_category(category: str)` - Filter by product category
- `find_products_by_price_range(min_price: float, max_price: float)` - Price ranges
- `filter_order_by_status(status: str)` - Find orders by status
- `find_orders_by_user_id(user_id: int)` - Find user's orders
- `find_orders_by_amount_range(min_amount: float, max_amount: float)` - Amount ranges

### Sample Data
- 3 users (including 1 flagged suspicious account)
- 2 products (smartphone and shoes)
- 2 orders (1 normal, 1 flagged as fraudulent)

## Redis Storage Structure

```
user:1 -> {"username": "john_doe", "email": "john@example.com", ...}
user:2 -> {"username": "jane_smith", "email": "jane@example.com", ...}
user:3 -> {"username": "suspicious_user", "account_status": "flagged", ...}

product:101 -> {"name": "Smartphone Pro", "category": "Electronics", "price": 999.99, ...}
product:102 -> {"name": "Running Shoes", "category": "Footwear", "price": 149.99, ...}

order:1001 -> {"user_id": 1, "status": "delivered", "product_ids": [102], ...}
order:1002 -> {"user_id": 3, "status": "flagged", "product_ids": [101, 101, 101], ...}
```

## Cleanup

```bash
docker-compose down -v  # Removes containers and volumes
```
