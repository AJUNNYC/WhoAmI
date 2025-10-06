from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
import uvicorn
import json
import time
import hashlib
import socket
import re
from datetime import datetime
import geoip2.database
import geoip2.errors
import ipaddress  # NEW

# Create FastAPI app instance
app = FastAPI(title="Maximum Signal Collector", version="2.0.0")

# Configure CORS middleware to allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://sultrier-harmonizable-bessie.ngrok-free.dev"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize GeoIP2 Reader (load database once at startup)
try:
    geoip_reader = geoip2.database.Reader('./GeoLite2-City.mmdb')
    print("✓ GeoIP2 database loaded successfully")
except Exception as e:
    print(f"⚠ Warning: Could not load GeoIP2 database: {e}")
    geoip_reader = None

# Pydantic model for comprehensive signal collection
class CollectedSignals(BaseModel):
    navigator: Optional[Dict[str, Any]] = None
    screen: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    tzOffsetMin: Optional[int] = None
    locale: Optional[str] = None
    performance: Optional[Dict[str, Any]] = None
    canvasFingerprintDataURL: Optional[str] = None
    webglRenderer: Optional[Dict[str, Any]] = None
    computedStyles: Optional[Dict[str, Any]] = None
    installedFontsDetection: Optional[List[str]] = None
    audioContextFingerprint: Optional[Dict[str, Any]] = None
    interaction: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None
    storage: Optional[Dict[str, Any]] = None
    deviceMotion: Optional[Dict[str, Any]] = None
    fileUploads: Optional[List[Dict[str, Any]]] = None
    documentReferrer: Optional[str] = None
    historyLength: Optional[int] = None
    previousUrlPath: Optional[str] = None
    mimeTypes: Optional[List[Dict[str, Any]]] = None
    plugins: Optional[List[Dict[str, Any]]] = None
    osHints: Optional[Dict[str, Any]] = None
    batteryStatus: Optional[Dict[str, Any]] = None

def is_private_ip(ip_str: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
    except ValueError:
        return True

def extract_client_ip(request: Request) -> str:
    """
    Prefer the first public IP from X-Forwarded-For, then X-Real-IP,
    falling back to request.client.host.
    Only trust headers if present (assumes you're using a trusted tunnel/reverse proxy).
    """
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        # XFF is a comma-separated list; the first is the original client
        for part in [p.strip() for p in xff.split(",")]:
            # Filter out empty/malformed; take first non-private/global IP
            try:
                ip_obj = ipaddress.ip_address(part)
                if not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local):
                    return part
            except ValueError:
                continue

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        try:
            ip_obj = ipaddress.ip_address(x_real_ip.strip())
            if not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local):
                return x_real_ip.strip()
        except ValueError:
            pass

    return request.client.host

def get_ip_geolocation(ip_address: str) -> Dict[str, Any]:
    """
    Get geolocation data from IP address using MaxMind GeoLite2 local database.
    Returns city, country, coordinates, timezone, etc.
    """
    if is_private_ip(ip_address):
        return {
            "ip": ip_address,
            "city": "localhost",
            "region": "localhost",
            "country": "localhost",
            "country_code": None,
            "postal": None,
            "latitude": None,
            "longitude": None,
            "timezone": None,
            "accuracy_radius": None,
            "note": "Private/localhost IP - no geolocation available"
        }

    if geoip_reader is None:
        return {"ip": ip_address, "error": "GeoIP2 database not loaded"}

    try:
        response = geoip_reader.city(ip_address)
        return {
            "ip": ip_address,
            "city": response.city.name,
            "city_geoname_id": response.city.geoname_id,
            "region": response.subdivisions.most_specific.name if response.subdivisions else None,
            "region_code": response.subdivisions.most_specific.iso_code if response.subdivisions else None,
            "region_geoname_id": response.subdivisions.most_specific.geoname_id if response.subdivisions else None,
            "country": response.country.name,
            "country_code": response.country.iso_code,
            "country_geoname_id": response.country.geoname_id,
            "continent": response.continent.name,
            "continent_code": response.continent.code,
            "postal": response.postal.code,
            "latitude": response.location.latitude,
            "longitude": response.location.longitude,
            "accuracy_radius": response.location.accuracy_radius,
            "timezone": response.location.time_zone,
            "metro_code": response.location.metro_code,
            "is_in_european_union": response.country.is_in_european_union,
            "registered_country": response.registered_country.name,
            "registered_country_code": response.registered_country.iso_code,
        }
    except geoip2.errors.AddressNotFoundError:
        return {"ip": ip_address, "error": f"IP address {ip_address} not found in database"}
    except Exception as e:
        return {"ip": ip_address, "error": f"Geolocation lookup failed: {str(e)}"}

