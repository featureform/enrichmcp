# Examples

This page shows practical examples of using enrichmcp to build AI-ready APIs.

## Basic Book Catalog

A simple book catalog demonstrating core enrichmcp features:

```python
from datetime import date
from enrichmcp import EnrichMCP, EnrichModel, Relationship
from pydantic import Field

# Create the application
app = EnrichMCP(title="Book Catalog API", description="A simple book catalog for AI agents")


# Define entities
@app.entity
class Author(EnrichModel):
    """Represents a book author."""

    id: int = Field(description="Author ID")
    name: str = Field(description="Author's full name")
    bio: str = Field(description="Short biography")
    birth_date: date = Field(description="Date of birth")

    # Relationship to books
    books: list["Book"] = Relationship(description="Books written by this author")


@app.entity
class Book(EnrichModel):
    """Represents a book in the catalog."""

    id: int = Field(description="Book ID")
    title: str = Field(description="Book title")
    isbn: str = Field(description="ISBN-13")
    published: date = Field(description="Publication date")
    pages: int = Field(description="Number of pages")
    author_id: int = Field(description="Author ID")

    # Relationship to author
    author: Author = Relationship(description="Author of this book")


# Sample data
AUTHORS = [
    {"id": 1, "name": "Jane Doe", "bio": "Bestselling author", "birth_date": date(1975, 5, 15)},
    {
        "id": 2,
        "name": "John Smith",
        "bio": "Science fiction writer",
        "birth_date": date(1980, 3, 20),
    },
]

BOOKS = [
    {
        "id": 1,
        "title": "The Great Adventure",
        "isbn": "978-0-123456-78-9",
        "published": date(2020, 1, 1),
        "pages": 350,
        "author_id": 1,
    },
    {
        "id": 2,
        "title": "Mystery of the Stars",
        "isbn": "978-0-123456-79-6",
        "published": date(2021, 6, 15),
        "pages": 425,
        "author_id": 1,
    },
    {
        "id": 3,
        "title": "Future Worlds",
        "isbn": "978-0-123456-80-2",
        "published": date(2022, 3, 10),
        "pages": 512,
        "author_id": 2,
    },
]


# Define resolvers
@Author.books.resolver
async def get_author_books(author_id: int) -> list["Book"]:
    """Get all books by an author."""
    author_books = [book for book in BOOKS if book["author_id"] == author_id]
    return [Book(**book_data) for book_data in author_books]


@Book.author.resolver
async def get_book_author(book_id: int) -> "Author":
    """Get the author of a book."""
    book = next((b for b in BOOKS if b["id"] == book_id), None)
    if book:
        author_data = next((a for a in AUTHORS if a["id"] == book["author_id"]), None)
        if author_data:
            return Author(**author_data)

    # Return a default author if not found
    return Author(
        id=-1,
        name="Unknown Author",
        bio="Author information not available",
        birth_date=date(1900, 1, 1),
    )


# Define root resources
@app.retrieve
async def list_authors() -> list[Author]:
    """List all authors in the catalog."""
    return [Author(**author_data) for author_data in AUTHORS]


@app.retrieve
async def get_author(author_id: int) -> Author:
    """Get a specific author by ID."""
    author_data = next((a for a in AUTHORS if a["id"] == author_id), None)
    if author_data:
        return Author(**author_data)

    return Author(id=-1, name="Not Found", bio="Author not found", birth_date=date(1900, 1, 1))


@app.retrieve
async def list_books() -> list[Book]:
    """List all books in the catalog."""
    return [Book(**book_data) for book_data in BOOKS]


@app.retrieve
async def search_books(title_contains: str) -> list[Book]:
    """Search for books by title."""
    matching_books = [book for book in BOOKS if title_contains.lower() in book["title"].lower()]
    return [Book(**book_data) for book_data in matching_books]


# Run the server
if __name__ == "__main__":
    app.run()
```

## Task Management System

A todo/task management API showing nested relationships:

