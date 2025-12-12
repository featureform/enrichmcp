# Context Engine for Redis — GraphQL for AI Agents (Draft 0.5)

**Author:** Simba Khadder (@simba.khadder)
**Tagline:** A unified semantic data layer for structured and unstructured information — a "GraphQL for AI Agents" built on Redis Query Engine (RQE) and exposed via MCP.

**What it is:** A long‑running service that loads code‑defined schemas, materializes Redis (RQE) indexes, and exposes auto‑generated MCP tools that allow agents to discover, traverse, and query data semantically. It is the pane of glass agents use to access and create context.

## Product Vision

**Unified surface:** One interface/endpoint for agents to retrieve all the context they need to complete their tasks.

**Schema‑driven:** Developers declare entities and fields with semantic intent; the service compiles them to RQE and generates tools.

**Relationship‑aware:** Traversals maintain semantic context across the data graph.

**MCP‑native:** Exposed entirely as MCP tools with typed I/O, discoverable by agents.

Traditional APIs force AI agents to choose between:
- **Structured queries** (SQL-like): Fast but limited to exact matches and ranges
- **Unstructured search** (full-text, vector similarity): Flexible but lacks precision and relationships

**The Context Engine eliminates this choice**, providing a single interface where agents can:
- Search for "AI chip companies" (unstructured semantic) AND filter by "market cap > $100B" (structured)
- Find "companies similar to Apple" (unstructured vector similarity) AND "in the Technology sector" (structured categorical)
- Traverse relationships while maintaining search context across the entire data graph

## Architecture: Schema-Driven Context Engine

The Context Engine operates as a long-running service with three core responsibilities:

1. **Schema Compilation**: Load developer-defined entity schemas and compile them into optimized RQE indexes
2. **Data Materialization**: Populate Redis with structured and unstructured data through multiple ingestion pathways
3. **MCP Tool Generation**: Auto-generate typed MCP tools that expose semantic query capabilities to AI agents

**Data Flow:**
- AI Agent → MCP Protocol → Context Engine → RQE (Redis) → Structured + Unstructured Data
- Schema Definition → Index Compilation → Tool Generation → Agent Discovery

**Core Components:**
- **ContextSchema**: Developer-defined entity models with semantic field annotations
- **RQE Compiler**: Transforms schema definitions into Redis Search indexes
- **MCP Tool Generator**: Creates discoverable tools for each entity and relationship
- **Query Orchestrator**: Handles complex multi-entity queries with relationship traversal

## Schema-Driven Development: ContextSchema and EnrichField

The Context Engine uses a schema-first approach where developers define entities with semantic intent. The service compiles these schemas into RQE indexes and generates MCP tools automatically.

