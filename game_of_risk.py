from random import randint
from time import sleep
from tkinter import Tk

from matplotlib import pyplot
import networkx

from players import ComputerPlayer, HumanPlayer


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
    # Game settings
    ARMY_AWARD_MIN = 3
    CARD_TRADE_INCREMENT = 2
    COLOR_COUNTER = 0
    INITIAL_ARMY_MIN = 20
    INITIAL_CARD_TRADE = 4
    PLAYER_MIN = 3
    PLAYER_MAX = 6
    TERRITORIES_MIN_ARMY_AWARD = 8
    TERRITORY_LIMIT = 50
    # Visualization settings
    ALL_WINDOWS = 'all'
    EDGE_COLOR = '#bdc2c9'
    EMPTY_NODE_COLOR = '#adb1b8'
    FONT_SIZE = 5
    FONT_WEIGHT = 'bold'
    COLORS = ['#e66a6a', '#6ab2e6', '#97e699', '#f3f57a', '#edb277', '#d39ef0']
    NODE_SIZE = 500

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
        # Game attributes
        self.title = ''
        self.players = []
        self.eliminated_players = []
        self.all_territories = []
        self.player_colors = dict()
        self.armies_for_card_trade = self.INITIAL_CARD_TRADE
        # Visualization attributes
        self.risk_map = networkx.Graph()
        self.root = Tk()
        self.root.withdraw()
        self.node_colors = []
        self.labels = dict()
        self.layout = None
        self.window_dimensions = self.get_window_dimensions()
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
        # Players can hold 7 cards at most
        self.card_deck = RiskDeck(7 * len(self.players))
        self.allocate_armies()
        self.position_risk_map()

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
            self.eliminate_player(defending_player)

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
            if i >= len(high_to_low_attack_rolls):
                break
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

    def draw_risk_map(self):
        self.update_risk_map()
        pyplot.close(self.ALL_WINDOWS)
        self.root.update_idletasks()
        pyplot.figure(num=self.title, figsize=self.window_dimensions)
        networkx.draw(
            self.risk_map,
            pos=self.layout,
            node_size=self.NODE_SIZE,
            node_color=self.node_colors,
            edge_color=self.EDGE_COLOR,
            labels=self.labels,
            font_size=self.FONT_SIZE,
            font_weight=self.FONT_WEIGHT,
        )
        pyplot.show(block=False)
        self.root.update()

    def eliminate_player(self, player):
        self.card_deck.give_back(player.cards)
        self.players.remove(player)
        self.eliminated_players.append(player)
        self.print_slow('\nWith no remaining territories, {} has been eliminated!'.format(player.name))

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

    def get_window_dimensions(self):
        # Match window dimensions to aspect ratio of computer
        return self.root.winfo_screenmmwidth() / 30, self.root.winfo_screenmmheight() / 40

    def initial_army_placement(self):
        available_territories = list.copy(self.all_territories)
        # Claim all initial territories
        for i in range(len(self.all_territories)):
            current_player = self.players[i % len(self.players)]
            if current_player.is_human:
                self.print_territory_info(available_territories)
                query = '\n{}\'s turn to place an army. Select the number of the territory to claim: '.format(
                    current_player.name,
                )
                selection = self.retrieve_numerical_input(query, len(available_territories) - 1)
                initial_selection = available_territories[selection]
            else:
                initial_selection = current_player.claim_territory(available_territories)
                self.print_slow('\n{} claimed {}.'.format(current_player.name, initial_selection.name))
            self.select_territory_initial(current_player, initial_selection, 1)
            available_territories.remove(initial_selection)
        self.print_slow('\nInitial army placement completed.\n')

        # Reinforce territories once all have been claimed
        for player in self.players:
            if player.army_count > 0:
                self.print_slow('\n{}\'s turn to reinforce territories.'.format(player.name))
            if player.is_human:
                while player.army_count > 0:
                    self.print_territory_info(player.controlled_territories)
                    query = 'Select the number of a territory to reinforce: '
                    reinforce_index = self.retrieve_numerical_input(
                        query,
                        len(player.controlled_territories) - 1,
                    )
                    reinforce_territory = player.controlled_territories[reinforce_index]
                    query = 'How many additional armies would you like to place in {}? (Up to {}) '.format(
                        reinforce_territory.name,
                        player.army_count,
                    )
                    reinforcement = self.retrieve_numerical_input(query, player.army_count)
                    self.change_armies(reinforce_territory, reinforcement)
                    player.army_count -= reinforcement
            else:
                reinforced_territory_names = player.reinforce_initial()
                self.print_slow('\n{} reinforced {}.'.format(player.name, ', '.join(reinforced_territory_names)))
        self.print_slow('\nReinforcement completed.\n')

    def play(self):
        self.print_slow('\nGAME OF RISK: {}\n'.format(self.title.upper()))
        self.initial_army_placement()
        current_turn = 0
        while len(self.players) > 1:
            # Visualize risk map
            self.draw_risk_map()
            self.turn(self.players[current_turn])
            # Index next player for turn or cycle back to first player
            current_turn = current_turn + 1 if current_turn < len(self.players) - 1 else 0
        winner = self.players[0].name
        confetti = '*' * (len(winner) + 8)
        self.print_slow('\n{0}\n*{1} wins!*\n{0}\n'.format(confetti, winner))
        # Spin down visualization
        pyplot.close(self.ALL_WINDOWS)
        self.root.update_idletasks()
        self.root.destroy()

    def position_risk_map(self):
        for territory in self.all_territories:
            # Include territory in map
            self.risk_map.add_node(territory.name)
            # Initiate with empty color
            self.node_colors.append(self.EMPTY_NODE_COLOR)
            # Label territory with name, army count, and occupying player
            self.labels[territory.name] = '{}\n0 armies\n'.format(territory.name)
            for neighbor in territory.neighbors:
                self.risk_map.add_edge(territory.name, neighbor.name)
        # Position nodes using a cost function based on path length
        self.layout = networkx.kamada_kawai_layout(self.risk_map)

    def select_territory_initial(self, player, territory, num_armies):
        self.change_armies(territory, num_armies)
        player.army_count -= num_armies
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
                if info_items[i]:
                    player_name = info_items[i].strip()
                    if is_human:
                        self.players.append(HumanPlayer(player_name))
                    else:
                        self.players.append(ComputerPlayer(player_name))
                    # Track player color for visualization
                    if self.COLOR_COUNTER >= len(self.COLORS):
                        raise Exception('too many {} players have been declared'.format(player_type))
                    self.player_colors[player_name] = self.COLORS[self.COLOR_COUNTER]
                    self.COLOR_COUNTER += 1
                    i += 1
                else:
                    raise Exception('a {} player with no name has been declared'.format(player_type))
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
        player_address = 'You' if player.is_human else player.name
        border = '-' * (len(player.name) + 12)
        self.print_slow('\n{0}\n| {1}\'s turn. |\n{0}'.format(border, player.name))

        # Phase 1: reinforce
        self.print_slow('\nPHASE 1: REINFORCE\n')
        reinforcements = self.calculate_reinforcements(player)
        self.print_slow('{} received {} reinforcements.\n'.format(player_address, reinforcements))
        # Capture territories for attack for computer player to determine reinforcements
        territories_for_attack = self.get_territories_for_attack(player)
        attack_route = None

        if player.is_human:
            while reinforcements > 0:
                self.print_territory_info(player.controlled_territories)
                self.print_slow('Here are the territories that you control.')
                query = 'Select the number of the territory you\'d like to reinforce: '
                reinforce_index = self.retrieve_numerical_input(query, len(player.controlled_territories) - 1)
                query = 'How many armies would you like to place in {}? (up to {}) '.format(
                    player.controlled_territories[reinforce_index].name,
                    reinforcements,
                )
                reinforcement_count = self.retrieve_numerical_input(query, reinforcements)
                self.change_armies(player.controlled_territories[reinforce_index], reinforcement_count)
                reinforcements -= reinforcement_count
        else:
            attack_route = player.choose_attack_route(territories_for_attack, reinforcements)
            # Reinforce territory with fewest armies if no attack is advisable
            if attack_route:
                territory_to_reinforce = attack_route[0]
            else:
                territory_to_reinforce = player.lowest_army_count()
            self.print_slow('{} reinforced {} with {} armies.'.format(
                player.name,
                territory_to_reinforce.name,
                reinforcements,
            ))
            self.change_armies(territory_to_reinforce, reinforcements)

        # Phase 2: attack
        attack = 0
        if len(territories_for_attack) > 0:
            if player.is_human:
                self.print_slow('\nPHASE 2: ATTACK\n')
                query = 'Would you like to attack? (1 = yes, 0 = no) '
                attack = self.retrieve_numerical_input(query, 1)
            else:
                attack = 1 if attack_route else 0
        while attack == 1 and len(self.players) > 1:
            if player.is_human:
                self.print_territory_info(territories_for_attack)
                query = 'Select the number of the territory you\'d like to attack: '
                attack_choice = self.retrieve_numerical_input(query, len(territories_for_attack) - 1)
                to_be_attacked = territories_for_attack[attack_choice]
                attacking_territories = self.get_surrounding_territories(player, to_be_attacked)
                # Display available territories to attack from
                self.print_territory_info(attacking_territories)
                query = 'Select the number of the territory you\'d like to attack from: '
                attacking_territory_choice = self.retrieve_numerical_input(query, len(attacking_territories) - 1)
                to_attack_from = attacking_territories[attacking_territory_choice]
            else:
                to_be_attacked = attack_route[1]
                to_attack_from = attack_route[0]

            # Engage in battle
            while True:
                defending_player = to_be_attacked.occupying_player
                attack_limit = 3 if to_attack_from.occupying_armies >= 4 else to_attack_from.occupying_armies - 1
                if player.is_human:
                    query = 'How many armies do you want to attack with? (up to {}) '.format(attack_limit)
                    attacking_armies = self.retrieve_numerical_input(query, attack_limit)
                else:
                    attacking_armies = attack_limit
                    army_tag = 'army' if attacking_armies == 1 else 'armies'
                    self.print_slow('\n{} is attacking {} with {} {} from {}.'.format(
                        player.name,
                        to_be_attacked.name,
                        attacking_armies,
                        army_tag,
                        to_attack_from.name,
                    ))
                defend_limit = 2 if to_be_attacked.occupying_armies >= 2 else 1
                if defending_player.is_human:
                    query = '{}, how many armies do you want to defend {} with? (up to {}) '.format(
                        defending_player.name,
                        to_be_attacked.name,
                        defend_limit,
                    )
                    defending_armies = self.retrieve_numerical_input(query, defend_limit)
                else:
                    defending_armies = defend_limit
                    army_tag = 'army' if defending_armies == 1 else 'armies'
                    self.print_slow('\n{} is defending {} with {} {}.'.format(
                        defending_player.name,
                        to_be_attacked.name,
                        defending_armies,
                        army_tag,
                    ))
                to_attack_with_count_before = to_attack_from.occupying_armies
                to_be_attacked_count_before = to_be_attacked.occupying_armies
                self.attack_territory(to_attack_from, to_be_attacked, attacking_armies, defending_armies)

                # Attacker is victorious
                if to_be_attacked.occupying_player == player:
                    self.print_slow('\n{} won {} and moved in {} armies.'.format(
                        player.name,
                        to_be_attacked.name,
                        to_be_attacked.occupying_armies,
                    ))
                    move_limit = to_attack_from.occupying_armies - 1
                    if len(self.players) == 1:
                        return
                    if move_limit > 0:
                        if player.is_human:
                            query = 'How many additional armies would you like to move there? (up to {}) '.format(
                                    move_limit,
                            )
                            num_armies = self.retrieve_numerical_input(query, move_limit)
                        else:
                            num_armies = player.armies_to_move(to_attack_from, move_limit)
                            army_tag = 'army' if num_armies == 1 else 'armies'
                            self.print_slow('\n{} moved {} additional {} to {}.'.format(
                                player.name,
                                num_armies,
                                army_tag,
                                to_be_attacked.name,
                            ))
                        self.fortify_territory(to_attack_from, to_be_attacked, num_armies)
                    break

                attack_loss = to_attack_with_count_before - to_attack_from.occupying_armies
                defend_loss = to_be_attacked_count_before - to_be_attacked.occupying_armies
                print('\n')
                if attack_loss > 0 and defend_loss == 0:
                    self.print_battle_report(to_attack_from, attack_loss)
                elif defend_loss > 0 and attack_loss == 0:
                    self.print_battle_report(to_be_attacked, defend_loss)
                else:
                    self.print_battle_report(to_attack_from, attack_loss)
                    self.print_battle_report(to_be_attacked, defend_loss)

                self.print_slow('\nRemaining attacking armies in {}: {}\nRemaining defending armies in {}: {}'.format(
                    to_attack_from.name,
                    to_attack_from.occupying_armies,
                    to_be_attacked.name,
                    to_be_attacked.occupying_armies,
                ))

                # Attacker is defeated
                if to_attack_from.occupying_armies == 1:
                    self.print_slow('\n{} suffered maximum casualties and can no longer attack this territory.'.format(
                        player_address,
                    ))
                    break

                # Choose to continue the fight
                else:
                    if player.is_human:
                        query = 'Would you like to continue the battle? (1 = yes, 0 = no) '
                        fight = self.retrieve_numerical_input(query, 1)
                    else:
                        fight = 1 if to_attack_from.occupying_armies >= to_be_attacked.occupying_armies else 0
                    if fight == 0:
                        if not player.is_human:
                            self.print_slow('\n{} is not continuing the battle.'.format(player.name))
                        break
            # Display risk map following battle sequence
            self.draw_risk_map()
            territories_for_attack = self.get_territories_for_attack(player)
            if len(territories_for_attack) == 0:
                break
            if player.is_human:
                query = 'Would you like to attack another territory? (1 = yes, 0 = no) '
                attack = self.retrieve_numerical_input(query, 1)
            else:
                attack_route = player.choose_attack_route(territories_for_attack, 0)
                attack = 1 if attack_route else 0

        # Phase 3: fortify
        territories_to_fortify = self.get_territories_to_fortify(player)
        fortify_route = None

        fortify = 0
        if len(territories_to_fortify) > 0:
            if player.is_human:
                self.print_slow('\nPHASE 3: FORTIFY\n')
                query = 'Would you like to fortify any territories? (1 = yes, 0 = no) '
                fortify = self.retrieve_numerical_input(query, 1)
            else:
                fortify_route = player.choose_fortify_route()
                fortify = 1 if fortify_route else 0
        if fortify == 1:
            if player.is_human:
                self.print_territory_info(territories_to_fortify)
                query = 'Select the number of the territory you\'d like to move armies to: '
                index_to = self.retrieve_numerical_input(query, len(territories_to_fortify) - 1)
                territory_to = territories_to_fortify[index_to]
                occupied_territories = self.get_surrounding_territories(player, territory_to)
                self.print_territory_info(occupied_territories)
                query = 'Select the number of the territory you\'d like to move armies from: '
                index_from = self.retrieve_numerical_input(query, len(occupied_territories) - 1)
                territory_from = occupied_territories[index_from]
                fortify_limit = territory_from.occupying_armies - 1
                query = 'How many armies would you like to move from {} to {}? (up to {}) '.format(
                    territory_from.name,
                    territory_to.name,
                    fortify_limit,
                )
                num_armies = self.retrieve_numerical_input(query, fortify_limit)
            else:
                territory_from = fortify_route[0]
                territory_to = fortify_route[1]
                num_armies = territory_from.occupying_armies // 2
                army_tag = 'army' if num_armies == 1 else 'armies'
                if num_armies > 0:
                    self.print_slow('\n{} fortified {} with {} {} from {}.'.format(
                        player.name,
                        territory_to.name,
                        num_armies,
                        army_tag,
                        territory_from.name,
                    ))
            self.fortify_territory(territory_from, territory_to, num_armies)
        self.print_slow('\nEnd of turn.\n')

    def update_risk_map(self):
        node_list = list(self.risk_map.nodes)
        for territory in self.all_territories:
            # Change color to reflect occupation
            if territory.occupying_player:
                node_index = node_list.index(territory.name)
                self.node_colors[node_index] = self.player_colors[territory.occupying_player.name]
            army_tag = 'army' if territory.occupying_armies == 1 else 'armies'
            occupier = '' if not territory.occupying_player else territory.occupying_player.name
            # Label territory with name, army count, and occupying player
            self.labels[territory.name] = '{}\n{} {}\n{}'.format(
                territory.name,
                territory.occupying_armies,
                army_tag,
                occupier,
            )

    @staticmethod
    # Accepts positive or negative integer to increase or decrease armies in a territory
    def change_armies(territory, num_armies):
        territory.occupying_armies += num_armies

    @staticmethod
    # Finds list of neighbors controlled by player
    def get_surrounding_territories(player, territory):
        surrounding_territories = []
        for neighbor in territory.neighbors:
            if neighbor.occupying_player == player and neighbor.occupying_armies > 1:
                surrounding_territories.append(neighbor)
        return surrounding_territories

    @staticmethod
    def get_territories_for_attack(player):
        territories_for_attack = []
        for territory in player.controlled_territories:
            if territory.occupying_armies > 1:
                for neighbor in territory.neighbors:
                    if neighbor.occupying_player != player and neighbor not in territories_for_attack:
                        territories_for_attack.append(neighbor)
        return territories_for_attack

    @staticmethod
    def get_territories_to_fortify(player):
        territories_to_fortify = []
        for territory in player.controlled_territories:
            if territory.occupying_armies > 1:
                for neighbor in territory.neighbors:
                    if neighbor.occupying_player == player and neighbor not in territories_to_fortify:
                        territories_to_fortify.append(neighbor)
        return territories_to_fortify

    @staticmethod
    def print_battle_report(losing_territory, loss_amount):
        army_description = 'armies' if loss_amount > 1 else 'army'
        print('{} lost {} {} from {}.'.format(
            losing_territory.occupying_player,
            loss_amount,
            army_description,
            losing_territory.name,
        ))

    @staticmethod
    def print_slow(output_string):
        print(output_string)
        sleep(1.0)

    @staticmethod
    def print_territory_info(territory_list):
        print('\n')
        for i, territory in enumerate(territory_list):
            occupant = territory.occupying_player.name if territory.occupying_player else 'unoccupied'
            print('[{}] {}, {} -- {}, {} armies'.format(
                i,
                territory.name,
                territory.continent,
                occupant,
                territory.occupying_armies,
            ))
        print('\n')

    @staticmethod
    def retrieve_numerical_input(query_string, n):
        user_input = input(query_string)
        while not (user_input.isnumeric() and 0 <= int(user_input) <= n):
            print("Oops, looks like that wasn't a valid number.")
            user_input = input(query_string)
        return int(user_input)

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
