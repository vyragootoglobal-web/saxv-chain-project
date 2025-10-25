# =====================================
#  SAXV Coin v1.0 - Fixed Supply 31M
#  Ringan, aman, tanpa error/hang
# =====================================

import json
import os

class SAXVCoin:
    def __init__(self, max_supply=31_000_000, data_file="saxv_data.json"):
        self.max_supply = max_supply
        self.total_supply = 0
        self.balances = {}
        self.data_file = data_file
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.total_supply = data.get("total_supply", 0)
                    self.balances = data.get("balances", {})
            except:
                print("⚠️ File data rusak, mulai dari awal.")
                self.save_data()

    def save_data(self):
        data = {
            "total_supply": self.total_supply,
            "balances": self.balances
        }
        with open(self.data_file, "w") as f:
            json.dump(data, f)

    def mint(self, address, amount):
        if self.total_supply + amount > self.max_supply:
            print("❌ Gagal: Supply sudah mencapai batas maksimal!")
            return
        self.total_supply += amount
        self.balances[address] = self.balances.get(address, 0) + amount
        self.save_data()
        print(f"✅ {amount} SAXV berhasil ditambahkan ke {address}")

    def transfer(self, sender, receiver, amount):
        if self.balances.get(sender, 0) < amount:
            print("❌ Gagal: Saldo tidak cukup!")
            return
        self.balances[sender] -= amount
        self.balances[receiver] = self.balances.get(receiver, 0) + amount
        self.save_data()
        print(f"💸 {amount} SAXV ditransfer dari {sender} ke {receiver}")

    def info(self):
        print("\n===== INFO KOIN SAXV =====")
        print(f"Total Supply: {self.total_supply:,} / {self.max_supply:,}")
        for addr, bal in self.balances.items():
            print(f"{addr}: {bal:,} SAXV")
        print("============================\n")


# ========== JALANKAN SIMULASI ==========
if __name__ == "__main__":
    saxv = SAXVCoin()

    # Cek apakah sudah pernah di-mint
    if saxv.total_supply == 0:
        saxv.mint("owner_wallet", 31_000_000)

    saxv.info()

    # Contoh transfer (opsional)
    saxv.transfer("owner_wallet", "user1", 1000)
    saxv.info()