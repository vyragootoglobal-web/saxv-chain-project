# ======================================
# SAXV Coin v3 Lite - No Owner Version
# Fixed Supply: 31,000,000 SAXV
# Super Ringan, Aman, Anti Error/Hang
# ======================================

import json, hashlib, time, os

DATA_FILE = "saxv_v3lite.json"
DIFFICULTY = 2  # aman untuk HP (tidak bikin panas / hang)

class Block:
    def __init__(self, index, transactions, previous_hash, timestamp=None, nonce=0):
        self.index = index
        self.timestamp = timestamp if timestamp else time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = f"{self.index}{self.timestamp}{self.transactions}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_data.encode()).hexdigest()


class SAXVCoin:
    def __init__(self, max_supply=31_000_000):
        self.max_supply = max_supply
        self.total_supply = 0
        self.balances = {}
        self.chain = []
        self.load_data()

    # ======== Blockchain System ========
    def create_genesis(self):
        genesis = Block(0, "Genesis Block", "0")
        self.chain = [genesis]
        self.save_data()
        print("🔗 Genesis block dibuat.")

    def last_block(self):
        return self.chain[-1]

    def add_block(self, transactions):
        last_hash = self.last_block().hash
        new_block = Block(len(self.chain), transactions, last_hash)
        self.chain.append(new_block)
        self.save_data()
        print(f"✅ Blok #{new_block.index} ditambahkan ({new_block.hash[:10]}...)")

    # ======== Koin System ========
    def mint_equal(self, user_list):
        """Bagi rata 31 juta ke semua user (sekali saja)."""
        if self.total_supply > 0:
            print("⚠️ Koin sudah pernah dibuat sebelumnya.")
            return
        jumlah_user = len(user_list)
        if jumlah_user == 0:
            print("❌ Tidak ada user.")
            return
        per_user = self.max_supply // jumlah_user
        for user in user_list:
            self.balances[user] = per_user
        self.total_supply = per_user * jumlah_user
        self.add_block(f"Mint {self.total_supply} SAXV dibagi rata ke {jumlah_user} user")
        print(f"💰 Total 31,000,000 SAXV dibagi rata ke {jumlah_user} user.")
        self.save_data()

    def transfer(self, sender, receiver, amount):
        if self.balances.get(sender, 0) < amount:
            print("❌ Saldo tidak cukup.")
            return
        self.balances[sender] -= amount
        self.balances[receiver] = self.balances.get(receiver, 0) + amount
        self.add_block(f"{sender} kirim {amount} SAXV ke {receiver}")
        print(f"💸 {amount} SAXV ditransfer dari {sender} ke {receiver}")
        self.save_data()

    # ======== Mining Simulasi ========
    def mine_block(self, miner):
        reward = 1
        if self.total_supply + reward > self.max_supply:
            print("❌ Supply penuh, tidak bisa mining.")
            return
        # proses ringan (simulasi, tidak berat)
        last_hash = self.last_block().hash
        tx = f"Mining reward {reward} ke {miner}"
        nonce = 0
        while True:
            data = f"{len(self.chain)}{tx}{last_hash}{nonce}"
            block_hash = hashlib.sha256(data.encode()).hexdigest()
            if block_hash.startswith("0" * DIFFICULTY):
                self.total_supply += reward
                self.balances[miner] = self.balances.get(miner, 0) + reward
                new_block = Block(len(self.chain), tx, last_hash, nonce=nonce)
                self.chain.append(new_block)
                self.save_data()
                print(f"⛏️ {miner} menambang 1 SAXV (hash {block_hash[:10]}...)")
                break
            nonce += 1

    # ======== Validasi ========
    def validate_chain(self):
        for i in range(1, len(self.chain)):
            prev = self.chain[i-1]
            curr = self.chain[i]
            if curr.previous_hash != prev.hash:
                print(f"❌ Error di blok #{i}: previous hash tidak cocok.")
                return False
            if curr.calculate_hash() != curr.hash:
                print(f"❌ Error di blok #{i}: hash tidak valid.")
                return False
        print("✅ Chain valid & aman.")
        return True

    # ======== Data Save / Load ========
    def save_data(self):
        data = {
            "total_supply": self.total_supply,
            "balances": self.balances,
            "chain": [{
                "index": b.index,
                "timestamp": b.timestamp,
                "transactions": b.transactions,
                "previous_hash": b.previous_hash,
                "nonce": b.nonce,
                "hash": b.hash
            } for b in self.chain]
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    d = json.load(f)
                    self.total_supply = d.get("total_supply", 0)
                    self.balances = d.get("balances", {})
                    self.chain = []
                    for b in d.get("chain", []):
                        blk = Block(
                            b["index"],
                            b["transactions"],
                            b["previous_hash"],
                            b["timestamp"],
                            b["nonce"]
                        )
                        blk.hash = b["hash"]
                        self.chain.append(blk)
            except:
                print("⚠️ File rusak, buat ulang.")
                self.create_genesis()
        if not self.chain:
            self.create_genesis()

    # ======== Info ========
    def info(self):
        print("\n===== INFO SAXV COIN =====")
        print(f"Total Supply: {self.total_supply:,} / {self.max_supply:,}")
        print("Daftar Saldo:")
        for user, bal in self.balances.items():
            print(f"  {user}: {bal:,} SAXV")
        print(f"Jumlah Blok: {len(self.chain)}\n============================\n")


# ======== DEMO OTOMATIS ========
if __name__ == "__main__":
    saxv = SAXVCoin()

    # Buat user contoh (tanpa owner)
    users = ["user1", "user2", "user3", "user4", "user5"]

    # Mint sekali jika belum pernah
    if saxv.total_supply == 0:
        saxv.mint_equal(users)

    saxv.info()

    # Simulasi transfer dan mining
    saxv.transfer("user1", "user2", 500)
    saxv.mine_block("user3")
    saxv.validate_chain()
    saxv.info()