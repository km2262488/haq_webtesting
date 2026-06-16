#!/usr/bin/env python3
"""
HAQTIVIST TOOL - Enhanced Version for Web Testing
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
import ssl  # Untuk HTTPS support

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
    'url_tested': None,
    'min_response_time': float('inf'),
    'max_response_time': 0
}

lock = threading.Lock()
stop_flag = threading.Event()

# ============ PAYLOAD UNTUK POST ============
POST_PAYLOADS = [
    '{"username":"testuser","password":"testpass123"}',
    '{"email":"test@example.com","name":"Test User"}',
    '{"data":{"id":1,"value":"sample"}}',
    'username=admin&password=admin123',
    'search=query&page=1&limit=10',
]

# ============ HEADER VARIANTS ============
def generate_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]
    return random.choice(agents)

def generate_random_headers():
    """Generate random HTTP headers untuk testing yang lebih realistis"""
    return {
        "Accept": random.choice([
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "application/json,text/plain,*/*",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        ]),
        "Accept-Language": random.choice([
            "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "en-US,en;q=0.9",
            "id;q=0.9,en;q=0.8"
        ]),
        "Accept-Encoding": "gzip, deflate",
        "Connection": "close",
        "Cache-Control": random.choice(["no-cache", "max-age=0"]),
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": random.choice(["document", "empty", "script"]),
        "Sec-Fetch-Mode": random.choice(["navigate", "cors", "no-cors"]),
        "Sec-Fetch-Site": random.choice(["none", "same-origin", "cross-site"]),
    }

def save_report(filename="test_report.json"):
    """Simpan laporan testing dengan lebih detail"""
    elapsed = (stats['end_time'] - stats['start_time']) if stats['end_time'] and stats['start_time'] else 0
    
    report = {
        "tool": "HAQTIVIST HTTP TESTER",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "url_tested": stats['url_tested'],
        "test_config": {
            "duration": elapsed,
            "total_requests": stats['total_requests']
        },
        "statistics": {
            'success_2xx': stats['success_2xx'],
            'redirect_3xx': stats['redirect_3xx'],
            'client_error_4xx': stats['client_error_4xx'],
            'server_error_5xx': stats['server_error_5xx'],
            'timeout': stats['timeout'],
            'error': stats['error'],
            'success_rate': (stats['success_2xx'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
        },
        "performance": {
            "duration_seconds": elapsed,
            "avg_response_time_ms": (sum(stats['response_times']) / len(stats['response_times']) * 1000) if stats['response_times'] else 0,
            "min_response_time_ms": (stats['min_response_time'] * 1000) if stats['min_response_time'] != float('inf') else 0,
            "max_response_time_ms": (stats['max_response_time'] * 1000),
            "rps": stats['total_requests'] / elapsed if elapsed > 0 else 0,
            "total_bytes_transferred_mb": stats['bytes_transferred'] / (1024 * 1024)
        },
        "response_times": [round(t * 1000, 2) for t in stats['response_times'][:1000]]  # Sample untuk file size
    }
    
    try:
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"{Fore.GREEN}[+] Report saved to {filename}")
        return True
    except Exception as e:
        print(f"{Fore.RED}[!] Error saving report: {e}")
        return False

# ============ CORE TESTING FUNCTION ============
def test_request(target, port, endpoint="/", method="GET", delay=0, payload=None, use_https=False, custom_headers=None):
    global stats
    start_time = time.time()
    s = None
    
    try:
        # Create socket with HTTPS support
        if use_https:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            s = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=target)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        s.settimeout(10)
        s.connect((target, port))
        
        # Build request
        request = f"{method} {endpoint} HTTP/1.1\r\n"
        request += f"Host: {target}\r\n"
        request += f"User-Agent: {generate_user_agent()}\r\n"
        
        # Add custom headers
        headers = generate_random_headers()
        if custom_headers:
            headers.update(custom_headers)
        
        for key, value in headers.items():
            request += f"{key}: {value}\r\n"
        
        # Add payload untuk POST
        if method == "POST" and payload:
            content_type = "application/json" if payload.startswith('{') else "application/x-www-form-urlencoded"
            request += f"Content-Type: {content_type}\r\n"
            request += f"Content-Length: {len(payload)}\r\n"
            request += "\r\n"
            request += payload
        else:
            request += "\r\n"
        
        s.send(request.encode())
        
        # Receive response
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
        
        # Update stats
        with lock:
            stats['total_requests'] += 1
            stats['bytes_transferred'] += len(response)
            stats['response_times'].append(response_time)
            
            if response_time < stats['min_response_time']:
                stats['min_response_time'] = response_time
            if response_time > stats['max_response_time']:
                stats['max_response_time'] = response_time
            
            if len(response) > 0:
                response_str = response[:200].decode('utf-8', errors='ignore')
                
                # Parse status code
                if "200" in response_str or "201" in response_str or "204" in response_str:
                    stats['success'] += 1
                    stats['success_2xx'] += 1
                elif "301" in response_str or "302" in response_str or "307" in response_str or "308" in response_str:
                    stats['success'] += 1
                    stats['redirect_3xx'] += 1
                elif "400" in response_str or "401" in response_str or "403" in response_str or "404" in response_str or "429" in response_str:
                    stats['client_error_4xx'] += 1
                elif "500" in response_str or "502" in response_str or "503" in response_str or "504" in response_str:
                    stats['server_error_5xx'] += 1
                else:
                    stats['success'] += 1
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

def worker(target, port, endpoint, method, duration, delay, payload=None, use_https=False, headers=None):
    start_time = time.time()
    while not stop_flag.is_set() and (time.time() - start_time) < duration:
        test_request(target, port, endpoint, method, delay, payload, use_https, headers)
        if delay > 0:
            time.sleep(delay)

# ============ MAIN ATTACK MODE ============
def attack_mode(target, port, endpoint, duration, threads, method="GET", delay=0, payload=None, use_https=False, headers=None):
    """Mode testing dengan LIVE STATS REAL TIME"""
    stats['url_tested'] = f"{'https' if use_https else 'http'}://{target}:{port}{endpoint}"
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.YELLOW}🎯 TARGET: {Fore.WHITE}{stats['url_tested']}")
    print(f"{Fore.CYAN}{'='*80}")
    print(f"{Fore.WHITE}📋 Konfigurasi Test:")
    print(f"   {Fore.LIGHTBLACK_EX}├─ Method:     {Fore.LIGHTWHITE_EX}{method}")
    print(f"   {Fore.LIGHTBLACK_EX}├─ Threads:    {Fore.LIGHTWHITE_EX}{threads}")
    print(f"   {Fore.LIGHTBLACK_EX}├─ Duration:   {Fore.LIGHTWHITE_EX}{duration} detik")
    print(f"   {Fore.LIGHTBLACK_EX}├─ Delay:      {Fore.LIGHTWHITE_EX}{delay} detik")
    print(f"   {Fore.LIGHTBLACK_EX}├─ Protocol:   {Fore.LIGHTWHITE_EX}{'HTTPS' if use_https else 'HTTP'}")
    if method == "POST":
        print(f"   {Fore.LIGHTBLACK_EX}└─ Payload:    {Fore.LIGHTWHITE_EX}{str(payload)[:50]}{'...' if len(str(payload)) > 50 else ''}")
    print(f"{Fore.CYAN}{'='*80}")
    
    print(f"\n{Fore.YELLOW}⚡ Starting load test... Press Ctrl+C to stop")
    print(f"{Fore.LIGHTBLACK_EX}[*] Memulai testing... Tekan Ctrl+C untuk berhenti\n")
    
    # Header Live Stats
    print(f"{Fore.LIGHTBLACK_EX}{'─'*85}")
    print(f"{Fore.CYAN}⏱️  WAKTU    │  ✅ 2xx  │  ↻ 3xx  │  ⚠ 4xx  │  ❌ 5xx  │  ⌛ T/O  │  📊 RPS    │  🧵 THR")
    print(f"{Fore.LIGHTBLACK_EX}{'─'*85}")
    
    start_time = time.time()
    stats['start_time'] = start_time
    
    thread_list = []
    last_update = 0
    
    try:
        # Start threads
        for _ in range(threads):
            t = threading.Thread(target=worker, args=(target, port, endpoint, method, duration, delay, payload, use_https, headers))
            t.daemon = True
            t.start()
            thread_list.append(t)
        
        # LIVE STATS UPDATE REAL TIME
        while any(t.is_alive() for t in thread_list):
            time.sleep(0.2)
            elapsed = time.time() - start_time
            
            if elapsed >= duration:
                stop_flag.set()
                break
            
            # Update display every 0.3 seconds
            if time.time() - last_update >= 0.3:
                with lock:
                    rps = stats['total_requests'] / elapsed if elapsed > 0 else 0
                    active = len([t for t in thread_list if t.is_alive()])
                    
                    sys.stdout.write(f"\r\033[K")
                    sys.stdout.write(
                        f"\r{Fore.CYAN}{elapsed:6.1f}s   │ "
                        f"{Fore.GREEN}{stats['success_2xx']:6d}  │ "
                        f"{Fore.LIGHTBLUE_EX}{stats['redirect_3xx']:6d}  │ "
                        f"{Fore.YELLOW}{stats['client_error_4xx']:6d}  │ "
                        f"{Fore.RED}{stats['server_error_5xx']:6d}  │ "
                        f"{Fore.MAGENTA}{stats['timeout']:6d}  │ "
                        f"{Fore.LIGHTWHITE_EX}{rps:8.1f}  │ "
                        f"{Fore.LIGHTCYAN_EX}{active:4d}"
                    )
                    sys.stdout.flush()
                    last_update = time.time()
        
        print(f"\n{Fore.LIGHTBLACK_EX}{'─'*85}")
        
        # Graceful shutdown
        stop_flag.set()
        for t in thread_list:
            t.join(timeout=1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}[!] Testing dihentikan oleh user")
        stop_flag.set()
    
    stats['end_time'] = time.time()

# ============ REPORT ============
def show_final_report():
    elapsed = stats['end_time'] - stats['start_time'] if stats['end_time'] and stats['start_time'] else 0
    success_rate = (stats['success_2xx'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
    
    print(f"\n\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.YELLOW}📊 FINAL TEST REPORT")
    print(f"{Fore.CYAN}{'='*80}")
    
    print(f"\n{Fore.WHITE}📈 REQUEST STATISTICS:")
    print(f"  {Fore.GREEN}✅ 2xx Success:      {stats['success_2xx']:>8} ({success_rate:.1f}%)")
    print(f"  {Fore.LIGHTBLUE_EX}↻ 3xx Redirect:     {stats['redirect_3xx']:>8}")
    print(f"  {Fore.YELLOW}⚠ 4xx Client Error:  {stats['client_error_4xx']:>8}")
    print(f"  {Fore.RED}🔥 5xx Server Error:  {stats['server_error_5xx']:>8}")
    print(f"  {Fore.MAGENTA}⌛ Timeout:          {stats['timeout']:>8}")
    print(f"  {Fore.RED}💥 Socket Error:     {stats['error']:>8}")
    print(f"  {Fore.WHITE}📦 Total Requests:   {stats['total_requests']:>8}")
    
    print(f"\n{Fore.WHITE}⚡ PERFORMANCE METRICS:")
    print(f"  {Fore.YELLOW}🕒 Duration:         {elapsed:>8.2f} detik")
    print(f"  {Fore.YELLOW}🚀 Requests/sec:     {stats['total_requests']/elapsed:>8.1f} RPS")
    
    if stats['response_times']:
        avg_response = sum(stats['response_times']) / len(stats['response_times']) * 1000
        print(f"  {Fore.YELLOW}⏱️  Avg Response:     {avg_response:>8.1f} ms")
        print(f"  {Fore.GREEN}⚡ Min Response:     {stats['min_response_time']*1000:>8.1f} ms")
        print(f"  {Fore.RED}🐌 Max Response:     {stats['max_response_time']*1000:>8.1f} ms")
    
    print(f"\n{Fore.WHITE}💾 BANDWIDTH:")
    print(f"  {Fore.YELLOW}📤 Total Transfer:   {stats['bytes_transferred']/1024/1024:>8.2f} MB")
    print(f"  {Fore.YELLOW}📤 Throughput:       {(stats['bytes_transferred']/elapsed)/1024:>8.1f} KB/s")
    
    print(f"\n{Fore.WHITE}🎯 SUCCESS RATE: ", end="")
    if success_rate >= 95:
        print(f"{Fore.GREEN}{success_rate:.1f}% 🏆 Excellent")
    elif success_rate >= 80:
        print(f"{Fore.LIGHTGREEN_EX}{success_rate:.1f}% ✅ Good")
    elif success_rate >= 60:
        print(f"{Fore.YELLOW}{success_rate:.1f}% ⚠️  Average")
    else:
        print(f"{Fore.RED}{success_rate:.1f}% ❌ Poor - Perlu Investigasi")
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.LIGHTBLACK_EX}Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Auto-save report
    save_report()

# ============ URL PARSING ============
def parse_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    parsed = urlparse(url)
    target = parsed.hostname
    port = parsed.port
    use_https = parsed.scheme == 'https'
    
    if not port:
        port = 443 if use_https else 80
    
    endpoint = parsed.path if parsed.path else '/'
    if parsed.query:
        endpoint += f"?{parsed.query}"
    
    return target, port, endpoint, use_https

# ============ HELP ============
def show_help():
    print(f"""
{Fore.CYAN}HAQTIVIST HTTP LOAD TESTER v2.0
{Fore.LIGHTBLACK_EX}For testing your own web applications

