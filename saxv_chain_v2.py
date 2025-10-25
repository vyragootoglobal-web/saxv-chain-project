import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadSignatureError

# ======= Wallet =======
class Wallet:
    def __init__(self):
        self.private_key = SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()

    def sign(self, message):
        message_bytes = json.dumps(message, sort_keys=True).encode()
        return self.private_key.sign(message_bytes).hex()

    @staticmethod
    def verify_signature(public_key_hex, message, signature_hex):
        try:
            public_key = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
            message_bytes = json.dumps(message, sort_keys=True).encode()
            signature = bytes.fromhex(signature_hex)
            return public_key.verify(signature, message_bytes)
        except BadSignatureError:
            return False

# ======= Blockchain =======
class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount, signature):
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }

        if sender != "0":  # "0" untuk mining reward
            if not Wallet.verify_signature(sender, transaction, signature):
                return False

        self.current_transactions.append(transaction)
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    # Proof-of-Work sederhana
    def proof_of_work(self, last_proof):
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# ======= Flask Web App =======
app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()
wallet = Wallet()  # Wallet node default

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Reward untuk miner
    blockchain.new_transaction(
        sender="0",
        recipient=wallet.public_key.to_string().hex(),
        amount=1,
        signature=""  # reward tidak perlu tanda tangan
    )

    block = blockchain.new_block(proof)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(
        values['sender'],
        values['recipient'],
        values['amount'],
        values['signature']
    )

    if not index:
        return jsonify({'message': 'Invalid Signature'}), 400

    return jsonify({'message': f'Transaction will be added to Block {index}'}), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/wallet', methods=['GET'])
def get_wallet():
    return jsonify({
        'private_key': wallet.private_key.to_string().hex(),
        'public_key': wallet.public_key.to_string().hex()
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)