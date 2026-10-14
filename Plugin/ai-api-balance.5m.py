#!/usr/bin/env python3
# <xbar.title>AI API Balance</xbar.title>
# <xbar.version>2.1.0</xbar.version>
# <xbar.author>fang775019070-rgb</xbar.author>
# <xbar.desc>DeepSeek, OpenRouter and Kimi API balances.</xbar.desc>
# <swiftbar.refreshOnOpen>true</swiftbar.refreshOnOpen>

import json
import getpass
import os
import shlex
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek", "short": "DS", "service": "DeepSeek Balance Widget",
        "url": "https://api.deepseek.com/user/balance", "currency": "CNY",
        "topup": "https://platform.deepseek.com/top_up", "dashboard": "https://platform.deepseek.com/usage",
    },
    "openrouter": {
        "name": "OpenRouter", "short": "OR", "service": "OpenRouter Balance Widget",
        "url": "https://openrouter.ai/api/v1/credits", "currency": "USD",
        "topup": "https://openrouter.ai/settings/credits", "dashboard": "https://openrouter.ai/activity",
    },
    "kimi": {
        "name": "Kimi", "short": "Kimi", "service": "Kimi Balance Widget",
        "url": "https://api.moonshot.cn/v1/users/me/balance", "currency": "CNY",
        "topup": "https://platform.kimi.com/console", "dashboard": "https://platform.kimi.com/console/fee-detail",
    },
}


class BalanceDataError(ValueError):
    """A user-safe explanation of an unsupported balance response."""


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward an Authorization header to a redirected destination.
        return None


