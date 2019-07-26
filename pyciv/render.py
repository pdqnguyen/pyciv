#! /usr/bin/python

import pygame as pg
import math
import os
import sys
from matplotlib.colors import to_rgb

from .bases import BASE_COLORS
from .features import FEATURE_COLORS
from .civilizations import CIV_COLORS
from .menu import PopupMenu


SQRT3 = math.sqrt(3)


def colorname2pg(name):
    rgb = [int(x * 255) for x in to_rgb(name)]
    return pg.Color(*rgb)


class RenderGrid(pg.Surface):
    def __init__(self, board, civs, screen=(1280, 720)):
        self.board = board
        self.civs = civs
        self.width, self.height = screen
        self.radius = self._radius()
        super(RenderGrid, self).__init__((self.width, self.height))

    def _radius(self):
        max_x = self.width / (self.board.shape[0] + 0.5) / SQRT3
        max_y = self.height / (1.5 * self.board.shape[1] + 0.5)
        return min(max_x, max_y)

    def _xy_offset(self, tile):
        # Tile position offsets
        if tile.y % 2 == 0:
            x_offset = SQRT3 * self.radius * (tile.x)
        else:
            x_offset = SQRT3 * self.radius * (tile.x + 0.5)
        y_offset = 1.5 * self.radius * (tile.y)
        return x_offset, y_offset

    def draw_base(self, tile):
        x_offset, y_offset = self._xy_offset(tile)
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
        color = self._get_base_color(tile.base)
        # Hex tile
        poly = pg.draw.polygon(self, color, points)
        # Black outline
        pg.draw.polygon(self, pg.Color(0, 0, 0), points, 2)
        return poly

    def draw_features(self, tile):
        x_offset, y_offset = self._xy_offset(tile)
        color = self._get_feature_color(tile.features[-1])
        circle_pos = (
            int(x_offset + 0.5 * SQRT3 * self.radius),
            int(y_offset + self.radius)
        )
        circle_r = int(round(0.5 * self.radius))
        pg.draw.circle(self, color, circle_pos, circle_r)
        return

    def draw_city(self, tile, color):
        x_offset, y_offset = self._xy_offset(tile)
        triangle = [
            (x_offset + 0.5 * SQRT3 * self.radius - self.radius / SQRT3, y_offset + 1.5 * self.radius),
            (x_offset + 0.5 * SQRT3 * self.radius + self.radius / SQRT3, y_offset + 1.5 * self.radius),
            (x_offset + 0.5 * SQRT3 * self.radius, y_offset + 0.5 * self.radius)
        ]
        pg.draw.polygon(self, color, triangle)
        return

    def draw_civ(self, civ, x_offset=0, y_offset=0):
        color = self._get_civ_color(civ.name)
        for city in civ:
            self.draw_city(city.tiles[0], color)
            for tile in city:
                x_offset, y_offset = self._xy_offset(tile)
                start_pos = (
                    int(x_offset + 0.5 * self.radius),
                    int(y_offset + 0.5 * self.radius)
                )
                end_pos = (
                    int(x_offset + 1.5 * self.radius),
                    int(y_offset + 1.5 * self.radius)
                )
                pg.draw.line(self, color, start_pos, end_pos, 4)
        return

    def draw(self):
        polygons = []
        for tile in self.board:
            poly = self.draw_base(tile)
            polygons.append((tile, poly))
            if tile.features:
                self.draw_features(tile)
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


def menu_data():
    data = (
        'Main',
        'End turn',
        'Close menu',
        'Quit game',
    )
    return data


def city_menu_data(city):
    prod_current = 'Production - {} ({:.1f}/{})'.format(
        city.prod.name,
        city.prod_progress,
        city.prod.cost['production']
    ) if city.prod else 'Production'
    prod_options = city.prod_options() if city.prod_options() else ['None']
    buildings = [b.name for b in city.buildings]
    data = (
        city.name,
        (
            prod_current,
            (
                'Choose production',
                *prod_options
            ),
            (
                'Buildings',
                *buildings
            )
        ),
        'End turn',
        'Close menu',
    )
    return data


def handle_menu(e, game, tile, city, civ):
    #print('Menu event: %s --- %d: %s' % (e.name, e.item_id, e.text))
    if e.name == 'Choose production...':
        if e.text != 'None':
            city.begin_prod(e.text)
    elif e.text == 'Close menu':
        return
    elif e.text == 'End turn':
        game.end_turn()
    elif e.text == 'Quit game':
        quit()


