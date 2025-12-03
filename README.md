# 🤖 SentinelOne

A custom-built moderation and utility bot tailored for the **Markaroni YouTube Channel Discord Server**. It helps keep the server safe, organized, and interactive, offering tools for message reporting, moderation actions, logging, and more.

---

## ✨ Features

* 🔨 **Message Reporting System**
  Members can react to messages with a 🚨 to report them. The bot will ask for a reason via DM and forward the report to a designated log channel.

* 📩 **Interactive DM Prompting**
  Once a message is reported, the bot sends a DM asking for the reason. On response, it automatically logs the report.

* 🧹 **Moderation Tools (WIP)**
  Commands to timeout, kick, or ban users (final moderation hooks can be added based on server role setup).

* 🛡️ **Secure and Role-Sensitive**
  Designed to only allow authorized users (like moderators) to perform sensitive actions.

* 🧾 **Detailed Logs**
  All moderation events and reports are logged into a specified channel to maintain transparency and records.

---

## ⚙️ Setup Instructions

### Requirements

* Python 3.10+
* `discord.py` v2.3+
* A bot token from the [Discord Developer Portal](https://discord.com/developers/applications)

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/SentinelOne.git
cd SentinelOne
pip install -r requirements.txt
```

### Configuration

* Create a `.env` file and add your bot token:

  ```env
  DISCORD_BOT_TOKEN=your_token_here
  ```


---

## 🚀 Running the Bot

```bash
python3 main.py
    OR
python main.py
```

---

## 🧠 How It Works (Report Flow)

1. A user reacts with 🚨 on any message.
2. The bot sends a DM: “You reacted on this message in \[Server]. Give the reason.”
3. The user replies with a reason.
4. The bot logs:

   * Who reported
   * Whom they reported
   * Original message content
   * The reason
   * In which channel the message was sent

---

## 📌 Notes

* Make sure the bot has permission to send DMs to users.
* If DMs are blocked by the user or server settings, the bot won’t be able to collect a reason.
* The message reply issue may occur due to missing `message_reference` handling or bot permissions. Check those if bugs persist.

---

## 💬 Contribution

PRs and suggestions are welcome! This bot is a WIP and designed specifically for **Markaroni's community** but feel free to adapt and extend it.

---

## 📄 License

MIT License – feel free to use, modify, and share.


