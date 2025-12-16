from abc import ABC, abstractmethod

class InventoryError(Exception):
    pass

class InventoryRepository(ABC):
    @abstractmethod
    def add_stock(self, sku: str, qty: int) -> None: ...
    @abstractmethod
    def get_stock(self, sku: str) -> int: ...
    @abstractmethod
    def reserve(self, sku: str, qty: int) -> None: ...
    @abstractmethod
    def release(self, sku: str, qty: int) -> None: ...

class InMemoryInventory(InventoryRepository):
    def __init__(self):
        self._stock = {}

    def add_stock(self, sku: str, qty: int) -> None:
        if qty < 0:
            raise InventoryError("qty must be >= 0")
        self._stock[sku] = self._stock.get(sku, 0) + qty

    def get_stock(self, sku: str) -> int:
        return self._stock.get(sku, 0)

    def reserve(self, sku: str, qty: int) -> None:
        if qty <= 0:
            raise InventoryError("qty must be > 0")
        cur = self._stock.get(sku, 0)
        if cur < qty:
            raise InventoryError("not enough stock")
        self._stock[sku] = cur - qty

    def release(self, sku: str, qty: int) -> None:
        if qty <= 0:
            raise InventoryError("qty must be > 0")
        self._stock[sku] = self._stock.get(sku, 0) + qty
