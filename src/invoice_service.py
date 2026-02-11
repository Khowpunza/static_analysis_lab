from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple


@dataclass
class LineItem:
    sku: str
    category: str
    unit_price: float
    qty: int
    fragile: bool = False


@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    country: str
    membership: str
    coupon: Optional[str]
    items: List[LineItem]


class InvoiceService:
    SHIPPING_RULES = {
        "TH": [(500, 60)],
        "JP": [(4000, 600)],
        "US": [(100, 15), (300, 8)],
        "DEFAULT": [(200, 25)],
    }

    TAX_RATE = {
        "TH": 0.07,
        "JP": 0.10,
        "US": 0.08,
        "DEFAULT": 0.05,
    }

    MEMBERSHIP_DISCOUNT = {
        "gold": 0.03,
        "platinum": 0.05,
    }

    FRAGILE_FEE_PER_ITEM = 5.0

    def __init__(self) -> None:
        self._coupon_rate: Dict[str, float] = {
            "WELCOME10": 0.10,
            "VIP20": 0.20,
            "STUDENT5": 0.05,
        }

    def _validate(self, inv: Invoice) -> List[str]:
        problems: List[str] = []
        if not inv:
            return ["Invoice is missing"]

        if not inv.invoice_id:
            problems.append("Missing invoice_id")
        if not inv.customer_id:
            problems.append("Missing customer_id")
        if not inv.items:
            problems.append("Invoice must contain items")

        for it in inv.items:
            if not it.sku:
                problems.append("Item sku is missing")
            if it.qty <= 0:
                problems.append(f"Invalid qty for {it.sku}")
            if it.unit_price < 0:
                problems.append(f"Invalid price for {it.sku}")
            if it.category not in ("book", "food", "electronics", "other"):
                problems.append(f"Unknown category for {it.sku}")

        return problems

    def _calculate_subtotal_and_fragile_fee(self, items: List[LineItem]) -> Tuple[float, float]:
        subtotal = 0.0
        fragile_fee = 0.0

        for it in items:
            subtotal += it.unit_price * it.qty
            if it.fragile:
                fragile_fee += self.FRAGILE_FEE_PER_ITEM * it.qty

        return subtotal, fragile_fee

    def _calculate_shipping(self, country: str, subtotal: float) -> float:
        rules = self.SHIPPING_RULES.get(country, self.SHIPPING_RULES["DEFAULT"])
        for limit, cost in rules:
            if subtotal < limit:
                return cost
        return 0.0

    def _calculate_discount(self, inv: Invoice, subtotal: float, warnings: List[str]) -> float:
        discount = 0.0

        discount += subtotal * self.MEMBERSHIP_DISCOUNT.get(inv.membership, 0.0)

        if inv.membership not in self.MEMBERSHIP_DISCOUNT and subtotal > 3000:
            discount += 20

        if inv.coupon:
            code = inv.coupon.strip()
            if code in self._coupon_rate:
                discount += subtotal * self._coupon_rate[code]
            else:
                warnings.append("Unknown coupon")

        return discount

    def _calculate_tax(self, country: str, taxable_amount: float) -> float:
        rate = self.TAX_RATE.get(country, self.TAX_RATE["DEFAULT"])
        return taxable_amount * rate

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        warnings: List[str] = []

        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        subtotal, fragile_fee = self._calculate_subtotal_and_fragile_fee(inv.items)
        shipping = self._calculate_shipping(inv.country, subtotal)
        discount = self._calculate_discount(inv, subtotal, warnings)
        tax = self._calculate_tax(inv.country, subtotal - discount)

        total = subtotal + shipping + fragile_fee + tax - discount
        total = max(total, 0)

        if subtotal > 10000 and inv.membership not in self.MEMBERSHIP_DISCOUNT:
            warnings.append("Consider membership upgrade")

        return total, warning