```python
from datetime import datetime
from enum import Enum
from enrichmcp import EnrichMCP, EnrichModel, Relationship
from pydantic import Field

app = EnrichMCP(
    title="Task Management API", description="Simple task tracking system for AI agents"
)


# Enums
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Status(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


# Entities
@app.entity
class Project(EnrichModel):
    """A project containing multiple tasks."""

    id: int = Field(description="Project ID")
    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    created_at: datetime = Field(description="Creation timestamp")
    due_date: datetime | None = Field(description="Project deadline")

    tasks: list["Task"] = Relationship(description="Tasks in this project")


@app.entity
class Task(EnrichModel):
    """An individual task or todo item."""

    id: int = Field(description="Task ID")
    title: str = Field(description="Task title")
    description: str = Field(description="Detailed description")
    project_id: int = Field(description="Parent project ID")
    priority: Priority = Field(description="Task priority level")
    status: Status = Field(description="Current status")
    created_at: datetime = Field(description="Creation timestamp")
    completed_at: datetime | None = Field(description="Completion timestamp")

    project: Project = Relationship(description="Project this task belongs to")


# Sample data
PROJECTS = [
    {
        "id": 1,
        "name": "Website Redesign",
        "description": "Redesign company website with new branding",
        "created_at": datetime(2024, 1, 1),
        "due_date": datetime(2024, 3, 1),
    },
    {
        "id": 2,
        "name": "Mobile App",
        "description": "Build mobile app for iOS and Android",
        "created_at": datetime(2024, 1, 15),
        "due_date": datetime(2024, 6, 1),
    },
]

TASKS = [
    {
        "id": 1,
        "title": "Design new homepage",
        "description": "Create mockups for new homepage design",
        "project_id": 1,
        "priority": Priority.HIGH,
        "status": Status.IN_PROGRESS,
        "created_at": datetime(2024, 1, 2),
        "completed_at": None,
    },
    {
        "id": 2,
        "title": "Update color scheme",
        "description": "Implement new brand colors across site",
        "project_id": 1,
        "priority": Priority.MEDIUM,
        "status": Status.TODO,
        "created_at": datetime(2024, 1, 3),
        "completed_at": None,
    },
    {
        "id": 3,
        "title": "Set up development environment",
        "description": "Configure React Native development environment",
        "project_id": 2,
        "priority": Priority.HIGH,
        "status": Status.DONE,
        "created_at": datetime(2024, 1, 16),
        "completed_at": datetime(2024, 1, 17),
    },
]


# Resolvers
@Project.tasks.resolver
async def get_project_tasks(project_id: int) -> list["Task"]:
    """Get all tasks for a project."""
    project_tasks = [task for task in TASKS if task["project_id"] == project_id]
    return [Task(**task_data) for task_data in project_tasks]


@Task.project.resolver
async def get_task_project(task_id: int) -> "Project":
    """Get the project a task belongs to."""
    task = next((t for t in TASKS if t["id"] == task_id), None)
    if task:
        project_data = next((p for p in PROJECTS if p["id"] == task["project_id"]), None)
        if project_data:
            return Project(**project_data)

    return Project(
        id=-1,
        name="Unknown Project",
        description="Project not found",
        created_at=datetime.now(),
        due_date=None,
    )


# Resources
@app.retrieve
async def list_projects() -> list[Project]:
    """List all projects."""
    return [Project(**project_data) for project_data in PROJECTS]


@app.retrieve
async def list_tasks(status: Status | None = None, priority: Priority | None = None) -> list[Task]:
    """List tasks with optional filtering."""
    filtered_tasks = TASKS

    if status:
        filtered_tasks = [t for t in filtered_tasks if t["status"] == status]

    if priority:
        filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority]

    return [Task(**task_data) for task_data in filtered_tasks]


@app.retrieve
async def get_project_summary(project_id: int) -> dict:
    """Get summary statistics for a project."""
    project_tasks = [t for t in TASKS if t["project_id"] == project_id]

    return {
        "project_id": project_id,
        "total_tasks": len(project_tasks),
        "completed_tasks": len([t for t in project_tasks if t["status"] == Status.DONE]),
        "high_priority_tasks": len([t for t in project_tasks if t["priority"] == Priority.HIGH]),
        "tasks_by_status": {
            status.value: len([t for t in project_tasks if t["status"] == status])
            for status in Status
        },
    }


if __name__ == "__main__":
    app.run()
```

## Recipe Collection

A recipe API demonstrating many-to-many style relationships:

