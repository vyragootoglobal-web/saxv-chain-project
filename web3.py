# Import library web3
from web3 import Web3

# 1. Tentukan URL Titik Akhir (ENDPOINT) Chainstack Anda
# Ganti dengan URL HTTPS endpoint dari dasbor Chainstack
CHAINSTACK_URL = "https://polygon-zkevm-mainnet.core.chainstack.com/325298772622cf88efcbb2466dcd76cc"

# 2. Inisiasi koneksi ke blockchain menggunakan HTTPProvider
w3 = Web3(Web3.HTTPProvider(CHAINSTACK_URL))

# 3. Tes Koneksi dan Ambil Data Dasar

# Cek apakah koneksi berhasil (True = Berhasil)
koneksi_berhasil = w3.is_connected()
print(f"Koneksi ke Polygon zkEVM berhasil: {koneksi_berhasil}")

if koneksi_berhasil:
    # Ambil nomor blok terbaru
    nomor_blok = w3.eth.block_number
    print(f"Nomor Blok Terbaru: {nomor_blok}")

    # Contoh: Ambil saldo ETH dari alamat tertentu (gunakan alamat tes jika perlu)
    alamat_test = '0x1c3C4029272828b1227D86bF3200424075fD022C' # Contoh alamat di zkEVM
    saldo_wei = w3.eth.get_balance(alamat_test)
    saldo_eth = w3.from_wei(saldo_wei, 'ether')
    print(f"Saldo {alamat_test}: {saldo_eth} ETH")

# 4. Melakukan Transaksi (Lanjutan)
# Jika Anda ingin mengirim transaksi (misalnya, mengirim token atau deploy kontrak), Anda perlu:
# a. Memiliki private key akun Anda.
# b. Membuat dan menandatangani transaksi secara lokal di Pydroid 3.
# c. Mengirim transaksi yang sudah ditandatangani ke node menggunakan w3.eth.send_raw_transaction()
