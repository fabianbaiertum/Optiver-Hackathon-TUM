import numpy as np
  
# As the implementation of each of the variables is the edge in future competitions, I excluded them here. 
# If you got any questions about it, just ask me

microprice=9.9
current_position=0
position_limit=50
tick_size=0.1

def MarketMaking(microprice:float,current_position:int,position_limit:int,history_microprices:list,product_data:dict):
    inventory_risk=calculate_inventory_risk(current_position,product_data["inventory_risk_factor"],position_limit,tick_size)
    base_spread=product_data["base_spread"]
    volatility=volatility_calculation(history_microprices,product_data["history_window_size"])*product_data["volatility_factor"]
    order_imbalance=order_imbalance_calculation(ask_volume,bid_volume)*product_data["imbalance_factor"]
    ask_price=microprice+base_spread/2+volatility+order_imbalance
    bid_price=microprice-base_spread/2-volatility+order_imbalance

    if current_position>0:
        ask_price-=inventory_risk
        bid_price-=inventory_risk
    elif current_position<0:
        ask_price+=inventory_risk
        bid_price+=inventory_risk
    else:
        ask_price=ask_price
        bid_price=bid_price
    round_ask=round(ask_price/tick_size)*tick_size
    round_bid=round(bid_price/tick_size)*tick_size

    ### for position sizing we always take the maximum available volume

    #ask_position=...
    #bid_position=...
    return round_ask,round_bid #,ask_position,bid_position
