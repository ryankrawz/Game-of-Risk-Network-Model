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

    # Allocates half of the armies if current territory still under threat
    def armies_to_move(self, territory_from, move_limit):
        for neighbor in territory_from.neighbors:
            if neighbor.occupying_player != self:
                return move_limit // 2
        return move_limit

    def choose_attack_route(self, territory_list, reinforcements):
        attack_route = None
        largest_difference = 0
        # Check for territory with smallest army count relative to attacker
        for territory in territory_list:
            for neighbor in territory.neighbors:
                if neighbor.occupying_player == self:
                    army_difference = neighbor.occupying_armies + reinforcements - territory.occupying_armies
                    if army_difference >= 0 and (not attack_route or army_difference > largest_difference):
                        attack_route = (neighbor, territory)
                        largest_difference = army_difference
        return attack_route

    def choose_fortify_route(self):
        fortify_route = None
        largest_disparity = 0
        # Prioritize territories with largest enemy army count differentials to receive fortifications
        territories_highest_differentials = sorted(
            self.controlled_territories,
            key=self.army_count_differential,
            reverse=True,
        )
        # Prioritize territories with smallest enemy army count differentials to provide fortifications
        i = len(territories_highest_differentials) - 1
        while i >= 0:
            for neighbor in territories_highest_differentials[i].neighbors:
                if neighbor.occupying_player == self:
                    current_disparity = i - territories_highest_differentials.index(neighbor)
                    if ((not fortify_route or current_disparity > largest_disparity) and
                       self.army_count_differential(neighbor) > 0):
                        fortify_route = (territories_highest_differentials[i], neighbor)
                        largest_disparity = current_disparity
            i -= 1
        return fortify_route

    def claim_territory(self, available_territories):
        # Territories have already been claimed
        if len(self.controlled_territories) > 0:
            empty_neighbors = self.get_unoccupied_neighbors(self.controlled_territories)
            # Neighbors to controlled territories are unoccupied
            if len(empty_neighbors) > 0:
                return self.lowest_neighbor_count(empty_neighbors)
        return self.lowest_neighbor_count(available_territories)

    def enemy_adjacent_territories(self, territory_list):
        adjacent_to_enemy = []
        for territory in territory_list:
            for neighbor in territory.neighbors:
                if neighbor.occupying_player != self and territory not in adjacent_to_enemy:
                    adjacent_to_enemy.append(territory)
        return adjacent_to_enemy

    # Determine territory with fewest armies
    def lowest_army_count(self):
        fewest_armies = None
        for territory in self.controlled_territories:
            if not fewest_armies or territory.occupying_armies < fewest_armies.occupying_armies:
                fewest_armies = territory
        return fewest_armies

    def reinforce_initial(self):
        reinforced_territory_names = []
        adjacent_to_enemy = self.enemy_adjacent_territories(self.controlled_territories)
        # Distribute an equal number of armies to all territories bordering an enemy
        while self.army_count > 0:
            current_territory = adjacent_to_enemy[self.army_count % len(adjacent_to_enemy)]
            current_territory.occupying_armies += 1
            self.army_count -= 1
            if current_territory.name not in reinforced_territory_names:
                reinforced_territory_names.append(current_territory.name)
        return reinforced_territory_names

    @staticmethod
    # Calculates total number advantage for all surrounding enemies of a territory
    def army_count_differential(territory):
        differential = 0
        for neighbor in territory.neighbors:
            if neighbor.occupying_player != territory.occupying_player:
                differential += neighbor.occupying_armies
        return differential

    @staticmethod
    def get_unoccupied_neighbors(territory_list):
        unoccupied_neighbors = []
        for territory in territory_list:
            for neighbor in territory.neighbors:
                if neighbor.is_empty() and neighbor not in unoccupied_neighbors:
                    unoccupied_neighbors.append(neighbor)
        return unoccupied_neighbors

    @staticmethod
    # Determine territory with fewest neighboring territories
    def lowest_neighbor_count(territory_list):
        fewest_neighbors = None
        for territory in territory_list:
            if not fewest_neighbors or len(territory.neighbors) < len(fewest_neighbors.neighbors):
                fewest_neighbors = territory
        return fewest_neighbors


class HumanPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.is_human = True
