# AI API 余额看板（AI API Balance）

[English](README.en.md) · [下载 Download](https://github.com/fang775019070-rgb/ai-api-balance/releases)

在 Mac 菜单栏查看 DeepSeek、OpenRouter 和 Kimi 国内站的 API 可用余额、充值余额及剩余额度。每 5 分钟自动刷新，打开菜单时也会刷新。基于原来的个人 API 计费余额插件整理，使用 Python 标准库和 SwiftBar。

## 显示的费用数据

| 平台 | 显示口径 | 币种 |
| --- | --- | --- |
| DeepSeek | 可用总余额、充值余额、赠送余额 | 平台返回的 CNY 或 USD，优先 CNY |
| OpenRouter Management Key | 账户购买额度减去已用额度，并显示累计使用额 | USD |
| OpenRouter 普通 Key | 该 Key 的剩余额度及使用额，需先为 Key 设置额度限制 | USD |
| Kimi 国内站 | 可用余额、现金余额、代金券 | CNY |

账户余额和单个 Key 的额度是不同统计口径，菜单会明确标示。普通 OpenRouter Key 没有设置额度时，显示说明而不把它当作零余额。本工具查询平台返回的数据，不计算每条请求的账单，也不转换人民币和美元汇率。

查询失败时，有历史结果就显示缓存值：菜单栏金额前带 `~`，菜单内注明上次更新时间和失败原因。没有历史结果时显示查询失败，不伪装成实时余额。

## 安装

1. 从 [SwiftBar 官方发行版](https://github.com/swiftbar/SwiftBar/releases) 安装并打开 SwiftBar；需要 Python 3.9 或更高版本，且 SwiftBar 能在 PATH 中找到 `python3`。Python 可从 [官方站点](https://www.python.org/downloads/macos/) 安装。
2. 下载本项目的 ZIP，解压并保留整个 **AIAPIBalance** 文件夹。
3. 在 SwiftBar 设置中，把该文件夹内的 **Plugin** 选为 Plugin Folder。不要只移动 Python 文件，设置 Key 的脚本需要保持相对位置。已有其他插件的用户可在原插件目录建立指向本 Python 文件的符号链接；插件会解析实际位置后查找设置脚本。
4. 点击菜单里的“设置或更新 API Key（选择平台）”，在终端选择 1、2 或 3，再按系统 `password` 提示输入相应 Key。也可直接双击 `setup-api-key.command`。输入内容不会显示，Control-C 可取消。
5. 在菜单中选择“立即刷新全部”。如未启动，可双击“启动余额看板.command”。是否登录时启动由 SwiftBar 自己的设置控制。

Kimi 使用国内站 `api.moonshot.cn`。国际站的 Key 与国内站不通用，不能通过更换 Key 直接使用这个国内站配置。菜单界面以中文为主，英文指南解释了字段和安装步骤。

## Key 与隐私

API Key 保存在当前用户的 macOS 钥匙串，服务名分别是 `DeepSeek Balance Widget`、`OpenRouter Balance Widget`、`Kimi Balance Widget`。这些名称兼容原个人插件。输入脚本使用系统安全提示，Key 不作为命令行参数传递，不写入插件或配置文件。更新时不先删除已有条目。

运行时仅向对应平台的余额 / Key 信息接口发送 Key；不调用模型生成接口，不上传余额到本项目作者，也没有遥测。HTTP 重定向会被拒绝，避免把授权头发送到重定向地址。OpenRouter Management Key 具有管理权限；只需要查看单个 Key 的额度时，普通限额 Key 即可。

余额和更新时间缓存保存在 SwiftBar 的插件缓存目录；独立运行时使用当前用户的 `~/Library/Caches/AIAPIBalance`。缓存文件只允许所有者读写，不缓存 Key。移除插件不会删除钥匙串中的 Key；需要删除时，请在“钥匙串访问”中按上述服务名查找并自行删除。

## 检查与打包

```sh
zsh test.sh
zsh package.sh
```

测试使用合成余额和模拟响应，覆盖币种、缺失数据、非有限金额、OpenRouter 权限回退、缓存、网络错误以及错误信息中的敏感内容处理。测试不读取真实钥匙串，不调用真实账户接口。自动检查通过不代表每个平台和 Key 都已做真实账户验证。

打包输出 `dist/AIAPIBalance-v2.1.0.zip` 和校验文件；发行包包含可运行插件、设置脚本及双语说明，不包含钥匙串、缓存和个人启动项。安装后仍需使用自己的 Key。

## 接口参考

- [DeepSeek 查询余额](https://api-docs.deepseek.com/zh-cn/api/get-user-balance/)
- [OpenRouter 账户额度](https://openrouter.ai/docs/api/api-reference/credits/get-remaining-credits) 与 [当前 Key 信息](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key)
- [Kimi 国内站查询余额](https://platform.kimi.com/docs/api/balance)
- [SwiftBar 插件格式和安装说明](https://github.com/swiftbar/SwiftBar)

MIT License，见 [LICENSE](LICENSE)。

检索关键词：API 计费、API 费用、余额查询、充值余额、剩余额度、DeepSeek、OpenRouter、Kimi、Moonshot、SwiftBar、macOS、API billing、credits、balance、usage。
