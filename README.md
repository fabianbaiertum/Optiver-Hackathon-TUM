# Optiver-Hackathon-TUM
The challenge was the following: create an market-making (MM) algorithm, but also incorporate a newsfeed using an LLM and based on the news, go directional instead of market neutral.
In general, we split the whole logic such that we update it separately for each stock (there were 5 different stocks). 
The competition assumed that the assets are close to be uncorrelated.
We only had around 4 hours of time (my team only 3 hours because we took the subway to one of our team members' homes).


## Market making strategy
I created an MM strategy similar to Guilbaud-Pham or Avellaneda & Stoikov frameworks. It has the following steps:

1. Use the microprice or a forecast of the microprice as the theoretical asset price
2. Introduce a base spread, such that ask=microprice+base_spread/2 to avoid a too tight spread in low volatile markets, for the bid=microprice-base_spread/2
3. Next, if the volatility is high, we want to quote a wider spread, and if it is low, we want to quote a tighter spread, thus: ask=microprice+base_spread/2+volatility, bid=microprice-base_spread/2-volatility
4. To account for the supply/demand we use the order imbalance
5. To avoid adverse selection (or price movements against our position we are holding), I introduce the inventory risk factor
   
Remarks: I scaled every of the components, such that it is easily adjustable in a trading competition without the need to find optimal parameters!
I used safety guards, such that bid-ask prices stay in a bounded area around the theoretical value. 
It was highly optimized for the Optibook and simplified compared to my MM strategy for IMC trading, because there wasn't any time or data set to backtest and optimize parameters. But compared to the IMC trading, 
I came up with new, elegant ways, on how to calculate and scale the parameters. I also included inventory risk this time.



## News strategy
We used the provived LLM, and did sentiment analysis. If we thought it is good news for the stock, we went long max position size; with bad news, we went short max position size. That was the basic idea of our directional trading.


## When to enter/exit directional trading and how
### Enter
The basic idea was to stop market making in the particular asset as soon as we got news and did the sentiment analysis of the news.
Then, if we hold any inventory of that asset, there are two options (for each of the two scenarios, but I only present one; the other is just the opposite logic):
1. If we bought the asset and we predict with the sentiment that the price of the asset will go up: we keep the amount of shares we have, and additionally buy the maximum amount of positions allowed for a price a little bit higher than the previous best ask (we could only sent IOC orders in that competition, thus in this scenario at best_ask+1 for example). (We can also keep the best_bid of our MM strategy in the market, for a second or so)
  
2. If we are short in the asset, but we predict that the price will go up: we go long with -current_position+position_limit

### Exit
For exiting the directional trading the idea is, as soon as the market incorporated the news, the market will get back into a mean reverting regime (checked this via plotting). 
After plotting the average price behavior after news events, I realized, that it is close to a straight line, indicating the market is going up. Thus, it made sense to use the z-score of the microprice to analyse 
when the directional movement is over. It was the case as soon as the z-score flipped its sign; then I returned to the MM algorithm.
