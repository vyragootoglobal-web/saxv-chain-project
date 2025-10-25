# =========================================
# SAXV v5 No-GUI - No Owner, Auto Distribute
# Super-light for Pydroid 3 (Snapdragon 660 / 4GB)
# Fixed supply = 31_000_000
# =========================================

import json, hashlib, time, os

DATA_FILE = "saxv_v5_nogui.json"
DIFFICULTY = 2        # ringan -> jangan naik kalau HP lawas
MAX_SUPPLY = 31_000_000

# --- Simple Block class (light) ---
class Block:
    def __init__(self, index, tx, prev_hash, timestamp=None, nonce=0, hash_value=None):
        self.index = int(index)
        self.transactions = tx
        self.previous_hash = prev_hash
        self.timestamp = float(timestamp) if timestamp is not None else time.time()
        self.nonce = int(nonce)
        self.hash = hash_value if hash_value else self.calc_hash()

    def calc_hash(self):
        s = f"{self.index}|{self.timestamp}|{self.transactions}|{self.previous_hash}|{self.nonce}"
        return hashlib.sha256(s.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash
        }

# --- Main coin class ---
class SAXV:
    def __init__(self, max_supply=MAX_SUPPLY):
        self.max_supply = int(max_supply)
        self.total_supply = 0
        self.balances = {}
        self.chain = []
        self.load()

    # genesis if needed
    def create_genesis(self):
        g = Block(0, "Genesis", "0", nonce=0)
        g.hash = g.calc_hash()
        self.chain = [g]
        self.save()
        print("🔗 Genesis dibuat.")

    def last_hash(self):
        return self.chain[-1].hash

    # very light PoW (difficulty low)
    def add_block(self, tx, skip_pow=False):
        idx = len(self.chain)
        prev = self.last_hash()
        blk = Block(idx, tx, prev, nonce=0)
        if not skip_pow:
            # find nonce quickly (keamanan rendah but light)
            while not blk.hash.startswith("0" * DIFFICULTY):
                blk.nonce += 1
                blk.hash = blk.calc_hash()
                # throttle to avoid heavy CPU: tiny sleep every some iterations
                if blk.nonce % 20000 == 0:
                    time.sleep(0.001)
        else:
            blk.hash = blk.calc_hash()
        self.chain.append(blk)
        self.save()
        return blk

    # distribute equally to provided wallet list (no owner)
    def distribute_equal(self, wallets):
        if self.total_supply > 0:
            print("⚠️ Sudah didistribusikan sebelumnya.")
            return False
        if not wallets:
            print("❌ Daftar wallet kosong.")
            return False
        per = self.max_supply // len(wallets)
        for w in wallets:
            self.balances[w] = self.balances.get(w, 0) + per
        # note: if there's remainder it stays undistributed (keamanan simpel)
        self.total_supply = per * len(wallets)
        self.add_block(f"Mint {self.total_supply} dibagi rata ke {len(wallets)} wallet", skip_pow=True)
        print(f"💰 {self.total_supply:,} SAXV dibagi ke {len(wallets)} wallet ({per:,} each).")
        return True

    def transfer(self, a_from, a_to, amount):
        amount = int(amount)
        if self.balances.get(a_from, 0) < amount:
            print("❌ Saldo tidak cukup.")
            return False
        self.balances[a_from] -= amount
        self.balances[a_to] = self.balances.get(a_to, 0) + amount
        self.add_block(f"{a_from} -> {a_to} : {amount}")
        print(f"💸 {amount} dikirim: {a_from} -> {a_to}")
        return True

    def mine_reward(self, miner, reward=1):
        reward = int(reward)
        if self.total_supply + reward > self.max_supply:
            print("❌ Supply penuh, mining dihentikan.")
            return False
        # super light mining (find nonce)
        idx = len(self.chain)
        prev = self.last_hash()
        tx = f"Reward {reward} -> {miner}"
        nonce = 0
        while True:
            data = f"{idx}|{tx}|{prev}|{nonce}"
            h = hashlib.sha256(data.encode()).hexdigest()
            if h.startswith("0" * DIFFICULTY):
                # create block
                b = Block(idx, tx, prev, nonce=nonce)
                b.hash = h
                self.chain.append(b)
                self.total_supply += reward
                self.balances[miner] = self.balances.get(miner, 0) + reward
                self.save()
                print(f"⛏️ {miner} menambang {reward} SAXV (nonce {nonce}).")
                return True
            nonce += 1
            if nonce % 20000 == 0:
                time.sleep(0.001)

    def validate(self):
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i-1]
            if curr.previous_hash != prev.hash:
                print(f"❌ Broken link di blok {curr.index}")
                return False
            if curr.calc_hash() != curr.hash:
                print(f"❌ Hash tidak cocok di blok {curr.index}")
                return False
            if not curr.hash.startswith("0" * DIFFICULTY) and curr.index != 0:
                print(f"❌ PoW invalid di blok {curr.index}")
                return False
        print("✅ Chain valid.")
        return True

    # persistence
    def save(self):
        d = {
            "total_supply": self.total_supply,
            "balances": self.balances,
            "chain": [b.to_dict() for b in self.chain]
        }
        with open(DATA_FILE, "w") as f:
            json.dump(d, f)

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    d = json.load(f)
                self.total_supply = int(d.get("total_supply", 0))
                self.balances = {k:int(v) for k,v in d.get("balances", {}).items()}
                self.chain = []
                for b in d.get("chain", []):
                    blk = Block(b.get("index"), b.get("transactions"), b.get("previous_hash"),
                                timestamp=b.get("timestamp"), nonce=b.get("nonce"), hash_value=b.get("hash"))
                    self.chain.append(blk)
            except Exception:
                print("⚠️ File data korup. Membuat genesis baru.")
                self.create_genesis()
        else:
            self.create_genesis()

    def info(self):
        print("\n=== SAXV Info ===")
        print(f"Total Supply: {self.total_supply:,} / {self.max_supply:,}")
        print("Balances:")
        for k,v in sorted(self.balances.items(), key=lambda x:-x[1]):
            print(f"  {k}: {v:,}")
        print(f"Blocks: {len(self.chain)} (DIFFICULTY={DIFFICULTY})")
        print("=================\n")

# --------- Simple CLI demo (safe & automatic) ----------
def main_demo():
    saxv = SAXV()

    # default wallet list — bisa diubah langsung di file sebelum run
    wallets = ["wallet1", "wallet2", "wallet3", "wallet4", "wallet5", "wallet6"]

    # distribute once if not yet
    if saxv.total_supply == 0:
        saxv.distribute_equal(wallets)

    saxv.info()

    # contoh otomatis: transfer kecil + mining ringan
    saxv.transfer("wallet1", "wallet2", 500)
    saxv.mine_reward("wallet3")
    saxv.validate()
    saxv.info()

    # interactive (opsional)
    print("Mode interaktif: ketik perintah atau 'exit'")
    print("Perintah: info | validate | transfer A B amount | mine miner | exit")
    while True:
        try:
            cmd = input(">> ").strip()
        except EOFError:
            break
        if not cmd:
            continue
        if cmd == "exit":
            break
        parts = cmd.split()
        if parts[0] == "info":
            saxv.info()
        elif parts[0] == "validate":
            saxv.validate()
        elif parts[0] == "transfer" and len(parts) == 4:
            saxv.transfer(parts[1], parts[2], int(parts[3]))
        elif parts[0] == "mine" and len(parts) == 2:
            saxv.mine_reward(parts[1])
        else:
            print("Perintah tidak dikenali.")

if __name__ == "__main__":
    main_demo()