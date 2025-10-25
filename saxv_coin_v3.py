# ==============================================
# SAXV Coin v3.0 - Verification & Chain Validation
# Lightweight for Pydroid 3 (Snapdragon 660 / 4GB)
# Fixed supply 31_000_000
# ==============================================

import json, hashlib, os, time

DATA_FILE = "saxv_chain_v3.json"
DIFFICULTY = 2   # very small so phone tidak ngadat (ubah ke 3 kalau mau lebih kuat)

class Block:
    def __init__(self, index, transactions, previous_hash, timestamp=None, nonce=0, hash_value=None):
        self.index = int(index)
        self.timestamp = float(timestamp) if timestamp is not None else time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = int(nonce)
        # calculate hash if none provided (useful for fresh block)
        self.hash = hash_value if hash_value is not None else self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}|{self.timestamp}|{self.transactions}|{self.previous_hash}|{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

class SAXVCoin:
    def __init__(self, max_supply=31_000_000):
        self.max_supply = int(max_supply)
        self.total_supply = 0
        self.balances = {}
        self.chain = []
        self.load_data()

    # ---------- Blockchain ----------
    def create_genesis_block(self):
        print("🔗 Membuat genesis block...")
        genesis = Block(0, "Genesis Block", "0", timestamp=time.time(), nonce=0)
        genesis.hash = genesis.calculate_hash()
        self.chain = [genesis]
        self.save_data()

    def get_last_block(self):
        return self.chain[-1]

    def add_block_object(self, block_obj):
        self.chain.append(block_obj)
        self.save_data()
        print(f"✅ Blok #{block_obj.index} ditambahkan (hash {block_obj.hash[:12]}...)")

    def mine_new_block(self, transactions):
        last = self.get_last_block()
        index = last.index + 1
        previous_hash = last.hash
        nonce = 0
        while True:
            candidate = Block(index, transactions, previous_hash, nonce=nonce)
            if candidate.hash.startswith("0" * DIFFICULTY):
                self.add_block_object(candidate)
                return candidate
            nonce += 1
            # very light throttle to avoid 100% CPU spiking on some phones
            if nonce % 10000 == 0:
                time.sleep(0.001)

    # ---------- Coin actions ----------
    def mint(self, address, amount):
        amount = int(amount)
        if self.total_supply + amount > self.max_supply:
            print("❌ Gagal mint: melebihi max supply.")
            return False
        self.total_supply += amount
        self.balances[address] = self.balances.get(address, 0) + amount
        tx = f"Mint {amount} SAXV -> {address}"
        self.mine_new_block(tx)
        print(f"✅ Mint {amount} ke {address}")
        self.save_data()
        return True

    def transfer(self, sender, receiver, amount):
        amount = int(amount)
        if self.balances.get(sender, 0) < amount:
            print("❌ Gagal transfer: saldo tidak cukup.")
            return False
        self.balances[sender] -= amount
        self.balances[receiver] = self.balances.get(receiver, 0) + amount
        tx = f"{sender} -> {receiver} : {amount} SAXV"
        self.mine_new_block(tx)
        print(f"💸 Transfer {amount} dari {sender} ke {receiver}")
        self.save_data()
        return True

    def mine_reward(self, miner, reward=1):
        reward = int(reward)
        if self.total_supply + reward > self.max_supply:
            print("❌ Tidak bisa mining: supply penuh.")
            return False
        self.total_supply += reward
        self.balances[miner] = self.balances.get(miner, 0) + reward
        tx = f"Reward {reward} -> {miner}"
        self.mine_new_block(tx)
        print(f"⛏️ {miner} menerima reward {reward} SAXV")
        self.save_data()
        return True

    # ---------- Validation ----------
    def validate_chain(self):
        if not self.chain:
            print("⚠️ Chain kosong.")
            return False
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i-1]
            # 1) previous hash link
            if current.previous_hash != prev.hash:
                print(f"❌ Broken link di blok #{current.index}: previous_hash mismatch.")
                return False
            # 2) hash correctness
            recalculated = current.calculate_hash()
            if recalculated != current.hash:
                print(f"❌ Hash tidak valid di blok #{current.index}.")
                return False
            # 3) proof-of-work check
            if not current.hash.startswith("0" * DIFFICULTY):
                print(f"❌ PoW tidak valid di blok #{current.index}.")
                return False
        print("✅ Chain valid.")
        return True

    def repair_chain(self):
        """Try to repair chain by recalculating hashes and re-mining light if needed.
           WARNING: This will change hashes and is only for local/testing chains."""
        if not self.chain:
            print("⚠️ Tidak ada yang perlu diperbaiki.")
            return False
        repaired = False
        for i in range(len(self.chain)):
            b = self.chain[i]
            # recalc hash with current nonce; if mismatches or not meet PoW, re-mine
            recalced = b.calculate_hash()
            if recalced != b.hash or not b.hash.startswith("0" * DIFFICULTY):
                print(f"🔧 Memperbaiki blok #{b.index}...")
                # simple re-mine starting from current nonce
                nonce = 0
                while True:
                    candidate = Block(b.index, b.transactions, b.previous_hash, timestamp=b.timestamp, nonce=nonce)
                    if candidate.calculate_hash().startswith("0" * DIFFICULTY):
                        candidate.hash = candidate.calculate_hash()
                        self.chain[i] = candidate
                        repaired = True
                        break
                    nonce += 1
        if repaired:
            # ensure links are consistent: update previous_hash of next blocks
            for j in range(1, len(self.chain)):
                self.chain[j].previous_hash = self.chain[j-1].hash
            self.save_data()
            print("✅ Perbaikan selesai, data disimpan.")
        else:
            print("ℹ️ Tidak ditemukan masalah besar.")
        return repaired

    # ---------- Persistence ----------
    def save_data(self):
        data = {
            "total_supply": self.total_supply,
            "balances": self.balances,
            "chain": [b.to_dict() for b in self.chain]
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    d = json.load(f)
                    self.total_supply = int(d.get("total_supply", 0))
                    self.balances = {k:int(v) for k,v in d.get("balances", {}).items()}
                    chain_list = d.get("chain", [])
                    self.chain = []
                    for b in chain_list:
                        # construct Block from dict safely
                        block = Block(
                            b.get("index"),
                            b.get("transactions"),
                            b.get("previous_hash"),
                            timestamp=b.get("timestamp"),
                            nonce=b.get("nonce"),
                            hash_value=b.get("hash")
                        )
                        self.chain.append(block)
            except Exception as e:
                print("⚠️ Data rusak atau tak terbaca. Membuat data baru.", str(e))
                self.chain = []
        if not self.chain:
            self.create_genesis_block()

    # ---------- Info ----------
    def info(self):
        print("\n===== SAXV v3 INFO =====")
        print(f"Total Supply: {self.total_supply:,} / {self.max_supply:,}")
        print("Balances:")
        for k,v in self.balances.items():
            print(f"  {k}: {v:,}")
        print(f"Blocks: {len(self.chain)} (difficulty {DIFFICULTY})")
        print("========================\n")

# ---------------- CLI Demo (light) ----------------
def demo_cli():
    saxv = SAXVCoin()
    # ensure minted once
    if saxv.total_supply == 0:
        saxv.mint("owner_wallet", 31_000_000)

    saxv.info()
    print("Commands: mint, transfer, mine, validate, repair, info, exit")
    while True:
        cmd = input(">> ").strip().lower()
        if cmd == "exit":
            break
        elif cmd == "info":
            saxv.info()
        elif cmd == "validate":
            saxv.validate_chain()
        elif cmd == "repair":
            saxv.repair_chain()
        elif cmd.startswith("mint"):
            # usage: mint addr amount
            parts = cmd.split()
            if len(parts) == 3:
                saxv.mint(parts[1], int(parts[2]))
            else:
                print("Usage: mint <addr> <amount>")
        elif cmd.startswith("transfer"):
            # usage: transfer sender receiver amount
            parts = cmd.split()
            if len(parts) == 4:
                saxv.transfer(parts[1], parts[2], int(parts[3]))
            else:
                print("Usage: transfer <sender> <receiver> <amount>")
        elif cmd.startswith("mine"):
            parts = cmd.split()
            if len(parts) == 2:
                saxv.mine_reward(parts[1])
            else:
                print("Usage: mine <miner_address>")
        else:
            print("Unknown command.")

if __name__ == "__main__":
    demo_cli()