@app.get("/")
def health():
    return {"status": "ok"}

@app.middleware("http")
async def add_client_hints_request(request: Request, call_next):
    """Middleware to request Client Hints on responses"""
    response = await call_next(request)

    client_hints = [
        "Sec-CH-UA", "Sec-CH-UA-Mobile", "Sec-CH-UA-Platform",
        "Sec-CH-UA-Arch", "Sec-CH-UA-Bitness", "Sec-CH-UA-Model",
        "Sec-CH-UA-Platform-Version", "Sec-CH-UA-Full-Version-List",
        "Sec-CH-UA-WoW64", "Device-Memory", "Downlink", "ECT", "RTT",
        "Save-Data", "Viewport-Width", "Width", "DPR",
        "Sec-CH-Prefers-Color-Scheme", "Sec-CH-Prefers-Reduced-Motion"
    ]
    response.headers["Accept-CH"] = ", ".join(client_hints)
    response.headers["Critical-CH"] = ", ".join(client_hints[:8])

    return response

@app.post("/collect")
async def collect_comprehensive_signals(request: Request, client_signals: CollectedSignals):
    """
    Maximum signal collection endpoint - collects everything possible without user permission.
    """
    request_start = time.time()

    # Get client IP (honor proxy headers) and perform geolocation lookup
    client_ip = extract_client_ip(request)
    geolocation_data = get_ip_geolocation(client_ip)

    server_signals = {
        "client_ip": client_ip,
        "client_port": request.client.port if hasattr(request.client, 'port') else None,
        "geolocation": geolocation_data,
        "http_method": request.method,
        "request_path": request.url.path,
        "query_string": str(request.query_params),
        "request_timestamp": time.time(),
        "request_datetime": datetime.utcnow().isoformat(),
        "url_scheme": request.url.scheme,
        "url_netloc": request.url.netloc,
        "url_full": str(request.url),
        "server_hostname": socket.gethostname(),
        "server_fqdn": socket.getfqdn(),
        "request_details": {
            "url_length": len(str(request.url)),
            "header_count": len(request.headers),
            "total_header_size": sum(len(k) + len(v) for k, v in request.headers.items()),
            "method_is_safe": request.method in ["GET", "HEAD", "OPTIONS"],
            "is_ajax": request.headers.get("x-requested-with", "").lower() == "xmlhttprequest",
            "is_prefetch": request.headers.get("x-moz") == "prefetch" or request.headers.get("x-purpose") == "preview",
            "is_secure": request.url.scheme == "https",
        },
        "http_headers": {
            "user_agent": request.headers.get("user-agent"),
            "accept": request.headers.get("accept"),
            "accept_language": request.headers.get("accept-language"),
            "accept_encoding": request.headers.get("accept-encoding"),
            "referer": request.headers.get("referer"),
            "cookie": request.headers.get("cookie"),
            "host": request.headers.get("host"),
            "origin": request.headers.get("origin"),
            "connection": request.headers.get("connection"),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
            "cache_control": request.headers.get("cache-control"),
            "pragma": request.headers.get("pragma"),
            "dnt": request.headers.get("dnt"),
            "upgrade_insecure_requests": request.headers.get("upgrade-insecure-requests"),
            "if_modified_since": request.headers.get("if-modified-since"),
            "if_none_match": request.headers.get("if-none-match"),
            "if_match": request.headers.get("if-match"),
            "if_unmodified_since": request.headers.get("if-unmodified-since"),
            "if_range": request.headers.get("if-range"),
            "range": request.headers.get("range"),
            "sec_fetch_dest": request.headers.get("sec-fetch-dest"),
            "sec_fetch_mode": request.headers.get("sec-fetch-mode"),
            "sec_fetch_site": request.headers.get("sec-fetch-site"),
            "sec_fetch_user": request.headers.get("sec-fetch-user"),
            "sec_gpc": request.headers.get("sec-gpc"),
            "sec_ch_ua": request.headers.get("sec-ch-ua"),
            "sec_ch_ua_mobile": request.headers.get("sec-ch-ua-mobile"),
            "sec_ch_ua_platform": request.headers.get("sec-ch-ua-platform"),
            "sec_ch_ua_arch": request.headers.get("sec-ch-ua-arch"),
            "sec_ch_ua_bitness": request.headers.get("sec-ch-ua-bitness"),
            "sec_ch_ua_full_version": request.headers.get("sec-ch-ua-full-version"),
            "sec_ch_ua_full_version_list": request.headers.get("sec-ch-ua-full-version-list"),
            "sec_ch_ua_model": request.headers.get("sec-ch-ua-model"),
            "sec_ch_ua_platform_version": request.headers.get("sec-ch-ua-platform-version"),
            "sec_ch_ua_wow64": request.headers.get("sec-ch-ua-wow64"),
            "save_data": request.headers.get("save-data"),
            "device_memory": request.headers.get("device-memory"),
            "downlink": request.headers.get("downlink"),
            "ect": request.headers.get("ect"),
            "rtt": request.headers.get("rtt"),
            "viewport_width": request.headers.get("viewport-width"),
            "width": request.headers.get("width"),
            "dpr": request.headers.get("dpr"),
            "sec_ch_prefers_color_scheme": request.headers.get("sec-ch-prefers-color-scheme"),
            "sec_ch_prefers_reduced_motion": request.headers.get("sec-ch-prefers-reduced-motion"),
            "sec_ch_prefers_reduced_transparency": request.headers.get("sec-ch-prefers-reduced-transparency"),
            "authorization": request.headers.get("authorization"),
            "proxy_authorization": request.headers.get("proxy-authorization"),
            "x_forwarded_for": request.headers.get("x-forwarded-for"),
            "x_forwarded_host": request.headers.get("x-forwarded-host"),
            "x_forwarded_proto": request.headers.get("x-forwarded-proto"),
            "x_forwarded_port": request.headers.get("x-forwarded-port"),
            "x_real_ip": request.headers.get("x-real-ip"),
            "x_client_ip": request.headers.get("x-client-ip"),
            "x_cluster_client_ip": request.headers.get("x-cluster-client-ip"),
            "forwarded": request.headers.get("forwarded"),
            "via": request.headers.get("via"),
            "cf_connecting_ip": request.headers.get("cf-connecting-ip"),
            "cf_ipcountry": request.headers.get("cf-ipcountry"),
            "cf_ray": request.headers.get("cf-ray"),
            "cf_visitor": request.headers.get("cf-visitor"),
            "true_client_ip": request.headers.get("true-client-ip"),
            "fastly_client_ip": request.headers.get("fastly-client-ip"),
            "x_azure_clientip": request.headers.get("x-azure-clientip"),
            "x_azure_socketip": request.headers.get("x-azure-socketip"),
            "x_requested_with": request.headers.get("x-requested-with"),
            "x_moz": request.headers.get("x-moz"),
            "x_purpose": request.headers.get("x-purpose"),
            "from": request.headers.get("from"),
            "max_forwards": request.headers.get("max-forwards"),
            "te": request.headers.get("te"),
            "trailer": request.headers.get("trailer"),
            "transfer_encoding": request.headers.get("transfer-encoding"),
            "expect": request.headers.get("expect"),
            "user_agent_parsed": parse_user_agent(request.headers.get("user-agent", "")),
        },
        "accept_language_parsed": parse_accept_language(request.headers.get("accept-language", "")),
        "accept_encoding_list": [enc.strip() for enc in request.headers.get("accept-encoding", "").split(",") if enc.strip()],
        "fingerprints": {
            "header_order_hash": hashlib.md5(str(list(request.headers.keys())).encode()).hexdigest(),
            "header_values_hash": hashlib.md5(str(dict(request.headers)).encode()).hexdigest(),
            "full_request_hash": hashlib.sha256(
                f"{request.method}{request.url.path}{dict(request.headers)}".encode()
            ).hexdigest(),
        },
        "bot_detection": {
            "is_bot_likely": is_bot(request.headers.get("user-agent", "")),
            "bot_patterns_matched": detect_bot_patterns(request.headers.get("user-agent", "")),
            "has_automation_headers": detect_automation_headers(request.headers),
        },
        "all_headers_raw": dict(request.headers),
    }

    response_time_ms = (time.time() - request_start) * 1000

    comprehensive_data = {
        "collection_metadata": {
            "timestamp": time.time(),
            "timestamp_iso": datetime.utcnow().isoformat(),
            "response_time_ms": response_time_ms,
            "collection_version": "2.0.0",
            "collector_type": "maximum_signals"
        },
        "server_signals": server_signals,
        "client_signals": client_signals.dict(),
        "signal_summary": {
            "total_server_signals": count_non_null_values(server_signals),
            "total_client_signals": count_non_null_values(client_signals.dict()),
            "collection_completeness": calculate_completeness(client_signals.dict()),
            "unique_identifiers": generate_unique_identifiers(server_signals, client_signals.dict())
        }
    }

    print("=" * 100)
    print("MAXIMUM SIGNAL COLLECTION COMPLETE")
    print("=" * 100)
    print(f"Collection Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Response Time: {response_time_ms:.2f}ms")
    print(f"Client IP: {client_ip}")
    print(f"Geo lookup raw: {geolocation_data}")  # ALWAYS show raw result

    # Print geolocation info if available
    if isinstance(geolocation_data, dict) and geolocation_data.get("city") is not None:
        print(f"Location: {geolocation_data.get('city')}, {geolocation_data.get('region')}, {geolocation_data.get('country')}")
        print(f"Coordinates: {geolocation_data.get('latitude')}, {geolocation_data.get('longitude')}")
        print(f"Timezone: {geolocation_data.get('timezone')}")

    print(f"User Agent: {request.headers.get('user-agent', 'Unknown')[:100]}...")
    print(f"Bot Detection: {server_signals['bot_detection']['is_bot_likely']}")
    print("-" * 100)

    signal_categories = {
        "Network/HTTP": len(server_signals.get('http_headers', {})),
        "Geolocation": count_non_null_values(geolocation_data),
        "Navigator/Device": count_non_null_values(client_signals.navigator),
        "Screen/Viewport": count_non_null_values(client_signals.screen),
        "Performance": count_non_null_values(client_signals.performance),
        "Graphics/Fingerprinting": sum([
            1 if client_signals.canvasFingerprintDataURL else 0,
            count_non_null_values(client_signals.webglRenderer),
            len(client_signals.installedFontsDetection or [])
        ]),
        "Interaction/Behavior": count_non_null_values(client_signals.interaction),
        "Capabilities": count_non_null_values(client_signals.capabilities),
        "Storage": count_non_null_values(client_signals.storage),
        "Device Motion": count_non_null_values(client_signals.deviceMotion)
    }

    for category, count in signal_categories.items():
        if count:
            print(f"{category}: {count} signals collected")

    print("-" * 100)
    print("FULL DATA DUMP:")
    print(json.dumps(comprehensive_data, indent=2, default=str))
    print("=" * 100)

    return {
        "status": "success",
        "message": "Maximum signal collection completed",
        "response_status": 200,
        "response_time_ms": response_time_ms,
        "data": comprehensive_data
    }

