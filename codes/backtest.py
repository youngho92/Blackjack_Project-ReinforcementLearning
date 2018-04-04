import operator
from deck import Deck
from state import State
from train import Train

## define the backtest class based on the trained matrix Q
class Backtest:
    ## initialize deck, state, and Q
    def __init__(self, Q):
        self.state=State()
        self.deck=Deck()
        self.deck.shuffle()
        self.Q=Q

    ## return available actions based on the current card_state and action
    def available_actions(self, card_state, action):
        ## 0: stand, 1: hit, 2: doubledown, 3: split
        ## split and doubledown allowed
        if action == 'initial' or action == 'split':
            if card_state == 'terminal':
                return [0]
            elif len(card_state[0]) == 2 and card_state[0][0] == card_state[0][1]:
                return [0, 1, 2, 3]
            else:
                return [0, 1, 2]
        ## split and doubledown are not allowed after hit
        elif action == 'hit':
            if card_state[0][0] == '21':
                return [0]
            else:
                return [0, 1]

    ## return row index of the Q Matrix for the given card state
    def state_to_row(self, card_state):
        if card_state == 'terminal':
            return (self.state.deck_state+901) * len(self.state.card_states)-1
        else:
            player = card_state[0]
            dealer = card_state[1]
            return (self.state.deck_state+900) * len(self.state.card_states) +\
        len(self.state.dealer_hand) * self.state.player_hand.index(player) + self.state.dealer_hand.index(dealer)

    ## possible sums for the sets of cards
    def sum_cases(self, hands):
        cases = [0]
        for hand in hands:
            if hand != 'A':
                cases = [case + int(hand) for case in cases]
            else:
                cases = [case + 1 for case in cases] + [case + 11 for case in cases]
        return cases


    ## return the reward when the player stands
    def stand_result(self, card_state, dealer_hidden):

        ## find the player's maximum sum
        player = card_state[0]
        player_sums = [s for s in self.sum_cases(player) if s <= 21]
        player_sum = max(player_sums)

        ## reveal the upside down card
        dealer = card_state[1] + (dealer_hidden, )
        dealer_sums = [s for s in self.sum_cases(dealer) if s <= 21]

        ## dealer keeps hitting until going bust
        while dealer_sums:
            if max(dealer_sums) > player_sum:  # dealer wins!
                return 0

            if max(dealer_sums) >= 17:
                if max(dealer_sums) == player_sum:  # draw!
                    return 1
                else:
                    return 2  # player wins!

            ## dealer draws a new card
            new_card = self.deck.draw()
            self.state.update_deck_state(new_card)

            dealer_sums = [s for s in self.sum_cases(dealer_sums + [new_card]) if s <= 21]

        return 2

    ## return immediate return when the player doubledowns
    def doubledown_result(self, card_state, dealer_hidden):
        player = card_state[0]

        ## draw a new card
        new_card = self.deck.draw()
        self.state.update_deck_state(new_card)

        player_sums = [s for s in self.sum_cases(player + (new_card, )) if s <= 21]

        if not player_sums: # player busts
            return -1

        ## find the maximum sum of the player
        player_sum = max(player_sums)
        dealer = card_state[1] + (dealer_hidden, )
        dealer_sums = [s for s in self.sum_cases(dealer) if s <= 21]

        ## dealer keeps hitting until going bust
        while dealer_sums:
            if max(dealer_sums) > player_sum:  # dealer wins!
                return -1

            if max(dealer_sums) >= 17:
                if max(dealer_sums) == player_sum:  # draw!
                    return 1
                else:
                    return 3  # player wins!

            ## dealer draws a new card
            new_card = self.deck.draw()
            self.state.update_deck_state(new_card)

            dealer_sums = [s for s in self.sum_cases(dealer_sums + [new_card]) if s <= 21]

        return 3

    ## play one game and return profit
    def game(self, card_state=(), dealer_hidden=False, phase='initial'):
        if phase == 'initial':  # game starts (default)

            ## draw 2 new cards
            player = tuple(self.deck.draw() for _ in range(2))
            dealer = tuple(self.deck.draw() for _ in range(2))

            ## update the deck state
            for p in player:
                self.state.update_deck_state(p)
            for d in dealer:
                self.state.update_deck_state(d)

            ## the second card is upside-down
            dealer_open = dealer[0]
            dealer_hidden = dealer[1]

            if set(player) == set(['10', 'A']):  # Blackjack!
                return 2.5

            if 'A' in player:
                index_A = player.index('A')
                player = (player[index_A], player[index_A^1])
            elif player[0] != player[1]:
                player = (str(sum([int(p) for p in player])), )
            card_state = (player, (dealer_open, ))

        ## Game continues after the player splits
        elif phase == 'split':
            new_card = self.deck.draw()
            self.state.update_deck_state(new_card)

            ## 'A' exists in the player's hand
            if card_state[0][0] == 'A':
                if new_card == '10':
                    return 2.5
                card_state = (('A', new_card), card_state[1])

            ## 'A' does not exist in the player's hand
            else:
                if new_card == 'A':
                    if card_state[0][0] == '10':
                        return 2.5
                    card_state = (('A', card_state[0][0]), card_state[1])
                else:
                    if card_state[0][0] == new_card:
                        card_state = ((new_card, new_card), card_state[1])
                    else:
                        card_state = ((str(int(new_card)+int(card_state[0][0])), ), card_state[1])

        ## Game continues after the player hits
        elif phase == 'hit':
            # draw a new card
            new_card = self.deck.draw()

            # update deck and card states
            self.state.update_deck_state(new_card)
            card_state = self.state.update_card_state(card_state, new_card)
            if card_state == 'terminal':
                return 0

        row = self.state_to_row(card_state)
        actions = self.available_actions(card_state, phase)
        d = {action: self.Q[row, action] for action in actions}
        action = sorted(d.items(), key=operator.itemgetter(1))[::-1][0][0]

        if action == 0: # stand
            return self.stand_result(card_state, dealer_hidden)
        elif action == 1: # hit
            return self.game(card_state=card_state, dealer_hidden=dealer_hidden, phase='hit')
        elif action == 2: # double down
            return self.doubledown_result(card_state, dealer_hidden)
        else: # split
            card_state = ((card_state[0][0], ), card_state[1])
            return1 = self.game(card_state=card_state, dealer_hidden=dealer_hidden, phase='split')
            return2 = self.game(card_state=card_state, dealer_hidden=dealer_hidden, phase='split')

            return return1 + return2

    ## backtest the model and return the profit list for n games
    def backtest(self, n):
        profit = [0]
        for _ in range(n):
            if len(self.deck.deck) < 40:
                self.deck=Deck()
                self.deck.shuffle()
                self.state.deck_state = 0
            profit.append(self.game())
        return profit
