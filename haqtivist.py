#!/usr/bin/env python3
"""
HAQTIVIST HTTP TESTER 
Ethical Security Testing Tool
"""

import socket
import threading
import time
import sys
import random
import json
import re
from datetime import datetime
from urllib.parse import urlparse
from colorama import init, Fore, Style

init(autoreset=True)

# ============ KONFIGURASI ============
stats = {
    'success': 0,
    'success_2xx': 0,
    'redirect_3xx': 0,
    'client_error_4xx': 0,
    'server_error_5xx': 0,
    'timeout': 0,
    'error': 0,
    'total_requests': 0,
    'bytes_transferred': 0,
    'response_times': [],
    'start_time': None,
    'end_time': None,
    'url_tested': None
}

lock = threading.Lock()
stop_flag = threading.Event()

# Konfigurasi payload untuk POST
POST_PAYLOADS = [
    '{"username":"test","password":"test123"}',
    "name=test&email=test@example.com",
    '{"data":"sample","value":123}',
    "------WebKitFormBoundary\r\nContent-Disposition: form-data; name=\"file\"\r\n\r\ntest\r\n------WebKitFormBoundary--"
]

# ============ FITUR PARSING URL ============

def parse_url(url):
    """Parse URL dan ekstrak target, port, endpoint"""
    original_url = url
    is_https = False
    
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    parsed = urlparse(url)
    target = parsed.hostname
    scheme = parsed.scheme
    
    # Deteksi HTTPS
    if scheme == 'https':
        is_https = True
        # HTTPS tidak support, ubah ke HTTP
        port = parsed.port if parsed.port else 80  # Ganti ke port 80
        print(f"{Fore.RED}[!] PERINGATAN: HTTPS (port 443) TIDAK DIDUKUNG!")
        print(f"{Fore.YELLOW}[!] Menggunakan HTTP ke port {port} sebagai gantinya")
        print(f"{Fore.YELLOW}[!] URL asli: {original_url}")
        print(f"{Fore.YELLOW}[!] URL test: http://{target}:{port}{parsed.path}")
    else:
        port = parsed.port if parsed.port else 80
    
    endpoint = parsed.path if parsed.path else '/'
    if parsed.query:
        endpoint += '?' + parsed.query
    
    return target, port, endpoint, is_https

def parse_url_file(filename):
    """Baca daftar URL dari file"""
    urls = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
    except FileNotFoundError:
        print(f"{Fore.RED}[!] File {filename} tidak ditemukan!")
        return []
    return urls

# ============ FITUR GENERATE ============

def generate_user_agent():
    """Random User-Agent"""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/121.0",
    ]
    return random.choice(agents)

def get_random_headers(target):
    """Generate random HTTP headers"""
    headers = {
        "Accept": random.choice(["text/html", "application/json", "application/xml", "*/*"]),
        "Accept-Language": random.choice(["id-ID,id;q=0.9", "en-US,en;q=0.8", "ms-MY,ms;q=0.9"]),
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": random.choice(["no-cache", "max-age=0", "no-store"]),
        "Connection": "close"
    }
    return headers

# ============ FITUR REPORT ============

