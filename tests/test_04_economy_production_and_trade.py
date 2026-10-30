"""
Consolidated Test Suite 04: Economy, Order Book, Production, Crafting, Spoilage, Debt, and Pricing.
"""
import unittest
from pathlib import Path

from src.core.path_utils import get_default_data_dir
from src.entities.item import ItemDefinition, ItemInstance
from src.economy.bargaining import OrderBook, OrderBookEntry, BargainingEngine
from src.economy.production import Recipe, ProductionManager
from src.economy.spoilage import SpoilageTracker
from src.economy.pricing import DynamicPricingEngine
from src.economy.finance import DebtManager
from src.economy.macro import MacroEconomicTracker
from src.simulation.engine import SimulationEngine


class TestEconomyProductionAndTrade(unittest.TestCase):
    """Verifies Order Book trade, Bargaining, Production, Spoilage, Pricing, Loans, and Macro Telemetry."""

    def setUp(self):
        self.data_dir = get_default_data_dir()
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)

    def test_order_book_trade_matching(self):
        book = OrderBook()

        # Submit sell ask at 5.0 gold
        book.submit_order(OrderBookEntry("ord_sell_1", "npc_seller", "item_wheat", "SELL", price=5.0, quantity=10, tick_created=1))
        # Submit buy bid at 6.0 gold
        book.submit_order(OrderBookEntry("ord_buy_1", "npc_buyer", "item_wheat", "BUY", price=6.0, quantity=5, tick_created=1))

        matched_trades = book.match_orders("item_wheat")
        self.assertEqual(len(matched_trades), 1)
        trade = matched_trades[0]
        self.assertEqual(trade["quantity"], 5)
        self.assertEqual(trade["price"], 5.5)  # Midpoint clearing

    def test_pairwise_reservation_price_bargaining(self):
        buyer = self.engine.npcs["npc_aldous"]
        seller = self.engine.npcs["npc_beatrice"]
        bread_item = ItemInstance("inst_bread_1", "item_bread")

        res = BargainingEngine.negotiate_trade(
            buyer=buyer,
            seller=seller,
            item_instance=bread_item,
            base_value=10.0,
            trust_score=50.0
        )

        self.assertIn("buyer_max", res)
        self.assertIn("seller_min", res)

    def test_production_crafting_and_spoilage_decay(self):
        recipe = Recipe("r_bread", "Bake Bread", inputs={"item_flour": 1}, outputs={"item_bread": 2}, required_capability="bakery_oven")
        inventory = [ItemInstance("inst_flour", "item_flour")]

        can_craft = ProductionManager.can_craft(inventory, recipe)
        self.assertTrue(can_craft)

        produced = ProductionManager.craft(inventory, recipe, crafter_id="npc_greta")
        self.assertEqual(len(produced), 2)
        self.assertEqual(produced[0].item_def_id, "item_bread")

        # Spoilage decay
        item_defs = {"item_bread": ItemDefinition("item_bread", "Bread", "food", spoil_rate=1.0)}
        bread_item = produced[0]
        bread_item.freshness = 10.0
        SpoilageTracker.apply_spoilage([bread_item], item_defs, in_pantry=False)
        self.assertEqual(bread_item.freshness, 9.0)

    def test_dynamic_pricing_and_debt_interest(self):
        price = DynamicPricingEngine.calculate_price(base_value=10.0, supply=2, demand=10, quality=1.5)
        self.assertGreater(price, 10.0)

        # Debt Manager
        debt_mgr = DebtManager()
        loan = debt_mgr.issue_loan(loan_id="loan_1", lender_id="npc_vance", borrower_id="npc_barnaby_beggar", principal=50.0, interest_rate=0.05)

        self.assertEqual(loan.remaining_balance, 50.0)
        debt_mgr.accrue_interest()
        self.assertGreater(loan.remaining_balance, 50.0)

    def test_macro_economic_telemetry_gini_and_wealth(self):
        gini = MacroEconomicTracker.calculate_gini_coefficient(self.engine.npcs)
        total_currency = MacroEconomicTracker.calculate_total_currency(self.engine.npcs)

        self.assertTrue(0.0 <= gini <= 1.0)
        self.assertGreater(total_currency, 0.0)


if __name__ == "__main__":
    unittest.main()
