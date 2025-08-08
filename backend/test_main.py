# test_main.py
import pytest
from fastapi.testclient import TestClient
from main import app, DB, PRODUCTS

# --- Test Setup ---
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_database():
    """Resets the in-memory database before each test."""
    DB["cart"] = {}
    DB["orders"] = []
    DB["store_stats"] = {
        "items_purchased_count": 0,
        "total_purchase_amount": 0.0,
        "discount_codes_list": [],
        "total_discount_amount": 0.0,
    }
    DB["current_discount_code"] = None
    yield

# --- Test Cases ---

def test_get_all_products():
    response = client.get("/products")
    assert response.status_code == 200
    assert response.json() == PRODUCTS

def test_add_item_to_cart():
    response = client.post("/cart/add", json={"item_id": "item_001", "quantity": 2})
    assert response.status_code == 200
    assert DB["cart"] == {"item_001": 2}

def test_add_multiple_items_to_cart():
    client.post("/cart/add", json={"item_id": "item_001", "quantity": 1})
    client.post("/cart/add", json={"item_id": "item_002", "quantity": 3})
    client.post("/cart/add", json={"item_id": "item_001", "quantity": 1})
    assert DB["cart"] == {"item_001": 2, "item_002": 3}

def test_add_invalid_item_to_cart():
    response = client.post("/cart/add", json={"item_id": "invalid_item", "quantity": 1})
    assert response.status_code == 404
    assert "Item not found" in response.json()["detail"]

def test_checkout_with_empty_cart():
    # **BUG FIX**: Send an empty JSON body to prevent 422 error.
    response = client.post("/checkout", json={})
    assert response.status_code == 400
    assert "Cart is empty" in response.json()["detail"]

def test_successful_checkout_no_discount():
    client.post("/cart/add", json={"item_id": "item_001", "quantity": 2}) # 19.99 * 2 = 39.98
    
    # **BUG FIX**: Send an empty JSON body.
    response = client.post("/checkout", json={})
    assert response.status_code == 200
    assert "Checkout successful!" in response.json()["message"]
    
    order = response.json()["order_details"]
    assert order["total"] == 39.98
    assert not order["discount_applied"]
    
    assert DB["cart"] == {}
    
    stats = DB["store_stats"]
    assert stats["items_purchased_count"] == 2
    assert stats["total_purchase_amount"] == 39.98
    assert len(DB["orders"]) == 1

def test_discount_generation_and_usage():
    nth_order_value = DB["nth_order_value"]

    for _ in range(nth_order_value - 1):
        client.post("/cart/add", json={"item_id": "item_001", "quantity": 1})
        # **BUG FIX**: Send an empty JSON body.
        client.post("/checkout", json={})
    
    assert DB["current_discount_code"] is None

    client.post("/cart/add", json={"item_id": "item_002", "quantity": 1})
    # **BUG FIX**: Send an empty JSON body.
    checkout_response = client.post("/checkout", json={})
    
    assert checkout_response.status_code == 200
    assert DB["current_discount_code"] is not None
    generated_code = DB["current_discount_code"]
    assert len(DB["store_stats"]["discount_codes_list"]) == 1

    client.post("/cart/add", json={"item_id": "item_003", "quantity": 1}) # Price: 24.99
    
    final_checkout_response = client.post("/checkout", json={"discount_code": generated_code})
    
    assert final_checkout_response.status_code == 200
    order_details = final_checkout_response.json()["order_details"]
    
    assert order_details["discount_applied"] is True
    assert order_details["subtotal"] == 24.99
    assert order_details["discount_amount"] == 2.50
    assert order_details["total"] == 22.49
    
    assert DB["current_discount_code"] is None

def test_checkout_with_invalid_discount_code():
    DB["current_discount_code"] = "VALID-CODE"
    client.post("/cart/add", json={"item_id": "item_004", "quantity": 1}) # Price: 49.99
    
    response = client.post("/checkout", json={"discount_code": "INVALID-CODE"})
    
    assert response.status_code == 200
    order = response.json()["order_details"]
    
    assert not order["discount_applied"]
    assert order["total"] == 49.99
    
    assert DB["current_discount_code"] == "VALID-CODE"

def test_admin_stats_endpoint():
    client.post("/cart/add", json={"item_id": "item_001", "quantity": 1}) # 19.99
    client.post("/checkout", json={})
    
    client.post("/cart/add", json={"item_id": "item_002", "quantity": 2}) # 15.49 * 2 = 30.98
    client.post("/checkout", json={})
    
    client.post("/cart/add", json={"item_id": "item_003", "quantity": 1}) # 24.99
    client.post("/checkout", json={})
    
    generated_code = DB["current_discount_code"]
    client.post("/cart/add", json={"item_id": "item_004", "quantity": 1}) # 49.99
    client.post("/checkout", json={"discount_code": generated_code})
    
    response = client.get("/admin/stats")
    assert response.status_code == 200
    stats = response.json()
    
    assert stats["items_purchased_count"] == 1 + 2 + 1 + 1
    
    expected_revenue = 19.99 + 30.98 + 24.99 + (49.99 - 5.00)
    assert stats["total_purchase_amount"] == pytest.approx(expected_revenue)
    
    assert len(stats["discount_codes_list"]) == 1
    assert stats["total_discount_amount"] == 5.00
