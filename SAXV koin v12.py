import json

# ---------------------------
# PASTE DATA V11 DI BAWAH
# ---------------------------
# Misal dari V11, ganti dengan object chain dan wallet yang kamu punya
blockchain = [
    # contoh block
    # {'index':1,'timestamp':...,'transactions':[...],'proof':1,'previous_hash':'0'},
]

wallet = {
    'address': 'node_id_example',
    'balance': 31000000  # saldo SAXV
}

# ---------------------------
# CEK STATUS
# ---------------------------
def check_blockchain():
    if len(blockchain)==0:
        print("❌ Blockchain belum dibuat!")
        return
    print(f"✅ Blockchain sudah dibuat! Total blok: {len(blockchain)}")
    print("Blok terakhir:")
    last_block = blockchain[-1]
    print(json.dumps(last_block, indent=4))

def check_wallet():
    print(f"Wallet Address: {wallet['address']}")
    print(f"Saldo SAXV: {wallet['balance']}")

# ---------------------------
# RUN
# ---------------------------
if __name__=="__main__":
    check_blockchain()
    check_wallet()