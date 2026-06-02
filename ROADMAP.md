# ip-check ROADMAP

> 本项目真实进度源,记录当前阶段、已完成、进行中、待办、阻塞、最近验证。
> 最后更新:2026-06-01

## 当前阶段

已发布的命令行工具 `ipcheck`(PyPI 包名 `ai-ipcheck`),单模块 CLI,版本 0.2.1,处于功能持续打磨阶段。最近一次改动是调整风险颜色分级:DNS 国内服务商、IP 标记为代理、机房托管由红色降为黄色提醒,综合结论仅 IPv6 泄露/风险分≥70/时区不一致才判高风险。当前重心在完善检测维度和公开文档。

## 已完成(已实现且已验证)

> 说明:已发布到 PyPI 且 README 配有运行截图(`screenshot.png`),核心命令可运行可视为已验证;但仓库内未见自动化测试或运行日志沉淀,以下条目以「已发布 + 截图证据」为依据。

- 单模块 CLI 工具落地:`src/ipcheck/cli.py` 集中全部逻辑,`pyproject.toml` 注册 `ipcheck` 命令,`python -m ipcheck` 入口可用
- 已发布到 PyPI:包名 `ai-ipcheck`(`ipcheck` 被占),CLI 命令名 `ipcheck`,版本号到 0.2.1
- 公网信息检测:经 ip-api.com 获取出口 IP、国家/省份/城市、ISP、组织、代理/托管标记、公网时区
- 本机网络检测:局域网 IPv4、IPv6 可用性、DNS 服务器(Windows/Unix/macOS 分别处理)及 DNS 服务商标注
- 代理检测:环境变量代理(HTTP_PROXY/HTTPS_PROXY/ALL_PROXY)、macOS 系统代理(scutil)、TUN/VPN 启发式判断
- IP 风险检测:仅当 proxy/hosting 命中时调用 proxycheck.io 查风险分数 + stopforumspam.org 查滥用记录
- 时区一致性检测:CLI 时区($TZ/系统)与公网 IP 的 IANA 时区比对,生成分项结论与综合结论
- `ipcheck --version` 命令
- 跨平台支持(macOS / Linux / Windows)与中英双语 README
- 风险颜色分级调整:DNS 国内服务商、IP 标记为代理、机房托管降为黄色提醒(不再触发综合高风险);风险分查询保持 <30 绿/<70 黄/≥70 红

## 进行中

- 待确认 — 未发现明确「写完代码但未验证」的半成品;最近 commit `5e687b5 Add system proxy and TUN detection` 已是完整功能提交

## 待办

- 完善 MCP 使用体验与公开文档(来自 projects.json 的 nextStep;注意:MCP server 已于 commit 16bf65f 移除并重构为纯 CLI,此 nextStep 与当前代码状态不一致,需主人确认方向是否仍要 MCP)
- 测试现状待澄清:CLAUDE.md 写「无测试」,但仓库存在 `tests/` 目录(mtime 2026-05-22),README 给出 `PYTHONPATH=src python -m unittest discover -s tests`;需确认测试是否真实存在并能跑通
- 非 macOS 平台的系统代理检测(当前 `get_system_proxy()` 仅 macOS 实现,其他平台不判断)

## 阻塞

- 无

## 最近验证

- 2026-06-01 — 版本号升至 0.2.1 并打包发布到 PyPI(https://pypi.org/project/ai-ipcheck/0.2.1/);`twine check` 通过,whl + sdist 上传成功
- 2026-06-01 — 风险颜色分级调整后运行 `PYTHONPATH=src python -m ipcheck` 验证通过:IP 标记为代理/机房托管显示黄色 `是 !`,风险分 66/100 显示黄色中风险,综合结论因无红线项判绿色低风险;DNS 国内服务商黄色因当前环境为 Cloudflare/Google 未触发实测,仅代码逻辑核对
- 待确认 — 仓库内无测试运行日志或验证记录文件;此前代码改动为 git 提交 `5e687b5 Add system proxy and TUN detection`(README/CLAUDE.md mtime 2026-05-22),README 附有运行截图 `screenshot.png` 可作为命令可运行的间接证据,但无对应的逐项验证记录
