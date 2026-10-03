import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import yfinance as yf
import threading
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import pandas as pd
import logging
import time
import os

try:
    import mplfinance as mpf
    HAS_MPF = True
except Exception:
    HAS_MPF = False

LOG_PATH = os.path.join(os.getcwd(), 'mcgs_trade.log')
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

AUTO_REFRESH_MS = 30000
SEARCH_LIMIT = 20

class StockTradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time Stock Trading with Symbol Search - NSE/BSE")

        self.dummy_balance = 0.0
        self.portfolio = {}
        self.order_history = []

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.window_width = int(self.screen_width * 0.7)
        self.window_height = int(self.screen_height * 0.65)
        self.root.geometry(f"{self.window_width}x{self.window_height}")

        self.main_container = ttk.Frame(root, padding="10")
        self.main_container.pack(fill='both', expand=True)

        self.setup_initial_balance()
        self.setup_responsive_ui()
        self.auto_refresh()
        self.root.bind('<Configure>', self.on_window_resize)

    def setup_initial_balance(self):
        while True:
            try:
                initial = simpledialog.askfloat(
                    "Initial Balance",
                    "Enter initial dummy balance (₹):",
                    initialvalue=100000.0,
                    minvalue=1000.0,
                    maxvalue=100000000.0
                )
                if initial is None:
                    initial = 100000.0
                self.dummy_balance = float(initial)
                break
            except Exception:
                messagebox.showerror("Invalid Input", "Please enter a valid number")

    def add_funds(self):
        try:
            amount = simpledialog.askfloat(
                "Add Funds",
                "Enter amount to add (₹):",
                initialvalue=10000.0,
                minvalue=100.0,
                maxvalue=1000000.0
            )
            if amount and amount > 0:
                self.dummy_balance += amount
                self.update_balance_display()
                messagebox.showinfo("Funds Added", f"Successfully added ₹{amount:,.2f} to your account!")
                self.status_bar.config(text=f"Added ₹{amount:,.2f} to balance")
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Input", "Please enter a valid number")

    def setup_responsive_ui(self):
        # Use PanedWindow for left (search) and right (chart)
        main_pane = ttk.PanedWindow(self.main_container, orient='horizontal')
        main_pane.pack(fill='both', expand=True)

        # Left side: controls and portfolio
        left_frame = ttk.Frame(main_pane, padding=6)
        main_pane.add(left_frame, weight=3)

        # Right side: chart
        right_frame = ttk.Frame(main_pane, padding=6)
        main_pane.add(right_frame, weight=2)

        # Balance frame
        balance_frame = ttk.LabelFrame(left_frame, text="Paper Trading Account", padding=8)
        balance_frame.pack(fill='x')

        self.balance_label = ttk.Label(balance_frame, text=f"Available Balance: ₹{self.dummy_balance:,.2f}", font=("Segoe UI", 12, "bold"))
        self.balance_label.pack(side='left')

        add_button = ttk.Button(balance_frame, text="Add Funds", command=self.add_funds)
        add_button.pack(side='right')

        values_frame = ttk.Frame(left_frame)
        values_frame.pack(fill='x', pady=(6, 6))

        self.portfolio_value_label = ttk.Label(values_frame, text="Portfolio Value: ₹0.00")
        self.portfolio_value_label.pack(side='left')

        self.total_value_label = ttk.Label(values_frame, text="Total Value: ₹0.00", font=("Segoe UI", 11, "bold"))
        self.total_value_label.pack(side='right')

        # Search area
        search_frame = ttk.LabelFrame(left_frame, text="Search Stock (NSE/BSE Only)", padding=8)
        search_frame.pack(fill='x', pady=(6, 6))

        entry_frame = ttk.Frame(search_frame)
        entry_frame.pack(fill='x')

        self.symbol_entry = ttk.Entry(entry_frame)
        self.symbol_entry.pack(side='left', fill='x', expand=True, padx=(0, 6))
        self.symbol_entry.bind('<KeyRelease>', self.on_key_release)

        search_btn = ttk.Button(entry_frame, text="Search", command=self.search_stocks)
        search_btn.pack(side='left')

        clear_btn = ttk.Button(entry_frame, text="Clear", command=self.clear_search)
        clear_btn.pack(side='left', padx=(6, 0))

        self.results_listbox = tk.Listbox(search_frame, height=5)
        self.results_listbox.pack(fill='x', pady=(6, 0))
        self.results_listbox.bind('<<ListboxSelect>>', self.on_select)

        # Info and price
        info_frame = ttk.Frame(left_frame)
        info_frame.pack(fill='x', pady=(6, 6))

        self.info_label = ttk.Label(info_frame, text="Select a stock to view information", wraplength=self.window_width//2, justify='left')
        self.info_label.pack(fill='x')

        price_frame = ttk.Frame(left_frame)
        price_frame.pack(fill='x')

        self.price_label = ttk.Label(price_frame, text="Current Price: -", font=("Segoe UI", 12, "bold"), foreground='blue')
        self.price_label.pack(side='left')

        refresh_price_btn = ttk.Button(price_frame, text="Refresh Price", command=self.get_current_price)
        refresh_price_btn.pack(side='right')

        cp_frame = ttk.LabelFrame(left_frame, text="Current Share Price", padding=6)
        cp_frame.pack(fill='x', pady=(6, 6))

        self.current_price_text = ttk.Entry(cp_frame, font=("Segoe UI", 11))
        self.current_price_text.pack(fill='x')
        self.current_price_text.state(['readonly'])

        trade_frame = ttk.Frame(left_frame)
        trade_frame.pack(fill='x', pady=(6, 6))

        buy_btn = tk.Button(trade_frame, text="BUY STOCK", command=self.buy_stock, bg='#4CAF50', fg='white')
        buy_btn.pack(side='left', fill='x', expand=True, padx=(0, 6))

        sell_btn = tk.Button(trade_frame, text="SELL STOCK", command=self.sell_stock, bg='#F44336', fg='white')
        sell_btn.pack(side='left', fill='x', expand=True)

        portfolio_frame = ttk.LabelFrame(left_frame, text="Your Portfolio", padding=6)
        portfolio_frame.pack(fill='both', expand=True, pady=(6, 6))

        columns = ("Symbol", "Quantity", "Avg Price", "Current Price", "P&L")
        self.portfolio_tree = ttk.Treeview(portfolio_frame, columns=columns, show='headings')
        for c in columns:
            self.portfolio_tree.heading(c, text=c)
            self.portfolio_tree.column(c, anchor='center')
        self.portfolio_tree.pack(fill='both', expand=True)

        self.portfolio_tree.tag_configure('profit', foreground='green')
        self.portfolio_tree.tag_configure('loss', foreground='red')

        # Right side chart
        chart_frame = ttk.LabelFrame(right_frame, text='Candlestick Chart - Last 1 Month', padding=6)
        chart_frame.pack(fill='both', expand=True)

        self.fig = Figure(figsize=(6, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        chart_controls = ttk.Frame(chart_frame)
        chart_controls.pack(fill='x')

        self.refresh_chart_btn = ttk.Button(chart_controls, text='Refresh Chart', command=self.refresh_candlestick_chart)
        self.refresh_chart_btn.pack(side='left')

        export_btn = ttk.Button(chart_controls, text='Export Orders CSV', command=self.export_orders_csv)
        export_btn.pack(side='right')

        self.status_bar = ttk.Label(self.main_container, text='Ready', relief='sunken', anchor='w')
        self.status_bar.pack(fill='x', pady=(4, 0))

    def search_stocks(self):
        query = self.symbol_entry.get().strip()
        if not query or len(query) < 2:
            messagebox.showinfo("Search", "Please enter at least 2 characters to search")
            return

        self.status_bar.config(text='Searching...')

        def _search():
            try:
                url = f"https://query1.finance.yahoo.com/v1/finance/search"
                resp = requests.get(url, params={'q': query}, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                data = resp.json()
                quotes = data.get('quotes', [])[:SEARCH_LIMIT]
                results = []
                self.search_results = []
                for q in quotes:
                    sym = q.get('symbol')
                    name = q.get('longname') or q.get('shortname') or ''
                    if sym and name and (sym.endswith('.NS') or sym.endswith('.BO')):
                        display = f"{sym} - {name}"
                        results.append(display)
                        self.search_results.append({'symbol': sym, 'name': name})
                self.root.after(0, lambda: self.update_search_results(results))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Search error: {e}"))

        threading.Thread(target=_search, daemon=True).start()


    def update_search_results(self, results):
        self.results_listbox.delete(0, tk.END)
        if results:
            for r in results:
                self.results_listbox.insert(tk.END, r)
            self.status_bar.config(text=f"Found {len(results)} results")
        else:
            self.results_listbox.insert(tk.END, 'No NSE/BSE stocks found')
            self.status_bar.config(text='No results')

    def on_key_release(self, event):
        if len(self.symbol_entry.get().strip()) >= 3:
            # Debounce by small delay using after
            if hasattr(self, '_search_after'):
                self.root.after_cancel(self._search_after)
            self._search_after = self.root.after(400, self.search_stocks)

    def on_select(self, event):
        sel = self.results_listbox.curselection()
        if sel:
            idx = sel[0]
            if idx < getattr(self, 'search_results', []).__len__():
                s = self.search_results[idx]
                self.set_symbol(s['symbol'])

    # -------------------- Display & Info --------------------
    def set_symbol(self, symbol):
        self.symbol_entry.delete(0, tk.END)
        self.symbol_entry.insert(0, symbol)
        self.display_stock_info(symbol)
        self.get_current_price()
        self.refresh_candlestick_chart()

    def display_stock_info(self, symbol):
        symbol = symbol.strip().upper()
        self.status_bar.config(text=f'Loading {symbol} info...')

        def _info():
            try:
                ticker = yf.Ticker(symbol)
                # Prefer fast_info and history
                name = ticker.fast_info.get('longName') if hasattr(ticker, 'fast_info') else None
                # Fallback to history's last index for currency if needed
                info_text = f"Symbol: {symbol}\nName: {name or 'N/A'}"
                self.root.after(0, lambda: self.info_label.config(text=info_text))
                self.root.after(0, lambda: self.status_bar.config(text=f'Loaded info for {symbol}'))
            except Exception as e:
                logging.exception('Error loading stock info')
                self.root.after(0, lambda: self.show_error(f'Error loading info: {e}'))

        threading.Thread(target=_info, daemon=True).start()

    # -------------------- Price fetching --------------------
    def get_current_stock_price(self, symbol):
        """Use history (reliable) to fetch latest available close/last price"""
        try:
            ticker = yf.Ticker(symbol)
            # Get intraday or last close
            df = ticker.history(period='2d', interval='1m')
            if df is not None and not df.empty:
                # Use last available close
                last = df['Close'].iloc[-1]
                return float(last)
            # fallback to daily
            df2 = ticker.history(period='5d')
            if df2 is not None and not df2.empty:
                return float(df2['Close'].iloc[-1])
            return None
        except Exception as e:
            logging.exception('Error fetching current stock price')
            return None

    def get_stock_data(self):
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol:
            return None
        try:
            price = self.get_current_stock_price(symbol)
            ticker = yf.Ticker(symbol)
            # Some info still available via fast_info
            currency = 'INR'
            try:
                if hasattr(ticker, 'fast_info') and ticker.fast_info:
                    currency = ticker.fast_info.get('currency', currency)
            except Exception:
                pass

            day_high = None
            day_low = None
            try:
                intraday = ticker.history(period='1d', interval='1m')
                if intraday is not None and not intraday.empty:
                    day_high = float(intraday['High'].max())
                    day_low = float(intraday['Low'].min())
            except Exception:
                pass

            return {
                'symbol': symbol,
                'current_price': price,
                'currency': currency,
                'day_high': day_high or 'N/A',
                'day_low': day_low or 'N/A',
                'name': getattr(ticker, 'info', {}).get('longName', 'N/A') if hasattr(ticker, 'info') else 'N/A'
            }
        except Exception as e:
            logging.exception('Error get_stock_data')
            return None

    def get_current_price(self):
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol:
            messagebox.showinfo('Info', 'Please enter/select a stock symbol')
            return
        self.status_bar.config(text=f'Fetching price for {symbol}...')

        def _fetch():
            stock_data = self.get_stock_data()
            self.root.after(0, lambda: self.update_price_display(stock_data))
            self.root.after(0, lambda: self.update_current_price_text(stock_data))

        threading.Thread(target=_fetch, daemon=True).start()

    def update_price_display(self, stock_data):
        if stock_data and stock_data['current_price'] is not None:
            price = stock_data['current_price']
            self.price_label.config(text=f"Current Price: {stock_data['currency']} {price:.2f}")
            self.additional_info = f"Day Range: {stock_data['day_low']} - {stock_data['day_high']}"
            self.status_bar.config(text=f"Price updated for {stock_data['symbol']}")
        else:
            self.price_label.config(text='Current Price: Error fetching data', foreground='red')
            self.status_bar.config(text='Error fetching price data')

    def update_current_price_text(self, stock_data):
        val = '₹0.00'
        if stock_data and stock_data.get('current_price'):
            val = f"₹{stock_data['current_price']:.2f}"
        # Make editable briefly
        try:
            self.current_price_text.state(['!readonly'])
            self.current_price_text.delete(0, 'end')
            self.current_price_text.insert(0, val)
            self.current_price_text.state(['readonly'])
        except Exception:
            pass

    # -------------------- Charting --------------------
    def refresh_candlestick_chart(self):
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol:
            messagebox.showinfo('Info', 'Please enter/select a stock symbol')
            return
        self.status_bar.config(text=f'Loading candlestick chart for {symbol}...')

        def _fetch_chart():
            try:
                end = datetime.now()
                start = end - timedelta(days=30)
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start, end=end, interval='1d')
                self.root.after(0, lambda: self.update_candlestick_chart(hist, symbol))
            except Exception as e:
                logging.exception('Error loading chart')
                self.root.after(0, lambda: self.show_error(f'Error loading chart: {e}'))

        threading.Thread(target=_fetch_chart, daemon=True).start()

    def update_candlestick_chart(self, hist, symbol):
        self.ax.clear()
        if hist is None or hist.empty:
            self.ax.text(0.5, 0.5, 'No data available for chart', ha='center')
            self.canvas.draw()
            self.status_bar.config(text=f'No chart data for {symbol}')
            return

        try:
            if HAS_MPF:
                # Use mplfinance to draw onto the existing axes
                mpf.plot(hist, type='candle', style='charles', ax=self.ax, axtitle=f'{symbol} - Last 1 Month')
            else:
                # Fallback: line + high-low shading
                dates = hist.index
                closes = hist['Close']
                highs = hist['High']
                lows = hist['Low']
                self.ax.plot(dates, closes, linewidth=2)
                self.ax.fill_between(dates, lows, highs, alpha=0.2)
                self.ax.set_title(f'{symbol} - Last 1 Month')
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
                self.fig.autofmt_xdate()

            self.canvas.draw()
            self.status_bar.config(text=f'Chart updated for {symbol}')
        except Exception as e:
            logging.exception('Error drawing chart')
            self.ax.clear()
            self.ax.text(0.5,0.5,f'Error drawing chart: {e}', ha='center', color='red')
            self.canvas.draw()
            self.status_bar.config(text='Error drawing chart')

    # -------------------- Trading --------------------
    def buy_stock(self):
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol:
            messagebox.showwarning('Input Error', 'Please enter a stock symbol')
            return
        stock_data = self.get_stock_data()
        if not stock_data or not stock_data.get('current_price'):
            self.show_error('Could not fetch current price for order')
            return
        self.confirm_order(stock_data, order_type='BUY')

    def sell_stock(self):
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol:
            messagebox.showwarning('Input Error', 'Please enter a stock symbol')
            return
        symbol = symbol.upper()
        if symbol not in self.portfolio:
            messagebox.showwarning('Portfolio Error', f"You don't own any shares of {symbol}")
            return
        stock_data = self.get_stock_data()
        if not stock_data or not stock_data.get('current_price'):
            self.show_error('Could not fetch current price for order')
            return
        self.confirm_order(stock_data, order_type='SELL')

    def confirm_order(self, stock_data, order_type='BUY'):
        qty_window = tk.Toplevel(self.root)
        qty_window.title(f"{order_type} Quantity")
        qty_window.geometry('320x180')
        qty_window.grab_set()

        max_qty = 0
        if order_type == 'BUY' and stock_data.get('current_price'):
            max_qty = int(self.dummy_balance // stock_data['current_price'])

        label_text = f"Enter quantity to {order_type}:"
        if order_type == 'BUY' and max_qty > 0:
            label_text += f"\n(Max affordable: {max_qty} shares)"

        ttk.Label(qty_window, text=label_text).pack(pady=(10,6))
        qty_var = tk.StringVar()
        qty_entry = ttk.Entry(qty_window, textvariable=qty_var)
        qty_entry.pack()
        qty_entry.focus()

        def on_confirm():
            try:
                q = int(qty_var.get())
                if q <= 0:
                    raise ValueError('Quantity must be positive')
                total = q * stock_data['current_price']
                if order_type == 'BUY' and total > self.dummy_balance:
                    messagebox.showerror('Insufficient Funds', f"You need ₹{total:,.2f} but only have ₹{self.dummy_balance:,.2f}")
                    return
                if order_type == 'SELL':
                    holding = self.portfolio[stock_data['symbol']]['quantity']
                    if q > holding:
                        messagebox.showerror('Insufficient Shares', f'You only have {holding} shares')
                        return
                if messagebox.askyesno(f'Confirm {order_type}', f"Confirm {order_type} {q} shares of {stock_data['symbol']} at ₹{stock_data['current_price']:.2f}?"):
                    self.execute_order(stock_data, q, order_type)
                    qty_window.destroy()
            except ValueError:
                messagebox.showwarning('Invalid Quantity', 'Please enter a valid positive integer')

        ttk.Button(qty_window, text='Confirm', command=on_confirm).pack(pady=10)

    def execute_order(self, stock_data, quantity, order_type):
        symbol = stock_data['symbol']
        price = stock_data['current_price']
        total = quantity * price

        if order_type == 'BUY':
            self.dummy_balance -= total
            if symbol in self.portfolio:
                old_qty = self.portfolio[symbol]['quantity']
                old_avg = self.portfolio[symbol]['avg_price']
                new_qty = old_qty + quantity
                new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty
                self.portfolio[symbol] = {'quantity': new_qty, 'avg_price': new_avg}
            else:
                self.portfolio[symbol] = {'quantity': quantity, 'avg_price': price}
            pnl = 0.0
            msg = f"Bought {quantity} shares of {symbol} for ₹{total:,.2f}"
        else:
            # SELL
            old_avg = self.portfolio[symbol]['avg_price']
            old_qty = self.portfolio[symbol]['quantity']
            new_qty = old_qty - quantity
            pnl = (price - old_avg) * quantity
            self.dummy_balance += total
            if new_qty <= 0:
                del self.portfolio[symbol]
            else:
                # keep avg price for remaining
                self.portfolio[symbol]['quantity'] = new_qty
            msg = f"Sold {quantity} shares of {symbol} for ₹{total:,.2f} (P&L: ₹{pnl:+.2f})"

        # Record order in history
        order_record = {
            'timestamp': datetime.now().isoformat(),
            'type': order_type,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total': total,
            'pnl': pnl
        }
        self.order_history.append(order_record)
        logging.info(f"Order executed: {order_record}")

        self.update_portfolio_display()
        self.update_balance_display()
        messagebox.showinfo('Order Executed', msg)
        self.status_bar.config(text=f"{order_type} executed for {quantity} {symbol}")

    def update_balance_display(self):
        # Update balance label and compute portfolio value
        self.balance_label.config(text=f"Available Balance: ₹{self.dummy_balance:,.2f}")
        portfolio_value = 0.0
        for sym, holding in list(self.portfolio.items()):
            cur = self.get_current_stock_price(sym)
            if cur:
                portfolio_value += holding['quantity'] * cur
        total = self.dummy_balance + portfolio_value
        self.portfolio_value_label.config(text=f"Portfolio Value: ₹{portfolio_value:,.2f}")
        self.total_value_label.config(text=f"Total Value: ₹{total:,.2f}")

    def update_portfolio_display(self):
        # Clear tree
        for i in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(i)
        for sym, holding in self.portfolio.items():
            cur = self.get_current_stock_price(sym) or 0.0
            qty = holding['quantity']
            avg = holding['avg_price']
            pnl = (cur - avg) * qty
            pnl_percent = ((cur - avg) / avg * 100) if avg else 0.0
            pnl_text = f"₹{pnl:+.2f} ({pnl_percent:+.2f}%)"
            tag = 'profit' if pnl >= 0 else 'loss'
            self.portfolio_tree.insert('', 'end', values=(sym, qty, f'₹{avg:.2f}', f'₹{cur:.2f}', pnl_text), tags=(tag,))
        # Update balances
        self.update_balance_display()

    # -------------------- Export --------------------
    def export_orders_csv(self):
        if not self.order_history:
            messagebox.showinfo('Export Orders', 'No orders to export')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files','*.csv')], initialfile='orders.csv')
        if not path:
            return
        try:
            df = pd.DataFrame(self.order_history)
            df.to_csv(path, index=False)
            messagebox.showinfo('Export', f'Order history exported to {path}')
        except Exception as e:
            logging.exception('Error exporting orders')
            self.show_error(f'Error exporting orders: {e}')

    # -------------------- Utilities --------------------
    def clear_search(self):
        self.symbol_entry.delete(0, 'end')
        self.results_listbox.delete(0, 'end')
        self.info_label.config(text='Select a stock to view information')
        self.price_label.config(text='Current Price: -', foreground='blue')
        try:
            self.current_price_text.state(['!readonly'])
            self.current_price_text.delete(0, 'end')
            self.current_price_text.insert(0, '₹0.00')
            self.current_price_text.state(['readonly'])
        except Exception:
            pass
        self.ax.clear()
        self.ax.text(0.5,0.5,'Select a stock to view candlestick chart', ha='center')
        self.canvas.draw()

    def show_error(self, message):
        messagebox.showerror('Error', message)
        self.status_bar.config(text=f'Error: {message}')

    def on_window_resize(self, event):
        if event.widget == self.root:
            new_width = event.width - 50
            self.info_label.config(wraplength=new_width)
            self.status_bar.config(text=f'Window: {event.width}x{event.height} | Balance: ₹{self.dummy_balance:,.2f}')

    def auto_refresh(self):
        try:
            if self.symbol_entry.get().strip():
                self.get_current_price()
            # Refresh portfolio prices
            self.update_portfolio_display()
        except Exception:
            logging.exception('Auto-refresh error')
        finally:
            self.root.after(AUTO_REFRESH_MS, self.auto_refresh)


if __name__ == '__main__':
    root = tk.Tk()
    app = StockTradingApp(root)
    root.mainloop()
