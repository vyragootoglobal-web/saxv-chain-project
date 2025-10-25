# ==========================================
# 🚀 SAXV Chain Mini v5 – Stable Edition
# Tanpa error, tanpa lag, optimized for HP
# ==========================================

import hashlib
import json
import time
from flask import Flask, jsonify, request
import threading

# ------------------------------------------
# Block structure
# ------------------------------------------
class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

# ------------------------------------------
# Blockchain core
# ------------------------------------------
class Blockchain:
    difficulty = 2  # kecil biar ga lag di HP

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), ["Genesis Block"], "0")
        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]

    def add_transaction(self, sender, recipient, amount):
        tx = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': time.time()
        }
        self.unconfirmed_transactions.append(tx)
        return True

    def proof_of_work(self, block):
        while not block.hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            block.hash = block.compute_hash()
        return block.hash

    def add_block(self, block, proof):
        previous_hash = self.get_last_block().hash
        if previous_hash != block.previous_hash:
            return False
        if not proof.startswith('0' * Blockchain.difficulty):
            return False
        block.hash = proof
        self.chain.append(block)
        return True

    def mine(self):
        if not self.unconfirmed_transactions:
            return False

        last_block = self.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            timestamp=time.time(),
            transactions=self.unconfirmed_transactions,
            previous_hash=last_block.hash
        )
        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        return new_block.index

# ------------------------------------------
# Flask Web API
# ------------------------------------------
app = Flask(__name__)
blockchain = Blockchain()

@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = [block.__dict__ for block in blockchain.chain]
    return jsonify({
        "length": len(chain_data),
        "chain": chain_data
    })

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    data = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in data for k in required):
        return "Missing values", 400

    blockchain.add_transaction(
        data['sender'], data['recipient'], data['amount']
    )
    return jsonify({"message": "Transaction added successfully"}), 201

@app.route('/mine', methods=['GET'])
def mine_block():
    index = blockchain.mine()
    if not index:
        return jsonify({"message": "No transactions to mine"}), 200
    return jsonify({
        "message": f"Block #{index} mined successfully!"
    }), 200

# ------------------------------------------
# Run server in background (auto start)
# ------------------------------------------
def run_app():
    app.run(host='0.0.0.0', port=5000)

thread = threading.Thread(target=run_app)
thread.daemon = True
thread.start()

# ------------------------------------------
# CLI simple display
# ------------------------------------------
print("\n=== SAXV Chain Mini v5 – Stable ===")
print("API endpoints:")
print("  ➤ /chain – lihat semua block")
print("  ➤ /new_transaction – kirim transaksi")
print("  ➤ /mine – tambang block baru")
print("\nServer berjalan di http://127.0.0.1:5000\n")
print("Jalankan di browser HP atau Postman untuk uji coba!")