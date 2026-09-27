# -*- coding: utf-8 -*-
import os
import sqlite3
import hashlib
import time
import random
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, Response, send_file, jsonify
import csv
import io

app = Flask(__name__)
app.secret_key = "VAJRA_PRO_SUPREME_2026"

DB_NAME = "vajra_erp.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, mobile TEXT, email TEXT)''')
            
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'VajraERP'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password, mobile, email) VALUES (?, ?, ?, ?)",
                           ("VajraERP", "Vajra@erp", "9876543210", "panchalnikunjait@gmail.com"))
        
        conn.execute('''CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, voucher_type TEXT, 
            ledger_name TEXT, amount REAL, gst_amount REAL, total_with_gst REAL, narration TEXT, crypto_hash TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, sku TEXT, 
            qty INTEGER, price REAL, movement_type TEXT, market_status TEXT DEFAULT 'REGULAR', timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, category TEXT, amount REAL, note TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, bank_name TEXT, account_no TEXT, balance REAL DEFAULT 0.0)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS bank_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, bank_id INTEGER, tx_type TEXT, amount REAL, payment_mode TEXT, narration TEXT, date TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS advances (
            id INTEGER PRIMARY KEY AUTOINCREMENT, party_name TEXT, adv_type TEXT, amount REAL, status TEXT DEFAULT 'PENDING', date TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS trading_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, asset_type TEXT, action_type TEXT, buy_price REAL, qty REAL, timestamp TEXT)''')

init_db()

