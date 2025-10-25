import json
import requests
import threading
import time

# ------------------------------
# RAM-based blockchain
# ------------------------------
class Block:
    def __init__(self, index, previous_hash, transactions):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.hash = self.compute_hash()

    def compute_hash(self):
        return str(hash((self.index, self.previous_hash, str(self.transactions))))

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        self.chain.append(Block(0, "0", []))

    def add_block(self, transactions):
        previous_hash = self.chain[-1].hash
        block = Block(len(self.chain), previous_hash, transactions)
        self.chain.append(block)

    def add_transaction(self, sender, receiver, amount):
        self.pending_transactions.append({
            "sender": sender,
            "receiver": receiver,
            "amount": amount
        })

    def mine_pending(self):
        if self.pending_transactions:
            self.add_block(self.pending_transactions)
            self.pending_transactions = []

    def snapshot(self):
        return {"chain": [vars(b) for b in self.chain]}

# ------------------------------
# Node & token
# ------------------------------
blockchain = Blockchain()

# Tambah transaksi dummy awal
blockchain.add_transaction("Alice", "Bob", 10)
blockchain.mine_pending()

# ------------------------------
# Kirim snapshot ke cloud
# ------------------------------
CLOUD_ENDPOINT = "https://your-cloud-server.com/upload_snapshot"  # ganti dengan server kamu

def send_snapshot():
    snapshot_data = blockchain.snapshot()
    try:
        response = requests.post(CLOUD_ENDPOINT, json=snapshot_data, timeout=10)
        if response.status_code == 200:
            print("✅ Snapshot terkirim ke cloud")
        else:
            print("⚠️ Gagal kirim snapshot:", response.status_code)
    except Exception as e:
        print("⚠️ Error kirim snapshot:", e)

# ------------------------------
# Auto snapshot periodik (default 5 menit)
# ------------------------------
def auto_snapshot(interval=300):
    while True:
        send_snapshot()
        time.sleep(interval)

threading.Thread(target=auto_snapshot, daemon=True).start()

# ------------------------------
# Demo transaksi interaktif
# ------------------------------
while True:
    cmd = input("Ketik transaksi (sender receiver amount) atau 'mine': ")
    if cmd.lower() == "mine":
        blockchain.mine_pending()
        print("✅ Block mined. Chain length:", len(blockchain.chain))
    else:
        try:
            s, r, a = cmd.split()
            blockchain.add_transaction(s, r, float(a))
            print("✅ Transaction added")
        except:
            print("⚠️ Format salah")