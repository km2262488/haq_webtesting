

**Alat Testing HTTP untuk Keperluan Etis & Edukasi**

[Fitur](#-fitur) • [Instalasi](#-instalasi) • [Penggunaan](#-penggunaan) • [Peringatan](#-peringatan)

</div>

---

## 📋 Tentang

**HAQTIVIST HTTP TESTER** adalah alat untuk melakukan **testing performa server HTTP** secara legal dan etis. Dibuat untuk tujuan:
- ✅ Testing server milik sendiri
- ✅ Benchmark performa aplikasi web
- ✅ Monitoring response time server
- ✅ Educational purposes (belajar socket programming)

> **⚠️ PENTING:** Alat ini BUKAN untuk DDoS atau serangan ilegal. Setiap penyalahgunaan sepenuhnya tanggung jawab pengguna.

---

## ✨ Fitur

| Fitur | Deskripsi |
|-------|------------|
| 🎨 **Hologram Banner** | Animasi banner dengan efek warna hologram |
| 📊 **Live Statistics** | Tampilan real-time RPS, request count, active threads |
| ⚡ **Multi-threading** | Support ribuan concurrent connections |
| 🎯 **Response Code Analysis** | Deteksi otomatis HTTP 200, 403, 404, 500, dll |
| 📈 **Performance Metrics** | Hitung response time (min/max/avg) |
| 💾 **Bandwidth Counter** | Total data transfer dalam MB/KB/s |
| 🔄 **Random User-Agent** | Rotasi User-Agent seperti browser real |
| 🛡️ **Auto Slow Down** | Otomatis kurangi speed jika banyak error |
| 📝 **Final Report** | Laporan lengkap dengan success rate |
| 🎮 **Multiple Methods** | Support GET, POST, PUT, DELETE |
| ⏱️ **Delay Adjustable** | Bisa atur jeda antar request |

---

## 🚀 Instalasi

### Prasyarat
- Python 3.7 atau lebih baru
- pip (Python package manager)

### Install Dependencies

```bash
# Clone repository (jika dari GitHub)
git clone https://github.com/km2262488/haq_webtesting.git
cd haq_webtesting

# Install required packages
pip install colorama
```

Manual Setup

```bash
# Download file haqtivist.py
wget https://raw.githubusercontent.com/haqtivist/haq_webtesting/main/haqtivist.py

# Install colorama
pip install colorama

# Jalankan
python3 haqtivist.py
```

---

💻 Penggunaan

Syntax Dasar

```bash
python haqtivist.py <IP> <PORT> <THREADS> <DURATION> [METHOD] [DELAY]
```

Parameter

Parameter Tipe Deskripsi Contoh
IP string Target IP atau domain localhost, 192.168.1.1
PORT int Port tujuan 80, 8080, 443
THREADS int Jumlah thread concurrent 10, 50, 100
DURATION int Durasi testing (detik) 5, 30, 60
METHOD string HTTP method (opsional) GET, POST, PUT
DELAY float Jeda antar request (opsional) 0, 0.05, 0.1

Contoh Penggunaan

1. Testing Dasar

```bash
python haqtivist.py localhost 8080 10 5
```

Testing ke localhost:8080 dengan 10 thread selama 5 detik.

2. Testing dengan POST Method

```bash
python haqtivist.py localhost 8080 20 10 POST
```

Mengirim request POST dengan 20 thread selama 10 detik.

3. Testing dengan Delay

```bash
python haqtivist.py 192.168.1.100 80 50 30 GET 0.05
```

50 thread, durasi 30 detik, jeda 0.05 detik antar request.

4. Testing Server Produksi Sendiri

```bash
python haqtivist.py api.kita.com 443 30 60 GET
```

Testing API server sendiri dengan 30 thread selama 60 detik.

Output yang Diharapkan

```
⚡ Active: 10 | ✓ Success: 542 | ✗ Fail: 23 | 📊 RPS: 54.2 | ⏱️ Elapsed: 10.2s

==================================================
📊 HASIL AKHIR HAQTIVIST HTTP TESTER
==================================================

📈 STATISTIK REQUEST:
  ✓ Sukses (2xx/3xx): 542
  ⚠ Gagal (4xx): 15
  ⌛ Timeout: 5
  💥 Error Socket: 3
  📦 Total Request: 565

⚡ PERFORMANCE:
  🕒 Durasi: 10.20 detik
  🚀 Rata-rata RPS: 55.4 req/detik
  📊 Peak RPS: 62
  ⏱️ Response Time (avg): 45.2ms

🎯 SUCCESS RATE: 95.9% (Excellent)
```

---

🖥️ Contoh Server Uji Coba

Untuk testing, Anda bisa membuat server sederhana:

Python HTTP Server

```bash
# Python built-in server
python -m http.server 8080
```

Node.js Server

```javascript
const http = require('http');
http.createServer((req, res) => {
    res.writeHead(200);
    res.end('OK');
}).listen(8080);
```

PHP Built-in Server

```bash
php -S localhost:8080
```

---

📊 Interpretasi Hasil

Metrik Baik Sedang Buruk
Success Rate 90% 70-90% < 70%
Response Time < 100ms 100-500ms 500ms
RPS (Requests/sec) 100 50-100 < 50
Error Rate < 5% 5-15% 15%

---

⚠️ Peringatan

❌ TIDAK UNTUK:

· Menyerang server orang lain tanpa izin
· DDoS attack
· Testing server pemerintah tanpa izin
· Aktivitas ilegal lainnya

✅ HANYA UNTUK:

· Server milik sendiri
· Server dengan izin tertulis
· Environment development/local
· Laboratorium/pembelajaran
· Bug bounty dengan scope diizinkan

📜 Konsekuensi Hukum (Indonesia)

Berdasarkan UU ITE Pasal 22, 24, 45B:

· Ancaman penjara 6-12 tahun
· Denda hingga Rp 12 miliar

---

🛠️ Troubleshooting

Error: ModuleNotFoundError: No module named 'colorama'

```bash
pip install colorama
```

Error: Connection refused

· Pastikan server target berjalan
· Cek port yang benar
· Cek firewall tidak memblokir

Error: Too many open files (Linux/Mac)

```bash
ulimit -n 65535
```

Performance Lambat

· Kurangi jumlah thread
· Tambahkan delay value (0.05 - 0.1)
· Cek koneksi internet/server

---

📁 Struktur File

```
haqtivist-http-tester/
├── haqtivist.py          # Main program
├── README.md             # Dokumentasi
├── requirements.txt      # Dependencies
└── LICENSE               # License file
```

requirements.txt

```
colorama>=0.4.4
```

---

🤝 Kontribusi

Kontribusi untuk pengembangan fitur etis sangat diterima:

1. Fork repository
2. Buat branch fitur (git checkout -b fitur-baru)
3. Commit perubahan (git commit -am 'Menambah fitur X')
4. Push ke branch (git push origin fitur-baru)
5. Buat Pull Request

Area yang bisa dikontribusi:

· ✅ Support HTTPS/SSL
· ✅ Export report ke JSON/CSV
· ✅ GUI version
· ✅ Docker support
· ✅ Proxy support

---

📞 Kontak & Support

· Developer: HAQTIVIST Team
· Email: ethical@haqtivist.security
· Website: Coming soon
· GitHub: github.com/haqtivist

---

📄 License

```
EDUCATIONAL USE ONLY LICENSE

Copyright (c) 2024 HAQTIVIST

IZIN TERBATAS:
1. Hanya untuk keperluan edukasi dan testing server sendiri
2. Dilarang digunakan untuk aktivitas ilegal
3. Dilarang digunakan untuk merugikan pihak lain
4. Pengguna bertanggung jawab penuh atas penyalahgunaan
```

---

⭐ Credits

· Python Socket Programming
· Colorama - Terminal styling
· Open Source Community
