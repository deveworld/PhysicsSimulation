import math
import os
import sys
import threading

import pygame

os.environ['SDL_VIDEO_CENTERED'] = "True"

Version = 'Alpha'
Title = 'Physics Simulation ' + Version
screen_width = 900
screen_height = 900
Fps = float("120")

simul_speed = 1
friction = -1

G = 2
E = 1
WALL_E = 0.7

vector = pygame.math.Vector2


def loadify(imgname):
    return pygame.image.load(imgname).convert_alpha()


class Planet(pygame.sprite.Sprite):

    def __init__(self, game, pos, m, vel=None, radius=None):
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.m = m
        if radius is None:
            self.radius = self.m / 2
        else:
            self.radius = radius
        self.image = pygame.transform.scale(loadify('data/planet.png'), (int(self.radius * 2), int(self.radius * 2)))
        self.image.set_colorkey((0, 255, 0))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.center = pos

        self.pos = vector(pos[0], pos[1])
        if vel is None:
            self.vel = vector(0, 0)
        else:
            self.vel = vel

    def calc_gravity(self, otpl):
        force = self.pos - otpl.pos
        if force == vector(0, 0):
            return vector(0, 0)
        distance = force.magnitude()
        force = force.normalize()
        strength = (G * self.m * otpl.m) / (distance ** 2)
        force = force * strength * -1
        return force

    def pos2rect(self):
        self.pos += self.vel * simul_speed
        self.rect.center = self.pos

    def update(self):
        for otpl in self.game.all_sprites:
            if self == otpl:
                continue

            f = self.calc_gravity(otpl)
            self.vel += vector(f.x / self.m, f.y / self.m) * simul_speed


class Simulation:

    def __init__(self):
        self.playing = True
        self.all_sprites = pygame.sprite.Group()
        pygame.init()
        icon = pygame.image.load('data/icon.png')  # By Djhé
        pygame.display.set_icon(icon)
        flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((screen_width, screen_height), flags, vsync=1)
        pygame.display.set_caption(Title)
        self.clock = pygame.time.Clock()
        self.running = True
        self.m = 100
        self.rad = 50
        self.mpos = (0, 0)

    def new(self):
        poses = [(450, 300, vector(1, 1).normalize()),
                 (300, 450, vector(1, -1).normalize()),
                 (450, 600, vector(-1, -1).normalize()),
                 (600, 450, vector(-1, 1).normalize())
                 ]
        for pos in poses:
            self.all_sprites.add(Planet(self, (pos[0], pos[1]), self.m, pos[2], self.rad))
        self.run()

    def run(self):
        while self.playing:
            self.clock.tick(Fps)
            self.events()
            up_t = threading.Thread(target=self.update)
            up_t.start()
            up_t.join()
            dr_t = threading.Thread(target=self.draw)
            dr_t.start()
            dr_t.join()

    def get_mouse_force(self, nowpos):
        if self.mpos == nowpos:
            return vector(0, 0), 0
        else:
            direction = nowpos - self.mpos
            angle = math.degrees(math.atan2(direction.y, direction.x))
            direct = math.floor(direction.magnitude() / 500)
            force = vector(math.cos(math.radians(angle)), math.sin(math.radians(angle))).normalize() * direct
            return force, direct

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mpos = vector(event.pos[0], event.pos[1])
            if event.type == pygame.MOUSEBUTTONUP:
                nowpos = vector(event.pos[0], event.pos[1])
                self.all_sprites.add(Planet(self, self.mpos, self.m, self.get_mouse_force(nowpos)[0], self.rad))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.m -= 100
                    if self.m < 100:
                        self.m = 100
                if event.key == pygame.K_RIGHT:
                    self.m += 100
                    if self.m > 1600:
                        self.m = 1600
                if event.key == pygame.K_UP:
                    self.rad += 20
                    if self.rad > 200:
                        self.rad = 200
                if event.key == pygame.K_DOWN:
                    self.rad -= 20
                    if self.rad < 20:
                        self.rad = 20
                if event.key == pygame.K_SPACE:
                    global simul_speed
                    if simul_speed == 1:
                        simul_speed = 0.01
                    elif simul_speed == 0.01:
                        simul_speed = 1

    @staticmethod
    def reflect_colliding_circles(a, b):
        delta = vector(a.rect.center[0], a.rect.center[1]) - vector(b.rect.center[0], b.rect.center[1])
        d = delta.length()
        mtd = delta * ((a.radius+b.radius)-d)/d

        im1 = 1 / a.m
        im2 = 1 / b.m

        a.pos += mtd * (im1 / (im1 + im2))
        b.pos -= mtd * (im2 / (im1 + im2))

        v = a.vel - b.vel
        vn = v.dot(mtd.normalize())
        if vn > 0.0:
            return

        i = (-1 * (1.0 + E) * vn) / (im1 + im2)
        impulse = mtd.normalize() * i
        if abs(impulse.x) < 0.01:
            impulse.x = 0
        if abs(impulse.y) < 0.01:
            impulse.y = 0
        if impulse == vector(0, 0):
            return

        a.vel += impulse * im1
        b.vel -= impulse * im2

    def update(self):
        self.all_sprites.update()
        for p1 in self.all_sprites:
            for p2 in self.all_sprites:
                if p1 == p2:
                    continue

                distan = vector(p1.rect.center[0], p1.rect.center[1]) - vector(p2.rect.center[0], p2.rect.center[1])
                distance_between = distan.length()
                combined_hitbox = p1.radius + p2.radius

                if combined_hitbox > distance_between:
                    self.reflect_colliding_circles(p1, p2)

        for pl in self.all_sprites:
            pl.pos2rect()
            if pl.pos.x - pl.radius < 0:
                pl.pos.x = pl.radius
                pl.vel.x = abs(pl.vel.x) * WALL_E
            elif pl.pos.x + pl.radius > self.screen.get_size()[0]:
                pl.pos.x = self.screen.get_size()[0] - pl.radius
                pl.vel.x = abs(pl.vel.x) * -1 * WALL_E

            if pl.pos.y - pl.radius <= 0:
                pl.pos.y = pl.radius
                pl.vel.y = abs(pl.vel.y) * WALL_E
            elif pl.pos.y + pl.radius >= self.screen.get_size()[1]:
                pl.pos.y = self.screen.get_size()[1] - pl.radius
                pl.vel.y = abs(pl.vel.y) * -1 * WALL_E

    def draw(self):
        self.screen.fill((20, 20, 20))
        self.all_sprites.draw(self.screen)
        self.draw_text('FPS : ' + str(round(self.clock.get_fps(), 1)), 22, (0, 255, 0), 100, 10)
        self.draw_text('m : ' + str(round(self.m, 1)), 22, (0, 255, 0), 100, 40)
        self.draw_text('rad : ' + str(round(self.rad, 1)), 22, (0, 255, 0), 100, 70)
        nowpos = vector(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
        self.draw_text('Mouse_Force : ' + str(self.get_mouse_force(nowpos)[1]), 22, (0, 255, 0), 100, 100)
        pygame.display.flip()

    def draw_text(self, text, size, color, x, y):
        font = pygame.font.Font(pygame.font.match_font('malgungothic'), size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)
        return text_rect


if __name__ == '__main__':
    simul = Simulation()
    while simul.running:
        simul.new()
    pygame.quit()
    sys.exit()
