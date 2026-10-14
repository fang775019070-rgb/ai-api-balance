# AI API 余额看板 — AI API Balance

[中文说明](README.md) · [Downloads](https://github.com/fang775019070-rgb/ai-api-balance/releases)

A SwiftBar plugin that displays DeepSeek, OpenRouter and Kimi China API balances in the macOS menu bar. It refreshes every five minutes and when the menu opens. It is based on the author's original personal API billing/balance utility and uses only Python's standard library.

| Provider | Reported measure | Currency |
| --- | --- | --- |
| DeepSeek | Available, paid and granted account balance | CNY or USD as returned; CNY preferred |
| OpenRouter Management Key | Purchased account credits minus total usage | USD |
| OpenRouter regular API key | That key's remaining limit and usage; a configured limit is required | USD |
| Kimi China | Available, cash and voucher account balance | CNY |

Account balances and key spending limits are different measures and are labeled in the menu. This plugin reads provider balance data; it does not calculate per-request invoices or currency conversions.

On failure, cached amounts have a `~` prefix and the menu shows the last update and the error. Without a cached result it reports a failure rather than displaying a fabricated zero.

## Setup

1. Install [SwiftBar from its official releases](https://github.com/swiftbar/SwiftBar/releases). Python 3.9+ must be available to SwiftBar as `python3` on PATH. It can be installed from [python.org](https://www.python.org/downloads/macos/).
2. Download and extract the release ZIP. Keep the entire **AIAPIBalance** folder together.
3. Choose its **Plugin** subfolder as SwiftBar's Plugin Folder. Do not move only the Python file: it locates the setup script relative to its resolved path. If you have existing plugins, create a symbolic link to the Python file in your existing plugin directory and keep the original package together.
4. Click **设置或更新 API Key（选择平台）** (Set or update API key), or double click `setup-api-key.command`. Choose DeepSeek (1), OpenRouter (2), or Kimi China (3). Enter the key at the hidden system password prompt. Control-C cancels.
5. Click **立即刷新全部** (Refresh all). The launcher **启动余额看板.command** can request SwiftBar startup and a plugin refresh. Configure login startup in SwiftBar itself if desired.

The menu UI is mainly Chinese: 可用余额 = available balance; 充值余额 / 现金余额 = paid / cash balance; 赠送余额 / 代金券 = grants / vouchers; 已使用 = used; 最后更新 = last update; 统计口径 = measure; 显示上次结果 = cached result.

Kimi is configured for the China endpoint `api.moonshot.cn` and CNY. International and China keys are independent; an international key will not work with this configuration.

## Credentials and privacy

Keys are stored in the current user's macOS Keychain under `DeepSeek Balance Widget`, `OpenRouter Balance Widget` and `Kimi Balance Widget`, preserving compatibility with the original utility. The setup uses the system's hidden prompt, keeps keys out of command arguments and source/configuration files, and does not delete an existing item before updating it.

Only the corresponding provider's balance/key information endpoints receive the credential. The plugin does not call model generation endpoints, send data to the project author, or collect telemetry. Redirects are rejected so the Authorization header is not forwarded to another destination. A Management Key has broader OpenRouter permissions; a regular key with a spending limit is sufficient if you only need that key's remaining budget.

Balance caches contain amounts and timestamps, not keys. They are saved to SwiftBar's per-plugin cache, or `~/Library/Caches/AIAPIBalance` outside SwiftBar, with owner-only file permissions. Removing the plugin does not remove Keychain entries; remove them manually through Keychain Access when desired.

## Test and package

```sh
zsh test.sh
zsh package.sh
```

Tests use synthetic balances and mocked responses. They do not access real Keychain entries or provider accounts. They cover currency handling, missing/non-finite values, the OpenRouter permission fallback, caches, failures and sensitive exception text. Passing these checks does not imply live verification for every provider and key.

The release ZIP contains the runnable plugin, setup/launcher scripts, bilingual guides and the MIT license. It contains no personal startup configuration, cached balances or credentials.

References: [DeepSeek balances](https://api-docs.deepseek.com/api/get-user-balance/), [OpenRouter account credits](https://openrouter.ai/docs/api/api-reference/credits/get-remaining-credits), [OpenRouter current key](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key), [Kimi China balances](https://platform.kimi.com/docs/api/balance), [SwiftBar documentation](https://github.com/swiftbar/SwiftBar).

MIT License. See [LICENSE](LICENSE).
