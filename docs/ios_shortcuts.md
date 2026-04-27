# iOS 快捷指令配置指南

## 前置条件

1. 在 iPhone 上安装 **ntfy** app（App Store 搜索 "ntfy"）
2. 打开 ntfy → 右上角 "+" → 订阅 topic，填入 `.env` 里的 `NTFY_DEFAULT_TOPIC` 值
3. 确保服务器已运行（`python3 run.py`），并且 iPhone 能访问服务器地址

> 如果手机和服务器不在同一 WiFi，需要配置 ngrok 或 Cloudflare Tunnel（见下方）

---

## 快捷指令 1：添加 Todo

在「快捷指令」app 中新建快捷指令，依次添加以下动作：

| 步骤 | 动作 | 配置 |
|------|------|------|
| 1 | **询问输入** | 提示语：`Todo 标题`，输入类型：文本 → 存为变量 `Title` |
| 2 | **询问输入**（可选） | 提示语：`备注`，输入类型：文本 → 存为变量 `Notes` |
| 3 | **获取 URL 内容** | 见下方详细配置 |
| 4 | **显示结果** | 显示上一步的输出 |

**步骤 3 详细配置：**
- URL: `http://192.168.x.x:8000/todos`（替换为你的服务器 IP）
- 方法: `POST`
- 请求头:
  - `Authorization`: `Bearer 你的API_KEY`
  - `Content-Type`: `application/json`
- 请求体（JSON）:
  ```json
  {
    "title": "{{Title}}",
    "notes": "{{Notes}}",
    "list": "Personal"
  }
  ```

**添加到主屏幕：** 在快捷指令详情页点击分享 → 添加到主屏幕

**Siri 触发：** 将快捷指令命名为「添加待办」，即可说「嘿 Siri，添加待办」

---

## 快捷指令 2：查看未完成 Todo

| 步骤 | 动作 | 配置 |
|------|------|------|
| 1 | **获取 URL 内容** | GET `http://192.168.x.x:8000/todos?completed=false&limit=20` + Authorization 头 |
| 2 | **从输入中获取字典** | 获取上一步结果 |
| 3 | **重复操作** | 对字典中每一项重复 |
| 4 | **显示通知** | 标题: `{{当前项目.title}}`，正文: `{{当前项目.notes}}` |

---

## 快捷指令 3：标记 Todo 完成

| 步骤 | 动作 | 配置 |
|------|------|------|
| 1 | **询问输入** | 提示语：`Todo ID`，输入类型：数字 → 存为变量 `TodoID` |
| 2 | **获取 URL 内容** | PATCH `http://192.168.x.x:8000/todos/{{TodoID}}` + 请求体 `{"completed": true}` |
| 3 | **显示结果** | |

---

## 自动化（定时提醒）

在「快捷指令」→「自动化」→「+" → 「时间」：

**示例：每天早上 9 点显示今日 Todo**
1. 触发器：每天 09:00
2. 动作：GET `/todos?completed=false` → 遍历 → 显示通知

---

## 跨网络访问（不在同一 WiFi）

### 方案 A：ngrok（免费，URL 每次重启变化）
```bash
# 在服务器端运行
ngrok http 8000
# 输出类似: https://abc123.ngrok-free.app
```
将 iPhone 快捷指令中的 URL 改为 `https://abc123.ngrok-free.app`

### 方案 B：Cloudflare Tunnel（免费，URL 永久）
```bash
cloudflared tunnel --url http://localhost:8000
# 输出类似: https://xxx.trycloudflare.com
```

### 方案 C：路由器端口转发
在路由器管理界面将外网端口 8000 转发到服务器的内网 IP:8000，然后用公网 IP 访问。
