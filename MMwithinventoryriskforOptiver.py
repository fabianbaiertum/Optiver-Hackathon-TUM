import numpy as np
PARAMS={"Product.one":
    { "inventory_risk_factor": 1, #how many ticks to move, when at max position limit (e.g. 0,1,2 ticks)
      "history_window_size":5,  #for std calculation and spread history maybe
      "base_spread":0.1, #amount how large a half spread should be at least
      "volatility_factor": 5, #how many ticks the volatility affects the spread, if volatility is high! #TODO is not in tick size right now
      "imbalance_factor": 1,    #integer, how many ticks to move, when extreme order imbalance, we do linear scaling, up to a certain point!
      "max_tick_deviation": 3,  # NEW: maximum ticks allowed away from microprice
      "max_post_volume": 10  # NEW: maximum volume to post per side
},
        "Product.stat_arb":
            {
            "entry_parameter":1,
            "exit_parameter":0.1,
            "epsilon":0.1
        }

}
#TODO make history of microprices a fixed length to avoid slow computation
micro_price=9.9
current_position=00
position_limit=50
history_microprices=[10,10.2,10.1,10,10.1,9.9]
tick_size=0.1
bid_volume=5
ask_volume=20

def microprice(volume_ask,volume_bid,bid_price,ask_price):
    return (volume_bid*ask_price+volume_ask*bid_price)/(volume_ask+volume_bid)

### Stat arb for the example basket=2*component1+1*component2
def stat_arb_spread(microprice_basket,microprice_component1,microprice_component2):
    return microprice_basket-2*microprice_component1-microprice_component2
#stat arb strategy, need to have a list of the previous timesteps spreads! #TODO have to decide on the window size of spread history
def stat_arb_strategy(microprice_basket,microprice_component1,microprice_component2,product_data,spread_history):

    #entry
    if stat_arb_spread(microprice_basket,microprice_component1,microprice_component2)>product_data["entry_parameter"]*np.std(spread_history)+product_data["epsilon"]:
        return "short basket, buy components","case1"
    elif stat_arb_spread(microprice_basket,microprice_component1,microprice_component2)<-product_data["entry_parameter"]*np.std(spread_history)-product_data["epsilon"]:
        return "buy basket, sell components","case2"

    #exit, if we are in case 1 we want to do
    if stat_arb_spread(microprice_basket,microprice_component1,microprice_component2)<product_data["exit_parameter"]*np.std(spread_history):
        return "long basket, sell components, such that position = 0 in all components and basket"

    if stat_arb_spread(microprice_basket,microprice_component1,microprice_component2)>-product_data["exit_parameter"]*np.std(spread_history):
        return "sell basket, buy components, such that position = 0 in all components and basket"

    ## always trade max available position in each component and basket!



### mean reversion strategies z score variant
def mean_reversion_strategy(microprice,product_data,price_history):
    z_score=(microprice-np.mean(price_history))/np.std(price_history)
    #entry if
    if z_score<-product_data["entry_parameter"]:
        return "buy component"
    elif z_score>product_data["entry_parameter"]:
        return "sell component" #shorting

    #exit when we are currently long
    if z_score>-product_data["exit_parameter"]:
        return "sell component" #such that position=0 afterwards

    #exit when we are currently short
    if z_score<product_data["exit_parameter"]:
        return "buy component" #such that position=0 afterwards
    ## position sizing: always go max volume available


### momentum strategies with moving averages
# simple moving average , inputs are microprices and a window size #TODO window, theta are parameters to set
def simple_moving_average(price_history, window):
    return (1/window) *np.sum(price_history[window:])

#exponential_moving_average , smoothing constant theta between 0 and 1
def exponential_moving_average(price_history, window,theta):
    recent_prices = price_history[-window:]
    weights = theta ** (np.arange(1, window + 1))
    norm = np.sum(weights)
    weighted_avg = np.sum(recent_prices[::-1] * weights) / norm
    return np.sum(weighted_avg) / norm

