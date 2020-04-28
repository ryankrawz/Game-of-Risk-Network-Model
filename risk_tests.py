from unittest import mock, TestCase

from game_of_risk import GameOfRisk


class ComputerPlayerTest(TestCase):
    def setUp(self):
        super().setUp()
        self.print_patch = mock.patch('builtins.print', side_effect=lambda s: None)
        self.print_patch.start()
        self.slow_patch = mock.patch('game_of_risk.GameOfRisk.print_slow', side_effect=lambda t: None)
        self.slow_patch.start()
        self.draw_patch = mock.patch('game_of_risk.GameOfRisk.draw_risk_map', side_effect=lambda: None)
        self.draw_patch.start()
        self.g = GameOfRisk('test_games/world_war_2_test.txt')
        self.stalin = self.g.players[4]
        self.hirohito = self.g.players[5]
        self.germany = self.g.all_territories[5]
        self.switzerland = self.g.all_territories[6]
        self.italy = self.g.all_territories[7]
        self.ussr = self.g.all_territories[19]
        self.latvia = self.g.all_territories[20]
        self.korea = self.g.all_territories[25]
        self.switzerland.occupying_player = self.stalin

    def tearDown(self):
        super().tearDown()
        self.print_patch.stop()
        self.slow_patch.stop()
        self.draw_patch.stop()

    def test_armies_to_move_all_friendly(self):
        for neighbor in self.switzerland.neighbors:
            neighbor.occupying_player = self.stalin
        num_armies = self.stalin.armies_to_move(self.switzerland, 10)
        self.assertEqual(num_armies, 10)

    def test_armies_to_move_with_enemy(self):
        for neighbor in self.switzerland.neighbors:
            neighbor.occupying_player = self.stalin
        self.switzerland.neighbors[3].occupying_player = self.hirohito
        num_armies = self.stalin.armies_to_move(self.switzerland, 10)
        self.assertEqual(num_armies, 5)

    def test_choose_attack_route_all_friendly(self):
        self.switzerland.occupying_player = self.hirohito
        self.switzerland.occupying_armies = 7
        neighbor_armies = [4, 1, 5, 2]
        for i in range(len(self.switzerland.neighbors)):
            self.switzerland.neighbors[i].occupying_player = self.hirohito
            self.switzerland.neighbors[i].occupying_armies = neighbor_armies[i]
        attack_route = self.stalin.choose_attack_route([self.switzerland], 3)
        self.assertIsNone(attack_route)

    def test_choose_attack_route_with_enemy(self):
        self.switzerland.occupying_player = self.hirohito
        self.switzerland.occupying_armies = 1
        neighbor_armies = [4, 7, 5, 2]
        for i in range(len(self.switzerland.neighbors)):
            if i == 1:
                self.switzerland.neighbors[i].occupying_player = self.hirohito
            else:
                self.switzerland.neighbors[i].occupying_player = self.stalin
            self.switzerland.neighbors[i].occupying_armies = neighbor_armies[i]
        attack_route = self.stalin.choose_attack_route([self.switzerland], 3)
        self.assertEqual(attack_route, (self.switzerland.neighbors[2], self.switzerland))

    def test_choose_fortify_route_no_connection(self):
        self.switzerland.occupying_armies = 1
        self.korea.occupying_player = self.stalin
        self.korea.occupying_armies = 1
        self.stalin.controlled_territories = [self.switzerland, self.korea]
        switzerland_neighbor_armies = [3, 7, 8, 4]
        for i in range(len(self.switzerland.neighbors)):
            self.switzerland.neighbors[i].occupying_player = self.hirohito
            self.switzerland.neighbors[i].occupying_armies = switzerland_neighbor_armies[i]
        korea_neighbor_armies = [2, 6, 5]
        for i in range(len(self.korea.neighbors)):
            self.korea.neighbors[i].occupying_player = self.hirohito
            self.korea.neighbors[i].occupying_armies = korea_neighbor_armies[i]
        differential = self.stalin.army_count_differential(self.switzerland)
        self.assertEqual(differential, 22)
        fortify_route = self.stalin.choose_fortify_route()
        self.assertIsNone(fortify_route)

    def test_choose_fortify_route_higher_differential(self):
        self.switzerland.occupying_armies = 1
        self.germany.occupying_player = self.stalin
        self.germany.occupying_armies = 1
        self.italy.occupying_player = self.stalin
        self.italy.occupying_armies = 1
        self.stalin.controlled_territories = [self.switzerland, self.germany, self.italy]
        germany_neighbor_armies = [2, 4, 3, 5, 1, 3, 9, 1]
        for i in range(len(self.germany.neighbors)):
            if self.germany.neighbors[i] != self.switzerland:
                self.germany.neighbors[i].occupying_player = self.hirohito
                self.germany.neighbors[i].occupying_armies = germany_neighbor_armies[i]
        italy_neighbor_armies = [8, 5, 7, 2, 2, 3]
        for i in range(len(self.italy.neighbors)):
            if self.italy.neighbors[i] != self.switzerland:
                self.italy.neighbors[i].occupying_player = self.hirohito
                self.italy.neighbors[i].occupying_armies = italy_neighbor_armies[i]
        differential = self.stalin.army_count_differential(self.italy)
        self.assertEqual(differential, 22)
        fortify_route = self.stalin.choose_fortify_route()
        self.assertEqual(fortify_route, (self.switzerland, self.germany))

    def test_claim_territory_empty_neighbors(self):
        self.stalin.controlled_territories = [self.switzerland]
        claimed_territory = self.stalin.claim_territory(self.switzerland.neighbors)
        self.assertEqual(claimed_territory, self.switzerland.neighbors[1])

    def test_claim_territory_no_empty_neighbors(self):
        self.stalin.controlled_territories = [self.switzerland]
        for neighbor in self.switzerland.neighbors:
            neighbor.occupying_player = self.hirohito
            neighbor.occupying_armies = 1
        claimed_territory = self.stalin.claim_territory([self.latvia, self.korea, self.ussr])
        self.assertEqual(claimed_territory, self.korea)

    def test_enemy_adjacent_territories_all_friendly(self):
        for neighbor in self.switzerland.neighbors:
            neighbor.occupying_player = self.stalin
        for neighbor in self.germany.neighbors:
            neighbor.occupying_player = self.stalin
        for neighbor in self.italy.neighbors:
            neighbor.occupying_player = self.stalin
        enemy_adjacent = self.stalin.enemy_adjacent_territories([self.switzerland, self.germany, self.italy])
        self.assertEqual(enemy_adjacent, [])

    def test_enemy_adjacent_territories_bordering_enemy(self):
        for neighbor in self.switzerland.neighbors:
            neighbor.occupying_player = self.stalin
        for neighbor in self.germany.neighbors:
            neighbor.occupying_player = self.stalin
        for neighbor in self.italy.neighbors:
            neighbor.occupying_player = self.stalin
        self.germany.neighbors[4].occupying_player = self.hirohito
        self.italy.neighbors[5].occupying_player = self.hirohito
        enemy_adjacent = self.stalin.enemy_adjacent_territories([self.switzerland, self.germany, self.italy])
        self.assertEqual(enemy_adjacent, [self.germany, self.italy])

    def test_lowest_army_count_same(self):
        self.stalin.controlled_territories = [self.switzerland, self.germany, self.italy]
        for territory in self.stalin.controlled_territories:
            territory.occupying_armies = 2
        lowest_army_territory = self.stalin.lowest_army_count()
        self.assertEqual(lowest_army_territory, self.switzerland)

    def test_lowest_army_count_different(self):
        self.stalin.controlled_territories = [self.switzerland, self.germany, self.italy]
        army_counts = [2, 3, 1]
        for i in range(len(self.stalin.controlled_territories)):
            self.stalin.controlled_territories[i].occupying_armies = army_counts[i]
        lowest_army_territory = self.stalin.lowest_army_count()
        self.assertEqual(lowest_army_territory, self.italy)

    def test_reinforce_initial(self):
        self.stalin.army_count = 20
        for neighbor in self.switzerland.neighbors:
            neighbor.occupying_player = self.stalin
        for neighbor in self.germany.neighbors:
            neighbor.occupying_player = self.stalin
        for neighbor in self.italy.neighbors:
            neighbor.occupying_player = self.stalin
        self.stalin.controlled_territories = [self.switzerland, self.germany, self.italy]
        self.germany.neighbors[4].occupying_player = self.hirohito
        self.italy.neighbors[5].occupying_player = self.hirohito
        reinforce_names = self.stalin.reinforce_initial()
        self.assertEqual(self.germany.occupying_armies, 10)
        self.assertEqual(self.italy.occupying_armies, 10)
        self.assertEqual(reinforce_names, ['Germany', 'Italy'])

    def test_get_unoccupied_neighbors(self):
        self.germany.occupying_player = self.stalin
        self.germany.occupying_armies = 1
        self.italy.occupying_player = self.stalin
        self.italy.occupying_armies = 1
        unoccupied_neighbors = self.stalin.get_unoccupied_neighbors([self.switzerland, self.germany, self.italy])
        unoccupied_names = [t.name for t in unoccupied_neighbors]
        self.assertEqual(unoccupied_names, ['France', 'Austria', 'Belgium', 'Netherlands', 'Denmark', 'Poland',
                                            'Czechoslovakia', 'Switzerland', 'Yugoslavia', 'Albania', 'Greece'])

    def test_lowest_neighbor_count(self):
        fewest_neighbor_territory = self.stalin.lowest_neighbor_count([self.switzerland, self.germany, self.italy])
        self.assertEqual(fewest_neighbor_territory, self.switzerland)


