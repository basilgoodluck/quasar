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
        cmd = [KRAKEN_CLI_PATH, "paper", "status", "-o", "json"]
        subprocess.check_output(cmd, timeout=10, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        try:
            init_cmd = [KRAKEN_CLI_PATH, "paper", "init", "--balance", "10000", "-o", "json"]
            subprocess.check_output(init_cmd, timeout=10)
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

    def open_position(self, decision: dict, price: float, reputation: float = 0.0) -> dict:
        if KRAKEN_PAPER_MODE:
            return self._open_position_paper(decision, price, reputation)

        pair     = decision["symbol"]
        action   = decision["action"]
        risk_pct = decision["risk_pct"]
        leverage = decision["leverage"]

        from contracts.vault import get_available_capital
        available = get_available_capital()
        amount    = round((available * risk_pct / 100) * leverage, 2)
        volume    = str(round(amount / price, 6))

        result = submit_trade_intent(pair, action, amount)
        if not result["approved"]:
            logger.warning(f"[{pair}] TradeIntent rejected: {result.get('reason')}")
            return {"executed": False, "reason": result.get("reason")}

        kraken_side = "buy" if action == "LONG" else "sell"
        cmd = [KRAKEN_CLI_PATH, "order", kraken_side, pair, volume, "--type", "market", "-o", "json"]

        try:
            raw   = subprocess.check_output(cmd, timeout=15, stderr=subprocess.DEVNULL)
            order = json.loads(raw)
            logger.info(f"[{pair}] order placed: {order}")

            cp = post_checkpoint(
                action=action,
                pair=pair,
                amount_usd=amount,
                price=price,
                reasoning=decision["explanation"],
                confidence=decision["regime"]["confidence"],
                intent_hash=result["intent_hash"],
            )

            _write_pending_outcome(
                intent_hash=result["intent_hash"],
                pair=pair,
                action=action,
                entry_price=price,
                amount_usd=amount,
                confidence=decision["regime"]["confidence"],
                reputation_at_entry=reputation,
                checkpoint_hash=cp["checkpoint_hash"],
            )

            return {
                "executed":   True,
                "order":      order,
                "intent_hash": result["intent_hash"],
                "checkpoint": cp,
            }

        except subprocess.CalledProcessError as e:
            err = e.output.decode() if e.output else str(e)
            logger.error(f"[{pair}] Kraken order failed: {err}")
            return {"executed": False, "reason": err}
        except Exception as e:
            logger.error(f"[{pair}] Kraken order failed: {e}")
            return {"executed": False, "reason": str(e)}

    def _open_position_paper(self, decision: dict, price: float, reputation: float = 0.0) -> dict:
        pair     = decision["symbol"]
        action   = decision["action"]
        risk_pct = decision["risk_pct"]
        leverage = decision["leverage"]

        from contracts.vault import get_available_capital
        available = get_available_capital()
        amount    = round((available * risk_pct / 100) * leverage, 2)
        volume    = str(round(amount / price, 6))

        kraken_side = "buy" if action == "LONG" else "sell"
        _ensure_paper_init()
        cmd = [KRAKEN_CLI_PATH, "paper", kraken_side, pair, volume, "-o", "json"]

        try:
            raw   = subprocess.check_output(cmd, timeout=15, stderr=subprocess.DEVNULL)
            order = json.loads(raw)
            logger.info(f"[{pair}] [PAPER] order placed: {order}")

            _write_pending_outcome(
                intent_hash="PAPER_MODE",
                pair=pair,
                action=action,
                entry_price=price,
                amount_usd=amount,
                confidence=decision["regime"]["confidence"],
                reputation_at_entry=reputation,
                checkpoint_hash="PAPER_MODE",
            )

            return {
                "executed": True,
                "order": order,
                "intent_hash": "PAPER_MODE",
                "checkpoint": "PAPER_MODE",
            }

        except Exception as e:
            logger.error(f"[{pair}] PAPER order failed: {e}")
            return {"executed": False, "reason": str(e)}

    def close_position(self, symbol: str, volume: str) -> dict:
        if KRAKEN_PAPER_MODE:
            cmd = [KRAKEN_CLI_PATH, "paper", "sell", symbol, volume, "-o", "json"]
        else:
            cmd = [KRAKEN_CLI_PATH, "order", "sell", symbol, volume, "--type", "market", "-o", "json"]

        try:
            raw   = subprocess.check_output(cmd, timeout=15, stderr=subprocess.DEVNULL)
            order = json.loads(raw)
            logger.info(f"[{symbol}] {'[PAPER] ' if KRAKEN_PAPER_MODE else ''}position closed: {order}")
            return {"closed": True, "order": order}
        except Exception as e:
            logger.error(f"[{symbol}] close failed: {e}")
            return {"closed": False, "reason": str(e)}

    def get_open_orders(self) -> dict:
        if KRAKEN_PAPER_MODE:
            cmd = [KRAKEN_CLI_PATH, "paper", "orders", "-o", "json"]
        else:
            cmd = [KRAKEN_CLI_PATH, "open-orders", "-o", "json"]

        try:
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
                [KRAKEN_CLI_PATH, "paper", "status", "-o", "json"],
                timeout=10, stderr=subprocess.DEVNULL,
            )
            return json.loads(raw)
        except Exception as e:
            logger.error(f"get_paper_status failed: {e}")
            return {}