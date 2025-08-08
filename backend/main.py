# main.py
# --- Import necessary libraries ---
# FastAPI is the modern web framework we're using.
# Pydantic is used for data validation and settings management.
# Starlette provides WebSocket support.
# uvicorn is the server that will run our app.
import uvicorn
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

# --- Application Setup ---
# Create the main FastAPI application instance
app = FastAPI(
    title="E-commerce API",
    description="A sophisticated API for an e-commerce store with real-time notifications.",
    version="1.0.0"
)

# --- CORS (Cross-Origin Resource Sharing) Middleware ---
# This is crucial for allowing our React frontend (running on a different port)
# to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for simplicity. In production, you'd list your frontend's domain.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Data Models (using Pydantic) ---
# Using models ensures that the data we receive is in the correct format.
# This prevents many common bugs and is a professional best practice.

class CartItem(BaseModel):
    item_id: str
    quantity: int

class CheckoutPayload(BaseModel):
    discount_code: Optional[str] = None


# --- In-Memory Database ---
# As requested, we use a simple Python dictionary as our in-memory store.
# In a real-world application, this would be a database like PostgreSQL or MongoDB.
PRODUCTS = {
    "item_001": {"name": "Quantum T-Shirt", "price": 19.99},
    "item_002": {"name": "Flux Capacitor Mug", "price": 15.49},
    "item_003": {"name": "Singularity Snapback", "price": 24.99},
    "item_004": {"name": "Code Weaver Hoodie", "price": 49.99},
}

DB = {
    "cart": {}, # Key: item_id, Value: quantity
    "orders": [],
    "store_stats": {
        "items_purchased_count": 0,
        "total_purchase_amount": 0.0,
        "discount_codes_list": [],
        "total_discount_amount": 0.0,
    },
    "current_discount_code": None,
    "nth_order_value": 3 # For quicker testing, let's make it every 3rd order.
}

# --- WebSocket Manager for Real-time Notifications ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- API Endpoints ---

# This is a simple "health check" endpoint to see if the server is running.
@app.get("/")
def read_root():
    return {"status": "E-commerce API is running"}

# --- User-Facing Endpoints ---

@app.get("/products")
def get_products():
    """Returns a list of all available products."""
    return PRODUCTS

@app.post("/cart/add")
def add_to_cart(item: CartItem):
    """
    Adds a specified quantity of an item to the cart.
    If the item is already in the cart, it updates the quantity.
    """
    if item.item_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Item not found")
    
    current_quantity = DB["cart"].get(item.item_id, 0)
    DB["cart"][item.item_id] = current_quantity + item.quantity
    return {"message": f"Added {item.quantity} of {PRODUCTS[item.item_id]['name']} to cart.", "cart": DB["cart"]}

@app.get("/cart")
def get_cart():
    """Retrieves the current state of the shopping cart."""
    return DB["cart"]

@app.post("/checkout")
async def checkout(payload: CheckoutPayload):
    """
    Processes the checkout, validates discount codes, updates store stats,
    and clears the cart. If the order is the nth order, it triggers the
    generation of a new discount code.
    """
    if not DB["cart"]:
        raise HTTPException(status_code=400, detail="Cart is empty")

    subtotal = sum(PRODUCTS[item_id]["price"] * quantity for item_id, quantity in DB["cart"].items())
    items_in_order = sum(DB["cart"].values())
    
    discount_amount = 0.0
    final_total = subtotal
    discount_applied = False

    if payload.discount_code and payload.discount_code == DB["current_discount_code"]:
        discount_amount = subtotal * 0.10  # 10% discount
        final_total = subtotal - discount_amount
        DB["current_discount_code"] = None  # Invalidate the code after use
        discount_applied = True

    order = {
        "order_id": len(DB["orders"]) + 1,
        "items": DB["cart"].copy(),
        "subtotal": round(subtotal, 2),
        "discount_applied": discount_applied,
        "discount_amount": round(discount_amount, 2),
        "total": round(final_total, 2),
    }
    DB["orders"].append(order)

    # Update stats
    stats = DB["store_stats"]
    stats["items_purchased_count"] += items_in_order
    stats["total_purchase_amount"] += final_total
    if discount_applied:
        stats["total_discount_amount"] += discount_amount

    # Clear the cart
    DB["cart"] = {}

    # Check for discount code generation
    if len(DB["orders"]) % DB["nth_order_value"] == 0:
        new_code = f"SAVE10-{str(uuid.uuid4())[:4].upper()}"
        DB["current_discount_code"] = new_code
        stats["discount_codes_list"].append(new_code)
        # Broadcast the new code to all connected clients
        await manager.broadcast(f"New Discount Code Available: {new_code}")

    return {"message": "Checkout successful!", "order_details": order}

# --- Admin Endpoints ---

@app.get("/admin/stats")
def get_store_stats():
    """
    Returns a comprehensive overview of store statistics.
    """
    return DB["store_stats"]

@app.get("/admin/orders")
def get_all_orders():
    """
    Returns a list of all orders placed.
    """
    return DB["orders"]

# --- WebSocket Endpoint for Real-time ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # The server will just keep the connection alive.
            # It will only send data when the broadcast function is called.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")

# --- To run this app ---
# 1. Make sure you have python, pip, and virtualenv installed.
# 2. In your terminal, run:
#    pip install "fastapi[all]" uvicorn
# 3. Save this code as main.py
# 4. In your terminal, run:
#    uvicorn main:app --reload
# 5. Open your browser to http://127.0.0.1:8000/docs to see the interactive API documentation.
