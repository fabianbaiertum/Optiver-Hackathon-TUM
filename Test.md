# Optiver Hackathon @ TUM

In June 2025, my team achieved **1st place in PnL out of 70+ teams** at the Optiver Hackathon at TUM.

The challenge was to build a trading algorithm on **Optiver’s Optibook** that combined classical **market making** with a **news-driven directional overlay**.  
The market-making component aimed to remain close to market-neutral, while the news component used an LLM-based sentiment feed to take directional positions when stock-specific information arrived.

Our strategy only ran for around **15 out of 20 minutes** during the final round, yet still achieved the highest PnL.  
This write-up is intentionally simplified and focuses on the **quantitative and engineering aspects** of my contribution.

I was responsible for designing and implementing the **core trading logic**, including:

- Market-making strategy
- Signal design
- Parameter scaling
- Inventory risk logic
- News-driven directional trading logic
- Strategy parameter optimization

My teammate adapted the API to Optibook, integrated multithreading, and added safeguards to ensure that we respected exchange constraints such as order-rate and quote-update limits.

---

## The challenge

The competition ran on **Optiver’s Optibook**, a simulated exchange where we traded against bots and other participant teams.

- Universe: **5 stocks**
- Objective: maximize **PnL**
- Assets were assumed to be approximately **uncorrelated**
- News events could affect individual stocks
- Only **IOC orders** were available for aggressive execution
- The system had practical microstructure constraints, including limits on order submissions and quote updates

The main strategic challenge was to combine two different regimes:

1. **Market-neutral market making** during normal periods
2. **Directional trading** after stock-specific news events

Since we had very limited development time during the event, the strategy had to be robust, interpretable, and easy to tune without extensive backtesting.

---

## Strategy overview

For each stock, the algorithm maintained a separate trading logic.  
This was natural because the competition setup assumed that the five assets were approximately uncorrelated.

The strategy consisted of two main components:

1. **Microstructure-based market making**
2. **LLM-based news sentiment trading**

During normal periods, the algorithm continuously quoted bid and ask prices around a theoretical value.  
When relevant news arrived for a stock, the algorithm temporarily stopped market making in that asset and switched into a directional execution mode.

---

## Market making with microstructure signals

The market-making strategy was inspired by classical market-making frameworks such as **Avellaneda–Stoikov** and **Guilbaud–Pham**, but simplified and adapted to the competition setting.

The goal was not to implement a fully theoretical optimal-control model, but to build a practical quoting engine whose behavior could be controlled with a small number of interpretable parameters.

For each stock, the strategy computed theoretical bid and ask levels using:

- Microprice
- Base spread
- Short-term volatility
- Order book imbalance
- Inventory risk
- Safety bounds around the theoretical value

---

## Pricing module

### 1. Theoretical price

The starting point was the **microprice**, or a short-term forecast of the microprice.

The microprice was useful because it incorporates top-of-book liquidity and therefore reacts faster than the midprice when one side of the book becomes weak.

This theoretical value formed the center of the quoting logic.

---

### 2. Base spread

To avoid quoting too tightly in quiet markets, I introduced a base spread around the theoretical price:

```text
ask = theoretical_price + base_spread / 2
bid = theoretical_price - base_spread / 2
```

This ensured that the strategy did not provide liquidity at an unattractive spread when there was little immediate signal.

---

### 3. Volatility adjustment

The spread was widened when short-term volatility increased:

```text
ask = theoretical_price + base_spread / 2 + volatility_adjustment
bid = theoretical_price - base_spread / 2 - volatility_adjustment
```

The intuition was simple:

- In low-volatility regimes, tighter quotes improve fill probability.
- In high-volatility regimes, wider quotes reduce adverse selection.

This made the market maker more defensive when prices were moving quickly.

---

### 4. Order book imbalance

To account for short-term supply and demand, I used **order book imbalance** as a directional skew.

If the bid side was much stronger than the ask side, the theoretical price was shifted upward.  
If the ask side was stronger, it was shifted downward.

A key part of the implementation was the scaling.  
Instead of allowing imbalance to move quotes by an uncontrolled amount, I scaled it so that its maximum influence was bounded by a multiple of the tick size:

```text
imbalance_adjustment ∈ [-parameter * tick_size, parameter * tick_size]
```

This gave direct control over how aggressively the market maker reacted to imbalance.

---

### 5. Inventory risk

