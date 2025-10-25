import hashlib
import json
from time import time
from uuid import uuid4
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import requests
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadSignatureError

# ===== Wallet =====
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

# ===== Blockchain =====
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
        transaction = {'sender': sender, 'recipient': recipient, 'amount': amount}
        if sender != "0":
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

# ======= Node Setup =====
wallet = Wallet()
blockchain = Blockchain()

# ======= GUI =======
root = tk.Tk()
root.title("SAXV Chain v4 GUI")
root.geometry("500x600")

# Output console
console = scrolledtext.ScrolledText(root, width=60, height=30)
console.pack()

def log(msg):
    console.insert(tk.END, f"{msg}\n")
    console.see(tk.END)

# Mine block
def mine_block():
    log("Mining block...")
    last_proof = blockchain.last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    blockchain.new_transaction(sender="0", recipient=wallet.public_key.to_string().hex(), amount=1, signature="")
    block = blockchain.new_block(proof)
    log(f"Block mined: Index {block['index']}")
    show_chain()

# New transaction
def send_transaction():
    sender = wallet.public_key.to_string().hex()
    recipient = recipient_entry.get()
    amount = amount_entry.get()
    try:
        amount = float(amount)
    except:
        messagebox.showerror("Error", "Amount harus angka")
        return
    tx = {'sender': sender, 'recipient': recipient, 'amount': amount}
    signature = wallet.sign(tx)
    index = blockchain.new_transaction(sender, recipient, amount, signature)
    if index:
        log(f"Transaction added to Block {index}")
    else:
        log("Transaction invalid")

# Show blockchain
def show_chain():
    console.delete(1.0, tk.END)
    for block in blockchain.chain:
        log(f"Index: {block['index']}, Proof: {block['proof']}, PrevHash: {block['previous_hash']}")
        for tx in block['transactions']:
            log(f"  TX: {tx}")
        log("----------")

# Wallet info
def show_wallet():
    log(f"Public Key: {wallet.public_key.to_string().hex()}")
    log(f"Private Key: {wallet.private_key.to_string().hex()}")

# Buttons
tk.Button(root, text="Mine Block", command=mine_block).pack()
tk.Button(root, text="Show Wallet", command=show_wallet).pack()

tk.Label(root, text="Recipient Public Key").pack()
recipient_entry = tk.Entry(root, width=60)
recipient_entry.pack()

tk.Label(root, text="Amount").pack()
amount_entry = tk.Entry(root, width=60)
amount_entry.pack()

tk.Button(root, text="Send Transaction", command=send_transaction).pack()
tk.Button(root, text="Show Blockchain", command=show_chain).pack()

log("SAXV Chain v4 GUI started!")
root.mainloop()