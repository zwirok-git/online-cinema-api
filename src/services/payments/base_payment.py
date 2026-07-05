from abc import ABC, abstractmethod
from datetime import datetime

from models import Payment


class IPaymentService(ABC):
    @abstractmethod
    async def create_checkout_session(
        self, order_id: int, user_id: int
    ) -> str:
        pass

    @abstractmethod
    async def handle_webhook(self, payload: bytes, sig_header: str) -> bool:
        pass

    @abstractmethod
    async def get_user_history(self, user_id: int) -> list[Payment]:
        pass

    @abstractmethod
    async def get_all_payments_for_admin(
        self,
        user_id: int | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Payment]:
        pass
