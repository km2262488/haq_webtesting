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

print("="*50)
print("   HAQTIVIST HTTP TESTER - SIMPLE VERSION")
print("="*50)

if len(sys.argv) < 5:
    print("Usage: python haqtivist.py <IP> <PORT> <THREADS> <DURATION>")
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

for _ in range(threads):
    t = threading.Thread(target=worker, args=(target, port, duration, stats, lock, stop_flag))
    t.start()
    thread_list.append(t)

# Hentikan tepat waktu, jangan menunggu response selesai
while time.time() - start_time < duration:
    if stop_flag.is_set():
        break
    time.sleep(0.1)
    
# Setelah duration habis, langsung stop
stop_flag.set()
            break
except KeyboardInterrupt:
    stop_flag.set()

for t in thread_list:
    t.join(timeout=1)

elapsed = time.time() - start_time
print(f"\n\n{'='*50}")
print("HASIL AKHIR")
print(f"{'='*50}")
print(f"✓ Success: {stats['success']}")
print(f"✗ Fail: {stats['fail']}")
print(f"📦 Total: {stats['total']}")
print(f"⏱️ Durasi: {elapsed:.2f}s")
print(f"🚀 RPS: {stats['total']/elapsed:.1f}")
print(f"💾 Transfer: {stats['bytes']/1024:.1f} KB")
print(f"🎯 Success Rate: {stats['success']/stats['total']*100:.1f}%" if stats['total'] > 0 else "N/A")
print(f"{'='*50}")