```python
from decimal import Decimal
from enrichmcp import ContextSchema, EnrichModel, EnrichField, Relationship, Embedding

schema = ContextSchema()

@schema.entity
class Stock(EnrichModel):
    """A publicly traded stock with rich semantic indexing for AI discovery."""

    # Primary key - generates exact lookup tools
    symbol: str = EnrichField(
        description="Stock ticker symbol like AAPL or TSLA",
        index="primary"  # → Generates: find_stocks_by_symbol(symbol)
    )

    # Structured numeric data - generates range query tools
    price: Decimal = EnrichField(
        description="Current stock price in USD",
        index="numeric"  # → Generates: find_stocks_in_price_range(min, max)
    )

    # Unstructured text data - generates full-text search tools
    name: str = EnrichField(
        description="Company name",
        index="text"  # → Generates: search_stocks_by_name(query)
    )

    # Unstructured vector data - generates semantic similarity tools
    description_embedding: Embedding = EnrichField(
        description="Business model and operations description",
        index="vector",
        vector_dim=1536,
        distance_metric="COSINE"  # → Generates: find_similar_stocks(stock_id)
    )

    # Hybrid indexing - generates multiple access patterns
    sector: str = EnrichField(
        description="Business sector like Technology or Healthcare",
        index=["tag", "text"]  # → Generates both exact and fuzzy matching
    )

    # Text-only unstructured data
    investment_thesis: str = EnrichField(
        description="Investment thesis and growth drivers",
        index=["text"]  # Keyword search only
    )

    # Relationships with foreign key specification
    earnings_reports: list["EarningsReport"] = Relationship(
        description="Quarterly earnings with financial metrics and narrative analysis",
        foreign_key="stock"  # → Generates: get_earnings_reports_for_stock(stock="AAPL")
    )

@schema.entity
class EarningsReport(EnrichModel):
    """Quarterly earnings combining structured metrics with unstructured insights."""

    # Full report content (not indexed by default)
    content: str = EnrichField(description="The full parsed text of the report")

    # Structured financial data
    revenue: Decimal = EnrichField(description="Revenue in millions", index="numeric")
    quarter: str = EnrichField(description="Quarter like Q3 2023", index="tag")

    # Unstructured narrative content with multiple indexes
    key_highlight: str = EnrichField(
        description="Main business achievements and developments",
        index=["text", "vector"]  # Both keyword search and semantic similarity
    )

    # Foreign key relationship
    stock: str = EnrichField(description="The company that reported these earnings")

# Compile schema and write to Redis
redis.write_schema("Stock Research API", "Semantic investment research for AI agents", schema)
```

## Data Ingestion: Three Pathways to Context Materialization

The Context Engine supports three distinct methods for populating the Redis-based context database, each optimized for different data sources and use cases:

### 1. RAG Pipeline Integration
**Best for**: Document processing, knowledge bases, content repositories

```python
# Documents are processed through RAG pipeline and materialized to Redis
@schema.ingest_pipeline
async def process_earnings_documents():
    """Process quarterly earnings PDFs into searchable context."""

    # RAG pipeline automatically:
    # 1. Extracts text from documents
    # 2. Chunks content semantically
    # 3. Generates vector embeddings
    # 4. Materializes to Redis using compiled schema indexes

    documents = await load_earnings_pdfs()
    for doc in documents:
        # Extract structured metadata
        metadata = extract_earnings_metadata(doc)

        # Process unstructured content
        chunks = semantic_chunker.chunk(doc.content)
        embeddings = await embedding_model.embed(chunks)

        # Materialize to Redis using schema-compiled indexes
        await context_engine.materialize_entity(
            entity_type="EarningsReport",
            entity_data={
                "quarter": metadata.quarter,      # Tag index
                "revenue": metadata.revenue,      # Numeric index
                "content": doc.content,           # Text index
                "key_highlight_embedding": embeddings[0]  # Vector index
            }
        )
```

### 2. RDI/ETL Batch Processing
**Best for**: Database synchronization, scheduled data updates, bulk imports

```python
# Redis Data Integration for batch processing
@schema.etl_job(schedule="0 2 * * *")  # Daily at 2 AM
async def sync_financial_data():
    """Sync financial database to Redis context store using compiled schema."""

    # ETL process handles:
    # 1. Extract from source databases
    # 2. Transform data according to schema definitions
    # 3. Materialize to Redis using compiled indexes

    # Extract from financial database
    stocks = await financial_db.get_all_stocks()
    earnings = await financial_db.get_recent_earnings()

    # Transform and materialize using schema
    for stock in stocks:
        # Generate embeddings for vector fields
        description_embedding = await embed_text(stock.description)

        # Materialize to Redis using schema-compiled indexes
        await context_engine.materialize_entity(
            entity_type="Stock",
            entity_data={
                "symbol": stock.symbol,                    # Primary index
                "price": stock.price,                      # Numeric index
                "name": stock.name,                        # Text index
                "sector": stock.sector,                    # Tag + text index
                "description_embedding": description_embedding,  # Vector index
                "investment_thesis": stock.investment_thesis     # Text index
            }
        )

    # Materialize earnings with foreign key relationships
    for earnings_report in earnings:
        await context_engine.materialize_entity(
            entity_type="EarningsReport",
            entity_data={
                "quarter": earnings_report.quarter,       # Tag index
                "revenue": earnings_report.revenue,       # Numeric index
                "content": earnings_report.content,       # Text index
                "stock": earnings_report.stock_symbol     # Foreign key
            }
        )
```

