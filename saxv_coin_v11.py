import hashlib
import json
import time
from uuid import uuid4
import threading
import requests
import tkinter as tk
from tkinter import messagebox
from flask import Flask, jsonify, request
from multiprocessing import Process

# ---------------------------
# CONFIG
# ---------------------------
SUPPLY = 31_000_000
MINING_REWARD = 10
NODE_ID = str(uuid4()).replace('-', '')
AUTO_MINING_INTERVAL = 15  # detik
AUTO_TX_INTERVAL = 20      # detik
AUTO_TX_RECEIVER = 'reward_address_123'

# ---------------------------
# BLOCKCHAIN CLASS
# ---------------------------
class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain)+1,
            'timestamp': time.time(),
            'transactions': self.transactions,
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.transactions=[]
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof=1
        while True:
            hash_op = hashlib.sha3_512(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_op[:4]=='0000':
                return new_proof
            new_proof+=1

    def hash(self, block):
        return hashlib.sha3_512(json.dumps(block, sort_keys=True).encode()).hexdigest()

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,'receiver': receiver,'amount': amount})
        return self.get_previous_block()['index']+1

    def is_chain_valid(self, chain=None):
        if chain is None:
            chain = self.chain
        prev_block = chain[0]
        index=1
        while index<len(chain):
            block=chain[index]
            if block['previous_hash']!=self.hash(prev_block):
                return False
            prev_proof=prev_block['proof']
            proof=block['proof']
            hash_op=hashlib.sha3_512(str(proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_op[:4]!='0000':
                return False
            prev_block=block
            index+=1
        return True

# ---------------------------
# NODE & WALLET
# ---------------------------
blockchain=Blockchain()
wallet={'address': NODE_ID,'balance': SUPPLY}
nodes=set()
node_status = {}

# ---------------------------
# FLASK SERVER
# ---------------------------
app=Flask(__name__)

@app.route('/mine_block',methods=['GET'])
def mine_block():
    prev_block=blockchain.get_previous_block()
    prev_proof=prev_block['proof']
    proof=blockchain.proof_of_work(prev_proof)
    prev_hash=blockchain.hash(prev_block)
    blockchain.add_transaction("SYSTEM",wallet['address'],MINING_REWARD)
    block=blockchain.create_block(proof,prev_hash)
    wallet['balance']+=MINING_REWARD
    return jsonify({'message':'Block mined!','index':block['index']}),200

@app.route('/add_transaction',methods=['POST'])
def add_transaction():
    tx=request.get_json()
    required=['sender','receiver','amount']
    if not all(k in tx for k in required):
        return 'Missing data',400
    blockchain.add_transaction(tx['sender'],tx['receiver'],tx['amount'])
    return jsonify({'message':'Transaction added'}),201

@app.route('/get_chain',methods=['GET'])
def get_chain():
    return jsonify({'chain':blockchain.chain,'length':len(blockchain.chain)}),200

@app.route('/connect_node',methods=['POST'])
def connect_node():
    node=request.get_json().get('node_address')
    if node:
        nodes.add(node)
        node_status[node] = 'unknown'
        return jsonify({'message':'Node connected','total_nodes':list(nodes)}),201
    return 'No node address',400

# ---------------------------
# SYNC & AUTO FUNCTIONS
# ---------------------------
def sync_chain():
    global blockchain, node_status
    for node in nodes:
        try:
            r=requests.get(f"{node}/get_chain",timeout=3)
            if r.status_code==200:
                length=r.json()['length']
                chain=r.json()['chain']
                if length>len(blockchain.chain) and blockchain.is_chain_valid(chain):
                    blockchain.chain=chain
                node_status[node] = 'online'
            else:
                node_status[node] = 'offline'
        except:
            node_status[node] = 'offline'
    threading.Timer(10.0,sync_chain).start()

def auto_mining():
    try:
        requests.get('http://127.0.0.1:5000/mine_block')
        wallet['balance']+=MINING_REWARD
    except:
        pass
    threading.Timer(AUTO_MINING_INTERVAL,auto_mining).start()

def auto_transaction():
    if wallet['balance']>=50:
        blockchain.add_transaction(wallet['address'],AUTO_TX_RECEIVER,50)
        wallet['balance']-=50
    threading.Timer(AUTO_TX_INTERVAL,auto_transaction).start()

def run_flask():
    sync_chain()
    auto_mining()
    auto_transaction()
    app.run(host='0.0.0.0',port=5000)

# ---------------------------
# GUI
# ---------------------------
def mine_gui():
    try:
        requests.get('http://127.0.0.1:5000/mine_block')
        wallet['balance']+=MINING_REWARD
        update_display()
        messagebox.showinfo("Mining","Block mined!")
    except:
        messagebox.showerror("Error","Server belum running!")

def send_gui():
    receiver=entry_receiver.get()
    try:
        amount=int(entry_amount.get())
    except:
        messagebox.showerror("Error","Jumlah harus angka!")
        return
    if wallet['balance']<amount:
        messagebox.showerror("Error","Saldo tidak cukup!")
        return
    blockchain.add_transaction(wallet['address'],receiver,amount)
    wallet['balance']-=amount
    update_display()
    messagebox.showinfo("Transaction",f"{amount} SAXV dikirim ke {receiver}")

def update_display():
    label_balance.config(text=f"Wallet Balance: {wallet['balance']} SAXV")
    text_chain.delete(1.0,tk.END)
    for block in blockchain.chain:
        text_chain.insert(tk.END,f"Index:{block['index']} | TX:{len(block['transactions'])}\n")
    text_nodes.delete(1.0,tk.END)
    for node,status in node_status.items():
        text_nodes.insert(tk.END,f"{node} : {status}\n")

def run_gui():
    root=tk.Tk()
    root.title("SAXV Node V11 Full Auto GUI")
    root.geometry("600x600")

    tk.Label(root,text=f"Node ID: {NODE_ID[:8]}...",font=("Arial",10)).pack(pady=5)
    global label_balance
    label_balance=tk.Label(root,text=f"Wallet Balance: {wallet['balance']} SAXV",font=("Arial",12))
    label_balance.pack(pady=5)

    tk.Button(root,text="Mine Block",command=mine_gui,bg="green",fg="white").pack(pady=5)

    frame_tx=tk.Frame(root)
    frame_tx.pack(pady=10)
    tk.Label(frame_tx,text="Receiver:").grid(row=0,column=0)
    global entry_receiver
    entry_receiver=tk.Entry(frame_tx)
    entry_receiver.grid(row=0,column=1)
    tk.Label(frame_tx,text="Amount:").grid(row=1,column=0)
    global entry_amount
    entry_amount=tk.Entry(frame_tx)
    entry_amount.grid(row=1,column=1)
    tk.Button(frame_tx,text="Send SAXV",command=send_gui,bg="blue",fg="white").grid(row=2,column=0,columnspan=2,pady=5)

    global text_chain
    text_chain=tk.Text(root,height=15)
    text_chain.pack(pady=10)

    tk.Label(root,text="Network Nodes Status:",font=("Arial",10)).pack()
    global text_nodes
    text_nodes=tk.Text(root,height=8)
    text_nodes.pack(pady=5)

    update_display()
    root.mainloop()

# ---------------------------
# RUN SERVER & GUI
# ---------------------------
if __name__=="__main__":
    p=Process(target=run_flask)
    p.start()
    run_gui()