class RenderGame(object):
    def __init__(self, game, screen=(1280, 720), rate=30, fontsize=36):
        self.game = game
        self.screen = screen
        self.rate = rate
        self.fontsize = fontsize
        self.active_city = False

    def render(self):
        os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
        from pygame.locals import QUIT, KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP, USEREVENT
        grid = RenderGrid(self.game.board, self.game.civs, screen=self.screen)
        try:
            pg.init()
            surface = pg.display.set_mode(self.screen, 1)
            font = pg.font.SysFont("Trebuchet", self.fontsize)
            clock = pg.time.Clock()

            # game loop
            while True:
                if self.game.active_civ().name not in self.game.humans:
                    self.game.cpu_turn()
                # render loop
                active_tile = None
                active_city = None
                while True:
                    if self.game.active_civ().name not in self.game.humans:
                        break
                    mouse = pg.mouse.get_pos()
                    tile, polygon = self.get_tile(grid, mouse)
                    city = self.game.get_city(tile)
                    civ = self.game.get_civ(tile)
                    pressed = False
                    for ev in pg.event.get():
                        if ev.type == QUIT:
                            pg.quit()
                            sys.exit()
                        if ev.type == MOUSEBUTTONDOWN:
                            pressed = True
                        if ev.type == MOUSEBUTTONUP:
                            if city and city.tiles[0] == tile:
                                active_tile = tile
                                active_city = city
                                PopupMenu(city_menu_data(active_city))#, pos=(0, 0))
                            else:
                                pass #PopupMenu(menu_data())
                        elif ev.type == USEREVENT:
                            if ev.code == 'MENU':
                                handle_menu(ev, self.game, active_tile, active_city, civ)
                        elif ev.type == KEYDOWN:
                            keypress = pg.key.get_pressed()
                            if ev.key == pg.K_c and pg.key.get_mods() & pg.KMOD_CTRL:
                                raise KeyboardInterrupt
                            elif ev.key == pg.K_RETURN and pg.key.get_mods() & pg.KMOD_SHIFT:
                                self.game.end_turn()
                    surface.blit(grid, (0, 0))
                    self.show_turn(surface, font)
                    self.show_button(surface, (0, 0), "End turn", font, pressed)
                    if tile:
                        self.show_tile_info(surface, tile, mouse, font)
                    # Open city menu
                    if tile and pressed:
                        self.active_city = city
                        if self.active_city:
                            self.show_production_menu(surface, self.active_city, polygon, font)
                    elif self.active_city:
                        self.show_production_menu(surface, self.active_city, polygon, font)
                    pg.display.update()
                    clock.tick(self.rate)
        finally:
            pg.quit()

    def get_tile(self, grid, mouse):
        polygons = grid.draw()
        for t, p in polygons:
            if p.inflate(-3, -3).collidepoint(mouse):
                return t, p
        return None, None

    def tile_info_text(self, tile):
        lines = []
        city = self.game.get_city(tile)
        civ = self.game.get_civ(tile)
        if city:
            lines.append("{} ({}){}".format(city.name, city.pp, "*" if city.capital else 0))
        header = ", ".join([tile.base] + tile.features)
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

    def show_tile_info(self, surface, tile, mouse, font):
        fontheight = font.get_height()
        text = self.tile_info_text(tile)
        self.show_textbox(surface, mouse, text, font)
        return

    def show_production_menu(self, surface, city, polygon, font):
        text = city.name + " ({}){}\n".format(city.civ, "*" if city.capital else 0)
        if city.prod:
            text += "Current production:\n{}\n".format(city.prod.name)
        text += "Choose production:\n"
        text += "\n".join(city.prod_options())
        lines = text.splitlines()
        x = self.screen[0] - max(font.size(line)[0] for line in lines)
        y = self.screen[1] - font.get_height() * len(lines)
        pos = (x, y)
        self.show_textbox(surface, pos, text, font)

    def show_button(self, surface, pos, text, font, pressed):
        mouse = pg.mouse.get_pos()
        click = pg.mouse.get_pressed()
        box = (font.size(text)[0], font.get_height())
        rect = pg.Rect((pos[0], pos[1], box[0], box[1]))
        if rect.collidepoint(mouse):
            color = pg.Color(100, 100, 100)
            if pressed:
                self.game.end_turn()
        else:
            color = pg.Color(0, 0, 0)
        button = font.render(text, 1, (255, 255, 255))
        pg.draw.rect(surface, color, rect)
        surface.blit(button, rect)
        return rect

    def show_turn(self, surface, font):
        text = "Turn: {}\nActive civ: {}".format(self.game.turn, self.game.active_civ().name)
        pos = (self.screen[0] - max(font.size(line)[0] for line in text.splitlines()), 0)
        self.show_textbox(surface, pos, text, font)
        return

    def show_textbox(self, surface, pos, text, font, color=None):
        lines = text.splitlines()
        box = (
            max([font.size(line)[0] for line in lines]),
            font.get_height() * len(lines)
        )
        tile_text_bg_rect = pg.Rect(
            pos[0], pos[1], box[0], box[1])
        tile_text_bg = pg.draw.rect(
            surface, pg.Color(0, 0, 0), tile_text_bg_rect)
        for i, line in enumerate(lines):
            tile_text = font.render(
                line, 1, (255, 255, 255))
            tile_text_rect = tile_text.get_rect()
            text_pos = (pos[0], pos[1] + font.get_height() * i)
            tile_text_rect.topleft = text_pos
            surface.blit(tile_text, tile_text_rect)
        return
