# ============================================
#  SAXV Coin v2.0 - Mini Blockchain Edition
#  Lightweight, no lag, fixed 31M supply
# ============================================

import json, hashlib, os, time

DATA_FILE = "saxv_chain_data.json"

class Block:
    def __init__(self, index, transactions, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.transactions}{self.previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()


class SAXVCoin:
    def __init__(self, max_supply=31_000_000):
        self.max_supply = max_supply
        self.total_supply = 0
        self.balances = {}
        self.chain = []
        self.load_data()

    # ===== Blockchain System =====
    def create_genesis_block(self):
        print("🔗 Membuat blok pertama (genesis)...")
        genesis_block = Block(0, "Genesis Block", "0")
        self.chain.append(genesis_block)
        self.save_data()

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, transactions):
        last_hash = self.get_last_block().hash
        new_block = Block(len(self.chain), transactions, last_hash)
        self.chain.append(new_block)
        self.save_data()
        print(f"✅ Blok #{new_block.index} berhasil ditambahkan ke chain.")

    # ===== Koin System =====
    def mint(self, address, amount):
        if self.total_supply + amount > self.max_supply:
            print("❌ Supply sudah mencapai batas maksimal!")
            return
        self.total_supply += amount
        self.balances[address] = self.balances.get(address, 0) + amount
        self.add_block(f"Mint {amount} SAXV ke {address}")
        print(f"✅ Mint {amount} SAXV ke {address}")

    def transfer(self, sender, receiver, amount):
        if self.balances.get(sender, 0) < amount:
            print("❌ Saldo tidak cukup!")
            return
        self.balances[sender] -= amount
        self.balances[receiver] = self.balances.get(receiver, 0) + amount
        self.add_block(f"{sender} kirim {amount} SAXV ke {receiver}")
        print(f"💸 {amount} SAXV dikirim dari {sender} ke {receiver}")

    # ===== Mining Simulasi =====
    def mine_block(self, miner):
        reward = 1  # reward kecil biar stabil
        if self.total_supply + reward <= self.max_supply:
            self.total_supply += reward
            self.balances[miner] = self.balances.get(miner, 0) + reward
            self.add_block(f"Mining reward {reward} SAXV ke {miner}")
            print(f"⛏️ {miner} berhasil menambang 1 SAXV!")
        else:
            print("❌ Supply penuh, tidak bisa mining lagi.")

    # ===== Data Save/Load =====
    def save_data(self):
        data = {
            "total_supply": self.total_supply,
            "balances": self.balances,
            "chain": [{
                "index": b.index,
                "timestamp": b.timestamp,
                "transactions": b.transactions,
                "previous_hash": b.previous_hash,
                "hash": b.hash
            } for b in self.chain]
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.total_supply = data.get("total_supply", 0)
                    self.balances = data.get("balances", {})
                    self.chain = [Block(**b) for b in data.get("chain", [])]
            except:
                print("⚠️ File rusak, reset data baru.")
                self.chain = []
        if not self.chain:
            self.create_genesis_block()

    def info(self):
        print("\n===== INFO SAXV COIN =====")
        print(f"Total Supply: {self.total_supply:,} / {self.max_supply:,}")
        print("Saldo Wallet:")
        for addr, bal in self.balances.items():
            print(f"  {addr}: {bal:,} SAXV")
        print(f"Total Block: {len(self.chain)}\n")


# ===== Jalankan Demo =====
if __name__ == "__main__":
    saxv = SAXVCoin()

    if saxv.total_supply == 0:
        saxv.mint("owner_wallet", 31_000_000)

    saxv.info()
    saxv.transfer("owner_wallet", "user1", 500)
    saxv.mine_block("miner1")
    saxv.info()