#!/usr/bin/env python3
"""
HAQTIVIST TOOL - Enhanced with Follow Redirect, Endpoint Testing & Monitoring
"""

import socket
import threading
import time
import sys
import random
import json
import re
from datetime import datetime
from urllib.parse import urlparse, urljoin
from colorama import init, Fore, Style
import ssl
from collections import defaultdict

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
    'max_response_time': 0,
    'redirect_chain': [],
    'status_code_distribution': defaultdict(int),
    'headers_received': defaultdict(lambda: defaultdict(int)),
    'response_sizes': []
}

lock = threading.Lock()
stop_flag = threading.Event()
monitor_data = {
    'timeline': [],
    'rps_history': [],
    'response_time_history': [],
    'error_rate_history': []
}

# ============ PAYLOAD ============
POST_PAYLOADS = [
    '{"username":"testuser","password":"testpass123"}',
    '{"email":"test@example.com","name":"Test User"}',
    '{"data":{"id":1,"value":"sample"}}',
    'username=admin&password=admin123',
    'search=query&page=1&limit=10',
    '{"action":"login","credentials":{"user":"demo","pass":"demo123"}}',
]

# ============ ENDPOINT SCENARIOS ============
ENDPOINT_SCENARIOS = {
    'basic': [
        {'endpoint': '/', 'method': 'GET', 'description': 'Homepage'},
        {'endpoint': '/about', 'method': 'GET', 'description': 'About Page'},
        {'endpoint': '/contact', 'method': 'GET', 'description': 'Contact Page'},
    ],
    'api': [
        {'endpoint': '/api/v1/users', 'method': 'GET', 'description': 'Get Users'},
        {'endpoint': '/api/v1/users/1', 'method': 'GET', 'description': 'Get User Detail'},
        {'endpoint': '/api/v1/auth/login', 'method': 'POST', 'description': 'Login', 'payload': True},
        {'endpoint': '/api/v1/data', 'method': 'POST', 'description': 'Create Data', 'payload': True},
        {'endpoint': '/api/v1/search', 'method': 'GET', 'description': 'Search', 'query': '?q=test'},
    ],
    'ecommerce': [
        {'endpoint': '/', 'method': 'GET', 'description': 'Homepage'},
        {'endpoint': '/products', 'method': 'GET', 'description': 'Product List'},
        {'endpoint': '/products/1', 'method': 'GET', 'description': 'Product Detail'},
        {'endpoint': '/cart', 'method': 'GET', 'description': 'Cart'},
        {'endpoint': '/checkout', 'method': 'POST', 'description': 'Checkout', 'payload': True},
    ],
    'wordpress': [
        {'endpoint': '/', 'method': 'GET', 'description': 'Homepage'},
        {'endpoint': '/wp-admin', 'method': 'GET', 'description': 'Admin Login'},
        {'endpoint': '/wp-json/wp/v2/posts', 'method': 'GET', 'description': 'API Posts'},
        {'endpoint': '/wp-login.php', 'method': 'POST', 'description': 'Login Form', 'payload': True},
    ],
    'custom': []
}

# ============ HELPERS ============
def generate_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Version/16.0 Mobile/15E148 Safari/604.1",
    ]
    return random.choice(agents)

def generate_random_headers():
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
    }

def extract_status_code(response):
    """Extract HTTP status code from response"""
    try:
        if len(response) > 0:
            response_str = response[:100].decode('utf-8', errors='ignore')
            match = re.search(r'HTTP/\d\.\d\s+(\d{3})', response_str)
            if match:
                return int(match.group(1))
            # Fallback: check for common status codes in response
            for code in [200, 201, 204, 301, 302, 303, 307, 308, 400, 401, 403, 404, 429, 500, 502, 503, 504]:
                if str(code) in response_str:
                    return code
    except:
        pass
    return None

def extract_redirect_location(response):
    """Extract Location header for redirect"""
    try:
        response_str = response.decode('utf-8', errors='ignore')
        lines = response_str.split('\r\n')
        for line in lines:
            if line.lower().startswith('location:'):
                location = line.split(':', 1)[1].strip()
                return location
    except:
        pass
    return None

