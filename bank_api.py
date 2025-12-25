from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)

# Database file
DB_FILE = 'bank_data.json'

# Initialize sample data if not exists
def init_database():
    if not os.path.exists(DB_FILE):
        sample_data = {
            "accounts": [
                {
                    "account_id": "ACC001",
                    "account_name": "John Doe",
                    "account_type": "Checking",
                    "balance": 12500.75,
                    "currency": "USD",
                    "status": "Active"
                },
                {
                    "account_id": "ACC002",
                    "account_name": "John Doe",
                    "account_type": "Savings",
                    "balance": 45000.50,
                    "currency": "USD",
                    "status": "Active"
                },
                {
                    "account_id": "ACC003",
                    "account_name": "Jane Smith",
                    "account_type": "Checking",
                    "balance": 8500.25,
                    "currency": "USD",
                    "status": "Active"
                }
            ],
            "transactions": [
                {
                    "transaction_id": "TXN001",
                    "account_id": "ACC001",
                    "type": "debit",
                    "amount": 250.00,
                    "description": "Grocery Store",
                    "date": "2024-01-15",
                    "category": "Food",
                    "status": "Completed"
                },
                {
                    "transaction_id": "TXN002",
                    "account_id": "ACC001",
                    "type": "credit",
                    "amount": 1500.00,
                    "description": "Salary Deposit",
                    "date": "2024-01-14",
                    "category": "Income",
                    "status": "Completed"
                },
                {
                    "transaction_id": "TXN003",
                    "account_id": "ACC002",
                    "type": "credit",
                    "amount": 500.00,
                    "description": "Transfer from Checking",
                    "date": "2024-01-13",
                    "category": "Transfer",
                    "status": "Completed"
                },
                {
                    "transaction_id": "TXN004",
                    "account_id": "ACC001",
                    "type": "debit",
                    "amount": 89.99,
                    "description": "Online Shopping",
                    "date": "2024-01-12",
                    "category": "Shopping",
                    "status": "Completed"
                },
                {
                    "transaction_id": "TXN005",
                    "account_id": "ACC003",
                    "type": "debit",
                    "amount": 1200.00,
                    "description": "Rent Payment",
                    "date": "2024-01-10",
                    "category": "Housing",
                    "status": "Completed"
                }
            ],
            "cards": [
                {
                    "card_id": "CARD001",
                    "card_number": "**** **** **** 1234",
                    "card_type": "Visa Debit",
                    "account_id": "ACC001",
                    "expiry": "12/2026",
                    "status": "Active",
                    "spent_this_month": 1250.75
                },
                {
                    "card_id": "CARD002",
                    "card_number": "**** **** **** 5678",
                    "card_type": "Mastercard Credit",
                    "account_id": "ACC002",
                    "expiry": "08/2025",
                    "status": "Active",
                    "spent_this_month": 500.00
                }
            ]
        }
        save_database(sample_data)

def load_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {"accounts": [], "transactions": [], "cards": []}

def save_database(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

# Serve CSS file
@app.route('/style.css')
def serve_css():
    return send_from_directory('.', 'style.css')

# API Health Check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Bank API"
    })

# Get all accounts
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    data = load_database()
    total_balance = sum(acc['balance'] for acc in data['accounts'])
    return jsonify({
        "accounts": data['accounts'],
        "total_balance": total_balance,
        "count": len(data['accounts'])
    })

# Get account by ID
@app.route('/api/accounts/<account_id>', methods=['GET'])
def get_account(account_id):
    data = load_database()
    account = next((acc for acc in data['accounts'] if acc['account_id'] == account_id), None)
    if account:
        # Get account transactions
        transactions = [t for t in data['transactions'] if t['account_id'] == account_id][-10:]
        return jsonify({
            "account": account,
            "recent_transactions": transactions
        })
    return jsonify({"error": "Account not found"}), 404

# Get all transactions
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    data = load_database()
    
    # Optional filters
    account_id = request.args.get('account_id')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    filtered_transactions = data['transactions']
    
    if account_id:
        filtered_transactions = [t for t in filtered_transactions if t['account_id'] == account_id]
    
    if category:
        filtered_transactions = [t for t in filtered_transactions if t['category'] == category]
    
    if start_date:
        filtered_transactions = [t for t in filtered_transactions if t['date'] >= start_date]
    
    if end_date:
        filtered_transactions = [t for t in filtered_transactions if t['date'] <= end_date]
    
    # Sort by date (newest first)
    filtered_transactions.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate summary
    total_debits = sum(t['amount'] for t in filtered_transactions if t['type'] == 'debit')
    total_credits = sum(t['amount'] for t in filtered_transactions if t['type'] == 'credit')
    
    return jsonify({
        "transactions": filtered_transactions,
        "summary": {
            "total_transactions": len(filtered_transactions),
            "total_debits": total_debits,
            "total_credits": total_credits,
            "net_flow": total_credits - total_debits
        }
    })

