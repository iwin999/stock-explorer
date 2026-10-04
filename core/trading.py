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
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from core.formatting import format_inr

IST = ZoneInfo("Asia/Kolkata")
DEFAULT_BALANCE = 100000.0  # virtual Rs 1,00,000
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
    def __init__(self, balance=DEFAULT_BALANCE, name="", created_at=None):
        self.name = name
        self.created_at = created_at      # when the account was first made (UTC text), or None for older accounts
        self.balance = float(balance)
        self.deposited = float(balance)  # total money put in; profit = total value - deposited
        # holdings looks like: {"RELIANCE.NS": {"quantity": 10, "avg_price": 2450.5}}
        self.holdings = {}
        # Open futures and options. Each is a dict with an "id", "type" ("FUT"/"OPT"), the underlying,
        # expiry date (text), lots, lot size and the prices it was opened at.
        self.derivatives = []
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


    # ---------------- futures ----------------
    def open_future(self, underlying, expiry, side, lots, price, lot_size, margin_pct):
        """Open a futures position. `side` is "LONG" (profit if the price rises) or "SHORT" (profit if it falls).

        Only a margin (a deposit) is blocked, not the full contract value. Profit and loss are
        settled in cash when the position is closed or expires.
        """
        self._check_order(lots, price, what="contract")
        margin = margin_pct * price * lot_size * lots
        if margin > self.balance:
            raise TradingError(f"Not enough cash for the margin: {format_inr(margin)} is needed "
                               f"but you have {format_inr(self.balance)}.")
        self.balance -= margin
        pos = {"id": uuid.uuid4().hex[:8], "type": "FUT", "underlying": underlying, "expiry": str(expiry),
               "side": side, "lots": lots, "lot_size": lot_size, "entry": price, "margin": margin}
        self.derivatives.append(pos)
        self._record(f"FUT {side} OPEN", self._describe(pos), lots, price, pnl=0.0)
        return pos

    def close_future(self, pos_id, price, reason="CLOSE"):
        """Close a futures position at `price`. Returns the profit or loss."""
        pos = self._find(pos_id, "FUT")
        direction = 1 if pos["side"] == "LONG" else -1
        pnl = direction * (price - pos["entry"]) * pos["lot_size"] * pos["lots"]
        self.balance += max(pos["margin"] + pnl, 0.0)       # a loss beyond the margin is not charged (simplified)
        self.derivatives.remove(pos)
        self._record(f"FUT {reason}", self._describe(pos), pos["lots"], price, pnl=pnl)
        return pnl

    # ---------------- options (buying only) ----------------
    def buy_option(self, underlying, expiry, strike, kind, lots, premium, lot_size):
        """Buy a call or put. The most you can lose is the premium paid."""
        self._check_order(lots, premium, what="option")
        cost = premium * lot_size * lots
        if cost > self.balance:
            raise TradingError(f"Not enough cash: this costs {format_inr(cost)} but you have {format_inr(self.balance)}.")
        self.balance -= cost
        pos = {"id": uuid.uuid4().hex[:8], "type": "OPT", "underlying": underlying, "expiry": str(expiry),
               "strike": strike, "kind": kind, "lots": lots, "lot_size": lot_size, "premium": premium}
        self.derivatives.append(pos)
        self._record(f"OPT BUY {kind}", self._describe(pos), lots, premium, pnl=0.0)
        return pos

    def sell_option(self, pos_id, premium_now, reason="SELL"):
        """Sell an option you hold (or let it expire, with reason "EXPIRED"). Returns the profit or loss."""
        pos = self._find(pos_id, "OPT")
        units = pos["lot_size"] * pos["lots"]
        self.balance += premium_now * units
        pnl = (premium_now - pos["premium"]) * units
        self.derivatives.remove(pos)
        self._record(f"OPT {reason}", self._describe(pos), pos["lots"], premium_now, pnl=pnl)
        return pnl

    # ---------------- helpers for derivatives ----------------
    def _find(self, pos_id, kind):
        for pos in self.derivatives:
            if pos["id"] == pos_id and pos["type"] == kind:
                return pos
        raise TradingError("That position is no longer open.")

    @staticmethod
    def _describe(pos):
        name = pos["underlying"].replace(".NS", "")
        if pos["type"] == "FUT":
            return f"{name} FUTURE {pos['expiry']} {pos['side']}"
        return f"{name} {pos['strike']:g} {pos['kind']} {pos['expiry']}"

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
        return {"name": self.name, "created_at": self.created_at, "balance": self.balance, "deposited": self.deposited, "holdings": self.holdings,
                "derivatives": self.derivatives, "order_history": self.order_history}

    @classmethod
    def from_dict(cls, data):
        p = cls(balance=data.get("balance", DEFAULT_BALANCE), name=data.get("name", ""),
                created_at=data.get("created_at"))
        p.deposited = data.get("deposited", DEFAULT_BALANCE)
        p.holdings = data.get("holdings", {})
        p.derivatives = data.get("derivatives", [])
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
    def _check_order(quantity, price, what="stock"):
        if not isinstance(quantity, int) or quantity <= 0:
            raise TradingError("Quantity must be a whole number greater than zero.")
        if not price or price <= 0:
            raise TradingError(f"Could not get a valid price for this {what} right now.")

    def _record(self, order_type, symbol, quantity, price, pnl):
        order = {
            "timestamp": datetime.now(IST).replace(tzinfo=None).isoformat(timespec="seconds"),     # Indian time (the server may be elsewhere)
            "type": order_type,
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "total": quantity * price,
            "pnl": pnl,
        }
        self.order_history.append(order)
        return order
