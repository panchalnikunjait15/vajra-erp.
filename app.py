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
    <title>Vajra Sovereign Pro Terminal - Secure Login</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #030712; color: #fff; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        .card { background: linear-gradient(135deg, #111827 0%, #0f172a 100%); padding: 35px 30px; border-radius: 16px; width: 100%; max-width: 400px; border: 1px solid #1f2937; text-align: center; box-shadow: 0 25px 60px rgba(0,0,0,0.9), 0 0 30px rgba(59,130,246,0.15); }
        .logo-box { width: 70px; height: 70px; background: linear-gradient(135deg, #3b82f6, #1d4ed8); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin: 0 auto 15px auto; box-shadow: 0 0 20px rgba(59,130,246,0.5); border: 2px solid #60a5fa; }
        .logo-box i { font-size: 2em; color: #fff; }
        h2 { color: #38bdf8; margin: 0 0 5px 0; font-size: 1.25em; letter-spacing: 0.5px; }
        p { color: #94a3b8; font-size: 0.85em; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 8px 0; background: #030712; border: 1px solid #374151; color: #fff; border-radius: 8px; box-sizing: border-box; font-size: 0.95em; }
        input:focus { border-color: #3b82f6; outline: none; box-shadow: 0 0 10px rgba(59,130,246,0.3); }
        .captcha-container { background: #0f172a; border: 1px solid #374151; padding: 12px; border-radius: 8px; margin: 12px 0; display: flex; align-items: center; justify-content: space-between; font-size: 1.1em; color: #38bdf8; font-family: monospace; font-weight: bold; }
        button { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; border: none; padding: 13px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 1em; margin-top: 12px; box-shadow: 0 4px 15px rgba(59,130,246,0.4); }
        button:hover { background: linear-gradient(135deg, #2563eb, #1d4ed8); }
        .error { color: #f43f5e; background: rgba(244,63,94,0.1); padding: 10px; border-radius: 8px; font-size: 0.85em; margin-bottom: 15px; border: 1px solid #f43f5e; text-align: left; }
        .success { color: #34d399; background: rgba(52,211,153,0.1); padding: 10px; border-radius: 8px; font-size: 0.85em; margin-bottom: 15px; border: 1px solid #34d399; text-align: left; }
        .link-text { margin-top: 15px; font-size: 0.85em; color: #94a3b8; }
        .link-text a { color: #38bdf8; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo-box"><i class="fas fa-chart-line"></i></div>
        <h2>Vajra Sovereign Pro Terminal</h2>
        <p>Supreme Global Secure Portal</p>
        
        {% if error %}<div class="error"><i class="fas fa-exclamation-triangle"></i> {{ error }}</div>{% endif %}
        {% if msg %}<div class="success"><i class="fas fa-check-circle"></i> {{ msg }}</div>{% endif %}

        <form method="POST">
            <input type="text" name="username" placeholder="Enterprise Username" required autocomplete="off">
            <input type="password" name="password" placeholder="Master Password" required autocomplete="off">
            
            <div class="captcha-container">
                <span><i class="fas fa-calculator" style="margin-right: 8px;"></i> Solve: {{ math_question }}</span>
            </div>
            <input type="number" name="math_input" placeholder="Enter Math Answer" required autocomplete="off">

            <button type="submit"><i class="fas fa-lock-open"></i> Secure Pro Login</button>
        </form>
        
        <div class="link-text">
            Don't have an account? <a href="/register">Register New User</a>
        </div>
    </div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vajra Sovereign Pro Terminal - User Registration</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #030712; color: #fff; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        .card { background: linear-gradient(135deg, #111827 0%, #0f172a 100%); padding: 35px 30px; border-radius: 16px; width: 100%; max-width: 400px; border: 1px solid #1f2937; text-align: center; box-shadow: 0 25px 60px rgba(0,0,0,0.9), 0 0 30px rgba(59,130,246,0.15); }
        .logo-box { width: 70px; height: 70px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin: 0 auto 15px auto; box-shadow: 0 0 20px rgba(16,185,129,0.5); border: 2px solid #34d399; }
        .logo-box i { font-size: 2em; color: #fff; }
        h2 { color: #34d399; margin: 0 0 5px 0; font-size: 1.25em; letter-spacing: 0.5px; }
        p { color: #94a3b8; font-size: 0.85em; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 8px 0; background: #030712; border: 1px solid #374151; color: #fff; border-radius: 8px; box-sizing: border-box; font-size: 0.95em; }
        input:focus { border-color: #10b981; outline: none; box-shadow: 0 0 10px rgba(16,185,129,0.3); }
        button { background: linear-gradient(135deg, #10b981, #059669); color: white; border: none; padding: 13px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 1em; margin-top: 12px; box-shadow: 0 4px 15px rgba(16,185,129,0.4); }
        button:hover { background: linear-gradient(135deg, #059669, #047857); }
        .error { color: #f43f5e; background: rgba(244,63,94,0.1); padding: 10px; border-radius: 8px; font-size: 0.85em; margin-bottom: 15px; border: 1px solid #f43f5e; text-align: left; }
        .link-text { margin-top: 15px; font-size: 0.85em; color: #94a3b8; }
        .link-text a { color: #38bdf8; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo-box"><i class="fas fa-user-plus"></i></div>
        <h2>Vajra Sovereign Pro Terminal</h2>
        <p>New Pro Trader Registration</p>
        
        {% if error %}<div class="error"><i class="fas fa-exclamation-triangle"></i> {{ error }}</div>{% endif %}

        <form method="POST">
            <input type="text" name="username" placeholder="Choose Username" required autocomplete="off">
            <input type="password" name="password" placeholder="Create Master Password" required autocomplete="off">
            <input type="text" name="mobile" placeholder="Mobile Number (10-digit)" required autocomplete="off">
            <input type="email" name="email" placeholder="Gmail Address" required autocomplete="off">

            <button type="submit"><i class="fas fa-user-check"></i> Register Account</button>
        </form>
        
        <div class="link-text">
            Already registered? <a href="/">Back to Login</a>
        </div>
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
    <title>Vajra Pro Terminal - Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #030712; color: #f8f9fa; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 15px; box-sizing: border-box; }
        header { background: #0f172a; padding: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #3b82f6; border-radius: 10px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { margin: 0; font-size: 1.25em; color: #38bdf8; letter-spacing: 0.5px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        
        .lang-switcher { display: flex; gap: 4px; background: #030712; padding: 3px; border-radius: 6px; border: 1px solid #1f2937; }
        .lang-btn { background: transparent; border: none; color: #94a3b8; padding: 6px 10px; cursor: pointer; font-size: 0.85em; font-weight: bold; border-radius: 4px; transition: 0.2s; }
        .lang-btn.active { background: #3b82f6; color: white; }

        .terminal-layout { display: grid; grid-template-columns: 2fr 1fr; gap: 15px; margin-bottom: 20px; }
        @media(max-width: 900px) { .terminal-layout { grid-template-columns: 1fr; } }

        .pro-nav-bar { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; margin-bottom: 20px; }
        .pro-nav-btn { background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid #3b82f6; color: #38bdf8; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; text-align: center; font-size: 0.9em; transition: 0.2s; display: flex; flex-direction: column; align-items: center; gap: 5px; text-decoration: none; }
        .pro-nav-btn:hover { background: #3b82f6; color: #fff; transform: translateY(-2px); }

        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }
        .kpi { background: #111827; padding: 15px; border-radius: 10px; border: 1px solid #1f2937; box-shadow: 0 8px 20px rgba(0,0,0,0.3); }
        .kpi h3 { margin: 0; font-size: 0.7em; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
        .kpi p { margin: 6px 0 0 0; font-size: 1.25em; font-weight: bold; color: #38bdf8; word-break: break-all; }
        
        .ai-banner { background: linear-gradient(135deg, #1e1b4b, #312e81); border: 1px solid #6366f1; padding: 15px; border-radius: 10px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
        .ai-banner h3 { margin: 0 0 4px 0; color: #e0e7ff; font-size: 1.05em; }
        .ai-banner p { margin: 0; font-size: 0.85em; color: #c7d2fe; }

        .main-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .card { background: #111827; padding: 18px; border-radius: 10px; border: 1px solid #1f2937; box-shadow: 0 8px 20px rgba(0,0,0,0.3); overflow-x: auto; }
        .card h3 { margin-top: 0; color: #38bdf8; font-size: 1.05em; border-bottom: 1px solid #1f2937; padding-bottom: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 5px; }
        
        label { font-size: 0.85em; color: #94a3b8; font-weight: bold; display: block; margin-top: 8px; }
        input, select, textarea { width: 100%; padding: 10px; margin-top: 4px; background: #030712; border: 1px solid #374151; color: #fff; border-radius: 6px; box-sizing: border-box; font-size: 0.95em; }
        input:focus, select:focus { border-color: #3b82f6; outline: none; }
        button { background: #3b82f6; color: #fff; border: none; padding: 11px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 12px; font-size: 0.95em; transition: 0.2s; }
        button:hover { background: #2563eb; }
        
        .btn-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
        .btn-row a, .btn-row button { background: #374151; color: white; padding: 10px 14px; border-radius: 6px; text-decoration: none; font-size: 0.85em; border: none; flex: 1; min-width: 130px; text-align: center; font-weight: bold; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 6px; }
        .logout { background: #f43f5e !important; }

        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.85em; min-width: 320px; }
        th, td { border: 1px solid #1f2937; padding: 8px 6px; text-align: left; word-break: break-word; }
        th { background: #0f172a; color: #38bdf8; }
        
        @media(max-width: 600px) {
            body { padding: 8px; }
            header { padding: 10px; }
            h1 { font-size: 1.05em; }
            .card { padding: 12px; }
        }
    </style>
</head>
<body>
    <header>
        <h1>
            <i class="fas fa-chart-line"></i> <span data-key="header_title">VAJRA PRO TRADING TERMINAL</span>
            <span style="font-size: 0.65em; background: rgba(59,130,246,0.2); border: 1px solid #3b82f6; padding: 2px 8px; border-radius: 15px; color: #38bdf8;">
                <i class="fas fa-user-circle"></i> {{ username }}
            </span>
        </h1>
        
        <div class="lang-switcher">
            <button class="lang-btn active" onclick="setLanguage('en')">EN</button>
            <button class="lang-btn" onclick="setLanguage('hi')">हिन्दी</button>
            <button class="lang-btn" onclick="setLanguage('gu')">ગુજરાતી</button>
        </div>

        <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
            <span style="font-family: monospace; color: #34d399; font-size: 0.8em;"><i class="fas fa-bolt"></i> {{ query_latency }} ms</span>
            <a href="/logout" class="logout" style="padding: 6px 12px; background: #f43f5e; color: #fff; border-radius: 6px; text-decoration:none; font-size:0.85em; font-weight:bold;" data-key="logout">Logout</a>
        </div>
    </header>
    
    <div class="btn-row">
        <a href="/backup_db"><i class="fas fa-database"></i> <span data-key="backup_db">Backup DB</span></a>
        <a href="/export_inventory_csv"><i class="fas fa-download"></i> <span data-key="export_csv">Export CSV</span></a>
        <a href="/print_report_view"><i class="fas fa-print"></i> <span data-key="print_report">Print / Save PDF</span></a>
    </div>

    <!-- 🚀 UPSTOX / COINDCX STYLE PRO NAVIGATION DRAWER -> OPENS TRADING WORLD -->
    <div class="pro-nav-bar">
        <a href="/pro_trading_hub" class="pro-nav-btn">
            <i class="fas fa-rocket fa-lg"></i> <span data-key="nav_futures">Futures & Options</span>
        </a>
        <a href="/pro_trading_hub" class="pro-nav-btn">
            <i class="fas fa-table-cells fa-lg"></i> <span data-key="nav_options">Option Chain</span>
        </a>
        <a href="/pro_trading_hub" class="pro-nav-btn">
            <i class="fas fa-piggy-bank fa-lg"></i> <span data-key="nav_sip">SIP / Earn</span>
        </a>
        <a href="/pro_trading_hub" class="pro-nav-btn">
            <i class="fas fa-receipt fa-lg"></i> <span data-key="nav_orders">Orders Book</span>
        </a>
        <a href="/pro_trading_hub" class="pro-nav-btn">
            <i class="fas fa-globe fa-lg"></i> <span data-key="nav_global">Global Futures</span>
        </a>
    </div>

    <!-- 🔥 TOP GAINERS & SMARTLIST MODULE -->
    <div class="card" style="margin-bottom: 20px; border: 1.5px solid #10b981; background: linear-gradient(135deg, #0f172a 0%, #064e3b 30%, #0f172a 100%);">
        <h3><span><i class="fas fa-fire" style="color: #10b981;"></i> <span data-key="smartlist_title">MTF Smartlist & Top Gainers (Live 1100+ Stocks)</span></span></h3>
        <p style="color: #94a3b8; font-size: 0.8em; margin-bottom: 12px;" data-key="smartlist_desc">High momentum stocks with 4X leverage calculation simulation.</p>
        
        <table>
            <tr><th data-key="th_stock_name">Stock / Corp Name</th><th data-key="th_segment">Segment</th><th data-key="th_ltp">LTP (₹)</th><th data-key="th_change">24h Change</th></tr>
            <tr>
                <td><strong>ABC CORP. LTD.</strong></td>
                <td>XYZ EQ</td>
                <td>₹<span class="num-val" data-val="481.60">481.60</span></td>
                <td style="color: #34d399; font-weight: bold;">+<span class="num-val" data-val="35.50">35.50</span> (+<span class="num-val" data-val="7.96">7.96</span>%)</td>
            </tr>
            <tr>
                <td><strong>RELIANCE IND.</strong></td>
                <td>REL EQ</td>
                <td>₹<span class="num-val" data-val="2940.15">2940.15</span></td>
                <td style="color: #34d399; font-weight: bold;">+<span class="num-val" data-val="114.20">114.20</span> (+<span class="num-val" data-val="4.04">4.04</span>%)</td>
            </tr>
            <tr>
                <td><strong>TATA MOTORS</strong></td>
                <td>TATAMTR</td>
                <td>₹<span class="num-val" data-val="980.25">980.25</span></td>
                <td style="color: #34d399; font-weight: bold;">+<span class="num-val" data-val="56.30">56.30</span> (+<span class="num-val" data-val="6.09">6.09</span>%)</td>
            </tr>
        </table>
    </div>

    <!-- 📊 PRO TERMINAL LAYOUT (CHART + EXECUTION ENGINE) -->
    <div class="terminal-layout">
        <!-- 📈 ADVANCED LIVE TRADINGVIEW CANDLESTICK CHART CONTAINER -->
        <div class="card" style="border: 1.5px solid #3b82f6; background: linear-gradient(135deg, #0f172a 0%, #020617 100%);">
            <h3><span><i class="fas fa-candlestick-chart" style="color: #38bdf8;"></i> <span data-key="chart_title">Live Pro Candlestick Chart (NIFTY / SENSEX / BTC)</span></span></h3>
            <p style="color: #94a3b8; font-size: 0.8em; margin-bottom: 10px;" data-key="chart_desc">Real-time interactive technical analysis workspace with multi-timeframe feeds.</p>
            
            <div style="width: 100%; height: 300px; background: #030712; border: 1px solid #1f2937; border-radius: 8px; position: relative; display: flex; align-items: center; justify-content: center;">
                <canvas id="proTradingChart" style="width: 100%; height: 100%;"></canvas>
            </div>
        </div>

        <!-- ⚡ PRO ORDER EXECUTION ENGINE (BUY / SELL) -->
        <div class="card" style="border: 1.5px solid #10b981; background: linear-gradient(135deg, #0f172a 0%, #064e3b 25%, #0f172a 100%);">
            <h3><span><i class="fas fa-bolt" style="color: #10b981;"></i> <span data-key="order_engine_title">Instant Pro Order Execution</span></span></h3>
            <p style="color: #94a3b8; font-size: 0.8em; margin-bottom: 10px;" data-key="order_engine_desc">Execute market/limit buy and sell orders instantly.</p>

            <form action="/add_watchlist" method="POST">
                <label data-key="lbl_symbol">Asset Symbol:</label>
                <input type="text" name="symbol" data-placeholder="ph_symbol" placeholder="e.g., RELIANCE, TCS, BTC" required>
                
                <div style="display: flex; gap: 8px;">
                    <div style="flex:1;">
                        <label data-key="lbl_asset_type">Asset Type:</label>
                        <select name="asset_type">
                            <option value="STOCK" data-key="opt_stock">Stock</option>
                            <option value="CRYPTO" data-key="opt_crypto">Crypto</option>
                            <option value="COMMODITY" data-key="opt_commodity">Commodity</option>
                        </select>
                    </div>
                    <div style="flex:1;">
                        <label data-key="th_action_type">Action:</label>
                        <select name="action_type">
                            <option value="BUY" data-key="opt_buy">BUY</option>
                            <option value="SELL" data-key="opt_sell">SELL</option>
                        </select>
                    </div>
                </div>

                <div style="display: flex; gap: 8px; margin-top: 4px;">
                    <div style="flex:1;">
                        <label data-key="th_buy">Price (₹):</label>
                        <input type="number" step="0.01" name="buy_price" placeholder="0.00" required>
                    </div>
                    <div style="flex:1;">
                        <label data-key="th_holding_qty">Quantity:</label>
                        <input type="number" step="0.01" name="qty" placeholder="1" required>
                    </div>
                </div>

                <button type="submit" style="background: linear-gradient(135deg, #10b981, #059669); margin-top: 15px;" data-key="btn_execute_trade">⚡ Execute Pro Order</button>
            </form>
        </div>
    </div>

    <!-- 📊 ACTIVE PORTFOLIO HOLDINGS & WATCHLIST -->
    <div class="card" style="margin-bottom: 20px; border: 1.5px solid #3b82f6;">
        <h3><span><i class="fas fa-briefcase"></i> <span data-key="portfolio_title">My Active Trading & Investment Portfolio</span></span></h3>
        <table>
            <tr><th data-key="th_symbol">Symbol</th><th data-key="th_type">Type</th><th data-key="th_action_type">Action</th><th data-key="th_buy">Price</th><th data-key="th_holding_qty">Qty</th><th data-key="th_action">Manage</th></tr>
            {% if watchlist %}
                {% for w in watchlist %}
                <tr>
                    <td><strong>{{ w[1] }}</strong></td>
                    <td><span class="asset-type" data-val="{{ w[2] }}">{{ w[2] }}</span></td>
                    <td>
                        {% if w[3] == 'BUY' %}
                            <span style="color: #34d399; font-weight: bold;" data-key="opt_buy">BUY</span>
                        {% else %}
                            <span style="color: #f43f5e; font-weight: bold;" data-key="opt_sell">SELL</span>
                        {% endif %}
                    </td>
                    <td>₹<span class="num-val" data-val="{{ "%.2f"|format(w[4]) }}">{{ "%.2f"|format(w[4]) }}</span></td>
                    <td><span class="num-val" data-val="{{ w[5] }}">{{ w[5] }}</span></td>
                    <td><a href="/delete_watchlist/{{ w[0] }}" style="color:#f43f5e; text-decoration:none; font-weight:bold;"><i class="fas fa-trash"></i> <span data-key="del">Delete</span></a></td>
                </tr>
                {% endfor %}
            {% else %}
                <tr><td colspan="6" style="text-align: center; color: #94a3b8;" data-key="no_watchlist">No active trades in portfolio.</td></tr>
            {% endif %}
        </table>
    </div>

    <script>
        let currentLang = 'en';

        const hindiDigits = {'0':'०', '1':'१', '2':'२', '3':'३', '4':'४', '5':'५', '6':'६', '7':'७', '8':'८', '9':'९', '.':'.'};
        const gujaratiDigits = {'0':'૦', '1':'૧', '2':'૨', '3':'૩', '4':'૪', '5':'૫', '6':'૬', '7':'૭', '8':'૮', '9':'૯', '.':'.'};

        function convertDigits(text, lang) {
            let str = String(text);
            if (lang === 'hi') {
                return str.split('').map(char => hindiDigits[char] !== undefined ? hindiDigits[char] : char).join('');
            } else if (lang === 'gu') {
                return str.split('').map(char => gujaratiDigits[char] !== undefined ? gujaratiDigits[char] : char).join('');
            }
            return str;
        }

        const translations = {
            en: {
                header_title: "VAJRA PRO TRADING TERMINAL",
                logout: "Logout",
                backup_db: "Backup DB",
                export_csv: "Export CSV",
                print_report: "Print / Save PDF",
                chart_title: "Live Pro Candlestick Chart (NIFTY / SENSEX / BTC)",
                chart_desc: "Real-time interactive technical analysis workspace with multi-timeframe feeds.",
                order_engine_title: "Instant Pro Order Execution",
                order_engine_desc: "Execute market/limit buy and sell orders instantly.",
                lbl_symbol: "Asset Symbol:",
                lbl_asset_type: "Asset Type:",
                portfolio_title: "My Active Trading & Investment Portfolio",
                th_symbol: "Symbol",
                th_type: "Type",
                th_action_type: "Action",
                th_buy: "Price",
                th_holding_qty: "Qty",
                th_action: "Manage",
                del: "Delete",
                no_watchlist: "No active trades in portfolio.",
                opt_stock: "Stock",
                opt_crypto: "Crypto",
                opt_commodity: "Commodity",
                opt_buy: "BUY",
                opt_sell: "SELL",
                asset_STOCK: "Stock",
                asset_CRYPTO: "Crypto",
                asset_COMMODITY: "Commodity",
                btn_execute_trade: "⚡ Execute Pro Order",
                smartlist_title: "MTF Smartlist & Top Gainers (Live 1100+ Stocks)",
                smartlist_desc: "High momentum stocks with 4X leverage calculation simulation.",
                th_stock_name: "Stock / Corp Name",
                th_segment: "Segment",
                th_ltp: "LTP (₹)",
                th_change: "24h Change",
                nav_futures: "Futures & Options",
                nav_options: "Option Chain",
                nav_sip: "SIP / Earn",
                nav_orders: "Orders Book",
                nav_global: "Global Futures"
            },
            hi: {
                header_title: "वज्र प्रो ट्रेडिंग टर्मिनल",
                logout: "लॉग आउट",
                backup_db: "डेटाबेस बैकअप",
                export_csv: "इन्वेंट्री एक्सपोर्ट",
                print_report: "प्रिंट / पीडीएफ सेव करें",
                chart_title: "लाइव प्रो कैंडलस्टिक चार्ट (निफ्टी / सेंसेक्स / बिटकॉइन)",
                chart_desc: "रीयल-टाइम इंटरैक्टिव तकनीकी विश्लेषण और मल्टी-टाइमफ्रेम डेटा।",
                order_engine_title: "त्वरित प्रो ऑर्डर निष्पादन",
                order_engine_desc: "मार्केट/लिमिट खरीदें और बेचें तुरंत निष्पादित करें।",
                lbl_symbol: "एसेट सिंबल:",
                lbl_asset_type: "एसेट प्रकार:",
                portfolio_title: "मेरा सक्रिय ट्रेडिंग और निवेश पोर्टफोलियो",
                th_symbol: "सिंबल",
                th_type: "प्रकार",
                th_action_type: "एक्शन",
                th_buy: "मूल्य",
                th_holding_qty: "मात्रा",
                th_action: "प्रबंधन",
                del: "हटाएं",
                no_watchlist: "पोर्टफोलियो में कोई सक्रिय ट्रेड नहीं है।",
                opt_stock: "स्टॉक",
                opt_crypto: "क्रिप्टो",
                opt_commodity: "कमोडिटी",
                opt_buy: "खरीदें (BUY)",
                opt_sell: "बेचें (SELL)",
                asset_STOCK: "स्टॉक",
                asset_CRYPTO: "क्रिप्टो",
                asset_COMMODITY: "कमोडिटी",
                btn_execute_trade: "⚡ प्रो ऑर्डर निष्पादित करें",
                smartlist_title: "एमटीएफ स्मार्टलिस्ट और टॉप गेनर्स (लाइव ११००+ स्टॉक)",
                smartlist_desc: "४एక్స్ लीवरेज गणना सिमुलेशन के साथ उच्च गति वाले स्टॉक।",
                th_stock_name: "स्टॉक / कॉर्प नाम",
                th_segment: "सेगमेंट",
                th_ltp: "एलटीपी (₹)",
                th_change: "२४घं बदलाव",
                nav_futures: "फ्यूचर्स एंड ऑप्शंस",
                nav_options: "ऑप्शन चेन",
                nav_sip: "एसआईपी / अर्न",
                nav_orders: "ऑर्डर्स बुक",
                nav_global: "ग्लोबल फ्यूचर्स"
            },
            gu: {
                header_title: "વજ્ર પ્રો ટ્રેડિંગ ટર્મિનલ",
                logout: "લોગઆઉટ",
                backup_db: "બેકઅપ ડીબી",
                export_csv: "ઇન્વેન્ટરી એક્સપોર્ટ",
                print_report: "પ્રિન્ટ / PDF સેવ કરો",
                chart_title: "લાઈવ પ્રો કેન્ડલસ્ટિક ચાર્ટ (નિફ્ટી / સેન્સેક્સ / બિટકોઈન)",
                chart_desc: "વાસ્તવિક સમયની ઇન્ટરેક્ટિવ તકનીકી વિશ્લેષણ અને મલ્ટી-ટાઇમફ્રેમ ફીડ્સ.",
                order_engine_title: "ઇન્સ્ટન્ટ પ્રો ઓર્ડર એક્ઝિક્યુશન",
                order_engine_desc: "માર્કેટ/લિમિટ ખરીદો અને વેચો ઓર્ડર તરત જ એક્ઝિક્યુટ કરો.",
                lbl_symbol: "એસેટ સિમ્બોલ:",
                lbl_asset_type: "એસેટ પ્રકાર:",
                portfolio_title: "મારું સક્રિય ટ્રેડિંગ અને ઇન્વેસ્ટમેન્ટ પોર્ટફોલિયો",
                th_symbol: "સિમ્બોલ",
                th_type: "પ્રકાર",
                th_action_type: "એક્શન",
                th_buy: "કિંમત",
                th_holding_qty: "જથ્થો",
                th_action: "મેનેજ",
                del: "ડિલીટ",
                no_watchlist: "પોર્ટફોલિયોમાં કોઈ સક્રિય ટ્રેડ નથી.",
                opt_stock: "સ્ટોક",
                opt_crypto: "ક્રિપ્ટો",
                opt_commodity: "કોમોડિટી",
                opt_buy: "ખરીદો (BUY)",
                opt_sell: "વેચો (SELL)",
                asset_STOCK: "સ્ટોક",
                asset_CRYPTO: "ક્રિપ્ટો",
                asset_COMMODITY: "કોમોડિટી",
                btn_execute_trade: "⚡ પ્રો ઓર્ડર એક્ઝિક્યુટ કરો",
                smartlist_title: "એમટીએફ સ્માર્ટલિસ્ટ અને ટોપ ગેનર્સ (લાઇવ ૧૧૦૦+ સ્ટોક્સ)",
                smartlist_desc: "૪X લીવરેજ ગણતરી સિમ્યુલેશન સાથે ઉચ્ચ મોમેન્ટમ સ્ટોક્સ.",
                th_stock_name: "સ્ટોક / કોર્પ નામ",
                th_segment: "સેગમેન્ટ",
                th_ltp: "એલટીપી (₹)",
                th_change: "૨૪કલાક ફેરફાર",
                nav_futures: "ફ્યુચર્સ એન્ડ ઓપ્શન્સ",
                nav_options: "ઓપ્શન ચેઈન",
                nav_sip: "SIP / અર્ન",
                nav_orders: "ઓર્ડર્સ બુક",
                nav_global: "ગ્લોબલ ફ્યુચર્સ"
            }
        };

        function setLanguage(lang) {
            currentLang = lang;
            document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.lang-btn').forEach(btn => {
                if((lang === 'en' && btn.textContent.includes('EN')) ||
                   (lang === 'hi' && btn.textContent.includes('हिन्दी')) ||
                   (lang === 'gu' && btn.textContent.includes('ગુજરાતી'))) {
                    btn.classList.add('active');
                }
            });
            
            const elements = document.querySelectorAll('[data-key]');
            elements.forEach(el => {
                const key = el.getAttribute('data-key');
                if (translations[lang] && translations[lang][key]) {
                    el.textContent = translations[lang][key];
                }
            });

            document.querySelectorAll('.num-val').forEach(el => {
                const rawVal = el.getAttribute('data-val');
                el.textContent = convertDigits(rawVal, lang);
            });

            document.querySelectorAll('.asset-type').forEach(el => {
                const atype = el.getAttribute('data-val');
                const tKey = 'asset_' + atype;
                if (translations[lang] && translations[lang][tKey]) {
                    el.textContent = translations[lang][tKey];
                } else {
                    el.textContent = atype;
                }
            });

            const inputs = document.querySelectorAll('[data-placeholder]');
            inputs.forEach(inp => {
                const pKey = inp.getAttribute('data-placeholder');
                if (translations[lang] && translations[lang][pKey]) {
                    inp.placeholder = translations[lang][pKey];
                }
            });
        }

        const ctx = document.getElementById('proTradingChart').getContext('2d');
        const proChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['09:15', '10:00', '11:00', '12:00', '13:00', '14:00', '15:30'],
                datasets: [{
                    label: 'NIFTY Live Price Action',
                    data: [24700, 24750, 24720, 24810, 24790, 24830, 24850],
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#94a3b8' } } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#1f2937' } },
                    y: { ticks: { color: '#34d399' }, grid: { color: '#1f2937' } }
                }
            }
        });
    </script>
</body>
</html>
"""

TRADING_WORLD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vajra Pro Trading World - Upstox/Groww Style</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #0b0f19; color: #f8f9fa; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 15px; box-sizing: border-box; }
        .top-bar { background: #111827; padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3b82f6; margin-bottom: 20px; }
        .back-btn { background: #374151; color: #fff; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 0.9em; display: inline-flex; align-items: center; gap: 6px; }
        .back-btn:hover { background: #4b5563; }
        .grid-world { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 15px; }
        .card-box { background: #111827; border: 1px solid #1f2937; padding: 20px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .card-box h3 { color: #38bdf8; margin-top: 0; display: flex; align-items: center; gap: 10px; font-size: 1.1em; border-bottom: 1px solid #1f2937; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.85em; }
        th, td { border: 1px solid #1f2937; padding: 8px; text-align: left; }
        th { background: #0f172a; color: #38bdf8; }
        input, select { width: 100%; padding: 10px; margin-top: 6px; background: #030712; border: 1px solid #374151; color: #fff; border-radius: 6px; box-sizing: border-box; }
        button { background: #10b981; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 12px; font-size: 1em; }
        button:hover { background: #059669; }
    </style>
</head>
<body>
    <div class="top-bar">
        <h2><i class="fas fa-globe-americas" style="color: #38bdf8;"></i> Vajra Pro Trading World (Live Exchange)</h2>
        <a href="/dashboard" class="back-btn"><i class="fas fa-arrow-left"></i> Back to Main ERP</a>
    </div>

    <div class="grid-world">
        <!-- 📈 ADVANCED TRADINGVIEW CHART -->
        <div class="card-box" style="grid-column: span 2;">
            <h3><i class="fas fa-chart-candlestick"></i> Advanced TradingView Multi-Timeframe Chart</h3>
            <div style="width: 100%; height: 350px; background: #030712; border: 1px solid #1f2937; border-radius: 8px;">
                <canvas id="worldChart" style="width: 100%; height: 100%;"></canvas>
            </div>
        </div>

        <!-- ⚡ INSTANT BUY/SELL ORDER EXECUTION -->
        <div class="card-box">
            <h3><i class="fas fa-bolt"></i> Instant Buy & Sell Terminal</h3>
            <form action="/add_watchlist" method="POST">
                <label>Symbol (e.g., RELIANCE, TCS, BTC):</label>
                <input type="text" name="symbol" required placeholder="Enter Symbol">
                
                <label>Asset Type:</label>
                <select name="asset_type">
                    <option value="STOCK">Stock (NSE/BSE)</option>
                    <option value="CRYPTO">Crypto Futures</option>
                    <option value="COMMODITY">Global Commodity</option>
                </select>

                <label>Action:</label>
                <select name="action_type">
                    <option value="BUY">BUY (Long)</option>
                    <option value="SELL">SELL (Short)</option>
                </select>

                <label>Execution Price (₹):</label>
                <input type="number" step="0.01" name="buy_price" required placeholder="0.00">

                <label>Quantity / Lots:</label>
                <input type="number" step="0.01" name="qty" required placeholder="1">

                <button type="submit">Place Instant Order</button>
            </form>
        </div>

        <!-- 📊 OPTION CHAIN & FUTURES SUMMARY -->
        <div class="card-box">
            <h3><i class="fas fa-table-cells"></i> Live Option Chain & PCR Summary</h3>
            <table>
                <tr><th>Strike</th><th>Call LTP</th><th>Put LTP</th><th>PCR</th></tr>
                <tr><td>16,150</td><td>₹764.00</td><td>₹15.00</td><td>2.64</td></tr>
                <tr><td>16,200</td><td>₹444.50</td><td>₹43.00</td><td>2.44</td></tr>
                <tr><td>16,250</td><td>₹263.00</td><td>₹66.00</td><td>2.04</td></tr>
                <tr><td>16,300</td><td>₹220.00</td><td>₹84.00</td><td>2.00</td></tr>
            </table>
        </div>
    </div>

    <script>
        const ctxW = document.getElementById('worldChart').getContext('2d');
        new Chart(ctxW, {
            type: 'line',
            data: {
                labels: ['09:15', '10:00', '11:00', '12:00', '13:00', '14:00', '15:30'],
                datasets: [{
                    label: 'Global Futures / Nifty Live Index',
                    data: [24800, 24840, 24790, 24890, 24860, 24920, 24950],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#94a3b8' } } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#1f2937' } },
                    y: { ticks: { color: '#34d399' }, grid: { color: '#1f2937' } }
                }
            }
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    msg = request.args.get("msg")
    
    if request.method == "GET":
        session.clear()
        n1 = random.randint(1, 15)
        n2 = random.randint(1, 10)
        op = random.choice(['+', '-'])
        if op == '-':
            if n1 < n2: n1, n2 = n2, n1
            session["math_ans"] = str(n1 - n2)
            session["math_q"] = f"{n1} - {n2} = ?"
        else:
            session["math_ans"] = str(n1 + n2)
            session["math_q"] = f"{n1} + {n2} = ?"

    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        user_math = request.form.get("math_input", "").strip()
        correct_math = session.get("math_ans", "")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if user_math != correct_math:
            error = "Math Trick Verification Failed! Try again."
            n1, n2 = random.randint(1, 15), random.randint(1, 10)
            session["math_ans"] = str(n1 + n2)
            session["math_q"] = f"{n1} + {n2} = ?"
        else:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
                user = cursor.fetchone()
                
            if user:
                session["logged_in"] = True
                session["username"] = username
                session.permanent = False 
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid Username or Password! Access Denied."
                n1, n2 = random.randint(1, 15), random.randint(1, 10)
                session["math_ans"] = str(n1 + n2)
                session["math_q"] = f"{n1} + {n2} = ?"

    return render_template_string(
        LOGIN_HTML, 
        error=error, 
        msg=msg,
        math_question=session.get("math_q", "5 + 3 = ?")
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        mobile = request.form.get("mobile", "").strip()
        email = request.form.get("email", "").strip()
        
        if not username or not password or not mobile or not email:
            error = "All fields are required!"
        else:
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    conn.execute("INSERT INTO users (username, password, mobile, email) VALUES (?, ?, ?, ?)",
                                 (username, password, mobile, email))
                return redirect(url_for("login", msg="Registration successful! Please login."))
            except sqlite3.IntegrityError:
                error = "Username already exists! Please choose another."
                
    return render_template_string(REGISTER_HTML, error=error)

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    username = session.get("username", "Admin")
    start_time = time.time()
    with sqlite3.connect(DB_NAME) as conn:
        vouchers = conn.execute("SELECT * FROM vouchers ORDER BY id DESC LIMIT 6").fetchall()
        revenue = conn.execute("SELECT SUM(total_with_gst) FROM vouchers WHERE voucher_type IN ('RECEIPT', 'SALES')").fetchone()[0] or 0.0
        expenses = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0.0
        
        banks = conn.execute("SELECT * FROM bank_accounts").fetchall()
        bank_bal = sum(b[3] for b in banks) if banks else 0.0
        
        adv_rows = conn.execute("SELECT adv_type, amount FROM advances WHERE status='PENDING'").fetchall()
        net_advances = sum(amt if t=='TAKEN' else -amt for t, amt in adv_rows)
        
        burn_rate = expenses if expenses > 0 else 1.0
        runway_days = int((bank_bal / burn_rate) * 30) if burn_rate > 0 else 999
        if runway_days < 0: runway_days = 0
        sentinel_status = "Optimal Liquidity" if runway_days > 30 else "Cash Conservation Alert"

        inv_rows = conn.execute("SELECT item_name, sku, qty, price, movement_type, market_status FROM inventory").fetchall()
        stock_map = {}
        for item_name, sku, qty, price, movement, m_status in inv_rows:
            if sku not in stock_map:
                stock_map[sku] = {"name": item_name, "qty": 0, "price": price, "status": m_status}
            if movement == 'INWARD':
                stock_map[sku]["qty"] += qty
            else:
                stock_map[sku]["qty"] -= qty
        
        stock_summary = []
        total_inv_val = 0.0
        for sku, data in stock_map.items():
            net_q = data["qty"]
            if net_q < 0: net_q = 0
            val = net_q * data["price"]
            total_inv_val += val
            stock_summary.append((data["name"], sku, data["status"], net_q, data["price"]))

        watchlist = conn.execute("SELECT * FROM trading_portfolio").fetchall()
        profit = revenue - expenses
        kpis = {"revenue": revenue, "expenses": expenses, "profit": profit, "inventory": total_inv_val, "bank_bal": bank_bal, "advances": net_advances}

    query_latency = round((time.time() - start_time) * 1000, 2)
    return render_template_string(DASHBOARD_HTML, vouchers=vouchers, kpis=kpis, banks=banks, stock_summary=stock_summary, runway_days=runway_days, sentinel_status=sentinel_status, query_latency=query_latency, username=username, watchlist=watchlist)

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
    return redirect(request.referrer or url_for("dashboard"))

@app.route("/delete_watchlist/<int:wid>")
def delete_watchlist(wid):
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM trading_portfolio WHERE id = ?", (wid,))
    return redirect(request.referrer or url_for("dashboard"))

@app.route("/print_report_view")
def print_report_view():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        vouchers = conn.execute("SELECT * FROM vouchers ORDER BY id DESC").fetchall()
        banks = conn.execute("SELECT * FROM bank_accounts").fetchall()
        inventory = conn.execute("SELECT * FROM inventory").fetchall()
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vajra ERP - Print Report</title>
            <style>
                body { background: white; color: black; font-family: sans-serif; padding: 20px; }
                h2 { color: #0f172a; border-bottom: 2px solid #2563eb; padding-bottom: 8px; }
                table { width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 25px; font-size: 0.9em; }
                th, td { border: 1px solid #cbd5e1; padding: 8px; text-align: left; }
                th { background: #f1f5f9; color: #1e293b; }
                .btn-container { display: flex; gap: 15px; justify-content: center; margin: 20px 0; flex-wrap: wrap; }
                .action-btn { background: #2563eb; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-size: 1em; cursor: pointer; font-weight: bold; text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }
                .download-btn { background: #10b981; }
                @media print { .btn-container { display: none; } }
            </style>
        </head>
        <body>
            <div class="btn-container">
                <button class="action-btn" onclick="window.print()">🖨️ Print Page</button>
                <a href="/download_report_file" class="action-btn download-btn">📥 Download Report File</a>
            </div>

            <h2>⚡ Vajra ERP - Official Business Report</h2>
            
            <h3>Recent Vouchers</h3>
            <table>
                <tr><th>ID</th><th>Date</th><th>Type</th><th>Party</th><th>Total (Inc. GST)</th></tr>
                {% for v in vouchers %}
                <tr><td>{{ v[0] }}</td><td>{{ v[1] }}</td><td>{{ v[2] }}</td><td>{{ v[3] }}</td><td>₹{{ "%.2f"|format(v[6]) }}</td></tr>
                {% endfor %}
            </table>

            <h3>Bank Accounts</h3>
            <table>
                <tr><th>Bank Name</th><th>Account No</th><th>Balance</th></tr>
                {% for b in banks %}
                <tr><td>{{ b[1] }}</td><td>{{ b[2] }}</td><td>₹{{ "%.2f"|format(b[3]) }}</td></tr>
                {% endfor %}
            </table>
        </body>
        </html>
    ''', vouchers=vouchers, banks=banks, inventory=inventory)

@app.route("/download_report_file")
def download_report_file():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        vouchers = conn.execute("SELECT * FROM vouchers ORDER BY id DESC").fetchall()
        banks = conn.execute("SELECT * FROM bank_accounts").fetchall()
        inventory = conn.execute("SELECT * FROM inventory").fetchall()
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Vajra ERP Report</title></head>
    <body style="font-family: sans-serif; padding: 20px;">
        <h2>⚡ Vajra ERP - Official Business Report</h2>
        <h3>Recent Vouchers</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr><th>ID</th><th>Date</th><th>Type</th><th>Party</th><th>Total (Inc. GST)</th></tr>
            {''.join(f"<tr><td>{v[0]}</td><td>{v[1]}</td><td>{v[2]}</td><td>{v[3]}</td><td>₹{v[6]:.2f}</td></tr>" for v in vouchers)}
        </table>
        <h3 style="margin-top: 20px;">Bank Accounts</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr><th>Bank Name</th><th>Account No</th><th>Balance</th></tr>
            {''.join(f"<tr><td>{b[1]}</td><td>{b[2]}</td><td>₹{b[3]:.2f}</td></tr>" for b in banks)}
        </table>
    </body>
    </html>
    """
    return Response(
        html_content,
        mimetype="text/html",
        headers={"Content-Disposition": "attachment;filename=Vajra_ERP_Report.html"}
    )

@app.route("/api/ai-assistant", methods=["POST", "GET"])
def ai_assistant():
    data = request.get_json(silent=True) or request.form or {}
    user_query = str(data.get("query", "")).lower()
    lang = str(data.get("lang", "en"))
    
    with sqlite3.connect(DB_NAME) as conn:
        rev = conn.execute("SELECT SUM(total_with_gst) FROM vouchers WHERE voucher_type IN ('RECEIPT', 'SALES')").fetchone()[0] or 0.0
        exp = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0.0
        net_profit = rev - exp
        banks_total = conn.execute("SELECT SUM(balance) FROM bank_accounts").fetchone()[0] or 0.0
        total_items = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0] or 0
    
    if lang == "gu":
        response_text = f"કુલ વેચાણ / આવક ₹{rev:.2f} છે."
        if "profit" in user_query or "nofo" in user_query or "નફો" in user_query or "nafa" in user_query:
            response_text = f"આજે કુલ નેટ નફો ₹{net_profit:.2f} થયો છે."
        elif "sales" in user_query or "vechan" in user_query or "aavak" in user_query or "revenue" in user_query:
            response_text = f"કુલ વેચાણ / આવક ₹{rev:.2f} છે."
        elif "bank" in user_query or "balance" in user_query or "belez" in user_query:
            response_text = f"બધી બેંકનું કુલ બેલેન્સ ₹{banks_total:.2f} છે."
        elif "stock" in user_query or "stok" in user_query:
            response_text = f"ઇન્વેન્ટરી સ્ટોક મેનેજમેન્ટમાં કુલ {total_items} આઇટમ્સ રજીસ્ટર થયેલી છે."
    elif lang == "hi":
        response_text = f"कुल राजस्व / बिक्री ₹{rev:.2f} है।"
        if "profit" in user_query or "labh" in user_query or "नफा" in user_query:
            response_text = f"आज कुल शुद्ध लाभ ₹{net_profit:.2f} हुआ है।"
        elif "sales" in user_query or "bikri" in user_query or "revenue" in user_query:
            response_text = f"कुल राजस्व / बिक्री ₹{rev:.2f} है।"
        elif "bank" in user_query or "balance" in user_query:
            response_text = f"सभी बैंकों का कुल शेष ₹{banks_total:.2f} है।"
        elif "stock" in user_query:
            response_text = f"इन्वेंट्री स्टॉक में कुल {total_items} आइटम पंजीकृत हैं।"
    else:
        response_text = f"Total revenue / sales is ₹{rev:.2f}."
        if "profit" in user_query:
            response_text = f"Today's net profit is ₹{net_profit:.2f}."
        elif "sales" in user_query or "revenue" in user_query:
            response_text = f"Total revenue / sales is ₹{rev:.2f}."
        elif "bank" in user_query or "balance" in user_query:
            response_text = f"Total bank balance across accounts is ₹{banks_total:.2f}."
        elif "stock" in user_query:
            response_text = f"Live inventory stock summary: {total_items} items registered."

    return jsonify({"status": "success", "reply": response_text})

@app.route("/add_bank", methods=["POST"])
def add_bank():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO bank_accounts (bank_name, account_no, balance) VALUES (?, ?, ?)",
                     (request.form.get("bank_name"), request.form.get("account_no"), float(request.form.get("balance"))))
    return redirect(url_for("dashboard"))

@app.route("/bank_transaction", methods=["POST"])
def bank_transaction():
    if not session.get("logged_in"): return redirect(url_for("login"))
    bank_id = int(request.form.get("bank_id"))
    tx_type = request.form.get("tx_type")
    payment_mode = request.form.get("payment_mode")
    amount = float(request.form.get("amount"))
    narration = request.form.get("narration", "")
    
    with sqlite3.connect(DB_NAME) as conn:
        if tx_type == "DEPOSIT":
            conn.execute("UPDATE bank_accounts SET balance = balance + ? WHERE id = ?", (amount, bank_id))
        else:
            conn.execute("UPDATE bank_accounts SET balance = balance - ? WHERE id = ?", (amount, bank_id))
        conn.execute("INSERT INTO bank_transactions (bank_id, tx_type, amount, payment_mode, narration, date) VALUES (?, ?, ?, ?, ?, ?)",
                     (bank_id, tx_type, amount, payment_mode, narration, datetime.now().strftime("%Y-%m-%d %H:%M")))
    return redirect(url_for("dashboard"))

@app.route("/add_advance", methods=["POST"])
def add_advance():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO advances (party_name, adv_type, amount, date) VALUES (?, ?, ?, ?)",
                     (request.form.get("party_name"), request.form.get("adv_type"), float(request.form.get("amount")), datetime.now().strftime("%Y-%m-%d")))
    return redirect(url_for("dashboard"))

@app.route("/add_voucher", methods=["POST"])
def add_voucher():
    if not session.get("logged_in"): return redirect(url_for("login"))
    v_type = request.form.get("voucher_type")
    ledger = request.form.get("ledger_name")
    amount = float(request.form.get("amount"))
    gst = amount * 0.18
    total = amount + gst
    crypto_hash = generate_hash(f"{datetime.now()}{v_type}{ledger}{total}")
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO vouchers (date, voucher_type, ledger_name, amount, gst_amount, total_with_gst, narration, crypto_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (datetime.now().strftime("%Y-%m-%d %H:%M"), v_type, ledger, amount, gst, total, request.form.get("narration", ""), crypto_hash))
    return redirect(url_for("dashboard"))

@app.route("/add_inventory", methods=["POST"])
def add_inventory():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO inventory (item_name, sku, qty, price, movement_type, market_status) VALUES (?, ?, ?, ?, ?, ?)",
                     (request.form.get("item_name"), request.form.get("sku"), int(request.form.get("qty")), 
                      float(request.form.get("price")), request.form.get("movement_type"), request.form.get("market_status")))
    return redirect(url_for("dashboard"))

@app.route("/export_inventory_csv")
def export_inventory_csv():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        data = conn.execute("SELECT * FROM inventory").fetchall()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Item Name', 'SKU', 'Qty', 'Price', 'Movement', 'Market Status', 'Timestamp'])
    cw.writerows(data)
    return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=inventory.csv"})

@app.route("/backup_db")
def backup_db():
    if not session.get("logged_in"): return redirect(url_for("login"))
    return send_file(os.path.abspath(DB_NAME), as_attachment=True)

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("logout")) # Fixed fallback

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5027))
    app.run(host="0.0.0.0", port=port)
