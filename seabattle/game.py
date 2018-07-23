# coding: utf-8

from __future__ import unicode_literals

import random
import re
import logging

from transliterate import translit

EMPTY = 0
SHIP = 1
BLOCKED = 2
HIT = 3
MISS = 4

log = logging.getLogger(__name__)
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

HORIZONTAL = 0
VERTICAL = 1


class BaseGame(object):
    position_patterns = [re.compile('^([a-zа-я]+)(\d+)$', re.UNICODE),  # a1
                         re.compile('^([a-zа-я]+)\s+(\w+)$', re.UNICODE),  # a 1; a один
                         re.compile('^(\w+)\s+(\w+)$', re.UNICODE),  # a 1; a один; 7 10
                         ]

    str_letters = ['а', 'б', 'в', 'г', 'д', 'е', 'ж', 'з', 'и', 'к']
    str_numbers = ['один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять', 'десять']

    letters_mapping = {
        'the': 'з',
        'за': 'з',
        'уже': 'ж',
        'трень': '3',
    }

    default_ships = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

    def __init__(self):
        self.size = 0
        self.ships = None
        self.field = []
        self.enemy_field = []

        self.ships_count = 0
        self.enemy_ships_count = 0

        self.last_shot_position = None
        self.last_enemy_shot_position = None
        self.numbers = None

    def start_new_game(self, size=10, field=None, ships=None, numbers=None):
        assert(size <= 10)
        assert(len(field) == size ** 2 if field is not None else True)

        self.size = size
        self.numbers = numbers if numbers is not None else False

        if ships is None:
            self.ships = self.default_ships
        else:
            self.ships = ships

        if field is None:
            self.generate_field()
        else:
            self.field = field

        self.enemy_field = [EMPTY] * self.size ** 2

        self.ships_count = self.enemy_ships_count = len(self.ships)

        self.last_shot_position = None
        self.last_enemy_shot_position = None

    def generate_field(self):
        raise NotImplementedError()

    def print_field(self, field=None):
        if not self.size:
            log.info('Empty field')
            return

        if field is None:
            field = self.field

        mapping = ['.', '1', '.', 'X', 'x']

        lines = ['']
        lines.append('-' * (self.size + 2))
        for y in range(self.size):
            lines.append('|%s|' % ''.join(str(mapping[x]) for x in field[y * self.size: (y + 1) * self.size]))
        lines.append('-' * (self.size + 2))
        log.info('\n'.join(lines))

    def print_enemy_field(self):
        self.print_field(self.enemy_field)

    def handle_enemy_shot(self, position):
        index = self.calc_index(position)

        if self.field[index] == SHIP:
            self.field[index] = HIT

            if self.is_dead_ship(index):
                self.ships_count -= 1
                return 'kill'
            else:
                return 'hit'
        elif self.field[index] == HIT:
            return 'kill' if self.is_dead_ship(index) else 'hit'
        else:
            return 'miss'

    def is_dead_ship(self, last_index):
        x, y = self.calc_position(last_index)
        x -= 1
        y -= 1

        def _line_is_dead(line, index):
            def _tail_is_dead(tail):
                for i in tail:
                    if i == HIT:
                        continue
                    elif i == SHIP:
                        return False
                    else:
                        return True
                return True

            return _tail_is_dead(line[index:]) and _tail_is_dead(line[index::-1])

        return (
            _line_is_dead(self.field[x::self.size], y) and
            _line_is_dead(self.field[y * self.size:(y + 1) * self.size], x)
        )

    def is_end_game(self):
        return self.is_victory() or self.is_defeat()

    def is_victory(self):
        return self.enemy_ships_count < 1

    def is_defeat(self):
        return self.ships_count < 1

    def do_shot(self):
        raise NotImplementedError()

    def repeat(self):
        return self.convert_from_position(self.last_shot_position, numbers=True)

    def reset_last_shot(self):
        self.last_shot_position = None

    def handle_enemy_reply(self, message):
        if self.last_shot_position is None:
            return

        index = self.calc_index(self.last_shot_position)

        if message in ['hit', 'kill']:
            self.enemy_field[index] = SHIP

            if message == 'kill':
                self.enemy_ships_count -= 1

        elif message == 'miss':
            self.enemy_field[index] = MISS

    def calc_index(self, position):
        x, y = position

        if x > self.size or y > self.size:
            raise ValueError('Wrong position: %s %s' % (x, y))

        return (y - 1) * self.size + x - 1

    def calc_position(self, index):
        y = index / self.size + 1
        x = index % self.size + 1

        return x, y

    def convert_to_position(self, position):
        position = position.lower()
        for pattern in self.position_patterns:
            match = pattern.match(position)

            if match is not None:
                break
        else:
            raise ValueError('Can\'t parse entire position: %s' % position)

        bits = match.groups()

        def _try_letter(bit):
            # проверяем особые случаи неправильного распознования STT
            bit = self.letters_mapping.get(bit, bit)

            # преобразуем в кириллицу
            bit = translit(bit, 'ru')

            try:
                return self.str_letters.index(bit) + 1
            except ValueError:
                raise

        def _try_number(bit):
            # проверяем особые случаи неправильного распознования STT
            bit = self.letters_mapping.get(bit, bit)

            if bit.isdigit():
                return int(bit)
            else:
                try:
                    return self.str_numbers.index(bit) + 1
                except ValueError:
                    raise

        x = bits[0].strip()
        try:
            x = _try_number(x)
        except ValueError:
            raise ValueError('Can\'t parse X point: %s' % x)

        y = bits[1].strip()
        try:
            y = _try_number(y)
        except ValueError:
            raise ValueError('Can\'t parse Y point: %s' % y)

        return x, y

    def convert_from_position(self, position, numbers=None):
        numbers = numbers if numbers is not None else self.numbers

        if numbers:
            x = position[0]
        else:
            x = self.str_letters[position[0] - 1]

        y = position[1]

        return '%s, %s' % (x, y)