def extract_server_header(response):
    """Extract Server header"""
    try:
        response_str = response.decode('utf-8', errors='ignore')
        lines = response_str.split('\r\n')
        for line in lines:
            if line.lower().startswith('server:'):
                server = line.split(':', 1)[1].strip()
                return server
    except:
        pass
    return None

def extract_content_type(response):
    """Extract Content-Type header"""
    try:
        response_str = response.decode('utf-8', errors='ignore')
        lines = response_str.split('\r\n')
        for line in lines:
            if line.lower().startswith('content-type:'):
                content_type = line.split(':', 1)[1].strip()
                return content_type
    except:
        pass
    return None

# ============ CORE TESTING WITH FOLLOW REDIRECT ============
def test_request_with_redirect(target, port, endpoint="/", method="GET", delay=0, payload=None, use_https=False, custom_headers=None, follow_redirect=True, max_redirects=5):
    global stats
    start_time = time.time()
    s = None
    redirect_count = 0
    current_target = target
    current_port = port
    current_endpoint = endpoint
    current_use_https = use_https
    redirect_chain = []
    
    try:
        response = None
        status_code = None
        
        while redirect_count <= max_redirects:
            s = None
            try:
                # Create socket
                if current_use_https:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    s = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=current_target)
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                s.settimeout(10)
                s.connect((current_target, current_port))
                
                # Build request
                request = f"{method} {current_endpoint} HTTP/1.1\r\n"
                request += f"Host: {current_target}\r\n"
                request += f"User-Agent: {generate_user_agent()}\r\n"
                
                headers = generate_random_headers()
                if custom_headers:
                    headers.update(custom_headers)
                
                for key, value in headers.items():
                    request += f"{key}: {value}\r\n"
                
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
                
                s.close()
                s = None
                
                # Extract status code
                status_code = extract_status_code(response)
                if status_code:
                    redirect_chain.append({
                        'url': f"{'https' if current_use_https else 'http'}://{current_target}:{current_port}{current_endpoint}",
                        'status_code': status_code
                    })
                
                # Check for redirect
                if follow_redirect and status_code and status_code in [301, 302, 303, 307, 308]:
                    location = extract_redirect_location(response)
                    if location:
                        redirect_count += 1
                        with lock:
                            stats['redirect_3xx'] += 1
                        
                        # Parse redirect location
                        parsed_location = urlparse(location)
                        if parsed_location.netloc:
                            current_target = parsed_location.hostname
                            current_port = parsed_location.port if parsed_location.port else (443 if parsed_location.scheme == 'https' else 80)
                            current_endpoint = parsed_location.path if parsed_location.path else '/'
                            if parsed_location.query:
                                current_endpoint += f"?{parsed_location.query}"
                            current_use_https = parsed_location.scheme == 'https'
                        else:
                            # Relative redirect
                            if location.startswith('/'):
                                current_endpoint = location
                            else:
                                current_endpoint = '/' + location
                        continue
                
                # Not a redirect or redirect limit reached
                break
                
            except Exception as e:
                if s:
                    try:
                        s.close()
                    except:
                        pass
                if redirect_count > 0 and status_code:
                    break
                raise e
            
            finally:
                if s:
                    try:
                        s.close()
                    except:
                        pass
        
        # Final response time
        response_time = time.time() - start_time
        
        # Update stats
        with lock:
            stats['total_requests'] += 1
            stats['bytes_transferred'] += len(response) if response else 0
            stats['response_times'].append(response_time)
            stats['response_sizes'].append(len(response) if response else 0)
            
            if response_time < stats['min_response_time']:
                stats['min_response_time'] = response_time
            if response_time > stats['max_response_time']:
                stats['max_response_time'] = response_time
            
            if status_code:
                stats['status_code_distribution'][status_code] += 1
                
                if 200 <= status_code < 300:
                    stats['success'] += 1
                    stats['success_2xx'] += 1
                elif 300 <= status_code < 400:
                    stats['success'] += 1
                    stats['redirect_3xx'] += 1
                elif 400 <= status_code < 500:
                    stats['client_error_4xx'] += 1
                elif 500 <= status_code < 600:
                    stats['server_error_5xx'] += 1
            else:
                stats['error'] += 1
            
            # Track headers
            if response:
                server = extract_server_header(response)
                if server:
                    stats['headers_received']['server'][server] += 1
                content_type = extract_content_type(response)
                if content_type:
                    stats['headers_received']['content-type'][content_type] += 1
            
            if redirect_chain:
                stats['redirect_chain'] = redirect_chain
        
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

