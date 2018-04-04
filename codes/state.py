from deck import Deck

## Define state types and update states based on action ##
## We will consider card states on the table and cards remaining ##
class State:
    def __init__(self):
        ## Dealer's hand ##
        dealer_hand = [(str(i), ) for i in range(2, 11)] + [('A', )]
        self.dealer_hand = dealer_hand

        ## Player's hand ##
        bj_hand = [('A', '10')]
        hard_hand = [(str(i), ) for i in range(5, 22)]
        soft_hand = [('A', str(i)) for i in range(2, 10)]
        pair_hand = [(str(i), str(i)) for i in range(2, 11)] + [('A', 'A')]
        player_hand = hard_hand + soft_hand + pair_hand
        self.player_hand = player_hand

        ## define card states
        card_states = []
        for player in player_hand:
            for dealer in dealer_hand:
                card_states.append((player, dealer))
        card_states += ['terminal']

        self.card_states = card_states

        ## define deck states
        self.deck_state = 0

    ## update the deck state based on card counting
    def update_deck_state(self, new_card):
        """
        ####### Hi-Low Card Counting #########
        if new_card in ['2', '3', '4', '5', '6']:
            self.deck_state -= 1
        elif new_card in ['10', 'A']:
            self.deck_state += 1
        return
        """

        ####### Omega-II Card Counting #########
        if new_card in ['4', '5', '6']:
            self.deck_state += 2
        elif new_card in ['2', '3', '7']:
            self.deck_state += 1
        elif new_card in ['10']:
            self.deck_state -= 2
        elif new_card in ['9']:
            self.deck_state -= 1


    ## possible sums for the sets of cards
    def sum_cases(self, hands):
        cases = [0]
        for hand in hands:
            ## 'A' can be counted as 1 or 11
            if hand != 'A':
                cases = [case + int(hand) for case in cases]
            else:
                cases = [case + 1 for case in cases] + \
                        [case + 11 for case in cases]
        return cases


    ## update the card state on the table
    ## for instance, if the player's current hand is ('A', '3') and draws '3', then the state becomes ('A', '6')

    def update_card_state(self, card_state, new_card):
        player = card_state[0]
        dealer = card_state[1]

        ## check if it busts
        check = [s for s in self.sum_cases(player + (new_card, )) if s <= 21]
        if not check:
            return 'terminal'

        # new_card == 'A'
        if new_card == 'A':
            if player == ('A', 'A'):
                return (('A', '2'), dealer)
            elif 'A' in player:
                if player[1] == '10':
                    return (('12', ), dealer)
                elif player[1] == '9':
                    return (('21', ), dealer)
                else:
                    current_sum = int(player[1]) + 1
                    return (('A', str(current_sum)), dealer)
            else:
                current_sum = sum([int(p) for p in player])
                if current_sum >= 20 or current_sum == 10:
                    return (('21', ), dealer)
                if current_sum > 10:
                    return ((str(current_sum+1), ), dealer)
                else:
                    return (('A', str(current_sum)), dealer)

        # new_card != 'A'
        else:
            if player == ('A', 'A'):
                if new_card == '10':
                    return (('12', ), dealer)
                elif new_card == '9':
                    return (('21', ), dealer)
                else:
                    current_sum = int(new_card) + 1
                    return (('A', str(current_sum)), dealer)

            elif 'A' in player:
                current_sum = int(new_card) + int(player[1])
                if current_sum == 10 or current_sum >= 20:
                    return (('21', ), dealer)
                elif current_sum > 10:
                    return ((str(current_sum+1),), dealer)
                else:
                    return (('A', str(current_sum)), dealer)

            else:
                current_sum = sum([int(p) for p in player]) + int(new_card)
                if current_sum == 21:
                    return (('21', ), dealer)
                else:
                    return ((str(current_sum), ), dealer)
