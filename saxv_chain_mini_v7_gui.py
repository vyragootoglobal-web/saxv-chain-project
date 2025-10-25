# saxv_chain_mini_v7_gui.py
# SAXV Chain Mini v7 Ultra-Light GUI for HP
# Tkinter GUI, single blockchain, pseudo multi-node, ECDSA

import hashlib
import json
import time
from ecdsa import SigningKey, VerifyingKey, NIST384p
import tkinter as tk
from tkinter import messagebox

# ----------------------------
# Blockchain Classes
# ----------------------------
class Block:
    def __init__(self, index, transactions, previous_hash, timestamp=None, nonce=0):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    difficulty = 1  # ringan untuk HP

    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], "0")
        self.chain.append(genesis_block)

    def last_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        if Blockchain.verify_transaction(transaction):
            self.pending_transactions.append(transaction)
            return True
        return False

    def mine_pending(self):
        if not self.pending_transactions:
            return None
        new_block = Block(
            index=self.last_block().index + 1,
            transactions=self.pending_transactions,
            previous_hash=self.last_block().hash
        )
        while not new_block.hash.startswith('0'*Blockchain.difficulty):
            new_block.nonce += 1
            new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    @staticmethod
    def verify_transaction(transaction):
        sender = transaction['sender']
        signature = bytes.fromhex(transaction['signature'])
        message = transaction['message'].encode()
        try:
            vk = VerifyingKey.from_string(bytes.fromhex(sender), curve=NIST384p)
            return vk.verify(signature, message)
        except:
            return False

# ----------------------------
# Wallet Class
# ----------------------------
class Wallet:
    def __init__(self):
        self.private_key = SigningKey.generate(curve=NIST384p)
        self.public_key = self.private_key.verifying_key

    def sign(self, message):
        return self.private_key.sign(message.encode()).hex()

    def get_address(self):
        return self.public_key.to_string().hex()

# ----------------------------
# GUI Functions
# ----------------------------
blockchain = Blockchain()
wallets = {}

def create_wallet():
    w = Wallet()
    wallets[w.get_address()] = w
    wallet_list.insert(tk.END, w.get_address())
    messagebox.showinfo("Wallet Created", f"New wallet created!\nAddress:\n{w.get_address()}")

def send_saxv():
    sender_addr = sender_entry.get()
    recipient_addr = recipient_entry.get()
    amount = amount_entry.get()
    message = f"{sender_addr} pays {recipient_addr} {amount} SAXV"

    if sender_addr not in wallets:
        messagebox.showerror("Error", "Sender wallet not found!")
        return

    tx = {
        "sender": sender_addr,
        "recipient": recipient_addr,
        "amount": float(amount),
        "message": message
    }
    tx["signature"] = wallets[sender_addr].sign(message)

    if blockchain.add_transaction(tx):
        messagebox.showinfo("Success", "Transaction added!")
    else:
        messagebox.showerror("Error", "Transaction failed verification!")

def mine_block():
    block = blockchain.mine_pending()
    if block:
        messagebox.showinfo("Mining Success", f"Block #{block.index} mined!\nHash: {block.hash}")
        blockchain_text.delete("1.0", tk.END)
        for blk in blockchain.chain:
            blockchain_text.insert(tk.END, f"Block {blk.index}: {blk.hash}\n")
    else:
        messagebox.showinfo("Info", "No transactions to mine.")

# ----------------------------
# GUI Layout
# ----------------------------
root = tk.Tk()
root.title("SAXV Chain Mini v7 GUI")

# Wallet frame
wallet_frame = tk.Frame(root)
wallet_frame.pack(pady=10)
tk.Button(wallet_frame, text="Create Wallet", command=create_wallet).pack()
wallet_list = tk.Listbox(wallet_frame, width=80)
wallet_list.pack()

# Transaction frame
tx_frame = tk.Frame(root)
tx_frame.pack(pady=10)
tk.Label(tx_frame, text="Sender Address").grid(row=0, column=0)
sender_entry = tk.Entry(tx_frame, width=80)
sender_entry.grid(row=0, column=1)

tk.Label(tx_frame, text="Recipient Address").grid(row=1, column=0)
recipient_entry = tk.Entry(tx_frame, width=80)
recipient_entry.grid(row=1, column=1)

tk.Label(tx_frame, text="Amount").grid(row=2, column=0)
amount_entry = tk.Entry(tx_frame, width=80)
amount_entry.grid(row=2, column=1)

tk.Button(tx_frame, text="Send SAXV", command=send_saxv).grid(row=3, column=0, columnspan=2, pady=5)

# Mining frame
mine_frame = tk.Frame(root)
mine_frame.pack(pady=10)
tk.Button(mine_frame, text="Mine Block", command=mine_block).pack()

# Blockchain display
blockchain_text = tk.Text(root, height=10, width=100)
blockchain_text.pack(pady=10)

root.mainloop()