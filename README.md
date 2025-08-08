# Full-Stack E-commerce Platform

![Project Screenshot](https://i.imgur.com/bLgBqK8.png)

This is a complete, full-stack e-commerce application built to demonstrate modern web development practices. It features a high-performance FastAPI backend, a dynamic and responsive React frontend (built with Vite), and real-time WebSocket notifications for a polished user experience.

---

## Core Features

-   **Product Catalog:** Browse a list of available products fetched from the backend.
-   **Dynamic Shopping Cart:** Add items to a cart that updates in real-time.
-   **Robust Checkout System:** Process orders, validate, and apply single-use discount codes.
-   **Automatic Discount Generation:** Every 3rd successful order automatically generates a new 10% discount code.
-   **Real-Time Notifications:** A new discount code is broadcast to all active users instantly via **WebSockets**, without needing a page refresh.
-   **Comprehensive Admin Dashboard:** View live store statistics, including total revenue, total items sold, and a list of all discount codes ever generated.
-   **Fully Tested Backend:** The API logic is validated by a comprehensive suite of **unit tests** using `pytest`, ensuring code quality and reliability.

---

## Technology Stack

-   **Backend:** **Python** with **FastAPI** (for high performance and automatic API documentation).
-   **Frontend:** **React** (built with **Vite** for a fast and modern development experience).
-   **Styling:** Plain **CSS Modules** for clean, scoped, and conflict-free styling.
-   **Real-time Communication:** **WebSockets**.
-   **Testing:** **Pytest** for backend unit testing.

---

## How to Run Locally

### Prerequisites
- Git
- Python 3.8+
- Node.js & npm

### Backend and frontend setup

```bash

Backend setup:
# Clone the repository and navigate into it
git clone [https://github.com/swaroopaloor/pro-ecommerce.git](https://github.com/swaroopaloor/pro-ecommerce.git)
cd pro-ecommerce/backend

# Create and activate a virtual environment
python -m venv venv
# On Windows: .\\venv\\Scripts\\activate
# On Mac/Linux: source venv/bin/activate

# Install dependencies
pip install fastapi "uvicorn[standard]" python-multipart jinja2 pytest httpx

# Run the server
uvicorn main:app --reload


# In a new terminal, navigate to the frontend directory
cd pro-ecommerce/frontend

# Install dependencies
npm install

# Run the application
npm run dev

The backend will be running at http://127.0.0.1:8000.
Access the interactive API documentation at http://127.0.0.1:8000/docs.


Frontend Setup:


# In a new terminal, navigate to the frontend directory
cd pro-ecommerce/frontend

# Install dependencies
npm install

# Run the application
npm run dev
The frontend will open automatically at http://localhost:5173 (or a similar port).

