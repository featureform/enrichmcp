import json

import pytest

from enrichmcp import (
    EnrichModel,
    Relationship,
)


class Address(EnrichModel):
    """Address entity for testing."""

    street: str
    city: str
    zip_code: str

    # Regular field that should be included in serialization
    country: str = "USA"


class User(EnrichModel):
    """User entity for testing."""

    id: int
    name: str
    email: str

    # Create a relationship field that should be excluded from serialization
    address: Relationship = Relationship(description="User's address")

    # Regular field that should be included in serialization
    is_active: bool = True


def test_model_dump_excludes_relationships():
    """Test that model_dump automatically excludes relationship fields."""
    user = User(id=1, name="John Doe", email="john@example.com")

    # Dump to dict
    user_dict = user.model_dump()

    # Check that regular fields are included
    assert "id" in user_dict
    assert user_dict["id"] == 1
    assert "name" in user_dict
    assert user_dict["name"] == "John Doe"
    assert "email" in user_dict
    assert user_dict["email"] == "john@example.com"
    assert "is_active" in user_dict
    assert user_dict["is_active"] is True

    # Check that relationship field is excluded
    assert "address" not in user_dict


def test_model_dump_json_excludes_relationships():
    """Test that model_dump_json automatically excludes relationship fields."""
    user = User(id=1, name="John Doe", email="john@example.com")

    # Dump to JSON
    user_json = user.model_dump_json()
    user_dict = json.loads(user_json)

    # Check that regular fields are included
    assert "id" in user_dict
    assert user_dict["id"] == 1
    assert "name" in user_dict
    assert user_dict["name"] == "John Doe"
    assert "email" in user_dict
    assert user_dict["email"] == "john@example.com"
    assert "is_active" in user_dict
    assert user_dict["is_active"] is True

    # Check that relationship field is excluded
    assert "address" not in user_dict


def test_model_dump_with_manual_exclude():
    """Test model_dump with manual exclude parameter."""
    user = User(id=1, name="John Doe", email="john@example.com")

    # Dump to dict with manual exclude
    user_dict = user.model_dump(exclude={"email"})

    # Check that regular fields are included
    assert "id" in user_dict
    assert user_dict["id"] == 1
    assert "name" in user_dict
    assert user_dict["name"] == "John Doe"
    assert "is_active" in user_dict
    assert user_dict["is_active"] is True

    # Check that manually excluded field is excluded
    assert "email" not in user_dict

    # Check that relationship field is also excluded
    assert "address" not in user_dict


def test_model_dump_json_with_manual_exclude():
    """Test model_dump_json with manual exclude parameter."""
    user = User(id=1, name="John Doe", email="john@example.com")

    # Dump to JSON with manual exclude
    user_json = user.model_dump_json(exclude={"email"})
    user_dict = json.loads(user_json)

    # Check that regular fields are included
    assert "id" in user_dict
    assert user_dict["id"] == 1
    assert "name" in user_dict
    assert user_dict["name"] == "John Doe"
    assert "is_active" in user_dict
    assert user_dict["is_active"] is True

    # Check that manually excluded field is excluded
    assert "email" not in user_dict

    # Check that relationship field is also excluded
    assert "address" not in user_dict


def test_model_with_multiple_relationships():
    """Test a model with multiple relationship fields."""

    class Product(EnrichModel):
        id: int
        name: str

        # Add multiple relationship fields
        category: Relationship = Relationship(description="Product category")
        supplier: Relationship = Relationship(description="Product supplier")
        reviews: Relationship = Relationship(description="Product reviews")

    product = Product(id=1, name="Test Product")

    # Check that relationship_fields correctly returns all relationship fields
    relationship_fields = product.__class__.relationship_fields()
    assert len(relationship_fields) == 3
    assert "category" in relationship_fields
    assert "supplier" in relationship_fields
    assert "reviews" in relationship_fields

    # Dump to dict and check that all relationships are excluded
    product_dict = product.model_dump()
    assert "id" in product_dict
    assert "name" in product_dict
    assert "category" not in product_dict
    assert "supplier" not in product_dict
    assert "reviews" not in product_dict


def test_relationship_fields_method():
    """Test the relationship_fields class method."""
    # Get relationship fields from User class
    fields = User.relationship_fields()

    # Should only contain 'address'
    assert len(fields) == 1
    assert "address" in fields

    # Test with a class that has no relationships
    class NoRelationships(EnrichModel):
        id: int
        name: str

    # Should be empty
    assert len(NoRelationships.relationship_fields()) == 0


def test_model_with_invalid_exclude_type():
    """Test that providing an invalid exclude type raises a TypeError."""
    user = User(id=1, name="John Doe", email="john@example.com")

    # Test with a dict which is not supported by our implementation
    with pytest.raises(TypeError) as exc_info:
        user.model_dump(exclude={"email": True})

    # Check that the error message is helpful
    assert "Cannot combine fields with exclude of type dict" in str(exc_info.value)


def test_relationship_not_set_on_instance():
    """Relationship defaults should be removed after initialization."""
    user = User(id=1, name="John Doe", email="john@example.com")

    # Relationship field should not be stored in the instance dict
    assert "address" not in user.__dict__

    # Attribute shouldn't exist on the instance
    assert not hasattr(user, "address")
    with pytest.raises(AttributeError):
        _ = user.address
