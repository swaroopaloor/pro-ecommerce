# main.py
# --- Import necessary libraries ---
import uvicorn
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

# --- Application Setup ---
app = FastAPI(
    title="E-commerce API",
    description="A sophisticated API for an e-commerce store with real-time notifications.",
    version="1.0.0"
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---
class CartItem(BaseModel):
    item_id: str
    quantity: int

class CheckoutPayload(BaseModel):
    discount_code: Optional[str] = None

# --- In-Memory Database ---
PRODUCTS = {
    "item_001": {"name": "Quantum T-Shirt", "price": 19.99},
    "item_002": {"name": "Flux Capacitor Mug", "price": 15.49},
    "item_003": {"name": "Singularity Snapback", "price": 24.99},
    "item_004": {"name": "Code Weaver Hoodie", "price": 49.99},
}

DB = {
    "cart": {},
    "orders": [],
    "store_stats": {
        "items_purchased_count": 0,
        "total_purchase_amount": 0.0,
        "discount_codes_list": [],
        "total_discount_amount": 0.0,
    },
    "current_discount_code": None,
    "nth_order_value": 3
}

# --- WebSocket Manager ---
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

@app.get("/")
def read_root():
    return {"status": "E-commerce API is running"}

@app.get("/products")
def get_products():
    return PRODUCTS

@app.post("/cart/add")
def add_to_cart(item: CartItem):
    if item.item_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Item not found")
    
    current_quantity = DB["cart"].get(item.item_id, 0)
    DB["cart"][item.item_id] = current_quantity + item.quantity
    return {"message": f"Added {item.quantity} of {PRODUCTS[item.item_id]['name']} to cart.", "cart": DB["cart"]}

@app.get("/cart")
def get_cart():
    return DB["cart"]

@app.post("/checkout")
async def checkout(payload: CheckoutPayload):
    if not DB["cart"]:
        raise HTTPException(status_code=400, detail="Cart is empty")

    subtotal = sum(PRODUCTS[item_id]["price"] * quantity for item_id, quantity in DB["cart"].items())
    items_in_order = sum(DB["cart"].values())
    
    discount_amount = 0.0
    discount_applied = False

    # Validate discount code
    if payload.discount_code and payload.discount_code == DB["current_discount_code"]:
        # **BUG FIX**: Calculate and round the discount immediately for precision.
        discount_amount = round(subtotal * 0.10, 2)
        DB["current_discount_code"] = None  # Invalidate the code after use
        discount_applied = True

    # **BUG FIX**: Calculate final total using the potentially rounded discount.
    final_total = subtotal - discount_amount

    order = {
        "order_id": len(DB["orders"]) + 1,
        "items": DB["cart"].copy(),
        "subtotal": round(subtotal, 2),
        "discount_applied": discount_applied,
        "discount_amount": discount_amount, # Already rounded
        "total": round(final_total, 2)
    }
    DB["orders"].append(order)

    # Update stats
    stats = DB["store_stats"]
    stats["items_purchased_count"] += items_in_order
    # **BUG FIX**: Update stats with the final, rounded total for consistency.
    stats["total_purchase_amount"] += round(final_total, 2)
    if discount_applied:
        stats["total_discount_amount"] += discount_amount

    # Clear the cart
    DB["cart"] = {}

    # Check for discount code generation
    if len(DB["orders"]) % DB["nth_order_value"] == 0:
        new_code = f"SAVE10-{str(uuid.uuid4())[:4].upper()}"
        DB["current_discount_code"] = new_code
        stats["discount_codes_list"].append(new_code)
        await manager.broadcast(f"New Discount Code Available: {new_code}")

    return {"message": "Checkout successful!", "order_details": order}


@app.get("/admin/stats")
def get_store_stats():
    return DB["store_stats"]

@app.get("/admin/orders")
def get_all_orders():
    return DB["orders"]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")