def parse_user_agent(user_agent: str) -> Dict[str, Any]:
    ua_lower = user_agent.lower()
    parsed = {
        "raw": user_agent,
        "length": len(user_agent),
        "os": "unknown",
        "os_version": None,
        "browser": "unknown",
        "browser_version": None,
        "is_mobile": False,
        "is_tablet": False,
        "is_bot": False,
        "device_type": "desktop",
        "engine": "unknown"
    }

    if "windows nt 10.0" in ua_lower:
        parsed["os"] = "windows"
        parsed["os_version"] = "10"
    elif "windows nt 6.3" in ua_lower:
        parsed["os"] = "windows"
        parsed["os_version"] = "8.1"
    elif "windows nt 6.2" in ua_lower:
        parsed["os"] = "windows"
        parsed["os_version"] = "8"
    elif "windows nt 6.1" in ua_lower:
        parsed["os"] = "windows"
        parsed["os_version"] = "7"
    elif "windows" in ua_lower:
        parsed["os"] = "windows"
    elif "mac os x" in ua_lower:
        parsed["os"] = "macos"
        mac_version = re.search(r'mac os x (\d+[._]\d+[._]?\d*)', ua_lower)
        if mac_version:
            parsed["os_version"] = mac_version.group(1).replace('_', '.')
    elif "linux" in ua_lower and "android" not in ua_lower:
        parsed["os"] = "linux"
    elif "android" in ua_lower:
        parsed["os"] = "android"
        parsed["is_mobile"] = True
        android_version = re.search(r'android (\d+\.?\d*)', ua_lower)
        if android_version:
            parsed["os_version"] = android_version.group(1)
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        parsed["os"] = "ios"
        ios_version = re.search(r'os (\d+[._]\d+[._]?\d*)', ua_lower)
        if ios_version:
            parsed["os_version"] = ios_version.group(1).replace('_', '.')

    if "edg/" in ua_lower or "edge/" in ua_lower:
        parsed["browser"] = "edge"
        edge_version = re.search(r'edg[e]?/(\d+\.?\d*)', ua_lower)
        if edge_version:
            parsed["browser_version"] = edge_version.group(1)
    elif "chrome/" in ua_lower and "edg" not in ua_lower:
        parsed["browser"] = "chrome"
        chrome_version = re.search(r'chrome/(\d+\.?\d*)', ua_lower)
        if chrome_version:
            parsed["browser_version"] = chrome_version.group(1)
    elif "firefox/" in ua_lower:
        parsed["browser"] = "firefox"
        firefox_version = re.search(r'firefox/(\d+\.?\d*)', ua_lower)
        if firefox_version:
            parsed["browser_version"] = firefox_version.group(1)
    elif "safari/" in ua_lower and "chrome" not in ua_lower:
        parsed["browser"] = "safari"
        safari_version = re.search(r'version/(\d+\.?\d*)', ua_lower)
        if safari_version:
            parsed["browser_version"] = safari_version.group(1)
    elif "opera" in ua_lower or "opr/" in ua_lower:
        parsed["browser"] = "opera"
        opera_version = re.search(r'(?:opera|opr)/(\d+\.?\d*)', ua_lower)
        if opera_version:
            parsed["browser_version"] = opera_version.group(1)

    if "gecko" in ua_lower and "like gecko" not in ua_lower:
        parsed["engine"] = "gecko"
    elif "webkit" in ua_lower:
        parsed["engine"] = "webkit"
    elif "trident" in ua_lower:
        parsed["engine"] = "trident"
    elif "blink" in ua_lower:
        parsed["engine"] = "blink"

    if "mobile" in ua_lower or "android" in ua_lower and "mobile" in ua_lower:
        parsed["is_mobile"] = True
        parsed["device_type"] = "mobile"
    if "tablet" in ua_lower or "ipad" in ua_lower:
        parsed["is_tablet"] = True
        parsed["device_type"] = "tablet"

    parsed["is_bot"] = is_bot(user_agent)

    return parsed

