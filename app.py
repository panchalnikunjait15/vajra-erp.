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

        .pro-nav-bar { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-bottom: 25px; }
        .pro-nav-btn { background: linear-gradient(135deg, #1e293b, #0f172a); border: 2px solid #3b82f6; color: #38bdf8; padding: 15px; border-radius: 10px; font-weight: bold; cursor: pointer; text-align: center; font-size: 1em; transition: 0.2s; display: flex; flex-direction: column; align-items: center; gap: 8px; text-decoration: none; box-shadow: 0 5px 15px rgba(59,130,246,0.2); }
        .pro-nav-btn:hover { background: #3b82f6; color: #fff; transform: translateY(-3px); }

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
            <i class="fas fa-chart-line"></i> <span data-key="header_title">VAJRA ERP & BUSINESS SUITE</span>
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

    <!-- 🚀 DIRECT UPSTOX / COINDCX PRO WORLD LAUNCHER -->
    <div class="pro-nav-bar">
        <a href="/pro_trading_hub" class="pro-nav-btn">
            <i class="fas fa-rocket fa-2x" style="color: #38bdf8;"></i> <span data-key="launch_terminal">🚀 Open Pro Trading Terminal (Upstox/Groww Mode)</span>
        </a>
    </div>

    <div class="kpi-grid">
        <div class="kpi"><h3 data-key="kpi_revenue">Total Revenue</h3><p>₹<span class="num-val" data-val="{{ "%.2f"|format(kpis.revenue) }}">{{ "%.2f"|format(kpis.revenue) }}</span></p></div>
        <div class="kpi"><h3 data-key="kpi_profit">Net Profit (P&L)</h3><p>₹<span class="num-val" data-val="{{ "%.2f"|format(kpis.profit) }}">{{ "%.2f"|format(kpis.profit) }}</span></p></div>
        <div class="kpi"><h3 data-key="kpi_bank">Total Bank Balance</h3><p style="color: #34d399;">₹<span class="num-val" data-val="{{ "%.2f"|format(kpis.bank_bal) }}">{{ "%.2f"|format(kpis.bank_bal) }}</span></p></div>
        <div class="kpi"><h3 data-key="kpi_advances">Net Advances</h3><p>₹<span class="num-val" data-val="{{ "%.2f"|format(kpis.advances) }}">{{ "%.2f"|format(kpis.advances) }}</span></p></div>
    </div>

    <div class="main-grid">
        <div class="card">
            <h3><span><i class="fas fa-book-open"></i> <span data-key="acc_title">Accounting & GST Voucher</span></span></h3>
            <form action="/add_voucher" method="POST">
                <label data-key="lbl_vtype">Voucher Type:</label>
                <select name="voucher_type">
                    <option value="RECEIPT" data-key="opt_receipt">RECEIPT</option>
                    <option value="PAYMENT" data-key="opt_payment">PAYMENT</option>
                    <option value="SALES" data-key="opt_sales">SALES</option>
                    <option value="PURCHASE" data-key="opt_purchase">PURCHASE</option>
                </select>
                <label data-key="lbl_party">Party / Ledger Name:</label><input type="text" name="ledger_name" required>
                <label data-key="lbl_amount">Base Amount (₹):</label><input type="number" step="0.01" name="amount" required>
                <label data-key="lbl_narration">Narration:</label><input type="text" name="narration">
                <button type="submit" data-key="btn_save_voucher">Save Voucher (Auto 18% GST)</button>
            </form>
        </div>

        <div class="card">
            <h3><span><i class="fas fa-boxes"></i> <span data-key="inv_title">Inventory Control</span></span></h3>
            <form action="/add_inventory" method="POST">
                <label data-key="lbl_movement">Movement Type:</label>
                <select name="movement_type">
                    <option value="INWARD" data-key="opt_inward">INWARD</option>
                    <option value="OUTWARD" data-key="opt_outward">OUTWARD</option>
                </select>
                <label data-key="lbl_item_name">Item Name:</label><input type="text" name="item_name" required>
                <label data-key="lbl_sku">SKU Code:</label><input type="text" name="sku" required>
                <label data-key="lbl_market_status">Market Trend Status:</label>
                <select name="market_status">
                    <option value="REGULAR" data-key="opt_regular">Regular Stock</option>
                    <option value="TRENDING" data-key="opt_trending">Fast-Moving (Trending)</option>
                </select>
                <div style="display: flex; gap: 8px; margin-top: 8px;">
                    <div style="flex:1;"><label data-key="lbl_qty">Qty:</label><input type="number" name="qty" required></div>
                    <div style="flex:1;"><label data-key="lbl_price">Price (₹):</label><input type="number" step="0.01" name="price" required></div>
                </div>
                <button type="submit" data-key="btn_update_stock">Update Stock</button>
            </form>
        </div>
    </div>

    <script>
        let currentLang = 'en';
        const hindiDigits = {'0':'०', '1':'१', '2':'२', '3':'३', '4':'४', '5':'५', '6':'६', '7':'७', '8':'८', '9':'९', '.':'.'};
        const gujaratiDigits = {'0':'૦', '1':'૧', '2':'૨', '3':'૩', '4':'૪', '5':'૫', '6':'૬', '7':'૭', '8':'૮', '9':'૯', '.':'.'};

        function convertDigits(text, lang) {
            let str = String(text);
            if (lang === 'hi') return str.split('').map(char => hindiDigits[char] !== undefined ? hindiDigits[char] : char).join('');
            if (lang === 'gu') return str.split('').map(char => gujaratiDigits[char] !== undefined ? gujaratiDigits[char] : char).join('');
            return str;
        }

        const translations = {
            en: {
                header_title: "VAJRA ERP & BUSINESS SUITE",
                logout: "Logout",
                backup_db: "Backup DB",
                export_csv: "Export CSV",
                print_report: "Print / Save PDF",
                launch_terminal: "🚀 Open Pro Trading Terminal (Upstox/Groww Mode)",
                kpi_revenue: "Total Revenue",
                kpi_profit: "Net Profit (P&L)",
                kpi_bank: "Total Bank Balance",
                kpi_advances: "Net Advances",
                acc_title: "Accounting & GST Voucher",
                lbl_vtype: "Voucher Type:",
                lbl_party: "Party / Ledger Name:",
                lbl_amount: "Base Amount (₹):",
                lbl_narration: "Narration:",
                btn_save_voucher: "Save Voucher (Auto 18% GST)",
                inv_title: "Inventory Control",
                lbl_movement: "Movement Type:",
                opt_inward: "INWARD",
                opt_outward: "OUTWARD",
                lbl_item_name: "Item Name:",
                lbl_sku: "SKU Code:",
                lbl_market_status: "Market Trend Status:",
                opt_regular: "Regular Stock",
                opt_trending: "Fast-Moving (Trending)",
                lbl_qty: "Qty:",
                lbl_price: "Price (₹):",
                btn_update_stock: "Update Stock",
                opt_receipt: "RECEIPT",
                opt_payment: "PAYMENT",
                opt_sales: "SALES",
                opt_purchase: "PURCHASE"
            },
            hi: {
                header_title: "वज्र ईआरपी और बिजनेस सूट",
                logout: "लॉग आउट",
                backup_db: "डेटाबेस बैकअप",
                export_csv: "इन्वेंट्री एक्सपोर्ट",
                print_report: "प्रिंट / पीडीएफ सेव करें",
                launch_terminal: "🚀 प्रो ट्रेडिंग टर्मिनल खोलें (Upstox/Groww मोड)",
                kpi_revenue: "कुल राजस्व",
                kpi_profit: "शुद्ध लाभ (P&L)",
                kpi_bank: "कुल बैंक शेष",
                kpi_advances: "शुद्ध अग्रिम",
                acc_title: "लेखांकन और जीएसटी वाउचर",
                lbl_vtype: "वाउचर प्रकार:",
                lbl_party: "पार्टी / लेजर नाम:",
                lbl_amount: "मूल राशि (₹):",
                lbl_narration: "विवरण:",
                btn_save_voucher: "वाउचर सहेजें (ऑटो 18% जीएसटी)",
                inv_title: "इन्वेंट्री नियंत्रण",
                lbl_movement: "मूवमेंट प्रकार:",
                opt_inward: "आवक",
                opt_outward: "जावक",
                lbl_item_name: "वस्तु का नाम:",
                lbl_sku: "SKU कोड:",
                lbl_market_status: "बाजार रुझान स्थिति:",
                opt_regular: "नियमित स्टॉक",
                opt_trending: "तेजी से बिकने वाला",
                lbl_qty: "मात्रा:",
                lbl_price: "मूल्य (₹):",
                btn_update_stock: "स्टॉक अपडेट करें",
                opt_receipt: "रसीद",
                opt_payment: "भुगतान",
                opt_sales: "बिक्री",
                opt_purchase: "खरीद"
            },
            gu: {
                header_title: "વજ્ર ERP અને બિઝનેસ સૂટ",
                logout: "લોગઆઉટ",
                backup_db: "બેકઅપ ડીબી",
                export_csv: "ઇન્વેન્ટરી એક્સપોર્ટ",
                print_report: "પ્રિન્ટ / PDF સેવ કરો",
                launch_terminal: "🚀 પ્રો ટ્રેડિંગ ટર્મિનલ ખોલો (Upstox/Groww મોડ)",
                kpi_revenue: "કુલ આવક",
                kpi_profit: "નેટ પ્રોફિટ (નફો)",
                kpi_bank: "કુલ બેંક બેલેન્સ",
                kpi_advances: "નેટ એડવાન્સ",
                acc_title: "એકાઉન્ટિંગ અને જીએસટી વાઉચર",
                lbl_vtype: "વાઉચર પ્રકાર:",
                lbl_party: "પાર્ટી / લેજર નામ:",
                lbl_amount: "મૂળ રકમ (₹):",
                lbl_narration: "નરેશન:",
                btn_save_voucher: "વાઉચર સેવ કરો (ઓટો ૧૮% GST)",
                inv_title: "ઇન્વેન્ટરી કંટ્રોલ",
                lbl_movement: "મૂવમેન્ટ પ્રકાર:",
                opt_inward: "આવક",
                opt_outward: "જાવક",
                lbl_item_name: "આઇટમનું નામ:",
                lbl_sku: "એસકેયુ કોડ:",
                lbl_market_status: "માર્કેટ ટ્રેન્ડ સ્ટેટસ:",
                opt_regular: "સામાન્ય સ્ટોક",
                opt_trending: "બજારમાં ચલતી વસ્તુ (Trending)",
                lbl_qty: "જથ્થો (Qty):",
                lbl_price: "કિંમત (₹):",
                btn_update_stock: "સ્ટોક અપડેટ કરો",
                opt_receipt: "રસીદ",
                opt_payment: "ચુકવણી",
                opt_sales: "વેચાણ",
                opt_purchase: "ખરીદી"
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
            
            document.querySelectorAll('[data-key]').forEach(el => {
                const key = el.getAttribute('data-key');
                if (translations[lang] && translations[lang][key]) {
                    el.textContent = translations[lang][key];
                }
            });

            document.querySelectorAll('.num-val').forEach(el => {
                el.textContent = convertDigits(el.getAttribute('data-val'), lang);
            });
        }
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
        body { background: #000000; color: #f8f9fa; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 15px; box-sizing: border-box; }
        .app-header { background: #121212; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2a2a2a; position: sticky; top: 0; z-index: 100; }
        .back-btn { background: #2a2a2a; color: #fff; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 0.9em; display: inline-flex; align-items: center; gap: 8px; }
        .back-btn:hover { background: #3b3b3b; }
        
        .exchange-tabs { display: flex; gap: 15px; background: #121212; padding: 12px 20px; border-bottom: 1px solid #2a2a2a; overflow-x: auto; }
        .ex-tab { background: transparent; border: none; color: #9ca3af; font-weight: bold; cursor: pointer; font-size: 0.95em; padding-bottom: 5px; white-space: nowrap; }
        .ex-tab.active { color: #10b981; border-bottom: 2px solid #10b981; }

        .exchange-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; padding: 20px 0; }
        @media(max-width: 900px) { .exchange-grid { grid-template-columns: 1fr; } }

        .ex-card { background: #121212; border: 1px solid #2a2a2a; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        .ex-card h3 { color: #fff; margin-top: 0; display: flex; justify-content: space-between; align-items: center; font-size: 1.1em; border-bottom: 1px solid #2a2a2a; padding-bottom: 12px; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9em; }
        th, td { border: 1px solid #2a2a2a; padding: 10px; text-align: left; }
        th { background: #1a1a1a; color: #9ca3af; font-weight: 600; }
        
        input, select { width: 100%; padding: 12px; margin-top: 8px; background: #1a1a1a; border: 1px solid #333; color: #fff; border-radius: 8px; box-sizing: border-box; }
        button.buy-btn { background: #10b981; color: white; border: none; padding: 14px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 15px; font-size: 1.05em; }
        button.buy-btn:hover { background: #059669; }
        
        .market-ticker { display: flex; gap: 15px; overflow-x: auto; padding: 10px 0; margin-bottom: 20px; }
        .ticker-pill { background: #121212; border: 1px solid #2a2a2a; padding: 10px 15px; border-radius: 8px; min-width: 140px; text-align: center; }
        .ticker-pill .val { color: #10b981; font-weight: bold; font-size: 1.05em; margin-top: 4px; }
    </style>
</head>
<body>
    <div class="app-header">
        <div style="display: flex; align-items: center; gap: 15px;">
            <a href="/dashboard" class="back-btn"><i class="fas fa-arrow-left"></i> Exit Pro Mode</a>
            <h2 style="margin: 0; font-size: 1.3em; color: #10b981;"><i class="fas fa-bolt"></i> VAJRA PRO EXCHANGE (Upstox / Groww Edition)</h2>
        </div>
        <div style="color: #9ca3af; font-size: 0.9em;">
            <i class="fas fa-circle" style="color: #10b981; font-size: 0.7em;"></i> Live Feed Connected (24x7)
        </div>
    </div>

    <div class="exchange-tabs">
        <button class="ex-tab active">Explore</button>
        <button class="ex-tab">Futures & Options</button>
        <button class="ex-tab">Option Chain</button>
        <button class="ex-tab">Global Futures (US Stocks)</button>
        <button class="ex-tab">SIP & Mutual Funds</button>
        <button class="ex-tab">Orders & Portfolio</button>
    </div>

    <div style="padding: 0 10px;">
        <!-- TICKER STRIP -->
        <div class="market-ticker">
            <div class="ticker-pill"><div style="font-size:0.8em; color:#9ca3af;">NIFTY 50</div><div class="val">₹24,850.30</div></div>
            <div class="ticker-pill"><div style="font-size:0.8em; color:#9ca3af;">SENSEX</div><div class="val">₹81,420.10</div></div>
            <div class="ticker-pill"><div style="font-size:0.8em; color:#9ca3af;">BITCOIN</div><div class="val">₹74,50,000</div></div>
            <div class="ticker-pill"><div style="font-size:0.8em; color:#9ca3af;">NSDQ 100</div><div class="val">25,259.00</div></div>
        </div>

        <div class="exchange-grid">
            <!-- LEFT COLUMN: LIVE CHARTS & TOP GAINERS -->
            <div>
                <div class="ex-card">
                    <h3><span><i class="fas fa-chart-candlestick" style="color: #38bdf8;"></i> TradingView Pro Live Chart</span> <span style="font-size: 0.8em; color: #10b981;">1m | 5m | 1h | 1D</span></h3>
                    <div style="width: 100%; height: 320px; background: #000; border: 1px solid #2a2a2a; border-radius: 8px;">
                        <canvas id="exchangeChart" style="width: 100%; height: 100%;"></canvas>
                    </div>
                </div>

                <div class="ex-card">
                    <h3><span><i class="fas fa-fire" style="color: #f59e0b;"></i> Top Gainers & MTF Smartlist (1100+ Stocks)</span></h3>
                    <table>
                        <tr><th>Stock Name</th><th>Segment</th><th>LTP</th><th>24h Change</th></tr>
                        <tr><td><strong>RELIANCE INDUSTRIES</strong></td><td>EQ</td><td>₹2,940.15</td><td style="color: #10b981;">+4.04%</td></tr>
                        <tr><td><strong>TATA MOTORS</strong></td><td>EQ</td><td>₹980.25</td><td style="color: #10b981;">+6.09%</td></tr>
                        <tr><td><strong>INFOSYS LTD</strong></td><td>EQ</td><td>₹1,850.40</td><td style="color: #10b981;">+2.85%</td></tr>
                    </table>
                </div>
            </div>

            <!-- RIGHT COLUMN: ORDER PLACEMENT & OPTION CHAIN -->
            <div>
                <div class="ex-card" style="border: 1.5px solid #10b981;">
                    <h3><span><i class="fas fa-shopping-cart"></i> Instant Order Execution</span></h3>
                    <form action="/add_watchlist" method="POST">
                        <label style="color:#9ca3af;">Symbol Search:</label>
                        <input type="text" name="symbol" required placeholder="e.g. RELIANCE, BTC, TSLA">
                        
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

                <div class="ex-card">
                    <h3><span><i class="fas fa-table-cells"></i> Live Option Chain (PCR)</span></h3>
                    <table>
                        <tr><th>Strike</th><th>Call LTP</th><th>Put LTP</th></tr>
                        <tr><td>16,150</td><td>₹764.00</td><td>₹15.00</td></tr>
                        <tr><td>16,200</td><td>₹444.50</td><td>₹43.00</td></tr>
                        <tr><td>16,250</td><td>₹263.00</td><td>₹66.00</td></tr>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        const ctxEx = document.getElementById('exchangeChart').getContext('2d');
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
    error = None
    msg = request.args.get("msg")
    
    if request.method == "GET":
        session.clear()
        n1, n2 = random.randint(1, 15), random.randint(1, 10)
        session["math_ans"] = str(n1 + n2)
        session["math_q"] = f"{n1} + {n2} = ?"

    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        if request.form.get("math_input", "").strip() != session.get("math_ans", ""):
            error = "Math Verification Failed!"
        else:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                               (request.form.get("username", "").strip(), request.form.get("password", "").strip()))
                user = cursor.fetchone()
            if user:
                session["logged_in"] = True
                session["username"] = user[1]
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid Credentials!"

    return render_template_string(LOGIN_HTML, error=error, msg=msg, math_question=session.get("math_q", "5 + 3 = ?"))

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("INSERT INTO users (username, password, mobile, email) VALUES (?, ?, ?, ?)",
                             (request.form.get("username"), request.form.get("password"), request.form.get("mobile"), request.form.get("email")))
            return redirect(url_for("login", msg="Registration successful! Please login."))
        except sqlite3.IntegrityError:
            error = "Username already exists!"
    return render_template_string(REGISTER_HTML, error=error)

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"): return redirect(url_for("login"))
    start_time = time.time()
    with sqlite3.connect(DB_NAME) as conn:
        vouchers = conn.execute("SELECT * FROM vouchers ORDER BY id DESC LIMIT 6").fetchall()
        revenue = conn.execute("SELECT SUM(total_with_gst) FROM vouchers WHERE voucher_type IN ('RECEIPT', 'SALES')").fetchone()[0] or 0.0
        expenses = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0.0
        banks = conn.execute("SELECT * FROM bank_accounts").fetchall()
        bank_bal = sum(b[3] for b in banks) if banks else 0.0
        adv_rows = conn.execute("SELECT adv_type, amount FROM advances WHERE status='PENDING'").fetchall()
        net_advances = sum(amt if t=='TAKEN' else -amt for t, amt in adv_rows)
        inv_rows = conn.execute("SELECT item_name, sku, qty, price, movement_type, market_status FROM inventory").fetchall()
        stock_map = {}
        for item_name, sku, qty, price, movement, m_status in inv_rows:
            if sku not in stock_map: stock_map[sku] = {"name": item_name, "qty": 0, "price": price, "status": m_status}
            if movement == 'INWARD': stock_map[sku]["qty"] += qty
            else: stock_map[sku]["qty"] -= qty
        stock_summary = [(data["name"], sku, data["status"], max(0, data["qty"]), data["price"]) for sku, data in stock_map.items()]
        profit = revenue - expenses
        kpis = {"revenue": revenue, "expenses": expenses, "profit": profit, "bank_bal": bank_bal, "advances": net_advances}
    query_latency = round((time.time() - start_time) * 1000, 2)
    return render_template_string(DASHBOARD_HTML, vouchers=vouchers, kpis=kpis, banks=banks, stock_summary=stock_summary, runway_days=45, sentinel_status="Optimal", query_latency=query_latency, username=session.get("username", "Admin"))

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

@app.route("/print_report_view")
def print_report_view():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        vouchers = conn.execute("SELECT * FROM vouchers ORDER BY id DESC").fetchall()
        banks = conn.execute("SELECT * FROM bank_accounts").fetchall()
    return render_template_string('''<h2>Report View</h2>''', vouchers=vouchers, banks=banks)

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
