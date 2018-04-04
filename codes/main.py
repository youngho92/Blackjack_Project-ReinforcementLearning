from train import Train
from backtest import Backtest


## train 6-deck blackjack game with 0.1 learning rate and 1 discount
t=Train(0.01, 1)
t.train(300000)

## backtest the blackjack game 10000 times based on the previous training result
backtest = Backtest(t.Q)
payoff = backtest.backtest(20000)

## calculate the accumulated payoff
accum_payoff = [payoff[0]]
for i in range(1, 20000):
    accum_payoff.append(accum_payoff[i-1] + payoff[i])

## find the accumulated winning odds
winning_odds = [accum_payoff[i]/(2*(i+1)) for i in range(20000)]
print(winning_odds[-1]) # print winning odds after player 20000 games
