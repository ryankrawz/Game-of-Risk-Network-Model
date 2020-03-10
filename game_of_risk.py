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
        self.card_ceiling = len(self.cards)

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
        # TODO: complete game play functionality
        # self.play()

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
        # TODO: loop through players and allow each to place a certain amount of armies in a territory
        # TODO: territories can only be reinforced once all territories have been selected

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
        player.cards.append(current_card)
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

    def play(self):
        current_turn = 0
        while len(self.players) > 1:
            self.turn(self.players[current_turn])
            # Index next player for turn or cycle back to first player
            current_turn = current_turn + 1 if current_turn < len(self.players) - 1 else 0
        # TODO: declare winner

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
            raise Exception('{} {} players were declared but {} too many names were provided'.format(
                num_players,
                player_type,
                len(info_items) - i,
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
        # Phase 1: reinforce
        reinforcements = self.calculate_reinforcements(player)
        # TODO: ask player where they would like to place reinforcements
        # Phase 2: attack
        # TODO: ask player if and where they would like to attack a territory
        # TODO: the territory should simply be fortified if it is already empty
        # Phase 3: fortify
        # TODO: ask player where they would like to move troops to and from
        return 0

    @staticmethod
    # Accepts positive or negative integer to increase or decrease armies in a territory
    def change_armies(territory, num_armies):
        territory.occupying_armies += num_armies

    @staticmethod
    def get_territories_for_attack(player):
        territories_for_attack = set()
        for territory in player.controlled_territories:
            if territory.occupying_armies > 1:
                territories_for_attack = territories_for_attack.union(territory.neigbors)
        return territories_for_attack

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
