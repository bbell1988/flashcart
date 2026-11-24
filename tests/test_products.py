from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_admin, register_and_login


async def test_list_products_is_public(client: AsyncClient):
    response = await client.get("/products")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_product_by_id_not_found_returns_404(client: AsyncClient):
    response = await client.get("/products/9999")
    assert response.status_code == 404


async def test_create_product_requires_admin_role(client: AsyncClient):
    """RBAC: a plain customer must be rejected with 403, not allowed to create products.

    This is the test that should fail loudly if the require_role('admin') dependency
    is ever accidentally removed from POST /products.
    """
    token = await register_and_login(client, "shopper@example.com", "pw", name="Shopper")
    response = await client.post(
        "/products",
        json={"name": "Sneaky Product", "price_cents": 100, "stock_qty": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


async def test_create_product_without_token_is_unauthorized(client: AsyncClient):
    response = await client.post(
        "/products", json={"name": "No Auth", "price_cents": 100, "stock_qty": 5}
    )
    assert response.status_code == 401


async def test_admin_can_create_and_fetch_product(client: AsyncClient, db_session: AsyncSession):
    token = await register_and_login(client, "admin1@example.com", "pw", name="Admin")
    await make_admin(db_session, "admin1@example.com")

    create_response = await client.post(
        "/products",
        json={"name": "Widget", "price_cents": 1500, "stock_qty": 20},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 200
    product = create_response.json()
    assert product["name"] == "Widget"
    assert product["stock_qty"] == 20

    fetch_response = await client.get(f"/products/{product['id']}")
    assert fetch_response.status_code == 200
    assert fetch_response.json()["id"] == product["id"]

    list_response = await client.get("/products")
    assert any(p["id"] == product["id"] for p in list_response.json())