class InputUtilitiesTest(TestCase):
    def setUp(self):
        super().setUp()
        self.print_patch = mock.patch('builtins.print', side_effect=lambda s: None)
        self.print_patch.start()
        self.slow_patch = mock.patch('game_of_risk.GameOfRisk.print_slow', side_effect=lambda t: None)
        self.slow_patch.start()
        self.draw_patch = mock.patch('game_of_risk.GameOfRisk.draw_risk_map', side_effect=lambda: None)
        self.draw_patch.start()

    def tearDown(self):
        super().tearDown()
        self.print_patch.stop()
        self.slow_patch.stop()
        self.draw_patch.stop()

    @mock.patch('builtins.input')
    def test_retrieve_numerical_input(self, input_mock):
        input_mock.side_effect = ['-1', '10', 'xyz', '5', '4']
        query = 'How many armies? (Up to {}) '.format(4)
        input_num = GameOfRisk.retrieve_numerical_input(query, 4)
        self.assertEqual(input_num, 4)


class RevolutionaryWarAllHumanTest(TestCase):
    def setUp(self):
        super().setUp()
        self.print_patch = mock.patch('builtins.print', side_effect=lambda s: None)
        self.print_patch.start()
        self.slow_patch = mock.patch('game_of_risk.GameOfRisk.print_slow', side_effect=lambda t: None)
        self.slow_patch.start()
        self.draw_patch = mock.patch('game_of_risk.GameOfRisk.draw_risk_map', side_effect=lambda: None)
        self.draw_patch.start()
        self.g = GameOfRisk('test_games/revolutionary_war_all_human.txt')
        self.america = self.g.players[0]
        self.france = self.g.players[1]
        self.great_britain = self.g.players[2]
        self.massachusetts = self.g.all_territories[3]
        self.new_york = self.g.all_territories[2]
        self.maryland = self.g.all_territories[9]
        self.virginia = self.g.all_territories[10]
        self.place_armies()

    def tearDown(self):
        super().tearDown()
        self.print_patch.stop()
        self.slow_patch.stop()
        self.draw_patch.stop()

    @mock.patch('builtins.input')
    def place_armies(self, input_mock):
        input_mock.side_effect = ['0', '8', '11', '0', '6', '8', '1', '3', '5', '1', '2',
                                  '2', '1', '0', '2', '30', '0', '15', '4', '15', '3', '31']
        self.g.initial_army_placement()

    def test_initial_army_placement(self):
        self.assertEqual(self.massachusetts.occupying_player, self.america)
        self.assertEqual(self.massachusetts.occupying_armies, 31)
        self.assertEqual(self.new_york.occupying_player, self.france)
        self.assertEqual(self.new_york.occupying_armies, 16)
        self.assertEqual(self.maryland.occupying_player, self.france)
        self.assertEqual(self.maryland.occupying_armies, 16)
        self.assertEqual(self.virginia.occupying_player, self.great_britain)
        self.assertEqual(self.virginia.occupying_armies, 32)

    @mock.patch('game_of_risk.GameOfRisk.calculate_reinforcements')
    @mock.patch('game_of_risk.GameOfRisk.roll_dice')
    @mock.patch('builtins.input')
    def test_turn_single_attack_no_fortify(self, input_mock, roll_dice_mock, reinforcements_mock):
        input_mock.side_effect = ['2', '3', '1', '0', '0', '3', '2', '0', '0', '0']
        roll_dice_mock.side_effect = [[5, 3, 1], [5, 2]]
        reinforcements_mock.return_value = 3
        self.g.turn(self.america)
        self.assertEqual(self.massachusetts.occupying_armies, 33)
        self.assertEqual(self.new_york.occupying_armies, 15)

    @mock.patch('game_of_risk.GameOfRisk.calculate_reinforcements')
    @mock.patch('game_of_risk.GameOfRisk.roll_dice')
    @mock.patch('builtins.input')
    def test_turn_full_attack_with_fortify(self, input_mock, roll_dice_mock, reinforcements_mock):
        input_mock.side_effect = ['3', '3', '1', '0', '0', '3', '2', '1', '3', '2', '1', '3', '2',
                                  '1', '3', '2', '1', '3', '2', '1', '3', '2', '1', '3', '2', '1',
                                  '3', '2', '10', '0', '1', '0', '0', '2']
        roll_dice_mock.side_effect = [[6, 5, 4], [1, 2], [6, 5, 4], [1, 2], [6, 5, 4], [1, 2],
                                      [6, 5, 4], [1, 2], [6, 5, 4], [1, 2], [6, 5, 4], [1, 2],
                                      [6, 5, 4], [1, 2], [6, 5, 4], [1, 2]]
        reinforcements_mock.return_value = 3
        self.g.turn(self.great_britain)
        self.assertEqual(self.virginia.occupying_armies, 20)
        self.assertEqual(self.maryland.occupying_player, self.great_britain)
        self.assertEqual(self.maryland.occupying_armies, 15)

    @mock.patch('game_of_risk.GameOfRisk.print_battle_report')
    @mock.patch('game_of_risk.GameOfRisk.calculate_reinforcements')
    @mock.patch('game_of_risk.GameOfRisk.roll_dice')
    @mock.patch('builtins.input')
    def test_turn_victory(self, input_mock, roll_dice_mock, reinforcements_mock, battle_report_mock):
        input_mock.side_effect = ['0', '3', '1', '0', '0', '1', '1']
        roll_dice_mock.side_effect = [[3], [1]]
        reinforcements_mock.return_value = 3
        self.g.players.remove(self.great_britain)
        self.g.eliminated_players.append(self.great_britain)
        maine = self.g.all_territories[0]
        new_hampshire = self.g.all_territories[1]
        for t in self.g.all_territories[2:]:
            t.occupying_player = self.france
            t.occupying_armies = 1
        maine.occupying_armies = 1
        new_hampshire.occupying_player = self.france
        new_hampshire.occupying_armies = 10
        self.america.controlled_territories = [maine]
        self.france.controlled_territories = self.g.all_territories[1:]
        self.g.turn(self.france)
        self.assertEqual(len(self.g.players), 1)
        self.assertEqual(len(self.g.eliminated_players), 2)
        battle_report_mock.assert_not_called()


