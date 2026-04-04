from unittest.mock import patch, MagicMock


def _mock_outcomes(rows):
    mock_conn  = MagicMock()
    mock_cur   = MagicMock()
    mock_cur.fetchall.return_value = rows
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__  = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__  = MagicMock(return_value=False)
    return mock_conn


@patch("agent.reputation.get_connection")
def test_returns_zero_when_not_enough_trades(mock_get_conn):
    mock_get_conn.return_value = _mock_outcomes([("WIN", 0.7), ("LOSS", 0.6)])
    from agent.reputation import get_reputation_score
    score = get_reputation_score()
    assert score == 0.0


@patch("agent.reputation.get_connection")
def test_perfect_win_rate_scores_high(mock_get_conn):
    rows = [("WIN", 0.7)] * 20
    mock_get_conn.return_value = _mock_outcomes(rows)
    from agent.reputation import get_reputation_score
    score = get_reputation_score()
    assert score > 0.7


@patch("agent.reputation.get_connection")
def test_all_losses_scores_low(mock_get_conn):
    rows = [("LOSS", 0.7)] * 20
    mock_get_conn.return_value = _mock_outcomes(rows)
    from agent.reputation import get_reputation_score
    score = get_reputation_score()
    assert score < 0.3


@patch("agent.reputation.get_connection")
def test_score_between_zero_and_one(mock_get_conn):
    rows = [("WIN", 0.65), ("LOSS", 0.55), ("WIN", 0.7),
            ("NEUTRAL", 0.5), ("WIN", 0.8)] * 4
    mock_get_conn.return_value = _mock_outcomes(rows)
    from agent.reputation import get_reputation_score
    score = get_reputation_score()
    assert 0.0 <= score <= 1.0


@patch("agent.reputation.get_connection")
def test_win_streak_adds_bonus(mock_get_conn):
    rows_streak   = [("WIN", 0.7)] * 10 + [("LOSS", 0.6)] * 5
    rows_no_streak = [("WIN", 0.7), ("LOSS", 0.6)] * 7 + [("WIN", 0.7)]
    mock_get_conn.return_value = _mock_outcomes(rows_streak)
    from agent.reputation import get_reputation_score
    score_streak = get_reputation_score()
    mock_get_conn.return_value = _mock_outcomes(rows_no_streak)
    score_no_streak = get_reputation_score()
    assert score_streak >= score_no_streak


@patch("agent.reputation.get_connection")
def test_neutral_outcomes_dont_crash(mock_get_conn):
    rows = [("NEUTRAL", 0.5)] * 20
    mock_get_conn.return_value = _mock_outcomes(rows)
    from agent.reputation import get_reputation_score
    score = get_reputation_score()
    assert isinstance(score, float)
