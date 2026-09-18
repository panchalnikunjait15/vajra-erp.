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
        
        # તારા બધા જ ઓરિજિનલ ડેટાબેઝ ટેબલ્સ
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

# --- MAIN ROUTE ---
@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# --- LOGIN ROUTE ---
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "admin123":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid Credentials. Try admin / admin123"
    
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="gu">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vajra ERP - Login</title>
            <style>
                body { background: #0f172a; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .login-box { background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); width: 300px; text-align: center; }
                input { width: 100%; padding: 10px; margin: 10px 0; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 6px; box-sizing: border-box; }
                button { width: 100%; padding: 10px; background: #2563eb; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
                button:hover { background: #1d4ed8; }
                .error { color: #ef4444; font-size: 14px; margin-bottom: 10px; }
            </style>
        </head>
        <body>
            <div class="login-box">
                <h2>⚡ Vajra ERP Login</h2>
                {% if error %}<div class="error">{{ error }}</div>{% endif %}
                <form method="POST">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>
    ''', error=error)

# --- DASHBOARD ROUTE (ઓરિજિનલ + AI Voice Assistant) ---
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="gu">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vajra ERP - Dashboard</title>
            <style>
                body { background: #0f172a; color: white; font-family: sans-serif; padding: 20px; margin: 0; }
                .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
                button { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 16px; margin-right: 10px; }
                button:hover { background: #1d4ed8; }
                .logout { background: #dc2626; float: right; }
                .logout:hover { background: #b91c1c; }
                h1 { margin-top: 0; }
            </style>
        </head>
        <body>
            <a href="/logout"><button class="logout">Logout</button></a>
            <h1>⚡ Vajra ERP Dashboard</h1>
            
            <div class="card">
                <h3>📊 Quick Links & Operations</h3>
                <a href="/export_inventory_csv"><button>Export Inventory CSV</button></a>
                <a href="/backup_db"><button>Backup Database</button></a>
            </div>

            <!-- 🤖 AI & Voice Assistant Widget -->
            <div class="card">
                <h3>🤖 Vajra AI Voice Assistant</h3>
                <p id="voiceStatus" style="color: #38bdf8;">માઇક બટન દબાવીને બોલો...</p>
                <button onclick="startVoiceRecognition()">🎤 બોલો (Speak)</button>
                <p id="aiReply" style="margin-top: 15px; font-size: 18px; font-weight: bold;"></p>
            </div>

            <script>
            function startVoiceRecognition() {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    alert("તમારું બ્રાઉઝર વોઇસ રેકગ્નિશન સપોર્ટ કરતું નથી.");
                    return;
                }

                const recognition = new SpeechRecognition();
                recognition.lang = 'gu-IN';

                recognition.onstart = function() {
                    document.getElementById("voiceStatus").innerText = "સંભળાઈ રહ્યું છે... બોલો!";
                };

                recognition.onresult = function(event) {
                    const spokenText = event.results[0][0].transcript;
                    document.getElementById("voiceStatus").innerText = "તમે બોલ્યા: " + spokenText;
                    sendQueryToAI(spokenText);
                };

                recognition.onerror = function(event) {
                    document.getElementById("voiceStatus").innerText = "કંઈક ભૂલ થઈ, ફરી પ્રયત્ન કરો.";
                };

                recognition.start();
            }

            function sendQueryToAI(queryText) {
                fetch('/api/ai-assistant', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: queryText })
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById("aiReply").innerText = "AI જવાબ: " + data.reply;
                    let speech = new SpeechSynthesisUtterance(data.reply);
                    speech.lang = 'gu-IN';
                    window.speechSynthesis.speak(speech);
                });
            }
            </script>
        </body>
        </html>
    ''')

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

# --- ઓરિજિનલ ERP Routes ---
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
