class Player:
    def __init__(self, name):
        self.name = name
        self.controlled_territories = []
        self.cards = []
        self.army_count = 0


class ComputerPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.is_human = False


class HumanPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.is_human = True


class Territory:
    def __init__(self, name, continent, neighbors):
        self.name = name
        self.continent = continent
        self.neighbors = neighbors
        self.occupying_player = None
        self.occupying_armies = 0


class GameOfRisk:
    def __init__(self, game_file):
        self.title = ''
        self.players = []
        self.eliminated_players = []
        self.all_territories = []
        # TODO
        self.card_deck = None
        self.total_card_trades = 0
        # TODO
        self.dice = None
        with open(game_file, 'r') as f:
            i = 0
            info = f.readline()
            while info:
                if i == 0:
                    self.title = info.strip()
                elif i == 1:
                    self.set_players(info)
                elif i == 2:
                    self.set_players(info, is_human=False)
                else:
                    self.set_territory(info)
                info = f.readline()
                i += 1
            if i < 4:
                raise Exception('uploaded file does not contain enough information to create a game')

    def set_players(self, line_info, is_human=True):
        player_type = 'human' if is_human else 'computer'
        info_items = line_info.split('|')
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
            raise Exception('{} {} players were declared but only {} names were provided'.format(
                num_players,
                player_type,
                i - 1,
            ))
        if i < len(info_items):
            raise Exception('{} {} players were declared but {} too many names were provided'.format(
                num_players,
                player_type,
                len(info_items) - i,
            ))

    def set_territory(self, line_info):
        info_items = line_info.split('|')
        neighbor_list = []
        try:
            for neighbor in info_items[2:]:
                neighbor_list.append(neighbor.strip())
            self.all_territories.append(Territory(info_items[0].strip(), info_items[1].strip(), neighbor_list))
        except IndexError:
            raise Exception('all territories must have at least one neighbor')
