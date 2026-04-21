# 在 Claude Code 中使用推送通知

## 环境变量配置

在 `.env` 中设置好 `API_KEY`，并确保服务器已运行。

```bash
export API_KEY="your-api-key-here"
export MOBILE_SERVER_URL="http://localhost:8000"
```

---

## 使用 notify.py 发送通知

```bash
# 立即发送
python3 notify.py "代码构建完成！"

# 自定义标题和优先级
python3 notify.py "测试全部通过" --title "CI 通知" --priority high --tags "white_check_mark"

# 定时发送（指定时间）
python3 notify.py "记得开会" --schedule "2026-04-22T14:00:00" --title "会议提醒"

# 定时发送（Cron，每天早上9点）
python3 notify.py "早安！今日计划？" --cron "0 9 * * *" --title "每日提醒"
```

---

## 使用 curl 直接调用

```bash
# 立即推送
curl -s -X POST http://localhost:8000/notify \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"任务完成","message":"重构工作已完成","priority":"high","tags":["tada"]}'

# 添加 Todo
curl -s -X POST http://localhost:8000/todos \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Review PR #42","list":"Work","priority":2}'

# 查询 Todo
curl -s "http://localhost:8000/todos?completed=false" \
  -H "Authorization: Bearer $API_KEY" | python3 -m json.tool

# 定时任务（明天早上9点）
curl -s -X POST http://localhost:8000/schedule \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"每日站会","message":"站会时间到了","run_at":"2026-04-22T09:00:00","priority":"high"}'

# 查看所有定时任务
curl -s http://localhost:8000/schedule \
  -H "Authorization: Bearer $API_KEY"

# 取消定时任务
curl -s -X DELETE "http://localhost:8000/schedule/<job_id>" \
  -H "Authorization: Bearer $API_KEY"
```

---

## 服务器健康检查

```bash
curl -s http://localhost:8000/health
# 返回: {"status":"ok","scheduled_jobs":2,"todo_count":5,"ntfy_topic":"myphone-xxx"}
```

---

## ntfy 优先级说明

| priority | 效果 |
|----------|------|
| `min` | 静默，只在通知中心显示 |
| `low` | 无声音 |
| `default` | 正常通知 |
| `high` | 高优先级，声音更响 |
| `urgent` | 紧急，突破免打扰模式 |

## 常用 ntfy 标签（表情）

`bell` 🔔 `warning` ⚠️ `tada` 🎉 `white_check_mark` ✅ `x` ❌ `alarm_clock` ⏰ `computer` 💻
