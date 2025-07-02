# Entities

## Overview

Entities are the core data models in enrichmcp. They extend Pydantic's `BaseModel` with additional capabilities for relationships and introspection.

## EnrichModel Base Class

All entities must inherit from `EnrichModel`:

```python
from enrichmcp import EnrichModel
from pydantic import Field


class MyEntity(EnrichModel):
    id: int = Field(description="Unique identifier")
```

## Class Methods

### `relationship_fields() -> set[str]`

Returns the names of all relationship fields in the model.

```python
fields = User.relationship_fields()
# {"orders", "profile"}
```

### `relationships() -> set[Relationship]`

Returns all relationship instances in the model.

```python
rels = User.relationships()
# {<Relationship>, <Relationship>}
```

### `describe() -> str`

Generate a human-readable description of the model instance.

```python
user = User(id=1, name="John")
print(user.describe())
# # User
# User account.
#
# ## Fields
# - **id** (int): User ID
# - **name** (str): Username
#
# ## Relationships
# - **orders** → list[Order]: User's orders
```

## Creating Entities

### Basic Entity

```python
@app.entity
class Product(EnrichModel):
    """Product in our catalog."""

    id: int = Field(description="Product ID")
    name: str = Field(description="Product name")
    price: float = Field(description="Price in USD")
    stock: int = Field(description="Available quantity")
```

### Entity with Relationships

```python
@app.entity
class Customer(EnrichModel):
    """Customer account."""

    id: int = Field(description="Customer ID")
    email: str = Field(description="Email address")

    # One-to-many relationship
    orders: list["Order"] = Relationship(description="Customer's orders")

    # One-to-one relationship
    profile: "Profile" = Relationship(description="Customer profile")
```

### Entity with Validation

```python
from pydantic import field_validator


@app.entity
class Product(EnrichModel):
    """Product with validation."""

    name: str = Field(description="Product name")
    price: float = Field(description="Price in USD")

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be positive")
        return v
```

## Field Types

### Basic Types

```python
name: str = Field(description="Text field")
age: int = Field(description="Integer field")
price: float = Field(description="Decimal field")
is_active: bool = Field(description="Boolean field")
```

### Optional Fields

```python
middle_name: str | None = Field(default=None, description="Optional middle name")
```

### Date/Time Fields

```python
from datetime import date, datetime

birth_date: date = Field(description="Date of birth")
created_at: datetime = Field(description="Creation timestamp")
```

### Enum Fields

```python
from enum import Enum


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


status: Status = Field(description="Account status")
```

### Collection Fields

```python
tags: list[str] = Field(description="List of tags", default_factory=list)
metadata: dict[str, Any] = Field(description="Arbitrary metadata", default_factory=dict)
```

### Mutable Fields

Fields are immutable unless `json_schema_extra={"mutable": True}`:

```python
@app.entity
class Customer(EnrichModel):
    id: int = Field(description="ID")
    email: str = Field(json_schema_extra={"mutable": True}, description="Email")

    # Customer.PatchModel is generated automatically
```

## Serialization

EnrichModel automatically excludes relationship fields when serializing:

```python
user = User(id=1, email="john@example.com")

# Relationships excluded from dict
data = user.model_dump()
# {"id": 1, "email": "john@example.com"}

# Relationships excluded from JSON
json_str = user.model_dump_json()
# '{"id": 1, "email": "john@example.com"}'
```

## Computed Properties

Add derived data using properties:

```python
@app.entity
class Order(EnrichModel):
    """Order with computed total."""

    subtotal: float = Field(description="Subtotal")
    tax_rate: float = Field(description="Tax rate")

    @property
    def tax(self) -> float:
        """Calculate tax amount."""
        return self.subtotal * self.tax_rate

    @property
    def total(self) -> float:
        """Calculate total."""
        return self.subtotal + self.tax
```

## Best Practices

1. **Always include docstrings** - The class docstring becomes the entity description
2. **Describe every field** - All fields must have descriptions
3. **Use meaningful names** - `customer_email` not `ce`
4. **Group related fields** - Consider nested models for complex data
5. **Add validation** - Use Pydantic validators for business rules

## Complete Example

```python
from datetime import datetime
from enum import Enum
from enrichmcp import EnrichModel, Relationship
from pydantic import Field, field_validator


class OrderStatus(str, Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


@app.entity
class Order(EnrichModel):
    """Customer order with validation and relationships."""

    # Basic fields
    id: int = Field(description="Order ID")
    status: OrderStatus = Field(description="Order status", default=OrderStatus.PENDING)

    # Amounts
    subtotal: float = Field(description="Order subtotal")
    tax_rate: float = Field(description="Tax rate (0.08 = 8%)", ge=0.0, le=1.0)
    shipping: float = Field(description="Shipping cost", ge=0.0)

    # Timestamps
    created_at: datetime = Field(description="Order creation time", default_factory=datetime.now)
    shipped_at: datetime | None = Field(default=None, description="When order was shipped")

    # Relationships
    customer: "Customer" = Relationship(description="Customer who placed the order")
    items: list["OrderItem"] = Relationship(description="Items in the order")

    # Computed properties
    @property
    def tax(self) -> float:
        """Calculate tax amount."""
        return round(self.subtotal * self.tax_rate, 2)

    @property
    def total(self) -> float:
        """Calculate order total."""
        return round(self.subtotal + self.tax + self.shipping, 2)

    # Validation
    @field_validator("subtotal", "shipping")
    @classmethod
    def amounts_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v
```
