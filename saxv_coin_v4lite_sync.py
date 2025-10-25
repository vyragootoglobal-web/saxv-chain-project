# ==============================================
# SAXV Coin v4 Lite - Cloud Sync via Sync Folder
# No Owner, Fixed Supply 31,000,000
# For Pydroid 3 (Snapdragon 660 / 4GB)
# ==============================================

import json, hashlib, time, os, shutil

# ----- CONFIG -----
DATA_FILE = "saxv_v4_data.json"           # local data file (inside Pydroid working dir)
SYNC_FOLDER = "/sdcard/Download/SAXV_SYNC"  # <-- set this to your phone's sync folder (Dropbox/Drive/etc)
SYNC_FILE = os.path.join(SYNC_FOLDER, "saxv_sync.json")
BACKUP_SUFFIX = ".bak"
DIFFICULTY = 2
MAX_SUPPLY = 31_000_000
# -------------------

class Block:
    def __init__(self, index, transactions, previous_hash, timestamp=None, nonce=0, hash_value=None):
        self.index = int(index)
        self.timestamp = float(timestamp) if timestamp is not None else time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = int(nonce)
        self.hash = hash_value if hash_value is not None else self.calculate_hash()

    def calculate_hash(self):
        s = f"{self.index}|{self.timestamp}|{self.transactions}|{self.previous_hash}|{self.nonce}"
        return hashlib.sha256(s.encode()).hexdigest()

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
    def __init__(self, max_supply=MAX_SUPPLY):
        self.max_supply = int(max_supply)
        self.total_supply = 0
        self.balances = {}
        self.chain = []
        # ensure sync folder exists if possible
        try:
            if not os.path.exists(SYNC_FOLDER):
                os.makedirs(SYNC_FOLDER, exist_ok=True)
        except Exception:
            pass
        # load local data, then try merging with sync file if present
        self.load_local()
        self.try_sync_merge()

    # ---------- blockchain basic ----------
    def create_genesis(self):
        genesis = Block(0, "Genesis Block", "0", timestamp=time.time(), nonce=0)
        genesis.hash = genesis.calculate_hash()
        self.chain = [genesis]
        self.save_all()
        print("🔗 Genesis block dibuat.")

    def last_block(self):
        return self.chain[-1]

    def add_block(self, transactions, nonce=0, skip_pow=False):
        last_hash = self.last_block().hash
        idx = len(self.chain)
        blk = Block(idx, transactions, last_hash, nonce=nonce)
        # if skip_pow True we accept the block as-is (used when merging trusted file)
        if not skip_pow:
            # very light "mining": search nonce until hash match difficulty
            n = 0
            while True:
                blk.nonce = n
                blk.hash = blk.calculate_hash()
                if blk.hash.startswith("0" * DIFFICULTY):
                    break
                n += 1
                if n % 10000 == 0:
                    time.sleep(0.0005)
        else:
            blk.hash = blk.calculate_hash()
        self.chain.append(blk)
        self.save_all()
        return blk

    # ---------- coin operations ----------
    def mint_equal(self, users):
        if self.total_supply > 0:
            print("⚠️ Koin sudah pernah dibuat.")
            return False
        if not users:
            print("❌ Tidak ada user.")
            return False
        per = self.max_supply // len(users)
        for u in users:
            self.balances[u] = self.balances.get(u, 0) + per
        self.total_supply = per * len(users)
        self.add_block(f"Mint {self.total_supply} dibagi rata ke {len(users)} user", skip_pow=True)
        print(f"💰 {self.total_supply:,} SAXV dibagi ke {len(users)} user ({per:,} each).")
        return True

    def transfer(self, sender, receiver, amount):
        amount = int(amount)
        if self.balances.get(sender, 0) < amount:
            print("❌ Saldo tidak cukup.")
            return False
        self.balances[sender] -= amount
        self.balances[receiver] = self.balances.get(receiver, 0) + amount
        self.add_block(f"{sender} -> {receiver} : {amount}")
        print(f"💸 {amount} ditransfer dari {sender} ke {receiver}")
        return True

    def mine_reward(self, miner, reward=1):
        reward = int(reward)
        if self.total_supply + reward > self.max_supply:
            print("❌ Supply penuh.")
            return False
        # simple light mining
        last_hash = self.last_block().hash
        tx = f"Reward {reward} -> {miner}"
        nonce = 0
        while True:
            data = f"{len(self.chain)}|{tx}|{last_hash}|{nonce}"
            h = hashlib.sha256(data.encode()).hexdigest()
            if h.startswith("0" * DIFFICULTY):
                # success
                self.total_supply += reward
                self.balances[miner] = self.balances.get(miner, 0) + reward
                newb = Block(len(self.chain), tx, last_hash, nonce=nonce)
                newb.hash = h
                self.chain.append(newb)
                self.save_all()
                print(f"⛏️ {miner} mined {reward} SAXV (hash {h[:10]}...)")
                return True
            nonce += 1

    # ---------- validation ----------
    def validate_chain(self):
        if not self.chain:
            return False
        for i in range(1, len(self.chain)):
            cur = self.chain[i]
            prev = self.chain[i-1]
            if cur.previous_hash != prev.hash:
                print(f"❌ Broken at block {cur.index}: prev hash mismatch.")
                return False
            if cur.calculate_hash() != cur.hash:
                print(f"❌ Invalid hash at block {cur.index}.")
                return False
            if not cur.hash.startswith("0" * DIFFICULTY) and cur.index != 0:
                print(f"❌ PoW missing at block {cur.index}.")
                return False
        print("✅ Chain valid.")
        return True

    # ---------- persistence & sync ----------
    def save_local(self):
        data = self._to_dict()
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
        # also write a timestamped backup
        try:
            shutil.copy(DATA_FILE, DATA_FILE + BACKUP_SUFFIX)
        except Exception:
            pass

    def save_sync_copy(self):
        """Copy local data to SYNC_FILE for cloud app to pick up."""
        try:
            if not os.path.exists(SYNC_FOLDER):
                os.makedirs(SYNC_FOLDER, exist_ok=True)
            shutil.copy(DATA_FILE, SYNC_FILE)
            # create a small meta file to help detection (timestamp)
            meta = {"updated": time.time(), "blocks": len(self.chain)}
            with open(SYNC_FILE + ".meta", "w") as m:
                json.dump(meta, m)
        except Exception as e:
            print("⚠️ Gagal menyalin ke folder sync:", str(e))

    def save_all(self):
        self.save_local()
        self.save_sync_copy()

    def load_local(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    d = json.load(f)
                self._load_from_dict(d)
                return
            except Exception:
                print("⚠️ Local data korup / tidak bisa dibaca. Membuat baru.")
        # if fail -> create genesis
        self.create_genesis()

    def load_sync_file(self):
        if os.path.exists(SYNC_FILE):
            try:
                with open(SYNC_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                # try reading backup file
                try:
                    with open(SYNC_FILE + BACKUP_SUFFIX, "r") as f:
                        return json.load(f)
                except Exception:
                    return None
        return None

    def try_sync_merge(self):
        """Attempt gentle merge: prefer chain with more blocks or newer meta timestamp."""
        sync_data = self.load_sync_file()
        if not sync_data:
            return False
        try:
            local_blocks = len(self.chain)
            sync_blocks = len(sync_data.get("chain", []))
            # prefer bigger chain; if equal, prefer newer meta (if meta exists)
            use_sync = False
            if sync_blocks > local_blocks:
                use_sync = True
            elif sync_blocks == local_blocks:
                # check meta timestamp
                try:
                    with open(SYNC_FILE + ".meta", "r") as m:
                        meta = json.load(m)
                        sync_time = meta.get("updated", 0)
                except Exception:
                    sync_time = 0
                # local file mtime
                try:
                    local_time = os.path.getmtime(DATA_FILE)
                except Exception:
                    local_time = 0
                if sync_time > local_time:
                    use_sync = True
            if use_sync:
                # backup local
                try:
                    shutil.copy(DATA_FILE, DATA_FILE + ".localbak")
                except Exception:
                    pass
                # load sync into current state
                self._load_from_dict(sync_data)
                # save local copy (overwrite) to keep consistent
                self.save_local()
                print("🔁 Sinkronisasi: memakai chain dari folder sync.")
                return True
        except Exception:
            pass
        return False

    def _to_dict(self):
        return {
            "total_supply": self.total_supply,
            "balances": self.balances,
            "chain": [b.to_dict() for b in self.chain]
        }

    def _load_from_dict(self, d):
        self.total_supply = int(d.get("total_supply", 0))
        self.balances = {k:int(v) for k,v in d.get("balances", {}).items()}
        self.chain = []
        for b in d.get("chain", []):
            blk = Block(b.get("index"), b.get("transactions"), b.get("previous_hash"),
                        timestamp=b.get("timestamp"), nonce=b.get("nonce"), hash_value=b.get("hash"))
            self.chain.append(blk)
        # if chain empty, create genesis
        if not self.chain:
            self.create_genesis()

    # ---------- info ----------
    def info(self):
        print("\n===== SAXV v4 Lite =====")
        print(f"Total Supply: {self.total_supply:,} / {self.max_supply:,}")
        print("Balances (sample up to 20):")
        shown = 0
        for k,v in sorted(self.balances.items(), key=lambda x:-x[1]):
            print(f"  {k}: {v:,}")
            shown += 1
            if shown >= 20: break
        print(f"Blocks: {len(self.chain)} | DIFFICULTY: {DIFFICULTY}")
        print("========================\n")


# ---------------- DEMO RUN (automatic) ----------------
if __name__ == "__main__":
    saxv = SAXVCoin()
    # If not minted yet, distribute equally among sample users
    if saxv.total_supply == 0:
        users = ["alice", "bob", "cara", "dedi", "erik", "fiona"]
        saxv.mint_equal(users)

    saxv.info()
    # simulate small actions
    saxv.transfer("alice", "bob", 250)
    saxv.mine_reward("cara")
    saxv.validate_chain()
    saxv.info()
    print("✅ Sim selesai. Periksa folder sinkronisasi kamu:", SYNC_FOLDER)