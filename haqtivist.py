#!/usr/bin/env python3
"""
HAQTIVIST TOOL 
"""

import socket
import threading
import time
import sys
import random
import json
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

POST_PAYLOADS = [
    '{"username":"test","password":"test123"}',
    "name=test&email=test@example.com",
    '{"data":"sample","value":123}',
]

def generate_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]
    return random.choice(agents)

def get_random_headers(target):
    return {
        "Accept": "text/html",
        "Accept-Language": "id-ID,id;q=0.9",
        "Connection": "close"
    }

def save_report(filename="haqtivist_report.json"):
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

def test_request(target, port, endpoint="/", method="GET", delay=0, payload=None):
    global stats
    start_time = time.time()
    s = None
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((target, port))
        
        request = f"{method} {endpoint} HTTP/1.1\r\n"
        request += f"Host: {target}\r\n"
        request += f"User-Agent: {generate_user_agent()}\r\n"
        request += "Accept: text/html\r\n"
        request += "Connection: close\r\n"
        request += "\r\n"
        
        s.send(request.encode())
        
        response = b""
        while True:
            try:
                chunk = s.recv(4096)
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
            
            if len(response) > 0:
                response_str = response[:100].decode('utf-8', errors='ignore')
                if "200" in response_str or "201" in response_str:
                    stats['success'] += 1
                    stats['success_2xx'] += 1
                elif "301" in response_str or "302" in response_str:
                    stats['success'] += 1
                    stats['redirect_3xx'] += 1
                elif "400" in response_str or "401" in response_str or "403" in response_str or "404" in response_str:
                    stats['client_error_4xx'] += 1
                elif "500" in response_str:
                    stats['server_error_5xx'] += 1
                else:
                    stats['success'] += 1
            else:
                stats['error'] += 1
        
    except socket.timeout:
        with lock:
            stats['timeout'] += 1
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
    start_time = time.time()
    while not stop_flag.is_set() and (time.time() - start_time) < duration:
        test_request(target, port, endpoint, method, delay, payload)
        if delay > 0:
            time.sleep(delay)

def attack_mode(target, port, endpoint, duration, threads, method="GET", delay=0, payload=None):
    """Mode testing dengan LIVE STATS REAL TIME"""
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
    
    print(f"\n{Fore.YELLOW}[!] PERINGATAN: Bismillah dulu baru klik enter")
    print(f"{Fore.LIGHTBLACK_EX}[*] Memulai testing... Tekan Ctrl+C untuk berhenti\n")
    
    # Header Live Stats
    print(f"{Fore.LIGHTBLACK_EX}{'─'*70}")
    print(f"{Fore.CYAN}⏱️  WAKTU    │  ✓ SUKSES  │  ✗ ERROR   │  📊 RPS    │  🧵 THREAD")
    print(f"{Fore.LIGHTBLACK_EX}{'─'*70}")
    
    start_time = time.time()
    stats['start_time'] = start_time
    
    thread_list = []
    
    try:
        for _ in range(threads):
            t = threading.Thread(target=worker, args=(target, port, endpoint, method, duration, delay, payload))
            t.daemon = True
            t.start()
            thread_list.append(t)
        
        # LIVE STATS UPDATE REAL TIME
        while any(t.is_alive() for t in thread_list):
            time.sleep(0.3)
            elapsed = time.time() - start_time
            
            # Hentikan tepat waktu
            if elapsed >= duration:
                stop_flag.set()
                break
            
            # Update display
            with lock:
                current_requests = stats['total_requests']
                rps = current_requests / elapsed if elapsed > 0 else 0
                active = len([t for t in thread_list if t.is_alive()])
                
                sys.stdout.write(f"\r\033[K")
                sys.stdout.write(
                    f"\r{Fore.CYAN}{elapsed:6.1f}s   │ "
                    f"{Fore.GREEN}{stats['success']:8d}   │ "
                    f"{Fore.RED}{(stats['error']+stats['timeout']):8d}   │ "
                    f"{Fore.YELLOW}{rps:8.1f}   │ "
                    f"{Fore.MAGENTA}{active:4d}"
                )
                sys.stdout.flush()
        
        print(f"\n{Fore.LIGHTBLACK_EX}{'─'*70}")
        
        # Beri waktu sedikit untuk thread selesai
        time.sleep(0.5)
        stop_flag.set()
        
        for t in thread_list:
            t.join(timeout=1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}[!] Testing dihentikan oleh user")
        stop_flag.set()
    
    stats['end_time'] = time.time()

def show_final_report():
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
        print(f"  {Fore.YELLOW}⏱️  Response Time (avg):  {avg_response:.1f}ms")
    
    print(f"\n{Fore.WHITE}💾 BANDWIDTH:")
    print(f"  {Fore.YELLOW}📤 Total Transfer:   {stats['bytes_transferred']/1024/1024:.2f} MB")
    
    print(f"\n{Fore.WHITE}🎯 SUCCESS RATE: ", end="")
    if success_rate >= 95:
        print(f"{Fore.GREEN}{success_rate:.1f}% (Excellent)")
    elif success_rate >= 80:
        print(f"{Fore.LIGHTGREEN_EX}{success_rate:.1f}% (Good)")
    else:
        print(f"{Fore.YELLOW}{success_rate:.1f}% (Average)")
    
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.LIGHTBLACK_EX}Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def parse_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    parsed = urlparse(url)
    target = parsed.hostname
    port = parsed.port if parsed.port else 80
    endpoint = parsed.path if parsed.path else '/'
    return target, port, endpoint

def show_help():
    print(f"""
{Fore.CYAN}HAQTIVIST HTTP TESTER v3.0

{Fore.YELLOW}Cara Penggunaan:{Fore.WHITE}
  python haqtivist.py --url http://localhost:8080 --threads 5 --duration 10

{Fore.YELLOW}Parameter:{Fore.WHITE}
  --url <URL>     Target URL (contoh: http://localhost:8080)
  --threads <N>   Jumlah thread concurrent (default: 5)
  --duration <S>  Durasi testing dalam detik (default: 10)
  --method <M>    HTTP method GET/POST (default: GET)
  --delay <D>     Delay antar request dalam detik (default: 0)

{Fore.YELLOW}Contoh:{Fore.WHITE}
  python haqtivist.py --url http://localhost:8080 --threads 10 --duration 10
  python haqtivist.py --url http://localhost:8080 --threads 5 --duration 30 --delay 0.2
    """)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit()
    
    url = None
    threads = 5
    duration = 10
    method = "GET"
    delay = 0
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ["--help", "-h"]:
            show_help()
            sys.exit()
        elif arg == "--url" and i+1 < len(sys.argv):
            url = sys.argv[i+1]
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
        else:
            i += 1
    
    if url:
        target, port, endpoint = parse_url(url)
        print(f"\n{Fore.GREEN}[+] Memproses URL: {url}")
        attack_mode(target, port, endpoint, duration, threads, method, delay)
        show_final_report()
    else:
        print(f"{Fore.RED}[!] Error: Harus menggunakan --url")
        show_help()
