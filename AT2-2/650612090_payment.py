from abc import ABC, abstractmethod

class PaymentDeclinedError(Exception):
    pass

class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount: float, currency: str) -> str: ...
    @abstractmethod
    def refund(self, transaction_id: str) -> None: ...

class SimplePayment(PaymentGateway):
    def charge(self, amount: float, currency: str) -> str:
        if amount <= 0:
            raise PaymentDeclinedError("invalid amount")
        if amount > 1000:
            raise PaymentDeclinedError("amount too high")
        return "tx-" + str(int(amount * 100))

    def refund(self, transaction_id: str) -> None:
        return
