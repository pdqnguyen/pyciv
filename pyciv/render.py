#! /usr/bin/python

import pygame as pg
import math
import os
import sys
import time
from matplotlib.colors import to_rgb

from . import menu_data
from . import utils as civutils
from .bases import BASE_COLORS
from .features import FEATURE_COLORS
from .civilizations import CIV_COLORS
from .menu import PopupMenu
from .utils import Action


SQRT3 = math.sqrt(3)

TILE_INFO_DELAY = 0.2


def colorname2pg(name):
    rgb = [int(x * 255) for x in to_rgb(name)]
    return pg.Color(*rgb)


class RenderGrid(pg.Surface):
    def __init__(self, board, civs, screen_size=(1280, 720)):
        self.board = board
        self.civs = civs
        self.width, self.height = screen_size
        self.radius = self._radius()
        super(RenderGrid, self).__init__((self.width, self.height))

    def _radius(self):
        max_x = self.width / (self.board.shape[0] + 0.5) / SQRT3
        max_y = self.height / (1.5 * self.board.shape[1] + 0.5)
        return min(max_x, max_y)

    def _xy_offset(self, x, y):
        # Tile position offsets
        if y % 2 == 0:
            x_offset = SQRT3 * self.radius * x
        else:
            x_offset = SQRT3 * self.radius * (x + 0.5)
        y_offset = 1.5 * self.radius * y
        return x_offset, y_offset

    def draw_base(self, tile, color=None):
        x_offset, y_offset = self._xy_offset(tile.x, tile.y)
        # Hex corner locations
        points = [
            (0.5 * SQRT3 * self.radius, 0),
            (SQRT3 * self.radius, 0.5 * self.radius),
            (SQRT3 * self.radius, 1.5 * self.radius),
            (0.5 * SQRT3 * self.radius, 2 * self.radius),
            (0, 1.5 * self.radius),
            (0, 0.5 * self.radius)
        ]
        points = [(x + x_offset, y + y_offset) for (x, y) in points]
        # Get color
        if color is None:
            color = self._get_base_color(tile.base)
        # Hex tile
        poly = pg.draw.polygon(self, color, points)
        # Black outline
        pg.draw.polygon(self, pg.Color(0, 0, 0), points, 2)
        return poly

    def draw_features(self, tile, color=None):
        x_offset, y_offset = self._xy_offset(tile.x, tile.y)
        if color is None:
            color = self._get_feature_color(tile.features[-1])
        circle_pos = (
            int(x_offset + 0.5 * SQRT3 * self.radius),
            int(y_offset + self.radius)
        )
        circle_r = int(round(0.5 * self.radius))
        pg.draw.circle(self, color, circle_pos, circle_r)
        return

    def draw_city(self, pos, color):
        x_offset, y_offset = self._xy_offset(*pos)
        triangle = [
            (x_offset + 0.5 * SQRT3 * self.radius - self.radius / SQRT3, y_offset + 1.5 * self.radius),
            (x_offset + 0.5 * SQRT3 * self.radius + self.radius / SQRT3, y_offset + 1.5 * self.radius),
            (x_offset + 0.5 * SQRT3 * self.radius, y_offset + 0.5 * self.radius)
        ]
        pg.draw.polygon(self, color, triangle)
        return

    def draw_territory(self, pos, color):
        x_offset, y_offset = self._xy_offset(*pos)
        points = [
            (0.5 * SQRT3 * self.radius, 0),
            (SQRT3 * self.radius, 0.5 * self.radius),
            (SQRT3 * self.radius, 1.5 * self.radius),
            (0.5 * SQRT3 * self.radius, 2 * self.radius),
            (0, 1.5 * self.radius),
            (0, 0.5 * self.radius)
        ]
        points = [(x + x_offset, y + y_offset) for (x, y) in points]
        if color is None:
            color = self._get_base_color(tile.base)
        pg.draw.polygon(self, color, points, 4)
        return

    def draw_unit(self, pos, color, bordercolor=colorname2pg('black')):
        x_offset, y_offset = self._xy_offset(*pos)
        circle_pos = (
            int(x_offset + 0.5 * SQRT3 * self.radius),
            int(y_offset + self.radius)
        )
        circle_r = int(round(0.4 * self.radius))
        pg.draw.circle(self, bordercolor, circle_pos, circle_r)
        pg.draw.circle(self, color, circle_pos, int(0.6 * circle_r))
        return

    def draw_civ(self, civ):
        color = self._get_civ_color(civ.name)
        for city in civ:
            self.draw_city(city.tiles[0].pos, color)
            for tile in city:
                self.draw_territory(tile.pos, color)
        for unit in civ.units:
            self.draw_unit(unit.pos, color)
        return

    def draw_text_grid_overlay(self, array, font):
        for i in range(array.shape[0]):
            for j in range(array.shape[1]):
                text = font.render(str(array[i, j]), 1, (255, 255, 255))
                text_rect = text.get_rect()
                if j % 2 == 0:
                    x = SQRT3 * self.radius * (i + 0.5)
                else:
                    x = SQRT3 * self.radius * (i + 1)
                y = 1.5 * self.radius * (j + 1)
                text_rect.center = (x, y - font.get_height())
                self.blit(text, text_rect)
        return

    def draw(self, highlight=None):
        polygons = []
        for tile in self.board:
            color = None
            if highlight:
                if tile not in highlight:
                    color = pg.Color(0, 0, 0)
            poly = self.draw_base(tile, color)
            polygons.append((tile, poly))
            if tile.features:
                self.draw_features(tile, color)
        for civ in self.civs:
            self.draw_civ(civ)
        return polygons

    @staticmethod
    def _get_base_color(base):
        b_color = BASE_COLORS.get(base)
        return colorname2pg(b_color)

    @staticmethod
    def _get_feature_color(feature):
        f_color = FEATURE_COLORS.get(feature)
        return colorname2pg(f_color)

    @staticmethod
    def _get_civ_color(civ):
        c_color = CIV_COLORS.get(civ)
        return colorname2pg(c_color)


