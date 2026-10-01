"""Optional Telegram alerts; failures never interrupt scanning."""
from __future__ import annotations

import asyncio
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def send(self, result: dict) -> bool:
        if not settings.enable_telegram or not settings.telegram_bot_token or not settings.telegram_chat_id:
            logger.info("Telegram skipped: not configured")
            return False
        risk = result.get("risk", {})
        reasons = "\n".join(f"• {item}" for item in result.get("reasoning", [])[:4]) or "• Mixed evidence"
        risks = "\n".join(f"• {item}" for item in result.get("risks", [])[:3]) or "• Standard market risk"
        message = (
            f"🚨 TRADE OPPORTUNITY\n\n{result['symbol']} — {result['recommendation']}\n"
            f"Score: {result['score']:.1f}/10 | Confidence: {result['confidence']:.0%}\nPrice: ${result['price']:.4f}\n\n"
            f"Entry: ${result['entry_min']:.4f} - ${result['entry_max']:.4f}\nStop: ${result['stop_loss']:.4f}\n"
            f"Targets: ${result['target_1']:.4f} / ${result['target_2']:.4f}\nRisk/Reward: 1:{result['risk_reward_ratio']:.1f}\n"
            f"Risk: {risk.get('risk_level', 'N/A')}\n\nMain reasons:\n{reasons}\n\nRisks:\n{risks}\n\nResearch signal only. Manual execution required."
        )
        async def _send() -> None:
            from telegram import Bot
            async with Bot(settings.telegram_bot_token) as bot:
                await bot.send_message(chat_id=settings.telegram_chat_id, text=message)
        try:
            try:
                asyncio.get_running_loop()
                import threading
                error: list[Exception] = []
                def runner() -> None:
                    try: asyncio.run(_send())
                    except Exception as exc: error.append(exc)
                thread = threading.Thread(target=runner, daemon=True); thread.start(); thread.join(20)
                if error: raise error[0]
            except RuntimeError:
                asyncio.run(_send())
            logger.info("Telegram status=sent symbol=%s", result["symbol"])
            return True
        except Exception as exc:
            logger.warning("Telegram unavailable error=%s", type(exc).__name__)
            return False
