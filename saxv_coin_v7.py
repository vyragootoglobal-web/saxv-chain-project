import hashlib
import json
import time
from uuid import uuid4
import tkinter as tk
from tkinter import messagebox

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
        check_proof = False
        while not check_proof:
            hash_op = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_op[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def is_chain_valid(self):
        prev_block = self.chain[0]
        index = 1
        while index < len(self.chain):
            block = self.chain[index]
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
wallet = {
    'address': NODE_ID,
    'balance': SUPPLY
}

# ---------------------------
# FUNCTIONS
# ---------------------------
def mine_block_gui():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    prev_hash = blockchain.hash(previous_block)
    blockchain.add_transaction("SYSTEM", wallet['address'], MINING_REWARD)
    block = blockchain.create_block(proof, prev_hash)
    wallet['balance'] += MINING_REWARD
    update_display()
    messagebox.showinfo("Mining", f"Block mined! Index: {block['index']}")

def send_saxv_gui():
    receiver = entry_receiver.get()
    try:
        amount = int(entry_amount.get())
    except:
        messagebox.showerror("Error", "Jumlah harus angka!")
        return
    if wallet['balance'] < amount:
        messagebox.showerror("Error", "Saldo tidak cukup!")
        return
    blockchain.add_transaction(wallet['address'], receiver, amount)
    wallet['balance'] -= amount
    update_display()
    messagebox.showinfo("Transaction", f"{amount} SAXV dikirim ke {receiver}")

def update_display():
    label_balance.config(text=f"Wallet Balance: {wallet['balance']} SAXV")
    text_chain.delete(1.0, tk.END)
    for block in blockchain.chain:
        text_chain.insert(tk.END, f"Index: {block['index']} | Transactions: {len(block['transactions'])}\n")

# ---------------------------
# GUI SETUP
# ---------------------------
root = tk.Tk()
root.title("SAXV Node V7")
root.geometry("500x500")

label_node = tk.Label(root, text=f"Node ID: {NODE_ID[:8]}...", font=("Arial", 10))
label_node.pack(pady=5)

label_balance = tk.Label(root, text=f"Wallet Balance: {wallet['balance']} SAXV", font=("Arial", 12))
label_balance.pack(pady=5)

btn_mine = tk.Button(root, text="Mine Block", command=mine_block_gui, bg="green", fg="white")
btn_mine.pack(pady=5)

frame_tx = tk.Frame(root)
frame_tx.pack(pady=10)

tk.Label(frame_tx, text="Receiver:").grid(row=0, column=0)
entry_receiver = tk.Entry(frame_tx)
entry_receiver.grid(row=0, column=1)

tk.Label(frame_tx, text="Amount:").grid(row=1, column=0)
entry_amount = tk.Entry(frame_tx)
entry_amount.grid(row=1, column=1)

btn_send = tk.Button(frame_tx, text="Send SAXV", command=send_saxv_gui, bg="blue", fg="white")
btn_send.grid(row=2, column=0, columnspan=2, pady=5)

text_chain = tk.Text(root, height=15)
text_chain.pack(pady=10)

update_display()
root.mainloop()