import pytest
from unittest.mock import patch, AsyncMock, MagicMock


def _mock_pool(rows):
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[
        {"status": r[0], "confidence_at_entry": r[1]} for r in rows
    ])
    mock_pool = AsyncMock()
    mock_pool.acquire = MagicMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=mock_conn),
        __aexit__=AsyncMock(return_value=False),
    ))
    return mock_pool


@pytest.mark.asyncio
@patch("agent.reputation.get_pool")
async def test_returns_zero_when_not_enough_trades(mock_get_pool):
    mock_get_pool.return_value = _mock_pool([("WIN", 0.7), ("LOSS", 0.6)])
    from agent.reputation import get_reputation_score
    score = await get_reputation_score()
    assert score == 0.0


@pytest.mark.asyncio
@patch("agent.reputation.get_pool")
async def test_perfect_win_rate_scores_high(mock_get_pool):
    mock_get_pool.return_value = _mock_pool([("WIN", 0.7)] * 20)
    from agent.reputation import get_reputation_score
    score = await get_reputation_score()
    assert score > 0.7


@pytest.mark.asyncio
@patch("agent.reputation.get_pool")
async def test_all_losses_scores_low(mock_get_pool):
    mock_get_pool.return_value = _mock_pool([("LOSS", 0.7)] * 20)
    from agent.reputation import get_reputation_score
    score = await get_reputation_score()
    assert score < 0.3


@pytest.mark.asyncio
@patch("agent.reputation.get_pool")
async def test_score_between_zero_and_one(mock_get_pool):
    rows = [("WIN", 0.65), ("LOSS", 0.55), ("WIN", 0.7),
            ("NEUTRAL", 0.5), ("WIN", 0.8)] * 4
    mock_get_pool.return_value = _mock_pool(rows)
    from agent.reputation import get_reputation_score
    score = await get_reputation_score()
    assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
@patch("agent.reputation.get_pool")
async def test_win_streak_adds_bonus(mock_get_pool):
    from agent.reputation import get_reputation_score

    mock_get_pool.return_value = _mock_pool([("WIN", 0.7)] * 10 + [("LOSS", 0.6)] * 5)
    score_streak = await get_reputation_score()

    mock_get_pool.return_value = _mock_pool([("WIN", 0.7), ("LOSS", 0.6)] * 7 + [("WIN", 0.7)])
    score_no_streak = await get_reputation_score()

    assert score_streak >= score_no_streak


@pytest.mark.asyncio
@patch("agent.reputation.get_pool")
async def test_neutral_outcomes_dont_crash(mock_get_pool):
    mock_get_pool.return_value = _mock_pool([("NEUTRAL", 0.5)] * 20)
    from agent.reputation import get_reputation_score
    score = await get_reputation_score()
    assert isinstance(score, float)