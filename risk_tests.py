from unittest import mock, TestCase

from game_of_risk import GameOfRisk


class WorldWar2Test(TestCase):
    def setUp(self):
        self.g = GameOfRisk('test_games/world_war_2_test.txt')
        self.roosevelt = self.g.players[0]
        self.churchill = self.g.players[1]
        self.great_britain = self.g.all_territories[0]
        self.france = self.g.all_territories[1]

    def calibrate_britain_and_france(self, britain_player, britain_count, france_player, france_count):
        britain_player.controlled_territories.append(self.great_britain)
        self.great_britain.occupying_player = britain_player
        self.great_britain.occupying_armies = britain_count
        france_player.controlled_territories.append(self.france)
        self.france.occupying_player = france_player
        self.france.occupying_armies = france_count

    def print_side_effect(self, *args, **kwargs):
        pass

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

    def test_allocate_armies(self):
        self.assertEqual(self.roosevelt.army_count, 20)

    @mock.patch('game_of_risk.GameOfRisk.decide_battle')
    def test_attack_territory_attacker_wins_defender_occupies(self, decide_battle_mock):
        decide_battle_mock.return_value = 1
        self.calibrate_britain_and_france(self.roosevelt, 3, self.churchill, 3)
        self.g.attack_territory(self.great_britain, self.france, 1, 1)
        self.assertEqual(self.france.occupying_armies, 2)

    @mock.patch('builtins.print')
    @mock.patch('game_of_risk.GameOfRisk.decide_battle')
    def test_attack_territory_attacker_wins_defender_leaves(self, decide_battle_mock, print_mock):
        decide_battle_mock.return_value = 1
        print_mock.side_effect = lambda s: None
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

    def test_get_territories_for_attack(self):
        self.roosevelt.controlled_territories = self.g.all_territories[-5:]
        territory_army_counts = [1, 2, 2, 1, 1]
        for i in range(len(self.roosevelt.controlled_territories)):
            self.roosevelt.controlled_territories[i].occupying_armies = territory_army_counts[i]
        territories_for_attack = self.g.get_territories_for_attack(self.roosevelt)
        correct = {'Siam', 'Philippines', 'Dutch East Indies', 'French Indo-China', 'Malaya', 'Burma'}
        self.assertEqual({t.name for t in territories_for_attack}, correct)

    def test_select_territory_initial(self):
        self.g.select_territory_initial(self.roosevelt, self.great_britain, 2)
        self.assertEqual(self.great_britain.occupying_armies, 2)
        self.assertEqual(self.great_britain.occupying_player, self.roosevelt)
        self.assertIn(self.great_britain, self.roosevelt.controlled_territories)
