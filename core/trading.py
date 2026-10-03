"""Paper-trading logic (carried over from the senior's Tkinter app).

This file has NO screen code. It only does the maths and bookkeeping, which
makes it easy to test and easy to explain: "money in, shares in, shares out".

Rules kept from the senior's version:
  * BUY  - needs enough cash; new average price is a weighted average.
  * SELL - needs enough shares; profit = (sell price - average price) * qty.
           After a partial sale the average price of the rest is unchanged.
  * Every trade is stored in an order history that can be exported to CSV.
"""
import json
import os
import tempfile
from datetime import datetime

import pandas as pd

from core.formatting import format_inr

DEFAULT_BALANCE = 100000.0  # virtual Rs 1,00,000
# Saving to a file only makes sense on ONE computer (local use). On a cloud server the
# file would be shared by every visitor, so saving is OFF unless STOCK_APP_SAVE=1.
SAVE_TO_DISK = os.environ.get("STOCK_APP_SAVE") == "1"
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "portfolio.json")


MIN_CAPITAL = 1000.0            # Rs 1,000
MAX_CAPITAL = 100000000.0       # Rs 10 crore (same limits as the senior's version)


def check_capital(amount):
    """Make sure a chosen starting amount is sensible; returns it as a float."""
    if amount is None or not (MIN_CAPITAL <= amount <= MAX_CAPITAL):
        raise TradingError(f"Starting capital must be between {format_inr(MIN_CAPITAL, 0)} "
                           f"and {format_inr(MAX_CAPITAL, 0)}.")
    return float(amount)


class TradingError(Exception):
    """A trade that is not allowed. The message is written for visitors to read."""


class Portfolio:
    def __init__(self, balance=DEFAULT_BALANCE):
        self.balance = float(balance)
        self.deposited = float(balance)  # total money put in; profit = total value - deposited
        # holdings looks like: {"RELIANCE.NS": {"quantity": 10, "avg_price": 2450.5}}
        self.holdings = {}
        self.order_history = []

    # ---------------- money ----------------
    def add_funds(self, amount):
        if amount <= 0:
            raise TradingError("Please enter an amount greater than zero.")
        self.balance += amount
        self.deposited += amount

    # ---------------- trading ----------------
    def buy(self, symbol, quantity, price):
        self._check_order(quantity, price)
        total = quantity * price
        if total > self.balance:
            raise TradingError(
                f"Not enough cash: this order costs {format_inr(total)} but you have {format_inr(self.balance)}."
            )

        self.balance -= total
        if symbol in self.holdings:
            # Weighted average: (old cost + new cost) / total shares.
            old = self.holdings[symbol]
            new_qty = old["quantity"] + quantity
            new_avg = (old["quantity"] * old["avg_price"] + total) / new_qty
            self.holdings[symbol] = {"quantity": new_qty, "avg_price": new_avg}
        else:
            self.holdings[symbol] = {"quantity": quantity, "avg_price": price}

        return self._record("BUY", symbol, quantity, price, pnl=0.0)

    def sell(self, symbol, quantity, price):
        self._check_order(quantity, price)
        if symbol not in self.holdings:
            raise TradingError(f"You don't own any shares of {symbol.replace('.NS', '')}.")
        held = self.holdings[symbol]
        if quantity > held["quantity"]:
            raise TradingError(f"You only own {held['quantity']} share(s) of {symbol.replace('.NS', '')}.")

        pnl = (price - held["avg_price"]) * quantity  # realised profit/loss
        self.balance += quantity * price
        remaining = held["quantity"] - quantity
        if remaining == 0:
            del self.holdings[symbol]
        else:
            held["quantity"] = remaining  # average price stays the same

        return self._record("SELL", symbol, quantity, price, pnl=pnl)

    # ---------------- reporting ----------------
    def holdings_table(self, latest_prices):
        """One row per holding with current value and unrealised profit/loss.

        latest_prices: dict like {"RELIANCE.NS": 2900.0}. If a price is missing
        we fall back to the average price so the row shows P&L of zero, not a crash.
        """
        rows = []
        for symbol, h in self.holdings.items():
            current = latest_prices.get(symbol) or h["avg_price"]
            invested = h["quantity"] * h["avg_price"]
            value = h["quantity"] * current
            pnl = value - invested
            rows.append({
                "Symbol": symbol,
                "Quantity": h["quantity"],
                "Avg Price": h["avg_price"],
                "Current Price": current,
                "Value": value,
                "P&L": pnl,
                "P&L %": (pnl / invested * 100) if invested else 0.0,
            })
        return pd.DataFrame(rows)

    def total_value(self, latest_prices):
        """Cash + current value of all holdings."""
        stocks = sum(
            h["quantity"] * (latest_prices.get(s) or h["avg_price"])
            for s, h in self.holdings.items()
        )
        return self.balance + stocks

    def orders_dataframe(self):
        return pd.DataFrame(self.order_history)

    def export_orders_csv(self, path):
        """Write order history to a CSV file. Returns False if there is nothing to export."""
        if not self.order_history:
            return False
        self.orders_dataframe().to_csv(path, index=False)
        return True

    # ---------------- saving (fixes: "not saved between sessions") ----------------
    def to_dict(self):
        return {"balance": self.balance, "deposited": self.deposited, "holdings": self.holdings, "order_history": self.order_history}

    @classmethod
    def from_dict(cls, data):
        p = cls(balance=data.get("balance", DEFAULT_BALANCE))
        p.deposited = data.get("deposited", DEFAULT_BALANCE)
        p.holdings = data.get("holdings", {})
        p.order_history = data.get("order_history", [])
        return p

    def save(self, path=DEFAULT_PATH):
        """Save to JSON. We write to a temp file first, then swap it in, so a crash
        half-way through can never leave a broken save file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        os.replace(tmp, path)

    @classmethod
    def load(cls, path=DEFAULT_PATH):
        """Load a saved portfolio, or start fresh if none exists / file is damaged."""
        try:
            with open(path) as f:
                return cls.from_dict(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()

    # ---------------- helpers ----------------
    @staticmethod
    def _check_order(quantity, price):
        if not isinstance(quantity, int) or quantity <= 0:
            raise TradingError("Quantity must be a whole number greater than zero.")
        if not price or price <= 0:
            raise TradingError("Could not get a valid price for this stock right now.")

    def _record(self, order_type, symbol, quantity, price, pnl):
        order = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "type": order_type,
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "total": quantity * price,
            "pnl": pnl,
        }
        self.order_history.append(order)
        return order
