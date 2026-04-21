# 手机消息推送 + 论文检索自动化系统

从 Windows 电脑向 iPhone 发推送通知、管理 Todo、每日自动检索社会学论文并发送到 iMessage 群组。

---

## 目录

- [系统架构](#系统架构)
- [第一步：安装和配置服务器](#第一步安装和配置服务器)
- [第二步：配置 iPhone 推送通知](#第二步配置-iphone-推送通知)
- [第三步：配置 iOS 快捷指令](#第三步配置-ios-快捷指令)
- [第四步：设置外网访问](#第四步设置外网访问)
- [第五步：Windows 开机自启](#第五步windows-开机自启)
- [第六步：iOS 自动化设置](#第六步ios-自动化设置)
- [日常使用](#日常使用)
- [API 速查](#api-速查)
- [常见问题](#常见问题)

---

## 系统架构

```
Windows 电脑（服务器）
  └── FastAPI + APScheduler
        ├── 每晚 21:00 → ntfy 推送「提交关键词」通知
        ├── 每早 08:00 → Semantic Scholar 检索 → Claude AI 总结
        │               → ntfy 推送摘要 + 存入数据库
        └── GET /routines/digest/latest ← iOS 快捷指令拉取
                                              └── 发送到 iMessage 群组

iPhone
  ├── ntfy app → 接收推送通知
  ├── 快捷指令「提交论文关键词」→ POST /routines/keywords
  ├── 快捷指令「发送论文速递」  → GET /routines/digest/latest → iMessage 群组
  └── iOS 自动化 → 每天 09:00 自动运行「发送论文速递」
```

推送方案使用 **ntfy.sh**（免费，无需 Apple 开发者账号）。外网访问使用 **Cloudflare Tunnel**（免费，永久 URL）。

---

## 第一步：安装和配置服务器

### 1.1 安装依赖

Windows 上需要先安装 Python 3.11+，然后：

```bash
cd claudecode
pip install -r requirements.txt
```

### 1.2 创建配置文件

复制示例配置并填入你的值：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# iPhone ntfy app 订阅的 topic（设成不易猜到的随机字符串，例如 myphone-xk7q2m）
NTFY_DEFAULT_TOPIC=myphone-你的随机字符串

# API 鉴权密钥（iOS 快捷指令调用时需要携带，设成一个长随机字符串）
API_KEY=你的长随机密钥

# Anthropic API 密钥（用于 Claude AI 总结论文）
# 从 https://console.anthropic.com 获取
ANTHROPIC_API_KEY=sk-ant-...

# 定时任务时间（Cron 格式，默认晚上9点询问关键词，早上8点检索论文）
EVENING_PROMPT_CRON=0 21 * * *
MORNING_SEARCH_CRON=0 8 * * *

# 其余保持默认即可
NTFY_BASE_URL=https://ntfy.sh
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DB_PATH=./todos.db
TIMEZONE=Asia/Shanghai
```

### 1.3 启动服务器

```bash
python3 run.py
```

看到以下输出说明启动成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

验证服务器正常运行：

```bash
curl http://localhost:8000/health
# 返回: {"status":"ok","scheduled_jobs":2,...}
```

---

## 第二步：配置 iPhone 推送通知

1. 在 iPhone 上安装 **ntfy** app（App Store 搜索「ntfy」）
2. 打开 ntfy → 右上角「+」→ 订阅 topic
3. 填入 `.env` 中 `NTFY_DEFAULT_TOPIC` 的值（例如 `myphone-xk7q2m`）
4. 服务器端发送测试通知验证：

```bash
curl -X POST http://localhost:8000/notify \
  -H "Authorization: Bearer 你的API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"测试","message":"连接成功！"}'
```

iPhone 上应立即收到通知。

---

## 第三步：配置 iOS 快捷指令

以下所有快捷指令中，将 `你的服务器地址` 替换为实际地址（局域网用 `http://192.168.x.x:8000`，外网用 Cloudflare Tunnel 地址）。

---

### 快捷指令 1：提交论文关键词

> 每晚收到推送后，点击按钮触发此快捷指令，输入明天想搜索的关键词。

**命名为：`提交论文关键词`**（名称必须完全一致，推送通知按钮会跳转到这个名字）

| 步骤 | 动作 | 配置 |
|------|------|------|
| 1 | **询问输入** | 提示语：`明天想搜什么社会学论文关键词？`，输入类型：文本，存为变量 `Keywords` |
| 2 | **获取 URL 内容** | 见下方 |
| 3 | **显示结果** | |

步骤 2 配置：
- URL: `http://你的服务器地址/routines/keywords`
- 方法: `POST`
- 请求头: `Authorization: Bearer 你的API_KEY`，`Content-Type: application/json`
- 请求体: `{"keywords": "{{Keywords}}"}`

---

### 快捷指令 2：发送论文速递到 iMessage 群组

> 每天早上服务器检索完论文后，此快捷指令取回格式化摘要并发到你的 iMessage 群组。

**命名为：`发送论文速递`**

| 步骤 | 动作 | 配置 |
|------|------|------|
| 1 | **获取 URL 内容** | GET `http://你的服务器地址/routines/digest/latest`，请求头加 Authorization |
| 2 | **从输入中获取字典** | 解析 JSON 响应 |
| 3 | **获取字典中的值** | 键名 `content`，存为变量 `DigestText` |
| 4 | **发送信息** | 收件人：选择你的 iMessage 群组；信息：`DigestText`；关闭「发送前询问」 |
| 5 | **（可选）通知** | 显示「论文速递已发送」 |

> **微信群用户：** iOS 无法直接向微信群发消息。把步骤 4 改为「**设定剪贴板**」→ `DigestText`，然后自动打开微信，手动粘贴发送。

---

### 快捷指令 3：添加 Todo（可选）

| 步骤 | 动作 | 配置 |
|------|------|------|
| 1 | **询问输入** | 提示语：`Todo 标题`，存为变量 `Title` |
| 2 | **获取 URL 内容** | POST `http://你的服务器地址/todos`，请求体 `{"title": "{{Title}}","list":"Personal"}` |
| 3 | **显示结果** | |

---

## 第四步：设置外网访问

如果手机不在家里 WiFi 范围内，需要外网访问方案。推荐 Cloudflare Tunnel（免费，永久 URL）：

### Cloudflare Tunnel（推荐）

1. 下载 `cloudflared`：https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

2. Windows 上运行：
```bash
cloudflared tunnel --url http://localhost:8000
```

3. 终端会输出类似：
```
https://random-name.trycloudflare.com
```

4. 将 iOS 快捷指令中的服务器地址改为这个 URL（带 `https://`）

> 每次重启 cloudflared 后 URL 会变化。固定 URL 需要注册 Cloudflare 账号并创建命名 tunnel（免费）。

### ngrok（备选）

```bash
ngrok http 8000
# 输出: https://abc123.ngrok-free.app
```

免费版每次重启 URL 变化。

---

## 第五步：Windows 开机自启

用 Windows 任务计划程序让服务器开机自动运行：

1. 打开「任务计划程序」→「创建基本任务」
2. 触发器：选「计算机启动时」
3. 操作：选「启动程序」
   - 程序：`C:\Users\你的用户名\AppData\Local\Programs\Python\Python311\python.exe`
   - 参数：`run.py`
   - 起始于：`C:\你的项目路径\claudecode`
4. 勾选「使用最高权限运行」→ 完成

验证：重启电脑后访问 `http://localhost:8000/health`。

---

## 第六步：iOS 自动化设置

在「快捷指令」→「自动化」→「+」配置以下两条自动化：

### 自动化 1：每晚推送关键词询问（服务器已自动推送，无需配置快捷指令自动化）

服务器每晚 21:00 自动推送通知，点通知上的「提交关键词」按钮即可触发快捷指令。

### 自动化 2：每天 09:00 发送论文速递到群组

| 设置项 | 值 |
|--------|-----|
| 触发器 | 时间 → 每天 09:00 |
| 动作 | 运行快捷指令「发送论文速递」 |
| 立即运行 | 开启（关闭「运行前询问」） |

> 设为 09:00 是因为服务器 08:00 开始检索，通常 08:10-08:20 完成，预留缓冲时间。

---

## 日常使用

### 完整的每日流程

```
晚上 21:00  iPhone 收到 ntfy 推送「今晚的论文关键词」
            点击通知上的「提交关键词」按钮
            → 打开快捷指令「提交论文关键词」
            → 输入关键词（如：digital inequality, algorithmic governance）
            → 发送到服务器保存

早上 08:00  服务器自动运行：
            1. 取出昨晚提交的关键词
            2. 检索 Semantic Scholar（最多6篇论文）
            3. Claude AI 生成：
               - 每篇论文2-3句摘要
               - 主题学术讨论
               - 格式化「论文速递」（适合群发的完整版）
            4. 推送两条 ntfy 通知（摘要 + 讨论）
            5. 存储论文速递到数据库

早上 09:00  iPhone 自动运行「发送论文速递」快捷指令
            → 从服务器取回论文速递文本
            → 自动发送到 iMessage 群组
```

### 手动操作

**网页控制台**（推荐）：访问 `http://你的服务器地址/dashboard`

- 查看和开关定时任务
- 手动提交关键词（不用手机也能提交）
- 直接发送推送通知
- 查看最近检索的论文列表

**命令行发送通知：**

```bash
curl -X POST http://localhost:8000/notify \
  -H "Authorization: Bearer 你的API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"提醒","message":"你的消息内容","priority":"high"}'
```

**查看今日论文速递：**

```bash
curl http://localhost:8000/routines/digest/latest \
  -H "Authorization: Bearer 你的API_KEY"
```

---

## API 速查

所有写操作需要请求头 `Authorization: Bearer 你的API_KEY`。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 服务器状态检查 |
| GET | `/dashboard` | 网页控制台 |
| POST | `/notify` | 立即发送推送通知 |
| POST | `/schedule` | 定时发送推送通知 |
| GET | `/schedule` | 查看所有定时任务 |
| DELETE | `/schedule/{id}` | 取消定时任务 |
| GET | `/todos` | 查询 Todo（支持 `?completed=false&list=Personal`） |
| POST | `/todos` | 添加 Todo |
| PATCH | `/todos/{id}` | 更新 Todo |
| DELETE | `/todos/{id}` | 删除 Todo |
| GET | `/routines` | 查看所有定时例程 |
| POST | `/routines/{id}/toggle` | 开关定时例程 |
| POST | `/routines/keywords` | 提交论文关键词 |
| GET | `/routines/papers/latest` | 查看最近检索的论文 |
| GET | `/routines/digest/latest` | 获取今日论文速递文本 |

**推送优先级（`priority` 字段）：**

| 值 | 效果 |
|----|------|
| `min` | 静默，只在通知中心显示 |
| `low` | 无声音 |
| `default` | 正常通知 |
| `high` | 高优先级，声音更响 |
| `urgent` | 紧急，突破免打扰模式 |

---

## 常见问题

**Q: iPhone 收不到推送通知**
- 检查 ntfy app 是否订阅了正确的 topic（和 `.env` 里的 `NTFY_DEFAULT_TOPIC` 一致）
- 检查服务器是否正常运行（访问 `/health`）
- 检查 iPhone 的通知权限是否授予了 ntfy app

**Q: 快捷指令提示「连接失败」**
- 确认 URL 正确（局域网还是外网地址）
- 确认服务器正在运行
- 如果用外网访问，检查 Cloudflare Tunnel 是否在运行

**Q: 早上没有收到论文推送**
- 检查前一天晚上是否提交了关键词（在控制台 `/dashboard` 可以查看）
- 查看服务器日志是否有错误
- 确认 `ANTHROPIC_API_KEY` 已正确填写

**Q: 论文速递没有发到群组**
- 检查「发送论文速递」快捷指令中的收件人是否正确选择了群组
- 确认 iOS 自动化的「运行前询问」已关闭
- 手动运行快捷指令测试是否正常

**Q: 想修改检索时间**
- 在网页控制台 `/dashboard` 直接修改
- 或编辑 `.env` 中的 `EVENING_PROMPT_CRON` / `MORNING_SEARCH_CRON`，重启服务器生效

**Q: 想要搜索其他领域的论文（不只社会学）**
- 提交关键词时直接输入其他领域的英文关键词即可，系统不限制学科
- 例如：`machine learning fairness`、`urban planning mobility`
