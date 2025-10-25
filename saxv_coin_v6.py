import hashlib
import json
import time
from uuid import uuid4

# ---------------------------
# CONFIG
# ---------------------------
SUPPLY = 31_000_000  # Total SAXV
MINING_REWARD = 10   # Reward per block
NODE_ID = str(uuid4()).replace('-', '')  # Unique node ID

# ---------------------------
# BLOCKCHAIN CLASS
# ---------------------------
class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')  # Genesis block

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.transactions,
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.transactions = []  # Reset current transactions
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while not check_proof:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self):
        previous_block = self.chain[0]
        block_index = 1
        while block_index < len(self.chain):
            block = self.chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

# ---------------------------
# NODE & WALLET
# ---------------------------
blockchain = Blockchain()
wallet = {
    'address': NODE_ID,
    'balance': SUPPLY
}

# ---------------------------
# MINING FUNCTION
# ---------------------------
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    # Reward to miner (from system)
    blockchain.add_transaction(sender="SYSTEM", receiver=wallet['address'], amount=MINING_REWARD)
    block = blockchain.create_block(proof, previous_hash)
    print(f"Block mined! Index: {block['index']}")
    print(f"Transactions: {block['transactions']}")
    print(f"Previous Hash: {block['previous_hash']}")
    print(f"Hash: {blockchain.hash(block)}\n")

# ---------------------------
# TRANSACTION FUNCTION
# ---------------------------
def send_saxv(receiver, amount):
    if wallet['balance'] < amount:
        print("Balance tidak cukup!")
        return False
    blockchain.add_transaction(sender=wallet['address'], receiver=receiver, amount=amount)
    wallet['balance'] -= amount
    print(f"{amount} SAXV dikirim ke {receiver}")
    return True

# ---------------------------
# RUN EXAMPLES
# ---------------------------
if __name__ == "__main__":
    print("=== SAXV Node V6 ===")
    print(f"Node ID: {NODE_ID}")
    print(f"Wallet balance: {wallet['balance']} SAXV\n")
    
    # Mine 2 blocks contoh
    mine_block()
    mine_block()
    
    # Kirim transaksi contoh
    send_saxv("receiver_address_123", 500)
    
    print("\nBlockchain valid:", blockchain.is_chain_valid())
    print(f"Wallet balance sekarang: {wallet['balance']}")