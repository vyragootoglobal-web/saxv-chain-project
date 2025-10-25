# v8_auto_sync.py
# SAXV Chain Mini v8 – Auto-Sync Pseudo Nodes, Mining Batch 3–5 TX
import hashlib, json, time, threading
from ecdsa import SigningKey, VerifyingKey, NIST384p

class Block:
    def __init__(self, index, txs, prev_hash):
        self.index = index
        self.transactions = txs
        self.previous_hash = prev_hash
        self.timestamp = time.time()
        self.nonce = 0
        self.hash = self.compute_hash()
    def compute_hash(self):
        return hashlib.sha256(json.dumps(self.__dict__, sort_keys=True).encode()).hexdigest()

class Blockchain:
    difficulty = 1
    max_tx_per_block = 5
    def __init__(self):
        self.chain = [Block(0, [], "0")]
        self.pending_transactions = []
    def last_block(self):
        return self.chain[-1]
    def add_tx(self, tx):
        if Blockchain.verify_tx(tx):
            self.pending_transactions.append(tx)
            return True
        return False
    def mine_pending(self):
        if not self.pending_transactions: return None
        batch = self.pending_transactions[:self.max_tx_per_block]
        new_block = Block(self.last_block().index+1, batch, self.last_block().hash)
        while not new_block.hash.startswith('0'*Blockchain.difficulty):
            new_block.nonce +=1
            new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        self.pending_transactions=self.pending_transactions[self.max_tx_per_block:]
        with open("v8_chain_backup.json","w") as f:
            json.dump([blk.__dict__ for blk in self.chain],f,indent=4)
        return new_block
    @staticmethod
    def verify_tx(tx):
        try:
            vk = VerifyingKey.from_string(bytes.fromhex(tx['sender']),curve=NIST384p)
            return vk.verify(bytes.fromhex(tx['signature']), tx['message'].encode())
        except:
            return False

# Pseudo multi-node sync
blockchain = Blockchain()
def auto_sync():
    while True:
        if blockchain.pending_transactions:
            blockchain.mine_pending()
        time.sleep(5)  # auto-sync tiap 5 detik

t = threading.Thread(target=auto_sync,daemon=True)
t.start()