class WorldWar2Test(TestCase):
    def setUp(self):
        super().setUp()
        self.print_patch = mock.patch('builtins.print', side_effect=lambda s: None)
        self.print_patch.start()
        self.slow_patch = mock.patch('game_of_risk.GameOfRisk.print_slow', side_effect=lambda t: None)
        self.slow_patch.start()
        self.draw_patch = mock.patch('game_of_risk.GameOfRisk.draw_risk_map', side_effect=lambda: None)
        self.draw_patch.start()
        self.g = GameOfRisk('test_games/world_war_2_test.txt')
        self.roosevelt = self.g.players[0]
        self.churchill = self.g.players[1]
        self.great_britain = self.g.all_territories[0]
        self.france = self.g.all_territories[1]

    def tearDown(self):
        super().tearDown()
        self.print_patch.stop()
        self.slow_patch.stop()
        self.draw_patch.stop()

    def calibrate_britain_and_france(self, britain_player, britain_count, france_player, france_count):
        britain_player.controlled_territories.append(self.great_britain)
        self.great_britain.occupying_player = britain_player
        self.great_britain.occupying_armies = britain_count
        france_player.controlled_territories.append(self.france)
        self.france.occupying_player = france_player
        self.france.occupying_armies = france_count

    def test_constructor(self):
        correct = 'World War II\nPlaying: Roosevelt, Churchill, Hitler, Mussolini, Stalin, ' \
                  'Hirohito\nEliminated: \nTerritories:\nGreat Britain, Europe --> France, ' \
                  'Belgium, Netherlands, Norway\nFrance, Europe --> Great Britain, Belgium, ' \
                  'Germany, Switzerland, Italy\nBelgium, Europe --> Netherlands, France, ' \
                  'Germany, Great Britain\nNetherlands, Europe --> Belgium, Great Britain, ' \
                  'Germany\nNorway, Europe --> Great Britain, Denmark\nGermany, Europe --> ' \
                  'France, Belgium, Netherlands, Denmark, Poland, Czechoslovakia, Austria, ' \
                  'Switzerland\nSwitzerland, Europe --> Germany, France, Italy, Austria\nItaly, ' \
                  'Europe --> France, Switzerland, Austria, Yugoslavia, Albania, Greece\nAustria, ' \
                  'Europe --> Switzerland, Germany, Czechoslovakia, Hungary, Yugoslavia, ' \
                  'Italy\nYugoslavia, Europe --> Italy, Austria, Hungary, Romania, Bulgaria, ' \
                  'Greece, Albania\nAlbania, Europe --> Italy, Yugoslavia, Greece\nGreece, ' \
                  'Europe --> Italy, Albania, Yugoslavia, Bulgaria\nDenmark, Europe --> Norway, ' \
                  'Germany\nPoland, Europe --> Germany, East Prussia, Lithuania, Latvia, USSR, ' \
                  'Romania, Czechoslovakia\nCzechoslovakia, Europe --> Germany, Poland, Romania, ' \
                  'Hungary, Austria\nRomania, Europe --> Hungary, Czechoslovakia, Poland, USSR, ' \
                  'Bulgaria, Yugoslavia\nHungary, Europe --> Austria, Czechoslovakia, Romania, ' \
                  'Yugoslavia\nBulgaria, Europe --> Yugoslavia, Romania, Greece\nEstonia, ' \
                  'Europe --> USSR, Latvia\nUSSR, Europe --> Estonia, Latvia, Poland, Romania, ' \
                  'Manchuria, Japan\nLatvia, Europe --> Estonia, USSR, Poland, Lithuania, ' \
                  'East Prussia\nLithuania, Europe --> Latvia, Poland, East Prussia\nEast ' \
                  'Prussia, Europe --> Latvia, Lithuania, Poland\nManchuria, Asia --> USSR, ' \
                  'Japan, Korea, China, Mongolia\nJapan, Asia --> USSR, Korea, China\nKorea, ' \
                  'Asia --> Japan, China, Manchuria\nChina, Asia --> Mongolia, Manchuria, ' \
                  'Korea, Japan, Philippines, French Indo-China, Burma\nMongolia, Asia --> ' \
                  'USSR, Manchuria, China\nPhilippines, Asia --> China, Malaya\nFrench ' \
                  'Indo-China, Asia --> Siam, Burma, China, Malaya\nBurma, Asia --> China, ' \
                  'French Indo-China, Siam\nSiam, Asia --> Burma, French Indo-China, ' \
                  'Malaya\nMalaya, Asia --> Siam, French Indo-China, Dutch East Indies, ' \
                  'Philippines\nDutch East Indies, Asia --> Malaya, New Guinea\nNew Guinea, ' \
                  'Asia --> Dutch East Indies'
        self.assertEqual(str(self.g), correct)

    def test_player_colors(self):
        correct = {'Roosevelt': '#e66a6a', 'Churchill': '#6ab2e6', 'Hitler': '#97e699',
                   'Mussolini': '#f3f57a', 'Stalin': '#edb277', 'Hirohito': '#d39ef0'}
        self.assertEqual(self.g.player_colors, correct)

    def test_allocate_armies(self):
        self.assertEqual(self.roosevelt.army_count, 20)

    @mock.patch('game_of_risk.GameOfRisk.decide_battle')
    def test_attack_territory_attacker_wins_defender_occupies(self, decide_battle_mock):
        decide_battle_mock.return_value = 1
        self.calibrate_britain_and_france(self.roosevelt, 3, self.churchill, 3)
        self.g.attack_territory(self.great_britain, self.france, 1, 1)
        self.assertEqual(self.france.occupying_armies, 2)

    @mock.patch('game_of_risk.GameOfRisk.decide_battle')
    def test_attack_territory_attacker_wins_defender_leaves(self, decide_battle_mock):
        decide_battle_mock.return_value = 1
        self.calibrate_britain_and_france(self.roosevelt, 3, self.churchill, 1)
        self.g.attack_territory(self.great_britain, self.france, 1, 1)
        self.assertEqual(self.france.occupying_armies, 1)
        self.assertEqual(self.france.occupying_player, self.roosevelt)
        self.assertIn(self.churchill, self.g.eliminated_players)
        self.assertNotIn(self.churchill, self.g.players)

    @mock.patch('game_of_risk.GameOfRisk.decide_battle')
    def test_attack_territory_defender_wins(self, decide_battle_mock):
        decide_battle_mock.return_value = -1
        self.calibrate_britain_and_france(self.roosevelt, 3, self.churchill, 3)
        self.g.attack_territory(self.great_britain, self.france, 1, 1)
        self.assertEqual(self.great_britain.occupying_armies, 2)

    @mock.patch('game_of_risk.GameOfRisk.decide_battle')
    def test_attack_territory_tie(self, decide_battle_mock):
        decide_battle_mock.return_value = 0
        self.calibrate_britain_and_france(self.roosevelt, 3, self.churchill, 3)
        self.g.attack_territory(self.great_britain, self.france, 1, 1)
        self.assertEqual(self.great_britain.occupying_armies, 2)
        self.assertEqual(self.france.occupying_armies, 2)

    @mock.patch('game_of_risk.GameOfRisk.determine_card_match')
    def test_calculate_reinforcements_few_territories(self, card_match_mock):
        card_match_mock.return_value = 0
        self.roosevelt.controlled_territories = self.g.all_territories[:3]
        reinforcements = self.g.calculate_reinforcements(self.roosevelt)
        self.assertEqual(reinforcements, 3)

    @mock.patch('game_of_risk.GameOfRisk.determine_card_match')
    def test_calculate_reinforcements_many_territories(self, card_match_mock):
        card_match_mock.return_value = 0
        self.roosevelt.controlled_territories = self.g.all_territories[:20]
        reinforcements = self.g.calculate_reinforcements(self.roosevelt)
        self.assertEqual(reinforcements, 6)

    @mock.patch('game_of_risk.GameOfRisk.roll_dice')
    def test_decide_battle_tie(self, roll_dice_mock):
        roll_dice_mock.return_value = [5, 4]
        armies_defeated = self.g.decide_battle(2, 2)
        self.assertEqual(armies_defeated, -2)

    @mock.patch('game_of_risk.GameOfRisk.roll_dice')
    def test_decide_battle_attack_win_2(self, roll_dice_mock):
        roll_dice_mock.side_effect = [[6, 5, 4], [3, 2]]
        armies_defeated = self.g.decide_battle(3, 2)
        self.assertEqual(armies_defeated, 2)

    @mock.patch('game_of_risk.GameOfRisk.roll_dice')
    def test_decide_battle_attack_win_1(self, roll_dice_mock):
        roll_dice_mock.side_effect = [[6, 5, 4], [2]]
        armies_defeated = self.g.decide_battle(3, 1)
        self.assertEqual(armies_defeated, 1)

    @mock.patch('game_of_risk.GameOfRisk.roll_dice')
    def test_decide_battle_defense_win_2(self, roll_dice_mock):
        roll_dice_mock.side_effect = [[2, 1], [3, 2]]
        armies_defeated = self.g.decide_battle(2, 2)
        self.assertEqual(armies_defeated, -2)

    @mock.patch('game_of_risk.GameOfRisk.roll_dice')
    def test_decide_battle_defense_win_1(self, roll_dice_mock):
        roll_dice_mock.side_effect = [[1], [3, 2]]
        armies_defeated = self.g.decide_battle(1, 2)
        self.assertEqual(armies_defeated, -1)

    def test_determine_card_match_none(self):
        self.roosevelt.cards = [1, 2, 1, 3]
        armies_from_cards = self.g.determine_card_match(self.roosevelt, 2)
        self.assertEqual(armies_from_cards, 0)
        self.assertEqual(self.roosevelt.cards, [1, 2, 1, 3, 2])

    def test_determine_card_match_exists(self):
        self.roosevelt.cards = [1, 2, 1, 3]
        current_count = len(self.g.card_deck.cards)
        armies_from_cards = self.g.determine_card_match(self.roosevelt, 1)
        self.assertEqual(armies_from_cards, 4)
        self.assertEqual(self.roosevelt.cards, [2, 3])
        self.assertEqual(len(self.g.card_deck.cards), current_count + 3)

    def test_fortify_territory(self):
        self.calibrate_britain_and_france(self.roosevelt, 3, self.roosevelt, 3)
        self.g.fortify_territory(self.great_britain, self.france, 1)
        self.assertEqual(self.great_britain.occupying_armies, 2)
        self.assertEqual(self.france.occupying_armies, 4)

    def test_get_surrounding_territories(self):
        territory_army_counts = [1, 2, 1, 2, 2]
        for i in range(len(self.france.neighbors[:4])):
            self.france.neighbors[i].occupying_player = self.roosevelt
            self.france.neighbors[i].occupying_armies = territory_army_counts[i]
        surrounding_territories = self.g.get_surrounding_territories(self.roosevelt, self.france)
        correct = ['Belgium', 'Switzerland']
        self.assertEqual([t.name for t in surrounding_territories], correct)

    def test_get_territories_for_attack(self):
        self.roosevelt.controlled_territories = self.g.all_territories[-5:]
        territory_army_counts = [1, 2, 2, 1, 1]
        for i in range(len(self.roosevelt.controlled_territories)):
            self.roosevelt.controlled_territories[i].occupying_armies = territory_army_counts[i]
        territories_for_attack = self.g.get_territories_for_attack(self.roosevelt)
        correct = ['Burma', 'French Indo-China', 'Malaya', 'Siam', 'Dutch East Indies', 'Philippines']
        self.assertEqual([t.name for t in territories_for_attack], correct)

    def test_get_territories_to_fortify(self):
        self.roosevelt.controlled_territories = self.g.all_territories[-5:]
        territory_army_counts = [1, 2, 2, 1, 1]
        for i in range(len(self.roosevelt.controlled_territories)):
            self.roosevelt.controlled_territories[i].occupying_player = self.roosevelt
            self.roosevelt.controlled_territories[i].occupying_armies = territory_army_counts[i]
        territories_to_fortify = self.g.get_territories_to_fortify(self.roosevelt)
        correct = ['Burma', 'Malaya', 'Siam', 'Dutch East Indies']
        self.assertEqual([t.name for t in territories_to_fortify], correct)

    def test_select_territory_initial(self):
        self.g.select_territory_initial(self.roosevelt, self.great_britain, 2)
        self.assertEqual(self.great_britain.occupying_armies, 2)
        self.assertEqual(self.great_britain.occupying_player, self.roosevelt)
        self.assertIn(self.great_britain, self.roosevelt.controlled_territories)