# Add new transaction
@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['account_id', 'type', 'amount', 'description', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Load current database
        db_data = load_database()
        
        # Create new transaction
        new_transaction = {
            "transaction_id": f"TXN{len(db_data['transactions']) + 1:03d}",
            "account_id": data['account_id'],
            "type": data['type'],
            "amount": float(data['amount']),
            "description": data['description'],
            "date": data.get('date', datetime.now().strftime('%Y-%m-%d')),
            "category": data['category'],
            "status": "Pending"
        }
        
        # Update account balance
        for account in db_data['accounts']:
            if account['account_id'] == data['account_id']:
                if data['type'] == 'credit':
                    account['balance'] += float(data['amount'])
                else:
                    account['balance'] -= float(data['amount'])
                break
        
        db_data['transactions'].append(new_transaction)
        save_database(db_data)
        
        return jsonify({
            "message": "Transaction added successfully",
            "transaction": new_transaction
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get cards
@app.route('/api/cards', methods=['GET'])
def get_cards():
    data = load_database()
    return jsonify({
        "cards": data['cards'],
        "count": len(data['cards'])
    })

# Get financial summary
@app.route('/api/summary', methods=['GET'])
def get_summary():
    data = load_database()
    
    total_balance = sum(acc['balance'] for acc in data['accounts'])
    total_transactions = len(data['transactions'])
    
    # Recent transactions (last 30 days simulated)
    recent_transactions = data['transactions'][-5:]  # Last 5 transactions
    
    # Monthly spending by category
    categories = {}
    for transaction in data['transactions']:
        if transaction['type'] == 'debit':
            cat = transaction['category']
            categories[cat] = categories.get(cat, 0) + transaction['amount']
    
    return jsonify({
        "summary": {
            "total_balance": total_balance,
            "total_accounts": len(data['accounts']),
            "active_cards": len(data['cards']),
            "total_transactions": total_transactions,
            "recent_transactions": recent_transactions
        },
        "spending_by_category": [
            {"category": cat, "amount": amount} 
            for cat, amount in categories.items()
        ]
    })

# Transfer between accounts
@app.route('/api/transfer', methods=['POST'])
def transfer_funds():
    try:
        data = request.get_json()
        
        required_fields = ['from_account', 'to_account', 'amount', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({"error": "Amount must be positive"}), 400
        
        db_data = load_database()
        
        # Find accounts
        from_acc = next((acc for acc in db_data['accounts'] if acc['account_id'] == data['from_account']), None)
        to_acc = next((acc for acc in db_data['accounts'] if acc['account_id'] == data['to_account']), None)
        
        if not from_acc or not to_acc:
            return jsonify({"error": "One or both accounts not found"}), 404
        
        if from_acc['balance'] < amount:
            return jsonify({"error": "Insufficient funds"}), 400
        
        # Update balances
        from_acc['balance'] -= amount
        to_acc['balance'] += amount
        
        # Create transfer transactions
        today = datetime.now().strftime('%Y-%m-%d')
        
        debit_transaction = {
            "transaction_id": f"TXN{len(db_data['transactions']) + 1:03d}",
            "account_id": data['from_account'],
            "type": "debit",
            "amount": amount,
            "description": f"Transfer to {to_acc['account_name']}: {data['description']}",
            "date": today,
            "category": "Transfer",
            "status": "Completed"
        }
        
        credit_transaction = {
            "transaction_id": f"TXN{len(db_data['transactions']) + 2:03d}",
            "account_id": data['to_account'],
            "type": "credit",
            "amount": amount,
            "description": f"Transfer from {from_acc['account_name']}: {data['description']}",
            "date": today,
            "category": "Transfer",
            "status": "Completed"
        }
        
        db_data['transactions'].extend([debit_transaction, credit_transaction])
        save_database(db_data)
        
        return jsonify({
            "message": "Transfer completed successfully",
            "new_balance": from_acc['balance'],
            "transactions": [debit_transaction, credit_transaction]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_database()
    print("Bank API Server Starting...")
    print("Dashboard available at: http://localhost:5000")
    app.run(debug=True, port=5000)