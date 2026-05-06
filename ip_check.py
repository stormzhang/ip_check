#!/usr/bin/env python3
"""
IP & 环境检测工具
检测本机 IP、IPv6、DNS、公网信息、代理状态、时区
支持 macOS / Linux / Windows
"""

import socket
import ipaddress
import os
import sys
import subprocess
import datetime
import re
import platform
import json
import urllib.request
import urllib.parse

# ── 编码修正（Windows cmd 默认非 UTF-8）────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

IS_WIN = platform.system() == 'Windows'


# ── 可选依赖自动安装（核心 HTTP 已用标准库，无需第三方）────
def _pip_install(packages):
    """多策略安装：普通 → --user → --break-system-packages；适配 PEP 668 环境。"""
    base = [sys.executable, '-m', 'pip', 'install', '--quiet', '--disable-pip-version-check']
    attempts = [
        base + packages,
        base + ['--user'] + packages,
        base + ['--user', '--break-system-packages'] + packages,
    ]
    for cmd in attempts:
        try:
            subprocess.check_call(cmd)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    # pip 可能未安装，用 ensurepip 引导后再试一轮
    try:
        subprocess.check_call([sys.executable, '-m', 'ensurepip', '--upgrade'])
        for cmd in attempts:
            try:
                subprocess.check_call(cmd)
                return True
            except subprocess.CalledProcessError:
                continue
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return False


def _ensure_deps():
    """仅处理可选增强包：Windows 彩色输出与时区数据；失败则静默降级。"""
    needed = []

    if IS_WIN:
        try:
            import colorama  # noqa: F401
        except ImportError:
            needed.append('colorama')
        try:
            import tzdata  # noqa: F401
        except ImportError:
            needed.append('tzdata')

    if sys.version_info < (3, 9):
        try:
            from backports import zoneinfo  # noqa: F401
        except ImportError:
            needed.append('backports.zoneinfo')

    if not needed:
        return

    print(f"检测到可选依赖缺失: {', '.join(needed)}，尝试自动安装...")
    if not _pip_install(needed):
        print(f"  自动安装失败，将以降级模式继续运行。如需完整功能可手动安装: pip install {' '.join(needed)}\n")

_ensure_deps()


# ── 标准库 HTTP 封装（替代 requests，零第三方依赖）─────────
def _http_get_json(url, params=None, timeout=6):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'claude-check/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8', errors='replace'))


# ── 已知 DNS ──────────────────────────────────────────────
KNOWN_DNS = {
    '1.1.1.1':         'Cloudflare (US)',
    '1.0.0.1':         'Cloudflare (US)',
    '1.1.1.2':         'Cloudflare for Families (US)',
    '1.0.0.2':         'Cloudflare for Families (US)',
    '1.1.1.3':         'Cloudflare for Families (US)',
    '1.0.0.3':         'Cloudflare for Families (US)',
    '8.8.8.8':         'Google Public DNS (US)',
    '8.8.4.4':         'Google Public DNS (US)',
    '9.9.9.9':         'Quad9 (US)',
    '149.112.112.112': 'Quad9 (US)',
    '208.67.222.222':  'OpenDNS/Cisco (US)',
    '208.67.220.220':  'OpenDNS/Cisco (US)',
    '223.5.5.5':       'AliDNS 阿里 (CN)',
    '223.6.6.6':       'AliDNS 阿里 (CN)',
    '119.29.29.29':    'DNSPod 腾讯 (CN)',
    '182.254.116.116': 'DNSPod 腾讯 (CN)',
    '114.114.114.114': '114DNS (CN)',
    '114.114.115.115': '114DNS (CN)',
    '180.76.76.76':    'BaiduDNS 百度 (CN)',
    '1.2.4.8':         'CNNIC (CN)',
    '210.2.4.8':       'CNNIC (CN)',
    '94.140.14.14':    'AdGuard (CY)',
    '94.140.15.15':    'AdGuard (CY)',
    '185.228.168.9':   'CleanBrowsing (US)',
    '185.228.169.9':   'CleanBrowsing (US)',
    '76.76.2.0':       'Alternate DNS (US)',
    '76.76.10.0':      'Alternate DNS (US)',
}