### 3. Lazy REST API Evaluation
**Best for**: External APIs, real-time data, on-demand enrichment

```python
# REST APIs are called lazily when MCP tools are invoked
@schema.lazy_resolver
async def get_real_time_market_data(symbol: str) -> dict:
    """Fetch live market data with Redis caching - auto-generates MCP tool."""

    # Check Redis cache first
    cached = await context_engine.get_cached(f"market_data:{symbol}")
    if cached and not is_stale(cached, ttl=60):  # 1 minute TTL
        return cached

    # Lazy evaluation: call external API
    market_api = get_market_api()
    live_data = await market_api.get_stock_data(symbol)

    # Enrich with semantic processing
    news_summary = await summarize_recent_news(live_data.news)
    sentiment_embedding = await embed_text(news_summary)

    enriched_data = {
        # Structured real-time data
        "price": live_data.current_price,
        "volume": live_data.volume,
        "change_percent": live_data.change_percent,

        # Unstructured enrichment
        "news_summary": news_summary,
        "sentiment_embedding": sentiment_embedding,
        "market_sentiment": analyze_sentiment(news_summary)
    }

    # Cache in Redis with TTL
    await context_engine.cache_with_ttl(
        key=f"market_data:{symbol}",
        data=enriched_data,
        ttl=60
    )

    return enriched_data

# Auto-generated MCP tool from lazy resolver
# Tool name: get_real_time_market_data
# Tool description: "Fetch live market data with Redis caching"
# Tool parameters: {"symbol": {"type": "string", "description": "Stock symbol"}}

# Usage: AI agents can discover and call this tool directly
# Agent: "Get real-time data for AAPL"
# → Calls get_real_time_market_data(symbol="AAPL")
# → Returns live market data with caching
```

## Auto-Generated MCP Tools: Discoverable Query Interface

From the schema definitions above, the Context Engine automatically generates comprehensive MCP tools that seamlessly blend structured and unstructured data access. These tools are discoverable by AI agents through the MCP protocol:

### Single-Dimension MCP Tools
```json
// Auto-generated MCP tools from schema compilation

// Primary key lookup tools
{
  "name": "find_stocks_by_symbol",
  "description": "Find stocks by ticker symbol",
  "inputSchema": {
    "type": "object",
    "properties": {
      "symbol": {"type": "string", "description": "Stock ticker symbol like AAPL or TSLA"}
    }
  }
}

// Numeric range query tools
{
  "name": "find_stocks_in_price_range",
  "description": "Find stocks within a price range",
  "inputSchema": {
    "type": "object",
    "properties": {
      "min_price": {"type": "number", "description": "Minimum price"},
      "max_price": {"type": "number", "description": "Maximum price"}
    }
  }
}

// Text search tools
{
  "name": "search_stocks_by_name",
  "description": "Search stocks by company name",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Search query for company names"}
    }
  }
}

// Vector similarity tools
{
  "name": "find_similar_stocks",
  "description": "Find stocks similar to a given stock",
  "inputSchema": {
    "type": "object",
    "properties": {
      "stock_symbol": {"type": "string", "description": "Reference stock symbol"},
      "limit": {"type": "integer", "description": "Maximum results to return"}
    }
  }
}
```

### Multi-Dimensional MCP Tools
The real power emerges when combining different data types in a single MCP tool:

