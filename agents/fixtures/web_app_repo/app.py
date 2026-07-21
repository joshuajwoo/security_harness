"""A simple FastAPI application with a health endpoint and items API.

The /health endpoint has a bug — it references an undefined variable.
"""

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Sample API")

# In-memory data store
items_db: dict[int, dict] = {
    1: {"name": "Widget", "price": 9.99},
    2: {"name": "Gadget", "price": 24.99},
    3: {"name": "Doohickey", "price": 4.99},
}


@app.get("/health")
def health_check():
    """Return the health status of the application.

    Should return {"status": "healthy", "version": "1.0.0"}.
    """
    # BUG: 'app_version' is not defined — should be a string literal
    return {"status": "healthy", "version": app_version}


@app.get("/items")
def list_items():
    """Return all items in the database."""
    return {"items": list(items_db.values()), "count": len(items_db)}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    """Return a specific item by ID."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


@app.post("/items")
def create_item(name: str, price: float):
    """Create a new item."""
    new_id = max(items_db.keys()) + 1 if items_db else 1
    items_db[new_id] = {"name": name, "price": price}
    return {"id": new_id, **items_db[new_id]}
