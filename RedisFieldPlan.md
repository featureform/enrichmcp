# Enhanced Field Implementation Plan

## Overview

This document provides a detailed implementation plan for enhancing the existing `Field` function with Redis search capabilities as the foundation of Redis search integration in EnrichMCP. This is Phase 1 of the Redis integration project and serves as the building block for all subsequent search functionality.

## Objectives

1. Enhance Pydantic's `Field` function with Redis search metadata through json_schema_extra
2. Ensure full backward compatibility with existing EnrichMCP patterns
3. Provide comprehensive test coverage for all field types and configurations
4. Create optional convenience functions for common search patterns
5. Establish the foundation for future Redis search features

## Implementation Tasks

### Task 1: Create Enhanced Field Module

**File: `src/enrichmcp/redis/__init__.py`**
```python
"""Redis search integration for EnrichMCP."""

from .field import TextSearch, TagFilter, VectorSearch, NumericSort, GeoSearch

__all__ = ["TextSearch", "TagFilter", "VectorSearch", "NumericSort", "GeoSearch"]
```

**File: `src/enrichmcp/redis/field.py`**

Create enhanced Field functions with the following requirements:

#### Core Enhanced Field Function
```python
def _create_search_field(
    *,
    description: str,
    search_type: Literal["text", "tag", "numeric", "geo", "vector"],
    search_config: dict,
    # Standard Pydantic field options
    default: Any = PydanticUndefined,
    json_schema_extra: dict | None = None,
    **kwargs
) -> Any:
    """Internal function to create fields with Redis search metadata."""

    # Merge search config with existing json_schema_extra
    extra = json_schema_extra or {}
    extra["redis_search"] = {
        "type": search_type,
        **search_config
    }

    return PydanticField(
        default=default,
        description=description,
        json_schema_extra=extra,
        **kwargs
    )
```

#### Convenience Functions
```python
def TextSearch(
    *,
    description: str,
    weight: float = 1.0,
    searchable: bool = True,
    no_stem: bool = False,
    phonetic_matcher: str | None = None,
    **kwargs
) -> Any:
    """Create a text-searchable field with full-text search capabilities."""

def TagFilter(
    *,
    description: str,
    filterable: bool = True,
    case_sensitive: bool = False,
    separator: str = ",",
    **kwargs
) -> Any:
    """Create a tag field for exact-match filtering and faceting."""

def VectorSearch(
    *,
    description: str,
    dims: int,
    algorithm: Literal["flat", "hnsw"] = "hnsw",
    distance_metric: Literal["cosine", "l2", "ip"] = "cosine",
    m: int = 16,
    ef_construction: int = 200,
    **kwargs
) -> Any:
    """Create a vector field for semantic similarity search."""

def NumericSort(
    *,
    description: str,
    sortable: bool = True,
    **kwargs
) -> Any:
    """Create a numeric field with sorting and range query capabilities."""

def GeoSearch(
    *,
    description: str,
    **kwargs
) -> Any:
    """Create a geo field for location-based search."""
```

#### Implementation Requirements

1. **Metadata Storage**: Store Redis search configuration in `json_schema_extra["redis_search"]`
2. **Parameter Validation**: Validate parameter combinations in each convenience function
3. **Backward Compatibility**: Regular `Field` continues to work unchanged
4. **Type Safety**: Proper type hints and runtime validation
5. **Documentation**: Comprehensive docstrings with examples for each function
6. **Flexibility**: Users can still use regular `Field` and add search metadata manually if needed

#### Metadata Structure
```python
# Expected metadata structure in json_schema_extra
{
    "redis_search": {
        "type": "text|tag|numeric|geo|vector",
        "searchable": bool,
        "weight": float,
        "no_stem": bool,
        "phonetic_matcher": str | None,
        "filterable": bool,
        "case_sensitive": bool,
        "separator": str,
        "sortable": bool,
        "dims": int | None,
        "algorithm": str,
        "distance_metric": str,
        "m": int,
        "ef_construction": int,
        "ef_runtime": int,
    }
}
```

### Task 2: Implementation Details

