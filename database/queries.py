from database.connection import get_connection


def get_or_create_user(google_id, email, username, avatar_url):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE google_id = %s", (google_id,))
            user = cur.fetchone()
            if user:
                return user
            cur.execute("""
                INSERT INTO users (google_id, email, username, avatar_url)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            """, (google_id, email, username, avatar_url))
            conn.commit()
            return cur.fetchone()


def create_session(user_id, token, expires_at):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                RETURNING *
            """, (user_id, token, expires_at))
            conn.commit()
            return cur.fetchone()


def get_session(token):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.*, u.* FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = %s AND s.expires_at > NOW()
            """, (token,))
            return cur.fetchone()


def delete_session(token):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE token = %s", (token,))
            conn.commit()


def upsert_user_profile(user_id, discord_id=None, telegram_id=None, wallet_address=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
            profile = cur.fetchone()
            if profile:
                cur.execute("""
                    UPDATE user_profiles
                    SET discord_id = COALESCE(%s, discord_id),
                        telegram_id = COALESCE(%s, telegram_id)
                    WHERE user_id = %s
                    RETURNING *
                """, (discord_id, telegram_id, user_id))
            else:
                cur.execute("""
                    INSERT INTO user_profiles (user_id, discord_id, telegram_id)
                    VALUES (%s, %s, %s)
                    RETURNING *
                """, (user_id, discord_id, telegram_id))
            conn.commit()
            return cur.fetchone()


def insert_snapshot(agent_id, symbol, regime, signal, confidence, atr, trend_strength, price_at_signal, raw):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO snapshots (agent_id, symbol, regime, signal, confidence, atr, trend_strength, price_at_signal, raw)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (agent_id, symbol, regime, signal, confidence, atr, trend_strength, price_at_signal, raw))
            conn.commit()
            return cur.fetchone()["id"]


def insert_trade(agent_id, snapshot_id, symbol, side, amount, price):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO trades (agent_id, snapshot_id, symbol, side, amount, price)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (agent_id, snapshot_id, symbol, side, amount, price))
            conn.commit()
            return cur.fetchone()["id"]


def update_trade(trade_id, status, tx_hash=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE trades SET status = %s, tx_hash = %s WHERE id = %s
            """, (status, tx_hash, trade_id))
            conn.commit()


def insert_signal(agent_id, symbol, source, action, confidence, raw):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO signals (agent_id, symbol, source, action, confidence, raw)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (agent_id, symbol, source, action, confidence, raw))
            conn.commit()


def upsert_position(agent_id, symbol, quantity, avg_price):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM positions WHERE agent_id = %s AND symbol = %s", (agent_id, symbol))
            position = cur.fetchone()
            if position:
                cur.execute("""
                    UPDATE positions SET quantity = %s, avg_price = %s, updated_at = NOW()
                    WHERE agent_id = %s AND symbol = %s
                """, (quantity, avg_price, agent_id, symbol))
            else:
                cur.execute("""
                    INSERT INTO positions (agent_id, symbol, quantity, avg_price)
                    VALUES (%s, %s, %s, %s)
                """, (agent_id, symbol, quantity, avg_price))
            conn.commit()


def insert_log(user_id, agent_id, message, metadata=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO logs (user_id, agent_id, message, metadata)
                VALUES (%s, %s, %s, %s)
            """, (user_id, agent_id, message, metadata))
            conn.commit()


def get_trades(agent_id, limit=50):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.*, s.regime, s.signal, s.confidence, s.atr, s.trend_strength, s.price_at_signal, s.raw
                FROM trades t
                LEFT JOIN snapshots s ON t.snapshot_id = s.id
                WHERE t.agent_id = %s
                ORDER BY t.created_at DESC
                LIMIT %s
            """, (agent_id, limit))
            return cur.fetchall()


def get_positions(agent_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM positions WHERE agent_id = %s", (agent_id,))
            return cur.fetchall()