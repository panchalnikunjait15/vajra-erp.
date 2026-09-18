# -*- coding: utf-8 -*-
import os
import sqlite3
import hashlib
import time
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, Response, send_file
import threading
import csv
import io

app = Flask(__name__)
app.secret_key = "VAJRA_ULTIMATE_SAFE_2026"

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

LOGIN_HTML = r"""
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

DASHBOARD_HTML = r"""
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
            <button class="lang-btn" onclick="setLanguage('hi')">&#2361;&#2368;&#2344;&#2368;</button>
            <button class="lang-btn" onclick="setLanguage('gu')">&#2a9;&#307;&#2ac1;&#2af3;&#2ab0;&#2abe;&#2aa4;&#2ac1;</button>
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
        <div class="kpi"><h3 data-key="kpi_revenue">Total Revenue</h3><p>&#8377;{{ "%.2f"|format(kpis.revenue) }}</p></div>
        <div class="kpi"><h3 data-key="kpi_profit">Net Profit (P&L)</h3><p>&#8377;{{ "%.2f"|format(kpis.profit) }}</p></div>
        <div class="kpi"><h3 data-key="kpi_bank">Total Bank Balance</h3><p style="color: #34d399;">&#8377;{{ "%.2f"|format(kpis.bank_bal) }}</p></div>
        <div class="kpi"><h3 data-key="kpi_advances">Net Advances</h3><p>&#8377;{{ "%.2f"|format(kpis.advances) }}</p></div>
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
                    <td style="font-weight: bold; color: #34d399;">&#8377;{{ "%.2f"|format(b[3]) }}</td>
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
                <td>&#8377;{{ "%.2f"|format(s[4]) }}</td>
                <td>&#8377;{{ "%.2f"|format(s[3] * s[4]) }}</td>
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
                <label data-key="lbl_amount">Base Amount (&#8377;):</label><input type="number" step="0.01" name="amount" required>
                <label data-key="lbl_narration">Narration:</label><input type="text" name="narration">
                <button type="submit" data-key="btn_save_voucher">&#9889; Save Voucher (Auto 18% GST)</button>
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
                <label data-key="lbl_amount">Amount (&#8377;):</label><input type="number" step="0.01" name="amount" required>
                <label data-key="lbl_ref">Narration / Ref:</label><input type="text" name="narration" placeholder="Txn ID / Ref No">
                <button type="submit" style="background:#10b981;" data-key="btn_process_tx">&#127976; Process Bank Txn</button>
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
                <label data-key="lbl_opening_bal">Opening Balance (&#8377;):</label><input type="number" step="0.01" name="balance" value="0.0" required>
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
                    <option value="TRENDING" data-key="opt_trending">&#128293; Fast-Moving (Trending)</option>
                </select>
                <div style="display: flex; gap: 10px; margin-top: 8px;">
                    <div style="flex:1;"><label data-key="lbl_qty">Qty:</label><input type="number" name="qty" required></div>
                    <div style="flex:1;"><label data-key="lbl_price">Price (&#8377;):</label><input type="number" step="0.01" name="price" required></div>
                </div>
                <button type="submit" data-key="btn_update_stock">&#128640; Update Stock</button>
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
                <label data-key="lbl_amount">Amount (&#8377;):</label><input type="number" step="0.01" name="amount" required>
                <button type="submit" style="background:#8b5cf6;" data-key="btn_record_adv">&#129309; Record Advance</button>
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
                <td>&#8377;{{ "%.2f"|format(v[6]) }}</td>
                <td>
                    <a href="https://wa.me/?text=Vajra%20ERP%20Invoice:%20{{ v[2] }}%20for%20{{ v[3] }}%20Amount:%20&#8377;{{ '%.2f'|format(v[6]) }}" target="_blank" class="whatsapp-btn">
                        <i class="fab fa-whatsapp"></i> <span data-key="send">Send</span>
                    </a>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <script>
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
                lbl_amount: "Base Amount (\u20b9):",
                lbl_narration: "Narration:",
                btn_save_voucher: "\u26a1 Save Voucher (Auto 18% GST)",
                bank_tx_title: "Indian Bank Transactions Hub",
                lbl_select_bank: "Select Bank:",
                lbl_tx_type: "Transaction Type:",
                opt_deposit: "Deposit",
                opt_withdraw: "Withdrawal",
                lbl_pay_mode: "Payment Mode:",
                lbl_ref: "Narration / Ref:",
                btn_process_tx: "\U0001f3e6 Process Bank Txn",
                lbl_add_bank: "+ Add Indian Bank Account:",
                lbl_acc_num: "Account Number:",
                lbl_opening_bal: "Opening Balance (\u20b9):",
                btn_register_bank: "Register Bank",
                inv_title: "Inventory Control",
                lbl_movement: "Movement Type:",
                opt_inward: "INWARD",
                opt_outward: "OUTWARD",
                lbl_item_name: "Item Name:",
                lbl_sku: "SKU Code:",
                lbl_market_status: "Market Trend Status:",
                opt_trending: "\U0001f525 Fast-Moving (Trending)",
                lbl_qty: "Qty:",
                lbl_price: "Price (\u20b9):",
                btn_update_stock: "\U0001f680 Update Stock",
                adv_title: "Advance Ledger",
                lbl_party_name: "Party Name:",
                lbl_adv_type: "Advance Type:",
                opt_adv_given: "Advance Given",
                opt_adv_taken: "Advance Taken",
                btn_record_adv: "\U0001f91d Record Advance",
                history_title: "Recent Vouchers & Sharing",
                th_type: "Type",
                th_party: "Party",
                th_total: "Total (Inc. GST)",
                th_action: "Action",
                send: "Send"
            },
            hi: {
                header_title: "\u0935\u091c\u094d\u0930 \u0938\u092e\u094d\u092a\u094d\u092f\u0941 \u0908\u0906\u0930\u092a\u0940 \u0913\u090f\u0938",
                logout: "\u0932\u0949\u0917 \u0906\u0909\u091f",
                backup_db: "\u0921\u0947\u091f\u093e\u092c\u0947\u0938 \u092c\u0948\u0915\u0905\u092a",
                export_csv: "\u0907\u0928\u094d\u0935\u0947\u0928\u094d\u0930\u094d\u0920\u0940 \u090f\u0915\u094d\u0938\u092a\u094b\u0930\u094d\u091f",
                print_report: "\u0930\u093f\u092a\u094b\u0930\u094d\u091f \u092a\u094d\u0930\u093f\u0902\u091f \u0915\u0930\u0947\u0902",
                sentinel_title: "\u0938\u092e\u094d\u092a\u094d\u0930\u092d\u0941 \u092c\u0939\u0941\u092d\u093e\u0937\u0940 \u092a\u094d\u0930\u0939\u0930\u0940",
                runway_label: "\u0905\u0928\u0941\u092e\u093e\u0928\u093f\u0924 \u0924\u0930\u0932\u0924\u093e \u0930\u0928\u0935\u0947",
                sentinel_status: "\u0938\u094d\u0925\u093f\u0924\u093f",
                cloud_status: "\u0915\u094d\u0932\u093e\u0909\u0921 \u0938\u094d\u0925\u093f\u0924\u093f",
                kpi_revenue: "\u0915\u0941\u0932 \u0930\u093e\u091c\u0938\u094d\u0935",
                kpi_profit: "\u0936\u0941\u0926\u094d\u0927 \u0932\u093e\u092d (P&L)",
                kpi_bank: "\u0915\u0941\u0932 \u092c\u0948\u0902\u0915 \u0936\u0947\u0937",
                kpi_advances: "\u0936\u0941\u0926\u094d\u0927 \u0905\u0917\u094d\u0930\u093f\u092e",
                bank_hub_title: "\u092d\u093e\u0930\u0924\u0940\u092f \u092c\u0948\u0902\u0915 \u0916\u093e\u0924\u093e \u0939\u092c",
                th_bank_name: "\u092c\u0948\u0902\u0915 \u0915\u093e \u0928\u093e\u092e",
                th_acc_no: "\u0916\u093e\u0924\u093e \u0938\u0902\u0916\u094d\u092f\u093e / \u0938\u0902\u0926\u0930\u094d\u092d",
                th_balance: "\u0935\u0930\u094d\u0924\u092e\u093e\u0928 \u0936\u0947\u0937",
                no_bank: "\u0905\u092d\u0940 \u0924\u0915 \u0915\u094b\u0908 \u092c\u0948\u0902\u0915 \u0916\u093e\u0924\u093e \u092a\u0902\u091c\u0940\u0915\u0943\u0924 \u0928\u0939\u0940\u0902 \u0939\u0948\u0964",
                stock_hub_title: "\u0932\u093e\u0907\u0935 \u0938\u094d\u091f\u0949\u0915 \u0914\u0930 \u092c\u093e\u091c\u093e\u0930 \u0930\u0941\u091d\u093e\u0928 \u0938\u094d\u0925\u093f\u0924\u093f",
                th_item: "\u0935\u0938\u094d\u0924\u0941 \u0915\u093e \u0928\u093e\u092e",
                th_sku: "SKU \u0915\u094b\u0921",
                th_status: "\u092c\u093e\u091c\u093e\u0930 \u0938\u094d\u0925\u093f\u0924\u093f",
                th_qty: "\u0935\u0930\u094d\u0924\u092e\u093e\u0928 \u092e\u093e\u0924\u094d\u0930\u093e",
                th_price: "\u0907\u0915\u093e\u0908 \u092e\u0942\u0932\u094d\u092f",
                th_val: "\u0938\u094d\u091f\u0949\u0915 \u092e\u0942\u0932\u094d\u092f",
                trending: "\u091f\u094d\u0930\u0947\u0902\u0921\u093f\u0902\u0917",
                regular: "\u0928\u093f\u092f\u092e\u093f\u0924",
                low_stock: "\u0915\u092e \u0938\u094d\u091f\u0949\u0915",
                acc_title: "\u0932\u0947\u0916\u093e\u0902\u0915\u0928 \u0914\u0930 \u091c\u0940\u090f\u0938\u091f\u0940 \u0935\u093e\u0909\u091a\u0930",
                lbl_vtype: "\u0935\u093e\u0909\u091a\u0930 \u092a\u094d\u0930\u0915\u093e\u0930:",
                lbl_party: "\u092a\u093e\u0930\u094d\u091f\u0940 / \u0932\u0947\u091c\u0930 \u0928\u093e\u092e:",
                lbl_amount: "\u092e\u0942\u0932 \u0930\u093e\u0936\u093f (\u20b9):",
                lbl_narration: "\u0935\u093f\u0935\u0930\u0923:",
                btn_save_voucher: "\u26a1 \u0935\u093e\u0909\u091a\u0930 \u0938\u0939\u0947\u091c\u0947\u0902 (\u0911\u091f\u094b 18% \u091c\u0940\u090f\u0938\u091f\u0940)",
                bank_tx_title: "\u092d\u093e\u0930\u0924\u0940\u092f \u092c\u0948\u0902\u0915 \u0932\u0947\u0928\u0926\u0947\u0928 \u0939\u092c",
                lbl_select_bank: "\u092c\u0948\u0902\u0915 \u091a\u0941\u0928\u0947\u0902:",
                lbl_tx_type: "\u0932\u0947\u0928\u0926\u0947\u0928 \u092a\u094d\u0930\u0915\u093e\u0930:",
                opt_deposit: "\u091c\u092e\u093e",
                opt_withdraw: "\u0928\u093f\u0915\u093e\u0938\u0940",
                lbl_pay_mode: "\u092d\u0941\u0917\u0924\u093e\u0928 \u092e\u094b\u0921:",
                lbl_ref: "\u0935\u093f\u0935\u0930\u0923 / \u0938\u0902\u0926\u0930\u094d\u092f:",
                btn_process_tx: "\U0001f3e6 \u092c\u0948\u0902\u0915 \u0932\u0947\u0928\u0926\u0947\u0928 \u092a\u094d\u0930\u0915\u094d\u0930\u093f\u092f\u093e",
                lbl_add_bank: "+ \u092d\u093e\u0930\u0924\u0940\u092f \u092c\u0948\u0902\u0915 \u0916\u093e\u0924\u093e \u091c\u094b\u0921\u093c\u0947\u0902:",
                lbl_acc_num: "\u0916\u093e\u0924\u093e \u0938\u0902\u0916\u094d\u092f\u093e:",
                lbl_opening_bal: "\u0936\u0941\u0930\u0941\u0906\u0924\u0940 \u0936\u0947\u0937 (\u20b9):",
                btn_register_bank: "\u092c\u0948\u0902\u0915 \u092a\u0902\u091c\u0940\u0915\u0943\u0924 \u0915\u0930\u0947\u0902",
                inv_title: "\u0907\u0928\u094d\u0935\u0947\u0928\u094d\u0930\u094d\u0920\u0940 \u0928\u093f\u092f\u0902\u0924\u094d\u0930\u0923",
                lbl_movement: "\u092e\u0942\u0935\u092e\u0947\u0902\u091f \u092a\u094d\u0930\u0915\u093e\u0930:",
                opt_inward: "\u0906\u0935\u0915",
                opt_outward: "\u091c\u093e\u0935\u0915",
                lbl_item_name: "\u0935\u0938\u094d\u0924\u0941 \u0915\u093e \u0928\u093e\u092e:",
                lbl_sku: "SKU \u0915\u094b\u0921:",
                lbl_market_status: "\u092c\u093e\u091c\u093e\u0930 \u0930\u0941\u091d\u093e\u0928 \u0938\u094d\u0925\u093f\u0924\u093f:",
                opt_trending: "\U0001f525 \u0924\u0947\u091c\u0940 \u0938\u0947 \u092c\u093f\u0915\u0928\u0947 \u0935\u093e\u0932\u093e",
                lbl_qty: "\u092e\u093e\u0924\u094d\u0930\u093e",
                lbl_price: "\u092e\u0942\u0932\u094d\u092f (\u20b9):",
                btn_update_stock: "\U0001f680 \u0938\u094d\u091f\u0949\u0915 \u0905\u092a\u0921\u0947\u091f \u0915\u0930\u0947\u0902",
                adv_title: "\u0905\u0917\u094d\u0930\u093f\u092e \u0916\u093e\u0924\u093e \u0932\u0947\u091c\u0930",
                lbl_party_name: "\u092a\u093e\u0930\u094d\u091f\u0940 \u0915\u093e \u0928\u093e\u092e:",
                lbl_adv_type: "\u0905\u0917\u094d\u0930\u093f\u092e \u092a\u094d\u0930\u0915\u093e\u0930:",
                opt_adv_given: "\u0905\u0917\u094d\u0930\u093f\u092e \u0926\u093f\u092f\u093e \u0917\u092f\u093e",
                opt_adv_taken: "\u0905\u0917\u094d\u0930\u093f\u092e \u0932\u093f\u092f\u093e \u0917\u092f\u093e",
                btn_record_adv: "\U0001f91d \u0905\u0917\u094d\u0930\u093f\u092e \u0926\u0930\u094d\u091c \u0915\u0930\u0947\u0902",
                history_title: "\u0939\u093e\u0932 \u0915\u0947 \u0935\u093e\u0909\u091a\u0930 \u0914\u0930 \u0936\u0947\u0930\u093f\u0902\u0917",
                th_type: "\u092a\u094d\u0930\u0915\u093e\u0930",
                th_party: "\u092a\u093e\u0930\u094d\u091f\u0940",
                th_total: "\u0915\u0941\u0932 (\u091c\u0940\u090f\u0938\u091f\u0940 \u0938\u0939\u093f\u0924)",
                th_action: "\u0915\u093e\u0930\u094d\u0930\u0935\u093e\u0908",
                send: "\u092d\u0947\u091c\u0947\u0902"
            },
            gu: {
                header_title: "\u0ab5\u0a9c\u0acd\u0ab0 \u0ab8\u0acb\u0ab5\u0ab0\u0abf\u0aa8 \u0a87\u0abe\u0ab0\u0aaa\u0ac0 \u0a93\u0a8f\u0ab8",
                logout: "\u0ab2\u0acb\u0a97\u0abe\u0a89\u0a9f",
                backup_db: "\u0aac\u0ac7\u0a95\u0a85\u0aaa \u0aa1\u0ac0\u0aac\u0ac0",
                export_csv: "\u0abf\u0a87\u0aa8\u0acd\u0ab5\u0ac7\u0aa8\u0acd\u0a9f\u0ab0\u0ac0 \u0a8f\u0a95\u0acd\u0ab8\u0aaa\u0acb\u0ab0\u0acd\u0a9f",
                print_report: "\u0aaa\u0acd\u0ab0\u0abf\u0aa8\u0acd\u0a9f \u0ab0\u0abf\u0aaa\u0acb\u0ab0\u0acd\u0a9f",
                sentinel_title: "\u0ab8\u0acb\u0ab5\u0ab0\u0abf\u0aa8 \u0aae\u0ab2\u0acd\u0a9f\u0ac0-\u0ab2\u0abf\u0a82\u0a97\u0acd\u0ab5\u0ac7\u0a9c \u0ab8\u0ac7\u0aa8\u0acd\u0a9f\u0abf\u0aa8\u0ab2",
                runway_label: "\u0a85\u0a82\u0aa6\u0abe\u0a9c\u0abf\u0aa4 \u0ab2\u0abf\u0a95\u0acd\u0ab5\u0abf\u0aa1\u0abf\u0a9f\u0ac0 \u0ab0\u0aa8\u0ab5\u0ac7",
                sentinel_status: "\u0ab8\u0acd\u0aa5\u0abf\u0aa4\u0abf",
                cloud_status: "\u0a95\u0acd\u0ab2\u0abe\u0a8a\u0aa1 \u0ab8\u0acd\u0a9f\u0ac7\u0a9f\u0ab8",
                kpi_revenue: "\u0a95\u0ac1\u0ab2 \u0a86\u0ab5\u0a95",
                kpi_profit: "\u0aa8\u0ac7\u0a9f \u0aaa\u0acd\u0ab0\u0acb\u0aab\u0abf\u0a9f (\u0aa8\u0aab\u0acb)",
                kpi_bank: "\u0a95\u0ac1\u0ab2 \u0aac\u0ac7\u0a82\u0a95 \u0aac\u0ac7\u0ab2\u0ac7\u0aa8\u0acd\u0ab8",
                kpi_advances: "\u0aa8\u0ac7\u0a9f \u0a8f\u0aa1\u0ab5\u0abe\u0aa8\u0acd\u0ab8",
                bank_hub_title: "\u0a87\u0aa8\u0acd\u0aa1\u0abf\u0aaf\u0aa8 \u0aac\u0ac7\u0a82\u0a95 \u0a8f\u0a95\u0abe\u0a8a\u0aa8\u0acd\u0a9f\u0acd\u0ab8 \u0ab9\u0aac",
                th_bank_name: "\u0aac\u0ac7\u0a82\u0a95\u0aa8\u0ac1\u0a82 \u0aa8\u0abe\u0aae",
                th_acc_no: "\u0a8f\u0a95\u0abe\u0a8a\u0aa8\u0acd\u0a9f \u0aa8\u0a82\u0aac\u0ab0 / \u0ab8\u0a82\u0aa6\u0ab0\u0acd\u0aad",
                th_balance: "\u0ab5\u0ab0\u0acd\u0aa4\u0aae\u0abe\u0aa8 \u0aac\u0ac7\u0ab2\u0ac7\u0aa8\u0acd\u0ab8",
                no_bank: "\u0ab9\u0a9c\u0ac0 \u0ab8\u0ac1\u0aa7\u0ac0 \u0a95\u0acb\u0a88 \u0aac\u0ac7\u0a82\u0a95 \u0a8f\u0aa1 \u0aa8\u0aa5\u0ac0 \u0a95\u0ab0\u0ac0.",
                stock_hub_title: "\u0ab2\u0abe\u0a87\u0ab5 \u0ab8\u0acd\u0a9f\u0acb\u0a95 \u0a85\u0aa8\u0ac7 \u0aae\u0abe\u0ab0\u0acd\u0a95\u0ac7\u0a9f \u0a9f\u0acd\u0ab0\u0ac7\u0a82\u0aa1\u0abf\u0a82\u0a97 \u0ab8\u0acd\u0a9f\u0ac7\u0a9f\u0ab8",
                th_item: "\u0a86\u0a88\u0a9f\u0aae\u0aa8\u0ac1\u0a82 \u0aa8\u0abe\u0aae",
                th_sku: "\u0a8f\u0ab8\u0a95\u0ac7\u0aaf\u0ac1 \u0a95\u0acb\u0aa1",
                th_status: "\u0aae\u0abe\u0ab0\u0acd\u0a95\u0ac7\u0a9f \u0ab8\u0acd\u0a9f\u0ac7\u0a9f\u0ab8",
                th_qty: "\u0a95\u0ac1\u0ab2 \u0a9c\u0aa5\u0acd\u0aa5\u0acb",
                th_price: "\u0aaf\u0ac1\u0aa8\u0abf\u0a9f \u0aaa\u0acd\u0ab0\u0abe\u0a87\u0ab8",
                th_val: "\u0ab8\u0acd\u0a9f\u0acb\u0a95 \u0ab5\u0ac7\u0ab2\u0acd\u0aaf\u0ac1",
                trending: "\u0aac\u0a9c\u0abe\u0ab0\u0aae\u0abe\u0a82 \u0a9a\u0ab2\u0aa4\u0ac0",
                regular: "\u0ab8\u0abe\u0aae\u0abe\u0aa8\u0acd\u0aaf",
                low_stock: "\u0a93\u0a9b\u0acb \u0ab8\u0acd\u0a9f\u0acb\u0a95",
                acc_title: "\u0a8f\u0a95\u0abe\u0a8a\u0aa8\u0acd\u0a9f\u0abf\u0a82\u0a97 \u0a85\u0aa8\u0ac7 \u0a9c\u0ac0\u0a8f\u0ab8\u0a9f\u0ac0 \u0ab5\u0abe\u0a89\u0a9a\u0ab0",
                lbl_vtype: "\u0ab5\u0abe\u0a89\u0a9a\u0ab0 \u0aaa\u0acd\u0ab0\u0a95\u0abe\u0ab0:",
                lbl_party: "\u0aaa\u0abe\u0ab0\u0acd\u0a9f\u0ac0 / \u0ab2\u0ac7\u0a9c\u0ab0 \u0aa8\u0abe\u0aae:",
                lbl_amount: "\u0aae\u0ac2\u0ab3 \u0ab0\u0a95\u0aae (\u20b9):",
                lbl_narration: "\u0aa8\u0ab0\u0ac7\u0ab6\u0aa8:",
                btn_save_voucher: "\u26a1 \u0ab5\u0abe\u0a89\u0a9a\u0ab0 \u0ab8\u0ac7\u0ab5 \u0a95\u0ab0\u0acb (\u0a93\u0a9f\u0acb \u0ae7\u0aeee% GST)",
                bank_tx_title: "\u0a87\u0aa8\u0acd\u0aa1\u0abf\u0aaf\u0aa8 \u0aac\u0ac7\u0a82\u0a95 \u0a9f\u0acd\u0ab0\u0abe\u0a82\u0a9d\u0ac7\u0a95\u0acd\u0ab6\u0aa8\u0acd\u0ab8 \u0ab9\u0aac",
                lbl_select_bank: "\u0aac\u0ac7\u0a82\u0a95 \u0aaa\u0ab8\u0a82\u0aa6 \u0a95\u0ab0\u0acb:",
                lbl_tx_type: "\u0a9f\u0acd\u0ab0\u0abe\u0a82\u0a9d\u0ac7\u0a95\u0acd\u0ab6\u0aa8 \u0aaa\u0acd\u0ab0\u0a95\u0abe\u0ab0:",
                opt_deposit: "\u0a9c\u0aae\u0abe",
                opt_withdraw: "\u0a89\u0aaa\u0abe\u0aa1",
                lbl_pay_mode: "\u0aaa\u0ac7\u0aae\u0ac7\u0aa8\u0acd\u0a9f \u0aae\u0acb\u0aa1:",
                lbl_ref: "\u0aa8\u0ab0\u0ac7\u0ab6\u0aa8 / \u0ab0\u0ac7\u0aab:",
                btn_process_tx: "\U0001f3e6 \u0aac\u0ac7\u0a82\u0a95 \u0a9f\u0acd\u0ab0\u0abe\u0a82\u0a9d\u0ac7\u0a95\u0acd\u0ab6\u0aa8 \u0aaa\u0acd\u0ab0\u0acb\u0ab8\u0ac7\u0ab8 \u0a95\u0ab0\u0acb",
                lbl_add_bank: "+ \u0aa8\u0ab5\u0ac0 \u0aac\u0ac7\u0a82\u0a95 \u0a89\u0aae\u0ac7\u0ab0\u0acb:",
                lbl_acc_num: "\u0a8f\u0a95\u0abe\u0a8a\u0aa8\u0acd\u0a9f \u0aa8\u0a82\u0aac\u0ab0:",
                lbl_opening_bal: "\u0ab6\u0acd\u0ab0\u0ac1\u0a86\u0aa4\u0aa8\u0ac1\u0a82 \u0aac\u0ac7\u0ab2\u0ac7\u0aa8\u0acd\u0ab8 (\u20b9):",
                btn_register_bank: "\u0aac\u0ac7\u0a82\u0a95 \u0ab0\u0a9c\u0abf\u0ab8\u0acd\u0ab5\u0ab0 \u0a95\u0ab0\u0acb",
                inv_title: "\u0a87\u0aa8\u0acd\u0ab5\u0ac7\u0aa8\u0acd\u0a9f\u0ab0\u0ac0 \u0a95\u0aa8\u0acd\u0a9f\u0acd\u0ab0\u0acb\u0ab2",
                lbl_movement: "\u0aae\u0ac2\u0ab5\u0aae\u0ac7\u0aa8\u0acd\u0a9f \u0aaa\u0acd\u0ab0\u0a95\u0abe\u0ab0:",
                opt_inward: "\u0a86\u0ab5\u0a95",
                opt_outward: "\u0a9c\u0abe\u0ab5\u0a95",
                lbl_item_name: "\u0a86\u0a88\u0a9f\u0aae\u0aa8\u0ac1\u0a82 \u0aa8\u0abe\u0aae:",
                lbl_sku: "\u0a8f\u0ab8\u0a95\u0ac7\u0aaf\u0ac1 \u0a95\u0acb\u0aa1:",
                lbl_market_status: "\u0aae\u0abe\u0ab0\u0acd\u0a95\u0ac7\u0a9f \u0a9f\u0acd\u0ab0\u0ac7\u0aa8\u0acd\u0aa1 \u0ab8\u0acd\u0a9f\u0ac7\u0a9f\u0ab8:",
                opt_trending: "\U0001f525 \u0aac\u0a9c\u0abe\u0ab0\u0aae\u0abe\u0a82 \u0a9a\u0ab2\u0aa4\u0ac0 \u0ab5\u0ab8\u0acd\u0aa4\u0ac1 (Trending)",
                lbl_qty: "\u0a9c\u0aa5\u0acd\u0aa5\u0acb (Qty):",
                lbl_price: "\u0a95\u0abf\u0a82\u0aae\u0aa4 (\u20b9):",
                btn_update_stock: "\U0001f680 \u0ab8\u0acd\u0a9f\u0acb\u0a95 \u0a85\u0aaa\u0aa1\u0ac7\u0a9f \u0a95\u0ab0\u0acb",
                adv_title: "\u0a8f\u0aa1\u0ab5\u0abe\u0aa8\u0acd\u0ab8 \u0a8f\u0a95\u0abe\u0a8a\u0aa8\u0acd\u0a9f \u0ab2\u0ac7\u0a9c\u0ab0",
                lbl_party_name: "\u0aaa\u0abe\u0ab0\u0acd\u0a9f\u0ac0\u0aa8\u0ac1\u0a82 \u0aa8\u0abe\u0aae:",
                lbl_adv_type: "\u0a8f\u0aa1\u0ab5\u0abe\u0aa8\u0acd\u0ab8 \u0aaa\u0acd\u0ab0\u0a95\u0abe\u0ab0:",
                opt_adv_given: "\u0a8f\u0aa1\u0ab5\u0abe\u0aa8\u0acd\u0ab8 \u0a86\u0aaa\u0ac7\u0ab2\u0ac1\u0a82",
                opt_adv_taken: "\u0a8f\u0aa1\u0ab5\u0abe\u0aa8\u0acd\u0ab8 \u0ab2\u0ac0\u0aa7\u0ac7\u0ab2\u0ac1\u0a82",
                btn_record_adv: "\U0001f91d \u0a8f\u0aa1\u0ab5\u0abe\u0aa8\u0acd\u0ab8 \u0aa8\u0acb\u0a82\u0aa7\u0ac0 \u0a95\u0ab0\u0acb",
                history_title: "\u0aa4\u0abe\u0a9c\u0ac7\u0aa4\u0ab0\u0aa8\u0abe \u0ab5\u0abe\u0a89\u0a9a\u0ab0\u0acd\u0ab8 \u0a85\u0aa8\u0ac7 \u0ab6\u0ac7\u0ab0\u0abf\u0a82\u0a97",
                th_type: "\u0aaa\u0acd\u0ab0\u0a95\u0abe\u0ab0",
                th_party: "\u0aaa\u0abe\u0ab0\u0acd\u0a9f\u0ac0",
                th_total: "\u0a95\u0ac1\u0ab2 (\u0a9c\u0ac0\u0a8f\u0ab8\u0a9f\u0ac0 \u0ab8\u0abe\u0aa5\u0ac7)",
                th_action: "\u0a8f\u0a95\u0acd\u0ab6\u0aa8",
                send: "\u0aae\u0acb\u0a95\u0ab2\u0acb"
            }
        };

        function setLanguage(lang) {
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