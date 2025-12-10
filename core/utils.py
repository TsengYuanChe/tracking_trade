def calc_avg_cost(buys):
    return sum(b["price"] for b in buys) / len(buys)