from deck import Deck
from state import State
import pandas as pd
import numpy as np

## train the model using Q-learning algorithm
class Train:
    ## define train parameters alpha, gamma, and Q
    def __init__(self, alpha, gamma):
        self.alpha=alpha # learning rate
        self.gamma=gamma
        self.state = State()
        self.deck = Deck()
        self.deck.shuffle()
        self.Q=np.matrix(np.zeros([len(self.state.card_states)*1801, 4]))

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

        '''
        deck_state = int(deck_state / card_numbers * 100)
        deck_state = -900  -> 0th row
        deck_state =   0  -> 900th row
        deck_state =  900 -> 1800th row
        '''

        deck_state = int(self.state.deck_state / len(self.deck.deck) * 300)

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


    ## return immediate reward when the player stands
    ## update Q-matrix based on the immediate reward
    def stand_result(self, card_state, dealer_hidden):

        ## find the player's maximum sum
        player = card_state[0]
        player_sums = [s for s in self.sum_cases(player) if s <= 21]
        player_sum = max(player_sums)

        ## reveal the upside down card
        dealer = card_state[1] + (dealer_hidden, )
        dealer_sums = [s for s in self.sum_cases(dealer) if s <= 21]
        reward = 2 # initialize reward

        ## dealer keeps hitting until going bust
        while dealer_sums:

            if max(dealer_sums) > player_sum: # dealer wins!
                reward = 0
                break

            if max(dealer_sums) >= 17:
                if max(dealer_sums) == player_sum: # draw!
                    reward = 1
                    break
                else:
                    reward = 2 # player wins!
                    break

            ## dealer draws a new card and update states
            new_card = self.deck.draw()
            self.state.update_deck_state(new_card)
            dealer_sums = [s for s in self.sum_cases(dealer_sums + [new_card]) if s <= 21]


        ## update Q
        row = self.state_to_row(card_state)
        next_row = self.state_to_row('terminal')
        self.Q[row, 0] = (1-self.alpha)*self.Q[row, 0] + self.alpha*(reward+self.gamma*self.Q[next_row, 0])

        return reward

    ## return immediate reward when the player doubledowns
    ## update Q-matrix based on the immediate reward
    def doubledown_result(self, card_state, dealer_hidden):
        player = card_state[0]

        ## Player draws a new card
        new_card = self.deck.draw()
        self.state.update_deck_state(new_card)

        player_sums = [s for s in self.sum_cases(player + (new_card, )) if s <= 21]

        if not player_sums: # player busts
            row = self.state_to_row(card_state)
            next_row = self.state_to_row('terminal')
            self.Q[row, 2] = (1-self.alpha)*self.Q[row, 2] + self.alpha*(-1+self.gamma*self.Q[next_row, 0])
            return -1

        ## find the maximum sum for the player
        player_sum = max(player_sums)
        dealer = card_state[1] + (dealer_hidden, )
        dealer_sums = [s for s in self.sum_cases(dealer) if s <= 21]
        reward = 3  # initialize a reward

        ## dealer keeps hitting until going bust
        while dealer_sums:
            if max(dealer_sums) > player_sum: # dealer wins!
                reward = -1
                break

            if max(dealer_sums) >= 17:
                if max(dealer_sums) == player_sum: # draw!
                    reward = 1
                    break
                else:
                    reward = 3 # player wins!
                    break

            ## dealer draws a new card
            new_card = self.deck.draw()
            self.state.update_deck_state(new_card)

            dealer_sums = [s for s in self.sum_cases(dealer_sums + [new_card]) if s <= 21]

        ## update Q
        row = self.state_to_row(card_state)
        next_row = self.state_to_row('terminal')
        self.Q[row, 2] = (1-self.alpha)*self.Q[row, 2] + self.alpha*(reward+self.gamma*self.Q[next_row, 0])

        return reward

    ## play one game and return profit
    def game(self, card_state=(), dealer_hidden=False, phase='initial'):
        if phase == 'initial': # game starts (default)

            ## draw 2 new cards
            player = tuple(self.deck.draw() for _ in range(2))
            dealer = tuple(self.deck.draw() for _ in range(2))

            ## update deck state
            for p in player:
                self.state.update_deck_state(p)
            for d in dealer:
                self.state.update_deck_state(d)

            ## the second card is upside-down
            dealer_open = dealer[0]
            dealer_hidden = dealer[1]

            if set(player) == set(['10', 'A']): # Blackjack!
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
            row = self.state_to_row(card_state)
            new_card = self.deck.draw()

            # update deck and card states
            self.state.update_deck_state(new_card)
            card_state = self.state.update_card_state(card_state, new_card)
            next_row = self.state_to_row(card_state)
            if card_state == 'terminal':
                self.Q[row, 1] = (1-self.alpha)*self.Q[row, 1] + self.alpha*(0+self.gamma*self.Q[next_row, 0])
                return 0


            # update Q
            next_actions = self.available_actions(card_state, phase)
            max_index = 0
            for next_action in next_actions:
                if self.Q[next_row, next_action] > self.Q[next_row, max_index]:
                    max_index = next_action

            self.Q[row, 1] = (1-self.alpha)*self.Q[row, 1] + self.alpha*(0+self.gamma*self.Q[next_row, max_index])

        ## extract possible actions based on card_state and phase
        actions = self.available_actions(card_state, phase)
        action = np.random.choice(actions)


        if action == 0: # stand
            return self.stand_result(card_state, dealer_hidden)
        elif action == 1: # hit
            return self.game(card_state=card_state, dealer_hidden=dealer_hidden, phase='hit')
        elif action == 2: # double down
            return self.doubledown_result(card_state, dealer_hidden)
        else: # split
            row = self.state_to_row(card_state)
            card_state = ((card_state[0][0], ), card_state[1])
            reward1 = self.game(card_state=card_state, dealer_hidden=dealer_hidden, phase='split')
            reward2 = self.game(card_state=card_state, dealer_hidden=dealer_hidden, phase='split')

            ## update Q
            next_row = self.state_to_row('terminal')
            self.Q[row, 3] = (1-self.alpha)*self.Q[row, 3] + self.alpha*((reward1+reward2)+self.gamma*self.Q[next_row, 0])
            return reward1 + reward2

    ## Train the model using Q-learning n times
    def train(self, n):
        for _ in range(n):
            ## When the number of remaining cards is lower than 40, the dealer uses a new card set
            if len(self.deck.deck) < 40:
                self.deck = Deck()
                self.deck.shuffle()
                self.state.deck_state = 0
            self.game()