#### Core Function Implementation
```python
def _create_search_field(
    *,
    description: str,
    search_type: Literal["text", "tag", "numeric", "geo", "vector"],
    search_config: dict,
    default: Any = PydanticUndefined,
    json_schema_extra: dict | None = None,
    **kwargs
) -> Any:
    """Internal function to create fields with Redis search metadata."""

    # Merge search config with existing json_schema_extra
    extra = json_schema_extra or {}
    extra["redis_search"] = {
        "type": search_type,
        **search_config
    }

    return PydanticField(
        default=default,
        description=description,
        json_schema_extra=extra,
        **kwargs
    )

def TextSearch(
    *,
    description: str,
    weight: float = 1.0,
    searchable: bool = True,
    no_stem: bool = False,
    phonetic_matcher: str | None = None,
    **kwargs
) -> Any:
    """Create a text-searchable field with full-text search capabilities."""

    if weight <= 0:
        raise ValueError("weight must be positive")

    search_config = {
        "searchable": searchable,
        "weight": weight,
        "no_stem": no_stem,
        "phonetic_matcher": phonetic_matcher,
    }

    return _create_search_field(
        description=description,
        search_type="text",
        search_config=search_config,
        **kwargs
    )

def VectorSearch(
    *,
    description: str,
    dims: int,
    algorithm: Literal["flat", "hnsw"] = "hnsw",
    distance_metric: Literal["cosine", "l2", "ip"] = "cosine",
    m: int = 16,
    ef_construction: int = 200,
    **kwargs
) -> Any:
    """Create a vector field for semantic similarity search."""

    if dims <= 0:
        raise ValueError("dims must be positive")
    if algorithm == "hnsw" and m <= 0:
        raise ValueError("m must be positive for HNSW algorithm")

    search_config = {
        "dims": dims,
        "algorithm": algorithm,
        "distance_metric": distance_metric,
        "m": m,
        "ef_construction": ef_construction,
    }

    return _create_search_field(
        description=description,
        search_type="vector",
        search_config=search_config,
        **kwargs
    )
```

### Task 3: Error Handling

Each convenience function implements validation with clear error messages:
- `TextSearch`: Validates weight > 0
- `VectorSearch`: Validates dims > 0, HNSW parameters
- `TagFilter`: Validates separator is non-empty string
- `NumericSort`: Basic parameter validation
- `GeoSearch`: Coordinate validation (future)

### Task 4: Documentation

Create comprehensive documentation including:
- Parameter reference for each convenience function
- Usage examples comparing regular Field vs search functions
- Best practices for choosing between different search types
- Performance considerations for each search type
- Examples showing backward compatibility

## Test Implementation Plan

### Test File Structure
```
tests/redis/
├── __init__.py
├── test_search_fields.py
├── conftest.py
└── fixtures/
    └── sample_models.py
```

### Test Categories

#### 1. Basic Field Creation Tests
**File: `tests/redis/test_search_fields.py`**

```python
class TestSearchFieldBasics:
    def test_regular_field_unchanged(self):
        """Test regular Field continues to work unchanged."""

    def test_search_field_metadata_structure(self):
        """Test search metadata is properly stored in json_schema_extra."""

    def test_search_field_preserves_pydantic_options(self):
        """Test that standard Pydantic Field options work with search fields."""

    def test_search_field_merges_json_schema_extra(self):
        """Test search metadata merges with existing json_schema_extra."""
```

#### 2. Convenience Function Tests
```python
class TestTextSearch:
    def test_text_search_basic(self):
        """Test basic TextSearch field creation."""

    def test_text_search_with_weight(self):
        """Test TextSearch with custom weight."""

    def test_text_search_with_phonetic_matcher(self):
        """Test TextSearch with phonetic matching."""

    def test_text_search_validation_errors(self):
        """Test validation errors for invalid TextSearch configs."""

class TestTagFilter:
    def test_tag_filter_basic(self):
        """Test basic TagFilter field creation."""

    def test_tag_filter_custom_separator(self):
        """Test TagFilter with custom separator."""

    def test_tag_filter_case_sensitive(self):
        """Test case-sensitive TagFilter."""

class TestNumericSort:
    def test_numeric_sort_basic(self):
        """Test basic NumericSort field creation."""

    def test_numeric_sort_options(self):
        """Test NumericSort with various options."""

class TestVectorSearch:
    def test_vector_search_basic(self):
        """Test basic VectorSearch field creation."""

    def test_vector_search_hnsw_params(self):
        """Test VectorSearch with HNSW parameters."""

    def test_vector_search_missing_dims_error(self):
        """Test error when dims not specified for VectorSearch."""

class TestGeoSearch:
    def test_geo_search_basic(self):
        """Test basic GeoSearch field creation."""
```