def dns_label(ip):
    if ip in KNOWN_DNS:
        return f"{ip}  {KNOWN_DNS[ip]}"
    try:
        if ipaddress.ip_address(ip).is_private:
            return f"{ip}  局域网路由器"
    except Exception:
        pass
    return ip




# ── zoneinfo（Windows 需额外安装 tzdata）─────────────────
try:
    from zoneinfo import ZoneInfo as _ZI
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo as _ZI  # type: ignore
    except ImportError:
        _ZI = None

def make_zone(name):
    """构造 ZoneInfo；失败（含 Windows 缺少 tzdata）返回 None。"""
    if not _ZI or not name:
        return None
    try:
        return _ZI(name)
    except Exception:
        return None


# ── 颜色 ─────────────────────────────────────────────────
def _init_color():
    if IS_WIN:
        # 优先 colorama
        try:
            import colorama
            colorama.init()
            return True
        except ImportError:
            pass
        # 次选：直接开启 Win10+ 虚拟终端处理
        try:
            import ctypes
            h = ctypes.windll.kernel32.GetStdHandle(-11)
            m = ctypes.c_ulong()
            ctypes.windll.kernel32.GetConsoleMode(h, ctypes.byref(m))
            ctypes.windll.kernel32.SetConsoleMode(h, m.value | 0x0004)
            return True
        except Exception:
            return False
    return True

_COLOR = _init_color()

class C:
    RESET  = "\033[0m"  if _COLOR else ""
    BOLD   = "\033[1m"  if _COLOR else ""
    RED    = "\033[91m" if _COLOR else ""
    GREEN  = "\033[92m" if _COLOR else ""
    YELLOW = "\033[93m" if _COLOR else ""
    CYAN   = "\033[96m" if _COLOR else ""
    GRAY   = "\033[90m" if _COLOR else ""

ANSI_RE = re.compile(r'\033\[[0-9;]*m')

def _cw(c):
    cp = ord(c)
    if (0x2E80 <= cp <= 0x303E or 0x3040 <= cp <= 0x33FF or
        0x3400 <= cp <= 0x4DBF or 0x4E00 <= cp <= 0x9FFF or
        0xAC00 <= cp <= 0xD7AF or 0xF900 <= cp <= 0xFAFF or
        0xFE30 <= cp <= 0xFE6F or 0xFF00 <= cp <= 0xFF60 or
        0x20000 <= cp <= 0x2FFFD):
        return 2
    return 1

def dlen(s):
    return sum(_cw(c) for c in ANSI_RE.sub('', s))

def ok(v):   return f"{C.GREEN}{v}{C.RESET}"
def warn(v): return f"{C.YELLOW}{v}{C.RESET}"
def bad(v):  return f"{C.RED}{v}{C.RESET}"


# ── 表格渲染 ──────────────────────────────────────────────
L1, L2 = 18, 46

def tbl_top(): print(f"  \u2554{'═'*(L1+2)}\u2564{'═'*(L2+2)}\u2557")
def tbl_sep(): print(f"  \u2560{'═'*(L1+2)}\u256a{'═'*(L2+2)}\u2563")
def tbl_bot(): print(f"  \u255a{'═'*(L1+2)}\u2567{'═'*(L2+2)}\u255d")

def tbl_row(label, value):
    value = str(value)
    lpad = ' ' * max(0, L1 - dlen(label))
    vpad = ' ' * max(0, L2 - dlen(value))
    lstr = f"{label}{lpad}" if label else ' ' * L1
    print(f"  \u2551 {lstr} \u2502 {value}{vpad} \u2551")


# ── 数据采集 ─────────────────────────────────────────────
def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return warn("获取失败")

