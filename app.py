# -*- coding: utf-8 -*-
import os
import sqlite3
import hashlib
import time
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, Response, send_file, jsonify
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

# --- AI & VOICE ASSISTANT API ROUTE ---
@app.route("/api/ai-assistant", methods=["POST"])
def ai_assistant():
    data = request.get_json() or {}
    user_query = data.get("query", "").lower()
    
    response_text = "માહિતી ઉપલબ્ધ નથી."
    
    if "profit" in user_query or "nofo" in user_query or "નફો" in user_query:
        response_text = "આજે કુલ નફો ₹12,500 થયો છે, જે ગઇકાલ કરતાં 15% વધુ છે."
    elif "sales" in user_query or "vechan" in user_query or "આવક" in user_query:
        response_text = "આજના દિવસનું કુલ વેચાણ ₹45,000 નું રહ્યું છે."
    elif "stock" in user_query or "stok" in user_query:
        response_text = "ચેતવણી: 3 પ્રોડક્ટ્સનો સ્ટોક પૂરો થવાની તૈયારીમાં છે."
    else:
        response_text = "માફ કરશો, હું આ પ્રશ્ન સમજી શક્યો નથી. તમે 'નફો', 'વેચાણ' અથવા 'સ્ટોક' વિશે પૂછી શકો છો."

    return jsonify({"status": "success", "reply": response_text})

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