def generate_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vajra Sovereign ERP & Pro Terminal - Login</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #030712; color: #fff; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        .card { background: linear-gradient(135deg, #111827 0%, #0f172a 100%); padding: 35px 30px; border-radius: 16px; width: 100%; max-width: 400px; border: 1px solid #1f2937; text-align: center; box-shadow: 0 25px 60px rgba(0,0,0,0.9); }
        .logo-box { width: 70px; height: 70px; background: linear-gradient(135deg, #3b82f6, #1d4ed8); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin: 0 auto 15px auto; box-shadow: 0 0 20px rgba(59,130,246,0.5); }
        .logo-box i { font-size: 2em; color: #fff; }
        h2 { color: #38bdf8; margin: 0 0 5px 0; font-size: 1.25em; }
        p { color: #94a3b8; font-size: 0.85em; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 8px 0; background: #030712; border: 1px solid #374151; color: #fff; border-radius: 8px; box-sizing: border-box; font-size: 0.95em; }
        input:focus { border-color: #3b82f6; outline: none; }
        button { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; border: none; padding: 13px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 1em; margin-top: 12px; }
        button:hover { background: linear-gradient(135deg, #2563eb, #1d4ed8); }
        .error { color: #f43f5e; background: rgba(244,63,94,0.1); padding: 10px; border-radius: 8px; font-size: 0.85em; margin-bottom: 15px; border: 1px solid #f43f5e; text-align: left; }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo-box"><i class="fas fa-shield-alt"></i></div>
        <h2>Vajra Sovereign ERP</h2>
        <p>Enterprise & Pro Trading Suite</p>
        {% if error %}<div class="error"><i class="fas fa-exclamation-triangle"></i> {{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username (VajraERP)" required autocomplete="off">
            <input type="password" name="password" placeholder="Password (Vajra@erp)" required autocomplete="off">
            <button type="submit"><i class="fas fa-lock-open"></i> Secure Login</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vajra ERP & Business Suite</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #030712; color: #f8f9fa; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 15px; box-sizing: border-box; }
        header { background: #0f172a; padding: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #3b82f6; border-radius: 10px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { margin: 0; font-size: 1.25em; color: #38bdf8; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        
        .pro-banner { background: linear-gradient(135deg, #1e1b4b, #312e81); border: 2px solid #3b82f6; padding: 20px; border-radius: 12px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; gap: 15px; flex-wrap: wrap; box-shadow: 0 10px 30px rgba(59,130,246,0.25); }
        .pro-banner h3 { margin: 0 0 5px 0; color: #e0e7ff; font-size: 1.2em; }
        .pro-banner p { margin: 0; color: #c7d2fe; font-size: 0.9em; }
        .launch-btn { background: #10b981; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1em; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 15px rgba(16,185,129,0.4); white-space: nowrap; }
        .launch-btn:hover { background: #059669; }

        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }
        .kpi { background: #111827; padding: 15px; border-radius: 10px; border: 1px solid #1f2937; box-shadow: 0 8px 20px rgba(0,0,0,0.3); }
        .kpi h3 { margin: 0; font-size: 0.7em; color: #94a3b8; text-transform: uppercase; }
        .kpi p { margin: 6px 0 0 0; font-size: 1.25em; font-weight: bold; color: #38bdf8; }

        .main-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .card { background: #111827; padding: 18px; border-radius: 10px; border: 1px solid #1f2937; box-shadow: 0 8px 20px rgba(0,0,0,0.3); overflow-x: auto; }
        .card h3 { margin-top: 0; color: #38bdf8; font-size: 1.05em; border-bottom: 1px solid #1f2937; padding-bottom: 8px; display: flex; align-items: center; gap: 8px; }
        
        label { font-size: 0.85em; color: #94a3b8; font-weight: bold; display: block; margin-top: 8px; }
        input, select { width: 100%; padding: 10px; margin-top: 4px; background: #030712; border: 1px solid #374151; color: #fff; border-radius: 6px; box-sizing: border-box; font-size: 0.95em; }
        button { background: #3b82f6; color: #fff; border: none; padding: 11px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 12px; }
        button:hover { background: #2563eb; }
        
        .btn-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
        .btn-row a { background: #374151; color: white; padding: 10px 14px; border-radius: 6px; text-decoration: none; font-size: 0.85em; font-weight: bold; display: inline-flex; align-items: center; gap: 6px; }
        .logout { background: #f43f5e !important; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.85em; }
        th, td { border: 1px solid #1f2937; padding: 8px; text-align: left; }
        th { background: #0f172a; color: #38bdf8; }
    </style>
</head>
<body>
    <header>
        <h1>
            <i class="fas fa-shield-alt"></i> VAJRA ERP & BUSINESS SUITE
            <span style="font-size: 0.65em; background: rgba(59,130,246,0.2); border: 1px solid #3b82f6; padding: 2px 8px; border-radius: 15px; color: #38bdf8;">
                <i class="fas fa-user-circle"></i> {{ username }}
            </span>
        </h1>
        <div style="display: flex; gap: 8px; align-items: center;">
            <span style="font-family: monospace; color: #34d399; font-size: 0.8em;"><i class="fas fa-bolt"></i> {{ query_latency }} ms</span>
            <a href="/logout" class="logout" style="padding: 6px 12px; border-radius: 6px; text-decoration:none; font-size:0.85em; font-weight:bold; color:#fff;">Logout</a>
        </div>
    </header>
    
    <!-- 🚀 DEDICATED PRO TRADING TERMINAL LAUNCH BANNER -->
    <div class="pro-banner">
        <div>
            <h3><i class="fas fa-rocket"></i> Vajra Pro Trading Terminal (Upstox & Groww Mode)</h3>
            <p>Access live futures, options chain, SIP, earn, global futures, and TradingView charts in a dedicated professional workspace without altering core ERP data.</p>
        </div>
        <a href="/pro_trading_hub" class="launch-btn"><i class="fas fa-external-link-alt"></i> Open Pro Trading World</a>
    </div>

    <div class="btn-row">
        <a href="/backup_db"><i class="fas fa-database"></i> Backup DB</a>
        <a href="/export_inventory_csv"><i class="fas fa-download"></i> Export CSV</a>
        <a href="/print_report_view"><i class="fas fa-print"></i> Print Report</a>
    </div>

    <div class="kpi-grid">
        <div class="kpi"><h3>Total Revenue</h3><p>₹{{ "%.2f"|format(kpis.revenue) }}</p></div>
        <div class="kpi"><h3>Net Profit (P&L)</h3><p>₹{{ "%.2f"|format(kpis.profit) }}</p></div>
        <div class="kpi"><h3>Total Bank Balance</h3><p style="color: #34d399;">₹{{ "%.2f"|format(kpis.bank_bal) }}</p></div>
        <div class="kpi"><h3>Net Advances</h3><p>₹{{ "%.2f"|format(kpis.advances) }}</p></div>
    </div>

    <div class="main-grid">
        <div class="card">
            <h3><i class="fas fa-book-open"></i> Accounting & GST Voucher</h3>
            <form action="/add_voucher" method="POST">
                <label>Voucher Type:</label>
                <select name="voucher_type">
                    <option value="RECEIPT">RECEIPT</option>
                    <option value="PAYMENT">PAYMENT</option>
                    <option value="SALES">SALES</option>
                    <option value="PURCHASE">PURCHASE</option>
                </select>
                <label>Party / Ledger Name:</label><input type="text" name="ledger_name" required>
                <label>Base Amount (₹):</label><input type="number" step="0.01" name="amount" required>
                <label>Narration:</label><input type="text" name="narration">
                <button type="submit">Save Voucher (Auto 18% GST)</button>
            </form>
        </div>

        <div class="card">
            <h3><i class="fas fa-boxes"></i> Inventory Control</h3>
            <form action="/add_inventory" method="POST">
                <label>Movement Type:</label>
                <select name="movement_type"><option value="INWARD">INWARD</option><option value="OUTWARD">OUTWARD</option></select>
                <label>Item Name:</label><input type="text" name="item_name" required>
                <label>SKU Code:</label><input type="text" name="sku" required>
                <div style="display: flex; gap: 8px; margin-top: 8px;">
                    <div style="flex:1;"><label>Qty:</label><input type="number" name="qty" required></div>
                    <div style="flex:1;"><label>Price (₹):</label><input type="number" step="0.01" name="price" required></div>
                </div>
                <button type="submit">Update Stock</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

TRADING_WORLD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vajra Pro Trading World - Upstox/Groww Edition</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #000000; color: #f8f9fa; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 0; box-sizing: border-box; }
        .app-header { background: #121212; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2a2a2a; position: sticky; top: 0; z-index: 100; }
        .back-btn { background: #2a2a2a; color: #fff; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 0.9em; display: inline-flex; align-items: center; gap: 8px; }
        .back-btn:hover { background: #3b3b3b; }
        
        .exchange-tabs { display: flex; gap: 20px; background: #121212; padding: 0 20px; border-bottom: 1px solid #2a2a2a; overflow-x: auto; }
        .ex-tab { background: transparent; border: none; color: #9ca3af; font-weight: bold; cursor: pointer; font-size: 1em; padding: 15px 5px; white-space: nowrap; border-bottom: 3px solid transparent; }
        .ex-tab.active { color: #10b981; border-bottom: 3px solid #10b981; }

        .tab-content { display: none; padding: 20px; }
        .tab-content.active { display: block; }

        .exchange-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        @media(max-width: 900px) { .exchange-grid { grid-template-columns: 1fr; } }

        .ex-card { background: #121212; border: 1px solid #2a2a2a; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        .ex-card h3 { color: #fff; margin-top: 0; display: flex; justify-content: space-between; align-items: center; font-size: 1.1em; border-bottom: 1px solid #2a2a2a; padding-bottom: 12px; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9em; }
        th, td { border: 1px solid #2a2a2a; padding: 12px; text-align: left; }
        th { background: #1a1a1a; color: #9ca3af; font-weight: 600; }
        
        input, select { width: 100%; padding: 12px; margin-top: 8px; background: #1a1a1a; border: 1px solid #333; color: #fff; border-radius: 8px; box-sizing: border-box; }
        button.buy-btn { background: #10b981; color: white; border: none; padding: 14px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 15px; font-size: 1.05em; }
        button.buy-btn:hover { background: #059669; }
        
        .market-ticker { display: flex; gap: 15px; overflow-x: auto; padding: 15px 20px; background: #0a0a0a; border-bottom: 1px solid #2a2a2a; }
        .ticker-pill { background: #121212; border: 1px solid #2a2a2a; padding: 10px 15px; border-radius: 8px; min-width: 150px; text-align: center; }
        .ticker-pill .val { color: #10b981; font-weight: bold; font-size: 1.1em; margin-top: 4px; }
    </style>
</head>
<body>
    <div class="app-header">
        <div style="display: flex; align-items: center; gap: 15px;">
            <a href="/dashboard" class="back-btn"><i class="fas fa-arrow-left"></i> Exit to ERP Dashboard</a>
            <h2 style="margin: 0; font-size: 1.3em; color: #10b981;"><i class="fas fa-bolt"></i> VAJRA PRO EXCHANGE (Upstox / Groww Edition)</h2>
        </div>
        <div style="color: #9ca3af; font-size: 0.9em;">
            <i class="fas fa-circle" style="color: #10b981; font-size: 0.7em;"></i> Live Feed Connected (24x7)
        </div>
    </div>

    <!-- TABS NAVIGATION -->
    <div class="exchange-tabs">
        <button class="ex-tab active" onclick="switchTab(event, 'tab-explore')">Explore / Gainers</button>
        <button class="ex-tab" onclick="switchTab(event, 'tab-futures')">Futures & Options</button>
        <button class="ex-tab" onclick="switchTab(event, 'tab-options')">Option Chain</button>
        <button class="ex-tab" onclick="switchTab(event, 'tab-global')">Global Futures (US Stocks)</button>
        <button class="ex-tab" onclick="switchTab(event, 'tab-sip')">SIP & Mutual Funds</button>
        <button class="ex-tab" onclick="switchTab(event, 'tab-orders')">Orders & Portfolio</button>
    </div>

    <!-- TICKER STRIP -->
    <div class="market-ticker">
        <div class="ticker-pill"><div style="font-size:0.8em; color:#9ca3af;">NIFTY 50 (NSE)</div><div class="val">₹24,850.30</div></div>
        <div class="ticker-pill"><div style="font-size:0.8em; color:#9ca3af;">SENSEX (BSE)</div><div class="val">₹81,420.10</div></div>
        <div class="ticker-pill"><div style="font-size:0.8em; color:#9ca3af;">BITCOIN (BTC)</div><div class="val">₹74,50,000</div></div>
        <div class="ticker-pill"><div style="font-size:0.8em; color:#9ca3af;">NSDQ 100</div><div class="val">25,259.00</div></div>
    </div>

    <!-- TAB 1: EXPLORE / GAINERS -->
    <div id="tab-explore" class="tab-content active">
        <div class="exchange-grid">
            <div>
                <div class="ex-card">
                    <h3><span><i class="fas fa-chart-candlestick" style="color: #38bdf8;"></i> TradingView Pro Live Chart</span></h3>
                    <div style="width: 100%; height: 350px; background: #000; border: 1px solid #2a2a2a; border-radius: 8px;">
                        <canvas id="exploreChart" style="width: 100%; height: 100%;"></canvas>
                    </div>
                </div>
                <div class="ex-card">
                    <h3><span><i class="fas fa-fire" style="color: #f59e0b;"></i> MTF Smartlist & Top Gainers (NSE/BSE 1100+ Stocks)</span></h3>
                    <table>
                        <tr><th>Stock / Corp Name</th><th>Segment</th><th>LTP</th><th>24h Change</th></tr>
                        <tr><td><strong>RELIANCE INDUSTRIES</strong></td><td>EQ</td><td>₹2,940.15</td><td style="color: #10b981;">+4.04%</td></tr>
                        <tr><td><strong>TATA MOTORS</strong></td><td>EQ</td><td>₹980.25</td><td style="color: #10b981;">+6.09%</td></tr>
                        <tr><td><strong>INFOSYS LTD</strong></td><td>EQ</td><td>₹1,850.40</td><td style="color: #10b981;">+2.85%</td></tr>
                        <tr><td><strong>HDFC BANK</strong></td><td>EQ</td><td>₹1,670.80</td><td style="color: #10b981;">+1.95%</td></tr>
                    </table>
                </div>
            </div>
            <div>
                <div class="ex-card" style="border: 1.5px solid #10b981;">
                    <h3><span><i class="fas fa-shopping-cart"></i> Instant Order Execution</span></h3>
                    <form action="/add_watchlist" method="POST">
                        <label style="color:#9ca3af;">Symbol Search:</label>
                        <input type="text" name="symbol" required placeholder="e.g. RELIANCE, TCS, BTC">
                        <label style="color:#9ca3af;">Segment:</label>
                        <select name="asset_type">
                            <option value="STOCK">NSE/BSE Equity</option>
                            <option value="CRYPTO">Crypto Futures</option>
                            <option value="COMMODITY">Global Commodity</option>
                        </select>
                        <label style="color:#9ca3af;">Action Type:</label>
                        <select name="action_type">
                            <option value="BUY">BUY (Long)</option>
                            <option value="SELL">SELL (Short)</option>
                        </select>
                        <label style="color:#9ca3af;">Limit / Market Price (₹):</label>
                        <input type="number" step="0.01" name="buy_price" required placeholder="0.00">
                        <label style="color:#9ca3af;">Quantity / Lots:</label>
                        <input type="number" step="0.01" name="qty" required placeholder="1">
                        <button type="submit" class="buy-btn">Place Order (Instant)</button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 2: FUTURES & OPTIONS -->
    <div id="tab-futures" class="tab-content">
        <div class="ex-card">
            <h3><i class="fas fa-rocket"></i> Nifty & BankNifty Futures (Live Expiry)</h3>
            <p style="color:#9ca3af;">Trade high-liquidity index and stock futures with instant margin calculation.</p>
            <table>
                <tr><th>Contract Name</th><th>Expiry Date</th><th>LTP (₹)</th><th>Open Interest (OI)</th><th>Action</th></tr>
                <tr><td><strong>NIFTY 28OCT FUT</strong></td><td>28-Oct-2026</td><td>₹24,880.50</td><td>1.45 Cr</td><td><button style="background:#10b981; padding:6px 12px; width:auto;">Trade Future</button></td></tr>
                <tr><td><strong>BANKNIFTY 28OCT FUT</strong></td><td>28-Oct-2026</td><td>₹51,400.00</td><td>98 Lakh</td><td><button style="background:#10b981; padding:6px 12px; width:auto;">Trade Future</button></td></tr>
                <tr><td><strong>RELIANCE 28OCT FUT</strong></td><td>28-Oct-2026</td><td>₹2,955.00</td><td>45 Lakh</td><td><button style="background:#10b981; padding:6px 12px; width:auto;">Trade Future</button></td></tr>
            </table>
        </div>
    </div>

    <!-- TAB 3: OPTION CHAIN -->
    <div id="tab-options" class="tab-content">
        <div class="ex-card">
            <h3><i class="fas fa-table-cells"></i> Advanced Option Chain & PCR Analytics (Upstox Pro Style)</h3>
            <p style="color:#9ca3af;">Spot Price: <strong style="color:#10b981;">₹24,850.30</strong> | PCR: <strong>2.24 (Bullish)</strong></p>
            <table>
                <tr><th>CALL OI (Lakhs)</th><th>CALL LTP</th><th>STRIKE PRICE</th><th>PUT LTP</th><th>PUT OI (Lakhs)</th></tr>
                <tr><td>45.2</td><td>₹764.00</td><td><strong style="color:#38bdf8;">16,150</strong></td><td>₹15.00</td><td>12.4</td></tr>
                <tr><td>32.1</td><td>₹444.50</td><td><strong style="color:#38bdf8;">16,200</strong></td><td>₹43.00</td><td>24.8</td></tr>
                <tr><td>18.5</td><td>₹263.00</td><td><strong style="color:#38bdf8;">16,250</strong></td><td>₹66.00</td><td>51.2</td></tr>
                <tr><td>12.0</td><td>₹220.00</td><td><strong style="color:#38bdf8;">16,300</strong></td><td>₹84.00</td><td>78.5</td></tr>
            </table>
        </div>
    </div>

    <!-- TAB 4: GLOBAL FUTURES -->
    <div id="tab-global" class="tab-content">
        <div class="ex-card">
            <h3><i class="fas fa-globe"></i> Global Futures in INR (24x7 US Tech Giants)</h3>
            <table>
                <tr><th>Global Giant</th><th>Symbol</th><th>LTP</th><th>24h Change</th></tr>
                <tr><td><strong>NASDAQ 100</strong></td><td>NSDQ100 / USDC</td><td>₹24,24,624.00</td><td style="color:#10b981;">+0.58%</td></tr>
                <tr><td><strong>GOOGLE (ALPHABET)</strong></td><td>GOOGL / USDC</td><td>₹29,997.10</td><td style="color:#f43f5e;">-2.21%</td></tr>
                <tr><td><strong>NVIDIA CORP</strong></td><td>NVDA / USDC</td><td>₹18,377.51</td><td style="color:#10b981;">+1.58%</td></tr>
                <tr><td><strong>TESLA INC</strong></td><td>TSLA / USDC</td><td>₹41,188.85</td><td style="color:#10b981;">+1.30%</td></tr>
            </table>
        </div>
    </div>

    <!-- TAB 5: SIP & MUTUAL FUNDS -->
    <div id="tab-sip" class="tab-content">
        <div class="ex-card">
            <h3><i class="fas fa-piggy-bank"></i> Vajra Smart SIP & High-Yield Earn Funds</h3>
            <p style="color:#9ca3af;">Automated mutual fund investments starting from ₹500/month with zero commission.</p>
            <table>
                <tr><th>Fund Name</th><th>Category</th><th>3Y Returns (CAGR)</th><th>Risk Level</th><th>Action</th></tr>
                <tr><td><strong>Vajra Bluechip Equity Fund</strong></td><td>Large Cap</td><td>22.4%</td><td>Moderate</td><td><button style="background:#3b82f6; padding:6px 12px; width:auto;">Start SIP</button></td></tr>
                <tr><td><strong>Sovereign Tech Opportunities Fund</strong></td><td>Sectoral / Thematic</td><td>28.6%</td><td>High</td><td><button style="background:#3b82f6; padding:6px 12px; width:auto;">Start SIP</button></td></tr>
            </table>
        </div>
    </div>

    <!-- TAB 6: ORDERS & PORTFOLIO -->
    <div id="tab-orders" class="tab-content">
        <div class="ex-card">
            <h3><i class="fas fa-receipt"></i> Active Orders & Holdings Portfolio</h3>
            <p style="color:#9ca3af;">Manage your active executions, open positions, and profit/loss summary.</p>
            <table>
                <tr><th>Symbol</th><th>Type</th><th>Action</th><th>Price</th><th>Qty</th><th>Status</th></tr>
                <tr><td>RELIANCE</td><td>STOCK</td><td>BUY</td><td>₹2,940.15</td><td>5.0</td><td><span style="color:#10b981; font-weight:bold;">EXECUTED (LIVE)</span></td></tr>
                <tr><td>BTC</td><td>CRYPTO</td><td>BUY</td><td>₹74,50,000</td><td>0.01</td><td><span style="color:#10b981; font-weight:bold;">EXECUTED (LIVE)</span></td></tr>
            </table>
        </div>
    </div>

    <script>
        function switchTab(evt, tabName) {
            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
            document.querySelectorAll('.ex-tab').forEach(et => et.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            evt.currentTarget.classList.add('active');
        }

        const ctxEx = document.getElementById('exploreChart').getContext('2d');
        new Chart(ctxEx, {
            type: 'line',
            data: {
                labels: ['09:15', '10:00', '11:00', '12:00', '13:00', '14:00', '15:30'],
                datasets: [{
                    label: 'NIFTY / SENSEX Live Feed',
                    data: [24750, 24780, 24730, 24820, 24800, 24850, 24850.3],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.08)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.25
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#9ca3af' } } },
                scales: {
                    x: { ticks: { color: '#9ca3af' }, grid: { color: '#1a1a1a' } },
                    y: { ticks: { color: '#10b981' }, grid: { color: '#1a1a1a' } }
                }
            }
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    error, msg = None, request.args.get("msg")
    if request.method == "GET": session.clear()
    if session.get("logged_in"): return redirect(url_for("dashboard"))
    if request.method == "POST":
        if request.form.get("username") == "VajraERP" and request.form.get("password") == "Vajra@erp":
            session["logged_in"] = True
            session["username"] = "VajraERP"
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid Credentials!"
    return render_template_string(LOGIN_HTML, error=error, msg=msg)

@app.route("/register", methods=["GET", "POST"])
def register():
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"): return redirect(url_for("login"))
    start_time = time.time()
    with sqlite3.connect(DB_NAME) as conn:
        revenue = conn.execute("SELECT SUM(total_with_gst) FROM vouchers WHERE voucher_type IN ('RECEIPT', 'SALES')").fetchone()[0] or 0.0
        expenses = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0.0
        banks = conn.execute("SELECT * FROM bank_accounts").fetchall()
        bank_bal = sum(b[3] for b in banks) if banks else 0.0
        adv_rows = conn.execute("SELECT adv_type, amount FROM advances WHERE status='PENDING'").fetchall()
        net_advances = sum(amt if t=='TAKEN' else -amt for t, amt in adv_rows)
        profit = revenue - expenses
        kpis = {"revenue": revenue, "expenses": expenses, "profit": profit, "bank_bal": bank_bal, "advances": net_advances}
    query_latency = round((time.time() - start_time) * 1000, 2)
    return render_template_string(DASHBOARD_HTML, kpis=kpis, query_latency=query_latency, username=session.get("username", "Admin"))

@app.route("/pro_trading_hub")
def pro_trading_hub():
    if not session.get("logged_in"): return redirect(url_for("login"))
    return render_template_string(TRADING_WORLD_HTML)

@app.route("/add_watchlist", methods=["POST"])
def add_watchlist():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO trading_portfolio (symbol, asset_type, action_type, buy_price, qty, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                     (request.form.get("symbol"), request.form.get("asset_type"), request.form.get("action_type"), float(request.form.get("buy_price")), float(request.form.get("qty")), datetime.now().strftime("%Y-%m-%d %H:%M")))
    return redirect(url_for("pro_trading_hub"))

@app.route("/print_report_view")
def print_report_view():
    if not session.get("logged_in"): return redirect(url_for("login"))
    return "Report View"

@app.route("/export_inventory_csv")
def export_inventory_csv():
    if not session.get("logged_in"): return redirect(url_for("login"))
    return "id,item,sku,qty\n1,Sample,SKU01,10", 200, {"Content-Type": "text/csv"}

@app.route("/backup_db")
def backup_db():
    if not session.get("logged_in"): return redirect(url_for("login"))
    return send_file(os.path.abspath(DB_NAME), as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5027))
    app.run(host="0.0.0.0", port=port)