def save_report(filename="haqtivist_report.json"):
    """Simpan hasil test ke file JSON"""
    elapsed = (stats['end_time'] - stats['start_time']) if stats['end_time'] and stats['start_time'] else 0
    report = {
        "tool": "HAQTIVIST HTTP TESTER",
        "version": "3.0",
        "timestamp": datetime.now().isoformat(),
        "url_tested": stats['url_tested'],
        "stats": {
            'success': stats['success'],
            'success_2xx': stats['success_2xx'],
            'redirect_3xx': stats['redirect_3xx'],
            'client_error_4xx': stats['client_error_4xx'],
            'server_error_5xx': stats['server_error_5xx'],
            'timeout': stats['timeout'],
            'error': stats['error'],
            'total_requests': stats['total_requests'],
            'bytes_transferred': stats['bytes_transferred']
        },
        "performance": {
            "duration": elapsed,
            "avg_response_time_ms": (sum(stats['response_times']) / len(stats['response_times']) * 1000) if stats['response_times'] else 0,
            "rps": stats['total_requests'] / elapsed if elapsed > 0 else 0
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"{Fore.GREEN}[+] Report saved to {filename}")

# ============ FITUR TESTING ============

def live_stats_display(threads_active, elapsed, rps, target, port):
    """Tampilan statistik real-time"""
    with lock:
        sys.stdout.write(f"\r\033[K")
        status_line = (
            f"{Fore.YELLOW}🎯 {target}:{port} | "
            f"{Fore.CYAN}🧵 {threads_active} | "
            f"{Fore.GREEN}✓ {stats['success']} | "
            f"{Fore.RED}✗ {stats['error']+stats['timeout']} | "
            f"{Fore.MAGENTA}📊 RPS: {rps:.1f} | "
            f"{Fore.LIGHTBLUE_EX}⏱️ {elapsed:.1f}s"
        )
        sys.stdout.write(status_line + Style.RESET_ALL)
        sys.stdout.flush()


        
        # Generate parameter random
        random_param = f"?_={int(time.time())}&r={random.randint(1000,9999)}"
        
        # Buat request berdasarkan method
        if method == "GET":
            if '?' in endpoint:
                request_line = f"{method} {endpoint}&r={random.randint(1000,9999)} HTTP/1.1\r\n"
            else:
                request_line = f"{method} {endpoint}{random_param} HTTP/1.1\r\n"
        elif method == "POST":
            if not pdef test_request(target, port, endpoint="/", method="GET", delay=0, payload=None, use_https=False):
    """HTTP/HTTPS Request dengan berbagai fitur"""
    global stats
    start_time = time.time()
    s = None
    
    try:
        # Buat socket biasa dulu
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((target, port))
        
        # Jika HTTPS, bungkus dengan SSL
        if use_https:
            import ssl
            context = ssl.create_default_context()
            s = context.wrap_socket(sock, server_hostname=target)
        else:
            s = sock
        
        
    except Exception as e:
        # ... error handling ...ayload:
                payload = random.choice(POST_PAYLOADS)
            request_line = f"{method} {endpoint} HTTP/1.1\r\n"
        else:
            request_line = f"{method} {endpoint} HTTP/1.1\r\n"
        
        # Headers
        headers = get_random_headers(target)
        request = request_line
        request += f"Host: {target}\r\n"
        request += f"User-Agent: {generate_user_agent()}\r\n"
        
        for key, value in headers.items():
            request += f"{key}: {value}\r\n"
        
        if method == "POST" and payload:
            request += f"Content-Type: application/x-www-form-urlencoded\r\n"
            request += f"Content-Length: {len(payload)}\r\n"
            request += "\r\n"
            request += payload
        else:
            request += "\r\n"
        
        s.send(request.encode())
        
        # Baca response
        response = b""
        while True:
            try:
                chunk = s.recv(8192)
                if not chunk:
                    break
                response += chunk
            except socket.timeout:
                break
            except:
                break
        
        response_time = time.time() - start_time
        
        with lock:
            stats['total_requests'] += 1
            stats['bytes_transferred'] += len(response)
            stats['response_times'].append(response_time)
            
            # Analisis response
            if len(response) > 0:
                response_str = response[:100].decode('utf-8', errors='ignore')
                
                if "200" in response_str:
                    stats['success'] += 1
                    stats['success_2xx'] += 1
                elif "201" in response_str or "204" in response_str:
                    stats['success'] += 1
                    stats['success_2xx'] += 1
                elif "301" in response_str or "302" in response_str or "307" in response_str:
                    stats['success'] += 1
                    stats['redirect_3xx'] += 1
                elif "400" in response_str or "401" in response_str or "403" in response_str or "404" in response_str:
                    stats['client_error_4xx'] += 1
                elif "500" in response_str or "502" in response_str or "503" in response_str:
                    stats['server_error_5xx'] += 1
                else:
                    if len(response) > 10:
                        stats['success'] += 1
                    else:
                        stats['client_error_4xx'] += 1
            else:
                stats['error'] += 1
        
    except socket.timeout:
        with lock:
            stats['timeout'] += 1
            stats['total_requests'] += 1
    except ConnectionRefusedError:
        with lock:
            stats['error'] += 1
            stats['total_requests'] += 1
    except Exception as e:
        with lock:
            stats['error'] += 1
            stats['total_requests'] += 1
    finally:
        if s:
            try:
                s.close()
            except:
                pass

def worker(target, port, endpoint, method, duration, delay, payload=None):
    """Worker thread"""
    start_time = time.time()
    request_count = 0
    
    while not stop_flag.is_set() and (time.time() - start_time) < duration:
        test_request(target, port, endpoint, method, delay, payload)
        request_count += 1
        
        if delay > 0:
            time.sleep(delay)
        elif stats['error'] > 100 and request_count % 100 == 0:
            time.sleep(0.1)

def attack_mode(target, port, endpoint, duration, threads, method="GET", delay=0, payload=None):
    """Mode testing utama"""
    stats['url_tested'] = f"http://{target}:{port}{endpoint}"
    
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.YELLOW}🎯 TARGET: {Fore.WHITE}{stats['url_tested']}")
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.WHITE}📋 Konfigurasi Test:")
    print(f"   {Fore.LIGHTBLACK_EX}├─ Method:     {Fore.LIGHTWHITE_EX}{method}")
    print(f"   {Fore.LIGHTBLACK_EX}├─ Threads:    {Fore.LIGHTWHITE_EX}{threads}")
    print(f"   {Fore.LIGHTBLACK_EX}├─ Duration:   {Fore.LIGHTWHITE_EX}{duration} detik")
    print(f"   {Fore.LIGHTBLACK_EX}└─ Delay:      {Fore.LIGHTWHITE_EX}{delay} detik")
    print(f"{Fore.CYAN}{'='*70}")
    
    print(f"\n{Fore.YELLOW}[!] PERINGATAN: Hanya untuk server milik sendiri!")
    print(f"{Fore.LIGHTBLACK_EX}[*] Memulai testing... Tekan Ctrl+C untuk berhenti\n")
    
    start_time = time.time()
    stats['start_time'] = start_time
    
    thread_list = []
    
    try:
        for _ in range(threads):
            t = threading.Thread(target=worker, args=(target, port, endpoint, method, duration, delay, payload))
            t.daemon = True
            t.start()
            thread_list.append(t)
        
        last_update = time.time()
        last_requests = 0
        
        while any(t.is_alive() for t in thread_list):
            time.sleep(0.3)
            elapsed = time.time() - start_time
            
            if elapsed >= duration:
                stop_flag.set()
                break
            
            if time.time() - last_update >= 0.8:
                with lock:
                    current_requests = stats['total_requests']
                    rps = (current_requests - last_requests) / 0.8
                    last_requests = current_requests
                    live_stats_display(len(thread_list), elapsed, rps, target, port)
                    last_update = time.time()
        
        for t in thread_list:
            t.join(timeout=1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}[!] Testing dihentikan oleh user")
        stop_flag.set()
    
    stats['end_time'] = time.time()