class UserState:
    def __init__(self, **kwargs):
        self.__default_attrs = kwargs.copy()
        self.update(**kwargs)

    def reset(self):
        for k, v in self.__default_attrs.items():
            setattr(self, k, v)

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class RenderGame:

    def __init__(self, game, screen_size=(1920, 1080), rate=30, fontsize=36, window_pos=(0, 40)):
        self.game = game
        self.screen_size = screen_size
        self.rate = rate
        self.fontsize = fontsize
        self.user_state = None
        # Pygame initialization
        os.environ['SDL_VIDEO_WINDOW_POS'] = '{:d},{:d}'.format(*window_pos)
        pg.init()
        self.__game_over = False
        self.__enable_render = True #enable_render
        if self.__enable_render:
            self.surface = pg.display.set_mode(self.screen_size, 1)
        self.font = pg.font.SysFont("Trebuchet", self.fontsize)
        self.clock = pg.time.Clock()

        self.grid = RenderGrid(self.game.board, self.game.civs, screen_size=self.screen_size)
        self.grid2 = RenderGrid(self.game.board, self.game.civs, screen_size=self.screen_size)
        self.grid2.set_alpha(80)

        # Initialize user interaction state
        self._init_user_state(
            hover_tile = None,
            hover_tile_time = time.time(),
            active_tile = None,
            active_unit = None,
            active_city = None,
            menu_selection = None,
            path = None,
            distance = 0
        )

    def _init_user_state(self, **kwargs):
        self.user_state = UserState(**kwargs)

    def update(self):
        if self.__enable_render:
            try:
                img_output = self.__view_update()
                #self.__controller_update()
            except Exception as e:
                self.quit_game()
                raise e
            else:
                return img_output

    def __on_click(self, tile):
        unit = self.game.get_unit(tile)
        units = self.game.get_units(tile)
        city = self.game.get_city(tile)
        civ = self.game.get_civ(tile)
        unit_selected = (unit and unit.pos == tile.pos and unit.civ == self.game.active_civ().name)
        city_selected = (city and city.tiles[0] == tile and city.civ == self.game.active_civ().name)
        active_unit_ = self.user_state.active_unit
        active_city_ = self.user_state.active_city
        menu_selection_ = self.user_state.menu_selection
        if active_unit_:
            if menu_selection_ in active_unit_.actions(self.game):
                self.user_state.update(active_unit=None, menu_selection=None)
                return Action(menu_selection_, unit=active_unit_, target=tile)
        elif active_city_:
            if menu_selection_ == 'range attack':
                self.user_state.update(active_city=None, menu_selection=None)
                return Action(menu_selection_, city=active_city_, target=tile)
        if city_selected:
            self.user_state.update(active_tile=tile, active_city=city)
            city_units = self.game.get_units(self.user_state.active_tile)
            PopupMenu(menu_data.get_city_options(self.game, self.user_state.active_city, civ, units=city_units))#, pos=(0, 0))
        elif unit_selected:
            self.user_state.update(active_tile=tile, active_unit=unit)
            if len(units) > 1:
                PopupMenu(menu_data.get_multi_unit_options(self.game, units, civ))
            elif len(units) == 1:
                PopupMenu(menu_data.get_unit_options(self.game, self.user_state.active_unit, civ))
        else:
            self.user_state.update(active_unit=None, active_city=None)
            PopupMenu(menu_data.get_default_options())

    def __on_menu_action(self, ev):
        if ev.name == "Choose production...":
            if ev.text != "No production options":
                active_city = self.user_state.active_city
                return Action('build', city=active_city, target=ev.text)
        elif "Unit actions" in ev.name:
            active_unit_name = ev.name.split()[2]
            active_unit_action = ev.text.lower()
            active_unit = self.game.get_unit_by_name(active_unit_name)
            if (active_unit_action == 'move') or ('attack' in active_unit_action):
                self.user_state.update(active_unit=active_unit, menu_selection=active_unit_action)
            else:
                self.user_state.update(active_unit=None)
                return Action(active_unit_action, unit=active_unit)
        elif ev.text == "City ranged attack":
            active_city = self.user_state.active_city
            self.user_state.update(active_city=active_city, menu_selection='range attack')
        elif ev.text == "End turn":
            return Action('end_turn')
        elif ev.text == "Quit game":
            quit()

    def __view_update(self):
        while True:
            polygons = self.grid.draw()
            mouse = pg.mouse.get_pos()
            tile, polygon = self.get_tile(polygons, mouse)
            unit = self.game.get_unit(tile)
            city = self.game.get_city(tile)
            civ = self.game.get_civ(tile)
            if unit and not civ:
                civ = self.game.find_civ(unit.civ)
            unit_selected = (unit and unit.pos == tile.pos and unit.civ == self.game.active_civ().name)
            city_selected = (city and city.tiles[0] == tile and city.civ == self.game.active_civ().name)
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                #==========================================================
                # HUMAN USER INPUTS

                if ev.type == pg.MOUSEBUTTONUP:
                    user_action = self.__on_click(tile)
                    if user_action:
                        self.user_state.reset()
                        return user_action
                elif ev.type == pg.USEREVENT:
                    if ev.code == 'MENU':
                        user_action = self.__on_menu_action(ev)
                        if user_action:
                            self.user_state.reset()
                            return user_action
                elif ev.type == pg.KEYDOWN:
                    if ev.key == pg.K_c and pg.key.get_mods() & pg.KMOD_CTRL:
                        raise KeyboardInterrupt
                    elif ev.key == pg.K_RETURN and pg.key.get_mods() & pg.KMOD_SHIFT:
                        return Action('end_turn') #self.game.end_turn()

                #==========================================================
            # Highlight tiles
            if self.user_state.active_unit and self.user_state.menu_selection:
                if self.user_state.menu_selection == 'move':
                    if self.user_state.hover_tile != tile and tile is not None:
                        path, costs = civutils.find_best_path(self.user_state.active_unit.pos, tile.pos, self.game)
                        distance = costs[tile.pos]
                        self.user_state.update(path=path, distance=distance)
                    if self.user_state.path:
                        for p in self.user_state.path:
                            self.grid.draw_territory(p, pg.Color(255, 0, 0))
                    highlight = self.user_state.active_unit.get_moves(self.game)
                    if self.user_state.active_unit._class == 'settler':
                        data = self.game.settler_scores(self.user_state.active_unit)
                        self.grid.draw_text_grid_overlay(data, self.font)
                    if self.user_state.active_unit._class == 'worker':
                        data = self.game.worker_scores(self.user_state.active_unit)
                        self.grid.draw_text_grid_overlay(data, self.font)
                elif 'attack' in self.user_state.menu_selection:
                    highlight = self.user_state.active_unit.get_targets(self.game)
                else:
                    highlight = None
            else:
                highlight = None
            self.grid2.draw(highlight)
            self.__blit(self.grid, (0, 0))
            self.__blit(self.grid2, (0, 0))
            self.show_turn()
            if tile:
                if self.user_state.active_unit:
                    if self.user_state.menu_selection == 'move':
                        if self.user_state.path:
                            self.show_distance(self.user_state.distance, mouse)
                if self.user_state.hover_tile != tile:
                    self.user_state.update(hover_tile=tile, tile_hover_time=time.time())
                if time.time() - self.user_state.tile_hover_time > TILE_INFO_DELAY:
                    self.show_tile_info(tile, mouse)
            pg.display.update()
            self.clock.tick(self.rate)

    def __blit(self, *args):
        self.surface.blit(*args)

    def get_tile(self, polygons, mouse):
        for t, p in polygons:
            if p.inflate(-3, -3).collidepoint(mouse):
                return t, p
        return None, None

    def show_distance(self, distance, mouse):
        text = self.font.render(str(distance), 1, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.bottomleft = (mouse[0], mouse[1] - self.font.get_height())
        self.__blit(text, text_rect)
        return

    def show_settler_score(self, pos, mouse):
        score = self.game.settler_score(pos)
        text = self.font.render(str(score), 1, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.bottomleft = (mouse[0], mouse[1] - self.font.get_height())
        self.__blit(text, text_rect)
        return

    def show_worker_score(self, pos, mouse):
        score = self.game.worker_score(pos)
        text = self.font.render(str(score), 1, (255, 255, 255))
        text_rect = text.get_rect()
        text_rect.bottomleft = (mouse[0], mouse[1] - self.font.get_height())
        self.__blit(text, text_rect)
        return

    def tile_info_text(self, tile):
        lines = []
        units = self.game.get_units(tile)
        city = self.game.get_city(tile)
        civ = self.game.get_civ(tile)
        if units:
            for unit in units:
                lines.append("{} - {}".format(unit.name, unit._class))
                if type(unit).__name__ == 'CombatUnit':
                    lines.append("HP: {}, CS: {}/{}".format(unit.hp, unit.atk_strength(tile), unit.def_strength(tile)))
        if city:
            lines.append("{} ({}){}".format(city.name, city.pp, "*" if city.capital else 0))
            lines.append("HP: {}, CS: {}".format(city.hp, city.def_strength(tile)))
        header = ", ".join([tile.base] + tile.features + tile.improvements + tile.resources)
        if civ:
            header += " ({})".format(civ.name)
        lines.append(header)
        lines.append("---")
        yields = tile.print_yields().split("\n")
        yields = [y for y in yields if y]
        lines += yields
        if city:
            if city.buildings:
                lines.append("---")
                buildings = [b.name for b in city.buildings]
                lines += buildings
        lines.append("---")
        lines.append(", ".join([str(tile.x), str(tile.y)]))
        text = "\n".join(lines)
        return text

    def show_tile_info(self, tile, mouse):
        text = self.tile_info_text(tile)
        self.show_textbox(mouse, text)
        return

    def show_turn(self):
        text = "Turn: {}\nActive civ: {}".format(self.game.turn, self.game.active_civ().name)
        pos = (self.screen_size[0] - max(self.font.size(line)[0] for line in text.splitlines()), 0)
        self.show_textbox(pos, text)
        return

    def show_textbox(self, pos, text, color=None):
        lines = text.splitlines()
        box = (
            max([self.font.size(line)[0] for line in lines]),
            self.font.get_height() * len(lines)
        )
        x, y = pos
        if x > self.screen_size[0] - box[0]:
            x -= box[0]
        if y > self.screen_size[1] - box[1]:
            y -= box[1]
        tile_text_bg_rect = pg.Rect(
            x, y, box[0], box[1])
        tile_text_bg = self.__draw_rect(pg.Color(0, 0, 0), tile_text_bg_rect)
        for i, line in enumerate(lines):
            tile_text = self.font.render(
                line, 1, (255, 255, 255))
            tile_text_rect = tile_text.get_rect()
            text_pos = (x, y + self.font.get_height() * i)
            tile_text_rect.topleft = text_pos
            self.__blit(tile_text, tile_text_rect)
        return

    def __draw_rect(self, color, rect):
        return pg.draw.rect(self.surface, color, rect)

    def quit_game(self):
        try:
            self.__game_over = True
            if self.__enable_render is True:
                pg.display.quit()
            pg.quit()
        except Exception:
            pass
