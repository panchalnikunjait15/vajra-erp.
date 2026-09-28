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
    <title>Vajra Sovereign ERP - Secure Login</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #030712; color: #fff; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        .card { background: linear-gradient(135deg, #111827 0%, #0f172a 100%); padding: 35px 30px; border-radius: 16px; width: 100%; max-width: 400px; border: 1px solid #1f2937; text-align: center; box-shadow: 0 25px 60px rgba(0,0,0,0.9); }
        .logo-box { width: 70px; height: 70px; background: linear-gradient(135deg, #3b82f6, #1d4ed8); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin: 0 auto 15px auto; box-shadow: 0 0 20px rgba(59,130,246,0.5); }
        h2 { color: #38bdf8; margin: 0 0 5px 0; font-size: 1.25em; }
        p { color: #94a3b8; font-size: 0.85em; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 8px 0; background: #030712; border: 1px solid #374151; color: #fff; border-radius: 8px; box-sizing: border-box; }
        .captcha-container { background: #0f172a; border: 1px solid #374151; padding: 12px; border-radius: 8px; margin: 12px 0; display: flex; align-items: center; justify-content: space-between; font-size: 1.1em; color: #38bdf8; font-family: monospace; font-weight: bold; }
        button { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; border: none; padding: 13px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 12px; }
        .error { color: #f43f5e; background: rgba(244,63,94,0.1); padding: 10px; border-radius: 8px; font-size: 0.85em; margin-bottom: 15px; border: 1px solid #f43f5e; text-align: left; }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo-box"><i class="fas fa-shield-alt" style="font-size: 2em; color: #fff;"></i></div>
        <h2>Vajra Sovereign ERP</h2>
        <p>Enterprise Login & Captcha Security</p>
        {% if error %}<div class="error"><i class="fas fa-exclamation-triangle"></i> {{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username (VajraERP)" required autocomplete="off">
            <input type="password" name="password" placeholder="Password (Vajra@erp)" required autocomplete="off">
            <div class="captcha-container">
                <span><i class="fas fa-calculator" style="margin-right: 8px;"></i> Solve: {{ math_question }}</span>
            </div>
            <input type="number" name="math_input" placeholder="Enter Math Answer" required autocomplete="off">
            <button type="submit">Secure Access Login</button>
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
    <title>Vajra ERP - Multi-Lingual Dashboard & AI Voice</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #030712; color: #f8f9fa; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 15px; box-sizing: border-box; }
        header { background: #0f172a; padding: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #3b82f6; border-radius: 10px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { margin: 0; font-size: 1.25em; color: #38bdf8; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        
        .lang-switcher { display: flex; gap: 4px; background: #030712; padding: 3px; border-radius: 6px; border: 1px solid #1f2937; }
        .lang-btn { background: transparent; border: none; color: #94a3b8; padding: 6px 10px; cursor: pointer; font-size: 0.85em; font-weight: bold; border-radius: 4px; transition: 0.2s; }
        .lang-btn.active { background: #3b82f6; color: white; }

        .pro-banner { background: linear-gradient(135deg, #1e1b4b, #312e81); border: 2px solid #3b82f6; padding: 20px; border-radius: 12px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; gap: 15px; flex-wrap: wrap; box-shadow: 0 10px 30px rgba(59,130,246,0.25); }
        .pro-banner h3 { margin: 0 0 5px 0; color: #e0e7ff; font-size: 1.2em; }
        .pro-banner p { margin: 0; color: #c7d2fe; font-size: 0.9em; }
        .launch-btn { background: #10b981; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1em; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 15px rgba(16,185,129,0.4); white-space: nowrap; }
        .launch-btn:hover { background: #059669; }

        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }
        .kpi { background: #111827; padding: 15px; border-radius: 10px; border: 1px solid #1f2937; box-shadow: 0 8px 20px rgba(0,0,0,0.3); }
        .kpi h3 { margin: 0; font-size: 0.7em; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
        .kpi p { margin: 6px 0 0 0; font-size: 1.25em; font-weight: bold; color: #38bdf8; word-break: break-all; }

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
        
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.85em; min-width: 320px; }
        th, td { border: 1px solid #1f2937; padding: 8px 6px; text-align: left; }
        th { background: #0f172a; color: #38bdf8; }
        
        .share-group { display: flex; gap: 4px; flex-wrap: wrap; }
        .whatsapp-btn { background: #25d366; color: white; padding: 4px 6px; border-radius: 4px; text-decoration: none; font-size: 0.7em; display: inline-flex; align-items: center; gap: 3px; font-weight: bold; }
        .telegram-btn { background: #0088cc; color: white; padding: 4px 6px; border-radius: 4px; text-decoration: none; font-size: 0.7em; display: inline-flex; align-items: center; gap: 3px; font-weight: bold; }
        .gmail-btn { background: #ea4335; color: white; padding: 4px 6px; border-radius: 4px; text-decoration: none; font-size: 0.7em; display: inline-flex; align-items: center; gap: 3px; font-weight: bold; }
    </style>
</head>
<body>
    <header>
        <h1>
            <i class="fas fa-shield-alt"></i> <span data-key="header_title">VAJRA ERP & BUSINESS SUITE</span>
            <span style="font-size: 0.65em; background: rgba(59,130,246,0.2); border: 1px solid #3b82f6; padding: 2px 8px; border-radius: 15px; color: #38bdf8;">
                <i class="fas fa-user-circle"></i> {{ username }}
            </span>
        </h1>
        
        <div class="lang-switcher">
            <button class="lang-btn active" onclick="setLanguage('en')">EN</button>
            <button class="lang-btn" onclick="setLanguage('hi')">हिन्दी</button>
            <button class="lang-btn" onclick="setLanguage('gu')">ગુજરાતી</button>
        </div>

        <div style="display: flex; gap: 8px; align-items: center;">
            <span style="font-family: monospace; color: #34d399; font-size: 0.8em;"><i class="fas fa-bolt"></i> {{ query_latency }} ms</span>
            <a href="/logout" class="logout" style="padding: 6px 12px; border-radius: 6px; text-decoration:none; font-size:0.85em; font-weight:bold; color:#fff;" data-key="logout">Logout</a>
        </div>
    </header>
    
    <!-- 🚀 PRO TRADING TERMINAL LAUNCH BANNER -->
    <div class="pro-banner">
        <div>
            <h3 data-key="pro_banner_title"><i class="fas fa-rocket"></i> Vajra Pro Trading Terminal (Upstox & Groww Mode)</h3>
            <p data-key="pro_banner_desc">Click here to open a dedicated professional trading exchange world featuring Futures, Option Chain, SIP/Earn, Orders, and TradingView charts.</p>
        </div>
        <a href="/pro_trading_hub" class="launch-btn"><i class="fas fa-external-link-alt"></i> <span data-key="launch_btn">Open Pro Trading World</span></a>
    </div>

    <div class="btn-row">
        <a href="/backup_db"><i class="fas fa-database"></i> <span data-key="backup_db">Backup DB</span></a>
        <a href="/export_inventory_csv"><i class="fas fa-download"></i> <span data-key="export_csv">Export CSV</span></a>
        <a href="/print_report_view"><i class="fas fa-print"></i> <span data-key="print_report">Print / Save PDF</span></a>
    </div>

    <!-- 🤖 VAJRA AI VOICE & SMART ASSISTANT WIDGET -->
    <div class="card" style="margin-bottom: 20px; border: 1.5px solid #818cf8; background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);">
        <h3><span><i class="fas fa-microphone-alt" style="color: #818cf8;"></i> <span data-key="ai_voice_title">Vajra AI Voice & Smart Assistant</span></span></h3>
        <p id="voiceStatus" style="color: #38bdf8; margin: 6px 0; font-size: 0.9em;" data-key="voice_hint">Click mic to speak or use quick buttons below:</p>
        <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 10px;">
            <button onclick="startVoiceRecognition()" style="background: linear-gradient(135deg, #2563eb, #1d4ed8); width: auto; padding: 9px 14px; margin-top: 0; border-radius: 8px;"><i class="fas fa-microphone"></i> <span data-key="speak_btn">🎤 Speak</span></button>
            <input type="text" id="aiTextInput" data-placeholder="type_query_placeholder" placeholder="Type query here..." style="flex: 1; min-width: 160px; margin-top: 0; padding: 10px; background: #030712; border: 1px solid #4f46e5; border-radius: 8px; color: #fff;" onkeypress="if(event.key==='Enter') sendQueryToAI(this.value)">
            <button onclick="sendQueryToAI(document.getElementById('aiTextInput').value)" style="background: linear-gradient(135deg, #10b981, #059669); width: auto; padding: 9px 16px; margin-top: 0; border-radius: 8px;"><span data-key="ask_btn">Ask AI</span></button>
        </div>
        <div style="display: flex; gap: 6px; flex-wrap: wrap; border-top: 1px solid #312e81; padding-top: 10px;">
            <button onclick="quickAsk('profit')" style="background: #3b82f6; width: auto; padding: 5px 10px; margin-top:0; font-size: 0.8em; border-radius: 6px;"><span data-key="btn_profit">Net Profit</span></button>
            <button onclick="quickAsk('sales')" style="background: #6366f1; width: auto; padding: 5px 10px; margin-top:0; font-size: 0.8em; border-radius: 6px;"><span data-key="btn_sales">Total Sales</span></button>
            <button onclick="quickAsk('bank')" style="background: #0ea5e9; width: auto; padding: 5px 10px; margin-top:0; font-size: 0.8em; border-radius: 6px;"><span data-key="btn_bank">Bank Balance</span></button>
            <button onclick="quickAsk('stock')" style="background: #10b981; width: auto; padding: 5px 10px; margin-top:0; font-size: 0.8em; border-radius: 6px;"><span data-key="btn_stock">Stock Summary</span></button>
        </div>
        <p id="aiReply" style="margin-top: 12px; font-size: 1em; font-weight: bold; color: #4ade80; border-left: 4px solid #22c55e; padding-left: 8px; display: none;"></p>
    </div>

    <div class="kpi-grid">
        <div class="kpi"><h3 data-key="kpi_revenue">Total Revenue</h3><p>₹<span class="num-val" data-val="{{ "%.2f"|format(kpis.revenue) }}">{{ "%.2f"|format(kpis.revenue) }}</span></p></div>
        <div class="kpi"><h3 data-key="kpi_profit">Net Profit (P&L)</h3><p>₹<span class="num-val" data-val="{{ "%.2f"|format(kpis.profit) }}">{{ "%.2f"|format(kpis.profit) }}</span></p></div>
        <div class="kpi"><h3 data-key="kpi_bank">Total Bank Balance</h3><p style="color: #34d399;">₹<span class="num-val" data-val="{{ "%.2f"|format(kpis.bank_bal) }}">{{ "%.2f"|format(kpis.bank_bal) }}</span></p></div>
        <div class="kpi"><h3 data-key="kpi_advances">Net Advances</h3><p>₹<span class="num-val" data-val="{{ "%.2f"|format(kpis.advances) }}">{{ "%.2f"|format(kpis.advances) }}</span></p></div>
    </div>

    <!-- BANK ACCOUNTS & TRANSACTIONS HUB (RESTORED) -->
    <div class="main-grid">
        <div class="card">
            <h3><span><i class="fas fa-university"></i> <span data-key="bank_hub_title">Indian Bank Accounts Hub</span></span></h3>
            <table>
                <tr><th data-key="th_bank_name">Bank Name</th><th data-key="th_acc_no">A/C No</th><th data-key="th_balance">Balance</th></tr>
                {% if banks %}
                    {% for b in banks %}
                    <tr>
                        <td><strong>{{ b[1] }}</strong></td>
                        <td><span class="num-val" data-val="{{ b[2] }}">{{ b[2] }}</span></td>
                        <td style="color:#34d399; font-weight:bold;">₹<span class="num-val" data-val="{{ "%.2f"|format(b[3]) }}">{{ "%.2f"|format(b[3]) }}</span></td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr><td colspan="3" style="text-align: center; color: #f43f5e;" data-key="no_bank">No bank accounts registered yet.</td></tr>
                {% endif %}
            </table>
            
            <form action="/add_bank" method="POST" style="margin-top:15px; border-top:1px solid #1f2937; padding-top:12px;">
                <label style="color:#38bdf8;" data-key="lbl_add_bank">+ Add Indian Bank Account:</label>
                <select name="bank_name" required>
                    <option value="State Bank of India (SBI)">State Bank of India (SBI)</option>
                    <option value="HDFC Bank">HDFC Bank</option>
                    <option value="ICICI Bank">ICICI Bank</option>
                    <option value="Axis Bank">Axis Bank</option>
                    <option value="Punjab National Bank (PNB)">Punjab National Bank (PNB)</option>
                    <option value="Bank of Baroda">Bank of Baroda</option>
                    <option value="The Kalupur Commercial Co-op Bank">The Kalupur Commercial Co-op Bank</option>
                </select>
                <label data-key="lbl_acc_num">Account Number:</label><input type="text" name="account_no" placeholder="Enter A/C No" required>
                <label data-key="lbl_opening_bal">Opening Balance (₹):</label><input type="number" step="0.01" name="balance" value="0.0" required>
                <button type="submit" style="background:#6366f1; margin-top:8px;" data-key="btn_register_bank">Register Bank</button>
            </form>
        </div>

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
    </div>

    <!-- INVENTORY & ADVANCES -->
    <div class="main-grid">
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
                <div style="display: flex; gap: 8px; margin-top: 8px;">
                    <div style="flex:1;"><label data-key="lbl_qty">Qty:</label><input type="number" name="qty" required></div>
                    <div style="flex:1;"><label data-key="lbl_price">Price (₹):</label><input type="number" step="0.01" name="price" required></div>
                </div>
                <button type="submit" data-key="btn_update_stock">Update Stock</button>
            </form>
        </div>

        <div class="card">
            <h3><span><i class="fas fa-hand-holding-usd"></i> <span data-key="adv_title">Advance Ledger</span></span></h3>
            <form action="/add_advance" method="POST">
                <label data-key="lbl_party_name">Party Name:</label><input type="text" name="party_name" required>
                <label data-key="lbl_adv_type">Advance Type:</label>
                <select name="adv_type">
                    <option value="GIVEN" data-key="opt_adv_given">Advance Given</option>
                    <option value="TAKEN" data-key="opt_adv_taken">Advance Taken</option>
                </select>
                <label data-key="lbl_amount">Amount (₹):</label><input type="number" step="0.01" name="amount" required>
                <button type="submit" style="background:#8b5cf6;" data-key="btn_record_adv">Record Advance</button>
            </form>
        </div>
    </div>

    <!-- RECENT VOUCHERS WITH DIRECT WHATSAPP, TELEGRAM & GMAIL SHARING -->
    <div class="card">
        <h3><span><i class="fas fa-history"></i> <span data-key="history_title">Recent Vouchers & Direct Sharing</span></span></h3>
        <table>
            <tr><th data-key="th_type">Type</th><th data-key="th_party">Party</th><th data-key="th_total">Total (Inc. GST)</th><th data-key="th_action">Action</th></tr>
            {% for v in vouchers %}
            <tr>
                <td><span class="vtype-val" data-val="{{ v[2] }}">{{ v[2] }}</span></td>
                <td>{{ v[3] }}</td>
                <td>₹<span class="num-val" data-val="{{ "%.2f"|format(v[6]) }}">{{ "%.2f"|format(v[6]) }}</span></td>
                <td>
                    <div class="share-group">
                        <a href="https://api.whatsapp.com/send?text=Vajra%20ERP%20Invoice:%20{{ v[2] }}%20for%20{{ v[3] }}%20Amount:%20₹{{ '%.2f'|format(v[6]) }}" target="_blank" class="whatsapp-btn">
                            <i class="fab fa-whatsapp"></i> <span data-key="share_wa">WA</span>
                        </a>
                        <a href="https://t.me/share/url?url=https://vajra-erp.onrender.com&text=Vajra%20ERP%20Invoice:%20{{ v[2] }}%20for%20{{ v[3] }}%20Amount:%20₹{{ '%.2f'|format(v[6]) }}" target="_blank" class="telegram-btn">
                            <i class="fab fa-telegram-plane"></i> <span data-key="share_tg">TG</span>
                        </a>
                        <a href="https://mail.google.com/mail/?view=cm&fs=1&su=Vajra%20ERP%20Invoice&body=Voucher%20Type:%20{{ v[2] }}%20Party:%20{{ v[3] }}%20Amount:%20₹{{ '%.2f'|format(v[6]) }}" target="_blank" class="gmail-btn">
                            <i class="fas fa-envelope"></i> <span data-key="share_mail">Mail</span>
                        </a>
                    </div>
                </td>
            </tr>
            {% endfor %}
        </table>
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
                pro_banner_title: "Vajra Pro Trading Terminal (Upstox & Groww Mode)",
                pro_banner_desc: "Click here to open a dedicated professional trading exchange world featuring Futures, Option Chain, SIP/Earn, Orders, and TradingView charts.",
                launch_btn: "Open Pro Trading World",
                kpi_revenue: "Total Revenue",
                kpi_profit: "Net Profit (P&L)",
                kpi_bank: "Total Bank Balance",
                kpi_advances: "Net Advances",
                bank_hub_title: "Indian Bank Accounts Hub",
                th_bank_name: "Bank Name",
                th_acc_no: "A/C No",
                th_balance: "Balance",
                no_bank: "No bank accounts registered yet.",
                lbl_add_bank: "+ Add Indian Bank Account:",
                lbl_acc_num: "Account Number:",
                lbl_opening_bal: "Opening Balance (₹):",
                btn_register_bank: "Register Bank",
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
                lbl_qty: "Qty:",
                lbl_price: "Price (₹):",
                btn_update_stock: "Update Stock",
                adv_title: "Advance Ledger",
                lbl_party_name: "Party Name:",
                lbl_adv_type: "Advance Type:",
                opt_adv_given: "Advance Given",
                opt_adv_taken: "Advance Taken",
                btn_record_adv: "Record Advance",
                history_title: "Recent Vouchers & Direct Sharing",
                th_type: "Type",
                th_party: "Party",
                th_total: "Total (Inc. GST)",
                th_action: "Action",
                share_wa: "WA",
                share_tg: "TG",
                share_mail: "Mail",
                ai_voice_title: "Vajra AI Voice & Smart Assistant",
                speak_btn: "🎤 Speak",
                ask_btn: "Ask AI",
                voice_hint: "Click mic to speak or use quick buttons below:",
                type_query_placeholder: "Type query here...",
                ai_prefix: "🤖 AI Answer: ",
                btn_profit: "Net Profit",
                btn_sales: "Total Sales",
                btn_bank: "Bank Balance",
                btn_stock: "Stock Summary",
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
                pro_banner_title: "वज्र प्रो ट्रेडिंग टर्मिनल (Upstox और Groww मोड)",
                pro_banner_desc: "फ्यूचर्स, ऑप्शन चेन, SIP/अर्न, ऑर्डर्स और TradingView चार्ट वाला समर्पित एक्सचेंज खोलने के लिए क्लिक करें।",
                launch_btn: "प्रो ट्रेडिंग वर्ल्ड खोलें",
                kpi_revenue: "कुल राजस्व",
                kpi_profit: "शुद्ध लाभ (P&L)",
                kpi_bank: "कुल बैंक शेष",
                kpi_advances: "शुद्ध अग्रिम",
                bank_hub_title: "भारतीय बैंक खाता हब",
                th_bank_name: "बैंक का नाम",
                th_acc_no: "खाता नंबर",
                th_balance: "शेष राशि",
                no_bank: "अभी तक कोई बैंक पंजीकृत नहीं है।",
                lbl_add_bank: "+ भारतीय बैंक खाता जोड़ें:",
                lbl_acc_num: "खाता संख्या:",
                lbl_opening_bal: "शुरुआती शेष (₹):",
                btn_register_bank: "बैंक पंजीकृत करें",
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
                lbl_qty: "मात्रा:",
                lbl_price: "मूल्य (₹):",
                btn_update_stock: "स्टॉक अपडेट करें",
                adv_title: "अग्रिम खाता लेजर",
                lbl_party_name: "पार्टी का नाम:",
                lbl_adv_type: "अग्रिम प्रकार:",
                opt_adv_given: "अग्रिम दिया गया",
                opt_adv_taken: "अग्रिम लिया गया",
                btn_record_adv: "अग्रिम दर्ज करें",
                history_title: "हाल के वाउचर और डायरेक्ट शेयरिंग",
                th_type: "प्रकार",
                th_party: "पार्टी",
                th_total: "कुल (जीएसटी सहित)",
                th_action: "कार्रवाई",
                share_wa: "व्हाट्सऐप",
                share_tg: "टेलीग्राम",
                share_mail: "मेल",
                ai_voice_title: "वज्र एआई वॉयस और स्मार्ट असिस्टेंट",
                speak_btn: "🎤 बोलें",
                ask_btn: "पूछें",
                voice_hint: "माइक दबाएं, क्विक बटन उपयोग करें या नीचे टाइप करें:",
                type_query_placeholder: "यहाँ अपना प्रश्न टाइप करें...",
                ai_prefix: "🤖 एआई उत्तर: ",
                btn_profit: "शुद्ध लाभ",
                btn_sales: "कुल बिक्री",
                btn_bank: "बैंक बैलेंस",
                btn_stock: "स्टॉक सारांश",
                vtype_RECEIPT: "रसीद",
                vtype_PAYMENT: "भुगतान",
                vtype_SALES: "बिक्री",
                vtype_PURCHASE: "खरीद"
            },
            gu: {
                header_title: "વજ્ર ERP અને બિઝનેસ સૂટ",
                logout: "લોગઆઉટ",
                backup_db: "બેકઅપ ડીબી",
                export_csv: "ઇન્વેન્ટરી એક્સપોર્ટ",
                print_report: "પ્રિન્ટ / PDF સેવ કરો",
                pro_banner_title: "વજ્ર પ્રો ટ્રેડિંગ ટર્મિનલ (Upstox & Groww મોડ)",
                pro_banner_desc: "ફ્યુચર્સ, ઓપ્શન ચેઈન, SIP/અર્ન, ઓર્ડર્સ અને TradingView ચાર્ટવાળી અદભુત ટ્રેડિંગ દુનિયા ખોલવા માટે ક્લિક કરો.",
                launch_btn: "પ્રો ટ્રેડિંગ વર્લ્ડ ખોલો",
                kpi_revenue: "કુલ આવક",
                kpi_profit: "નેટ પ્રોફિટ (નફો)",
                kpi_bank: "કુલ બેંક બેલેન્સ",
                kpi_advances: "નેટ એડવાન્સ",
                bank_hub_title: "ઇન્ડિયન બેંક એકાઉન્ટ્સ હબ",
                th_bank_name: "બેંકનું નામ",
                th_acc_no: "એકાઉન્ટ નંબર",
                th_balance: "બેલેન્સ",
                no_bank: "હજી સુધી કોઈ બેંક એડ નથી કરી.",
                lbl_add_bank: "+ નવી બેંક ઉમેરો:",
                lbl_acc_num: "એકાઉન્ટ નંબર:",
                lbl_opening_bal: "શરૂઆતનું બેલેન્સ (₹):",
                btn_register_bank: "બેંક રજીસ્ટર કરો",
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
                lbl_qty: "જથ્થો (Qty):",
                lbl_price: "કિંમત (₹):",
                btn_update_stock: "સ્ટોક અપડેટ કરો",
                adv_title: "એડવાન્સ એકાઉન્ટ લેજર",
                lbl_party_name: "પાર્ટીનું નામ:",
                lbl_adv_type: "એડવાન્સ પ્રકાર:",
                opt_adv_given: "એડવાન્સ આપેલું",
                opt_adv_taken: "એડવાન્સ લીધેલું",
                btn_record_adv: "એડવાન્સ નોંધી કરો",
                history_title: "તાજેતરના વાઉચર્સ અને ડાયરેક્ટ શેરિંગ",
                th_type: "પ્રકાર",
                th_party: "પાર્ટી",
                th_total: "કુલ (જીએસટી સાથે)",
                th_action: "એક્શન",
                share_wa: "વ્હોટ્સએપ",
                share_tg: "ટેલિગ્રામ",
                share_mail: "મેઇલ",
                ai_voice_title: "વજ્ર એઆઈ વોઇસ અને સ્માર્ટ અસિસ્ટન્ટ",
                speak_btn: "🎤 બોલો",
                ask_btn: "પૂછો",
                voice_hint: "માઇક, ક્વિક બટન અથવા નીચે ટાઈપ કરો:",
                type_query_placeholder: "તમારો પ્રશ્ન અહીં ટાઈપ કરો...",
                ai_prefix: "🤖 એઆઈ જવાબ: ",
                btn_profit: "નેટ નફો",
                btn_sales: "કુલ વેચાણ",
                btn_bank: "બેંક બેલેન્સ",
                btn_stock: "સ્ટોક રિપોર્ટ",
                vtype_RECEIPT: "રસીદ",
                vtype_PAYMENT: "ચુકવણી",
                vtype_SALES: "વેચાણ",
                vtype_PURCHASE: "ખરીદી"
            }
        };

        function setLanguage(lang) {
            currentLang = lang;
            document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            document.querySelectorAll('[data-key]').forEach(el => {
                const key = el.getAttribute('data-key');
                if (translations[lang] && translations[lang][key]) {
                    el.textContent = translations[lang][key];
                }
            });

            document.querySelectorAll('.num-val').forEach(el => {
                el.textContent = convertDigits(el.getAttribute('data-val'), lang);
            });

            document.querySelectorAll('.vtype-val').forEach(el => {
                const vtype = el.getAttribute('data-val');
                const tKey = 'vtype_' + vtype;
                if (translations[lang] && translations[lang][tKey]) {
                    el.textContent = translations[lang][tKey];
                } else {
                    el.textContent = vtype;
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

        let activeRecognition = null;

        function startVoiceRecognition() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert(currentLang === 'gu' ? "આ બ્રાઉઝરમાં વોઇસ સપોર્ટ નથી." : "Voice recognition not supported.");
                return;
            }
            try {
                if (activeRecognition) { activeRecognition.abort(); }
                activeRecognition = new SpeechRecognition();
                activeRecognition.continuous = false;
                activeRecognition.interimResults = true;
                activeRecognition.lang = currentLang === 'gu' ? 'gu-IN' : (currentLang === 'hi' ? 'hi-IN' : 'en-US');
                
                document.getElementById("voiceStatus").innerText = currentLang === 'gu' ? "સંભળાઈ રહ્યું છે... બોલો!" : "Listening...";

                activeRecognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById("aiTextInput").value = transcript;
                    if (event.results[0].isFinal) {
                        sendQueryToAI(transcript);
                    }
                };

                activeRecognition.onerror = function() {
                    document.getElementById("voiceStatus").innerText = "Mic error.";
                };

                activeRecognition.onend = function() {
                    document.getElementById("voiceStatus").innerText = currentLang === 'gu' ? "માઈક બંધ." : "Mic idle.";
                };

                activeRecognition.start();
            } catch(e) {
                document.getElementById("voiceStatus").innerText = "Mic unavailable.";
            }
        }

        function quickAsk(queryType) {
            document.getElementById("aiTextInput").value = queryType;
            sendQueryToAI(queryType);
        }

        function sendQueryToAI(queryText) {
            if(!queryText.trim()) return;
            const replyElem = document.getElementById("aiReply");
            replyElem.style.display = "block";
            replyElem.innerText = "Processing...";

            fetch('/api/ai-assistant', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: queryText, lang: currentLang })
            })
            .then(res => res.json())
            .then(data => {
                let replyPrefix = currentLang === 'gu' ? "🤖 એઆઈ જવાબ: " : (currentLang === 'hi' ? "🤖 एआई उत्तर: " : "🤖 AI Answer: ");
                replyElem.innerText = replyPrefix + data.reply;
            })
            .catch(err => {
                replyElem.innerText = "Error connecting to AI Assistant.";
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

        .tab-content { display: none; padding: 20px; max-width: 1300px; margin: 0 auto; }
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
        <button class="ex-tab active" onclick="switchTab(event, 'tab-explore')"><i class="fas fa-compass"></i> Explore / Gainers</button>
        <button class="ex-tab" onclick="switchTab(event, 'tab-futures')"><i class="fas fa-rocket"></i> Futures & Options</button>
        <button class="ex-tab" onclick="switchTab(event, 'tab-options')"><i class="fas fa-table-cells"></i> Option Chain</button>
        <button class="ex-tab" onclick="switchTab(event, 'tab-global')"><i class="fas fa-globe"></i> Global Futures</button>
        <button class="ex-tab" onclick="switchTab(event, 'tab-sip')"><i class="fas fa-piggy-bank"></i> SIP & Mutual Funds</button>
        <button class="ex-tab" onclick="switchTab(event, 'tab-orders')"><i class="fas fa-receipt"></i> Orders & Portfolio</button>
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
            <table>
                <tr><th>Contract Name</th><th>Expiry Date</th><th>LTP (₹)</th><th>Open Interest (OI)</th><th>Action</th></tr>
                <tr><td><strong>NIFTY 28OCT FUT</strong></td><td>28-Oct-2026</td><td>₹24,880.50</td><td>1.45 Cr</td><td><button style="background:#10b981; padding:6px 12px; width:auto;">Trade Future</button></td></tr>
                <tr><td><strong>BANKNIFTY 28OCT FUT</strong></td><td>28-Oct-2026</td><td>₹51,400.00</td><td>98 Lakh</td><td><button style="background:#10b981; padding:6px 12px; width:auto;">Trade Future</button></td></tr>
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
            </table>
        </div>
    </div>

    <!-- TAB 5: SIP & EARN -->
    <div id="tab-sip" class="tab-content">
        <div class="ex-card">
            <h3><i class="fas fa-piggy-bank"></i> Vajra Smart SIP & High-Yield Earn Funds</h3>
            <table>
                <tr><th>Fund Name</th><th>Category</th><th>3Y Returns (CAGR)</th><th>Action</th></tr>
                <tr><td><strong>Vajra Bluechip Equity Fund</strong></td><td>Large Cap</td><td>22.4%</td><td><button style="background:#3b82f6; padding:6px 12px; width:auto;">Start SIP</button></td></tr>
            </table>
        </div>
    </div>

    <!-- TAB 6: ORDERS & PORTFOLIO -->
    <div id="tab-orders" class="tab-content">
        <div class="ex-card">
            <h3><i class="fas fa-receipt"></i> Active Orders & Holdings Portfolio</h3>
            <table>
                <tr><th>Symbol</th><th>Type</th><th>Action</th><th>Price</th><th>Qty</th><th>Status</th></tr>
                <tr><td>RELIANCE</td><td>STOCK</td><td>BUY</td><td>₹2,940.15</td><td>5.0</td><td><span style="color:#10b981; font-weight:bold;">EXECUTED (LIVE)</span></td></tr>
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
    if request.method == "GET":
        session.clear()
        n1, n2 = random.randint(1, 15), random.randint(1, 10)
        session["math_ans"] = str(n1 + n2)
        session["math_q"] = f"{n1} + {n2} = ?"
    if session.get("logged_in"): return redirect(url_for("dashboard"))
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
        profit = revenue - expenses
        kpis = {"revenue": revenue, "expenses": expenses, "profit": profit, "bank_bal": bank_bal, "advances": net_advances}
    query_latency = round((time.time() - start_time) * 1000, 2)
    return render_template_string(DASHBOARD_HTML, vouchers=vouchers, kpis=kpis, banks=banks, query_latency=query_latency, username=session.get("username", "Admin"))

@app.route("/pro_trading_hub")
def pro_trading_hub():
    if not session.get("logged_in"): return redirect(url_for("login"))
    return render_template_string(TRADING_WORLD_HTML)

@app.route("/api/ai-assistant", methods=["POST"])
def ai_assistant():
    data = request.get_json(silent=True) or {}
    q = str(data.get("query", "")).lower()
    lang = str(data.get("lang", "en"))
    
    with sqlite3.connect(DB_NAME) as conn:
        rev = conn.execute("SELECT SUM(total_with_gst) FROM vouchers WHERE voucher_type IN ('RECEIPT', 'SALES')").fetchone()[0] or 0.0
        purch = conn.execute("SELECT SUM(total_with_gst) FROM vouchers WHERE voucher_type = 'PURCHASE'").fetchone()[0] or 0.0
        exp = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0.0
        net_profit = rev - exp
        banks_total = conn.execute("SELECT SUM(balance) FROM bank_accounts").fetchone()[0] or 0.0
        total_items = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0] or 0
    
    if lang == "gu":
        response_text = f"કુલ વેચાણ / આવક ₹{rev:.2f} છે."
        if "profit" in q or "labh" in q or "નફો" in q or "nafa" in q:
            response_text = f"આજે કુલ નેટ નફો ₹{net_profit:.2f} થયો છે."
        elif "sales" in q or "vechan" in q or "aavak" in q or "revenue" in q or "વેચાણ" in q:
            response_text = f"કુલ વેચાણ / આવક ₹{rev:.2f} છે."
        elif "purchase" in q or "kharidi" in q or "ખરીદી" in q:
            response_text = f"કુલ ખરીદી ₹{purch:.2f} છે."
        elif "bank" in q or "balance" in q or "belez" in q:
            response_text = f"બધી બેંકનું કુલ બેલેન્સ ₹{banks_total:.2f} છે."
        elif "stock" in q or "stok" in q:
            response_text = f"ઇન્વેન્ટરી સ્ટોક મેનેજમેન્ટમાં કુલ {total_items} આઇટમ્સ રજીસ્ટર થયેલી છે."
    elif lang == "hi":
        response_text = f"कुल राजस्व / बिक्री ₹{rev:.2f} है।"
        if "profit" in q or "labh" in q or "नफा" in q:
            response_text = f"आज कुल शुद्ध लाभ ₹{net_profit:.2f} हुआ है।"
        elif "sales" in q or "bikri" in q or "revenue" in q:
            response_text = f"कुल राजस्व / बिक्री ₹{rev:.2f} है।"
        elif "purchase" in q or "kharidi" in q:
            response_text = f"कुल खरीद ₹{purch:.2f} है।"
        elif "bank" in q or "balance" in q:
            response_text = f"सभी बैंकों का कुल शेष ₹{banks_total:.2f} है।"
        elif "stock" in q:
            response_text = f"इन्वेंट्री स्टॉक में कुल {total_items} आइटम पंजीकृत हैं।"
    else:
        response_text = f"Total revenue / sales is ₹{rev:.2f}."
        if "profit" in q:
            response_text = f"Today's net profit is ₹{net_profit:.2f}."
        elif "sales" in q or "revenue" in q:
            response_text = f"Total revenue / sales is ₹{rev:.2f}."
        elif "purchase" in q:
            response_text = f"Total purchase is ₹{purch:.2f}."
        elif "bank" in q or "balance" in q:
            response_text = f"Total bank balance across accounts is ₹{banks_total:.2f}."
        elif "stock" in q:
            response_text = f"Live inventory stock summary: {total_items} items registered."

    return jsonify({"status": "success", "reply": response_text})

@app.route("/add_watchlist", methods=["POST"])
def add_watchlist():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO trading_portfolio (symbol, asset_type, action_type, buy_price, qty, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                     (request.form.get("symbol"), request.form.get("asset_type"), request.form.get("action_type"), float(request.form.get("buy_price")), float(request.form.get("qty")), datetime.now().strftime("%Y-%m-%d %H:%M")))
    return redirect(url_for("pro_trading_hub"))

@app.route("/add_bank", methods=["POST"])
def add_bank():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO bank_accounts (bank_name, account_no, balance) VALUES (?, ?, ?)",
                     (request.form.get("bank_name"), request.form.get("account_no"), float(request.form.get("balance"))))
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
        conn.execute("INSERT INTO inventory (item_name, sku, qty, price, movement_type) VALUES (?, ?, ?, ?, ?)",
                     (request.form.get("item_name"), request.form.get("sku"), int(request.form.get("qty")), float(request.form.get("price")), request.form.get("movement_type")))
    return redirect(url_for("dashboard"))

@app.route("/add_advance", methods=["POST"])
def add_advance():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO advances (party_name, adv_type, amount, date) VALUES (?, ?, ?, ?)",
                     (request.form.get("party_name"), request.form.get("adv_type"), float(request.form.get("amount")), datetime.now().strftime("%Y-%m-%d")))
    return redirect(url_for("dashboard"))

@app.route("/print_report_view")
def print_report_view():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        vouchers = conn.execute("SELECT * FROM vouchers ORDER BY id DESC").fetchall()
        banks = conn.execute("SELECT * FROM bank_accounts").fetchall()
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vajra ERP - Print & Download Report</title>
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
    ''', vouchers=vouchers, banks=banks)

@app.route("/download_report_file")
def download_report_file():
    if not session.get("logged_in"): return redirect(url_for("login"))
    with sqlite3.connect(DB_NAME) as conn:
        vouchers = conn.execute("SELECT * FROM vouchers ORDER BY id DESC").fetchall()
        banks = conn.execute("SELECT * FROM bank_accounts").fetchall()
    
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
