# saxv_chain_mini_v15.py
# SAXV Chain Mini V15 – Full Mini-Mainnet & Token Ready
# Optimized for Oppo A60 / Pydroid 3

import hashlib
import json
import time
from threading import Thread
import random
import gzip
from ecdsa import SigningKey, SECP256k1

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
        self.mempool = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), [], "0")
        self.chain.append(genesis_block)

    def add_new_transaction(self, transaction):
        self.mempool.append(transaction)
        if len(self.mempool) > 10:
            self.mempool = self.mempool[-10:]

    def mine_batch(self):
        if not self.mempool:
            return False
        last_block = self.chain[-1]
        batch = self.mempool[:5]
        new_block = Block(index=last_block.index + 1,
                          timestamp=time.time(),
                          transactions=batch,
                          previous_hash=last_block.hash)
        new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        self.mempool = self.mempool[5:]
        return new_block.index

    def snapshot_chain(self):
        with gzip.open("saxv_chain_snapshot.json.gz", "wt", encoding="utf-8") as f:
            json.dump([block.__dict__ for block in self.chain], f)
        print("[Snapshot] Blockchain saved to cloud-ready gzip file")

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if current.hash != current.compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

# ==== WALLET ====
class Wallet:
    def __init__(self):
        self.private_key = SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()

    def sign_transaction(self, transaction):
        tx_string = json.dumps(transaction, sort_keys=True)
        return self.private_key.sign(tx_string.encode()).hex()

# ==== NODE SIMULATION ====
blockchain = Blockchain()
node_id = random.randint(1,1000)
wallet = Wallet()
peers = ["Node1", "Node2"]

# ==== TOKEN INTEGRATION ====
token_name = "SAXV"
token_balances = {wallet.public_key.to_string().hex(): 1000}  # initial token balance

def transfer_token(to_pubkey, amount):
    sender = wallet.public_key.to_string().hex()
    if token_balances.get(sender,0) >= amount:
        token_balances[sender] -= amount
        token_balances[to_pubkey] = token_balances.get(to_pubkey,0) + amount
        tx = {"from": sender, "to": to_pubkey, "amount": amount, "token": token_name}
        tx["signature"] = wallet.sign_transaction(tx)
        blockchain.add_new_transaction(tx)
        print(f"[Token] {amount} {token_name} sent to {to_pubkey}")
    else:
        print("[Token] Insufficient balance")

# ==== NODE FUNCTIONS ====
def add_demo_transactions():
    tx_count = 1
    while True:
        tx = {"from": wallet.public_key.to_string().hex(), "to": "Bob", "amount": tx_count, "node": node_id}
        tx["signature"] = wallet.sign_transaction(tx)
        blockchain.add_new_transaction(tx)
        tx_count += 1
        time.sleep(2)

def auto_mine():
    while True:
        mined = blockchain.mine_batch()
        if mined:
            print(f"[Node {node_id}] Block {mined} mined. Total chain: {len(blockchain.chain)}")
        time.sleep(5)

def broadcast_transactions():
    while True:
        if blockchain.mempool:
            for peer in peers:
                print(f"[Node {node_id}] Broadcasting {len(blockchain.mempool)} tx to {peer}")
        time.sleep(5)

def cloud_sync_snapshot():
    while True:
        blockchain.snapshot_chain()
        time.sleep(60)

# ==== RUN NODES ====
t1 = Thread(target=add_demo_transactions)
t2 = Thread(target=auto_mine)
t3 = Thread(target=broadcast_transactions)
t4 = Thread(target=cloud_sync_snapshot)
t1.start()
t2.start()
t3.start()
t4.start()
t1.join()
t2.join()
t3.join()
t4.join()