#### 3. Pydantic Integration Tests
```python
class TestPydanticIntegration:
    def test_search_fields_in_model(self):
        """Test search fields work in Pydantic models."""

    def test_model_with_mixed_fields(self):
        """Test model with both search fields and regular Field."""

    def test_model_serialization(self):
        """Test model serialization excludes search metadata."""

    def test_model_validation(self):
        """Test Pydantic validation works normally."""

    def test_field_metadata_preservation(self):
        """Test search metadata is preserved in model_fields."""
```

#### 4. Error Handling Tests
```python
class TestErrorHandling:
    def test_text_search_invalid_weight(self):
        """Test error for invalid weight values in TextSearch."""

    def test_vector_search_invalid_dims(self):
        """Test error when VectorSearch has invalid dims."""

    def test_vector_search_invalid_hnsw_params(self):
        """Test errors for invalid HNSW parameters."""

    def test_tag_filter_invalid_separator(self):
        """Test error for invalid separator in TagFilter."""
```

#### 5. Edge Cases and Complex Scenarios
```python
class TestEdgeCases:
    def test_all_search_types_in_model(self):
        """Test model with all search field types."""

    def test_json_schema_extra_merge(self):
        """Test merging search metadata with existing json_schema_extra."""

    def test_nested_model_search_fields(self):
        """Test search fields in nested models."""

    def test_inheritance_scenarios(self):
        """Test search fields in model inheritance."""

    def test_backward_compatibility(self):
        """Test that existing Field usage is unaffected."""
```

### Test Fixtures

**File: `tests/redis/conftest.py`**
```python
import pytest
from pydantic import BaseModel, Field
from enrichmcp.redis import TextSearch, TagFilter, VectorSearch, NumericSort

@pytest.fixture
def sample_text_field():
    """Sample text search field."""
    return TextSearch(
        description="Sample text field",
        weight=2.0
    )

@pytest.fixture
def sample_model_class():
    """Sample model class with search fields."""
    class SampleModel(BaseModel):
        # Regular field (unchanged)
        id: str = Field(description="Document ID")

        # Search fields
        title: str = TextSearch(
            description="Document title",
            weight=2.0
        )
        category: str = TagFilter(
            description="Document category"
        )
        price: float = NumericSort(
            description="Item price"
        )
        embedding: list[float] = VectorSearch(
            description="Content embedding",
            dims=1536
        )

    return SampleModel
```

**File: `tests/redis/fixtures/sample_models.py`**
```python
"""Sample models for testing search field functionality."""

from pydantic import BaseModel, Field
from enrichmcp.redis import TextSearch, TagFilter, VectorSearch, NumericSort

class DocumentModel(BaseModel):
    """Sample document model with various field types."""

    # Regular field (no search capabilities)
    id: str = Field(description="Document ID")

    # Search fields using convenience functions
    title: str = TextSearch(
        description="Document title",
        weight=3.0
    )

    content: str = TextSearch(
        description="Document content",
        weight=1.0
    )

    tags: list[str] = TagFilter(
        description="Document tags",
        separator=","
    )

    created_timestamp: int = NumericSort(
        description="Creation timestamp"
    )

    embedding: list[float] = VectorSearch(
        description="Document embedding",
        dims=1536,
        algorithm="hnsw",
        distance_metric="cosine"
    )

class MixedFieldModel(BaseModel):
    """Model showing regular Field and search fields together."""

    # Regular fields
    id: str = Field(description="ID")
    created_at: str = Field(description="Creation date")

    # Search fields
    name: str = TextSearch(description="Name", weight=2.0)
    category: str = TagFilter(description="Category")

    # Regular field with manual search metadata (advanced usage)
    description: str = Field(
        description="Description",
        json_schema_extra={
            "redis_search": {
                "type": "text",
                "searchable": True,
                "weight": 1.0
            }
        }
    )
```

## Test Execution Strategy

