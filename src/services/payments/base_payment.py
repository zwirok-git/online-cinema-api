from abc import ABC, abstractmethod


class IPaymentService(ABC):
    @abstractmethod
    async def create_checkout_session(
        self, order_id: int, user_id: int
    ) -> str:
        pass

    @abstractmethod
    async def handle_webhook(self, payload: bytes, sig_header: str) -> bool:
        pass
