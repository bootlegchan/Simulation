"""
Order-Book Bargaining Engine: Dynamic asymmetric trade matching and pairwise price negotiation.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from src.entities.npc import NPC
from src.entities.item import ItemInstance

@dataclass
class OrderBookEntry:
    entry_id: str
    trader_id: str
    item_def_id: str
    order_type: str  # "BUY" or "SELL"
    price: float
    quantity: int
    tick_created: int

class OrderBook:
    """Central limit order book for item definitions."""

    def __init__(self):
        self.bids: Dict[str, List[OrderBookEntry]] = {}  # item_def_id -> sorted high to low
        self.asks: Dict[str, List[OrderBookEntry]] = {}  # item_def_id -> sorted low to high

    def submit_order(self, entry: OrderBookEntry) -> None:
        if entry.order_type == "BUY":
            self.bids.setdefault(entry.item_def_id, []).append(entry)
            self.bids[entry.item_def_id].sort(key=lambda x: x.price, reverse=True)
        else:
            self.asks.setdefault(entry.item_def_id, []).append(entry)
            self.asks[entry.item_def_id].sort(key=lambda x: x.price)

    def match_orders(self, item_def_id: str) -> List[Dict[str, Any]]:
        """Match highest buy bids against lowest sell asks."""
        matches = []
        bids = self.bids.get(item_def_id, [])
        asks = self.asks.get(item_def_id, [])

        while bids and asks and bids[0].price >= asks[0].price:
            bid = bids[0]
            ask = asks[0]
            clearing_price = round((bid.price + ask.price) / 2.0, 2)
            traded_qty = min(bid.quantity, ask.quantity)

            matches.append({
                "item_def_id": item_def_id,
                "buyer_id": bid.trader_id,
                "seller_id": ask.trader_id,
                "price": clearing_price,
                "quantity": traded_qty,
            })

            bid.quantity -= traded_qty
            ask.quantity -= traded_qty

            if bid.quantity <= 0:
                bids.pop(0)
            if ask.quantity <= 0:
                asks.pop(0)

        return matches

class BargainingEngine:
    """Pairwise negotiation based on need urgency, personality greed, and trust."""

    @staticmethod
    def calculate_reservation_price(
        npc: NPC,
        base_value: float,
        is_seller: bool,
        trust_score: float = 0.0
    ) -> float:
        greed = npc.personality.get("conscientiousness", 0.5) * 0.4
        hunger = npc.needs.get("hunger", 0.0) / 100.0

        if is_seller:
            # Urgent sellers lower prices; greedy sellers raise prices; trusted buyers get discounts
            discount = trust_score * 0.002
            markup = greed - (hunger * 0.2)
            res_price = base_value * (1.0 + markup - discount)
        else:
            # Urgent buyers pay higher prices; trusted sellers get higher offers
            markup = (hunger * 0.3) + (trust_score * 0.001)
            res_price = base_value * (1.0 + markup)

        return max(0.5, round(res_price, 2))

    @staticmethod
    def negotiate_trade(
        buyer: NPC,
        seller: NPC,
        item_instance: ItemInstance,
        base_value: float,
        trust_score: float = 0.0
    ) -> Dict[str, Any]:
        buyer_max = BargainingEngine.calculate_reservation_price(buyer, base_value, is_seller=False, trust_score=trust_score)
        seller_min = BargainingEngine.calculate_reservation_price(seller, base_value, is_seller=True, trust_score=trust_score)

        if buyer_max >= seller_min and buyer.wealth >= seller_min:
            final_price = round((buyer_max + seller_min) / 2.0, 2)
            # Execute transaction
            buyer.wealth -= final_price
            seller.wealth += final_price
            if item_instance in seller.inventory:
                seller.inventory.remove(item_instance)
                item_instance.owner_id = buyer.id
                buyer.inventory.append(item_instance)

            return {
                "success": True,
                "final_price": final_price,
                "buyer_max": buyer_max,
                "seller_min": seller_min,
            }

        return {
            "success": False,
            "reason": "Reservation prices incompatible or insufficient funds",
            "buyer_max": buyer_max,
            "seller_min": seller_min,
        }
