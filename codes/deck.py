import pandas as pd
import numpy as np

## define deck types and draws ##
class Deck:

    ## draw a new deck
    def __init__(self):
        nd = []
        for i in range(2, 10):
            nd += [str(i)] * 4 * 6  # 6-deck Blackjack game
        nd += ['10'] * 16 * 6 + ['A'] * 4 * 6
        self.deck = nd

    ## shuffle it
    def shuffle(self):
        shuffle_times = np.random.randint(15, 20)
        for _ in range(shuffle_times):
            np.random.shuffle(self.deck)

    ## draw a new card
    def draw(self):
        return self.deck.pop(0)

    ## return the number of remaining cards
    def size(self):
        return len(self.deck)