def parse_accept_language(accept_language: str) -> List[Dict[str, Any]]:
    if not accept_language:
        return []

    languages = []
    parts = accept_language.split(",")

    for part in parts:
        part = part.strip()
        if ";q=" in part:
            lang, quality = part.split(";q=")
            languages.append({
                "language": lang.strip(),
                "quality": float(quality.strip()),
            })
        else:
            languages.append({
                "language": part,
                "quality": 1.0,
            })

    languages.sort(key=lambda x: x["quality"], reverse=True)
    return languages

def is_bot(user_agent: str) -> bool:
    if not user_agent:
        return False

    ua_lower = user_agent.lower()
    bot_indicators = [
        'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python',
        'java', 'http', 'headless', 'phantom', 'selenium', 'puppeteer',
        'slurp', 'facebook', 'twitter', 'linkedinbot', 'whatsapp',
        'telegram', 'discord', 'slack', 'google', 'bing', 'yahoo',
        'baidu', 'yandex', 'duckduck', 'archive', 'scrapy'
    ]

    return any(indicator in ua_lower for indicator in bot_indicators)

def detect_bot_patterns(user_agent: str) -> List[str]:
    if not user_agent:
        return []

    ua_lower = user_agent.lower()
    patterns = {
        'googlebot': 'Google Bot',
        'bingbot': 'Bing Bot',
        'slurp': 'Yahoo Bot',
        'duckduckbot': 'DuckDuckGo Bot',
        'baiduspider': 'Baidu Spider',
        'yandexbot': 'Yandex Bot',
        'facebookexternalhit': 'Facebook Bot',
        'twitterbot': 'Twitter Bot',
        'linkedinbot': 'LinkedIn Bot',
        'whatsapp': 'WhatsApp',
        'telegrambot': 'Telegram Bot',
        'discordbot': 'Discord Bot',
        'slackbot': 'Slack Bot',
        'curl': 'cURL',
        'wget': 'Wget',
        'python': 'Python Script',
        'java': 'Java Client',
        'selenium': 'Selenium',
        'puppeteer': 'Puppeteer',
        'playwright': 'Playwright',
        'headless': 'Headless Browser',
        'phantom': 'PhantomJS',
    }

    matched = []
    for pattern, name in patterns.items():
        if pattern in ua_lower:
            matched.append(name)

    return matched

