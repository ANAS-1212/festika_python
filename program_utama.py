#!/usr/bin/env python3
# kopbox_pos_nodb_kodeperkategori.py
from datetime import datetime, timedelta
import os
import sys
import time

# ---------- config ----------
DBLESS_SAMPLE = True  # isi sample data awal

# ---------- helper ----------
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def pause(msg="Tekan Enter untuk melanjutkan..."):
    input(msg)

def colored(text, color_code):
    try:
        return f"\033[{color_code}m{text}\033[0m"
    except:
        return text

# ============================================================
#  SIMPLE POS (No DB) - local_id per kategori + kode prefix
# ============================================================
class SimplePOS:
    def __init__(self):
        # kategori: [{'id':1,'nama':'Makanan','kode':'MA','created_at':...}, ...]
        self.kategori = []
        # barang: [{'id':global_id,'kategori_id':1,'local_id':1,'kode':'MA001','nama':..,'stok':..,'harga':..,'created_at':..}, ...]
        self.barang = []
        # penjualan: [{'id':1,'kode_barang':'MA001','nama_barang':..,'jumlah':..,'harga_satuan':..,'total_harga':..,'created_at':..}, ...]
        self.penjualan = []
        self.keranjang = []

        if DBLESS_SAMPLE:
            self._init_sample_data()

    # ----------------------------
    # id helpers (global id only for internal lists)
    # ----------------------------
    def _next_global_id(self, collection):
        if not collection:
            return 1
        return max(item['id'] for item in collection) + 1

    def _next_local_id_for_category(self, kategori_id):
        local_ids = [b['local_id'] for b in self.barang if b['kategori_id'] == kategori_id]
        if not local_ids:
            return 1
        return max(local_ids) + 1

    # ----------------------------
    # reindex: rapikan local_id per kategori & regenerate kode
    # ----------------------------
    def reindex_barang_per_kategori(self):
        # for each category, enumerate its items in ascending old local_id or created_at and reassign local_id 1..n
        for kat in sorted(self.kategori, key=lambda x: x['id']):
            items = [b for b in self.barang if b['kategori_id'] == kat['id']]
            # sort by (local_id if exists) then by global id to get stable order
            items_sorted = sorted(items, key=lambda x: (x.get('local_id', 999999), x['id']))
            for new_local, item in enumerate(items_sorted, start=1):
                item['local_id'] = new_local
                item['kode'] = f"{kat['kode'].upper()}{new_local:03d}"

    def reindex_all(self):
        # optional: reindex kategori ids (global) and barang local ids
        # we keep kategori global id stable for relations; only barang local ids adjusted
        self.reindex_barang_per_kategori()

    # ----------------------------
    # sample data
    # ----------------------------
    def _init_sample_data(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.kategori:
            self.kategori.append({'id': 1, 'nama': 'Makanan', 'kode': 'MA', 'created_at': now})
            self.kategori.append({'id': 2, 'nama': 'Minuman', 'kode': 'MI', 'created_at': now})
            self.kategori.append({'id': 3, 'nama': 'Snack', 'kode': 'SN', 'created_at': now})
        if not self.barang:
            # note: assign local_id and kode via helper to keep consistent
            self.barang.append({'id': 1, 'kategori_id': 1, 'local_id': 1, 'kode': 'MA001', 'nama': 'Nasi Goreng', 'stok': 20, 'harga': 20000, 'created_at': now})
            self.barang.append({'id': 2, 'kategori_id': 1, 'local_id': 2, 'kode': 'MA002', 'nama': 'Mie Goreng', 'stok': 100, 'harga': 20000, 'created_at': now})
            self.barang.append({'id': 3, 'kategori_id': 1, 'local_id': 3, 'kode': 'MA003', 'nama': 'Soto', 'stok': 100, 'harga': 13112, 'created_at': now})
            self.barang.append({'id': 4, 'kategori_id': 2, 'local_id': 1, 'kode': 'MI001', 'nama': 'Es Teh', 'stok': 50, 'harga': 5000, 'created_at': now})
            self.barang.append({'id': 5, 'kategori_id': 3, 'local_id': 1, 'kode': 'SN001', 'nama': 'Cici', 'stok': 100, 'harga': 10000, 'created_at': now})
            # jika nanti ada penghapusan, gunakan reindex_barang_per_kategori()

    # ============================================================
    # UI: welcome & main menu
    # ============================================================
    def welcome_screen(self):
        clear()
        logo = [
            r" _  __            ____                ",
            r"| |/ /           |  _ \               ",
            r"| ' / ___  _____ | |_) | ____  __  __",
            r"|  < / _ \| '_  )|   < |/  _ \ \ \/ /",
            r"| |\ \_ _/|  _ _/|_____/\____/ /_/\_\ ",
            r"|_| \\    | |                         ",
            r"      |_|          K O P B O X"
        ]

        for line in logo:
            print(colored(line.center(60), "96"))
        pilih = input("\nTekan Enter untuk masuk, ketik 'q' untuk keluar: ").lower()
        if pilih == "q":
            sys.exit(0)

    def main_menu(self):
        while True:
            clear()
            print(colored("==== MENU UTAMA KOPBOX POS (Kode per Kategori) ====", "94"))
            print("1. Daftar Kategori & Barang")
            print("2. Jual Barang (pakai Kode)")
            print("3. Rekap Penjualan")
            print("0. Keluar")
            pilih = input("\nPilih [0-3]: ").strip()
            if pilih == "1":
                self.menu_kategori()
            elif pilih == "2":
                self.menu_jual()
            elif pilih == "3":
                self.rekap_penjualan()
            elif pilih == "0":
                print("Terima kasih.")
                break
            else:
                pause("Pilihan tidak valid.")

    # ============================================================
    # KATEGORI (dgn kode prefix)
    # ============================================================
    def menu_kategori(self):
        while True:
            clear()
            print(colored("📂 DAFTAR KATEGORI (Kode Prefix)", "96"))
            print("=" * 60)
            self.tampil_kategori()
            print("-" * 60)
            print("1. Tambah Kategori")
            print("2. Edit Kategori")
            print("3. Hapus Kategori")
            print("4. Masuk Tabel Barang")
            print("5. Rapikan ID Barang per Kategori (reindex)")
            print("0. Kembali")
            pilih = input("\nPilih [0-5]: ").strip()
            if pilih == "1":
                self.tambah_kategori()
            elif pilih == "2":
                self.edit_kategori()
            elif pilih == "3":
                self.hapus_kategori()
            elif pilih == "4":
                self.masuk_tabel_barang()
            elif pilih == "5":
                self.reindex_all()
                pause("ID barang per kategori dirapikan.")
            elif pilih == "0":
                break
            else:
                pause("Pilihan tidak valid.")

    def tampil_kategori(self):
        if not self.kategori:
            print("Belum ada kategori.")
            return
        print(f"{'ID':<4} {'Kode':<6} {'Nama Kategori':<30} {'Dibuat'}")
        print("-" * 60)
        for k in sorted(self.kategori, key=lambda x: x['id']):
            print(f"{k['id']:<4} {k['kode']:<6} {k['nama']:<30} {k['created_at']}")

    def tambah_kategori(self):
        clear()
        print(colored("➕ TAMBAH KATEGORI", "92"))
        nama = input("Nama kategori: ").strip()
        if not nama:
            pause("Nama tidak boleh kosong.")
            return
        kode = input("Kode prefix (2-3 huruf, contoh MA, MI): ").strip().upper()
        if not kode.isalpha() or len(kode) < 2 or len(kode) > 4:
            pause("Kode harus 2-4 huruf alphabet.")
            return
        if any(k['kode'].upper() == kode for k in self.kategori):
            pause("Kode sudah digunakan. Pilih kode lain.")
            return
        new_id = self._next_global_id(self.kategori)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.kategori.append({'id': new_id, 'nama': nama, 'kode': kode, 'created_at': now})
        pause("Kategori berhasil ditambahkan.")

    def edit_kategori(self):
        try:
            idk = int(input("ID kategori: "))
        except:
            pause("ID tidak valid.")
            return
        kat = next((k for k in self.kategori if k['id'] == idk), None)
        if not kat:
            pause("Kategori tidak ditemukan.")
            return
        nama_baru = input(f"Nama baru [{kat['nama']}]: ").strip() or kat['nama']
        kode_baru = input(f"Kode baru [{kat['kode']}]: ").strip().upper() or kat['kode']
        if not kode_baru.isalpha() or len(kode_baru) < 2 or len(kode_baru) > 4:
            pause("Kode harus 2-4 huruf alphabet.")
            return
        if any(k['kode'].upper() == kode_baru and k['id'] != idk for k in self.kategori):
            pause("Kode sudah digunakan kategori lain.")
            return
        old_kode = kat['kode']
        kat['nama'] = nama_baru
        kat['kode'] = kode_baru
        # update semua kode barang yang punya kategori ini
        for b in self.barang:
            if b['kategori_id'] == idk:
                b['kode'] = f"{kode_baru}{b['local_id']:03d}"
        pause("Kategori diperbarui.")

    def hapus_kategori(self):
        try:
            idk = int(input("ID kategori: "))
        except:
            pause("ID tidak valid.")
            return
        kat = next((k for k in self.kategori if k['id'] == idk), None)
        if not kat:
            pause("Kategori tidak ditemukan.")
            return
        kon = input(f"Hapus kategori '{kat['nama']}' beserta semua barang di dalamnya? (y/n): ").lower()
        if kon != "y":
            pause("Dibatalkan.")
            return
        # hapus barang kategori
        self.barang = [b for b in self.barang if b['kategori_id'] != idk]
        # hapus kategori
        self.kategori = [k for k in self.kategori if k['id'] != idk]
        # reindex barang
        self.reindex_all()
        pause("Kategori dan barang terkait dihapus & ID dirapikan.")

    # ============================================================
    # BARANG (local_id & kode per kategori)
    # ============================================================
    def masuk_tabel_barang(self):
        try:
            idk = int(input("Masukkan ID kategori: "))
        except:
            pause("ID tidak valid.")
            return
        kat = next((k for k in self.kategori if k['id'] == idk), None)
        if not kat:
            pause("Kategori tidak ditemukan.")
            return
        nama_kategori = kat['nama']
        while True:
            clear()
            print(colored(f"📦 DATA BARANG — {nama_kategori} (Kode: {kat['kode']})", "96"))
            self.tampil_barang_by_kategori(idk)
            print("-" * 60)
            print("1. Tambah Barang")
            print("2. Edit Barang")
            print("3. Hapus Barang")
            print("4. Rapikan ID Barang (peringkat ulang local_id)")
            print("0. Kembali")
            pilih = input("\nPilih [0-4]: ").strip()
            if pilih == "1":
                self.tambah_barang(idk)
            elif pilih == "2":
                self.edit_barang(idk)
            elif pilih == "3":
                self.hapus_barang(idk)
            elif pilih == "4":
                self.reindex_barang_per_kategori()
                pause("Local ID & kode barang dirapikan untuk kategori ini.")
            elif pilih == "0":
                break
            else:
                pause("Pilihan tidak valid.")

    def tampil_barang_by_kategori(self, kategori_id):
        rows = [b for b in self.barang if b['kategori_id'] == kategori_id]
        if not rows:
            print("Belum ada barang.")
            return
        print(f"{'No':<4} {'Kode':<8} {'Nama Barang':<30} {'Stok':<6} {'Harga':<12} {'Dibuat'}")
        print("-" * 90)
        for r in sorted(rows, key=lambda x: x['local_id']):
            print(f"{r['local_id']:<4} {r['kode']:<8} {r['nama']:<30} {r['stok']:<6} Rp {r['harga']:<10,} {r['created_at']}")

    def tambah_barang(self, kategori_id):
        clear()
        kat = next((k for k in self.kategori if k['id'] == kategori_id), None)
        if not kat:
            pause("Kategori tidak ditemukan.")
            return
        print(colored("➕ TAMBAH BARANG", "92"))
        nama = input("Nama barang: ").strip()
        if not nama:
            pause("Nama tidak boleh kosong.")
            return
        try:
            stok = int(input("Stok: "))
            harga = int(input("Harga: "))
        except:
            pause("Stok/Harga harus angka.")
            return
        local_id = self._next_local_id_for_category(kategori_id)
        kode = f"{kat['kode'].upper()}{local_id:03d}"
        new_global_id = self._next_global_id(self.barang)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.barang.append({
            'id': new_global_id,
            'kategori_id': kategori_id,
            'local_id': local_id,
            'kode': kode,
            'nama': nama,
            'stok': stok,
            'harga': harga,
            'created_at': now
        })
        pause(f"Barang '{nama}' berhasil ditambahkan dengan kode {kode}.")

    def edit_barang(self, kategori_id):
        try:
            kode = input("Masukkan Kode barang (contoh MA001): ").strip().upper()
        except:
            pause("Input tidak valid.")
            return
        b = next((x for x in self.barang if x['kode'].upper() == kode and x['kategori_id'] == kategori_id), None)
        if not b:
            pause("Barang tidak ditemukan di kategori ini.")
            return
        nama_lama, stok_lama, harga_lama = b['nama'], b['stok'], b['harga']
        nama_baru = input(f"Nama baru [{nama_lama}]: ").strip() or nama_lama
        stok_baru = input(f"Stok baru [{stok_lama}]: ")
        harga_baru = input(f"Harga baru [{harga_lama}]: ")
        try:
            stok_final = int(stok_baru) if stok_baru else stok_lama
            harga_final = int(harga_baru) if harga_baru else harga_lama
        except:
            pause("Stok/Harga harus angka.")
            return
        b['nama'] = nama_baru
        b['stok'] = stok_final
        b['harga'] = harga_final
        pause("Barang diperbarui.")

    def hapus_barang(self, kategori_id):
        try:
            kode = input("Masukkan Kode barang yang dihapus (contoh MA001): ").strip().upper()
        except:
            pause("Input tidak valid.")
            return
        b = next((x for x in self.barang if x['kode'].upper() == kode and x['kategori_id'] == kategori_id), None)
        if not b:
            pause("Barang tidak ditemukan.")
            return
        kon = input(f"Hapus barang '{b['nama']}' [{b['kode']}]? (y/n): ").lower()
        if kon != "y":
            pause("Dibatalkan.")
            return
        # hapus - PERBAIKAN: gunakan AND bukan OR
        self.barang = [x for x in self.barang if not (x['kode'].upper() == kode and x['kategori_id'] == kategori_id)]
        # hapus penjualan terkait jika diinginkan (di sini kita hapus riwayat barang itu)
        self.penjualan = [p for p in self.penjualan if p['kode_barang'] != kode]
        # rapikan local_id/ kode
        self.reindex_barang_per_kategori()
        pause("Barang dihapus & local_id dirapikan untuk kategori ini.")

    # ============================================================
    # PENJUALAN (pilih barang pakai kode seperti MA001)
    # ============================================================
    def tampil_barang_penjualan(self):
        if not self.barang:
            print("Belum ada barang.")
            return
        # group by category for neat display
        for kat in sorted(self.kategori, key=lambda x: x['id']):
            print(colored(f"\n== {kat['nama']} (Kode: {kat['kode']}) ==", "96"))
            rows = [b for b in self.barang if b['kategori_id'] == kat['id']]
            if not rows:
                print("  (Belum ada barang)")
                continue
            print(f"  {'No':<3} {'Kode':<8} {'Nama':<25} {'Stok':<5} {'Harga'}")
            for r in sorted(rows, key=lambda x: x['local_id']):
                print(f"  {r['local_id']:<3} {r['kode']:<8} {r['nama']:<25} {r['stok']:<5} Rp {r['harga']:,}")

    def menu_jual(self):
        while True:
            clear()
            print(colored("🛒 MENU PENJUALAN (Masukkan Kode barang, mis: MA001)", "94"))
            self.tampil_barang_penjualan()
            print("\nKetik 0 untuk kembali.")
            kode = input("\nMasukkan Kode barang: ").strip().upper()
            if kode == "0" or kode == "":
                return
            b = next((x for x in self.barang if x['kode'].upper() == kode), None)
            if not b:
                pause("Barang tidak ditemukan. Pastikan kode benar.")
                continue
            print(f"\nNama: {b['nama']}  |  Stok: {b['stok']}  |  Harga: Rp {b['harga']:,}")
            try:
                jumlah = int(input("Jumlah beli: "))
            except:
                pause("Jumlah harus angka.")
                continue
            if jumlah <= 0:
                pause("Jumlah harus > 0.")
                continue
            if jumlah > b['stok']:
                pause(f"Stok tidak cukup. Stok tersedia: {b['stok']}")
                continue
            # kurangi stok
            b['stok'] -= jumlah
            item = {
                "kode_barang": b['kode'],
                "nama": b['nama'],
                "jumlah": jumlah,
                "harga_satuan": b['harga'],
                "total": jumlah * b['harga']
            }
            self.keranjang.append(item)
            print("\nItem ditambahkan ke keranjang.")
            while True:
                print("\n1. Tambah barang lagi")
                print("2. Lihat keranjang / Cetak nota")
                print("0. Batal transaksi")
                pilih = input("Pilih: ").strip()
                if pilih == "1":
                    break
                elif pilih == "2":
                    self.menu_keranjang()
                    return
                elif pilih == "0":
                    self._rollback_keranjang_stok()
                    self.keranjang.clear()
                    pause("Transaksi dibatalkan, stok dikembalikan.")
                    return
                else:
                    print("Pilihan tidak valid.")

    def _rollback_keranjang_stok(self):
        for it in self.keranjang:
            b = next((x for x in self.barang if x['kode'] == it['kode_barang']), None)
            if b:
                b['stok'] += it['jumlah']

    def menu_keranjang(self):
       while  True:
            clear()
            print(colored("🛒 KERANJANG BELANJA", "93"))
            if not self.keranjang:
                print("Keranjang kosong.")
                pause()
                return
            total_belanja = 0
            print(f"{'No':<3} {'Kode':<8} {'Nama':<30} {'Qty':<5} {'Harga':<12} {'Total'}")
            print("-" * 90)
            for i, it in enumerate(self.keranjang, start=1):
                print(f"{i:<3} {it['kode_barang']:<8} {it['nama']:<30} {it['jumlah']:<5} Rp {it['harga_satuan']:<10,} Rp {it['total']:,}")
                total_belanja += it['total']
            print("-" * 90)
            print(colored(f"TOTAL: Rp {total_belanja:,}", "92"))
            print("\n1. Tambah barang")
            print("2. Cetak Nota")
            print("3. Hapus item dari keranjang")
            print("0. Kembali ke menu utama (Batalkan keranjang)")
            pilih = input("Pilih: ").strip()
            if pilih == "1":
                return
            elif pilih == "2":
                self.cetak_nota()
                return
            elif pilih == "3":
                try:
                    idx = int(input("Masukkan No item yang dihapus: "))
                except:
                    pause("Input tidak valid.")
                    continue
                if idx < 1 or idx > len(self.keranjang):
                    pause("Nomor item tidak valid.")
                    continue
                item = self.keranjang.pop(idx - 1)
                b = next((x for x in self.barang if x['kode'] == item['kode_barang']), None)
                if b:
                    b['stok'] += item['jumlah']
                pause("Item dihapus & stok dikembalikan.")
            elif pilih == "0":
                self._rollback_keranjang_stok()
                self.keranjang.clear()
                pause("Keranjang dibatalkan dan stok dikembalikan.")
                return
            else:
                pause("Pilihan tidak valid.")

    def cetak_nota(self):
        if not self.keranjang:
            pause("Keranjang kosong.")
            return
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_final = 0
        for it in self.keranjang:
            new_id = self._next_global_id(self.penjualan)
            rec = {
                'id': new_id,
                'kode_barang': it['kode_barang'],
                'nama_barang': it['nama'],
                'jumlah': it['jumlah'],
                'harga_satuan': it['harga_satuan'],
                'total_harga': it['total'],
                'created_at': waktu
            }
            self.penjualan.append(rec)
            total_final += it['total']
        clear()
        print(colored("🧾 NOTA PEMBELIAN", "92"))
        print(f"Tanggal: {waktu}")
        for it in self.keranjang:
            print(f"{it['kode_barang']} - {it['nama']} x{it['jumlah']} = Rp {it['total']:,}")
        print("-" * 60)
        print(colored(f"TOTAL BAYAR: Rp {total_final:,}", "93"))
        print("-" * 60)
        self.keranjang.clear()
        pause("Transaksi selesai dan disimpan (in-memory).")

    # ============================================================
    # REKAP PENJUALAN
    # ============================================================
    def _print_rekap(self, rows, title):
        clear()
        print(colored(title, "96"))
        print("-" * 100)
        if not rows:
            print("Tidak ada transaksi untuk periode ini.")
            print("-" * 100)
            return
        print(f"{'ID':<4} {'Kode':<8} {'Barang':<30} {'Qty':<5} {'Harga':<12} {'Total':<12} {'Tanggal'}")
        print("-" * 100)
        total_all = 0
        for r in sorted(rows, key=lambda x: x['id']):
            print(f"{r['id']:<4} {r['kode_barang']:<8} {r['nama_barang']:<30} {r['jumlah']:<5} Rp {r['harga_satuan']:<10,} Rp {r['total_harga']:<10,} {r['created_at']}")
            total_all += r['total_harga']
        print("-" * 100)
        print(colored(f"TOTAL: Rp {total_all:,}", "93"))

    def _valid_date(self, s):
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return True
        except:
            return False

    def rekap_penjualan(self):
        while True:
            clear()
            print(colored("📊 MENU REKAP PENJUALAN", "96"))
            print("1. Rekap Harian")
            print("2. Rekap Mingguan")
            print("3. Rekap Bulanan")
            print("4. Rekap Semua")
            print("0. Kembali")
            pilih = input("\nPilih: ").strip()
            if pilih == "1":
                today = datetime.now().date()
                rows = [p for p in self.penjualan if datetime.strptime(p['created_at'], "%Y-%m-%d %H:%M:%S").date() == today]
                self._print_rekap(rows, "📅 REKAP HARIAN — Hari Ini")
                ans = input("\nGunakan tanggal lain? (y/n): ").strip().lower()
                if ans == "y":
                    t = input("Masukkan tanggal (YYYY-MM-DD): ").strip()
                    if not self._valid_date(t):
                        pause("Format tanggal tidak valid.")
                        continue
                    rows2 = [p for p in self.penjualan if p['created_at'].startswith(t)]
                    self._print_rekap(rows2, f"📅 REKAP HARIAN — {t}")
                    pause()
                else:
                    pause()
            elif pilih == "2":
                today = datetime.now().date()
                start_of_week = today - timedelta(days=today.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                rows = [p for p in self.penjualan if start_of_week <= datetime.strptime(p['created_at'], "%Y-%m-%d %H:%M:%S").date() <= end_of_week]
                self._print_rekap(rows, f"📅 REKAP MINGGUAN — {start_of_week} s/d {end_of_week}")
                ans = input("\nGunakan rentang minggu lain? (y/n): ").strip().lower()
                if ans == "y":
                    t1 = input("Masukkan tanggal mulai (YYYY-MM-DD): ").strip()
                    t2 = input("Masukkan tanggal akhir (YYYY-MM-DD): ").strip()
                    if not (self._valid_date(t1) and self._valid_date(t2)):
                        pause("Format salah. Gunakan YYYY-MM-DD.")
                        continue
                    d1 = datetime.strptime(t1, "%Y-%m-%d").date()
                    d2 = datetime.strptime(t2, "%Y-%m-%d").date()
                    if d2 < d1:
                        pause("Tanggal akhir harus sama atau setelah tanggal mulai.")
                        continue
                    rows2 = [p for p in self.penjualan if d1 <= datetime.strptime(p['created_at'], "%Y-%m-%d %H:%M:%S").date() <= d2]
                    self._print_rekap(rows2, f"📅 REKAP MINGGUAN — {t1} s/d {t2}")
                    pause()
                else:
                    pause()
            elif pilih == "3":
                now = datetime.now()
                rows = [p for p in self.penjualan if datetime.strptime(p['created_at'], "%Y-%m-%d %H:%M:%S").month == now.month and datetime.strptime(p['created_at'], "%Y-%m-%d %H:%M:%S").year == now.year]
                self._print_rekap(rows, f"📅 REKAP BULANAN — {now.strftime('%B %Y')}")
                pause()
            elif pilih == "4":
                self._print_rekap(self.penjualan, "📊 REKAP SEMUA PENJUALAN")
                pause()
            elif pilih == "0":
                return
            else:
                pause("Pilihan tidak valid.")

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    app = SimplePOS()
    app.welcome_screen()
    app.main_menu()