class Game(BaseGame):
    """Реализация игры с ипользованием обычного random"""

    def generate_field(self):
        """Метод генерации поля"""
        self.field = [0] * self.size ** 2

        for length in self.ships:
            self.place_ship(length)

        for i in range(len(self.field)):
            if self.field[i] == BLOCKED:
                self.field[i] = EMPTY

    def place_ship(self, length):
        def _try_to_place():
            x = random.randint(1, self.size)
            y = random.randint(1, self.size)
            direction = random.choice([1, self.size])

            index = self.calc_index((x, y))
            values = self.field[index:None if direction == self.size else index + self.size - index % self.size:direction][:length]

            if len(values) < length or any(values):
                return False

            for i in range(length):
                current_index = index + direction * i

                for j in [0, 1, -1]:
                    if (j != 0
                            and current_index % self.size in (0, self.size - 1)
                            and (current_index + j) % self.size in (0, self.size - 1)):
                        continue

                    for k in [0, self.size, -self.size]:
                        neighbour_index = current_index + k + j

                        if (neighbour_index < 0
                                or neighbour_index >= len(self.field)
                                or self.field[neighbour_index] == SHIP):
                            continue

                        self.field[neighbour_index] = BLOCKED

                self.field[current_index] = SHIP

            return True

        while not _try_to_place():
            pass

    def get_next_regular_shot_position(self):
        def get_next_position():
            not_used_predefined_shots_by_step_4 = [
                (idx, position) for idx, position in enumerate(self.predefined_shots_by_step_4)
                if position is not None]
            if not_used_predefined_shots_by_step_4:
                idx, position = random.choice(not_used_predefined_shots_by_step_4)
                # отмечаем, что использовали выстрел
                self.predefined_shots_by_step_4[idx] = None
                return position

            not_used_predefined_shots_by_step_2 = [
                (idx, position) for idx, position in enumerate(self.predefined_shots_by_step_2)
                if position is not None]
            if not_used_predefined_shots_by_step_2:
                idx, position = random.choice(not_used_predefined_shots_by_step_2)
                # отмечаем, что использовали выстрел
                self.predefined_shots_by_step_2[idx] = None
                return position

            index = random.choice([i for i, v in enumerate(self.enemy_field) if v == EMPTY])
            return self.calc_position(index)

        next_position = get_next_position()
        while self.get_enemy_position_status(position=next_position) != EMPTY:
            next_position = get_next_position()

        return next_position

    def mark_enemy_position(self, position, status):
        x, y = position
        if (1 <= x <= self.size) and (1 <= y <= self.size):
            self.enemy_field[self.calc_index(position=position)] = status

    def get_enemy_position_status(self, position):
        x, y = position
        if (1 <= x <= self.size) and (1 <= y <= self.size):
            return self.enemy_field[self.calc_index(position=position)]

    def mark_positions_around_ship_as_missed(self, position, direction=None):
        x, y = position
        # север-восток
        self.mark_enemy_position((x + 1, y - 1), MISS)
        # юго-восток
        self.mark_enemy_position((x + 1, y + 1), MISS)
        # северо-запад
        self.mark_enemy_position((x - 1, y - 1), MISS)
        # юго-запад
        self.mark_enemy_position((x - 1, y + 1), MISS)

        # проверяем клетку сверху
        if direction in (None, UP):
            north_position = (x, y - 1)
            if self.get_enemy_position_status(position=north_position) == SHIP:
                self.mark_positions_around_ship_as_missed(position=north_position, direction=UP)
            else:
                self.mark_enemy_position(north_position, MISS)

        # проверяем клетку справа
        if direction in (None, RIGHT):
            east_position = (x + 1, y)
            if self.get_enemy_position_status(position=east_position) == SHIP:
                self.mark_positions_around_ship_as_missed(position=east_position, direction=RIGHT)
            else:
                self.mark_enemy_position(east_position, MISS)

        # проверяем клетку снизу
        if direction in (None, DOWN):
            south_position = (x, y + 1)
            if self.get_enemy_position_status(position=south_position) == SHIP:
                self.mark_positions_around_ship_as_missed(position=south_position, direction=DOWN)
            else:
                self.mark_enemy_position(south_position, MISS)

        # проверяем клетку слева
        if direction in (None, LEFT):
            west_position = (x - 1, y)
            if self.get_enemy_position_status(position=west_position) == SHIP:
                self.mark_positions_around_ship_as_missed(position=west_position, direction=LEFT)
            else:
                self.mark_enemy_position(west_position, MISS)

    def do_specified_shot(self, position):
        self.last_shot_position = position
        self.last_shot_enemy_ships_count = self.enemy_ships_count

    def get_next_possible_shots(self, position, direction=None):
        start_x, start_y = position

        ship_orientation = None
        vertical_possible_shots = []

        # проверяем клетку сверху
        if direction in (None, UP):
            north_position = (start_x, start_y - 1)
            enemy_position_status = self.get_enemy_position_status(position=north_position)
            if enemy_position_status == SHIP:
                ship_orientation = VERTICAL
                vertical_possible_shots += self.get_next_possible_shots(position=north_position, direction=UP)
            elif enemy_position_status == EMPTY:
                vertical_possible_shots.append(north_position)

        # проверяем клетку снизу
        if direction in (None, DOWN):
            south_position = (start_x, start_y + 1)
            enemy_position_status = self.get_enemy_position_status(position=south_position)
            if enemy_position_status == SHIP:
                ship_orientation = VERTICAL
                vertical_possible_shots += self.get_next_possible_shots(position=south_position, direction=DOWN)
            elif enemy_position_status == EMPTY:
                vertical_possible_shots.append(south_position)

        horisontal_possible_shots = []

        # проверяем клетку справа
        if direction in (None, RIGHT):
            east_position = (start_x + 1, start_y)
            enemy_position_status = self.get_enemy_position_status(position=east_position)
            if enemy_position_status == SHIP:
                ship_orientation = HORIZONTAL
                horisontal_possible_shots += self.get_next_possible_shots(position=east_position, direction=RIGHT)
            elif enemy_position_status == EMPTY:
                horisontal_possible_shots.append(east_position)

        # проверяем клетку слева
        if direction in (None, LEFT):
            west_position = (start_x - 1, start_y)
            enemy_position_status = self.get_enemy_position_status(position=west_position)
            if enemy_position_status == SHIP:
                ship_orientation = HORIZONTAL
                horisontal_possible_shots += self.get_next_possible_shots(position=west_position, direction=LEFT)
            elif enemy_position_status == EMPTY:
                horisontal_possible_shots.append(west_position)

        if ship_orientation == VERTICAL:
            return vertical_possible_shots
        elif ship_orientation == HORIZONTAL:
            return horisontal_possible_shots

        return vertical_possible_shots + horisontal_possible_shots

    def do_shot(self):
        """Метод выбора координаты выстрела.

        ЕГО И НУЖНО ЗАМЕНИТЬ НА СВОЙ АЛГОРИТМ
        """

        # index = random.choice([i for i, v in enumerate(self.enemy_field) if v == EMPTY])
        #
        # self.last_shot_position = self.calc_position(index)
        if self.last_shot_position is None:
            self.do_specified_shot(self.get_next_regular_shot_position())

        if self.get_enemy_position_status(position=self.last_shot_position) == SHIP:
            # в прошлый раз попали в корабль
            if self.last_shot_enemy_ships_count == self.enemy_ships_count:
                # поразили корабль, но не потопили
                if self.found_ship:
                    # уже ранее обнуружили корабль
                    next_possible_shots = self.get_next_possible_shots(self.first_ship_hit_position)
                    self.do_specified_shot(random.choice(next_possible_shots))
                else:
                    # только что обнаружили корабль
                    self.found_ship = True
                    self.first_ship_hit_position = self.last_shot_position

                    next_possible_shots = self.get_next_possible_shots(self.first_ship_hit_position)
                    self.do_specified_shot(random.choice(next_possible_shots))
            else:
                # потопили корабль
                self.mark_positions_around_ship_as_missed(position=self.last_shot_position)

                # сбрасываем вспомогательные данные о найденном корабле
                self.found_ship = False
                self.first_ship_hit_position = None

                # делаем обычный выстрел
                self.do_specified_shot(self.get_next_regular_shot_position())
        else:
            # в прошлый раз промахнулись
            if self.found_ship:
                next_possible_shots = self.get_next_possible_shots(self.first_ship_hit_position)
                self.do_specified_shot(random.choice(next_possible_shots))
            else:
                # обычный выстрел
                self.do_specified_shot(self.get_next_regular_shot_position())

        return self.convert_from_position(self.last_shot_position)

    def __init__(self):
        super(Game, self).__init__()

        self.predefined_shots_by_step_4 = None
        self.predefined_shots_by_step_2 = None

        self.last_shot_enemy_ships_count = 0
        self.last_shot_direction = None
        self.first_ship_hit_position = None
        self.found_ship = False

    def start_new_game(self, size=10, field=None, ships=None, numbers=None):
        super(Game, self).start_new_game(size=size, field=field, ships=ships, numbers=numbers)

        self.predefined_shots_by_step_4 = [position for position in self.diagonal_shots(step=4)]
        self.predefined_shots_by_step_2 = [position for position in self.diagonal_shots(step=2)]

        self.last_shot_enemy_ships_count = self.enemy_ships_count
        self.last_shot_direction = None
        self.first_ship_hit_position = None
        self.found_ship = False

    def diagonal_positions(self, field_size):
        for i in range(field_size):
            yield field_size - i, i + 1

    def diagonal_shots(self, step):
        number_of_step_field = (self.size + step - 1) // step
        for fy in range(number_of_step_field):
            for fx in range(number_of_step_field):
                for x, y in self.diagonal_positions(field_size=step):
                    effective_x = x + fx * step
                    if effective_x > self.size:
                        continue
                    effective_y = y + fy * step
                    if effective_y > self.size:
                        continue
                    yield effective_x, effective_y

    # def predefined_shots(self):
    #     for step_value in (4, 2):
    #         for position in self.diagonal_shots(step=step_value):
    #             enemy_position_index = self.calc_index(position=position)
    #             if self.enemy_field[enemy_position_index] != EMPTY:
    #                 continue
    #             yield position