def detect_automation_headers(headers: Dict) -> bool:
    automation_indicators = [
        headers.get("x-requested-with") == "XMLHttpRequest",
        "headless" in headers.get("user-agent", "").lower(),
        "selenium" in headers.get("user-agent", "").lower(),
        "puppeteer" in headers.get("user-agent", "").lower(),
        "playwright" in headers.get("user-agent", "").lower(),
        headers.get("sec-ch-ua") and "Headless" in headers.get("sec-ch-ua", ""),
    ]

    return any(automation_indicators)

def count_non_null_values(data: Any) -> int:
    if isinstance(data, dict):
        count = 0
        for value in data.values():
            if value is not None:
                if isinstance(value, (dict, list)):
                    count += count_non_null_values(value)
                else:
                    count += 1
        return count
    elif isinstance(data, list):
        return sum(1 for item in data if item is not None)
    else:
        return 1 if data is not None else 0

def calculate_completeness(client_signals: Dict[str, Any]) -> Dict[str, float]:
    categories = {
        "navigator": client_signals.get("navigator", {}),
        "screen": client_signals.get("screen", {}),
        "performance": client_signals.get("performance", {}),
        "interaction": client_signals.get("interaction", {}),
        "capabilities": client_signals.get("capabilities", {}),
        "storage": client_signals.get("storage", {})
    }

    completeness = {}
    for category, data in categories.items():
        if data:
            total_possible = len(data) if isinstance(data, dict) else 1
            collected = count_non_null_values(data)
            completeness[category] = (collected / total_possible) * 100 if total_possible > 0 else 0

    return completeness