def show_final_report():
    """Laporan akhir yang detail"""
    elapsed = stats['end_time'] - stats['start_time'] if stats['end_time'] and stats['start_time'] else 0
    success_rate = (stats['success'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
    
    print(f"\n\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.YELLOW}📊 HASIL AKHIR HAQTIVIST HTTP TESTER")
    print(f"{Fore.CYAN}{'='*70}")
    
    print(f"\n{Fore.WHITE}📈 STATISTIK REQUEST:")
    print(f"  {Fore.GREEN}✓ 2xx Success:     {stats['success_2xx']}")
    print(f"  {Fore.LIGHTBLUE_EX}↻ 3xx Redirect:    {stats['redirect_3xx']}")
    print(f"  {Fore.YELLOW}⚠ 4xx Client Error: {stats['client_error_4xx']}")
    print(f"  {Fore.RED}🔥 5xx Server Error: {stats['server_error_5xx']}")
    print(f"  {Fore.MAGENTA}⌛ Timeout:         {stats['timeout']}")
    print(f"  {Fore.RED}💥 Socket Error:    {stats['error']}")
    print(f"  {Fore.WHITE}📦 Total Request:   {stats['total_requests']}")
    
    print(f"\n{Fore.WHITE}⚡ PERFORMANCE:")
    print(f"  {Fore.YELLOW}🕒 Durasi:          {elapsed:.2f} detik")
    print(f"  {Fore.YELLOW}🚀 Rata-rata RPS:    {stats['total_requests']/elapsed:.1f} req/detik")
    
    if stats['response_times']:
        avg_response = sum(stats['response_times']) / len(stats['response_times']) * 1000
        min_response = min(stats['response_times']) * 1000
        max_response = max(stats['response_times']) * 1000
        print(f"  {Fore.YELLOW}⏱️  Response Time (avg):  {avg_response:.1f}ms")
        print(f"  {Fore.YELLOW}⏱️  Response Time (min):   {min_response:.1f}ms")
        print(f"  {Fore.YELLOW}⏱️  Response Time (max):   {max_response:.1f}ms")
    
    print(f"\n{Fore.WHITE}💾 BANDWIDTH:")
    print(f"  {Fore.YELLOW}📤 Total Transfer:   {stats['bytes_transferred']/1024/1024:.2f} MB")
    print(f"  {Fore.YELLOW}📤 Rata-rata Transfer: {stats['bytes_transferred']/1024/elapsed:.1f} KB/s")
    
    print(f"\n{Fore.WHITE}🎯 SUCCESS RATE: ", end="")
    if success_rate >= 95:
        print(f"{Fore.GREEN}{success_rate:.1f}% (Excellent) ⭐⭐⭐⭐⭐")
    elif success_rate >= 80:
        print(f"{Fore.LIGHTGREEN_EX}{success_rate:.1f}% (Good) ⭐⭐⭐⭐")
    elif success_rate >= 60:
        print(f"{Fore.YELLOW}{success_rate:.1f}% (Average) ⭐⭐⭐")
    elif success_rate >= 40:
        print(f"{Fore.MAGENTA}{success_rate:.1f}% (Poor) ⭐⭐")
    else:
        print(f"{Fore.RED}{success_rate:.1f}% (Bad) ⭐")
    
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.LIGHTBLACK_EX}Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Fore.LIGHTBLACK_EX}HAQTIVIST - For Ethical Testing Only")