# SMA rule
parameter_upper = 0.1
parameter_lower = 0.01
"""
window=2
if simple_moving_average(prices,window)/prices[-1]>parameter_upper:
    #sell
elif simple_moving_average(prices,window)/prices[-1]<parameter_lower:
    #buy
else:
    #do nothing and wait
theta=0.5
if exponential_moving_average(prices,window,theta)/prices[-1]>parameter_upper:
    #sell
elif exponential_moving_average(prices,window,theta)/prices[-1]<parameter_lower:
    #buy

else:
    #do nothing
"""

# bollinger weigthed moving average (BMWA)
def bollinger_moving_average(price_history,window):
    recent_prices = price_history[-window:]
    weights = np.arange(window, 0, -1)  # weights = [m, m-1, ..., 1]
    norm = np.sum(weights)
    return np.dot(recent_prices, weights) / norm

#BMWA rule to trade:
def bmwa_std(price_history, window):
    # Extract the last m prices
    recent_prices = price_history[-window:]
    # Compute the BWMA
    weights = np.arange(window, 0, -1)
    norm = np.sum(weights)
    bwma = np.dot(recent_prices, weights) / norm
    # Compute squared deviations from BWMA
    squared_deviations = (recent_prices - bwma) ** 2
    # Sample standard deviation (divide by m - 1)
    return np.sqrt(np.sum(squared_deviations) / (window - 1))

"""
#BMWA rule for trading:
window=2
if prices[-1]>(bollinger_moving_average(prices,window)+2*bmwa_std(prices,window)):
    #sell
elif prices[-1]< bollinger_moving_average(prices,window)-2*bmwa_std(prices,window):
    #buy


"""


#moving average oscillator, let m<n short and long averages (EMA(window=5) , EMA(window=10) e.g.)

#Oscillator rule SIGNALS a BREAK in the trend
#enter if:
small=2
large=5
theta=0.5
"""
if (exponential_moving_average(prices,small-1,theta)<exponential_moving_average(prices,large-1,theta) ) and (exponential_moving_average(prices,small,theta)>exponential_moving_average(prices,large,theta)):
    #then enter
# enter the market
#if  EMA(window=small,until time t-1)<EMA(window=large,until time t-1)   and EMA(window=small,until time t)> EMA(window=large,until time t):
#we can do EMA(prices, window=small-1) and EMA(prices,window=large-1) to achieve the until time t-1, a bit dirty but should work

#exit if
if ((exponential_moving_average(prices,small-1,theta)>exponential_moving_average(prices,large-1,0.5)) and exponential_moving_average(prices,small,theta)<exponential_moving_average(prices,large,theta)):
    #then exit 

"""

#RSI Ocillator
def calculate_RSI(price_history, window):
    diffs = np.diff(price_history[-(window + 1):])  # Get m differences
    gains = np.where(diffs > 0, diffs, 0)
    losses = np.where(diffs < 0, -diffs, 0)
    U_t = np.sum(gains)
    D_t = np.sum(losses)
    # Prevent division by zero
    if D_t == 0:
        return 100.0  # Max RSI if no losses
    RS = U_t / D_t
    RSI = 100 - (100 / (1 + RS))
    return RSI

#RSI rule:
#window=3
"""
if calculate_RSI(prices,window)>70:   #market overbought
    #sell or exit buy position
if calculate_RSI(prices,window)<30: #market oversold
    #buy or exit short position

"""


### MARKET MAKING

def calculate_inventory_risk(inventory, inventory_factor, position_limit, tick_size):
    """
    Calculate inventory risk linearly scaled with inventory position.

    Parameters:
        inventory (float): Current net position (can be positive or negative).
        inventory_factor (float): Risk sensitivity factor.
        position_limit (float): Maximum allowable absolute position.
        tick_size (float): Minimum price increment.

    Returns:
        float: Calculated inventory risk.
    """
    # Ensure inventory stays within bounds
    abs_inventory = min(abs(inventory), position_limit)

    # Linear scaling from 0 to 1
    scaling_factor = abs_inventory / position_limit

    inventory_risk = inventory_factor * scaling_factor * tick_size
    return inventory_risk