```json
// Combined query tools auto-generated from schema relationships
{
  "name": "search_stocks_advanced",
  "description": "Advanced stock search combining multiple criteria",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name_query": {"type": "string", "description": "Text search in company names"},
      "description_query": {"type": "string", "description": "Text search in descriptions"},
      "similar_to_symbol": {"type": "string", "description": "Find stocks similar to this symbol"},
      "sector": {"type": "string", "description": "Filter by business sector"},
      "min_price": {"type": "number", "description": "Minimum stock price"},
      "max_price": {"type": "number", "description": "Maximum stock price"},
      "investment_style": {"type": "array", "items": {"type": "string"}, "description": "Investment style tags"},
      "limit": {"type": "integer", "default": 10, "description": "Maximum results"}
    }
  }
}

// Relationship traversal tools
{
  "name": "get_earnings_reports_for_stock",
  "description": "Get earnings reports for a specific stock",
  "inputSchema": {
    "type": "object",
    "properties": {
      "stock_symbol": {"type": "string", "description": "Stock ticker symbol"},
      "quarter_filter": {"type": "string", "description": "Filter by quarter like Q3 2023"},
      "min_revenue": {"type": "number", "description": "Minimum revenue filter"}
    }
  }
}

// Cross-entity semantic search
{
  "name": "find_investment_opportunities",
  "description": "Find stocks with earnings that match investment themes",
  "inputSchema": {
    "type": "object",
    "properties": {
      "theme": {"type": "string", "description": "Investment theme like 'AI breakthrough' or 'renewable energy'"},
      "min_similarity": {"type": "number", "default": 0.7, "description": "Minimum semantic similarity score"},
      "sector_filter": {"type": "array", "items": {"type": "string"}, "description": "Limit to specific sectors"}
    }
  }
}
```

## RQE-Powered Query Translation

Behind the scenes, EnrichMCP translates high-level semantic queries into optimized RQE commands that execute across multiple index types simultaneously:

### Query Translation Examples

```python
# AI Agent Request: "Find AI chip companies under $300"
semantic_query = {
    "description_query": "artificial intelligence chip semiconductor GPU",
    "max_price": 300,
    "sector": "Technology"
}

# EnrichMCP translates to RQE:
rqe_query = """
FT.SEARCH stocks_idx
"@description_vector:[KNN 50 $ai_vector]
 @price:[0 300]
 @sector:{Technology}"
PARAMS 2 ai_vector <embedding_blob>
SORTBY price ASC
LIMIT 0 10
"""

# AI Agent Request: "Show me earnings reports similar to NVIDIA's Q4 2024"
similarity_query = {
    "similar_to_earnings_id": 123,
    "min_similarity": 0.7,
    "min_revenue": 1000
}

# EnrichMCP translates to RQE:
rqe_query = """
FT.SEARCH earnings_idx
"@highlight_vector:[KNN 20 $nvidia_vector AS similarity_score]
 @revenue:[1000 +inf]"
PARAMS 2 nvidia_vector <nvidia_q4_embedding>
FILTER "@similarity_score >= 0.7"
SORTBY similarity_score DESC
"""
```

### Relationship-Aware Query Execution

EnrichMCP maintains semantic context across relationship traversals:

```python
# AI Agent: "Find technology stocks with recent earnings mentioning 'AI breakthrough'"
@app.retrieve
async def find_ai_breakthrough_stocks() -> list[Stock]:
    # Step 1: Find earnings reports with AI breakthrough mentions
    ai_earnings = await search_earnings_by_highlight(
        query="AI breakthrough artificial intelligence",
        date_range=("2024-01-01", None),  # Recent only
        min_similarity=0.8
    )

    # Step 2: Get related stocks, maintaining semantic context
    breakthrough_stocks = []
    for earnings in ai_earnings:
        stock = await earnings.stock  # Relationship traversal
        if stock.sector in ["Technology", "Semiconductors"]:
            breakthrough_stocks.append(stock)

    # Step 3: Rank by semantic similarity to "AI breakthrough" concept
    return await rank_by_similarity(
        breakthrough_stocks,
        concept="AI breakthrough innovation"
    )
```