```python
from enrichmcp import EnrichMCP, EnrichModel, Relationship
from pydantic import Field

app = EnrichMCP(title="Recipe API", description="A collection of recipes with ingredients")


@app.entity
class Recipe(EnrichModel):
    """A cooking recipe."""

    id: int = Field(description="Recipe ID")
    name: str = Field(description="Recipe name")
    description: str = Field(description="Brief description")
    prep_time: int = Field(description="Preparation time in minutes")
    cook_time: int = Field(description="Cooking time in minutes")
    servings: int = Field(description="Number of servings")
    instructions: str = Field(description="Step-by-step instructions")

    ingredients: list["Ingredient"] = Relationship(description="Ingredients used in this recipe")


@app.entity
class Ingredient(EnrichModel):
    """A cooking ingredient."""

    id: int = Field(description="Ingredient ID")
    name: str = Field(description="Ingredient name")
    category: str = Field(description="Ingredient category (vegetable, meat, etc)")

    recipes: list["Recipe"] = Relationship(description="Recipes that use this ingredient")


# Sample data
RECIPES = [
    {
        "id": 1,
        "name": "Spaghetti Carbonara",
        "description": "Classic Italian pasta dish",
        "prep_time": 10,
        "cook_time": 20,
        "servings": 4,
        "instructions": "1. Cook pasta\n2. Fry pancetta\n3. Mix eggs and cheese\n4. Combine",
    },
    {
        "id": 2,
        "name": "Caesar Salad",
        "description": "Fresh romaine with Caesar dressing",
        "prep_time": 15,
        "cook_time": 0,
        "servings": 2,
        "instructions": "1. Wash lettuce\n2. Make dressing\n3. Add croutons\n4. Toss and serve",
    },
]

INGREDIENTS = [
    {"id": 1, "name": "Spaghetti", "category": "pasta"},
    {"id": 2, "name": "Eggs", "category": "dairy"},
    {"id": 3, "name": "Pancetta", "category": "meat"},
    {"id": 4, "name": "Parmesan", "category": "dairy"},
    {"id": 5, "name": "Romaine Lettuce", "category": "vegetable"},
    {"id": 6, "name": "Croutons", "category": "bread"},
]

# Recipe-ingredient mappings
RECIPE_INGREDIENTS = {
    1: [1, 2, 3, 4],  # Carbonara uses spaghetti, eggs, pancetta, parmesan
    2: [5, 6, 4],  # Caesar uses romaine, croutons, parmesan
}


# Resolvers
@Recipe.ingredients.resolver
async def get_recipe_ingredients(recipe_id: int) -> list["Ingredient"]:
    """Get all ingredients for a recipe."""
    ingredient_ids = RECIPE_INGREDIENTS.get(recipe_id, [])
    ingredients = [ing for ing in INGREDIENTS if ing["id"] in ingredient_ids]
    return [Ingredient(**ing_data) for ing_data in ingredients]


@Ingredient.recipes.resolver
async def get_ingredient_recipes(ingredient_id: int) -> list["Recipe"]:
    """Get all recipes using an ingredient."""
    recipe_ids = [
        recipe_id
        for recipe_id, ingredients in RECIPE_INGREDIENTS.items()
        if ingredient_id in ingredients
    ]
    recipes = [recipe for recipe in RECIPES if recipe["id"] in recipe_ids]
    return [Recipe(**recipe_data) for recipe_data in recipes]


# Resources
@app.retrieve
async def list_recipes() -> list[Recipe]:
    """List all recipes."""
    return [Recipe(**recipe_data) for recipe_data in RECIPES]


@app.retrieve
async def search_recipes_by_ingredient(ingredient_name: str) -> list[Recipe]:
    """Find recipes containing a specific ingredient."""
    # Find ingredient
    ingredient = next(
        (ing for ing in INGREDIENTS if ingredient_name.lower() in ing["name"].lower()), None
    )

    if not ingredient:
        return []

    # Get recipes with this ingredient
    return await get_ingredient_recipes(ingredient["id"])


@app.retrieve
async def get_quick_recipes(max_time: int = 30) -> list[Recipe]:
    """Get recipes that can be made quickly."""
    quick_recipes = [
        recipe for recipe in RECIPES if (recipe["prep_time"] + recipe["cook_time"]) <= max_time
    ]
    return [Recipe(**recipe_data) for recipe_data in quick_recipes]


if __name__ == "__main__":
    app.run()
```

These examples demonstrate:
- Basic entity definition with `@app.entity`
- Relationship definition with `Relationship()`
- Resolver implementation with `@Entity.field.resolver`
- Resource creation with `@app.retrieve`
- Simple in-memory data storage
- Filtering and searching patterns

All using only the features that enrichmcp actually provides!

## SQLAlchemy Auto-Generation

The `examples/sqlalchemy_shop` project shows how `include_sqlalchemy_models`
can generate entities and resolvers directly from SQLAlchemy models. It works
with any async database backend supported by SQLAlchemy (for example
PostgreSQL with `asyncpg`).

The `examples/shop_api_gateway` project shows how EnrichMCP can act as a simple API gateway in front of another FastAPI service.
