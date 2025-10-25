# saxv_chain_mini_v10.py
# SAXV Chain Mini V10 – Auto Mining Batch
# Optimized for Oppo A60 / Pydroid 3

import hashlib
import json
import time
from threading import Thread
import random

# ==== BLOCKCHAIN ====
class Block:
    def __init__(self, index, timestamp, transactions, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.unconfirmed_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), [], "0")
        self.chain.append(genesis_block)

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def mine_batch(self):
        if not self.unconfirmed_transactions:
            return False
        last_block = self.chain[-1]
        batch = self.unconfirmed_transactions[:5]  # max 5 tx per block
        new_block = Block(index=last_block.index + 1,
                          timestamp=time.time(),
                          transactions=batch,
                          previous_hash=last_block.hash)
        new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        self.unconfirmed_transactions = self.unconfirmed_transactions[5:]
        return new_block.index

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if current.hash != current.compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

# ==== NODE SIMULATION ====
blockchain = Blockchain()
node_id = random.randint(1, 1000)

def add_demo_transactions():
    tx_count = 1
    while True:
        tx = {"from": "Alice", "to": "Bob", "amount": tx_count, "node": node_id}
        blockchain.add_new_transaction(tx)
        tx_count += 1
        time.sleep(2)

def auto_mine():
    while True:
        mined = blockchain.mine_batch()
        if mined:
            print(f"[Node {node_id}] Block {mined} mined. Total chain: {len(blockchain.chain)}")
        time.sleep(5)  # mining interval

def broadcast_transactions():
    while True:
        if blockchain.unconfirmed_transactions:
            print(f"[Node {node_id}] Broadcasting {len(blockchain.unconfirmed_transactions)} tx")
        time.sleep(5)

# ==== RUN NODES ====
t1 = Thread(target=add_demo_transactions)
t2 = Thread(target=auto_mine)
t3 = Thread(target=broadcast_transactions)
t1.start()
t2.start()
t3.start()
t1.join()
t2.join()
t3.join()