## Context Engine: Redis-Powered Semantic Orchestration

The context engine leverages Redis as both the data store and intelligent caching layer, providing multi-level semantic query optimization and result caching.

### Redis-Based Intelligent Caching

The context engine uses Redis for sophisticated multi-level caching:

```python
@app.retrieve
async def semantic_stock_search(query: str, filters: dict) -> list[Stock]:
    ctx = app.get_context()

    # Redis cache for vector embeddings (global scope)
    embedding_key = f"embedding:{hash(query)}"
    query_embedding = await ctx.redis.get(embedding_key)

    if not query_embedding:
        query_embedding = await generate_embedding(query)
        # Cache embeddings with long TTL - they rarely change
        await ctx.redis.setex(embedding_key, 3600, pickle.dumps(query_embedding))

    # Redis cache for search results (user-scoped)
    user_id = ctx.get_user_id()
    cache_key = f"search:{user_id}:{hash(query)}:{hash(str(filters))}"

    cached_results = await ctx.redis.get(cache_key)
    if cached_results:
        results = pickle.loads(cached_results)
    else:
        # Execute semantic search using RQE
        results = await execute_rqe_semantic_search(query_embedding, filters)
        # Cache results with shorter TTL for freshness
        await ctx.redis.setex(cache_key, 300, pickle.dumps(results))

    await ctx.info(f"Semantic search for '{query}' returned {len(results)} results")
    return results
```

### Redis-Powered Cross-Entity Resolution

The context engine uses Redis to maintain semantic coherence across relationship traversals:

```python
@app.retrieve
async def find_investment_opportunities(theme: str) -> dict:
    """Find stocks and related earnings that match an investment theme."""
    ctx = app.get_context()

    # Redis cache for theme embeddings
    theme_key = f"theme_embedding:{hash(theme)}"
    theme_embedding = await ctx.redis.get(theme_key)

    if not theme_embedding:
        theme_embedding = await generate_embedding(f"investment theme: {theme}")
        await ctx.redis.setex(theme_key, 7200, pickle.dumps(theme_embedding))  # 2 hour TTL

    # Find stocks matching the theme using RQE vector search
    await ctx.report_progress(25, 100, "Finding thematic stocks")

    # RQE query for vector similarity with Redis
    rqe_query = f"""
    FT.SEARCH stocks_idx
    "@description_vector:[KNN 20 $theme_vector AS similarity_score]"
    PARAMS 2 theme_vector {theme_embedding.tobytes()}
    FILTER "@similarity_score >= 0.75"
    SORTBY similarity_score DESC
    """
    matching_stocks = await ctx.redis.ft("stocks_idx").search(rqe_query)

    # Find earnings reports that reinforce the theme
    await ctx.report_progress(50, 100, "Analyzing earnings narratives")
    thematic_earnings = []

    for stock in matching_stocks:
        # Use Redis to get related earnings efficiently
        earnings_key = f"stock_earnings:{stock.id}"
        earnings_ids = await ctx.redis.smembers(earnings_key)

        for earnings_id in earnings_ids:
            # Check cached similarity scores first
            similarity_key = f"similarity:{earnings_id}:{hash(theme)}"
            cached_similarity = await ctx.redis.get(similarity_key)

            if cached_similarity:
                similarity_score = float(cached_similarity)
            else:
                # Calculate and cache similarity
                earnings = await get_earnings_by_id(earnings_id)
                similarity_score = await calculate_vector_similarity(
                    earnings.key_highlight_embedding,
                    theme_embedding
                )
                await ctx.redis.setex(similarity_key, 1800, str(similarity_score))  # 30 min cache

            if similarity_score > 0.7:
                thematic_earnings.append({
                    "stock_id": stock.id,
                    "earnings_id": earnings_id,
                    "theme_alignment": similarity_score
                })

    await ctx.report_progress(100, 100, "Analysis complete")

    # Cache final results in Redis
    result = {
        "theme": theme,
        "matching_stocks": len(matching_stocks),
        "aligned_earnings": thematic_earnings,
        "confidence": calculate_theme_confidence(thematic_earnings)
    }

    result_key = f"investment_analysis:{hash(theme)}"
    await ctx.redis.setex(result_key, 600, pickle.dumps(result))  # 10 min cache

    return result
```