def decimal_value(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise BalanceDataError("余额数据格式错误") from None
    if not result.is_finite():
        raise BalanceDataError("余额数据格式错误")
    return result


def get_key(service):
    try:
        result = subprocess.run(
            ["/usr/bin/security", "find-generic-password", "-s", service,
             "-a", getpass.getuser(), "-w"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def cache_dir():
    fallback = Path.home() / "Library" / "Caches" / "AIAPIBalance"
    path = Path(os.environ.get("SWIFTBAR_PLUGIN_CACHE_PATH") or fallback)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def read_cache(provider):
    path = cache_dir() / f"{provider}.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("currency") not in {"CNY", "USD"}:
            return None
        decimal_value(value.get("total"))
        for field in ("paid", "bonus", "used"):
            if value.get(field) is not None:
                decimal_value(value[field])
        return value
    except (OSError, ValueError):
        return None


def write_cache(provider, value):
    directory = cache_dir()
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                         prefix=f".{provider}-", delete=False) as file:
            temp_path = Path(file.name)
            json.dump(value, file, ensure_ascii=False)
        # NamedTemporaryFile starts with owner-only permissions.
        os.replace(temp_path, directory / f"{provider}.json")
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def request_json(url, key):
    request = urllib.request.Request(url, headers={"Accept": "application/json", "Authorization": f"Bearer {key}", "User-Agent": "AIBalanceWidget/2.1"})
    opener = urllib.request.build_opener(NoRedirects)
    with opener.open(request, timeout=12) as response:
        return json.load(response)


def parse_deepseek(payload):
    if not isinstance(payload, dict):
        raise BalanceDataError("没有返回余额")
    items = payload.get("balance_infos") or []
    if not isinstance(items, list):
        raise BalanceDataError("没有返回余额")
    items = [x for x in items if isinstance(x, dict) and x.get("currency") in {"CNY", "USD"}]
    item = next((x for x in items if x.get("currency") == "CNY"), items[0] if items else None)
    if not item:
        raise BalanceDataError("没有返回余额")
    return {"total": str(decimal_value(item.get("total_balance"))), "paid": str(decimal_value(item.get("topped_up_balance", "0.00"))), "bonus": str(decimal_value(item.get("granted_balance", "0.00"))), "currency": item["currency"], "available": bool(payload.get("is_available")), "mode": "账户余额"}


def parse_openrouter(payload):
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        raise BalanceDataError("没有返回余额")
    purchased = decimal_value(data.get("total_credits"))
    used = decimal_value(data.get("total_usage"))
    return {"total": str(max(Decimal("0"), purchased - used)), "paid": str(purchased), "bonus": None, "currency": "USD", "available": purchased > used, "mode": "账户余额", "used": str(used)}


def parse_openrouter_key(payload):
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        raise BalanceDataError("没有返回额度")
    remaining = data.get("limit_remaining")
    if remaining is None:
        raise BalanceDataError("普通 Key 未设置额度；账户余额需要 Management Key")
    return {"total": str(decimal_value(remaining)), "paid": str(decimal_value(data.get("limit") or 0)), "bonus": None, "currency": "USD", "available": decimal_value(remaining) > 0, "mode": "API Key 剩余额度", "used": str(decimal_value(data.get("usage", 0)))}


def parse_kimi(payload):
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict) or not payload.get("status", True) or "available_balance" not in data:
        raise BalanceDataError("没有返回余额")
    total = decimal_value(data["available_balance"])
    return {"total": str(total), "paid": str(decimal_value(data.get("cash_balance", 0))), "bonus": str(decimal_value(data.get("voucher_balance", 0))), "currency": "CNY", "available": total > 0, "mode": "账户余额"}


def fetch(provider, key):
    config = PROVIDERS[provider]
    try:
        payload = request_json(config["url"], key)
        result = parse_deepseek(payload) if provider == "deepseek" else parse_openrouter(payload) if provider == "openrouter" else parse_kimi(payload)
    except urllib.error.HTTPError as exc:
        if provider == "openrouter" and exc.code == 403:
            result = parse_openrouter_key(request_json("https://openrouter.ai/api/v1/key", key))
        else:
            raise
    result["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        write_cache(provider, result)
    except OSError:
        # A fresh API result remains useful even if local caching is unavailable.
        pass
    return result


def error_text(exc):
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 401: return "API Key 无效或与平台区域不匹配"
        if exc.code == 403: return "API Key 权限不足"
        if exc.code == 429: return "请求过于频繁"
        return f"接口错误 {exc.code}"
    if isinstance(exc, urllib.error.URLError): return "网络连接失败"
    if isinstance(exc, BalanceDataError): return str(exc)
    return "查询失败，请稍后刷新"


def symbol(currency):
    return "¥" if currency == "CNY" else "$" if currency == "USD" else f"{currency} "


def amount(value):
    try: return f"{Decimal(str(value)):.2f}"
    except Exception: return str(value)


def time_text(value):
    try: return datetime.fromisoformat(value).astimezone().strftime("%H:%M")
    except Exception: return "未知"


def setup_command():
    return str(Path(__file__).resolve().parent.parent / "setup-api-key.command")


def main():
    keys = {pid: get_key(cfg["service"]) for pid, cfg in PROVIDERS.items()}
    results, errors, stale = {}, {}, set()
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(fetch, pid, key): pid for pid, key in keys.items() if key}
        for job in as_completed(jobs):
            pid = jobs[job]
            try: results[pid] = job.result()
            except Exception as exc:
                errors[pid] = error_text(exc)
                cached = read_cache(pid)
                if cached:
                    results[pid] = cached
                    stale.add(pid)

    header = []
    for pid, cfg in PROVIDERS.items():
        if pid in results:
            item = results[pid]
            cached_mark = "~" if pid in stale else ""
            header.append(f"{cfg['short']} {cached_mark}{symbol(item['currency'])}{amount(item['total'])}")
    title = " · ".join(header) if header else "AI 余额：查询失败" if any(keys.values()) else "AI 余额：请设置 Key"
    color = " color=#D97706" if stale or errors else ""
    print(f"{title} | sfimage=creditcard.fill{color}")
    print("---")

    setup = setup_command()
    for index, (pid, cfg) in enumerate(PROVIDERS.items()):
        if index: print("---")
        print(f"{cfg['name']} | size=13")
        if pid in results:
            item = results[pid]; money = symbol(item["currency"])
            print(f"--可用余额：{money}{amount(item['total'])}")
            print(f"--统计口径：{item.get('mode', '账户余额')}")
            if pid == "deepseek":
                print(f"--充值余额：{money}{amount(item.get('paid', 0))}")
                print(f"--赠送余额：{money}{amount(item.get('bonus', 0))}")
            elif pid == "kimi":
                print(f"--现金余额：{money}{amount(item.get('paid', 0))}")
                print(f"--代金券：{money}{amount(item.get('bonus', 0))}")
            elif pid == "openrouter":
                print(f"--已使用：{money}{amount(item.get('used', 0))}")
            print(f"--最后更新：{time_text(item.get('updated_at'))}")
            if pid in stale: print(f"--显示上次结果：{errors.get(pid)} | color=#D97706")
        elif keys[pid]:
            print(f"--查询失败：{errors.get(pid, '未知错误')} | color=#D97706")
        else:
            print("--尚未设置 API Key")
        print(f"--前往充值 | href={cfg['topup']} sfimage=creditcard.fill")
        print(f"--打开用量后台 | href={cfg['dashboard']} sfimage=chart.bar.fill")

    print("---")
    print(f"设置或更新 API Key（选择平台）… | bash=/usr/bin/open param1={shlex.quote(setup)} terminal=false")
    print("立即刷新全部 | refresh=true sfimage=arrow.clockwise")
    return 0


if __name__ == "__main__":
    sys.exit(main())
