# saxv_chain_mini_v7.py
# Ultra-clean version for Pydroid 3 / Oppo A60
# SAXV Chain Mini v7 with wallet & ECDSA

import hashlib
import json
import time
from ecdsa import SigningKey, VerifyingKey, NIST384p

# ----------------------------
# Blockchain and Block Class
# ----------------------------
class Block:
    def __init__(self, index, transactions, previous_hash, timestamp=None, nonce=0):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    difficulty = 2  # adjustable for HP

    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], "0")
        self.chain.append(genesis_block)

    def last_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        if Blockchain.verify_transaction(transaction):
            self.pending_transactions.append(transaction)
            return True
        return False

    def mine_pending(self):
        if not self.pending_transactions:
            return False
        new_block = Block(
            index=self.last_block().index + 1,
            transactions=self.pending_transactions,
            previous_hash=self.last_block().hash
        )
        while not new_block.hash.startswith('0'*Blockchain.difficulty):
            new_block.nonce += 1
            new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    @staticmethod
    def verify_transaction(transaction):
        sender = transaction['sender']
        signature = bytes.fromhex(transaction['signature'])
        message = transaction['message'].encode()
        try:
            vk = VerifyingKey.from_string(bytes.fromhex(sender), curve=NIST384p)
            return vk.verify(signature, message)
        except:
            return False

# ----------------------------
# Wallet Class
# ----------------------------
class Wallet:
    def __init__(self):
        self.private_key = SigningKey.generate(curve=NIST384p)
        self.public_key = self.private_key.verifying_key

    def sign(self, message):
        return self.private_key.sign(message.encode()).hex()

    def get_address(self):
        return self.public_key.to_string().hex()

# ----------------------------
# Simple Test
# ----------------------------
if __name__ == "__main__":
    # Create blockchain
    blockchain = Blockchain()

    # Create wallets
    alice = Wallet()
    bob = Wallet()

    # Alice sends 10 SAXV to Bob
    tx = {
        "sender": alice.get_address(),
        "recipient": bob.get_address(),
        "amount": 10,
        "message": "Alice pays Bob 10 SAXV"
    }
    tx["signature"] = alice.sign(tx["message"])

    if blockchain.add_transaction(tx):
        print("Transaction added!")
    else:
        print("Transaction failed verification.")

    # Mine block
    block = blockchain.mine_pending()
    if block:
        print(f"Block #{block.index} mined with hash: {block.hash}")
    else:
        print("No transactions to mine.")

    # Display blockchain
    for blk in blockchain.chain:
        print(f"Block {blk.index}: {blk.hash}")