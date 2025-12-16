class ShippingService:
    def cost(self, total_weight: float, region: str) -> float:
        if region == "TH":
            return 50.0 if total_weight <= 5 else 120.0
        return 300.0
