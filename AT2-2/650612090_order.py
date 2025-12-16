from dataclasses import dataclass
from typing import List, Dict
from inventory import InventoryRepository, InventoryError
from payment import PaymentGateway, PaymentDeclinedError
from shipping import ShippingService
from emailer import EmailService

@dataclass
class LineItem:
    sku: str
    qty: int
    price: float
    weight: float

class OrderService:
    def __init__(self, inv: InventoryRepository, pay: PaymentGateway,
                 ship: ShippingService, mail: EmailService):
        self.inv = inv
        self.pay = pay
        self.ship = ship
        self.mail = mail

    def place_order(self, customer_email: str, items: List[Dict], region: str) -> dict:
        line_items = [LineItem(**it) for it in items]

        try:
            for li in line_items:
                self.inv.reserve(li.sku, li.qty)
        except InventoryError:
            raise

        subtotal = sum(li.qty * li.price for li in line_items)
        total_weight = sum(li.qty * li.weight for li in line_items)
        shipping_cost = self.ship.cost(total_weight, region)
        total = subtotal + shipping_cost

        try:
            tx_id = self.pay.charge(total, "THB")
        except PaymentDeclinedError:
            for li in line_items:
                self.inv.release(li.sku, li.qty)
            raise

        try:
            self.mail.send(customer_email, "Order confirmed",
                           f"Total amount {total:.2f} THB, tx={tx_id}")
        except Exception:
            pass

        return {
            "total": round(total, 2),
            "shipping": round(shipping_cost, 2),
            "transaction_id": tx_id,
        }