{Fore.YELLOW}USAGE:{Fore.WHITE}
  python haqtivist.py --url <URL> [OPTIONS]

{Fore.YELLOW}REQUIRED:{Fore.WHITE}
  --url <URL>     Target URL (http://localhost:8080/api/test)

{Fore.YELLOW}OPTIONS:{Fore.WHITE}
  --threads <N>   Number of concurrent threads (default: 5)
  --duration <S>  Test duration in seconds (default: 10)
  --method <M>    HTTP method: GET or POST (default: GET)
  --delay <D>     Delay between requests in seconds (default: 0)
  --payload <P>   Payload for POST requests (default: auto-generate)

{Fore.YELLOW}EXAMPLES:{Fore.WHITE}
  # Basic GET test
  python haqtivist.py --url http://localhost:8080 --threads 10 --duration 10
  
  # POST test with specific payload
  python haqtivist.py --url http://localhost:8080/api/login --method POST --payload '{{"user":"admin","pass":"123"}}'
  
  # HTTPS test with 20 threads
  python haqtivist.py --url https://example.com --threads 20 --duration 30 --delay 0.1

{Fore.YELLOW}OUTPUT:{Fore.WHITE}
  - Real-time statistics on console
  - JSON report: test_report.json
  
{Fore.RED}⚠️  DISCLAIMER:{Fore.WHITE}
  Use this tool only on systems you own or have permission to test.
  Unauthorized testing is illegal.
    """)

# ============ MAIN ============
if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit()
    
    # Parse arguments
    url = None
    threads = 5
    duration = 10
    method = "GET"
    delay = 0
    payload = None
    
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
        elif arg == "--payload" and i+1 < len(sys.argv):
            payload = sys.argv[i+1]
            i += 2
        else:
            print(f"{Fore.RED}[!] Unknown argument: {arg}")
            show_help()
            sys.exit()
    
    if not url:
        print(f"{Fore.RED}[!] Error: --url is required")
        show_help()
        sys.exit()
    
    # Parse URL and run test
    try:
        target, port, endpoint, use_https = parse_url(url)
        
        # Generate payload if not specified
        if method == "POST" and not payload:
            payload = random.choice(POST_PAYLOADS)
        
        print(f"\n{Fore.GREEN}[+] Target: {target}:{port}{endpoint}")
        print(f"{Fore.GREEN}[+] Protocol: {'HTTPS' if use_https else 'HTTP'}")
        
        attack_mode(target, port, endpoint, duration, threads, method, delay, payload, use_https)
        show_final_report()
        
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}")
        sys.exit(1)
