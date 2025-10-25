# saxv_chain_mini_v8.py
# SAXV Chain Mini V8 – Local Blockchain for HP
# Ultra-lightweight, optimized for Oppo A60 / Pydroid 3

import hashlib
import json
import time
from threading import Thread

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

    def mine(self):
        if not self.unconfirmed_transactions:
            return False
        last_block = self.chain[-1]
        new_block = Block(index=last_block.index + 1,
                          timestamp=time.time(),
                          transactions=self.unconfirmed_transactions[:3],  # max 3 tx per block
                          previous_hash=last_block.hash)
        new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        self.unconfirmed_transactions = self.unconfirmed_transactions[3:]
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

def add_demo_transactions():
    tx_count = 1
    while True:
        blockchain.add_new_transaction({"from": "Alice", "to": "Bob", "amount": tx_count})
        tx_count += 1
        time.sleep(2)  # reduce CPU load

def auto_mine():
    while True:
        mined = blockchain.mine()
        if mined:
            print(f"Block {mined} mined. Total chain: {len(blockchain.chain)}")
        time.sleep(5)  # mining interval

# ==== RUN NODES ====
t1 = Thread(target=add_demo_transactions)
t2 = Thread(target=auto_mine)
t1.start()
t2.start()
t1.join()
t2.join()