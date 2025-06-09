# Optiver-Hackathon-TUM
The challenge was the following: create an market-making (MM) algorithm, but also incorporate a newsfeed using an LLM and based on the news go directional instead of market neutral.
In general, we split the whole logic such that we update it separately for each stock (there were 5 different stocks).

## Market making strategy
I created an MM strategy similar to Guilbaud-Pham.



## News strategy
We used the provived LLM, and did sentiment analysis. If we thought it is good news for the stock, we went long max position size; with bad news, we went short max position size. That was the basic idea of our directional trading.


## When to enter/exit directional trading and how
