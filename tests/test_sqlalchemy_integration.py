"""
Tests for SQLAlchemy integration with EnrichMCP.
"""

# ruff: noqa: N806,E721

import types
from datetime import date, datetime
from typing import Union, get_args, get_origin

import pytest
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from enrichmcp import EnrichModel, Relationship
from enrichmcp.sqlalchemy import EnrichSQLAlchemyMixin


class TestBasicModel:
    """Test basic SQLAlchemy model conversion."""

    def test_simple_model_conversion(self):
        """Test converting a simple SQLAlchemy model to EnrichModel."""

        class Base(DeclarativeBase):
            pass

        class User(Base, EnrichSQLAlchemyMixin):
            """User entity for testing."""

            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True, info={"description": "User ID"})
            username: Mapped[str] = mapped_column(info={"description": "Username"})
            email: Mapped[str] = mapped_column(info={"description": "Email address"})
            is_active: Mapped[bool] = mapped_column(
                default=True, info={"description": "Active status"}
            )

        # Convert to EnrichModel
        UserEnrichModel = User.__enrich_model__()

        # Check that it's a proper EnrichModel subclass
        assert issubclass(UserEnrichModel, EnrichModel)

        # Check fields exist
        fields = UserEnrichModel.model_fields
        assert "id" in fields
        assert "username" in fields
        assert "email" in fields
        assert "is_active" in fields

        # Check field types
        assert fields["id"].annotation == int
        assert fields["username"].annotation == str
        assert fields["email"].annotation == str
        assert fields["is_active"].annotation == bool

        # Check descriptions
        assert fields["id"].description == "User ID"
        assert fields["username"].description == "Username"
        assert fields["email"].description == "Email address"
        assert fields["is_active"].description == "Active status"

    def test_nullable_columns(self):
        """Test that nullable columns are converted to Optional types."""

        class Base(DeclarativeBase):
            pass

        class Product(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "products"

            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(nullable=False)
            description: Mapped[str | None] = mapped_column(
                nullable=True, info={"description": "Product description"}
            )
            price: Mapped[float | None] = mapped_column(nullable=True)

        ProductEnrichModel = Product.__enrich_model__()
        fields = ProductEnrichModel.model_fields

        # Non-nullable fields should not be Optional
        assert fields["id"].annotation == int
        assert fields["name"].annotation == str

        # Nullable fields should be Optional
        # Check if it's Optional by looking at the annotation
        desc_type = fields["description"].annotation
        price_type = fields["price"].annotation

        # In Python 3.10+, Optional[X] is Union[X, None]
        assert get_origin(desc_type) in {Union, types.UnionType}
        assert type(None) in get_args(desc_type)
        assert str in get_args(desc_type)

        assert get_origin(price_type) in {Union, types.UnionType}
        assert type(None) in get_args(price_type)
        assert float in get_args(price_type)

    def test_excluded_fields(self):
        """Test that fields marked with exclude=True are not included."""

        class Base(DeclarativeBase):
            pass

        class User(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True)
            username: Mapped[str] = mapped_column()
            password_hash: Mapped[str] = mapped_column(info={"exclude": True})
            secret_token: Mapped[str] = mapped_column(
                info={"exclude": True, "description": "Should not appear"}
            )

        UserEnrichModel = User.__enrich_model__()
        fields = UserEnrichModel.model_fields

        # Check included fields
        assert "id" in fields
        assert "username" in fields

        # Check excluded fields
        assert "password_hash" not in fields
        assert "secret_token" not in fields

    def test_various_column_types(self):
        """Test conversion of various SQLAlchemy column types."""

        class Base(DeclarativeBase):
            pass

        class DataTypes(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "data_types"

            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            name: Mapped[str] = mapped_column(String(100))
            description: Mapped[str] = mapped_column(Text)
            is_active: Mapped[bool] = mapped_column(Boolean)
            price: Mapped[float] = mapped_column(Float)
            created_at: Mapped[datetime] = mapped_column(DateTime)
            birth_date: Mapped[date] = mapped_column(Date)

        DataTypesEnrichModel = DataTypes.__enrich_model__()
        fields = DataTypesEnrichModel.model_fields

        # Check type conversions
        assert fields["id"].annotation == int
        assert fields["name"].annotation == str
        assert fields["description"].annotation == str
        assert fields["is_active"].annotation == bool
        assert fields["price"].annotation == float
        assert fields["created_at"].annotation == datetime
        # Date type should be converted properly
        assert fields["birth_date"].annotation == date

    def test_model_documentation(self):
        """Test that model docstring is preserved."""

        class Base(DeclarativeBase):
            pass

        class Order(Base, EnrichSQLAlchemyMixin):
            """Order represents a customer purchase."""

            __tablename__ = "orders"

            id: Mapped[int] = mapped_column(primary_key=True)
            total: Mapped[float] = mapped_column()

        OrderEnrichModel = Order.__enrich_model__()
        assert OrderEnrichModel.__doc__ == "Order represents a customer purchase."

    def test_default_descriptions(self):
        """Test that fields without descriptions get default ones."""

        class Base(DeclarativeBase):
            pass

        class Item(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "items"

            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column()  # No description in info

        ItemEnrichModel = Item.__enrich_model__()
        fields = ItemEnrichModel.model_fields

        # Should have default descriptions
        assert fields["id"].description == "id field"
        assert fields["name"].description == "name field"


class TestRelationships:
    """Test SQLAlchemy relationship conversion."""

    def test_one_to_many_relationship(self):
        """Test one-to-many relationship conversion."""

        class Base(DeclarativeBase):
            pass

        class User(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True)
            username: Mapped[str] = mapped_column()
            orders: Mapped[list["Order"]] = relationship(
                back_populates="user", info={"description": "User's orders"}
            )

        class Order(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "orders"

            id: Mapped[int] = mapped_column(primary_key=True)
            user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
            user: Mapped[User] = relationship(
                back_populates="orders", info={"description": "Order's user"}
            )

        # Convert to EnrichModel
        UserEnrichModel = User.__enrich_model__()
        fields = UserEnrichModel.model_fields

        # Check that orders field exists and is a Relationship
        assert "orders" in fields
        assert isinstance(fields["orders"].default, Relationship)
        assert fields["orders"].default.description == "User's orders"

        # Check the type annotation (should be list["OrderEnrichModel"])
        # The annotation will be a string forward reference
        assert "list" in str(fields["orders"].annotation)
        assert "OrderEnrichModel" in str(fields["orders"].annotation)

    def test_many_to_one_relationship(self):
        """Test many-to-one relationship conversion."""

        class Base(DeclarativeBase):
            pass

        class Order(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "orders"

            id: Mapped[int] = mapped_column(primary_key=True)
            user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
            user: Mapped["User"] = relationship(
                info={"description": "Customer who placed the order"}
            )

        class User(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True)
            username: Mapped[str] = mapped_column()

        OrderEnrichModel = Order.__enrich_model__()
        fields = OrderEnrichModel.model_fields

        # Check that user field exists and is a Relationship
        assert "user" in fields
        assert isinstance(fields["user"].default, Relationship)
        assert fields["user"].default.description == "Customer who placed the order"

        # Type should be just "UserEnrichModel" (not List)
        assert "UserEnrichModel" in str(fields["user"].annotation)
        assert "List" not in str(fields["user"].annotation)

    def test_excluded_relationship(self):
        """Test that relationships marked with exclude=True are not included."""

        class Base(DeclarativeBase):
            pass

        class User(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True)
            username: Mapped[str] = mapped_column()
            secret_orders: Mapped[list["Order"]] = relationship(
                info={"exclude": True}, overlaps="public_orders"
            )
            public_orders: Mapped[list["Order"]] = relationship(
                info={"description": "Public orders"}, overlaps="secret_orders"
            )

        class Order(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "orders"
            id: Mapped[int] = mapped_column(primary_key=True)
            user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

        UserEnrichModel = User.__enrich_model__()
        fields = UserEnrichModel.model_fields

        # Check that excluded relationship is not included
        assert "secret_orders" not in fields
        assert "public_orders" in fields

    def test_relationship_without_description(self):
        """Test relationship with no description gets a default one."""

        class Base(DeclarativeBase):
            pass

        class User(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True)
            posts: Mapped[list["Post"]] = relationship()

        class Post(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "posts"

            id: Mapped[int] = mapped_column(primary_key=True)
            user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

        UserEnrichModel = User.__enrich_model__()
        fields = UserEnrichModel.model_fields

        assert "posts" in fields
        assert isinstance(fields["posts"].default, Relationship)
        assert fields["posts"].default.description == "Relationship to PostEnrichModel"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_non_declarative_base_raises_error(self):
        """Test that using the mixin without DeclarativeBase raises an error."""

        class NotSQLAlchemy(EnrichSQLAlchemyMixin):
            """This is not a SQLAlchemy model."""

            pass

        with pytest.raises(TypeError) as exc_info:
            NotSQLAlchemy.__enrich_model__()

        assert "must inherit from SQLAlchemy DeclarativeBase" in str(exc_info.value)

    def test_model_with_no_docstring(self):
        """Test model without docstring gets a default one."""

        class Base(DeclarativeBase):
            pass

        class NoDoc(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "no_doc"
            id: Mapped[int] = mapped_column(primary_key=True)

        NoDocEnrichModel = NoDoc.__enrich_model__()
        assert NoDocEnrichModel.__doc__ == "NoDoc entity"

    def test_async_attrs_compatibility(self):
        """Test that the mixin works with AsyncAttrs."""

        class Base(DeclarativeBase):
            pass

        class AsyncUser(Base, AsyncAttrs, EnrichSQLAlchemyMixin):
            """Async user model."""

            __tablename__ = "async_users"

            id: Mapped[int] = mapped_column(primary_key=True)
            username: Mapped[str] = mapped_column()

        # Should work without issues
        AsyncUserEnrichModel = AsyncUser.__enrich_model__()
        assert issubclass(AsyncUserEnrichModel, EnrichModel)
        assert "id" in AsyncUserEnrichModel.model_fields
        assert "username" in AsyncUserEnrichModel.model_fields

    def test_generated_model_name(self):
        """Test that generated EnrichModel has correct name."""

        class Base(DeclarativeBase):
            pass

        class Customer(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "customers"
            id: Mapped[int] = mapped_column(primary_key=True)

        CustomerEnrichModel = Customer.__enrich_model__()
        assert CustomerEnrichModel.__name__ == "CustomerEnrichModel"

    def test_model_inheritance(self):
        """Test that the EnrichModel properly inherits from EnrichModel base."""

        class Base(DeclarativeBase):
            pass

        class Product(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "products"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column()

        ProductEnrichModel = Product.__enrich_model__()

        # Should be a proper EnrichModel with all its methods
        assert hasattr(ProductEnrichModel, "model_dump")
        assert hasattr(ProductEnrichModel, "model_dump_json")
        assert hasattr(ProductEnrichModel, "relationship_fields")
        assert hasattr(ProductEnrichModel, "describe")

    def test_sqlalchemy_model_reference_stored(self):
        """Test that reference to original SQLAlchemy model is stored."""

        class Base(DeclarativeBase):
            pass

        class Order(Base, EnrichSQLAlchemyMixin):
            __tablename__ = "orders"
            id: Mapped[int] = mapped_column(primary_key=True)

        OrderEnrichModel = Order.__enrich_model__()
        assert hasattr(OrderEnrichModel, "_sqlalchemy_model")
        assert OrderEnrichModel._sqlalchemy_model is Order


class TestComplexScenarios:
    """Test more complex real-world scenarios."""

    def test_full_ecommerce_model(self):
        """Test a complete e-commerce model setup."""

        class Base(DeclarativeBase):
            pass

        class User(Base, EnrichSQLAlchemyMixin):
            """User account in the system."""

            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True, info={"description": "User ID"})
            email: Mapped[str] = mapped_column(unique=True, info={"description": "Email address"})
            username: Mapped[str] = mapped_column(info={"description": "Display name"})
            password_hash: Mapped[str] = mapped_column(info={"exclude": True})
            created_at: Mapped[datetime] = mapped_column(
                info={"description": "Account creation time"}
            )
            is_active: Mapped[bool] = mapped_column(
                default=True, info={"description": "Account status"}
            )

            orders: Mapped[list["Order"]] = relationship(
                back_populates="user", info={"description": "Orders placed by this user"}
            )
            reviews: Mapped[list["Review"]] = relationship(
                back_populates="user", info={"description": "Product reviews by this user"}
            )

        class Product(Base, EnrichSQLAlchemyMixin):
            """Product in the catalog."""

            __tablename__ = "products"

            id: Mapped[int] = mapped_column(primary_key=True, info={"description": "Product ID"})
            name: Mapped[str] = mapped_column(info={"description": "Product name"})
            description: Mapped[str | None] = mapped_column(
                Text, nullable=True, info={"description": "Product description"}
            )
            price: Mapped[float] = mapped_column(info={"description": "Product price"})
            stock_quantity: Mapped[int] = mapped_column(info={"description": "Available stock"})

            reviews: Mapped[list["Review"]] = relationship(
                back_populates="product", info={"description": "Customer reviews"}
            )

        class Order(Base, EnrichSQLAlchemyMixin):
            """Customer order."""

            __tablename__ = "orders"

            id: Mapped[int] = mapped_column(primary_key=True, info={"description": "Order ID"})
            user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
            total_amount: Mapped[float] = mapped_column(info={"description": "Order total"})
            status: Mapped[str] = mapped_column(info={"description": "Order status"})
            created_at: Mapped[datetime] = mapped_column(info={"description": "Order date"})

            user: Mapped[User] = relationship(
                back_populates="orders", info={"description": "Customer who placed the order"}
            )

        class Review(Base, EnrichSQLAlchemyMixin):
            """Product review."""

            __tablename__ = "reviews"

            id: Mapped[int] = mapped_column(primary_key=True)
            user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
            product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
            rating: Mapped[int] = mapped_column(info={"description": "Rating 1-5"})
            comment: Mapped[str | None] = mapped_column(
                Text, nullable=True, info={"description": "Review text"}
            )

            user: Mapped[User] = relationship(back_populates="reviews")
            product: Mapped[Product] = relationship(back_populates="reviews")

        # Convert all models
        UserEnrichModel = User.__enrich_model__()
        ProductEnrichModel = Product.__enrich_model__()
        OrderEnrichModel = Order.__enrich_model__()
        ReviewEnrichModel = Review.__enrich_model__()

        # Verify User model
        user_fields = UserEnrichModel.model_fields
        assert "id" in user_fields
        assert "email" in user_fields
        assert "username" in user_fields
        assert "password_hash" not in user_fields  # Should be excluded
        assert "created_at" in user_fields
        assert "is_active" in user_fields
        assert "orders" in user_fields
        assert "reviews" in user_fields

        # Verify relationships are properly typed
        assert isinstance(user_fields["orders"].default, Relationship)
        assert isinstance(user_fields["reviews"].default, Relationship)

        # Verify Order model
        order_fields = OrderEnrichModel.model_fields
        assert "user" in order_fields
        assert isinstance(order_fields["user"].default, Relationship)

        # Verify all models are proper EnrichModels
        for model in [UserEnrichModel, ProductEnrichModel, OrderEnrichModel, ReviewEnrichModel]:
            assert issubclass(model, EnrichModel)
