import json
import subprocess
import time
from abc import ABC, abstractmethod
from contracts.router import submit_trade_intent
from contracts.validation import post_checkpoint, post_skip_checkpoint
from database.connection import get_connection
from config import KRAKEN_CLI_PATH, KRAKEN_PAPER_MODE
from logger import get_logger

logger = get_logger(__name__)

def _pf(symbol: str) -> str:
    return symbol if symbol.startswith("PF_") else f"PF_{symbol}"

def _write_pending_outcome(
    intent_hash: str,
    pair: str,
    action: str,
    entry_price: float,
    amount_usd: float,
    confidence: float,
    reputation_at_entry: float,
    checkpoint_hash: str,
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO trade_outcomes
                    (intent_hash, pair, action, entry_price, amount_usd,
                     confidence_at_entry, reputation_at_entry, checkpoint_hash,
                     status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PENDING', %s)
                ON CONFLICT (intent_hash) DO NOTHING
            """, (
                intent_hash, pair, action, entry_price, amount_usd,
                confidence, reputation_at_entry, checkpoint_hash,
                int(time.time()),
            ))
            conn.commit()

def _ensure_paper_init():
    try:
        subprocess.check_output(
            [KRAKEN_CLI_PATH, "futures", "paper", "status", "-o", "json"],
            timeout=10, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        try:
            subprocess.check_output(
                [KRAKEN_CLI_PATH, "futures", "paper", "init", "--balance", "10000", "-o", "json"],
                timeout=10
            )
            logger.info("[paper] paper account initialised with $10,000")
        except Exception as e:
            logger.error(f"[paper] init failed: {e}")

class BaseStrategy(ABC):

    def skip(self, symbol: str, reason: str, confidence: float = 0.0, post_on_chain: bool = False) -> dict:
        if post_on_chain and not KRAKEN_PAPER_MODE:
            try:
                post_skip_checkpoint(pair=symbol, reason=reason, confidence=confidence)
                logger.info(f"[{symbol}] SKIP posted on-chain: {reason}")
            except Exception as e:
                logger.error(f"[{symbol}] SKIP checkpoint failed: {e}")

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

    def _exec(self, side: str, pair: str, volume: str, leverage: float, order_type: str = "market") -> dict:
        pair = _pf(pair)

        if KRAKEN_PAPER_MODE:
            _ensure_paper_init()
            base = [KRAKEN_CLI_PATH, "futures", "paper"]
        else:
            base = [KRAKEN_CLI_PATH, "futures", "order"]

        cmd = base + [
            side,
            pair,
            volume,
            "--leverage", str(leverage),
            "--type", order_type,
            "-o", "json"
        ]

        raw = subprocess.check_output(cmd, timeout=15, stderr=subprocess.DEVNULL)
        return json.loads(raw)

    def open_position(self, decision: dict, price: float, reputation: float = 0.0, order_type: str = "market") -> dict:
        pair     = decision["symbol"]
        action   = decision["action"]
        risk_pct = decision["risk_pct"]
        leverage = decision["leverage"]

        from contracts.vault import get_available_capital
        available = get_available_capital()
        amount    = round((available * risk_pct / 100) * leverage, 2)
        volume    = str(round(amount / price, 6))

        if not KRAKEN_PAPER_MODE:
            result = submit_trade_intent(pair, action, amount)
            if not result["approved"]:
                logger.warning(f"[{pair}] TradeIntent rejected: {result.get('reason')}")
                return {"executed": False, "reason": result.get("reason")}
            intent_hash = result["intent_hash"]
        else:
            result = {"intent_hash": "PAPER_MODE"}
            intent_hash = "PAPER_MODE"

        side = "buy" if action == "LONG" else "sell"

        try:
            order = self._exec(side, pair, volume, leverage, order_type)
            logger.info(f"[{pair}] {'[PAPER] ' if KRAKEN_PAPER_MODE else ''}order placed: {order}")

            if not KRAKEN_PAPER_MODE:
                cp = post_checkpoint(
                    action=action,
                    pair=pair,
                    amount_usd=amount,
                    price=price,
                    reasoning=decision["explanation"],
                    confidence=decision["regime"]["confidence"],
                    intent_hash=intent_hash,
                )
                checkpoint_hash = cp["checkpoint_hash"]
            else:
                cp = "PAPER_MODE"
                checkpoint_hash = "PAPER_MODE"

            _write_pending_outcome(
                intent_hash=intent_hash,
                pair=_pf(pair),
                action=action,
                entry_price=price,
                amount_usd=amount,
                confidence=decision["regime"]["confidence"],
                reputation_at_entry=reputation,
                checkpoint_hash=checkpoint_hash,
            )

            return {
                "executed":   True,
                "order":      order,
                "intent_hash": intent_hash,
                "checkpoint": cp,
            }

        except subprocess.CalledProcessError as e:
            err = e.output.decode() if e.output else str(e)
            logger.error(f"[{pair}] order failed: {err}")
            return {"executed": False, "reason": err}
        except Exception as e:
            logger.error(f"[{pair}] order failed: {e}")
            return {"executed": False, "reason": str(e)}

    def close_position(self, symbol: str, volume: str, order_type: str = "market") -> dict:
        pair = _pf(symbol)
        side = "sell"

        try:
            order = self._exec(side, pair, volume, 1, order_type)
            logger.info(f"[{symbol}] {'[PAPER] ' if KRAKEN_PAPER_MODE else ''}position closed: {order}")
            return {"closed": True, "order": order}
        except Exception as e:
            logger.error(f"[{symbol}] close failed: {e}")
            return {"closed": False, "reason": str(e)}

    def get_open_orders(self) -> dict:
        try:
            if KRAKEN_PAPER_MODE:
                cmd = [KRAKEN_CLI_PATH, "futures", "paper", "orders", "-o", "json"]
            else:
                cmd = [KRAKEN_CLI_PATH, "futures", "open-orders", "-o", "json"]

            raw = subprocess.check_output(cmd, timeout=15, stderr=subprocess.DEVNULL)
            return json.loads(raw)
        except Exception as e:
            logger.error(f"get_open_orders failed: {e}")
            return {}

    def get_paper_status(self) -> dict:
        if not KRAKEN_PAPER_MODE:
            return {}
        try:
            raw = subprocess.check_output(
                [KRAKEN_CLI_PATH, "futures", "paper", "status", "-o", "json"],
                timeout=10, stderr=subprocess.DEVNULL,
            )
            return json.loads(raw)
        except Exception as e:
            logger.error(f"get_paper_status failed: {e}")
            return {}