#!/usr/bin/env python3
"""
Test Telegram Notifications

Quick script to test your Telegram bot configuration.

Usage:
    python3 scripts/test_telegram.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.telegram_notifier import TelegramNotifier
from config.settings import settings


def main():
    print("\n" + "="*70)
    print("TELEGRAM NOTIFICATION TEST")
    print("="*70 + "\n")

    # Check configuration
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not configured in .env")
        print("\nTo configure Telegram notifications:")
        print("1. Talk to @BotFather on Telegram")
        print("2. Create a new bot with /newbot")
        print("3. Copy the bot token")
        print("4. Add to .env: TELEGRAM_BOT_TOKEN=your_token_here")
        return

    if not settings.TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID not configured in .env")
        print("\nTo get your Chat ID:")
        print("1. Send a message to your bot on Telegram")
        print("2. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
        print("3. Look for 'chat':{'id': 123456789}")
        print("4. Add to .env: TELEGRAM_CHAT_ID=123456789")
        return

    if not settings.TELEGRAM_NOTIFICATIONS_ENABLED:
        print("⚠️  Telegram notifications are DISABLED in .env")
        print("\nTo enable notifications:")
        print("Add to .env: TELEGRAM_NOTIFICATIONS_ENABLED=true")
        print("\nTesting anyway...")

    print(f"Bot Token: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"Chat ID: {settings.TELEGRAM_CHAT_ID}")
    print(f"Enabled: {settings.TELEGRAM_NOTIFICATIONS_ENABLED}")
    print()

    # Initialize notifier
    telegram = TelegramNotifier(
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        chat_id=settings.TELEGRAM_CHAT_ID,
        enabled=True  # Force enable for testing
    )

    # Send test message
    print("Sending test message...")
    success = telegram.send_test_message()

    if success:
        print("\n✅ SUCCESS! Check your Telegram for the test message.")
        print("\nTelegram notifications are working correctly!")
    else:
        print("\n❌ FAILED! Could not send message.")
        print("\nPossible issues:")
        print("1. Bot token is invalid")
        print("2. Chat ID is incorrect")
        print("3. You haven't started a conversation with the bot")
        print("   → Open Telegram and send /start to your bot")
        print("4. Network/firewall issues")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
