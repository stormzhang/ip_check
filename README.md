# ip_check

A lightweight diagnostic tool for AI developers to verify network environment compatibility and IP reputation for LLM API access.

![screenshot](./claude-check.png)

[English](#english) | [中文](#中文)

---

## English

### Why

To ensure AI tools like Claude Code, OpenAI API, and Cursor run smoothly and reliably, a properly configured network environment is essential. Common issues that may affect performance:

- **IPv6 leaking real location** — Most proxies only handle IPv4; IPv6 can expose your actual geographic location
- **DNS leakage** — Local DNS servers can reveal your true location to AI services
- **High-risk IP** — Datacenter IPs or abused IPs may affect connection quality
- **Timezone mismatch** — Inconsistency between local timezone and IP geolocation

`ip_check` detects all these issues in one run, ensuring your AI tools run smoothly and stably.

### Features

| Check Item | Description |
|------------|-------------|
| LAN IP / IPv6 | Detect local IP, verify if IPv6 is disabled |
| DNS Servers | Identify DNS origin (domestic/foreign), label known DNS providers |
| Public IP Info | Exit IP, country, region, ISP, organization |
| Proxy Detection | Env proxy settings, whether IP is flagged as proxy |
| IP Type | Residential vs. datacenter IP identification |
| IP Risk Score | Risk scoring via proxycheck.io |
| Abuse Records | IP abuse lookup via StopForumSpam |
| Timezone Consistency | Compare local CLI timezone with public IP geolocation timezone |

### Quick Start

```bash
python ip_check.py
```

Dependencies (`requests`, etc.) will be auto-detected and installed on first run.

#### Requirements

- Python 3.7+
- macOS / Linux / Windows

### Understanding the Results

**LAN & DNS** — Disable IPv6 if possible. Most proxies don't handle IPv6 traffic, which may expose two IPs from different regions simultaneously. If a domestic DNS is detected, adjust DNS settings in your proxy software.

**Public IP Info** — Shows your exit IP after proxy, including country/region, ISP, and timezone. These directly affect how AI services evaluate your request origin.

**IP Risk Assessment** — Identifies whether your IP is residential or datacenter. Datacenter IPs aren't necessarily problematic, but the tool will query risk scores and abuse records. Switch nodes if your risk score is high.

**Timezone Consistency** — Compares your local `$TZ` environment variable (or system timezone) with the public IP's timezone. Keeping them consistent ensures a better service experience. Set `TZ` in your shell config to match your IP's IANA timezone (e.g., `America/Los_Angeles`).

### MCP Server

ip_check is also available as an MCP server, allowing Claude Code and Claude Desktop to call diagnostic tools directly.

#### Install

```bash
pip install ip-check-mcp
```

#### Add to Claude Code

```bash
claude mcp add --transport stdio ip-check -- ip-check-mcp
```

#### Add to Claude Desktop

Add the following to your Claude Desktop config file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "ip-check": {
      "command": "ip-check-mcp"
    }
  }
}
```

#### Available Tools

| Tool | Description |
|------|-------------|
| `check_all` | Full diagnostic — IP, DNS, proxy, risk, timezone |
| `check_ip_risk` | Check risk score for a specific IP address |
| `check_dns` | Check DNS server configuration |

#### Usage

Once configured, just ask Claude in natural language:

- "Check if my network environment is good for AI tools"
- "Is my current IP risky?"
- "Check my DNS configuration"

Claude will automatically call the corresponding tool and return a structured diagnostic report, for example:

```
> Check my network environment

Network:   LAN IP 192.168.1.100 | IPv6 disabled ✓
DNS:       1.1.1.1 Cloudflare (US) ✓
Public IP: 203.0.113.50 | United States / California
ISP:       Residential IP | Risk 12/100 (low) ✓
Timezone:  America/Los_Angeles — consistent ✓