def get_ipv6():
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.connect(("2001:4860:4860::8888", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and ip not in ('', '::'):
            return ip
    except Exception:
        pass
    return warn("已禁用")

def get_dns_servers():
    servers = []
    if IS_WIN:
        # PowerShell：读取所有网卡的 IPv4 DNS（去重）
        try:
            r = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 'Get-DnsClientServerAddress -AddressFamily IPv4 | '
                 'Select-Object -ExpandProperty ServerAddresses'],
                capture_output=True, text=True, timeout=5, encoding='utf-8',
            )
            seen = set()
            for line in r.stdout.splitlines():
                ip = line.strip()
                if not ip:
                    continue
                try:
                    ipaddress.ip_address(ip)
                    if ip not in seen:
                        seen.add(ip)
                        servers.append(ip)
                except ValueError:
                    pass
        except Exception:
            pass
    else:
        # Linux：/etc/resolv.conf
        try:
            seen = set()
            with open('/etc/resolv.conf') as f:
                for line in f:
                    if line.strip().startswith('nameserver'):
                        ip = line.split()[1]
                        if ip not in seen:
                            seen.add(ip)
                            servers.append(ip)
        except Exception:
            pass
        # macOS：scutil --dns
        if not servers:
            try:
                r = subprocess.run(
                    ['scutil', '--dns'], capture_output=True, text=True, timeout=3,
                )
                seen = set()
                for line in r.stdout.splitlines():
                    line = line.strip()
                    if line.startswith('nameserver['):
                        ip = line.split(':', 1)[1].strip()
                        if ip not in seen:
                            seen.add(ip)
                            servers.append(ip)
            except Exception:
                pass
    return servers

def get_public_info():
    try:
        return _http_get_json(
            "http://ip-api.com/json/",
            params={"fields": "status,message,country,regionName,city,isp,org,proxy,hosting,query,timezone"},
        )
    except Exception as e:
        return {"status": "fail", "message": str(e)}

def get_ip_risk(ip):
    try:
        data = _http_get_json(
            f"https://proxycheck.io/v2/{ip}",
            params={"risk": 1, "vpn": 1, "asn": 1},
        ).get(ip, {})
        risk  = data.get("risk")
        itype = data.get("type", "")
        proxy = data.get("proxy", "")
        parts = []
        if risk is not None:
            score = int(risk)
            if score < 30:
                color, level = C.GREEN, "低风险"
            elif score < 70:
                color, level = C.YELLOW, "中风险"
            else:
                color, level = C.RED, "高风险"
            parts.append(f"{color}{score}/100 {level}{C.RESET}")
        if itype:
            parts.append(f"类型 {itype}")
        if proxy == "yes":
            parts.append(bad("已标记为代理"))
        return "  ".join(parts) if parts else warn("暂无数据")
    except Exception as e:
        return warn(f"查询失败（{e}）")

def get_stopforumspam(ip):
    try:
        data = _http_get_json(
            "https://api.stopforumspam.org/api",
            params={"json": 1, "ip": ip},
        ).get("ip", {})
        if not data.get("appears"):
            return [ok("未收录  低风险 ✓")]
        confidence = float(data.get("confidence", 0))
        frequency  = int(data.get("frequency", 0))
        last_seen  = (data.get("lastseen") or "")[:10]
        if confidence < 30:
            color, level = C.GREEN, "低风险"
        elif confidence < 70:
            color, level = C.YELLOW, "中风险"
        else:
            color, level = C.RED, "高风险"
        lines = [f"{color}{confidence:.1f}/100 {level}{C.RESET}  举报 {frequency} 次"]
        if last_seen:
            lines.append(f"最近举报 {last_seen}")
        return lines
    except Exception as e:
        return [warn(f"查询失败（{e}）")]

def get_proxy_envs():
    seen = {}
    for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                "http_proxy", "https_proxy", "all_proxy"]:
        val = os.environ.get(key)
        if val and val not in seen.values():
            seen[key.upper()] = val
    return seen

def _utc_str(offset):
    """timedelta → 'UTC±HH:MM' 字符串"""
    total = int(offset.total_seconds())
    h, r  = divmod(abs(total), 3600)
    sign  = "+" if total >= 0 else "-"
    return f"UTC{sign}{h:02d}:{r//60:02d}"

def get_cli_tz_name():
    """
    返回 (tz_name, is_iana) 元组。
    - 优先取 $TZ 环境变量（跨平台，IANA 格式）
    - Windows 下退而取 PowerShell 本地时区 ID（非 IANA，用于展示）
    - 最后用 Python tzname() 兜底
    """
    tz_env = os.environ.get('TZ', '')
    if tz_env:
        return tz_env, True

    if IS_WIN:
        try:
            r = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 '[System.TimeZoneInfo]::Local.Id'],
                capture_output=True, text=True, timeout=3, encoding='utf-8',
            )
            win_id = r.stdout.strip()
            if win_id:
                return win_id, False   # Windows ID，非 IANA
        except Exception:
            pass

    name = datetime.datetime.now().astimezone().tzname() or "Unknown"
    return name, False


