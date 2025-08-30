# orders-service/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import pymysql

import requests

app = FastAPI(title="Orders Service")

MYSQL_USER = os.getenv("MYSQL_USER", "user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Pa55w0rd")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ordersdb")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))

USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8001/users/")
PRODUCTS_SERVICE_URL = os.getenv("PRODUCTS_SERVICE_URL", "http://localhost:8002/products/")

def get_conn():
    import logging
    logging.basicConfig(level=logging.INFO, force=True)
    logging.info(f"Connecting to database at {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE} as {MYSQL_USER}")
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        port=int(MYSQL_PORT),
        cursorclass=pymysql.cursors.DictCursor
    )


class Order(BaseModel):
    user_id: int
    product_id: str
    quantity: int

@app.post("/orders/")
def create_order(order: Order):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (user_id, product_id, quantity) VALUES (%s, %s, %s)",
        (order.user_id, order.product_id, order.quantity)
    )
    conn.commit()
    order_id = cur.lastrowid
    cur.close()
    conn.close()
    return {"id": order_id, "msg": "Order created"}

@app.get("/orders/")
def list_orders():
    try:
      conn = get_conn()
      cur = conn.cursor()
      cur.execute("SELECT id, user_id, product_id, quantity FROM orders")
      orders = cur.fetchall()
      cur.close()
      conn.close()
      return orders
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/user/{user_id}")
def get_orders_by_user(user_id: int):
    try:
    # 1. Obtener órdenes del usuario
      conn = get_conn()
      cur = conn.cursor()
      cur.execute("SELECT * FROM orders WHERE user_id = %s", (user_id,))
      orders = cur.fetchall()
      cur.close()
      conn.close()

      if not orders:
          return []

      # 2. Obtener nombre del usuario
      user_resp = requests.get(f"{USERS_SERVICE_URL}{user_id}")
      if user_resp.status_code != 200:
          user_name = None
      else:
          user_data = user_resp.json()
          user_name = user_data.get("name")

      # 3. Enriquecer cada orden con datos de producto
      enriched_orders = []
      for order in orders:
          product_id = order["product_id"]
          prod_resp = requests.get(f"{PRODUCTS_SERVICE_URL}{product_id}")
          if prod_resp.status_code == 200:
              product_data = prod_resp.json()
          else:
              product_data = {}

          enriched_orders.append({
              "order_id": order["id"],
              "user_id": order["user_id"],
              "user_name": user_name,
              "product_id": product_id,
              "product": product_data,
              "quantity": order.get("quantity"),
              "created_at": order.get("created_at")
          })

      return enriched_orders
    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))