def generate_unique_identifiers(server_signals: Dict, client_signals: Dict) -> Dict[str, str]:
    ua = server_signals.get('http_headers', {}).get('user_agent', '')
    accept_lang = server_signals.get('http_headers', {}).get('accept_language', '')
    accept_enc = server_signals.get('http_headers', {}).get('accept_encoding', '')
    canvas = client_signals.get('canvasFingerprintDataURL', '')
    webgl_renderer = str(client_signals.get('webglRenderer', {}))
    screen_info = str(client_signals.get('screen', {}))
    navigator_info = str(client_signals.get('navigator', {}))
    combined = f"{ua}|{accept_lang}|{accept_enc}|{canvas}|{webgl_renderer}|{screen_info}|{navigator_info}"

    return {
        "basic_fingerprint": hashlib.md5(f"{ua}{accept_lang}".encode()).hexdigest(),
        "canvas_fingerprint": hashlib.sha256(canvas.encode()).hexdigest() if canvas else None,
        "webgl_fingerprint": hashlib.sha256(webgl_renderer.encode()).hexdigest(),
        "screen_fingerprint": hashlib.sha256(screen_info.encode()).hexdigest(),
        "combined_fingerprint": hashlib.sha256(combined.encode()).hexdigest(),
        "session_id": hashlib.sha256(f"{combined}{time.time()}".encode()).hexdigest()[:32]
    }

if __name__ == "__main__":
    # Enable proxy headers here as well when running directly
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, proxy_headers=True)