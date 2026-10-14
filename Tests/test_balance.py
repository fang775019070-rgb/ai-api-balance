import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
import urllib.error
from unittest.mock import patch


plugin_path = Path(__file__).resolve().parents[1] / "Plugin" / "ai-api-balance.5m.py"
spec = importlib.util.spec_from_file_location("balance_plugin", plugin_path)
balance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(balance)


class BalanceTests(unittest.TestCase):
    def test_deepseek_prefers_cny_without_mixing_currencies(self):
        value = balance.parse_deepseek({"is_available": True, "balance_infos": [
            {"currency": "USD", "total_balance": "8.50"},
            {"currency": "CNY", "total_balance": "19.80", "topped_up_balance": "15.30", "granted_balance": "4.50"},
        ]})
        self.assertEqual((value["currency"], value["total"], value["bonus"]), ("CNY", "19.80", "4.50"))

    def test_deepseek_can_report_usd(self):
        value = balance.parse_deepseek({"balance_infos": [{"currency": "USD", "total_balance": "8.50"}]})
        self.assertEqual((value["currency"], balance.symbol(value["currency"])), ("USD", "$"))

    def test_missing_values_are_not_fabricated_zero_balances(self):
        for parser, payload in [
            (balance.parse_deepseek, {"balance_infos": [{"currency": "CNY"}]}),
            (balance.parse_openrouter, {"data": {}}),
            (balance.parse_kimi, {"status": True, "data": {}}),
        ]:
            with self.subTest(parser=parser.__name__), self.assertRaises(balance.BalanceDataError):
                parser(payload)

    def test_nonfinite_and_invalid_amounts_are_rejected(self):
        for value in [None, "NaN", "Infinity", "-Infinity", "not-a-number", {}]:
            with self.subTest(value=value), self.assertRaises(balance.BalanceDataError):
                balance.decimal_value(value)

    def test_openrouter_subtraction_uses_decimal_precision(self):
        result = balance.parse_openrouter({"data": {"total_credits": "0.30", "total_usage": "0.10"}})
        self.assertEqual(result["total"], "0.20")
        self.assertEqual(result["mode"], "账户余额")

    def test_openrouter_exhausted_account(self):
        result = balance.parse_openrouter({"data": {"total_credits": "2", "total_usage": "3"}})
        self.assertEqual(result["total"], "0")
        self.assertFalse(result["available"])

    def test_unlimited_regular_key_has_no_account_balance(self):
        with self.assertRaisesRegex(balance.BalanceDataError, "Management Key"):
            balance.parse_openrouter_key({"data": {"limit": None, "limit_remaining": None}})

    def test_regular_key_measure_is_labeled_separately(self):
        result = balance.parse_openrouter_key({"data": {"limit": 50, "limit_remaining": 17.5, "usage": 32.5}})
        self.assertEqual((result["total"], result["mode"]), ("17.5", "API Key 剩余额度"))

    def test_openrouter_403_falls_back_to_key_endpoint(self):
        error = urllib.error.HTTPError(balance.PROVIDERS["openrouter"]["url"], 403, "Forbidden", {}, None)
        with patch.object(balance, "request_json", side_effect=[error, {"data": {"limit": 10, "limit_remaining": 6, "usage": 4}}]) as request, \
             patch.object(balance, "write_cache"):
            result = balance.fetch("openrouter", "test-credential")
        self.assertEqual(result["mode"], "API Key 剩余额度")
        self.assertEqual(request.call_args_list[1].args[0], "https://openrouter.ai/api/v1/key")

    def test_401_does_not_trigger_extra_authenticated_request(self):
        error = urllib.error.HTTPError(balance.PROVIDERS["openrouter"]["url"], 401, "Unauthorized", {}, None)
        with patch.object(balance, "request_json", side_effect=error) as request:
            with self.assertRaises(urllib.error.HTTPError):
                balance.fetch("openrouter", "test-credential")
        self.assertEqual(request.call_count, 1)

    def test_kimi_cash_can_be_negative_while_voucher_remains(self):
        result = balance.parse_kimi({"code": 0, "status": True, "data": {
            "available_balance": "4.20", "cash_balance": "-1.10", "voucher_balance": "4.20",
        }})
        self.assertEqual((result["total"], result["paid"], result["currency"]), ("4.20", "-1.10", "CNY"))

    def test_failed_kimi_response_does_not_use_embedded_data(self):
        with self.assertRaises(balance.BalanceDataError):
            balance.parse_kimi({"status": False, "data": {"available_balance": "99"}})

    def test_corrupt_or_incomplete_cache_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"SWIFTBAR_PLUGIN_CACHE_PATH": directory}):
            cache = Path(directory) / "deepseek.json"
            for value in ["{broken", "[]", '{"total":"NaN","currency":"CNY"}', '{"currency":"CNY"}']:
                cache.write_text(value)
                self.assertIsNone(balance.read_cache("deepseek"))

    def test_cache_is_private_and_contains_no_credentials(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"SWIFTBAR_PLUGIN_CACHE_PATH": directory}):
            balance.write_cache("deepseek", {"total": "3.20", "currency": "CNY"})
            path = Path(directory) / "deepseek.json"
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(json.loads(path.read_text()), {"total": "3.20", "currency": "CNY"})
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_cache_failure_does_not_hide_fresh_balance(self):
        with patch.object(balance, "request_json", return_value={"data": {"total_credits": 10, "total_usage": 3}}), \
             patch.object(balance, "write_cache", side_effect=OSError("read-only")):
            self.assertEqual(balance.fetch("openrouter", "test-credential")["total"], "7")

    def test_unknown_exception_does_not_expose_sensitive_text(self):
        self.assertNotIn("private-example", balance.error_text(RuntimeError("private-example")))

    def test_failed_refresh_is_marked_stale_and_does_not_print_key(self):
        cache = {"total": "5.30", "currency": "CNY", "updated_at": "2026-01-01T10:00:00+00:00"}
        output = io.StringIO()
        with patch.object(balance, "get_key", side_effect=["private-example", "", ""]), \
             patch.object(balance, "fetch", side_effect=urllib.error.URLError("offline")), \
             patch.object(balance, "read_cache", return_value=cache), contextlib.redirect_stdout(output):
            self.assertEqual(balance.main(), 0)
        rendered = output.getvalue()
        self.assertIn("DS ~¥5.30", rendered)
        self.assertIn("显示上次结果", rendered)
        self.assertNotIn("private-example", rendered)

    def test_failure_without_cache_is_not_a_setup_prompt(self):
        output = io.StringIO()
        with patch.object(balance, "get_key", side_effect=["test-credential", "", ""]), \
             patch.object(balance, "fetch", side_effect=RuntimeError("error")), \
             patch.object(balance, "read_cache", return_value=None), contextlib.redirect_stdout(output):
            balance.main()
        self.assertIn("AI 余额：查询失败", output.getvalue().splitlines()[0])

    def test_redirect_does_not_forward_authorization(self):
        self.assertIsNone(balance.NoRedirects().redirect_request(None, None, 302, "Found", {}, "https://example.invalid/"))

    def test_menu_setup_path_with_spaces_is_one_argument(self):
        import shlex
        output = io.StringIO()
        path = "/example/My Tools/setup-api-key.command"
        with patch.object(balance, "get_key", return_value=""), patch.object(balance, "setup_command", return_value=path), \
             contextlib.redirect_stdout(output):
            balance.main()
        setup_line = next(line for line in output.getvalue().splitlines() if "bash=/usr/bin/open" in line)
        self.assertIn("param1=" + path, shlex.split(setup_line.split(" | ", 1)[1]))


if __name__ == "__main__":
    unittest.main()
