import React, { useState, useEffect, useRef } from 'react';
import styles from './App.module.css'; // Correctly importing the CSS Module

// --- Configuration ---
const API_URL = 'http://127.0.0.1:8000';
const WEBSOCKET_URL = 'ws://127.0.0.1:8000/ws';

// --- Helper Components ---
const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const typeClass = {
    success: styles.toastSuccess,
    error: styles.toastError,
    info: styles.toastInfo,
  };

  return (
    <div className={`${styles.toast} ${typeClass[type]}`}>
      <span>{message}</span>
      <button onClick={onClose}>X</button>
    </div>
  );
};

const Spinner = () => (
  <div className={styles.spinnerContainer}>
    <div className={styles.spinner}></div>
  </div>
);

// --- Main Application Components ---
const ProductList = ({ products, onAddToCart, loading }) => (
  <div className={styles.card}>
    <h2 className={styles.cardTitle}>Our Products</h2>
    {loading ? <Spinner /> : (
      <div className={styles.productList}>
        {Object.entries(products).map(([id, product]) => (
          <div key={id} className={styles.productItem}>
            <div>
              <p className={styles.productName}>{product.name}</p>
              <p className={styles.productPrice}>${product.price.toFixed(2)}</p>
            </div>
            <button
              onClick={() => onAddToCart(id)}
              className={styles.button}
            >
              Add to Cart
            </button>
          </div>
        ))}
      </div>
    )}
  </div>
);

const Cart = ({ cart, products, onCheckout, discountCode, setDiscountCode, lastOrder }) => {
  const cartItems = Object.entries(cart);

  if (cartItems.length === 0) {
    return (
      <div className={styles.card}>
        <h2 className={styles.cardTitle}>Shopping Cart</h2>
        <p className={styles.emptyCartMessage}>Your cart is empty.</p>
        {lastOrder && (
            <div className={styles.lastOrderInfo}>
                <h3>Last Order Placed Successfully!</h3>
                <p>Order ID: {lastOrder.order_id}</p>
                <p>Total: ${lastOrder.total.toFixed(2)}</p>
            </div>
        )}
      </div>
    );
  }

  const subtotal = cartItems.reduce((acc, [id, quantity]) => {
    return acc + (products[id]?.price || 0) * quantity;
  }, 0);

  return (
    <div className={styles.card}>
      <h2 className={styles.cardTitle}>Shopping Cart</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {cartItems.map(([id, quantity]) => (
          <div key={id} className={styles.cartItem}>
            <p>{products[id]?.name || 'Unknown Item'} x {quantity}</p>
            <p>${((products[id]?.price || 0) * quantity).toFixed(2)}</p>
          </div>
        ))}
      </div>
      <div className={styles.cartSubtotal}>
        <span>Subtotal</span>
        <span>${subtotal.toFixed(2)}</span>
      </div>
      <div style={{ marginTop: '1rem' }}>
        <input
          type="text"
          value={discountCode}
          onChange={(e) => setDiscountCode(e.target.value)}
          placeholder="Enter discount code"
          className={styles.inputField}
        />
        <button
          onClick={onCheckout}
          className={`${styles.button} ${styles.buttonSuccess}`}
        >
          Checkout
        </button>
      </div>
    </div>
  );
};

const AdminPanel = ({ stats, orders, loading }) => (
  <div className={`${styles.card} ${styles.adminPanel}`}>
    <h2 className={styles.cardTitle}>Admin Panel</h2>
    {loading ? <Spinner /> : (
      <>
        <div className={styles.statsGrid}>
          <div className={styles.statCard}>
            <p className={styles.statLabel}>Total Revenue</p>
            <p className={styles.statValue}>${stats.total_purchase_amount?.toFixed(2) || '0.00'}</p>
          </div>
          <div className={styles.statCard}>
            <p className={styles.statLabel}>Items Sold</p>
            <p className={styles.statValue}>{stats.items_purchased_count || 0}</p>
          </div>
          <div className={styles.statCard}>
            <p className={styles.statLabel}>Discounts Given</p>
            <p className={styles.statValue}>${stats.total_discount_amount?.toFixed(2) || '0.00'}</p>
          </div>
          <div className={styles.statCard}>
            <p className={styles.statLabel}>Total Orders</p>
            <p className={styles.statValue}>{orders.length || 0}</p>
          </div>
        </div>
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#9ca3af', marginBottom: '0.5rem' }}>Discount Codes Issued</h3>
          <div className={styles.discountCodeList}>
            {stats.discount_codes_list?.length > 0 ? (
              <div>
                {stats.discount_codes_list.map(code => (
                  <span key={code} className={styles.discountCode}>{code}</span>
                ))}
              </div>
            ) : (
              <p className={styles.emptyCartMessage}>No codes issued yet.</p>
            )}
          </div>
        </div>
      </>
    )}
  </div>
);

