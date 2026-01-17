class SlippageModel:
    def apply(self, price, qty):
        if qty <= 50: slip = 0.0005
        elif qty <= 200: slip = 0.001
        else: slip = 0.002
        return round(price * (1 + slip), 2)

class ExecutionEngine:
    def __init__(self):
        self.slippage = SlippageModel()

    def execute_buy(self, price, qty):
        return self.slippage.apply(price, qty)
