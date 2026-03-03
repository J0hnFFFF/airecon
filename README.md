# AIRecon (智能重构)

**基于大语言模型的前沿 AI 安全代理引擎**，可全自动将松散的开源安全工具编织成为一个拥有 **“规划→侦察→分析→渗透→报告”** 全链路操作能力的高级红队系统。

</div>

---

## 核心架构概览

AIRecon 是一套复合型系统，其包含：**一个认知中枢（LLM Agent）、一套控制流管道（Pipeline Engine），以及一个高度隔离的真实命令执行沙箱（Docker Sandbox）。**

相比只有分析响应能力的 API AI 层，**AIRecon 具备真实系统的可控执行权限**。你可以把它当作为一个真正“坐在屏幕前帮你跑漏扫、找弱点”数字黑客同事。

### 主要功能

- **自动化工作流 (Autonomous Pipeline)**<br>流水线式执行“侦察 (RECON) → 分析 (ANALYSIS) → 利用 (EXPLOIT) → 生成验证报告 (REPORT)”。摆脱循环等待死板迭代的旧思路，基于真实的探查结果做出阶段变更评估。
- **状态持久化与抗遗忘设计**<br>您的进度（如已经采集的子域名、端口分布、指纹技术以及漏洞）都能随时记录进 `~/.airecon/sessions/`。系统设计有通过每 5 步自动执行二次摘要抓取 (`session_to_context`)进入新 Prompt 的措施，避免在长时漏洞挖矿等大型扫描之后触发“由于上下文丢失和幻觉产生的乱杀”。
- **内置原生 Caido 代理操作池集成**<br>与重播或漏洞发现结合，提供基于 Burp Intruder 模块思路的漏洞 Payload `§FUZZ§` 标志符化并发机制。
- **自动认证抓取与浏览器渲染支持**<br>支持使用 Playwright 后台进行：常规节点抓取模拟操作、支持 OAuth 解析捕获、并具备免第三方认证库内建执行 TOTP 标准等高阶浏览器联动渗透（无需介入或传导 Session 抓包数据）。
- **复合 Fuzzing 测试引擎 (Fuzzing Engine)**<br>内含变异引擎（MutationEngine）、具有预判性质的启发选代引擎（ExpertHeuristics），并且内置一个自带超过 1000 种针对主流漏洞（如 SQL 注入与 SSRF 等）Payload 及链接链路引擎。
- **自适应技能与零配置自动化 (Skills Knowledge Base)**<br>预建装填超过 56 种常见漏洞挖掘与操作标准化执行动作文件 (Skills)，覆盖范围涉及如 SQLi、XSS、业务逻辑出错、JWT伪造 及 云设施渗透 漏洞排查方法。系统通过内部强大的正则字典映射表，随时投向环境最迫切的安全操作方法之中。
- **多代理并发渗透与专家调动配置 (Multi-Agent Orchestration)**<br>主系统具备任务切片职能：遇到核心漏洞即可调用专研的 `spawn_agent`（指派 XSS 专职探测子模块），用单独的工作区环境隔离侦察。使用 `run_parallel_agents` 并发不同业务目标；或者设定以 DAG 为图谱模型的高级连贯处理控制链。
- **命令行界面 TUI (彩色高刷操作屏幕)**<br>流式输出色彩反馈体系：开启中的端口（蓝）、重大 CVE 系统编号确认及高危发现（橘加粗表示），各种结果情况实时流追踪，一眼便可知晓整体扫描脉络。

---

## 模型与系统配置要求

AIRecon 使用灵活后段设定。你能随时通过 `~/.airecon/config.json` 文件自由更改。支持后端：

- **私有本地服务端 (首选 Ollama 支持):** 例如 `qwen3:32b`，它极大地保护您的网络扫描过程隐私与公司机密边界。
- **主流的大模型云原生服务:** (目前提供支持 **OpenAI/o1/gpt-4o**、**Anthropic claude-3-5**，并集成对 **DeepSeek** 服务底座完美对接) 云服务内部集成针对网络中断的异常的**防崩溃并发指数退避机制 (Exponential Backoff)** 从而解决大请求规模和并发查询环境导致程序闪崩的情况。

### ⚠️ Ollama 本地化模型硬件参考需求
*请切记：基于系统的命令逻辑回传机制与逻辑梳理需求，所选用作脑部的模型必须要具有 <think>（深度连续推理思考），或具有出色 Function-calling (工具映射) 接口响应功能！**不推荐把体积小于参数 30B 级别的轻量模型用于核心扫描，否则大概率由于幻觉导致出现卡死、虚空捏造不存在的 CVE 等恶劣状况！***

