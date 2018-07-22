# coding: utf-8
from __future__ import unicode_literals
from seabattle.game import Game, MISS

import pytest


@pytest.fixture
def game():
    g = Game()
    g.start_new_game()

    return g


@pytest.fixture
def game_with_field(game):
    field = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0,
             1, 1, 1, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 1, 0, 1, 0, 1, 0, 0,
             1, 1, 0, 1, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 1, 0, 1, 1, 1, 0, 0,
             0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 1, 0, 0, 1, 1, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 1, 0]

    game.start_new_game(field=field)

    return game


def test_helper_functions(game):
    assert game.calc_index((4, 7)) == 63

    assert game.calc_position(63) == (4, 7)

    assert game.convert_to_position('a10') == (1, 10)
    assert game.convert_to_position('d 7') == (5, 7)
    assert game.convert_to_position('д 5') == (5, 5)
    assert game.convert_to_position('g 3') == (4, 3)

    assert game.convert_to_position('k 1') == (10, 1)
    assert game.convert_to_position('k 2') == (10, 2)
    assert game.convert_to_position('k 10') == (10, 10)
    assert game.convert_to_position('k два') == (10, 2)

    assert game.convert_to_position('d пять') == (5, 5)

    assert game.convert_to_position('10 10') == (10, 10)
    assert game.convert_to_position('1 2') == (1, 2)
    assert game.convert_to_position('8 4') == (8, 4)
    assert game.convert_to_position('восемь четыре') == (8, 4)

    assert game.convert_to_position('уже 4') == (7, 4)
    assert game.convert_to_position('the 4') == (8, 4)
    assert game.convert_to_position('за 4') == (8, 4)

    with pytest.raises(ValueError):
        assert game.convert_to_position('1') == (1, 1)

    with pytest.raises(ValueError):
        game.convert_to_position('т шесть')

    with pytest.raises(ValueError):
        game.convert_to_position('д пятнадцать')

    assert game.convert_from_position((1, 1)) == 'а, 1'
    assert game.convert_from_position((6, 5)) == 'е, 5'
    assert game.convert_from_position((6, 5), numbers=True) == '6, 5'


def test_shot(game):
    pass


def test_dead_ship(game_with_field):
    assert game_with_field.handle_enemy_shot((7, 1)) == 'kill'

    assert game_with_field.handle_enemy_shot((1, 5)) == 'hit'
    assert game_with_field.handle_enemy_shot((2, 5)) == 'kill'

    assert game_with_field.handle_enemy_shot((1, 2)) == 'hit'
    assert game_with_field.handle_enemy_shot((2, 2)) == 'hit'
    assert game_with_field.handle_enemy_shot((3, 2)) == 'kill'


def test_repeat(game):
    game.last_shot_position = (5, 7)
    assert '5, 7' == game.repeat()


def test_handle_shot(game_with_field):
    assert game_with_field.handle_enemy_shot((4, 7)) == 'hit'
    assert game_with_field.handle_enemy_shot((4, 7)) == 'hit'

    assert game_with_field.handle_enemy_shot((7, 1)) == 'kill'
    assert game_with_field.handle_enemy_shot((7, 1)) == 'kill'

    assert game_with_field.handle_enemy_shot((4, 2)) == 'miss'

    with pytest.raises(ValueError):
        game_with_field.handle_enemy_shot((19, 6))


def test_handle_reply(game):
    game.do_shot()
    game.handle_enemy_reply('miss')


def test_diagonal_shot():
    field_2_by_2 = [
        0, 1,
        1, 0
    ]
    g = Game()
    g.start_new_game(size=2, field=field_2_by_2)

    for position in g.diagonal_positions(field_size=2):
        assert g.handle_enemy_shot(position=position) == 'kill'

    field_4_by_4 = [
        0, 0, 0, 1,
        0, 0, 1, 0,
        0, 1, 0, 0,
        1, 0, 0, 0,
    ]
    g.start_new_game(size=4, field=field_4_by_4)

    for position in g.diagonal_positions(field_size=4):
        assert g.handle_enemy_shot(position=position) == 'kill'