### Phase 1: Core Functionality
1. Run basic field creation tests
2. Verify metadata structure and storage
3. Test parameter validation
4. Ensure backward compatibility

### Phase 2: Integration Testing
1. Test RedisField in Pydantic models
2. Verify serialization behavior
3. Test complex field combinations
4. Validate error handling

### Phase 3: Edge Cases
1. Test all parameter combinations
2. Verify inheritance scenarios
3. Test performance with large models
4. Validate memory usage

### Test Commands
```bash
# Run all search field tests
pytest tests/redis/test_search_fields.py -v

# Run with coverage
pytest tests/redis/test_search_fields.py --cov=src/enrichmcp/redis/field --cov-report=html

# Run specific test categories
pytest tests/redis/test_search_fields.py::TestTextSearch -v
pytest tests/redis/test_search_fields.py::TestPydanticIntegration -v

# Run performance tests
pytest tests/redis/test_search_fields.py::TestEdgeCases::test_backward_compatibility -v
```

## Success Criteria

### Functional Requirements
- [ ] Search convenience functions create valid Pydantic Field objects
- [ ] All search metadata correctly stored in json_schema_extra
- [ ] Parameter validation works for all convenience functions
- [ ] Backward compatibility maintained (regular Field unchanged)
- [ ] Error messages are clear and helpful
- [ ] Manual search metadata via json_schema_extra still works

### Quality Requirements
- [ ] 100% test coverage on all convenience functions
- [ ] All edge cases covered with tests
- [ ] Performance equivalent to regular Field
- [ ] Memory usage reasonable for large models
- [ ] Documentation complete with examples for each function

### Integration Requirements
- [ ] Works in EnrichModel classes
- [ ] Compatible with existing EnrichMCP patterns
- [ ] Serialization excludes search metadata appropriately
- [ ] Field metadata accessible for future schema generation
- [ ] Mixed usage (regular Field + search fields) works seamlessly

## Implementation Notes

### Development Environment Setup
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests during development
pytest tests/redis/test_search_fields.py --watch

# Type checking
mypy src/enrichmcp/redis/field.py

# Linting
ruff check src/enrichmcp/redis/field.py
```

### Code Quality Standards
- Follow existing EnrichMCP code style
- Use type hints throughout
- Comprehensive docstrings with examples
- Clear error messages with actionable guidance
- Performance considerations for large-scale usage

### Documentation Requirements
- Function docstrings with all parameters documented for each convenience function
- Usage examples comparing regular Field vs search convenience functions
- Best practices for choosing between different search types
- Performance and memory considerations
- Integration examples with EnrichModel
- Backward compatibility examples

## Usage Examples

### Basic Usage
```python
from pydantic import BaseModel, Field
from enrichmcp.redis import TextSearch, TagFilter, VectorSearch

class Article(BaseModel):
    # Regular fields (no search)
    id: str = Field(description="Article ID")
    created_at: str = Field(description="Creation timestamp")

    # Search fields
    title: str = TextSearch(description="Article title", weight=2.0)
    content: str = TextSearch(description="Article content", weight=1.0)
    category: str = TagFilter(description="Article category")
    tags: list[str] = TagFilter(description="Article tags", separator=",")
    embedding: list[float] = VectorSearch(description="Content embedding", dims=1536)
```

### Advanced Usage (Manual Metadata)
```python
class Document(BaseModel):
    # Convenience function
    title: str = TextSearch(description="Title", weight=2.0)

    # Manual metadata (for advanced cases)
    content: str = Field(
        description="Content",
        json_schema_extra={
            "redis_search": {
                "type": "text",
                "searchable": True,
                "weight": 1.0,
                "no_stem": True
            }
        }
    )
```

## Next Steps After Completion

Once search field functions are implemented and tested:

1. **Field Detection Methods**: Add methods to detect and extract Redis search fields from models
2. **Schema Generation**: Create functions to generate Redis search schemas from field metadata
3. **Mock Redis Interface**: Implement abstract interface for Redis operations
4. **RedisModel Extension**: Extend EnrichModel with Redis search capabilities
5. **Integration Testing**: Test complete flow with real Redis instance

This foundation will enable all subsequent Redis search functionality while maintaining EnrichMCP's principles of type safety, backward compatibility, and developer experience.
