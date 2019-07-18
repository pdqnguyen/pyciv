#! /usr/bin/python

import pygame as pg
import math
import sys
from matplotlib.colors import to_rgb

from .bases import BASE_COLORS
from .features import FEATURE_COLORS
from .civilizations import CIV_COLORS


SQRT3 = math.sqrt(3)


def colorname2pg(name):
    rgb = [int(x * 255) for x in to_rgb(name)]
    return pg.Color(*rgb)


class RenderGrid(pg.Surface):
    def __init__(self, board, screen=(1280, 720)):
        self.board = board
        self.width, self.height = screen
        self.radius = self._radius()
        super(RenderGrid, self).__init__((self.width, self.height))

    def _radius(self):
        max_x = self.width / (self.board.shape[0] + 0.5) / SQRT3
        max_y = self.height / (1.5 * self.board.shape[1] + 0.5)
        return min(max_x, max_y)

    def draw_base(self, tile, x_offset=0, y_offset=0):
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

    def draw_features(self, tile, x_offset=0, y_offset=0):
        color = self._get_feature_color(tile.features[-1])
        circle_pos = (
            int(x_offset + 0.5 * SQRT3 * self.radius),
            int(y_offset + self.radius)
        )
        circle_r = int(round(0.5 * self.radius))
        pg.draw.circle(self, color, circle_pos, circle_r)
        return

    def draw_city(self, tile, x_offset=0, y_offset=0):
        color = self._get_civ_color(tile.civ)
        triangle = [
            (x_offset + 0.5 * SQRT3 * self.radius - self.radius / SQRT3, y_offset + 1.5 * self.radius),
            (x_offset + 0.5 * SQRT3 * self.radius + self.radius / SQRT3, y_offset + 1.5 * self.radius),
            (x_offset + 0.5 * SQRT3 * self.radius, y_offset + 0.5 * self.radius)
        ]
        pg.draw.polygon(self, color, triangle)
        return

    def draw_civ(self, tile, x_offset=0, y_offset=0):
        color = self._get_civ_color(tile.civ)
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
            # Tile position offsets
            if tile.y % 2 == 0:
                x_offset = SQRT3 * self.radius * (tile.x)
            else:
                x_offset = SQRT3 * self.radius * (tile.x + 0.5)
            y_offset = 1.5 * self.radius * (tile.y)
            poly = self.draw_base(tile, x_offset=x_offset, y_offset=y_offset)
            if tile.features:
                self.draw_features(tile, x_offset=x_offset, y_offset=y_offset)
            if tile.city:
                self.draw_city(tile, x_offset=x_offset, y_offset=y_offset)
            if tile.civ:
                self.draw_civ(tile, x_offset=x_offset, y_offset=y_offset)
            polygons.append((tile, poly))
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


class RenderGame(object):
    def __init__(self, game, screen=(1280, 720), rate=30, fontsize=36):
        self.game = game
        self.screen = screen
        self.rate = rate
        self.fontsize = fontsize

    def render(self):
        from pygame.locals import QUIT, MOUSEBUTTONDOWN
        grid = RenderGrid(self.game.board, screen=self.screen)
        try:
            pg.init()
            surface = pg.display.set_mode(self.screen, 1)
            font = pg.font.SysFont("Trebuchet", self.fontsize)
            clock = pg.time.Clock()

            polygons = []
            active_city = False

            while True:
                pressed = False
                for ev in pg.event.get():
                    if ev.type == QUIT:
                        pg.quit()
                        sys.exit()
                    if ev.type == MOUSEBUTTONDOWN:
                        pressed = True
                mouse = pg.mouse.get_pos()
                tile, polygon = self.get_tile(grid, mouse)
                surface.blit(grid, (0, 0))
                self.show_turn(surface, font)
                self.show_button(surface, (0, 0), "End turn", font, pressed)
                if tile:
                    self.show_tile_info(surface, tile, mouse, font)
                # Open city menu
                if tile and pressed:
                    if tile.city:
                        active_city = tile.city
                        self.show_production_menu(surface, active_city, polygon, font)
                    else:
                        active_city = None
                elif active_city:
                    self.show_production_menu(surface, active_city, polygon, font)
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
        if tile.city:
            lines.append("{} ({})".format(tile.city.name, tile.city.p))
        header = ", ".join([tile.base] + tile.features)
        if tile.civ:
            header += " ({})".format(tile.civ)
        lines.append(header)
        lines.append("---")
        yields = tile.print_yields().split("\n")
        yields = [y for y in yields if y]
        lines += yields
        if tile.city:
            if tile.city.buildings:
                lines.append("---")
                buildings = [b.name for b in tile.city.buildings]
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
        text = city.name + " ({})\n".format(city.civ)
        text += "Choose production:\n"
        text += "\n".join(city.production_options())
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
                self.game.next_turn()
        else:
            color = pg.Color(0, 0, 0)
        button = font.render(text, 1, (255, 255, 255))
        pg.draw.rect(surface, color, rect)
        surface.blit(button, rect)
        return rect

    def show_turn(self, surface, font):
        text = "Turn: {}\nActive civ: {}".format(self.game.turn, self.game.active_civ())
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