Your network environment looks good for AI tools.
```

---

## 中文

### 为什么需要这个工具

想让 Claude Code、OpenAI API、Cursor 等 AI 工具流畅稳定运行，网络环境配置至关重要。以下问题可能影响使用体验：

- **IPv6 泄露真实地址** — 代理通常只处理 IPv4，IPv6 会暴露你的实际位置
- **DNS 泄露** — 使用国内 DNS 会暴露真实地理位置
- **IP 风险过高** — 机房 IP 或被滥用的 IP 可能影响连接质量
- **时区不一致** — 本地时区配置与 IP 所在地不匹配

`ip_check` 一键检测这些问题，确保你的 AI 工具流畅稳定运行。

### 功能

| 检测项 | 说明 |
|--------|------|
| 局域网 IP / IPv6 | 检测本机 IP，确认 IPv6 是否已禁用 |
| DNS 服务器 | 识别 DNS 来源（国内/国外），标注已知 DNS 服务商 |
| 公网 IP 信息 | 出口 IP、国家、地区、ISP、运营商 |
| 代理检测 | 环境变量代理配置、IP 是否被标记为代理 |
| IP 类型 | 住宅 IP / 机房 IP 识别 |
| IP 风险评分 | 通过 proxycheck.io 查询风险分数 |
| 滥用记录 | 通过 StopForumSpam 查询 IP 是否被举报 |
| 时区一致性 | 对比本地 CLI 时区与公网 IP 所在时区是否匹配 |

### 快速开始

```bash
python ip_check.py
```

首次运行会自动检测并提示安装缺少的依赖（`requests` 等）。

#### 环境要求

- Python 3.7+
- 支持 macOS / Linux / Windows

### 结果说明

**局域网 & DNS** — IPv6 建议禁用，大部分代理不处理 IPv6 流量，开启后可能同时暴露两个不同地区的 IP 地址。如果检测到国内 DNS，需要在代理软件中调整 DNS 设置。

**公网 IP 信息** — 显示经过代理后的出口 IP、所在国家/地区、ISP 和时区。这些信息直接影响 AI 服务对你请求来源的判断。

**IP 风险评估** — 检测 IP 是住宅还是机房类型。机房 IP 不一定有问题，但会进一步查询风险评分和滥用记录。如果风险评分偏高，建议更换节点。

**时区一致性** — 对比本地 `$TZ` 环境变量（或系统时区）与公网 IP 所在时区。保持一致可以获得更好的服务体验。建议在 shell 配置中设置 `TZ` 为与 IP 所在地匹配的 IANA 时区（如 `America/Los_Angeles`）。

### MCP Server

ip_check 同时提供 MCP server，可以让 Claude Code 和 Claude Desktop 直接调用诊断工具。

#### 安装

```bash
pip install ip-check-mcp
```

#### 添加到 Claude Code

```bash
claude mcp add --transport stdio ip-check -- ip-check-mcp
```

#### 添加到 Claude Desktop

在 Claude Desktop 配置文件中添加（macOS 路径：`~/Library/Application Support/Claude/claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "ip-check": {
      "command": "ip-check-mcp"
    }
  }
}
```

#### 可用工具

| 工具 | 说明 |
|------|------|
| `check_all` | 全量检测 — IP、DNS、代理、风险、时区 |
| `check_ip_risk` | 查询指定 IP 的风险评分 |
| `check_dns` | 检测 DNS 服务器配置 |

#### 使用方式

配置完成后，直接用自然语言向 Claude 提问即可：

- "帮我检查下网络环境适不适合跑 AI 工具"
- "我现在的 IP 有风险吗"
- "检查下我的 DNS 配置"

Claude 会自动调用对应工具，返回结构化的诊断报告，例如：

```
> 帮我检查下网络环境

网络：    局域网 IP 192.168.1.100 | IPv6 已禁用 ✓
DNS：     1.1.1.1 Cloudflare (US) ✓
公网 IP： 203.0.113.50 | United States / California
ISP：     住宅 IP | 风险 12/100（低风险）✓
时区：    America/Los_Angeles — 一致 ✓

你的网络环境适合运行 AI 工具。
```

---

## AI-Native Development

> This MCP integration was built using Claude Code. From protocol definition to server implementation, the entire workflow was AI-augmented, demonstrating the power of the Model Context Protocol.

## License

[MIT](LICENSE) © 2026 stormzhang