def volatility_calculation(history_microprices,window_size): #need to do volatility*volatility_factor
    #we are using realized volatility here P.142 from Algorithmic trading and quantitative strategies, but the square root of it and log of the prices.
    returns=np.diff(np.log(history_microprices))
    volatility=np.sum(np.square(returns))  #RV divided by window size to avoid high dependence on window size
    volatility=np.sqrt(volatility)
    #TODO fix the scaling for volatility
    return volatility

def order_imbalance_calculation(ask_volume,bid_volume,tick_size): #need to do order_imbalance*imbalance_factor
    order_imbalance=(bid_volume-ask_volume)/(bid_volume+ask_volume) #is between -1 and 1, need to find a appropriate scaling, to have an easy to set parameter for imbalance_factor

    # to get a output in tick size value, so we get between -0.1 and 0.1 and just multiply by imbalance_factor to get how many ticks it should maximally move
    # /10 is the same as *tick_size, when tick_size is 0.1
    #TODO use tanh for better scaling!
    order_imbalance=np.tanh(order_imbalance)*tick_size
    return  order_imbalance

def inventory_aware_volume_limit(current_position, position_limit, market_bid_volume, market_ask_volume, max_post_volume):
    ask_capacity = max(0, position_limit + current_position)  # how much you can sell
    bid_capacity = max(0, position_limit - current_position)  # how much you can buy

    bid_volume_post = min(bid_capacity, market_bid_volume, max_post_volume)
    ask_volume_post = min(ask_capacity, market_ask_volume, max_post_volume)

    return bid_volume_post, ask_volume_post

def MarketMaking(microprice:float,current_position:int,position_limit:int,history_microprices:list,product_data:dict):
    inventory_risk=calculate_inventory_risk(current_position,product_data["inventory_risk_factor"],position_limit,tick_size)
    base_spread=product_data["base_spread"]
    volatility=volatility_calculation(history_microprices,product_data["history_window_size"])*product_data["volatility_factor"]
    order_imbalance=order_imbalance_calculation(ask_volume,bid_volume,tick_size)*product_data["imbalance_factor"]
    ask_price=microprice+base_spread/2+volatility+order_imbalance
    bid_price=microprice-base_spread/2-volatility+order_imbalance
    #to handle inventory risk in a momentum market (and make inventory_risk_factor=0 if market is flat or mean reverting)
    if current_position>0:
        ask_price-=inventory_risk
        bid_price-=inventory_risk
    elif current_position<0:
        ask_price+=inventory_risk
        bid_price+=inventory_risk
    else:
        ask_price=ask_price
        bid_price=bid_price

    max_deviation = product_data["max_tick_deviation"] * tick_size
    # Ask price: bounded between [microprice - 1 tick, microprice + max_deviation]
    ask_price = max(ask_price, microprice - tick_size)
    ask_price = min(ask_price, microprice + max_deviation)

    # Bid price: bounded between [microprice - max_deviation, microprice + 1 tick]
    bid_price = max(bid_price, microprice - max_deviation)
    bid_price = min(bid_price, microprice + tick_size)

    min_spread = tick_size  # or use product_data["base_spread"]

    if bid_price >= ask_price - min_spread:
        bid_price = microprice - min_spread / 2
        ask_price = microprice + min_spread / 2

    round_ask=round(ask_price/tick_size)*tick_size
    round_bid=round(bid_price/tick_size)*tick_size

    ### for position sizing we always take the maximum available volume
    # Get max_post_volume from config
    max_post_volume = product_data["max_post_volume"]

    # Determine inventory-aware volume
    bid_volume_post, ask_volume_post = inventory_aware_volume_limit(current_position,position_limit,bid_volume,ask_volume,max_post_volume)

    #TODO check logic of position sizing
    #ask_position=...
    #bid_position=...
    return round_ask,round_bid,bid_volume_post, ask_volume_post #,ask_position,bid_position

ask_price,bid_price, bid_volume, ask_volume=MarketMaking(micro_price,current_position,position_limit,history_microprices,PARAMS["Product.one"])
print(ask_price,bid_price,bid_volume,ask_volume)

print(volatility_calculation(history_microprices,window_size=5))


#TODO for the decision when to do stat arb and market making, we need a value to pass: if stat_arb=True we don't do MM, and stat arb is true when there either
#TODO is a trading opportunity or when we are holding a position from stat arb!

