import pytest
from unittest.mock import MagicMock
from inventory import InMemoryInventory, InventoryError, InventoryRepository
from payment import PaymentGateway, PaymentDeclinedError, SimplePayment
from shipping import ShippingService
from emailer import EmailService
from order import OrderService

# ==========================================
# 1. Custom Stubs & Spies (Helper Classes)
# ==========================================

class SpyEmail(EmailService):
    """Spy: ใช้ตรวจสอบว่ามีการเรียกส่งอีเมลจริงหรือไม่ และตรวจสอบเนื้อหา"""
    def __init__(self):
        self.sent_emails = []  # เก็บประวัติการส่ง (To, Subject, Body)

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body
        })

class StubPayment(PaymentGateway):
    """Stub: ควบคุมพฤติกรรมการจ่ายเงิน (บังคับให้ผ่าน หรือ ล้มเหลว)"""
    def __init__(self, force_fail=False):
        self.force_fail = force_fail

    def charge(self, amount: float, currency: str) -> str:
        if self.force_fail:
            raise PaymentDeclinedError("Forced failure by Stub")
        return "tx-stub-success"

    def refund(self, transaction_id: str) -> None:
        pass

# ==========================================
# 2. Test Cases
# ==========================================

# --- A. Top-down Integration Testing ---
# เน้นทดสอบ OrderService โดยใช้ Stub/Spy แทน component ล่างๆ
@pytest.mark.topdown
class TestTopDown:
    
    def test_order_success_sends_email(self):
        """Top-down: สั่งซื้อสำเร็จ ต้องเรียก Email Service (ใช้ Spy ตรวจสอบ)"""
        # Setup
        inv = InMemoryInventory()
        inv.add_stock("SKU01", 10)
        
        pay_stub = StubPayment(force_fail=False) # Stub ให้จ่ายเงินผ่านเสมอ
        ship = ShippingService() # Logic ง่ายๆ ใช้ของจริงได้ หรือจะ Mock ก็ได้
        email_spy = SpyEmail() # Spy
        
        service = OrderService(inv, pay_stub, ship, email_spy)
        
        # Action
        items = [{"sku": "SKU01", "qty": 1, "price": 100.0, "weight": 1.0}]
        result = service.place_order("customer@test.com", items, "TH")
        
        # Assert (Spy Check)
        assert len(email_spy.sent_emails) == 1
        assert email_spy.sent_emails[0]["subject"] == "Order confirmed"
        assert "tx-stub-success" in result["transaction_id"]

    def test_payment_failure_releases_stock(self):
        """Top-down: จ่ายเงินไม่ผ่าน (Stub) ต้องคืน Stock (Rollback)"""
        # Setup
        inv = InMemoryInventory()
        inv.add_stock("SKU02", 5)
        
        pay_stub = StubPayment(force_fail=True) # Stub ให้จ่ายเงินล้มเหลว
        ship = ShippingService()
        email_spy = SpyEmail()
        
        service = OrderService(inv, pay_stub, ship, email_spy)
        
        # Action
        items = [{"sku": "SKU02", "qty": 2, "price": 100.0, "weight": 1.0}]
        
        with pytest.raises(PaymentDeclinedError):
            service.place_order("fail@test.com", items, "TH")
            
        # Assert (Check Side Effect)
        # สต็อกต้องกลับมาเท่าเดิม (5) เพราะถูก reserve แล้ว release คืน
        assert inv.get_stock("SKU02") == 5
        # ต้องไม่มีการส่งอีเมล
        assert len(email_spy.sent_emails) == 0


# --- B. Bottom-up Integration Testing ---
# เน้นทดสอบ Component ล่างสุด (Inventory) ให้มั่นใจก่อน
@pytest.mark.bottomup
class TestBottomUp:
    
    def test_inventory_reserve_and_release(self):
        """Bottom-up: ทดสอบ Logic การตัดและคืนสต็อกของ Inventory โดยตรง"""
        inv = InMemoryInventory()
        inv.add_stock("ITEM-A", 10)
        
        # Test Reserve
        inv.reserve("ITEM-A", 4)
        assert inv.get_stock("ITEM-A") == 6
        
        # Test Reserve Fail (Not enough stock)
        with pytest.raises(InventoryError):
            inv.reserve("ITEM-A", 7) # เหลือ 6 ขอ 7 ต้อง Error
            
        # Test Release
        inv.release("ITEM-A", 2)
        assert inv.get_stock("ITEM-A") == 8 # 6 + 2
        
    def test_inventory_add_invalid(self):
        """Bottom-up: เพิ่มสต็อกผิดเงื่อนไข"""
        inv = InMemoryInventory()
        with pytest.raises(InventoryError):
            inv.add_stock("ITEM-B", -1)


# --- C. Sandwich Integration Testing ---
# ใช้ Real Components ตรงกลางและล่าง (Inventory, Payment จริง) แต่ Spy ตัวบน/ปลายทาง (Email)
@pytest.mark.sandwich
class TestSandwich:
    
    def test_real_payment_flow_with_region_us(self):
        """Sandwich: ใช้ SimplePayment จริง + Inventory จริง + Email Spy ทดสอบ Region US"""
        # Setup
        inv = InMemoryInventory()
        inv.add_stock("IPHONE", 10)
        
        pay_real = SimplePayment() # ใช้ของจริง (Logic: amount <= 1000 ผ่าน)
        ship_real = ShippingService()
        email_spy = SpyEmail()
        
        service = OrderService(inv, pay_real, ship_real, email_spy)
        
        # Action (ยอดเงินรวม shipping ต้องไม่เกิน 1000)
        # Region US ค่าส่ง 300
        # สินค้า 1 ชิ้น ราคา 500 -> Total = 800 (ผ่านเงื่อนไข <= 1000 ของ SimplePayment)
        items = [{"sku": "IPHONE", "qty": 1, "price": 500.0, "weight": 0.5}]
        result = service.place_order("sandwich@test.com", items, "US")
        
        # Assert
        assert result["shipping"] == 300.0 # ตรวจสอบ Logic Shipping
        assert result["total"] == 800.0
        assert inv.get_stock("IPHONE") == 9 # ตรวจสอบ Real Inventory ตัดจริง
        assert len(email_spy.sent_emails) == 1 # ตรวจสอบ Email Spy

    def test_real_payment_over_limit_fails(self):
        """Sandwich: ทดสอบเงื่อนไขของ Real Payment (ยอดเกิน 1000 ต้อง Error)"""
        inv = InMemoryInventory()
        inv.add_stock("LAPTOP", 5)
        
        pay_real = SimplePayment()
        ship_real = ShippingService()
        email_spy = SpyEmail()
        
        service = OrderService(inv, pay_real, ship_real, email_spy)
        
        # Action: ราคารวมเกิน 1000 (900 + 300 ค่าส่ง = 1200)
        items = [{"sku": "LAPTOP", "qty": 1, "price": 900.0, "weight": 2.0}]
        
        with pytest.raises(PaymentDeclinedError):
            service.place_order("rich@test.com", items, "EU")
            
        # Assert Rollback
        assert inv.get_stock("LAPTOP") == 5