I also added an inventory-risk adjustment to reduce exposure when the strategy accumulated a large position.

The inventory signal was scaled using a `tanh` transformation.  
This had two advantages:

1. Small positions produced approximately linear quote adjustments.
2. Large positions saturated smoothly instead of causing unstable quote shifts.

The resulting behavior was:

- If inventory was too long, quotes were skewed downward to encourage selling and discourage further buying.
- If inventory was too short, quotes were skewed upward to encourage buying and discourage further selling.

This made the market maker more robust than a purely symmetric quoting strategy.

---

## Parameter scaling

A major focus of my implementation was making the strategy easy to tune under time pressure.

Instead of introducing many sensitive parameters, I designed each signal so that it had a clear and bounded effect on the final bid and ask prices.

Examples:

- Order imbalance could move quotes by at most a chosen number of ticks.
- Inventory risk was smoothly bounded using `tanh`.
- Volatility widened the spread but did not move quotes outside predefined safety bounds.
- Final bid and ask prices were constrained to remain within a bounded region around the theoretical value.

This allowed us to adjust the behavior of the algorithm using only a few interpretable parameter values, which was important because there was no time for large-scale backtesting during the hackathon.

---

## News-driven directional trading

The second component was a directional trading strategy based on the provided news feed and LLM sentiment analysis.

When a news item arrived, the LLM was used to classify:

- The affected stock
- Whether the news was positive, negative, or neutral
- Whether the signal was strong enough to justify directional trading

If the news was positive for a stock, the strategy aimed to build a long position.  
If the news was negative, it aimed to build a short position.

For strong signals, the strategy targeted the maximum allowed directional exposure.

---

## Entering directional mode

When relevant news arrived for a stock, the algorithm stopped normal market making in that asset and switched into directional execution.

For example, if the news was positive:

1. If we were already long, we kept the existing position and bought additional volume up to the position limit.
2. If we were short, we first neutralized the short exposure and then built a long position.
3. Since only IOC orders were available, we executed aggressively by crossing the spread, for example buying slightly above the current best ask.

The opposite logic was used for negative news.

The important idea was that news events created a temporary directional regime.  
During that regime, passive market making was less attractive because it could leave us providing liquidity on the wrong side of an informed price move.

---

## Exiting directional mode

To decide when to exit directional trading, I analyzed the average price behavior after news events.

Empirically, price reactions after news were close to directional moves followed by a return to a more mean-reverting regime.  
To detect when the directional move had likely faded, I used a **z-score of the microprice**.

The basic exit condition was:

- Stay in directional mode while the microprice continued to move in the predicted direction.
- Exit once the z-score flipped sign, indicating that the directional pressure had likely weakened or reversed.
- After exiting, return the asset to the normal market-making strategy.

This gave the strategy a simple regime-switching structure:

```text
normal market making
        ↓
news event + sentiment signal
        ↓
directional execution
        ↓
microprice z-score reversal
        ↓
return to market making
```

---

## Execution considerations

The strategy was specifically adapted to the Optibook setting, where we traded against other teams as well as bots.

This affected the execution logic.  
Compared to my earlier IMC Prosperity market-making strategy, I simplified the model but made it more practical for a live competition environment.

Important execution considerations included:

- Avoiding overly tight quotes that would be adversely selected
- Adjusting quotes based on current inventory
- Crossing the spread aggressively only when news signals justified it
- Respecting order-rate and quote-update limits
- Keeping the strategy robust under limited runtime and limited calibration data

Because other participants were also competing for fills, getting execution priority mattered.  
The market-making parameters were therefore tuned not only for theoretical profitability, but also for practical fill behavior in Optibook.

---

## Result

Despite our strategy running for only around **15 of the 20 minutes** in the final round, we achieved the **highest PnL** and placed **1st out of 70+ teams**.

The result came from combining:

- A robust microprice-based market maker
- Carefully scaled microstructure signals
- Inventory-aware quote skewing
- Fast regime switching after news events
- Aggressive directional execution when sentiment signals were strong

The main edge was the combination of practical market-making logic with a simple but effective news-driven directional overlay.

---

## Code availability

The codebase contains:

- Market-making logic
- Microprice and order-imbalance signals
- Volatility-based spread adjustment
- Inventory-risk adjustment
- News sentiment integration
- Directional entry and exit logic
- Optibook-specific execution logic

The implementation was designed under severe time constraints and optimized for robustness, interpretability, and practical execution during the live competition.
