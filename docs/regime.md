# Regime Detection

## The Core Idea

Most regime detection fails because it tries to explicitly define what a regime is. You write rules — VIX above X, price below its 200-day, volatility exceeds some threshold — and the market finds a way to invalidate them. The rules overfit to historical patterns that don't repeat cleanly. You end up with a system that's always one regime behind reality.

The approach here is different. Instead of detecting regime and then deciding whether to trade, we let the model's own uncertainty do the work. We train an LSTM on a wide set of market features and ask it to predict forward returns. The output is a confidence score between 0 and 1. When the market is trending cleanly with participation behind it, the model is confident. When conditions are chaotic, fragmented, or contradictory, confidence collapses naturally — not because we told it to, but because the features genuinely stop agreeing with each other. That collapsed confidence is your regime filter. You don't trade below a threshold. Position size scales with the score above it.

This matters because regime is not a binary state. It's a spectrum, and it changes gradually. A hard switch between "bull" and "bear" creates whipsawing. A continuous confidence score lets you scale exposure smoothly as conditions deteriorate or improve.

---

## Why LSTM

Market data is a sequence. What happened in the last 4 hours affects how you should interpret what's happening now. A model that looks at each bar in isolation throws away that context entirely.

LSTMs are built for sequences. They maintain a hidden state across time steps, which means the model can learn that a funding rate spike following a period of low volatility means something different from the same spike in the middle of an already-chaotic session. That temporal context is where the real signal lives.

The window we use — 96 bars of 15-minute data — covers 24 hours. That's enough to capture a full intraday cycle, see how a move developed, whether volume confirmed it, whether order flow was aligned. It's not so long that you're feeding the model ancient history that dilutes the current signal.

The output is a single scalar — the predicted forward return, rescaled to 0–1. We use that as a proxy for confidence. High predicted return with high certainty = model sees a real move. Low or uncertain prediction = model is confused = you don't trade.

---

## The Features and Why Each One Is There

**Price structure** — log returns, EMA distances, realized volatility, ATR. These capture where price is relative to its own history and how violently it's moving. Realized vol specifically tells you whether current movement is normal or anomalous for this instrument.

**CVD (Cumulative Volume Delta)** — the difference between buyer-initiated and seller-initiated volume, accumulated over time. This is the most important order flow feature. Price can move up on weak buying — institutions distributing into retail momentum. CVD exposes that. If price is rising but CVD is flat or falling, the move has no real participation. The model learns this divergence as a signal to distrust the trend.

**Funding rate** — in perpetual futures, funding is paid between longs and shorts every 8 hours. When funding is deeply positive, the market is heavily long and paying to stay long. That's a crowding signal. Extremes in either direction don't predict direction reliably, but they do predict instability. The model learns that extreme funding correlates with sharp reversals and choppy conditions.

**Open interest** — the total number of open contracts. OI expanding during a move means new money is entering, confirming the trend. OI collapsing means positions are closing — the move is ending or reversing. OI change is one of the cleanest confirmation signals in crypto because it directly measures whether traders are committing capital to the direction.

**Liquidations** — forced closures of leveraged positions. Large liquidation clusters are both a leading and lagging signal. A cascade of long liquidations creates forced selling that accelerates a move. But after a large liquidation sweep, the overleveraged positions are gone and the market often stabilizes or reverses. The model sees the ratio of long vs short liquidations and learns what each configuration typically precedes.

---

## What the Model Is Actually Learning

The model is not learning "this is a bull market." It's learning the statistical relationships between these features across time and what they predict about the next bar's return. Implicitly, it learns:

- When CVD, OI expansion, and funding are aligned, returns are more predictable
- When liquidations are spiking and funding is extreme, returns become noisy and hard to predict
- When price is moving but volume delta doesn't confirm it, the move tends to fail

None of this is hard-coded. It emerges from training on two years of data across multiple symbols. The model generalizes across BTC, ETH, SOL because the underlying market mechanics — how funding, OI, and CVD interact — are consistent even when the price action looks different.

---

## Training and Labeling

The label for each sequence is the forward return of the next bar, rescaled to a 0–1 range. This is a regression target, not a classification. We're not asking the model to predict buy or sell. We're asking it to predict how much return potential exists in the current configuration of features.

Training on multiple symbols simultaneously is important. It prevents the model from overfitting to BTC-specific patterns and forces it to learn mechanics that generalize. A model trained only on BTC will fail on SOL during a period where BTC is ranging but SOL is trending independently.

We use 85% of data for training and hold 15% for validation, monitoring validation loss to save the best checkpoint and avoid overfitting. Gradient clipping is applied during training to prevent the LSTM's hidden state from exploding, which is a known failure mode on volatile financial time series.

---

## Limitations

**The label is imperfect.** Forward return is a noisy proxy for "good trading conditions." A sequence where the model is confident and the next bar returns nothing might still be a legitimate signal that took longer to play out. The model doesn't know about multi-bar moves during training. This is a fundamental limitation of single-step regression on financial data.

**It requires retraining.** Market structure changes. The relationship between funding and price behavior in 2022 is not identical to 2024. A model trained and never updated will degrade. Periodic retraining — monthly or quarterly — is necessary to keep it calibrated.

**CVD from kline data is approximate.** True CVD requires tick-level trade data with side classification. The taker buy volume from Binance klines is a reasonable approximation but it's aggregated at the bar level and loses intrabar sequence information. Proper tick-level CVD would be stronger but requires significantly more storage and processing.

**Liquidation data has coverage gaps.** Binance only exposes recent liquidation orders via REST. The historical liquidation data available for training is limited, which means this feature is weaker during training than it will be in live inference where you have a continuous stream. The model compensates by not over-weighting it, but it means the liquidation signal is underrepresented in learned weights relative to its true predictive value.

**Confidence score is not calibrated probability.** A score of 0.7 does not mean there is a 70% chance the trade succeeds. It means the model's output neuron fired at 0.7 given the input. Treat it as a relative signal for position sizing, not an absolute probability. Calibration requires additional post-processing that is not currently implemented.

**No cross-asset context.** The model sees each symbol in isolation. In reality, BTC dominance shifts, ETH/BTC ratio, and macro crypto sentiment affect individual symbols. A more complete model would incorporate cross-asset features. This is a meaningful gap that limits performance during macro regime shifts where correlations spike.