def test_diagonal_shots():
    field_size = 10
    field_with_step_4 = [
        0, 0, 0, 1, 0, 0, 0, 1, 0, 0,
        0, 0, 1, 0, 0, 0, 1, 0, 0, 0,
        0, 1, 0, 0, 0, 1, 0, 0, 0, 1,
        1, 0, 0, 0, 1, 0, 0, 0, 1, 0,
        0, 0, 0, 1, 0, 0, 0, 1, 0, 0,
        0, 0, 1, 0, 0, 0, 1, 0, 0, 0,
        0, 1, 0, 0, 0, 1, 0, 0, 0, 1,
        1, 0, 0, 0, 1, 0, 0, 0, 1, 0,
        0, 0, 0, 1, 0, 0, 0, 1, 0, 0,
        0, 0, 1, 0, 0, 0, 1, 0, 0, 0,
    ]

    g = Game()
    g.start_new_game(size=field_size, field=field_with_step_4)
    for position in g.diagonal_shots(step=4):
        assert g.handle_enemy_shot(position=position) == 'kill'

    field_with_step_2 = [
        0, 1, 0, 1, 0, 1, 0, 1, 0, 1,
        1, 0, 1, 0, 1, 0, 1, 0, 1, 0,
        0, 1, 0, 1, 0, 1, 0, 1, 0, 1,
        1, 0, 1, 0, 1, 0, 1, 0, 1, 0,
        0, 1, 0, 1, 0, 1, 0, 1, 0, 1,
        1, 0, 1, 0, 1, 0, 1, 0, 1, 0,
        0, 1, 0, 1, 0, 1, 0, 1, 0, 1,
        1, 0, 1, 0, 1, 0, 1, 0, 1, 0,
        0, 1, 0, 1, 0, 1, 0, 1, 0, 1,
        1, 0, 1, 0, 1, 0, 1, 0, 1, 0,
    ]

    g = Game()
    g.start_new_game(size=field_size, field=field_with_step_2)
    for position in g.diagonal_shots(step=2):
        assert g.handle_enemy_shot(position=position) == 'kill'


def test_get_next_possible_shots(game_with_field):
    enemy_field = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0,
                   1, 1, 1, 0, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 1, 0, 1, 0, 1, 0, 0,
                   1, 1, 0, 1, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 1, 0, 1, 1, 1, 0, 0,
                   0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
                   0, 1, 0, 0, 1, 1, 0, 0, 0, 0,
                   0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
    game_with_field.enemy_field = list(enemy_field)

    next_possible_shots = game_with_field.get_next_possible_shots(position=(7, 1))
    assert len(next_possible_shots) == 3
    assert (6, 1) in next_possible_shots
    assert (8, 1) in next_possible_shots
    assert (7, 2) in next_possible_shots

    next_possible_shots = game_with_field.get_next_possible_shots(position=(7, 7))
    assert len(next_possible_shots) == 2
    assert (9, 7) in next_possible_shots
    assert (5, 7) in next_possible_shots

    next_possible_shots = game_with_field.get_next_possible_shots(position=(2, 8))
    assert len(next_possible_shots) == 2
    assert (2, 7) in next_possible_shots
    assert (2, 10) in next_possible_shots


def test_mark_positions_around_ship_as_missed(game_with_field):
    enemy_field = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0,
                   1, 1, 1, 0, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 1, 0, 1, 0, 1, 0, 0,
                   1, 1, 0, 1, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
                   0, 0, 0, 1, 0, 1, 1, 1, 0, 0,
                   0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
                   0, 1, 0, 0, 1, 1, 0, 0, 0, 0,
                   0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
    game_with_field.enemy_field = list(enemy_field)
    game_with_field.mark_positions_around_ship_as_missed(position=(7, 1))
    positions_to_be_marked_as_miss = [
        (6, 1),
        (8, 1),
        (6, 2),
        (7, 2),
        (8, 2),
    ]
    for miss_position in positions_to_be_marked_as_miss:
        assert game_with_field.enemy_field[game_with_field.calc_index(miss_position)] == MISS

    game_with_field.enemy_field = list(enemy_field)
    game_with_field.mark_positions_around_ship_as_missed(position=(7, 7))
    positions_to_be_marked_as_miss = [
        (5, 6),
        (6, 6),
        (7, 6),
        (8, 6),
        (9, 6),

        (5, 7),
        (9, 7),

        (5, 8),
        (6, 8),
        (7, 8),
        (8, 8),
        (9, 8),
    ]
    for miss_position in positions_to_be_marked_as_miss:
        assert game_with_field.enemy_field[game_with_field.calc_index(miss_position)] == MISS
