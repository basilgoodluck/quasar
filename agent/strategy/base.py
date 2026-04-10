import asyncio
import json
import time
from abc import ABC, abstractmethod
from contracts.router import submit_trade_intent
from contracts.validation import post_checkpoint, post_skip_checkpoint
from database.connection import get_pool
from config import KRAKEN_CLI_PATH, KRAKEN_PAPER_MODE
from logger import get_logger

logger = get_logger(__name__)

def _pf(symbol: str) -> str:
    base = symbol.replace("USDT", "")
    base = "XBT" if base == "BTC" else base
    return f"PF_{base}USD"


async def _write_pending_outcome(
    intent_hash: str,
    pair: str,
    action: str,
    entry_price: float,
    amount_usd: float,
    confidence: float,
    reputation_at_entry: float,
    checkpoint_hash: str,
):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO trade_outcomes
                (intent_hash, pair, action, entry_price, amount_usd,
                 confidence_at_entry, reputation_at_entry, checkpoint_hash,
                 status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'PENDING', $9)
            ON CONFLICT (intent_hash) DO NOTHING
        """,
            intent_hash, pair, action, entry_price, amount_usd,
            confidence, reputation_at_entry, checkpoint_hash,
            int(time.time()),
        )


async def _ensure_paper_init():
    try:
        proc = await asyncio.create_subprocess_exec(
            KRAKEN_CLI_PATH, "futures", "paper", "status", "-o", "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"status check failed: {stderr.decode()}")
    except Exception as e:
        logger.warning(f"[paper] status check failed, attempting init: {e}")
        try:
            proc = await asyncio.create_subprocess_exec(
                KRAKEN_CLI_PATH, "futures", "paper", "init", "--balance", "10000", "-o", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.error(f"[paper] init failed stdout={stdout.decode()} stderr={stderr.decode()}")
            else:
                logger.info("[paper] paper account initialised with $10,000")
        except Exception as e:
            logger.error(f"[paper] init failed: {e}")


class BaseStrategy(ABC):

    def skip(self, symbol: str, reason: str, confidence: float = 0.0, post_on_chain: bool = False) -> dict:
        if post_on_chain and not KRAKEN_PAPER_MODE:
            try:
                post_skip_checkpoint(pair=symbol, reason=reason, confidence=confidence)
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
    async def analyze(self, symbol: str) -> dict:
        ...

    async def _exec(self, side: str, pair: str, volume: str, leverage: float, order_type: str = "market", price: float | None = None) -> dict:
        pair = _pf(pair)

        if KRAKEN_PAPER_MODE:
            await _ensure_paper_init()
            cmd = [KRAKEN_CLI_PATH, "futures", "paper", side, pair, volume, "--leverage", str(leverage), "--type", order_type, "-o", "json"]
            if price is not None:
                cmd += ["--price", str(price)]
        else:
            cmd = [KRAKEN_CLI_PATH, "futures", "order", side, pair, volume, "--leverage", str(leverage), "--type", order_type, "-o", "json"]
            if price is not None:
                cmd += ["--price", str(price)]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise Exception(f"stdout={stdout.decode()} stderr={stderr.decode()}")

        return json.loads(stdout)

    async def open_position(self, decision: dict, price: float, reputation: float = 0.0, order_type: str = "market") -> dict:
        pair     = decision["symbol"]
        action   = decision["action"]
        leverage = decision["leverage"]

        amount = decision["amount_usd"]  # FIX: use pre-computed amount from compute_risk
        volume = str(round(amount / price, 6))

        if not KRAKEN_PAPER_MODE:
            loop   = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, submit_trade_intent, pair, action, amount)
            if not result["approved"]:
                logger.warning(f"[{pair}] TradeIntent rejected: {result.get('reason')}")
                return {"executed": False, "reason": result.get("reason")}
            intent_hash = result["intent_hash"]
        else:
            result      = {"intent_hash": "PAPER_MODE"}
            intent_hash = "PAPER_MODE"

        side = "buy" if action == "LONG" else "sell"

        try:
            limit_price = price if order_type != "market" else None
            order = await self._exec(side, pair, volume, leverage, order_type, price=limit_price)
            logger.info(f"[{pair}] {'[PAPER] ' if KRAKEN_PAPER_MODE else ''}order placed: {order}")

            if not KRAKEN_PAPER_MODE:
                loop = asyncio.get_event_loop()
                try:
                    cp = await loop.run_in_executor(None, lambda: post_checkpoint(
                        action=action,
                        pair=pair,
                        amount_usd=amount,
                        price=price,
                        reasoning=decision["explanation"],
                        confidence=decision["regime"]["confidence"],
                        intent_hash=intent_hash,
                    ))
                    checkpoint_hash = cp["checkpoint_hash"]
                except Exception as e:
                    logger.error(f"[{pair}] checkpoint failed: {e}")
                    checkpoint_hash = "FAILED"
            else:
                cp              = "PAPER_MODE"
                checkpoint_hash = "PAPER_MODE"

            await _write_pending_outcome(
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
                "executed":    True,
                "order":       order,
                "intent_hash": intent_hash,
                "checkpoint":  cp,
            }

        except Exception as e:
            err = str(e)
            logger.error(f"[{pair}] order failed: {err}")
            return {"executed": False, "reason": err}

    async def close_position(self, symbol: str, volume: str, order_type: str = "market") -> dict:
        pair = _pf(symbol)
        try:
            order = await self._exec("sell", pair, volume, 1, order_type)
            logger.info(f"[{symbol}] {'[PAPER] ' if KRAKEN_PAPER_MODE else ''}position closed: {order}")
            return {"closed": True, "order": order}
        except Exception as e:
            logger.error(f"[{symbol}] close failed: {e}")
            return {"closed": False, "reason": str(e)}

    async def get_open_orders(self) -> dict:
        try:
            if KRAKEN_PAPER_MODE:
                cmd = [KRAKEN_CLI_PATH, "futures", "paper", "orders", "-o", "json"]
            else:
                cmd = [KRAKEN_CLI_PATH, "futures", "open-orders", "-o", "json"]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if not stdout:
                logger.error(f"get_open_orders failed stderr={stderr.decode()}")
                return {}
            return json.loads(stdout)
        except Exception as e:
            logger.error(f"get_open_orders failed: {e}")
            return {}

    async def get_paper_status(self) -> dict:
        if not KRAKEN_PAPER_MODE:
            return {}
        try:
            proc = await asyncio.create_subprocess_exec(
                KRAKEN_CLI_PATH, "futures", "paper", "status", "-o", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if not stdout:
                logger.error(f"get_paper_status failed stderr={stderr.decode()}")
                return {}
            return json.loads(stdout)
        except Exception as e:
            logger.error(f"get_paper_status failed: {e}")
            return {}