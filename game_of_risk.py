from random import randint


class Player:
    def __init__(self, name):
        self.name = name
        self.controlled_territories = []
        self.cards = []
        self.army_count = 0

    def __str__(self):
        return self.name


class ComputerPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.is_human = False
        # TODO: implement algorithm for computer player


class HumanPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.is_human = True


class RiskDeck:
    def __init__(self, card_count):
        each_category = card_count // 3
        self.cards = [1] * each_category + [2] * each_category + [3] * each_category

    def draw(self):
        random_card_index = randint(0, len(self.cards) - 1)
        random_card = self.cards[random_card_index]
        self.cards.remove(random_card)
        return random_card

    def give_back(self, card_list):
        self.cards.extend(card_list)


class Territory:
    def __init__(self, name, continent):
        self.name = name
        self.continent = continent
        self.neighbors = []
        self.occupying_player = None
        self.occupying_armies = 0

    def is_empty(self):
        return self.occupying_armies == 0

    def __str__(self):
        return '{}, {} --> {}'.format(self.name, self.continent, ', '.join([n.name for n in self.neighbors]))


class GameOfRisk:
    ARMY_AWARD_MIN = 3
    CARD_TRADE_INCREMENT = 2
    INITIAL_ARMY_MIN = 20
    INITIAL_CARD_TRADE = 4
    PLAYER_MIN = 3
    PLAYER_MAX = 6
    TERRITORIES_MIN_ARMY_AWARD = 8
    TERRITORY_LIMIT = 100

    """
    Example text data file below. First line is only title of game, second line is number of human players
    followed by each of the player names, third line is number of computer players followed by each of the
    player names, all remaining lines are the name of a territory, then its respective continent, then all
    of its neighbors. '|' is the delimiter.

    World War II
    4|Fred|Becky|Daisy|Luke
    2|Hal|Terminator
    France|Europe|Germany|Spain|Italy
    Japan|Asia|China|Hawaii
    ...
    """

    def __init__(self, game_file):
        self.title = ''
        self.players = []
        self.eliminated_players = []
        self.all_territories = []
        self.armies_for_card_trade = self.INITIAL_CARD_TRADE
        # Read each line of data file to populate information for game
        with open(game_file, 'r') as f:
            i = 0
            info = f.readline()
            while info:
                # Number of territories exceeds limit
                if i > self.TERRITORY_LIMIT + 3:
                    raise Exception('{} is the maximum number of territories allowed'.format(self.TERRITORY_LIMIT))
                # First line: title of game
                if i == 0:
                    self.title = info.strip()
                # Second line: human players
                elif i == 1:
                    self.set_players(info)
                # Third line: computer players
                elif i == 2:
                    self.set_players(info, is_human=False)
                # Remaining lines: territory configurations
                else:
                    self.set_territory(info)
                info = f.readline()
                i += 1
            if i < 4:
                raise Exception('uploaded file does not contain enough information to create a game')
        if not self.PLAYER_MIN <= len(self.players) <= self.PLAYER_MAX:
            raise Exception('{} players have been declared but the game requires {} to {}'.format(
                len(self.players),
                self.PLAYER_MIN,
                self.PLAYER_MAX,
            ))
        for territory in self.all_territories:
            if not territory.continent:
                raise Exception('{} has been specified as a neighbor but has not been declared itself'.format(
                    territory.name
                ))
        self.card_deck = RiskDeck(len(self.all_territories))
        self.allocate_armies()

    def __str__(self):
        return '{}\nPlaying: {}\nEliminated: {}\nTerritories:\n{}'.format(
            self.title,
            ', '.join([str(p) for p in self.players]),
            ', '.join([str(e) for e in self.eliminated_players]),
            '\n'.join([str(t) for t in self.all_territories]),
        )

    def allocate_armies(self):
        # The less players there are, the more armies they receive, at an increment of 5
        num_armies = self.INITIAL_ARMY_MIN + 5 * (self.PLAYER_MAX - len(self.players))
        for player in self.players:
            player.army_count = num_armies

    def attack_territory(self, attacking_territory, defending_territory, attacking_count, defending_count):
        attacking_player = attacking_territory.occupying_player
        defending_player = defending_territory.occupying_player
        armies_defeated = self.decide_battle(attacking_count, defending_count)
        if armies_defeated > 0:
            self.change_armies(defending_territory, -armies_defeated)
            if defending_territory.is_empty():
                self.fortify_territory(attacking_territory, defending_territory, attacking_count)
                defending_territory.occupying_player = attacking_territory.occupying_player
                attacking_player.controlled_territories.append(defending_territory)
                defending_player.controlled_territories.remove(defending_territory)
        elif armies_defeated < 0:
            self.change_armies(attacking_territory, armies_defeated)
        else:
            self.change_armies(attacking_territory, -1)
            self.change_armies(defending_territory, -1)
        # Eliminate player from contention if they no longer control any territories
        if len(defending_player.controlled_territories) == 0:
            self.players.remove(defending_player)
            self.eliminated_players.append(defending_player)

    def calculate_reinforcements(self, player):
        num_territories = len(player.controlled_territories)
        if num_territories <= self.TERRITORIES_MIN_ARMY_AWARD:
            armies_from_territories = self.ARMY_AWARD_MIN
        else:
            armies_from_territories = num_territories // 3
        new_card = self.card_deck.draw()
        armies_from_cards = self.determine_card_match(player, new_card)
        return armies_from_territories + armies_from_cards

    def decide_battle(self, attacking_count, defending_count):
        high_to_low_attack_rolls = self.roll_dice(attacking_count)
        high_to_low_defend_rolls = self.roll_dice(defending_count)
        armies_defeated = 0
        for i in range(len(high_to_low_defend_rolls)):
            if high_to_low_attack_rolls[i] > high_to_low_defend_rolls[i]:
                armies_defeated += 1
            else:
                armies_defeated -= 1
        return armies_defeated

    def determine_card_match(self, player, current_card):
        player.cards.append(current_card)
        matching_cards = []
        for card in player.cards:
            if card == current_card:
                matching_cards.append(card)
            if len(matching_cards) == 3:
                # Remove cards from player and add them back to the deck
                for match_card in matching_cards:
                    player.cards.remove(match_card)
                self.card_deck.give_back(matching_cards)
                # Award armies based on number of card trades thus far, then adjust award
                armies_from_cards = self.armies_for_card_trade
                self.armies_for_card_trade += self.CARD_TRADE_INCREMENT
                return armies_from_cards
        return 0

    def fortify_territory(self, from_territory, to_territory, num_armies):
        self.change_armies(from_territory, -num_armies)
        self.change_armies(to_territory, num_armies)

    def get_or_create_territory(self, territory_name, continent_name):
        for territory in self.all_territories:
            if territory.name == territory_name:
                # Continent field updated if territory was first declared as neighbor
                if continent_name and not territory.continent:
                    territory.continent = continent_name
                return territory
        new_territory = Territory(territory_name, continent_name)
        self.all_territories.append(new_territory)
        return new_territory

    def initial_army_placement(self):
        pass
        # TODO: loop through players and allow each to place a certain amount of armies in a territory
        # TODO: territories can only be reinforced once all territories have been selected

    def play(self):
        self.initial_army_placement()
        current_turn = 0
        while len(self.players) > 1:
            self.turn(self.players[current_turn])
            # Index next player for turn or cycle back to first player
            current_turn = current_turn + 1 if current_turn < len(self.players) - 1 else 0
        # TODO: declare winner

    def select_territory_initial(self, player, territory, num_armies):
        self.change_armies(territory, num_armies)
        territory.occupying_player = player
        player.controlled_territories.append(territory)

    def set_players(self, line_info, is_human=True):
        player_type = 'human' if is_human else 'computer'
        info_items = line_info.split('|')
        # First item is number of players, remaining items are player names
        num_players = int(info_items[0].strip())
        i = 1
        try:
            while i < num_players + 1:
                if is_human:
                    self.players.append(HumanPlayer(info_items[i].strip()))
                else:
                    self.players.append(ComputerPlayer(info_items[i].strip()))
                i += 1
        except IndexError:
            # Number of players indicated > number of names given
            raise Exception('{} {} players were declared but only {} names were provided'.format(
                num_players,
                player_type,
                i - 1,
            ))
        if i < len(info_items):
            # Number of players indicated < number of names given
            raise Exception('only {} {} players were declared but {} names were provided'.format(
                num_players,
                player_type,
                len(info_items) - 1,
            ))

    def set_territory(self, line_info):
        info_items = line_info.split('|')
        try:
            current_territory = self.get_or_create_territory(info_items[0].strip(), info_items[1].strip())
            neighbor_list = []
            for neighbor in info_items[2:]:
                neighbor_list.append(self.get_or_create_territory(neighbor.strip(), None))
            current_territory.neighbors.extend(neighbor_list)
        except IndexError:
            raise Exception('all territories must belong to a continent and have at least one neighbor')

    def turn(self, player):
        print('Player {}\'s turn.'.format(player.name))
        # Phase 1: reinforce
        print('PHASE 1: REINFORCE')
        reinforcements = self.calculate_reinforcements(player)
        
        while reinforcements != 0:
            i = 0
            for territory in player.controlled_territories:
                print('{}: {}, {} -- {} troops'.format(i, territory.name, territory.continent, territory.occupying_armies))
                i += 1
            reinforced_territory = int(input('Here are the territories that you control.\n Choose the number \
             corresponding to the territory you would like to fortify.'))
            reinforcement_count = int(input('You have {} reinforcements remaining. How many armies \
             would you like to place in {}?'.format(reinforcements, player.controlled_territories[place])))

            self.change_armies(player.controlled_territories[place], reinforcement_count)
            reinforcements -= reinforcement_count


        # Phase 2: attack
        print('PHASE 2: ATTACK')
        # TODO: ask player if and where they would like to attack a territory
        attack = int(input('Would you like to attack? (1 = yes, 0 = no)'))
        while attack == 1:
            territories_for_attack = self.get_territories_for_attack(player)
            i = 0
            # Display available territories to attack
            for territory in territories_for_attack:
                print('{}: {}, {} -- {} defending troops'.format(i, territory.name, territory.continent, territory.occupying_armies))
                i += 1
            attack_choice = int(input("Which territory would you like to attack? (Please select the number)"))
            to_be_attacked = territories_for_attack[attack_choice]
            attacking_territories = self.get_attacking_territories(player, to_be_attacked)
            # Display available territories to attack with
            i = 0
            for territory in attacking_territories:
                print('{}: {}, {} -- {} available troops for attack'.format(i, territory.name, territory.continent, territory.occupying_armies - 1))
                i += 1
            attacking_territory_choice = int(input('Which territory would you like to attack with? (Please select the number)'))
            to_attack_with = attacking_territories[attacking_territory_choice]


            # Engage in battle
            while True:
                attacking_armies = int(input('How many armies do you want to attack with? (up to {})'.format(3 if to_attack_with.occupying_armies >= 4 else to_attack_with.occupying_armies - 1)))
                defending_armies = int(input('{}, how many armies would you like to defend with? (up to {})'.format(to_be_attacked.occupying_player, 2 if to_be_attacked.occupying_armies >= 2 else 1)))
                self.attack_territory(to_attack_with, to_be_attacked, attacking_armies, defending_armies)
                print('Remaining attacking armies: {}\nRemaining defending armies: {}'.format(to_attack_with.occupying_armies, to_be_attacked.occupying_armies))

                # Attacker is victorious
                if to_be_attacked.occupying_armies == 0:
                    num_armies = int(input('{} won the territory {}. How many armies would you like to move here? (up to {})'.format(to_attack_with.occupying_player, to_be_attacked.name, to_attack_with.occupying_armies - 1)))
                    self.fortify_territory(to_attack_with, to_be_attacked, num_armies)
                    break

                # Attacker is defeated
                elif to_attack_with.occupying_armies == 1:
                    print('You can no longer attack this territory. You have been defeated.')
                    break

                # Choose to continue the fight
                else:
                    fight = int(input('Would you like to continue the battle? (1 = yes, 0 = no)'))
                    if fight == 0:
                        break
            attack = int(input('Would you like to attack another territory? (1 = yes, 0 = no)'))


        # Phase 3: fortify
        print('PHASE 3: FORTIFY')
        fortify = int(input('Would you like to fortify any territories? (1 = yes, 0 = no)'))
        if fortify == 1:
            while True:
                i = 0
                for territory in player.controlled_territories:
                    print('{}: {}, {} -- {} troops'.format(i, territory.name, territory.continent, territory.occupying_armies))
                index_from = int(input('Select the territory that you would like to move armies from. (Select the number)'))
                territory_from = player.controlled_territories[index_from]
                index_to = int(input('Select the territory that you would like to move armies to. (Select the number)'))
                territory_to = player.controlled_territories[index_to]
                num_armies = int(input('How many armies would you like to move from {} to {}? (up to {})'.format(territory_from, territory_to, territory_from.occupying_armies - 1)))
                self.fortify_territory(territory_from, territory_to, num_armies)

                continue_fortify = int(input('Would you like to continue fortifying? (1 = yes, 0 = no)'))
                if continue_fortify == 0:
                    break

        print('End of turn.')


    @staticmethod
    # Accepts positive or negative integer to increase or decrease armies in a territory
    def change_armies(territory, num_armies):
        territory.occupying_armies += num_armies

    @staticmethod
    def get_territories_for_attack(player):
        territories_for_attack = set()
        for territory in player.controlled_territories:
            if territory.occupying_armies > 1:
                uncontrolled_territories = {n for n in territory.neighbors if n.occupying_player != player}
                territories_for_attack = territories_for_attack.union(uncontrolled_territories)
        return territories_for_attack


    # input: player and territory to attacking
    # output: list of owned territories to attack with
    @staticmethod
    def get_attacking_territories(player, territory):
        neighbors = set(territory.neighbors)
        player_territories = set(player.controlled_territories)
        attacking_territories = neighbors.intersection(player_territories)
        return list(attacking_territories)

    @staticmethod
    def roll_dice(num_rolls):
        rolls = []
        for _ in range(num_rolls):
            current_roll = randint(1, 6)
            i = 0
            while i < len(rolls) and current_roll < rolls[i]:
                i += 1
            rolls.insert(i, current_roll)
        return rolls