# ============ MODE URL ============

def test_single_url(url, threads, duration, delay=0, method="GET"):
    """Test single URL"""
    target, port, endpoint, is_https = parse_url(url)
    
    if is_https:
        print(f"{Fore.YELLOW}[!] Melanjutkan testing dengan HTTP (port {port})")
        print(f"{Fore.YELLOW}[!] Pastikan server HTTP berjalan di port tersebut\n")
    
    attack_mode(target, port, endpoint, duration, threads, method, delay)
    show_final_report()

def test_multiple_urls(urls, threads, duration, delay=0, method="GET"):
    """Test multiple URLs"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.YELLOW}📋 Multi-URL Testing Mode")
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.WHITE}Total URL yang akan di test: {len(urls)}")
    
    https_count = 0
    for url in urls:
        if url.startswith('https://'):
            https_count += 1
    
    if https_count > 0:
        print(f"{Fore.YELLOW}[!] Terdapat {https_count} URL HTTPS yang akan dikonversi ke HTTP")
        print(f"{Fore.YELLOW}[!] Pastikan server HTTP berjalan di port yang sesuai\n")
    
    for i, url in enumerate(urls, 1):
        print(f"\n{Fore.LIGHTBLACK_EX}{'─'*40}")
        print(f"{Fore.GREEN}[{i}/{len(urls)}] Testing: {url}")
        print(f"{Fore.LIGHTBLACK_EX}{'─'*40}")
        
        target, port, endpoint, is_https = parse_url(url)
        
        if is_https:
            print(f"{Fore.YELLOW}[!] Konversi HTTPS -> HTTP, menggunakan port {port}")
        
        # Reset stats untuk setiap URL
        for key in stats:
            if key not in ['url_tested']:
                if isinstance(stats[key], list):
                    stats[key] = []
                else:
                    stats[key] = 0
        stats['response_times'] = []
        
        attack_mode(target, port, endpoint, duration, threads, method, delay)
        show_final_report()
        
        if i < len(urls):
            print(f"\n{Fore.YELLOW}[!] Menunggu 2 detik sebelum test URL berikutnya...")
            time.sleep(2)

# ============ MODE INTERAKTIF ============

def interactive_mode():
    """Mode interaktif - input manual"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.YELLOW}🎮 INTERACTIVE MODE - HTTP TESTER")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    print(f"{Fore.WHITE}Pilih mode test:")
    print(f"  {Fore.CYAN}[1] {Fore.WHITE}Single URL (otomatis parsing)")
    print(f"  {Fore.CYAN}[2] {Fore.WHITE}Multiple URL (dari file)")
    print(f"  {Fore.CYAN}[3] {Fore.WHITE}Custom target (IP/Host + Port)")
    
    choice = input(f"\n{Fore.YELLOW}Pilihan [1-3]: {Fore.WHITE}").strip()
    
    if choice == '1':
        url = input(f"{Fore.WHITE}URL target {Fore.YELLOW}[http://localhost:8080]{Fore.WHITE}: ") or "http://localhost:8080"
        method = input(f"{Fore.WHITE}HTTP Method {Fore.YELLOW}[GET]{Fore.WHITE}: ") or "GET"
        threads = int(input(f"{Fore.WHITE}Threads {Fore.YELLOW}[10]{Fore.WHITE}: ") or "10")
        duration = int(input(f"{Fore.WHITE}Duration (detik) {Fore.YELLOW}[10]{Fore.WHITE}: ") or "10")
        delay = float(input(f"{Fore.WHITE}Delay (detik) {Fore.YELLOW}[0]{Fore.WHITE}: ") or "0")
        
        save = input(f"{Fore.WHITE}Simpan report? {Fore.YELLOW}[y/N]{Fore.WHITE}: ").lower() == 'y'
        
        test_single_url(url, threads, duration, delay, method.upper())
        
        if save:
            save_report()
    
    elif choice == '2':
        filename = input(f"{Fore.WHITE}File URL list {Fore.YELLOW}[urls.txt]{Fore.WHITE}: ") or "urls.txt"
        urls = parse_url_file(filename)
        if not urls:
            print(f"{Fore.RED}[!] Tidak ada URL yang ditemukan!")
            return
        
        method = input(f"{Fore.WHITE}HTTP Method {Fore.YELLOW}[GET]{Fore.WHITE}: ") or "GET"
        threads = int(input(f"{Fore.WHITE}Threads {Fore.YELLOW}[10]{Fore.WHITE}: ") or "10")
        duration = int(input(f"{Fore.WHITE}Duration (detik) {Fore.YELLOW}[5]{Fore.WHITE}: ") or "5")
        delay = float(input(f"{Fore.WHITE}Delay (detik) {Fore.YELLOW}[0]{Fore.WHITE}: ") or "0")
        
        test_multiple_urls(urls, threads, duration, delay, method.upper())
    
    else:
        target = input(f"{Fore.WHITE}Target IP/Domain {Fore.YELLOW}[localhost]{Fore.WHITE}: ") or "localhost"
        port = int(input(f"{Fore.WHITE}Port {Fore.YELLOW}[8080]{Fore.WHITE}: ") or "8080")
        endpoint = input(f"{Fore.WHITE}Endpoint {Fore.YELLOW}[/]{Fore.WHITE}: ") or "/"
        method = input(f"{Fore.WHITE}HTTP Method {Fore.YELLOW}[GET]{Fore.WHITE}: ") or "GET"
        threads = int(input(f"{Fore.WHITE}Threads {Fore.YELLOW}[10]{Fore.WHITE}: ") or "10")
        duration = int(input(f"{Fore.WHITE}Duration (detik) {Fore.YELLOW}[10]{Fore.WHITE}: ") or "10")
        delay = float(input(f"{Fore.WHITE}Delay (detik) {Fore.YELLOW}[0]{Fore.WHITE}: ") or "0")
        
        save = input(f"{Fore.WHITE}Simpan report? {Fore.YELLOW}[y/N]{Fore.WHITE}: ").lower() == 'y'
        
        attack_mode(target, port, endpoint, duration, threads, method.upper(), delay)
        show_final_report()
        
        if save:
            save_report()

