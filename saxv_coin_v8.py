import hashlib
import json
import time
from uuid import uuid4
from flask import Flask, jsonify, request
import requests
import threading

# ---------------------------
# CONFIG
# ---------------------------
SUPPLY = 31_000_000
MINING_REWARD = 10
NODE_ID = str(uuid4()).replace('-', '')

# ---------------------------
# BLOCKCHAIN CLASS
# ---------------------------
class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')  # Genesis block

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.transactions,
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        while True:
            hash_op = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_op[:4] == '0000':
                return new_proof
            new_proof += 1

    def hash(self, block):
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        return self.get_previous_block()['index'] + 1

    def is_chain_valid(self, chain=None):
        if chain is None:
            chain = self.chain
        prev_block = chain[0]
        index = 1
        while index < len(chain):
            block = chain[index]
            if block['previous_hash'] != self.hash(prev_block):
                return False
            prev_proof = prev_block['proof']
            proof = block['proof']
            hash_op = hashlib.sha256(str(proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_op[:4] != '0000':
                return False
            prev_block = block
            index += 1
        return True

# ---------------------------
# NODE & WALLET
# ---------------------------
blockchain = Blockchain()
wallet = {'address': NODE_ID, 'balance': SUPPLY}

# List of connected nodes
nodes = set()

# ---------------------------
# FLASK SERVER
# ---------------------------
app = Flask(__name__)

@app.route('/mine_block', methods=['GET'])
def mine_block():
    prev_block = blockchain.get_previous_block()
    prev_proof = prev_block['proof']
    proof = blockchain.proof_of_work(prev_proof)
    prev_hash = blockchain.hash(prev_block)
    blockchain.add_transaction("SYSTEM", wallet['address'], MINING_REWARD)
    block = blockchain.create_block(proof, prev_hash)
    wallet['balance'] += MINING_REWARD
    response = {
        'message': 'Block mined!',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    tx = request.get_json()
    required = ['sender', 'receiver', 'amount']
    if not all(k in tx for k in required):
        return 'Missing data', 400
    index = blockchain.add_transaction(tx['sender'], tx['receiver'], tx['amount'])
    return jsonify({'message': f'Transaction added to block {index}'}), 201

@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain, 'length': len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/connect_node', methods=['POST'])
def connect_node():
    node = request.get_json().get('node_address')
    if node:
        nodes.add(node)
        return jsonify({'message': 'Node connected', 'total_nodes': list(nodes)}), 201
    return 'No node address', 400

# ---------------------------
# SYNC FUNCTION
# ---------------------------
def sync_chain():
    global blockchain
    for node in nodes:
        try:
            response = requests.get(f"{node}/get_chain")
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > len(blockchain.chain) and blockchain.is_chain_valid(chain):
                    blockchain.chain = chain
        except:
            pass
    threading.Timer(10.0, sync_chain).start()  # Sync every 10 detik

# ---------------------------
# RUN SERVER
# ---------------------------
if __name__ == '__main__':
    sync_chain()
    app.run(host='0.0.0.0', port=5000)