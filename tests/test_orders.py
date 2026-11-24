from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_admin, register_and_login


async def _create_product(client: AsyncClient, db_session: AsyncSession, stock_qty: int = 10) -> dict:
    """Helper: register+promote an admin, create a product, return its JSON."""
    admin_token = await register_and_login(client, "product-admin@example.com", "pw", name="Admin")
    await make_admin(db_session, "product-admin@example.com")
    response = await client.post(
        "/products",
        json={"name": "Test Widget", "price_cents": 1000, "stock_qty": stock_qty},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return response.json()


async def test_place_order_happy_path_decrements_stock(client: AsyncClient, db_session: AsyncSession):
    product = await _create_product(client, db_session, stock_qty=10)
    customer_token = await register_and_login(client, "buyer@example.com", "pw", name="Buyer")

    response = await client.post(
        "/orders",
        json={"items": [{"product_id": product["id"], "quantity": 3}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 200
    order = response.json()
    assert order["status"] == "pending"
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 3
    assert order["items"][0]["price_at_purchase"] == 1000

    after = await client.get(f"/products/{product['id']}")
    assert after.json()["stock_qty"] == 7


async def test_place_order_insufficient_stock_leaves_db_unchanged(
    client: AsyncClient, db_session: AsyncSession
):
    """The core Task 9 requirement: a forced failure must not partially apply."""
    product = await _create_product(client, db_session, stock_qty=5)
    customer_token = await register_and_login(client, "overbuyer@example.com", "pw", name="Overbuyer")

    response = await client.post(
        "/orders",
        json={"items": [{"product_id": product["id"], "quantity": 999}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 400

    after = await client.get(f"/products/{product['id']}")
    assert after.json()["stock_qty"] == 5

    orders_response = await client.get(
        "/orders", headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert orders_response.json() == []


async def test_order_idor_other_user_cannot_view_order(client: AsyncClient, db_session: AsyncSession):
    """Insecure Direct Object Reference check: user B must not be able to view
    user A's order by ID, even with a valid token of their own."""
    product = await _create_product(client, db_session, stock_qty=10)
    token_a = await register_and_login(client, "ordera@example.com", "pw", name="UserA")
    token_b = await register_and_login(client, "orderb@example.com", "pw", name="UserB")

    place_response = await client.post(
        "/orders",
        json={"items": [{"product_id": product["id"], "quantity": 1}]},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    order_id = place_response.json()["id"]

    own_view = await client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert own_view.status_code == 200

    other_view = await client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert other_view.status_code == 404

    b_order_list = await client.get("/orders", headers={"Authorization": f"Bearer {token_b}"})
    assert b_order_list.json() == []


async def test_admin_sees_all_orders(client: AsyncClient, db_session: AsyncSession):
    product = await _create_product(client, db_session, stock_qty=10)
    customer_token = await register_and_login(client, "customerx@example.com", "pw", name="CustomerX")
    await client.post(
        "/orders",
        json={"items": [{"product_id": product["id"], "quantity": 1}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )

    admin_token = await register_and_login(client, "orders-admin@example.com", "pw", name="OrdersAdmin")
    await make_admin(db_session, "orders-admin@example.com")

    admin_orders = await client.get("/orders", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_orders.status_code == 200
    assert len(admin_orders.json()) >= 1
