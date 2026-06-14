import socket
import threading
import time
import sys
from datetime import datetime

def test_request(target, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((target, port))
        s.send(b"GET / HTTP/1.1\r\nHost: " + target.encode() + b"\r\nConnection: close\r\n\r\n")
        
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.close()
        
        if b"200" in data:
            return True, len(data)
        return False, len(data)
    except Exception as e:
        return False, 0

def worker(target, port, duration, stats, lock, stop_flag):
    start = time.time()
    while not stop_flag.is_set() and time.time() - start < duration:
        success, bytes_recv = test_request(target, port)
        with lock:
            stats['total'] += 1
            if success:
                stats['success'] += 1
            else:
                stats['fail'] += 1
            stats['bytes'] += bytes_recv
        time.sleep(0.05)

# ============ MAIN PROGRAM ============
print("="*50)
print("   HAQTIVIST HTTP TESTER - SIMPLE VERSION")
print("="*50)

if len(sys.argv) < 5:
    print("Usage: python haq_simple.py <IP> <PORT> <THREADS> <DURATION>")
    print("Example: python haq_simple.py localhost 8080 5 10")
    sys.exit()

target = sys.argv[1]
port = int(sys.argv[2])
threads = int(sys.argv[3])
duration = int(sys.argv[4])

stats = {'success': 0, 'fail': 0, 'total': 0, 'bytes': 0}
lock = threading.Lock()
stop_flag = threading.Event()

print(f"\nTesting {target}:{port} with {threads} threads for {duration}s\n")

thread_list = []
start_time = time.time()

# Start all threads
for _ in range(threads):
    t = threading.Thread(target=worker, args=(target, port, duration, stats, lock, stop_flag))
    t.daemon = True
    t.start()
    thread_list.append(t)

# Live stats display
try:
    while time.time() - start_time < duration:
        elapsed = time.time() - start_time
        with lock:
            rps = stats['total'] / elapsed if elapsed > 0 else 0
            # Clear line and show stats
            sys.stdout.write(f"\r\033[K")
            sys.stdout.write(f"⏱️ {elapsed:5.1f}s | ✓ {stats['success']:6d} | ✗ {stats['fail']:6d} | 📊 RPS: {rps:6.1f}")
            sys.stdout.flush()
        time.sleep(0.3)
    
    # Setelah duration habis, stop semua thread
    stop_flag.set()
    
except KeyboardInterrupt:
    print(f"\n\n[!] Testing dihentikan oleh user")
    stop_flag.set()

# Wait for all threads to finish
for t in thread_list:
    t.join(timeout=2)

elapsed = time.time() - start_time

# Final report
print(f"\n\n{'='*50}")
print("HASIL AKHIR")
print(f"{'='*50}")
print(f"✓ Success: {stats['success']}")
print(f"✗ Fail: {stats['fail']}")
print(f"📦 Total: {stats['total']}")
print(f"⏱️ Durasi: {elapsed:.2f}s")
print(f"🚀 RPS: {stats['total']/elapsed:.1f}" if elapsed > 0 else "N/A")
print(f"💾 Transfer: {stats['bytes']/1024:.1f} KB")
if stats['total'] > 0:
    print(f"🎯 Success Rate: {stats['success']/stats['total']*100:.1f}%")
else:
    print("🎯 Success Rate: N/A")
print(f"{'='*50}")
