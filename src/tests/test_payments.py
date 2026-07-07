import pytest
import pytest_asyncio
import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from models.users import UserModel
from models.orders import Order, OrderStatus
from models import Payment, PaymentStatus
from api.dependencies import get_payment_service

API_PREFIX = "/api/v1"


@pytest_asyncio.fixture(scope="function")
async def test_order(db_session: AsyncSession, test_user: UserModel) -> Order:
    order = Order(
        user_id=test_user.id,
        total_amount=Decimal("150.00"),
        status=OrderStatus.PENDING
    )
    db_session.add(order)
    await db_session.flush()
    await db_session.refresh(order)
    return order


@pytest.mark.asyncio
async def test_create_checkout_session_success(client: AsyncClient, test_order: Order):
    mock_url = "https://checkout.stripe.com/c/pay/cs_test_12345"
    mock_create_session = AsyncMock(return_value=mock_url)

    mock_payment_service = MagicMock()
    mock_payment_service.create_checkout_session = mock_create_session

    app.dependency_overrides[get_payment_service] = lambda: mock_payment_service

    try:
        payload = {"order_id": test_order.id}
        response = await client.post(f"{API_PREFIX}/payments/sessions", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["checkout_url"] == "https://checkout.stripe.com/c/pay/cs_test_12345"

        mock_create_session.assert_called_once_with(
            order_id=test_order.id,
            user_id=test_order.user_id
        )
    finally:
        app.dependency_overrides.pop(get_payment_service, None)


@pytest.mark.asyncio
async def test_create_checkout_session_invalid_status(client: AsyncClient, db_session: AsyncSession, test_order: Order):
    test_order.status = OrderStatus.PAID
    await db_session.flush()

    payload = {"order_id": test_order.id}
    response = await client.post(f"{API_PREFIX}/payments/sessions", json=payload)

    assert response.status_code == 400
    assert "This order cannot be paid anymore" in response.json()["detail"]["recommendation"]


@pytest.mark.asyncio
async def test_stripe_webhook_success(client: AsyncClient, db_session: AsyncSession, test_order: Order):
    webhook_payload = {
        "id": "evt_test_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_12345",
                "metadata": {
                    "order_id": str(test_order.id),
                    "user_id": str(test_order.user_id)
                }
            }
        }
    }

    with patch("stripe.Webhook.construct_event", return_value=webhook_payload):
        headers = {"Stripe-Signature": "t=123,v1=mock_signature"}
        response = await client.post(
            f"{API_PREFIX}/payments/webhook",
            content=json.dumps(webhook_payload),
            headers=headers
        )

        assert response.status_code == 200
        assert response.json() == {"status": "success"}


@pytest.mark.asyncio
async def test_get_payment_history(client: AsyncClient, db_session: AsyncSession, test_user: UserModel, test_order: Order):
    payment = Payment(
        user_id=test_user.id,
        order_id=test_order.id,
        amount=test_order.total_amount,
        status=PaymentStatus.SUCCESSFUL,
        external_payment_id="cs_test_999"
    )
    db_session.add(payment)
    await db_session.flush()

    response = await client.get(f"{API_PREFIX}/payments/history")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["order_id"] == test_order.id
    assert data[0]["amount"] == f"{test_order.total_amount:.2f}" or data[0]["amount"] == str(test_order.total_amount)


@pytest.mark.asyncio
async def test_admin_get_all_payments_denied_for_user(client: AsyncClient):
    response = await client.get(f"{API_PREFIX}/payments/admin/list")
    assert response.status_code in (401, 403)