def worker(target, port, endpoint, method, duration, delay, payload=None, use_https=False, headers=None, follow_redirect=True):
    start_time = time.time()
    while not stop_flag.is_set() and (time.time() - start_time) < duration:
        test_request_with_redirect(target, port, endpoint, method, delay, payload, use_https, headers, follow_redirect)
        if delay > 0:
            time.sleep(delay)

# ============ ATTACK MODE ============
def attack_mode(target, port, endpoint, duration, threads, method="GET", delay=0, payload=None, use_https=False, headers=None, follow_redirect=True, scenario_name=None):
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
    print(f"   {Fore.LIGHTBLACK_EX}├─ Redirect:   {Fore.LIGHTWHITE_EX}{'Follow' if follow_redirect else 'No Follow'}")
    if scenario_name:
        print(f"   {Fore.LIGHTBLACK_EX}└─ Scenario:   {Fore.LIGHTWHITE_EX}{scenario_name}")
    if method == "POST":
        print(f"   {Fore.LIGHTBLACK_EX}└─ Payload:    {Fore.LIGHTWHITE_EX}{str(payload)[:50]}{'...' if len(str(payload)) > 50 else ''}")
    print(f"{Fore.CYAN}{'='*80}")
    
    print(f"\n{Fore.YELLOW}⚡ Starting load test... Press Ctrl+C to stop")
    print(f"{Fore.LIGHTBLACK_EX}[*] Memulai testing... Tekan Ctrl+C untuk berhenti\n")
    
    print(f"{Fore.LIGHTBLACK_EX}{'─'*95}")
    print(f"{Fore.CYAN}⏱️  WAKTU    │  ✅ 2xx  │  ↻ 3xx  │  ⚠ 4xx  │  ❌ 5xx  │  ⌛ T/O  │  📊 RPS    │  📈 AVG(ms) │  🧵 THR")
    print(f"{Fore.LIGHTBLACK_EX}{'─'*95}")
    
    start_time = time.time()
    stats['start_time'] = start_time
    
    thread_list = []
    last_update = 0
    monitor_interval = 5  # seconds

    def analyze_results():
    print(f"\n{Fore.YELLOW}📊 DETAILED ANALYSIS:")
    
    # Response time distribution
    if stats['response_times']:
        sorted_times = sorted(stats['response_times'])
        percentiles = {
            'p50': sorted_times[int(len(sorted_times)*0.5)] * 1000,
            'p90': sorted_times[int(len(sorted_times)*0.9)] * 1000,
            'p95': sorted_times[int(len(sorted_times)*0.95)] * 1000,
            'p99': sorted_times[int(len(sorted_times)*0.99)] * 1000
        }
        print(f"  {Fore.WHITE}Response Time Percentiles:")
        print(f"    {Fore.GREEN}├─ P50 (median): {percentiles['p50']:.1f}ms")
        print(f"    {Fore.YELLOW}├─ P90:          {percentiles['p90']:.1f}ms")
        print(f"    {Fore.YELLOW}├─ P95:          {percentiles['p95']:.1f}ms")
        print(f"    {Fore.RED}└─ P99:          {percentiles['p99']:.1f}ms")
    
    try:
        for _ in range(threads):
            t = threading.Thread(target=worker, args=(target, port, endpoint, method, duration, delay, payload, use_https, headers, follow_redirect))
            t.daemon = True
            t.start()
            thread_list.append(t)
        
        while any(t.is_alive() for t in thread_list):
            time.sleep(0.2)
            elapsed = time.time() - start_time
            
            if elapsed >= duration:
                stop_flag.set()
                break
            
            if time.time() - last_update >= 0.3:
                with lock:
                    rps = stats['total_requests'] / elapsed if elapsed > 0 else 0
                    active = len([t for t in thread_list if t.is_alive()])
                    avg_response = (sum(stats['response_times']) / len(stats['response_times']) * 1000) if stats['response_times'] else 0
                    
                    sys.stdout.write(f"\r\033[K")
                    sys.stdout.write(
                        f"\r{Fore.CYAN}{elapsed:6.1f}s   │ "
                        f"{Fore.GREEN}{stats['success_2xx']:6d}  │ "
                        f"{Fore.LIGHTBLUE_EX}{stats['redirect_3xx']:6d}  │ "
                        f"{Fore.YELLOW}{stats['client_error_4xx']:6d}  │ "
                        f"{Fore.RED}{stats['server_error_5xx']:6d}  │ "
                        f"{Fore.MAGENTA}{stats['timeout']:6d}  │ "
                        f"{Fore.LIGHTWHITE_EX}{rps:8.1f}  │ "
                        f"{Fore.LIGHTCYAN_EX}{avg_response:8.1f}  │ "
                        f"{Fore.LIGHTCYAN_EX}{active:4d}"
                    )
                    sys.stdout.flush()
                    last_update = time.time()
                    
                    # Monitor data collection
                    if int(elapsed) % monitor_interval == 0 and int(elapsed) > 0:
                        monitor_data['timeline'].append(elapsed)
                        monitor_data['rps_history'].append(rps)
                        monitor_data['response_time_history'].append(avg_response)
                        error_rate = ((stats['error'] + stats['timeout']) / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
                        monitor_data['error_rate_history'].append(error_rate)
        
        print(f"\n{Fore.LIGHTBLACK_EX}{'─'*95}")
        
        stop_flag.set()
        for t in thread_list:
            t.join(timeout=1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}[!] Testing dihentikan oleh user")
        stop_flag.set()
    
    stats['end_time'] = time.time()

# ============ SCENARIO TESTING ============
def run_scenario_test(target, port, use_https, scenario_name, threads=10, duration=30, delay=0.1):
    """Run test scenario with multiple endpoints"""
    scenario = ENDPOINT_SCENARIOS.get(scenario_name)
    if not scenario:
        print(f"{Fore.RED}[!] Scenario '{scenario_name}' not found")
        return
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.YELLOW}🎯 RUNNING SCENARIO: {scenario_name.upper()}")
    print(f"{Fore.CYAN}{'='*80}")
    
    total_endpoints = len(scenario)
    results = []
    
    for idx, endpoint_config in enumerate(scenario, 1):
        endpoint = endpoint_config['endpoint']
        method = endpoint_config.get('method', 'GET')
        description = endpoint_config.get('description', '')
        
        print(f"\n{Fore.WHITE}[{idx}/{total_endpoints}] Testing: {Fore.YELLOW}{endpoint}")
        print(f"   {Fore.LIGHTBLACK_EX}├─ Method: {method}")
        print(f"   {Fore.LIGHTBLACK_EX}└─ Desc:   {description}")
        
        # Prepare payload if needed
        payload = None
        if endpoint_config.get('payload', False) and method == 'POST':
            payload = random.choice(POST_PAYLOADS)
        
        # Add query params if specified
        test_endpoint = endpoint
        if endpoint_config.get('query'):
            test_endpoint = endpoint + endpoint_config['query']
        
        # Reset stats for this endpoint
        endpoint_stats = stats.copy()
        for key in ['success_2xx', 'redirect_3xx', 'client_error_4xx', 'server_error_5xx', 
                    'timeout', 'error', 'total_requests', 'response_times']:
            stats[key] = 0
        stats['response_times'] = []
        stats['min_response_time'] = float('inf')
        stats['max_response_time'] = 0
        
        # Run test
        attack_mode(target, port, test_endpoint, duration, threads, method, delay, payload, use_https, follow_redirect=True, scenario_name=f"{scenario_name}/{endpoint}")
        
        # Collect results
        results.append({
            'endpoint': test_endpoint,
            'method': method,
            'description': description,
            'requests': stats['total_requests'],
            'success_rate': (stats['success_2xx'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0,
            'avg_response_ms': (sum(stats['response_times']) / len(stats['response_times']) * 1000) if stats['response_times'] else 0,
            'errors': stats['error'] + stats['timeout'],
            'status_codes': dict(stats['status_code_distribution'])
        })
        
        # Reset stats for next endpoint
        stats['status_code_distribution'] = defaultdict(int)
    
    # Show scenario summary
    show_scenario_summary(results, scenario_name)
    return results

def show_scenario_summary(results, scenario_name):
    print(f"\n\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.YELLOW}📊 SCENARIO SUMMARY: {scenario_name.upper()}")
    print(f"{Fore.CYAN}{'='*80}")
    
    total_requests = sum(r['requests'] for r in results)
    avg_success_rate = sum(r['success_rate'] for r in results) / len(results) if results else 0
    avg_response = sum(r['avg_response_ms'] for r in results) / len(results) if results else 0
    
    print(f"\n{Fore.WHITE}📈 Overall Performance:")
    print(f"  {Fore.YELLOW}├─ Total Requests:   {total_requests}")
    print(f"  {Fore.YELLOW}├─ Avg Success Rate: {avg_success_rate:.1f}%")
    print(f"  {Fore.YELLOW}└─ Avg Response:     {avg_response:.1f}ms")
    
    print(f"\n{Fore.WHITE}📊 Per-Endpoint Results:")
    print(f"{Fore.LIGHTBLACK_EX}{'─'*70}")
    print(f"{Fore.CYAN}Endpoint{' ':<30} │ Requests │ Success% │ Avg(ms)")
    print(f"{Fore.LIGHTBLACK_EX}{'─'*70}")
    
    for r in results:
        endpoint_display = r['endpoint'][:30] + '...' if len(r['endpoint']) > 30 else r['endpoint']
        print(f"{Fore.WHITE}{endpoint_display:<30} │ "
              f"{r['requests']:>8} │ "
              f"{r['success_rate']:>8.1f} │ "
              f"{r['avg_response_ms']:>8.1f}")
    
    # Save scenario report
    scenario_report = {
        'scenario': scenario_name,
        'timestamp': datetime.now().isoformat(),
        'results': results,
        'summary': {
            'total_requests': total_requests,
            'avg_success_rate': avg_success_rate,
            'avg_response_ms': avg_response
        }
    }
    
    filename = f"scenario_report_{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(scenario_report, f, indent=2)
    print(f"\n{Fore.GREEN}[+] Scenario report saved to {filename}")

# ============ MONITORING DISPLAY ============
def show_monitoring_report():
    print(f"\n\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.YELLOW}📊 MONITORING REPORT")
    print(f"{Fore.CYAN}{'='*80}")
    
    if monitor_data['rps_history']:
        print(f"\n{Fore.WHITE}📈 Performance Trend:")
        print(f"  {Fore.YELLOW}├─ Avg RPS:     {sum(monitor_data['rps_history'])/len(monitor_data['rps_history']):.1f}")
        print(f"  {Fore.YELLOW}├─ Max RPS:     {max(monitor_data['rps_history']):.1f}")
        print(f"  {Fore.YELLOW}├─ Avg Response: {sum(monitor_data['response_time_history'])/len(monitor_data['response_time_history']):.1f}ms")
        print(f"  {Fore.YELLOW}└─ Avg Error:   {sum(monitor_data['error_rate_history'])/len(monitor_data['error_rate_history']):.1f}%")
    
    # Status code distribution
    if stats['status_code_distribution']:
        print(f"\n{Fore.WHITE}📊 Status Code Distribution:")
        for code, count in sorted(stats['status_code_distribution'].items()):
            percentage = (count / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
            color = Fore.GREEN if code < 300 else Fore.YELLOW if code < 400 else Fore.RED
            print(f"  {color}├─ {code}: {count} ({percentage:.1f}%)")
    
    # Headers analysis
    if stats['headers_received']:
        print(f"\n{Fore.WHITE}📋 Headers Analysis:")
        for header, values in stats['headers_received'].items():
            print(f"  {Fore.YELLOW}├─ {header}:")
            for value, count in sorted(values.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"  │  {Fore.LIGHTWHITE_EX}└─ {value}: {count} requests")
    
    # Response size analysis
    if stats['response_sizes']:
        print(f"\n{Fore.WHITE}📦 Response Size Analysis:")
        avg_size = sum(stats['response_sizes']) / len(stats['response_sizes'])
        print(f"  {Fore.YELLOW}├─ Avg Size:   {avg_size/1024:.2f} KB")
        print(f"  {Fore.YELLOW}├─ Min Size:   {min(stats['response_sizes'])/1024:.2f} KB")
        print(f"  {Fore.YELLOW}└─ Max Size:   {max(stats['response_sizes'])/1024:.2f} KB")

# ============ REPORT ============
def save_report(filename="test_report.json"):
    elapsed = (stats['end_time'] - stats['start_time']) if stats['end_time'] and stats['start_time'] else 0
    
    report = {
        "tool": "HAQTIVIST HTTP TESTER v3.0",
        "timestamp": datetime.now().isoformat(),
        "url_tested": stats['url_tested'],
        "test_config": {
            "duration": elapsed,
            "total_requests": stats['total_requests'],
            "follow_redirect": True
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
        "status_code_distribution": dict(stats['status_code_distribution']),
        "headers_analysis": dict(stats['headers_received']),
        "redirect_chain": stats['redirect_chain'][:10] if stats['redirect_chain'] else [],
        "monitoring": {
            "rps_history": monitor_data['rps_history'][:100],
            "response_time_history": monitor_data['response_time_history'][:100],
            "error_rate_history": monitor_data['error_rate_history'][:100]
        }
    }
    
    try:
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"{Fore.GREEN}[+] Report saved to {filename}")
        return True
    except Exception as e:
        print(f"{Fore.RED}[!] Error saving report: {e}")
        return False

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
    
    # Show monitoring summary
    show_monitoring_report()
    
    # Show redirect chain if any
    if stats['redirect_chain']:
        print(f"\n{Fore.WHITE}🔗 Redirect Chain:")
        for idx, redirect in enumerate(stats['redirect_chain'][:5], 1):
            print(f"  {Fore.YELLOW}{idx}. {redirect['url']} → {redirect['status_code']}")
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.LIGHTBLACK_EX}Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    save_report()

# ============ URL PARSING ============
def parse_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    parsed = urlparse(url)
    target = parsed.hostname
    use_https = parsed.scheme == 'https'
    
    if parsed.port:
        port = parsed.port
    else:
        port = 443 if use_https else 80
    
    if target and ':' in target:
        target = target.split(':')[0]
    
    endpoint = parsed.path if parsed.path else '/'
    if parsed.query:
        endpoint += f"?{parsed.query}"
    
    return target, port, endpoint, use_https

# ============ HELP ============
def show_help():
    print(f"""
{Fore.CYAN}HAQTIVIST HTTP LOAD TESTER v3.0
{Fore.LIGHTBLACK_EX}For testing your own web applications

{Fore.YELLOW}USAGE:{Fore.WHITE}
  python haqtivist.py --url <URL> [OPTIONS]
  python haqtivist.py --scenario <SCENARIO> --url <URL> [OPTIONS]

{Fore.YELLOW}REQUIRED:{Fore.WHITE}
  --url <URL>     Target URL (http://localhost:8080/api/test)

{Fore.YELLOW}OPTIONS:{Fore.WHITE}
  --threads <N>   Number of concurrent threads (default: 5)
  --duration <S>  Test duration in seconds (default: 10)
  --method <M>    HTTP method: GET or POST (default: GET)
  --delay <D>     Delay between requests in seconds (default: 0)
  --payload <P>   Payload for POST requests (default: auto-generate)
  --no-redirect   Disable follow redirect (default: follow)

{Fore.YELLOW}SCENARIO OPTIONS:{Fore.WHITE}
  --scenario <S>  Test scenario: basic, api, ecommerce, wordpress, custom
  --endpoints <E> Custom endpoints (comma separated)
  --scenario-duration <S> Duration per endpoint in scenario (default: 5)

{Fore.YELLOW}EXAMPLES:{Fore.WHITE}
  # Basic GET test
  python haqtivist.py --url http://localhost:8080 --threads 10 --duration 10
  
  # POST test with specific payload
  python haqtivist.py --url http://localhost:8080/api/login --method POST --payload '{{"user":"admin","pass":"123"}}'
  
  # Run API scenario
  python haqtivist.py --scenario api --url https://api.example.com --threads 5 --scenario-duration 10
  
  # Custom endpoints
  python haqtivist.py --scenario custom --url http://localhost:8080 --endpoints "/,/about,/api/users" --threads 3

{Fore.YELLOW}SCENARIOS:{Fore.WHITE}
  basic        - Homepage, About, Contact
  api          - Users, Login, Data endpoints
  ecommerce    - Products, Cart, Checkout
  wordpress    - WordPress specific endpoints
  custom       - Your own endpoints

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
    scenario = None
    custom_endpoints = None
    scenario_duration = 5
    follow_redirect = True
    
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
        elif arg == "--no-redirect":
            follow_redirect = False
            i += 1
        elif arg == "--scenario" and i+1 < len(sys.argv):
            scenario = sys.argv[i+1].lower()
            i += 2
        elif arg == "--endpoints" and i+1 < len(sys.argv):
            custom_endpoints = sys.argv[i+1].split(',')
            i += 2
        elif arg == "--scenario-duration" and i+1 < len(sys.argv):
            scenario_duration = int(sys.argv[i+1])
            i += 2
        else:
            print(f"{Fore.RED}[!] Unknown argument: {arg}")
            show_help()
            sys.exit()
    
    if not url:
        print(f"{Fore.RED}[!] Error: --url is required")
        show_help()
        sys.exit()
    
    # Parse URL
    try:
        target, port, endpoint, use_https = parse_url(url)
        print(f"\n{Fore.GREEN}[+] Target: {target}:{port}{endpoint}")
        print(f"{Fore.GREEN}[+] Protocol: {'HTTPS' if use_https else 'HTTP'}")
        
        # Handle scenario testing
        if scenario:
            if scenario == 'custom' and custom_endpoints:
                # Build custom scenario
                ENDPOINT_SCENARIOS['custom'] = []
                for ep in custom_endpoints:
                    ep = ep.strip()
                    if ep.startswith('POST:'):
                        ep = ep.replace('POST:', '')
                        ENDPOINT_SCENARIOS['custom'].append({
                            'endpoint': ep,
                            'method': 'POST',
                            'description': f'Custom POST {ep}',
                            'payload': True
                        })
                    else:
                        ENDPOINT_SCENARIOS['custom'].append({
                            'endpoint': ep,
                            'method': 'GET',
                            'description': f'Custom GET {ep}'
                        })
            
            if scenario in ENDPOINT_SCENARIOS:
                run_scenario_test(target, port, use_https, scenario, threads, scenario_duration, delay)
            else:
                print(f"{Fore.RED}[!] Scenario '{scenario}' not found")
                print(f"{Fore.YELLOW}Available: {', '.join(ENDPOINT_SCENARIOS.keys())}")
                sys.exit()
        else:
            # Single endpoint test
            if method == "POST" and not payload:
                payload = random.choice(POST_PAYLOADS)
            
            attack_mode(target, port, endpoint, duration, threads, method, delay, payload, use_https, follow_redirect=follow_redirect)
            show_final_report()
        
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}")
        sys.exit(1)