# ============ MAIN ============
def show_help():
    """Tampilkan help"""
    print(f"""
{Fore.CYAN}HAQTIVIST HTTP TESTER v3.0 - Cara Penggunaan

{Fore.YELLOW}📌 Mode URL (Single):
{Fore.WHITE}  python haqtivist.py --url http://localhost:8080 --threads 10 --duration 10
  python haqtivist.py --url https://example.com --threads 5 --duration 5
  {Fore.LIGHTBLACK_EX}(URL HTTPS akan otomatis dikonversi ke HTTP)

{Fore.YELLOW}📌 Mode Multi-URL (dari file):
{Fore.WHITE}  python haqtivist.py --urls urls.txt --threads 10 --duration 5

{Fore.YELLOW}📌 Mode Custom (IP/Host + Port):
{Fore.WHITE}  python haqtivist.py --target localhost -p 8080 --threads 10 --duration 10

{Fore.YELLOW}📌 Mode Interaktif:
{Fore.WHITE}  python haqtivist.py --interactive

{Fore.YELLOW}📌 Simpan Report:
{Fore.WHITE}  python haqtivist.py --url http://localhost:8080 --save

{Fore.YELLOW}⚠️  Peringatan: 
   - HTTPS tidak didukung, akan dikonversi ke HTTP
   - Pastikan server HTTP berjalan di port yang dituju
    """)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit()
    
    # Default values
    target = None
    port = None
    url = None
    urls_file = None
    threads = 10
    duration = 10
    method = "GET"
    delay = 0
    endpoint = "/"
    save_flag = False
    interactive = False
    
    # Parse arguments
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ["--help", "-h"]:
            show_help()
            sys.exit()
        elif arg == "--interactive":
            interactive = True
            i += 1
        elif arg == "--url" and i+1 < len(sys.argv):
            url = sys.argv[i+1]
            i += 2
        elif arg == "--urls" and i+1 < len(sys.argv):
            urls_file = sys.argv[i+1]
            i += 2
        elif arg == "--target" and i+1 < len(sys.argv):
            target = sys.argv[i+1]
            i += 2
        elif arg == "-p" and i+1 < len(sys.argv):
            port = int(sys.argv[i+1])
            i += 2
        elif arg == "--threads" and i+1 < len(sys.argv):
            threads = int(sys.argv[i+1])
            i += 2
        elif arg == "--duration" and i+1 < len(sys.argv):
            duration = int(sys.argv[i+1])
            i += 2
        elif arg == "--method" and i+1 < len(sys.argv):
            method = sys.argv[i+1].upper()
            i += 2
        elif arg == "--delay" and i+1 < len(sys.argv):
            delay = float(sys.argv[i+1].replace(',', '.'))
            i += 2
        elif arg == "--save":
            save_flag = True
            i += 1
        else:
            if not url and not target:
                if sys.argv[i].startswith(('http://', 'https://')) or '/' in sys.argv[i] or '.' in sys.argv[i]:
                    url = sys.argv[i]
                else:
                    target = sys.argv[i]
            i += 1
    
    # Konfirmasi untuk non-localhost
    if target and target not in ["localhost", "127.0.0.1"]:
        confirm = input(f"{Fore.YELLOW}Apakah Anda memiliki izin tertulis untuk testing? (y/N): ").lower()
        if confirm != 'y':
            print(f"{Fore.RED}Testing dibatalkan.")
            sys.exit()
    
    if interactive:
        interactive_mode()
    elif url:
        test_single_url(url, threads, duration, delay, method)
        if save_flag:
            save_report()
    elif urls_file:
        urls = parse_url_file(urls_file)
        if urls:
            test_multiple_urls(urls, threads, duration, delay, method)
    elif target and port:
        attack_mode(target, port, endpoint, duration, threads, method, delay)
        show_final_report()
        if save_flag:
            save_report()
    else:
        show_help()
