#!/usr/bin/env python3
"""
saxv_chain_mini_v6.py
Minimal multi-node blockchain (SAXV Chain Mini v6)
- Lightweight PoW
- Peer registration + simple longest-chain consensus
- Persistent file storage per node (chain_{port}.json)
Designed to run on resource-limited devices (Pydroid 3 / Acode)
"""

import hashlib
import json
import time
import os
import sys
import threading
from uuid import uuid4
from urllib.parse import urlparse

try:
    from flask import Flask, jsonify, request
except Exception as e:
    print("ERROR: Flask not found. Install with: pip install Flask")
    raise

try:
    import requests
except Exception as e:
    print("ERROR: requests not found. Install with: pip install requests")
    raise

# --------- Configuration (tune these for HP) ----------
DIFFICULTY = 2  # number of leading zeros required in hash (keep very small on HP)
MAX_TX_BATCH = 20  # max txs per block (keep small)
STORAGE_DIR = "."  # where chain files are saved
# -------------------------------------------------------

class SAXVChain:
    def __init__(self, node_id, port):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        self.node_id = node_id
        self.port = port
        # load or create genesis
        self.filename = os.path.join(STORAGE_DIR, f"chain_{self.port}.json")
        if os.path.exists(self.filename):
            self._load_chain()
            print(f"[node {self.port}] Loaded chain from {self.filename} (len={len(self.chain)})")
        else:
            # create genesis block
            self.new_block(previous_hash='1', proof=100)
            self._save_chain()
            print(f"[node {self.port}] Created genesis block")

    def _save_chain(self):
        try:
            with open(self.filename, "w") as f:
                json.dump({
                    "chain": self.chain,
                    "nodes": list(self.nodes),
                    "current_transactions": self.current_transactions
                }, f)
        except Exception as e:
            print("[save chain] failed:", e)

    def _load_chain(self):
        with open(self.filename, "r") as f:
            data = json.load(f)
            self.chain = data.get("chain", [])
            self.nodes = set(data.get("nodes", []))
            self.current_transactions = data.get("current_transactions", [])

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions[:MAX_TX_BATCH],
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]) if self.chain else '1'
        }
        # add and clear used transactions
        self.chain.append(block)
        # remove included txs from current_transactions
        self.current_transactions = self.current_transactions[len(block['transactions']):]
        self._save_chain()
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Adds a transaction to the list of transactions
        """
        tx = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': time.time()
        }
        self.current_transactions.append(tx)
        self._save_chain()
        return self.last_block['index'] + 1 if self.chain else 1

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        """
        # We must ensure the Dictionary is ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1] if self.chain else None

    def proof_of_work(self, last_proof, difficulty=DIFFICULTY):
        """
        Simple Proof of Work:
         - find p such that hash(pp') has difficulty leading zeros
        """
        proof = 0
        target = "0" * difficulty
        while True:
            guess = f'{last_proof}{proof}'.encode()
            guess_hash = hashlib.sha256(guess).hexdigest()
            if guess_hash[:difficulty] == target:
                return proof
            proof += 1

    def register_node(self, address):
        """
        Add a new node's address (e.g. http://192.168.1.2:5001)
        """
        parsed = urlparse(address)
        if parsed.netloc:
            self.nodes.add(parsed.geturl().split("://")[-1])
        elif parsed.path:
            # accept addresses without scheme
            self.nodes.add(parsed.path)
        self._save_chain()

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # check previous hash
            if block['previous_hash'] != self.hash(last_block):
                return False
            # check proof of work
            last_proof = last_block['proof']
            proof = block['proof']
            guess = f'{last_proof}{proof}'.encode()
            guess_hash = hashlib.sha256(guess).hexdigest()
            if guess_hash[:DIFFICULTY] != "0" * DIFFICULTY:
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        Consensus Algorithm: resolve by replacing our chain with the longest valid one in the network
        """
        neighbours = self.nodes.copy()
        new_chain = None
        max_length = len(self.chain)

        for node in neighbours:
            url = f'http://{node}/chain'
            try:
                r = requests.get(url, timeout=3)
                if r.status_code == 200:
                    data = r.json()
                    length = data.get('length')
                    chain = data.get('chain')
                    if length and chain and length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except Exception:
                # network error or node offline — ignore
                pass

        if new_chain:
            self.chain = new_chain
            self._save_chain()
            return True
        return False

# ---------------- Flask App ----------------
app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')

# parse port from args
if len(sys.argv) >= 2:
    try:
        PORT = int(sys.argv[1])
    except:
        PORT = 5000
else:
    PORT = 5000

chain = SAXVChain(node_id=node_identifier, port=PORT)

@app.route('/mine', methods=['GET'])
def mine():
    # quick consensus before mining to avoid wasteful mining on an outdated chain
    chain.resolve_conflicts()

    last_block = chain.last_block
    last_proof = last_block['proof'] if last_block else 0
    proof = chain.proof_of_work(last_proof)

    # reward for mining (sender "0" means new coin)
    chain.new_transaction(sender="0", recipient=chain.node_id, amount=1)

    previous_hash = chain.hash(last_block) if last_block else '1'
    block = chain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json(force=True)
    required = ['sender', 'recipient', 'amount']
    if not values or not all(k in values for k in required):
        return 'Missing values', 400
    index = chain.new_transaction(values['sender'], values['recipient'], values['amount'])
    return jsonify({'message': f'Transaction will be added to block {index}'}), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    return jsonify({
        'chain': chain.chain,
        'length': len(chain.chain)
    }), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json(force=True)
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a list of node addresses", 400
    for n in nodes:
        chain.register_node(n)
    return jsonify({'message': 'Nodes added', 'total_nodes': list(chain.nodes)}), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = chain.resolve_conflicts()
    if replaced:
        return jsonify({'message': 'Our chain was replaced', 'new_chain': chain.chain}), 200
    else:
        return jsonify({'message': 'Our chain is authoritative', 'chain': chain.chain}), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'node_id': chain.node_id,
        'port': chain.port,
        'peers': list(chain.nodes),
        'chain_length': len(chain.chain),
        'pending_txs': len(chain.current_transactions)
    }), 200

# Lightweight background consensus ticker (optional)
def periodic_consensus(interval=30):
    while True:
        try:
            changed = chain.resolve_conflicts()
            if changed:
                print(f"[{chain.port}] Consensus replaced chain (len={len(chain.chain)})")
        except Exception:
            pass
        time.sleep(interval)

if __name__ == '__main__':
    # start background thread only if not on extremely constrained env
    try:
        t = threading.Thread(target=periodic_consensus, args=(20,), daemon=True)
        t.start()
    except Exception:
        pass

    print(f"Starting SAXV Chain Mini v6 on port {PORT} (DIFFICULTY={DIFFICULTY})")
    app.run(host='0.0.0.0', port=PORT)