| 核心推荐 | 拉取安装命令 | 推荐显存 VRAM | 注意事项与注释 |
|----------|-------------|------|-------|
| **Qwen3.5 122B** | `ollama pull qwen3.5:122b` | 48+ GB | 高质量环境部署，强烈建议搭配高端多 GPU （目前逻辑最佳）|
| **Qwen3 32B** | `ollama pull qwen3:32b` | 20 GB | **基本推荐基元下限配置**，各功能可得保障并流畅运行 |
| **Qwen3 30B (A3B MoE架构)** | `ollama pull qwen3:30b-a3b` | 16 GB | 显卡未受限 24G 的较低配置服务器的推理权衡版本 |

**(注：类似 Llama3/Mistral/Phi 之类的无长推理思维链模型会导致 Agent 操作偏移不适用于本架构！)**

---

## 安装说明与应用部署

### 基础支持需求
- **Python**: 3.10+ （环境必要保证）
- **Docker**: (核心安全需求)。为了生成能够测试并且真实触发工具扫描的沙箱：系统执行前必须要启动 Docker Runtime 以支持隔离化环境构建工具箱 (Kali / Ubuntu)。
- 可连接互联网或已安装好的 Ollama 环境 / 可用的远程 API 服务商。

### 第1步 — 下载库与准备初始环境
安装脚本会自动下载集成包（如缺少时会自动协助拉取 Poetry 处理）

```bash
git clone https://github.com/pikpikcu/airecon.git
cd airecon
./install.sh
```

### 第2步 — 载入配置模型
基于我们上面的需求请拉模型（如果是选用云服务可通过跳过并配置下方的 JSON）：

```bash
ollama pull qwen3:32b
```

### 第3步 — 验证与环境变量整合
若无法随处可得启动，可把系统生成的默认的二进制加载到用户的 PATH 系统目录:

```bash
# 加入至 ~/.bashrc 或者是 ~/.zshrc 
export PATH=\"$HOME/.local/bin:$PATH\"

# 查验一下当前安装
airecon --version
```

### (选填环节): 构建自动化与补充镜像
- **手动编译 Docker 安全执行隔离区箱:** 初次启动 AIRecon 系统就会触发 `docker_auto_build` 默认机制帮您安装。如果不幸失效或你想手动拉 Kali 进行编译可以使用此命令: `docker build -t airecon-sandbox airecon/containers/kali/`。
- **开启自承载 OSINT 调查服务终端 (SearXNG 推荐):** 假如你不想借由外部系统接口做 Google Dork 查询。你可以修改本程序的 config (`searxng_url`)，随后终端拉取： `docker run -d --name searxng -p 8080:8080 searxng/searxng`

---

## 配置文件中心 (`~/.airecon/config.json`)

一切配置将在环境初启时在您的全局目录自动落点。

> 如想要使用各种不同的新模型：修改 `\"ai_provider\"` 后填写您的对应云提供商或接口。如下方例子演示：

```json
{
    "ollama_url": "http://127.0.0.1:11434",
    "ollama_model": "qwen3.5:122b",
    "prox_port": 3000,
    "docker_image": "airecon-sandbox",
    "docker_auto_build": true,
    "deep_recon_autostart": true,
    "agent_max_tool_iterations": 500,
    "vuln_similarity_threshold": 0.7,
    "allow_destructive_testing": true,

    "ai_provider": "openai",
    "openai_api_key": "sk-your-xxx",
    "openai_model": "gpt-4o"
}
```

**若干个可以高度自定义化的测试变量释出:**
- `allow_destructive_testing` : 打开具有验证攻击性确认或执行破坏修改操作验证（谨慎对未授权网络开放以防止发生高危害变更）。
- `agent_max_tool_iterations` : 最高容忍循环任务扫描长度（如果一直扫不出东西）。
- `vuln_similarity_threshold`: 在 0 到 1.0 的安全去重区间内使用杰卡德相似指数处理漏洞发现合并（默认为 0.7）。

---

## 使用技巧与测试用例

唤醒您的交互界面终端并体验 TUI (或者如果想要接着继续跑之前的系统断点，可以补全指令：`airecon start --session <ID>`)
```bash
airecon start 
```

### 发起普通对话以触发功能
这能非常简便：不需要编写晦涩和繁长的命令行。

**精准特定侦察（单行命令执行）：**
```text
查找 example.com 下开放的所有子域名。
扫描 10.0.0.1 的系统端口。
使用 nuclei 针对当前生成出的 output/live_hosts.txt 执行一次综合审查。
检查 https://example.com/login 的系统节点是否包含能够 XSS 弹窗执行的条件。
Fuzzing 利用业务逻辑 API /api/v1/users ，排查系统可能的越权问题 (IDOR)。
```

**无死角业务系统探测（贯穿式）：**
```text
全阶段扫描并分析挖掘 example.com (full recon on example.com)
针对目标系统 https://target.com 呈现一份严密的 Bug Bounty （漏洞赏金）级安全全流程分析评估表。
```

