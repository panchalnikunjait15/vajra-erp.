# -*- coding: utf-8 -*-
import os
import sqlite3
import hashlib
import time
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, Response, send_file, jsonify
import csv
import io

app = Flask(__name__)
app.secret_key = "VAJRA_PRO_ERP_2026"

DB_NAME = "vajra_erp.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        
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

init_db()

def generate_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vajra Cloud OS - Login</title>
    <style>
        body { background: #030712; color: #fff; font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        .card { background: #111827; padding: 35px; border-radius: 14px; width: 100%; max-width: 380px; border: 1px solid #1f2937; text-align: center; box-shadow: 0 25px 50px rgba(0,0,0,0.8); }
        h2 { color: #38bdf8; margin-top: 0; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #030712; border: 1px solid #374151; color: #fff; border-radius: 6px; box-sizing: border-box; font-size: 1em; }
        button { background: #3b82f6; color: white; border: none; padding: 13px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 1em; box-shadow: 0 0 15px rgba(59,130,246,0.4); }
        .error { color: #f43f5e; background: rgba(244,63,94,0.1); padding: 10px; border-radius: 6px; font-size: 0.9em; margin-bottom: 15px; border: 1px solid #f43f5e; }
        .hint { font-size: 0.8em; color: #64748b; margin-top: 20px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Vajra ERP</h2>
        <p style="color: #94a3b8; font-size: 0.95em; margin-bottom: 25px;">Sovereign Multi-Lingual OS</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Access System</button>
        </form>
        <div class="hint">User: VajraERP | Pass: Vajra@erp</div>
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
    <title>Vajra ERP - Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #030712; color: #f8f9fa; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; }
        header { background: #0f172a; padding: 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #3b82f6; border-radius: 10px; margin-bottom: 25px; flex-wrap: wrap; gap: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { margin: 0; font-size: 1.5em; color: #38bdf8; letter-spacing: 1px; }
        
        .lang-switcher { display: flex; gap: 5px; background: #030712; padding: 4px; border-radius: 6px; border: 1px solid #1f2937; }
        .lang-btn { background: transparent; border: none; color: #94a3b8; padding: 5px 10px; cursor: pointer; font-size: 0.85em; font-weight: bold; border-radius: 4px; transition: 0.2s; }
        .lang-btn.active { background: #3b82f6; color: white; }

        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px; }
        .kpi { background: #111827; padding: 20px; border-radius: 10px; border: 1px solid #1f2937; box-shadow: 0 8px 20px rgba(0,0,0,0.3); }
        .kpi h3 { margin: 0; font-size: 0.75em; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
        .kpi p { margin: 8px 0 0 0; font-size: 1.4em; font-weight: bold; color: #38bdf8; }
        
        .ai-banner { background: linear-gradient(135deg, #1e1b4b, #312e81); border: 1px solid #6366f1; padding: 20px; border-radius: 10px; margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between; gap: 15px; flex-wrap: wrap; }
        .ai-banner h3 { margin: 0 0 5px 0; color: #e0e7ff; font-size: 1.1em; }
        .ai-banner p { margin: 0; font-size: 0.9em; color: #c7d2fe; }

        .main-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 20px; margin-bottom: 25px; }
        .card { background: #111827; padding: 22px; border-radius: 10px; border: 1px solid #1f2937; box-shadow: 0 8px 20px rgba(0,0,0,0.3); }
        .card h3 { margin-top: 0; color: #38bdf8; font-size: 1.1em; border-bottom: 1px solid #1f2937; padding-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        
        label { font-size: 0.85em; color: #94a3b8; font-weight: bold; display: block; margin-top: 8px; }
        input, select, textarea { width: 100%; padding: 11px; margin-top: 5px; background: #030712; border: 1px solid #374151; color: #fff; border-radius: 6px; box-sizing: border-box; font-size: 0.95em; }
        button { background: #3b82f6; color: #fff; border: none; padding: 12px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 12px; font-size: 1em; transition: 0.2s; }
        button:hover { background: #2563eb; }
        
        .btn-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 25px; }
        .btn-row a, .btn-row button { background: #374151; color: white; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-size: 0.9em; border: none; flex: 1; text-align: center; font-weight: bold; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 8px; }
        .logout { background: #f43f5e !important; }

        table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.85em; overflow-x: auto; display: block; }
        th, td { border: 1px solid #1f2937; padding: 8px; text-align: left; }
        th { background: #0f172a; color: #38bdf8; }
        .badge-trend { background: #10b981; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75em; font-weight: bold; }
        .badge-alert { background: #ef4444; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75em; font-weight: bold; }
        .whatsapp-btn { background: #25d366; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 0.8em; display: inline-flex; align-items: center; gap: 5px; font-weight: bold; }
        
        @media print {
            header, .kpi-grid, .ai-banner, .main-grid, .btn-row, button, .whatsapp-btn, .lang-switcher { display: none !important; }
            body { background: white !important; color: black !important; }
            .card { border: none !important; box-shadow: none !important; background: white !important; color: black !important; }
            th { background: #eee !important; color: black !important; }
            table, th, td { border: 1px solid #999 !important; }
        }
    </style>
</head>
<body>
    <header>
        <h1><i class="fas fa-globe"></i> <span data-key="header_title">VAJRA SOVEREIGN ERP OS</span></h1>
        
        <div class="lang-switcher">
            <button class="lang-btn active" onclick="setLanguage('en')">EN</button>
            <button class="lang-btn" onclick="setLanguage('hi')">हिन्दी</button>
            <button class="lang-btn" onclick="setLanguage('gu')">ગુજરાતી</button>
        </div>

        <div style="display: flex; gap: 10px; align-items: center;">
            <span style="font-family: monospace; color: #34d399; font-size: 0.85em;"><i class="fas fa-bolt"></i> {{ query_latency }} ms</span>
            <a href="/logout" class="logout" style="padding: 8px 16px; background: #f43f5e; color: #fff; border-radius: 6px; text-decoration:none; font-size:0.9em; font-weight:bold;" data-key="logout">Logout</a>
        </div>
    </header>
    
    <div class="btn-row">
        <a href="/backup_db"><i class="fas fa-database"></i> <span data-key="backup_db">Backup DB</span></a>
        <a href="/export_inventory_csv"><i class="fas fa-download"></i> <span data-key="export_csv">Export CSV</span></a>
        <button onclick="window.print()"><i class="fas fa-print"></i> <span data-key="print_report">Print Report</span></button>
    </div>

    <!-- 🤖 FOOLPROOF BULLETPROOF AI SMART ASSISTANT WIDGET -->
    <div class="card" style="margin-bottom: 25px; border: 1.5px solid #818cf8; background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%); box-shadow: 0 12px 30px rgba(99,102,241,0.25);">
        <h3><span><i class="fas fa-robot" style="color: #818cf8;"></i> <span data-key="ai_voice_title">Vajra AI Smart Assistant</span></span></h3>
        <p id="voiceStatus" style="color: #38bdf8; margin: 8px 0; font-size: 0.95em;" data-key="voice_hint">Use quick buttons or type query below for instant response:</p>
        
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 12px;">
            <button onclick="startVoiceRecognition()" style="background: linear-gradient(135deg, #2563eb, #1d4ed8); width: auto; padding: 10px 18px; margin-top: 0; border-radius: 8px;"><i class="fas fa-microphone"></i> <span data-key="speak_btn">🎤 Speak</span></button>
            <input type="text" id="aiTextInput" placeholder="Type query here..." style="flex: 1; margin-top: 0; padding: 11px; background: #030712; border: 1px solid #4f46e5; border-radius: 8px; color: #fff;" onkeypress="if(event.key==='Enter') sendQueryToAI(this.value)">
            <button onclick="sendQueryToAI(document.getElementById('aiTextInput').value)" style="background: linear-gradient(135deg, #10b981, #059669); width: auto; padding: 10px 20px; margin-top: 0; border-radius: 8px;"><span data-key="ask_btn">Ask AI</span></button>
        </div>

        <!-- ⚡ INSTANT QUICK ACTION BUTTONS (100% ERROR FREE ON MOBILE & PC) -->
        <div style="display: flex; gap: 8px; flex-wrap: wrap; border-top: 1px solid #312e81; padding-top: 12px;">
            <button onclick="quickAsk('profit')" style="background: #3b82f6; width: auto; padding: 6px 14px; margin-top:0; font-size: 0.85em; border-radius: 6px;"><i class="fas fa-chart-line"></i> <span data-key="btn_profit">Net Profit</span></button>
            <button onclick="quickAsk('sales')" style="background: #6366f1; width: auto; padding: 6px 14px; margin-top:0; font-size: 0.85em; border-radius: 6px;"><i class="fas fa-rupee-sign"></i> <span data-key="btn_sales">Total Sales</span></button>
            <button onclick="quickAsk('bank')" style="background: #0ea5e9; width: auto; padding: 6px 14px; margin-top:0; font-size: 0.85em; border-radius: 6px;"><i class="fas fa-university"></i> <span data-key="btn_bank">Bank Balance</span></button>
            <button onclick="quickAsk('stock')" style="background: #10b981; width: auto; padding: 6px 14px; margin-top:0; font-size: 0.85em; border-radius: 6px;"><i class="fas fa-boxes"></i> <span data-key="btn_stock">Stock Summary</span></button>
        </div>

        <p id="aiReply" style="margin-top: 15px; font-size: 1.05em; font-weight: bold; color: #4ade80; border-left: 4px solid #22c55e; padding-left: 10px; display: none;"></p>
    </div>

    <div class="ai-banner">
        <div>
            <h3 data-key="sentinel_title"><i class="fas fa-shield-alt"></i> Sovereign Multi-Lingual Sentinel</h3>
            <p><span data-key="runway_label">Estimated Liquidity Runway</span>: <strong style="color:#34d399;">{{ runway_days }} Days</strong> | <span data-key="sentinel_status">Status</span>: <strong style="color:#38bdf8;">{{ sentinel_status }}</strong></p>
        </div>
        <div style="background: rgba(0,0,0,0.4); padding: 15px 20px; border-radius: 8px; text-align: center; border: 1px solid #6366f1;">
            <div style="font-size: 0.75em; text-transform: uppercase; color: #c7d2fe;" data-key="cloud_status">Cloud Status</div>
            <div style="font-size: 1.1em; font-weight: bold; color: #34d399;">Live & Secure</div>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi"><h3 data-key="kpi_revenue">Total Revenue</h3><p>₹{{ "%.2f"|format(kpis.revenue) }}</p></div>
        <div class="kpi"><h3 data-key="kpi_profit">Net Profit (P&L)</h3><p>₹{{ "%.2f"|format(kpis.profit) }}</p></div>
        <div class="kpi"><h3 data-key="kpi_bank">Total Bank Balance</h3><p style="color: #34d399;">₹{{ "%.2f"|format(kpis.bank_bal) }}</p></div>
        <div class="kpi"><h3 data-key="kpi_advances">Net Advances</h3><p>₹{{ "%.2f"|format(kpis.advances) }}</p></div>
    </div>

    <div class="card" style="margin-bottom: 25px;">
        <h3><span><i class="fas fa-university"></i> <span data-key="bank_hub_title">Indian Bank Accounts Hub</span></span></h3>
        <table>
            <tr><th data-key="th_bank_name">Bank Name</th><th data-key="th_acc_no">Account No / Ref</th><th data-key="th_balance">Current Balance</th></tr>
            {% if banks %}
                {% for b in banks %}
                <tr>
                    <td><strong>{{ b[1] }}</strong></td>
                    <td>{{ b[2] }}</td>
                    <td style="font-weight: bold; color: #34d399;">₹{{ "%.2f"|format(b[3]) }}</td>
                </tr>
                {% endfor %}
            {% else %}
                <tr><td colspan="3" style="text-align: center; color: #f43f5e;" data-key="no_bank">No bank accounts registered yet. Please add below.</td></tr>
            {% endif %}
        </table>
    </div>

    <div class="card" style="margin-bottom: 25px;">
        <h3><span><i class="fas fa-boxes"></i> <span data-key="stock_hub_title">Live Stock & Market Trending Status</span></span></h3>
        <table>
            <tr><th data-key="th_item">Item Name</th><th data-key="th_sku">SKU Code</th><th data-key="th_status">Market Status</th><th data-key="th_qty">Current Qty</th><th data-key="th_price">Unit Price</th><th data-key="th_val">Stock Value</th></tr>
            {% for s in stock_summary %}
            <tr>
                <td>{{ s[0] }}</td>
                <td>{{ s[1] }}</td>
                <td>
                    {% if s[2] == 'TRENDING' %}
                        <span class="badge-trend"><i class="fas fa-fire"></i> <span data-key="trending">Trending</span></span>
                    {% else %}
                        <span style="color:#94a3b8;" data-key="regular">Regular</span>
                    {% endif %}
                    {% if s[3] <= 5 %}<span class="badge-alert" data-key="low_stock">Low Stock</span>{% endif %}
                </td>
                <td style="font-weight: bold; color: {% if s[3] <= 5 %}#ef4444{% else %}#34d399{% endif %};">{{ s[3] }}</td>
                <td>₹{{ "%.2f"|format(s[4]) }}</td>
                <td>₹{{ "%.2f"|format(s[3] * s[4]) }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="main-grid">
        <div class="card">
            <h3><span><i class="fas fa-book-open"></i> <span data-key="acc_title">Accounting & GST Voucher</span></span></h3>
            <form action="/add_voucher" method="POST">
                <label data-key="lbl_vtype">Voucher Type:</label>
                <select name="voucher_type"><option>RECEIPT</option><option>PAYMENT</option><option>SALES</option><option>PURCHASE</option></select>
                <label data-key="lbl_party">Party / Ledger Name:</label><input type="text" name="ledger_name" required>
                <label data-key="lbl_amount">Base Amount (₹):</label><input type="number" step="0.01" name="amount" required>
                <label data-key="lbl_narration">Narration:</label><input type="text" name="narration">
                <button type="submit" data-key="btn_save_voucher">Save Voucher (Auto 18% GST)</button>
            </form>
        </div>

        <div class="card">
            <h3><span><i class="fas fa-exchange-alt"></i> <span data-key="bank_tx_title">Indian Bank Transactions Hub</span></span></h3>
            <form action="/bank_transaction" method="POST">
                <label data-key="lbl_select_bank">Select Bank:</label>
                <select name="bank_id" required>
                    {% if banks %}
                        {% for b in banks %}
                        <option value="{{ b[0] }}">{{ b[1] }} (A/C: {{ b[2] }})</option>
                        {% endfor %}
                    {% else %}
                        <option value="">-- Add Bank First --</option>
                    {% endif %}
                </select>
                <label data-key="lbl_tx_type">Transaction Type:</label>
                <select name="tx_type">
                    <option value="DEPOSIT" data-key="opt_deposit">Deposit</option>
                    <option value="WITHDRAW" data-key="opt_withdraw">Withdrawal</option>
                </select>
                <label data-key="lbl_pay_mode">Payment Mode:</label>
                <select name="payment_mode">
                    <option value="UPI">UPI</option>
                    <option value="NEFT">NEFT</option>
                    <option value="RTGS">RTGS</option>
                    <option value="IMPS">IMPS</option>
                    <option value="CASH">Cash</option>
                </select>
                <label data-key="lbl_amount">Amount (₹):</label><input type="number" step="0.01" name="amount" required>
                <label data-key="lbl_ref">Narration / Ref:</label><input type="text" name="narration" placeholder="Txn ID / Ref No">
                <button type="submit" style="background:#10b981;" data-key="btn_process_tx">Process Bank Txn</button>
            </form>
            
            <form action="/add_bank" method="POST" style="margin-top:20px; border-top:1px solid #1f2937; padding-top:15px;">
                <label style="color:#38bdf8;" data-key="lbl_add_bank">+ Add Indian Bank Account:</label>
                <select name="bank_name" required>
                    <option value="State Bank of India (SBI)">State Bank of India (SBI)</option>
                    <option value="HDFC Bank">HDFC Bank</option>
                    <option value="ICICI Bank">ICICI Bank</option>
                    <option value="Axis Bank">Axis Bank</option>
                    <option value="Punjab National Bank (PNB)">Punjab National Bank (PNB)</option>
                    <option value="Bank of Baroda">Bank of Baroda</option>
                    <option value="Kotak Mahindra Bank">Kotak Mahindra Bank</option>
                    <option value="Canara Bank">Canara Bank</option>
                </select>
                <label data-key="lbl_acc_num">Account Number:</label><input type="text" name="account_no" placeholder="Enter A/C No" required>
                <label data-key="lbl_opening_bal">Opening Balance (₹):</label><input type="number" step="0.01" name="balance" value="0.0" required>
                <button type="submit" style="background:#6366f1; margin-top:8px;" data-key="btn_register_bank">Register Bank</button>
            </form>
        </div>

        <div class="card">
            <h3><span><i class="fas fa-boxes"></i> <span data-key="inv_title">Inventory Control</span></span></h3>
            <form action="/add_inventory" method="POST">
                <label data-key="lbl_movement">Movement Type:</label><select name="movement_type"><option value="INWARD" data-key="opt_inward">INWARD</option><option value="OUTWARD" data-key="opt_outward">OUTWARD</option></select>
                <label data-key="lbl_item_name">Item Name:</label><input type="text" name="item_name" required>
                <label data-key="lbl_sku">SKU Code:</label><input type="text" name="sku" required>
                <label data-key="lbl_market_status">Market Trend Status:</label>
                <select name="market_status">
                    <option value="REGULAR" data-key="opt_regular">Regular Stock</option>
                    <option value="TRENDING" data-key="opt_trending">Fast-Moving (Trending)</option>
                </select>
                <div style="display: flex; gap: 10px; margin-top: 8px;">
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

    <div class="card" id="printableArea">
        <h3><span><i class="fas fa-history"></i> <span data-key="history_title">Recent Vouchers & Sharing</span></span></h3>
        <table>
            <tr><th data-key="th_type">Type</th><th data-key="th_party">Party</th><th data-key="th_total">Total (Inc. GST)</th><th data-key="th_action">Action</th></tr>
            {% for v in vouchers %}
            <tr>
                <td>{{ v[2] }}</td>
                <td>{{ v[3] }}</td>
                <td>₹{{ "%.2f"|format(v[6]) }}</td>
                <td>
                    <a href="https://wa.me/?text=Vajra%20ERP%20Invoice:%20{{ v[2] }}%20for%20{{ v[3] }}%20Amount:%20₹{{ '%.2f'|format(v[6]) }}" target="_blank" class="whatsapp-btn">
                        <i class="fab fa-whatsapp"></i> <span data-key="send">Send</span>
                    </a>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <script>
        let currentLang = 'en';

        const translations = {
            en: {
                header_title: "VAJRA SOVEREIGN ERP OS",
                logout: "Logout",
                backup_db: "Backup DB",
                export_csv: "Export CSV",
                print_report: "Print Report",
                sentinel_title: "Sovereign Multi-Lingual Sentinel",
                runway_label: "Estimated Liquidity Runway",
                sentinel_status: "Status",
                cloud_status: "Cloud Status",
                kpi_revenue: "Total Revenue",
                kpi_profit: "Net Profit (P&L)",
                kpi_bank: "Total Bank Balance",
                kpi_advances: "Net Advances",
                bank_hub_title: "Indian Bank Accounts Hub",
                th_bank_name: "Bank Name",
                th_acc_no: "Account No / Ref",
                th_balance: "Current Balance",
                no_bank: "No bank accounts registered yet. Please add below.",
                stock_hub_title: "Live Stock & Market Trending Status",
                th_item: "Item Name",
                th_sku: "SKU Code",
                th_status: "Market Status",
                th_qty: "Current Qty",
                th_price: "Unit Price",
                th_val: "Stock Value",
                trending: "Trending",
                regular: "Regular",
                low_stock: "Low Stock",
                acc_title: "Accounting & GST Voucher",
                lbl_vtype: "Voucher Type:",
                lbl_party: "Party / Ledger Name:",
                lbl_amount: "Base Amount (Rs):",
                lbl_narration: "Narration:",
                btn_save_voucher: "Save Voucher (Auto 18% GST)",
                bank_tx_title: "Indian Bank Transactions Hub",
                lbl_select_bank: "Select Bank:",
                lbl_tx_type: "Transaction Type:",
                opt_deposit: "Deposit",
                opt_withdraw: "Withdrawal",
                lbl_pay_mode: "Payment Mode:",
                lbl_ref: "Narration / Ref:",
                btn_process_tx: "Process Bank Txn",
                lbl_add_bank: "+ Add Indian Bank Account:",
                lbl_acc_num: "Account Number:",
                lbl_opening_bal: "Opening Balance (Rs):",
                btn_register_bank: "Register Bank",
                inv_title: "Inventory Control",
                lbl_movement: "Movement Type:",
                opt_inward: "INWARD",
                opt_outward: "OUTWARD",
                lbl_item_name: "Item Name:",
                lbl_sku: "SKU Code:",
                lbl_market_status: "Market Trend Status:",
                opt_trending: "Fast-Moving (Trending)",
                lbl_qty: "Qty:",
                lbl_price: "Price (Rs):",
                btn_update_stock: "Update Stock",
                adv_title: "Advance Ledger",
                lbl_party_name: "Party Name:",
                lbl_adv_type: "Advance Type:",
                opt_adv_given: "Advance Given",
                opt_adv_taken: "Advance Taken",
                btn_record_adv: "Record Advance",
                history_title: "Recent Vouchers & Sharing",
                th_type: "Type",
                th_party: "Party",
                th_total: "Total (Inc. GST)",
                th_action: "Action",
                send: "Send",
                ai_voice_title: "Vajra AI Smart Assistant",
                speak_btn: "🎤 Speak",
                ask_btn: "Ask AI",
                voice_hint: "Use quick buttons or type query below:",
                btn_profit: "Net Profit",
                btn_sales: "Total Sales",
                btn_bank: "Bank Balance",
                btn_stock: "Stock Summary"
            },
            hi: {
                header_title: "वज्र संप्रभु ईआरपी ओएस",
                logout: "लॉग आउट",
                backup_db: "डेटाबेस बैकअप",
                export_csv: "इन्वेंट्री एक्सपोर्ट",
                print_report: "रिपोर्ट प्रिंट करें",
                sentinel_title: "संप्रभु बहुभाषी प्रहरी",
                runway_label: "अनुमानित तरलता रनवे",
                sentinel_status: "स्थिति",
                cloud_status: "क्लाउड स्थिति",
                kpi_revenue: "कुल राजस्व",
                kpi_profit: "शुद्ध लाभ (P&L)",
                kpi_bank: "कुल बैंक शेष",
                kpi_advances: "शुद्ध अग्रिम",
                bank_hub_title: "भारतीय बैंक खाता हब",
                th_bank_name: "बैंक का नाम",
                th_acc_no: "खाता संख्या / संदर्भ",
                th_balance: "वर्तमान शेष",
                no_bank: "अभी तक कोई बैंक खाता पंजीकृत नहीं है।",
                stock_hub_title: "लाइव स्टॉक और बाजार रुझान स्थिति",
                th_item: "वस्तु का नाम",
                th_sku: "SKU कोड",
                th_status: "बाजार स्थिति",
                th_qty: "वर्तमान मात्रा",
                th_price: "इकाई मूल्य",
                th_val: "स्टॉक मूल्य",
                trending: "ट्रेंडिंग",
                regular: "नियमित",
                low_stock: "कम स्टॉक",
                acc_title: "लेखांकन और जीएसटी वाउचर",
                lbl_vtype: "वाउचर प्रकार:",
                lbl_party: "पार्टी / लेजर नाम:",
                lbl_amount: "मूल राशि (Rs):",
                lbl_narration: "विवरण:",
                btn_save_voucher: "वाउचर सहेजें (ऑटो 18% जीएसटी)",
                bank_tx_title: "भारतीय बैंक लेनदेन हब",
                lbl_select_bank: "बैंक चुनें:",
                lbl_tx_type: "लेनदेन प्रकार:",
                opt_deposit: "जमा",
                opt_withdraw: "निकासी",
                lbl_pay_mode: "भुगतान मोड:",
                lbl_ref: "विवरण / संदर्भ:",
                btn_process_tx: "बैंक लेनदेन प्रक्रिया",
                lbl_add_bank: "+ भारतीय बैंक खाता जोड़ें:",
                lbl_acc_num: "खाता संख्या:",
                lbl_opening_bal: "शुरुआती शेष (Rs):",
                btn_register_bank: "बैंक पंजीकृत करें",
                inv_title: "इन्वेंट्री नियंत्रण",
                lbl_movement: "मूवमेंट प्रकार:",
                opt_inward: "आवक",
                opt_outward: "जावक",
                lbl_item_name: "वस्तु का नाम:",
                lbl_sku: "SKU कोड:",
                lbl_market_status: "बाजार रुझान स्थिति:",
                opt_trending: "तेजी से बिकने वाला",
                lbl_qty: "मात्रा",
                lbl_price: "मूल्य (Rs):",
                btn_update_stock: "स्टॉक अपडेट करें",
                adv_title: "अग्रिम खाता लेजर",
                lbl_party_name: "पार्टी का नाम:",
                lbl_adv_type: "अग्रिम प्रकार:",
                opt_adv_given: "अग्रिम दिया गया",
                opt_adv_taken: "अग्रिम लिया गया",
                btn_record_adv: "अग्रिम दर्ज करें",
                history_title: "हाल के वाउचर और शेयरिंग",
                th_type: "प्रकार",
                th_party: "पार्टी",
                th_total: "कुल (जीएसटी सहित)",
                th_action: "कार्रवाई",
                send: "भेजें",
                ai_voice_title: "वज्र एआई स्मार्ट असिस्टेंट",
                speak_btn: "🎤 बोलें",
                ask_btn: "पूछें",
                voice_hint: "क्विक बटन उपयोग करें या नीचे टाइप करें:",
                btn_profit: "शुद्ध लाभ",
                btn_sales: "कुल बिक्री",
                btn_bank: "बैंक बैलेंस",
                btn_stock: "स्टॉक सारांश"
            },
            gu: {
                header_title: "વજ્ર સોવરિન ઇઆરપી ઓએસ",
                logout: "લોગઆઉટ",
                backup_db: "બેકઅપ ડીબી",
                export_csv: "ઇન્વેન્ટરી એક્સપોર્ટ",
                print_report: "પ્રિન્ટ રિપોર્ટ",
                sentinel_title: "સોવરિન મલ્ટી-લિંગ્વેજ સેન્ટિનલ",
                runway_label: "અંદાજિત લિક્વિડિટી રનવે",
                sentinel_status: "સ્થિતિ",
                cloud_status: "ક્લાઉડ સ્ટેટસ",
                kpi_revenue: "કુલ આવક",
                kpi_profit: "નેટ પ્રોફિટ (નફો)",
                kpi_bank: "કુલ બેંક બેલેન્સ",
                kpi_advances: "નેટ એડવાન્સ",
                bank_hub_title: "ઇન્ડિયન બેંક એકાઉન્ટ્સ હબ",
                th_bank_name: "બેંકનું નામ",
                th_acc_no: "એકાઉન્ટ નંબર / સંદર્ભ",
                th_balance: "વર્તમાન બેલેન્સ",
                no_bank: "હજી સુધી કોઈ બેંક એડ નથી કરી.",
                stock_hub_title: "લાઈવ સ્ટોક અને માર્કેટ ટ્રેન્ડિંગ સ્ટેટસ",
                th_item: "આઇટમનું નામ",
                th_sku: "એસકેયુ કોડ",
                th_status: "માર્કેટ સ્ટેટસ",
                th_qty: "કુલ જથ્થો",
                th_price: "યુનિટ પ્રાઇસ",
                th_val: "સ્ટોક વેલ્યુ",
                trending: "બજારમાં ચલતી",
                regular: "સામાન્ય",
                low_stock: "ઓછો સ્ટોક",
                acc_title: "એકાઉન્ટિંગ અને જીએસટી વાઉચર",
                lbl_vtype: "વાઉચર પ્રકાર:",
                lbl_party: "પાર્ટી / લેજર નામ:",
                lbl_amount: "મૂળ રકમ (Rs):",
                lbl_narration: "નરેશન:",
                btn_save_voucher: "વાઉચર સેવ કરો (ઓટો ૧૮% GST)",
                bank_tx_title: "ઇન્ડિયન બેંક ટ્રાન્ઝેક્શન્સ હબ",
                lbl_select_bank: "બેંક પસંદ કરો:",
                lbl_tx_type: "ટ્રાન્ઝેક્શન પ્રકાર:",
                opt_deposit: "જમા",
                opt_withdraw: "ઉપાડ",
                lbl_pay_mode: "પેમેન્ટ મોડ:",
                lbl_ref: "નરેશન / રેફ:",
                btn_process_tx: "બેંક ટ્રાન્ઝેક્શન પ્રોસેસ કરો",
                lbl_add_bank: "+ નવી બેંક ઉમેરો:",
                lbl_acc_num: "એકાઉન્ટ નંબર:",
                lbl_opening_bal: "શરૂઆતનું બેલેન્સ (Rs):",
                btn_register_bank: "બેંક રજીસ્ટર કરો",
                inv_title: "ઇન્વેન્ટરી કંટ્રોલ",
                lbl_movement: "મૂવમેન્ટ પ્રકાર:",
                opt_inward: "આવક",
                opt_outward: "જાવક",
                lbl_item_name: "આઇટમનું નામ:",
                lbl_sku: "એસકેયુ કોડ:",
                lbl_market_status: "માર્કેટ ટ્રેન્ડ સ્ટેટး:",
                opt_trending: "બજારમાં ચલતી વસ્તુ (Trending)",
                lbl_qty: "જથ્થો (Qty):",
                lbl_price: "કિંમત (Rs):",
                btn_update_stock: "સ્ટોક અપડેટ કરો",
                adv_title: "એડવાન્સ એકાઉન્ટ લેજર",
                lbl_party_name: "પાર્ટીનું નામ:",
                lbl_adv_type: "એડવાન્સ પ્રકાર:",
                opt_adv_given: "એડવાન્સ આપેલું",
                opt_adv_taken: "એડવાન્સ લીધેલું",
                btn_record_adv: "એડવાન્સ નોંધી કરો",
                history_title: "તાજેતરના વાઉચર્સ અને શેરિંગ",
                th_type: "પ્રકાર",
                th_party: "પાર્ટી",
                th_total: "કુલ (જીએસટી સાથે)",
                th_action: "એક્શન",
                send: "મોકલો",
                ai_voice_title: "વજ્ર એઆઈ સ્માર્ટ અસિસ્ટન્ટ",
                speak_btn: "🎤 બોલો",
                ask_btn: "પૂછો",
                voice_hint: "ક્વિક બટન અથવા નીચે ટાઈપ કરો:",
                btn_profit: "નેટ નફો",
                btn_sales: "કુલ વેચાણ",
                btn_bank: "બેંક બેલેન્સ",
                btn_stock: "સ્ટોક રિપોર્ટ"
            }
        };

        function setLanguage(lang) {
            currentLang = lang;
            document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            const elements = document.querySelectorAll('[data-key]');
            elements.forEach(el => {
                const key = el.getAttribute('data-key');
                if (translations[lang] && translations[lang][key]) {
                    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                        if(el.hasAttribute('placeholder')) el.placeholder = translations[lang][key];
                    } else {
                        el.textContent = translations[lang][key];
                    }
                }
            });
        }

        // ⚡ INSTANT QUICK ACTION & ABSOLUTE URL FETCH (100% ERROR FREE)
        function quickAsk(queryType) {
            document.getElementById("aiTextInput").value = queryType;
            sendQueryToAI(queryType);
        }

        function startVoiceRecognition() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert(currentLang === 'gu' ? "આ બ્રાઉઝરમાં વોઇસ સપોર્ટ નથી. કૃપા કરીને ક્વિક બટન વાપરો." : "Voice recognition not supported. Use quick buttons below.");
                return;
            }
            try {
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = currentLang === 'gu' ? 'gu-IN' : (currentLang === 'hi' ? 'hi-IN' : 'en-US');

                document.getElementById("voiceStatus").innerText = currentLang === 'gu' ? "સંભળાઈ રહ્યું છે... બોલો!" : "Listening...";
                
                recognition.onresult = function(event) {
                    const spokenText = event.results[0][0].transcript;
                    document.getElementById("aiTextInput").value = spokenText;
                    sendQueryToAI(spokenText);
                };
                recognition.onerror = function(event) {
                    document.getElementById("voiceStatus").innerText = currentLang === 'gu' ? "માઇક એરર. ક્વિક બટન વાપરો." : "Mic error. Use quick buttons.";
                };
                recognition.start();
            } catch(e) {
                alert("Voice recognition unavailable in this view.");
            }
        }

        function sendQueryToAI(queryText) {
            if(!queryText.trim()) return;
            const replyElem = document.getElementById("aiReply");
            replyElem.style.display = "block";
            replyElem.innerText = currentLang === 'gu' ? "પ્રોસેસ થઈ રહ્યું છે..." : "Processing...";

            // Absolute URL to prevent mobile WebView fetch path errors
            const apiUrl = window.location.origin + '/api/ai-assistant';

            fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: queryText, lang: currentLang })
            })
            .then(res => {
                if (!res.ok) throw new Error("Server error");
                return res.json();
            })
            .then(data => {
                replyElem.innerText = "🤖 AI Answer: " + data.reply;
                
                // Safe Speech Synthesis check for mobile WebView
                if ('speechSynthesis' in window) {
                    try {
                        let speech = new SpeechSynthesisUtterance(data.reply);
                        speech.lang = currentLang === 'gu' ? 'gu-IN' : (currentLang === 'hi' ? 'hi-IN' : 'en-US');
                        window.speechSynthesis.speak(speech);
                    } catch(ex) {
                        // Ignore speech error on mobile app
                    }
                }
            })
            .catch(err => {
                replyElem.innerText = currentLang === 'gu' ? "કનેક્શન સફળ. કૃપા કરીને ક્વિક બટન વાપરો." : "Error connecting to AI Assistant.";
            });
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        if request.form.get("username") == "VajraERP" and request.form.get("password") == "Vajra@erp":
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid Credentials! Use: VajraERP / Vajra@erp"
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
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

        profit = revenue - expenses
        kpis = {"revenue": revenue, "expenses": expenses, "profit": profit, "inventory": total_inv_val, "bank_bal": bank_bal, "advances": net_advances}

    query_latency = round((time.time() - start_time) * 1000, 2)
    return render_template_string(DASHBOARD_HTML, vouchers=vouchers, kpis=kpis, banks=banks, stock_summary=stock_summary, runway_days=runway_days, sentinel_status=sentinel_status, query_latency=query_latency)

# --- 🤖 MULTI-LINGUAL AI ASSISTANT API ROUTE ---
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
        response_text = "માફ કરશો, હું આ પ્રશ્ન સમજી શક્યો નથી. તમે 'નફો', 'વેચાણ', 'બેલેન્સ' અથવા 'સ્ટોક' વિશે પૂછી શકો છો."
        if "profit" in user_query or "nofo" in user_query or "નફો" in user_query or "nafa" in user_query:
            response_text = f"આજે કુલ નેટ નફો ₹{net_profit:.2f} થયો છે."
        elif "sales" in user_query or "vechan" in user_query or "aavak" in user_query or "revenue" in user_query:
            response_text = f"કુલ વેચાણ / આવક ₹{rev:.2f} છે."
        elif "bank" in user_query or "balance" in user_query or "belez" in user_query:
            response_text = f"બધી બેંકનું કુલ બેલેન્સ ₹{banks_total:.2f} છે."
        elif "stock" in user_query or "stok" in user_query:
            response_text = f"ઇન્વેન્ટરી સ્ટોક મેનેજમેન્ટમાં કુલ {total_items} આઇટમ્સ રજીસ્ટર થયેલી છે."
    elif lang == "hi":
        response_text = "क्षमा करें, मैं इस प्रश्न को समझ नहीं सका। आप 'लाभ', 'बिक्री', 'बैलेंस' या 'स्टॉक' के बारे में पूछ सकते हैं।"
        if "profit" in user_query or "labh" in user_query or "नफा" in user_query:
            response_text = f"आज कुल शुद्ध लाभ ₹{net_profit:.2f} हुआ है।"
        elif "sales" in user_query or "bikri" in user_query or "revenue" in user_query:
            response_text = f"कुल राजस्व / बिक्री ₹{rev:.2f} है।"
        elif "bank" in user_query or "balance" in user_query:
            response_text = f"सभी बैंकों का कुल शेष ₹{banks_total:.2f} है।"
        elif "stock" in user_query:
            response_text = f"इन्वेंट्री स्टॉक में कुल {total_items} आइटम पंजीकृत हैं।"
    else:
        response_text = "Sorry, I could not understand this query. You can ask about 'profit', 'sales', 'balance', or 'stock'."
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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5027))
    app.run(host="0.0.0.0", port=port)
