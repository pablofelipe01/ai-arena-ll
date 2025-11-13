# Telegram Notifications Setup

Get real-time alerts about your trading system directly on Telegram!

---

## 📱 What You'll Receive

- **Server Events**: Startup, shutdown, errors
- **Grid Events**: New grids created, cycles completed
- **Trading Events**: Positions opened/closed, stop loss triggered
- **Summaries**: Hourly and daily performance reports

---

## 🤖 Step 1: Create Your Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a conversation with `/start`
3. Create a new bot with `/newbot`
4. Follow the prompts:
   - **Bot Name**: `My Trading Bot` (or whatever you want)
   - **Username**: `my_trading_bot` (must end with `_bot`)
5. **SAVE THE TOKEN** - You'll get something like:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

---

## 💬 Step 2: Get Your Chat ID

### Method 1: Using Bot (Easiest)

1. Find your bot on Telegram (search for the username you created)
2. Send `/start` to your bot
3. Visit this URL in your browser (replace `<YOUR_BOT_TOKEN>`):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
4. Look for the `"chat":{"id":123456789}` in the response
5. **SAVE THIS NUMBER** - That's your Chat ID

### Method 2: Using @userinfobot

1. Search for `@userinfobot` on Telegram
2. Send `/start`
3. It will reply with your Chat ID

---

## ⚙️ Step 3: Configure Your .env File

Add these lines to your `.env` file:

```bash
# Telegram Notifications
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
TELEGRAM_NOTIFICATIONS_ENABLED=true
```

Replace:
- `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` with your bot token
- `987654321` with your chat ID

---

## ✅ Step 4: Test Your Setup

Run the test script:

```bash
python3 scripts/test_telegram.py
```

You should see:
```
✅ SUCCESS! Check your Telegram for the test message.
```

And receive a message on Telegram saying:
```
✅ TELEGRAM NOTIFICATIONS ENABLED

Bot is connected and ready to send alerts.
```

---

## 🚀 Step 5: Start Your Server

Restart your trading server:

```bash
python3 scripts/start.py
```

You should immediately receive a notification:
```
🚀 SERVER STARTED

Time: 2025-01-12 15:00:00
Grids Recovered: 17

System is now online and trading.
```

---

## 🔔 What Notifications You'll Get

### System Events
- **🚀 Server Started** - When server boots up
- **⛔ Server Stopped** - When server shuts down
- **❌ Error** - Critical errors

### Grid Trading
- **📊 Grid Created** - New grid set up (silent notification)
- **💰 Grid Cycle Completed** - When buy-sell cycle completes
- **🛑 Stop Loss Triggered** - When grid hits stop loss

### Position Events
- **🟢 Position Opened** - New LONG position (silent)
- **🔴 Position Opened** - New SHORT position (silent)
- **✅ Position Closed** - Profitable close
- **❌ Position Closed** - Loss close

### Reports
- **📈 Hourly Summary** - Every hour (silent)
- **📊 Daily Summary** - Once a day

---

## 🛠️ Troubleshooting

### "Failed to send message"

1. **Check bot token** - Make sure it's correct, no extra spaces
2. **Check chat ID** - Should be a number, not username
3. **Start the bot** - You MUST send `/start` to your bot first
4. **Test manually**:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" \
     -d "chat_id=<YOUR_CHAT_ID>" \
     -d "text=Test message"
   ```

### "Bot token not configured"

- Your `.env` file doesn't have `TELEGRAM_BOT_TOKEN`
- Or it's empty/commented out

### "Chat ID not configured"

- Your `.env` file doesn't have `TELEGRAM_CHAT_ID`
- Or it's empty/commented out

### "Notifications disabled"

- Set `TELEGRAM_NOTIFICATIONS_ENABLED=true` in `.env`

---

## 📝 Example .env Configuration

```bash
# Telegram Notifications
TELEGRAM_BOT_TOKEN=6234567890:AAHxyz123ABC_def456GHI-jkl789MNOpqr
TELEGRAM_CHAT_ID=123456789
TELEGRAM_NOTIFICATIONS_ENABLED=true
```

---

## 🔒 Security Notes

- **Never share your bot token** - Anyone with it can control your bot
- **Never commit `.env` to git** - It's already in `.gitignore`
- **Bot can only message you** - It can't see other chats
- **You control the bot** - You can revoke token anytime via @BotFather

---

## 🎯 Next Steps

Once notifications are working:

1. **Test a restart** - Stop and start server, check if you get notifications
2. **Wait for grid events** - You'll get notifications as trading happens
3. **Monitor your phone** - You can now track trading from anywhere!

---

## 💡 Pro Tips

1. **Mute chat for silent notifications** - Unmute for important ones only
2. **Pin the chat** - Easy access to trading updates
3. **Create a group** - Invite your bot and team members
4. **Multiple bots** - Create different bots for testnet vs mainnet

---

## 🆘 Need Help?

If you're stuck:

1. Run the test script: `python3 scripts/test_telegram.py`
2. Check server logs: `tail -f logs/app.log | grep -i telegram`
3. Verify `.env` configuration
4. Test bot manually with curl command above

---

**You're all set! 🎉**

Your trading system will now keep you informed 24/7 via Telegram.