**含凭证式环境检测支持操作：**
```text
登录测试：用 admin@example.com 和 password123 进入 https://example.com/login，再排查其是否潜藏 IDOR。
带 2FA (TOTP验证码保护) : 使用口令密匙（例如 JBSWY3DPEHPK3PXP）进入目标控制端 https://app.example.com 检测
```

**多代理执行体系发令（Multi-Agent System）:**
```text
对 https://example.com/search 单独创建（spawn）一个专攻 XSS 利用探测分析的小型子代理。
将子域名侦察代理化，并设定对 target1.com, target2.com 采取并行扫描挖掘工作 (parallel recon) 。
```

---

## TUI 控制台视图示意
由于您的运行过程是在复杂的代理协调框架下调用的工具流：左侧窗口负责通讯追踪、反馈错误，工具运行使用方框并依据左端颜色描绘呈现调用/完成生命周期。
右侧的工作窗口为您直接映射本地 `workspace/` 以及针对高价值产物：例如被分析系统捕捉并经过有效性筛查出的 CVSS 评估的 Markdown 漏洞表。下方展示了 Docker、模型连接运行时的概览。

```text
┌──────────────────────────────────────────────────────────┐
│  AI 交互与通信日志展示        │  本地工作区目录视图 Tree       │
│                               │  └── example.com/        │
│  [工具信息] subfinder正在调度  │      ├── output/         │
│  ┌─────────────────────────┐  │      ├── tools/          │
│  │ execute                 │  │      └── vulnerabilities/ │
│  │ subfinder -d example.com│  │          └── sqli.md     │
│  │ [黄色包边状态=正在处理内] │  │                          │
│  └─────────────────────────┘  │  实时系统漏洞探测板        │
│                               │  ┌─────────────────────┐ │
│  找到目标: sub1.example.com │  │ \u2b55\ufe0f SQL注入风险 /api/login │ │
│                               │  └─────────────────────┘ │
├──────────────────────────────────────────────────────────┤
│  ● Ollama/云端  ● Docker集成 │ 运行模型: qwen3.5:122b  │ 
└──────────────────────────────────────────────────────────┘
```

---

## 防撞车与知识技术防漏失去重管理机制

> 在多阶段、极度冗长而深邃的网路数据交互采集环境过程中，往往最令大型生成式系统头疼的是：“它经常忘事，且喜欢瞎造相同的事情”。

为了规避该问题，AIRecon 设置了核心的安全拦截阀门组件：
1. Jaccard (杰卡德相似系数去重)：任何产出的漏洞都必须被系统抽样计算，低于 `vuln_similarity_threshold` 的才会正式登记在主干记录上。
2. 内部上下文的摘要快取回读 (`Context Re-injection`)机制：防止超过上下文导致的认知空白。

---

## 数据产出记录规范 

每当渗透发现漏洞后，系统必定将最终包含有效测试方式的报告文件导出至被建立对象本地操作文件夹下的 `vulnerabilities/` （也就是您的 `workspace/`，方便快速将漏洞文件直接整合交递平台汇报）：

```markdown
# 位于 /api/v1/login 下的 SQL 类型注入验证

**漏洞定级:** HIGH (依照评价规范体系 CVSS 评分: 9.1)
**危害划分:** SQL Injection
**接口与访问节点:** POST /api/v1/login

## 漏洞详细原理及成因解析
[系统出具的不得少于80个英文字节标准长度的代码执行回溯链路分析或解释文档...]

## 基于请求协议的无害可复现验证脚本 (Python)
```python
import requests
response = requests.post("https://example.com/api/v1/login",
    data={"username": "admin'--", "password": "x"})
# 执行之后如果回退状态标为 HTTP 200 并含有合法登录会话则视为系统漏洞确认成立。
```
## 提供凭据信息说明与附带解释 (Evidence)
HTTP 200 OK — 顺利获取到了管理员认证的跳过身份特权

## 安全建议 (系统主动修缮源码范例提示)
```python
# 利用 SQL Parameterized 占位符操作防范预拼接防越位：
cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s",
               (username, password))
```

## 系统评分量表
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
```
所有 AI 产出的可验证攻击或挖掘流程（如带有 *might, could be vulnerable* 不确定的推诿性用词或不能提供足够有效验证代码字符数的情形下），该信息或文书**必定被系统拦截，报告做不合格驳回，指令代理进行继续排查直至得到验证肯定！**

---

<div align=\"center\">

**开源协议 :** MIT License <br>

<h3>\u26a0\ufe0f 免责警告与法律要求 (Disclaimer)</h3>
 本软件由原作者编写仅仅作为**合规授权场景以及教育、安全研判等内部自证用途进行合法的使用。** 用户利用本文档体系构建并造成的未授权使用与后果行为（包括任何意外连带破坏事故/滥用渗透及侵入动作），均需自主承载所有责任，本站开发者团队既不对该滥用带来的法律责任进行受权或者担责！务请获得系统主/甲方确权认可后展开行为操作。

</div>