### Redis-Based Query Optimization

The context engine uses Redis to learn from query patterns and optimize future searches:

```python
@app.retrieve
async def adaptive_company_search(description: str) -> list[Stock]:
    """Search that adapts based on query patterns stored in Redis."""
    ctx = app.get_context()

    # Check Redis for cached query analysis
    analysis_key = f"query_analysis:{hash(description)}"
    query_type = await ctx.redis.get(analysis_key)

    if not query_type:
        query_type = await analyze_query_intent(description)
        # Cache query analysis for future use
        await ctx.redis.setex(analysis_key, 86400, query_type)  # 24 hour cache

    # Adapt RQE search strategy based on query type
    if query_type == "sector_focused":
        # Emphasize sector matching in RQE query
        rqe_query = f"""
        FT.SEARCH stocks_idx
        "(@description:{description}) | (@sector:{description})"
        SCORER TFIDF.DOCNORM
        WITHSCORES
        """
        results = await ctx.redis.ft("stocks_idx").search(rqe_query)

    elif query_type == "technology_focused":
        # Use specialized tech embeddings with Redis vector search
        tech_embedding_key = f"tech_embedding:{hash(description)}"
        tech_embedding = await ctx.redis.get(tech_embedding_key)

        if not tech_embedding:
            tech_embedding = await get_specialized_embedding(description, domain="technology")
            await ctx.redis.setex(tech_embedding_key, 3600, pickle.dumps(tech_embedding))
        else:
            tech_embedding = pickle.loads(tech_embedding)

        rqe_query = f"""
        FT.SEARCH stocks_idx
        "@description_vector:[KNN 10 $tech_vector]"
        PARAMS 2 tech_vector {tech_embedding.tobytes()}
        """
        results = await ctx.redis.ft("stocks_idx").search(rqe_query)
    else:
        # Standard balanced search using Redis full-text + vector
        embedding = await generate_embedding(description)
        rqe_query = f"""
        FT.SEARCH stocks_idx
        "((@description:{description}) => {{$weight: 0.4}} |
         (@description_vector:[KNN 10 $query_vector]) => {{$weight: 0.6}})"
        PARAMS 2 query_vector {embedding.tobytes()}
        """
        results = await ctx.redis.ft("stocks_idx").search(rqe_query)

    # Store search strategy performance metrics in Redis
    strategy_key = f"search_strategy:{hash(description)}"
    await ctx.redis.hset(strategy_key, mapping={
        "query_type": query_type,
        "result_count": len(results),
        "timestamp": time.time()
    })
    await ctx.redis.expire(strategy_key, 86400)  # 24 hour expiry

    return results
```

### Redis-Centric Lifespan Management

The lifespan system manages Redis connections and other resources:

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator, Any
import redis.asyncio as redis

@asynccontextmanager
async def lifespan(app: EnrichMCP) -> AsyncIterator[dict[str, Any]]:
    # Startup: Initialize Redis and other resources
    redis_client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=False,  # Keep binary for embeddings
        max_connections=20
    )

    # Initialize RQE indexes if they don't exist
    await setup_rqe_indexes(redis_client)

    market_api = MarketDataAPI(api_key=settings.api_key)

    try:
        # Yield context available in all requests
        yield {
            "redis": redis_client,
            "market_api": market_api
        }
    finally:
        # Cleanup: Close connections
        await redis_client.close()
        await market_api.close()