// --- Main App Component ---
export default function App() {
  const [products, setProducts] = useState({});
  const [cart, setCart] = useState({});
  const [stats, setStats] = useState({});
  const [orders, setOrders] = useState([]);
  const [discountCode, setDiscountCode] = useState('');
  const [lastOrder, setLastOrder] = useState(null);
  const [toast, setToast] = useState(null);
  const [loading, setLoading] = useState({ products: true, stats: true });
  
  const ws = useRef(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(prev => ({ ...prev, products: true, stats: true }));
        const [productsRes, cartRes, statsRes, ordersRes] = await Promise.all([
          fetch(`${API_URL}/products`),
          fetch(`${API_URL}/cart`),
          fetch(`${API_URL}/admin/stats`),
          fetch(`${API_URL}/admin/orders`),
        ]);
        setProducts(await productsRes.json());
        setCart(await cartRes.json());
        setStats(await statsRes.json());
        setOrders(await ordersRes.json());
      } catch (error) {
        setToast({ message: 'Failed to fetch initial data.', type: 'error' });
      } finally {
        setLoading({ products: false, stats: false });
      }
    };
    fetchData();

    ws.current = new WebSocket(WEBSOCKET_URL);
    ws.current.onmessage = (event) => {
      setToast({ message: event.data, type: 'info' });
      fetchAdminStats(); 
    };

    return () => ws.current?.close();
  }, []);

  const fetchAdminStats = async () => {
    try {
      setLoading(prev => ({ ...prev, stats: true }));
      const [statsRes, ordersRes] = await Promise.all([
        fetch(`${API_URL}/admin/stats`),
        fetch(`${API_URL}/admin/orders`),
      ]);
      setStats(await statsRes.json());
      setOrders(await ordersRes.json());
    } catch (error) {
       setToast({ message: 'Failed to update admin stats.', type: 'error' });
    } finally {
      setLoading(prev => ({ ...prev, stats: false }));
    }
  };

  const handleAddToCart = async (itemId) => {
    try {
      const response = await fetch(`${API_URL}/cart/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId, quantity: 1 }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);
      setCart(data.cart);
      setToast({ message: `Added ${products[itemId].name} to cart.`, type: 'success' });
    } catch (error) {
      setToast({ message: error.message, type: 'error' });
    }
  };

  const handleCheckout = async () => {
    try {
      const response = await fetch(`${API_URL}/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ discount_code: discountCode }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);
      
      setToast({ message: 'Checkout successful!', type: 'success' });
      setCart({});
      setDiscountCode('');
      setLastOrder(data.order_details);
      fetchAdminStats();
    } catch (error)
 {
      setToast({ message: error.message, type: 'error' });
    }
  };

  return (
    <div className={styles.appContainer}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <header className={styles.header}>
        <h1>E-commerce Dashboard</h1>
        <p>A sophisticated storefront powered by FastAPI and React.</p>
      </header>
      
      <main className={styles.mainGrid}>
        <ProductList products={products} onAddToCart={handleAddToCart} loading={loading.products} />
        <Cart cart={cart} products={products} onCheckout={handleCheckout} discountCode={discountCode} setDiscountCode={setDiscountCode} lastOrder={lastOrder} />
      </main>
      
      <AdminPanel stats={stats} orders={orders} loading={loading.stats} />
    </div>
  );
}