# ── 主程序 ────────────────────────────────────────────────
def main():
    pub = get_public_info()

    print(f"\n  {C.BOLD}IP & 环境检测工具{C.RESET}  "
          f"{C.GRAY}({platform.system()} / Python {platform.python_version()}){C.RESET}\n")
    tbl_top()

    # 本机网络
    tbl_row("局域网 IP", get_lan_ip())
    tbl_row("IPv6 地址", get_ipv6())
    dns = get_dns_servers()
    if dns:
        tbl_row("DNS 服务器", dns_label(dns[0]))
        for d in dns[1:]:
            tbl_row("", dns_label(d))
    else:
        tbl_row("DNS 服务器", warn("获取失败"))

    tbl_sep()

    # 公网信息
    if pub.get("status") == "success":
        tbl_row("公网 IP",          pub.get("query", "-"))
        tbl_row("国家 / 省份",      f"{pub.get('country', '-')} / {pub.get('regionName', '-')}")
        tbl_row("城市",              pub.get("city", "-"))
        tbl_row("ISP(互联网服务商)", pub.get("isp", "-"))
        tbl_row("组织",              pub.get("org", "-"))
        pub_tz_name = pub.get("timezone", "")
        if pub_tz_name:
            zi = make_zone(pub_tz_name)
            if zi:
                off = datetime.datetime.now(zi).utcoffset()
                tbl_row("所处时区", f"{pub_tz_name}  ({_utc_str(off)})")
            else:
                tbl_row("所处时区", pub_tz_name)
        else:
            tbl_row("所处时区", "-")
    else:
        tbl_row("公网请求", bad(pub.get("message", "未知错误")))

    tbl_sep()

    # 代理检测
    proxy_envs = get_proxy_envs()
    if proxy_envs:
        for k, v in proxy_envs.items():
            tbl_row(k, warn(v))
    else:
        tbl_row("环境变量代理", ok("未设置"))
    if pub.get("status") == "success":
        tbl_row("IP 标记为代理", bad("是 ✗") if pub.get("proxy")   else ok("否 ✓"))
        tbl_row("机房 / 托管",   bad("是 ✗") if pub.get("hosting") else ok("否 ✓"))
        if pub.get("hosting") or pub.get("proxy"):
            pub_ip = pub.get("query", "")
            tbl_row("IP 风险查询",  get_ip_risk(pub_ip))
            spam_lines = get_stopforumspam(pub_ip)
            tbl_row("垃圾滥用记录", spam_lines[0])
            for line in spam_lines[1:]:
                tbl_row("", line)

    tbl_sep()

    # 时区
    cli_dt     = datetime.datetime.now().astimezone()
    cli_offset = cli_dt.utcoffset()
    tz_name, is_iana = get_cli_tz_name()
    tbl_row("CLI 时区", f"{tz_name}  ({_utc_str(cli_offset)})")

    pub_tz_name = pub.get("timezone", "") if pub.get("status") == "success" else ""
    if pub_tz_name:
        pub_zi     = make_zone(pub_tz_name)
        pub_offset = datetime.datetime.now(pub_zi).utcoffset() if pub_zi else None

        if is_iana:
            # $TZ 是 IANA 格式，直接比较名称（最准确）
            match = ok("一致 ✓") if tz_name == pub_tz_name else bad("不一致 ✗")
        elif pub_offset is not None:
            # Windows 无 IANA $TZ，退而比较 UTC 偏移
            if cli_offset == pub_offset:
                match = warn("UTC 偏移一致（建议设置 $TZ=IANA 名称精确比对）")
            else:
                match = bad("不一致 ✗（UTC 偏移不同）")
        else:
            match = warn("无法比对（tzdata 未安装？pip install tzdata）")
        tbl_row("时区一致性", match)

    tbl_bot()

    # Windows 提示
    if IS_WIN and _ZI is None:
        print(f"\n  {C.YELLOW}提示：pip install tzdata  （Windows 时区精确比对所需）{C.RESET}")
    if IS_WIN and not _COLOR:
        print(f"\n  提示：pip install colorama  （启用彩色输出）")
    print()


if __name__ == "__main__":
    main()