async def setup_rqe_indexes(redis_client):
    """Initialize Redis Search indexes for structured and unstructured data."""

    # Stock entity index with mixed data types
    stock_schema = [
        TextField("symbol", weight=2.0),           # Structured tag
        NumericField("price"),                     # Structured numeric
        TextField("name", weight=1.5),             # Unstructured text
        TextField("description"),                  # Unstructured text
        VectorField("description_vector",          # Unstructured vector
                   "HNSW", {
                       "TYPE": "FLOAT32",
                       "DIM": 1536,
                       "DISTANCE_METRIC": "COSINE"
                   })
    ]

    try:
        await redis_client.ft("stocks_idx").create_index(stock_schema)
    except Exception:
        pass  # Index already exists

# Create app with Redis-centric lifespan
app = EnrichMCP("Stock API", "Investment research", lifespan=lifespan)

@app.retrieve
async def get_real_time_price(symbol: str) -> Decimal:
    ctx = app.get_context()

    # Access Redis directly from lifespan context
    redis_client = ctx.request_context.lifespan_context["redis"]
    market_api = ctx.request_context.lifespan_context["market_api"]

    # Redis-based caching with TTL
    price_key = f"price:{symbol}"
    cached_price = await redis_client.get(price_key)

    if cached_price:
        return Decimal(cached_price.decode())

    # Fetch from external API
    price = await market_api.get_price(symbol)

    # Cache in Redis with 1 minute TTL
    await redis_client.setex(price_key, 60, str(price))

    return price
```

## The Future: GraphQL for AI Agents

The Context Engine represents a paradigm shift in how AI agents interact with data. By unifying structured and unstructured information into a single semantic interface exposed through MCP, it creates what we call **"GraphQL for AI Agents"** - a self-describing, discoverable, and traversable data layer that speaks the language of artificial intelligence.

### Key Benefits

1. **Structured + Unstructured Unification**: No more choosing between structured precision and unstructured flexibility
2. **Auto-Discovery**: AI agents can explore and understand your entire data model through introspection
3. **Relationship-Aware**: Maintain semantic context while traversing entity relationships
4. **Redis-Powered Performance**: RQE backend provides sub-millisecond queries across massive datasets
5. **Multiple Data Ingestion**: RAG pipelines, ETL processes, and lazy REST API evaluation
6. **Developer Friendly**: Declarative field definitions automatically generate comprehensive APIs

### Real-World Impact

This architecture enables AI agents to answer complex questions that previously required multiple API calls and manual data correlation:

- **"Find undervalued AI companies with strong earnings growth"** → Combines unstructured vector similarity, structured financial metrics, and categorical filtering in a single Redis query
- **"Show me companies similar to Tesla but in different sectors"** → Unstructured vector similarity with structured categorical exclusion
- **"Which earnings reports mention supply chain issues and how did it affect stock performance?"** → Unstructured text search with relationship traversal and structured numerical analysis
- **"Get real-time sentiment on renewable energy stocks"** → Lazy REST API evaluation with Redis caching and semantic processing

### The Path Forward

The Context Engine transforms data access from a technical challenge into a semantic conversation. AI agents no longer need to understand your API structure - your schema-compiled MCP tools explain themselves to AI agents, creating a truly symbiotic relationship between artificial intelligence and human-designed data systems.

**Key Innovations:**
- **Schema-First Development**: Define entities once, get comprehensive MCP tools automatically
- **Redis-Native Performance**: Sub-millisecond queries across structured and unstructured data
- **MCP-Native Discovery**: AI agents discover capabilities through standard MCP protocol
- **Relationship-Aware Traversal**: Maintain semantic context across entity boundaries
- **Multi-Modal Ingestion**: RAG pipelines, ETL processes, and lazy API evaluation

This is the future of AI-native data access: **schema-driven, MCP-native, Redis-powered, and infinitely discoverable**.
