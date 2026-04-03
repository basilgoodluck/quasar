from abc import ABC, abstractmethod
from contracts.router import submit_trade_intent
from contracts.validation import post_checkpoint
from config import KRAKEN_CLI_PATH, KRAKEN_SANDBOX, KRAKEN_API_KEY, KRAKEN_API_SECRET
from logger import get_logger
import subprocess
import json

logger = get_logger(__name__)


class BaseStrategy(ABC):

    def skip(self, symbol: str, reason: str) -> dict:
        return {
            "symbol":      symbol,
            "action":      "SKIP",
            "leverage":    0.0,
            "risk_pct":    0.0,
            "rr_ratio":    0.0,
            "explanation": reason,
            "ready":       False,
        }

    @abstractmethod
    def analyze(self, symbol: str) -> dict:
        ...

    def open_position(self, decision: dict, price: float) -> dict:
        pair      = decision["symbol"]
        action    = decision["action"]
        risk_pct  = decision["risk_pct"]
        leverage  = decision["leverage"]
        rr_ratio  = decision["rr_ratio"]

        from contracts.vault import get_available_capital
        available = get_available_capital()
        amount    = round((available * risk_pct / 100) * leverage, 2)

        result = submit_trade_intent(pair, action, amount)
        if not result["approved"]:
            logger.warning(f"[{pair}] TradeIntent rejected: {result.get('reason')}")
            return {"executed": False, "reason": result.get("reason")}

        kraken_action = "buy" if action == "LONG" else "sell"
        volume        = str(round(amount / price, 6))

        cmd = [KRAKEN_CLI_PATH, "--json"]
        if KRAKEN_SANDBOX:
            cmd.append("--sandbox")
        cmd += ["--api-key", KRAKEN_API_KEY, "--api-secret", KRAKEN_API_SECRET]
        cmd += ["order", "add", "--pair", pair, "--type", kraken_action, "--ordertype", "market", "--volume", volume]

        try:
            out    = subprocess.check_output(cmd, timeout=15)
            order  = json.loads(out)
            logger.info(f"[{pair}] order placed: {order}")

            post_checkpoint(
                action=action,
                pair=pair,
                amount_usd=amount,
                price=price,
                reasoning=decision["explanation"],
                confidence=decision["regime"]["confidence"],
                intent_hash=result["intent_hash"],
            )

            return {"executed": True, "order": order, "intent_hash": result["intent_hash"]}

        except Exception as e:
            logger.error(f"[{pair}] Kraken order failed: {e}")
            return {"executed": False, "reason": str(e)}

    def close_position(self, symbol: str, volume: str) -> dict:
        cmd = [KRAKEN_CLI_PATH, "--json"]
        if KRAKEN_SANDBOX:
            cmd.append("--sandbox")
        cmd += ["--api-key", KRAKEN_API_KEY, "--api-secret", KRAKEN_API_SECRET]
        cmd += ["order", "add", "--pair", symbol, "--type", "sell", "--ordertype", "market", "--volume", volume]

        try:
            out   = subprocess.check_output(cmd, timeout=15)
            order = json.loads(out)
            logger.info(f"[{symbol}] position closed: {order}")
            return {"closed": True, "order": order}
        except Exception as e:
            logger.error(f"[{symbol}] close failed: {e}")
            return {"closed": False, "reason": str(e)}

    def get_open_orders(self) -> dict:
        cmd = [KRAKEN_CLI_PATH, "--json", "--api-key", KRAKEN_API_KEY, "--api-secret", KRAKEN_API_SECRET, "order", "list"]
        try:
            out = subprocess.check_output(cmd, timeout=15)
            return json.loads(out)
        except Exception as e:
            logger.error(f"get_open_orders failed: {e}")
            return {}