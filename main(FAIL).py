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
Fps = float("inf")

simul_speed = 2
friction = -1

G = 3
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
        # self.angle = 0

        self.pos = vector(pos[0], pos[1])
        if vel is None:
            self.vel = vector(0, 0)
        else:
            self.vel = vel

    def calc_gravity(self, otpl):
        force = self.pos - otpl.pos
        distance = force.magnitude()
        if force == vector(0, 0):
            return vector(0, 0)
        force = force.normalize()
        strength = -(G * self.m * otpl.m) / (distance ** 2)
        force = force * strength
        return force

    def pos2rect(self):
        self.pos += self.vel * simul_speed
        self.rect.center = self.pos

    # b = vector(self.pos.x, self.pos.y)
    # a -= b
    # if not a == vector(0,0):
    #	a = a.normalize()
    # self.angle = math.degrees(math.atan2(a.y, a.x))

    def update(self):
        for otpl in self.game.all_sprites:
            if self == otpl:
                continue

            f = self.calc_gravity(otpl)
            self.vel += vector(f.x / self.m, f.y / self.m)

# collision = abs(combinedHitbox-distanceBetween)/combinedHitbox
# collision = 1
# if ((otpl.pos.x - self.pos.x)*(otpl.vel.x - self.vel.x) < 0) or ((otpl.pos.y - self.pos.y)*(otpl.vel.y - self.vel.y) < 0):
#	angle = math.atan2((otpl.pos.y - self.pos.y), (otpl.pos.x - self.pos.x))
#	v1h = self.vel.x*math.cos(angle)+self.vel.y*math.sin(angle)
#	v1v = self.vel.x*math.sin(angle)-self.vel.y*math.cos(angle)
#	v2h = otpl.vel.x*math.cos(angle)+otpl.vel.y*math.sin(angle)
#	v2v = otpl.vel.x*math.sin(angle)-otpl.vel.y*math.cos(angle)
#	nv1h = (v2h - v1h) * (1 + E) / (self.m / otpl.m + 1) + v1h
#	nv2h = (v1h - v2h) * (1 + E) / (otpl.m / self.m + 1) + v2h
#	self.vel.x = (nv1h * math.cos(angle) + v1v * math.sin(angle))# * collision
#	self.vel.y = (nv1h * math.sin(angle) - v1v * math.cos(angle))# * collision
#	otpl.vel.x = (nv2h * math.cos(angle) + v2v * math.sin(angle))# * collision
#	otpl.vel.y = (nv2h * math.sin(angle) - v2v * math.cos(angle))# * collision


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
        self.rad = 20
        self.mpos = (0, 0)

    def new(self):
        poses = [(450, 300, vector(-1, -1).normalize()),
                 (300, 450, vector(-1, 1).normalize()),
                 (450, 600, vector(1, 1).normalize()),
                 (600, 450, vector(1, -1).normalize())
                 ]
        for pos in poses:
            self.all_sprites.add(Planet(self, (pos[0], pos[1]), self.m, pos[2]))
        # for x in range(100):
        #	self.all_sprites.add(Planet(self, (random.randrange(0, screen_width),random.randrange(0, screen_height)), 10))
        self.run()

    def run(self):
        while self.playing:
            # pygame.time.wait(10)
            self.clock.tick(Fps)
            self.events()
            up_t = threading.Thread(target=self.update)
            up_t.start()
            up_t.join()
            dr_t = threading.Thread(target=self.draw)
            dr_t.start()
            dr_t.join()

    # self.update()
    # self.draw()

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
    def reflect_colliding_circles(c1, c2):
        def calculate_mtd(pl1, pl2):
            """source: https://stackoverflow.com/q/345838/1093087"""
            delta = pl1.pos - pl2.pos
            d = delta.magnitude()
            return delta * (pl1.radius + pl2.radius - d) / d

        # inverse masses, mtd, restitution
        im1 = 1.0 / c1.m
        im2 = 1.0 / c2.m
        mtd = calculate_mtd(c1, c2)
        normal_mtd = mtd.normalize()
        restitution = 1

        # impact speed
        v = c1.vel - c2.vel
        vn = normal_mtd * v  # v.dot(normal_mtd)

        # circle moving away from each other already -- return
        # original velocities
        if vn > 0.0:
            return c1.vel, c2.vel

        # collision impulse
        i = (-1.0 * (1.0 + restitution) * vn) / (im1 + im2)
        impulse = normal_mtd * i

        # change in momentum
        print(impulse)
        new_c1_v = c1.vel + (impulse * im1)
        new_c2_v = c2.vel - (impulse * im2)

        return new_c1_v, new_c2_v

    def update(self):
        # self.all_sprites.update()
        for pu in self.all_sprites:
            pu.update()
        for p1 in self.all_sprites:
            for p2 in self.all_sprites:
                if p1 == p2:
                    continue

                distan = p1.pos - p2.pos
                distance_between = distan.magnitude()
                combined_hitbox = p1.radius + p2.radius

                if combined_hitbox > distance_between:
                    c1, c2 = self.reflect_colliding_circles(p1, p2)
                    p1.vel = c1
                    p2.vel = c2
        # tangent = math.atan2(distan.y, distan.x)
        # p1.angle = 2 * tangent - p1.angle
        # p2.angle = 2 * tangent - p2.angle

        # (p1.vel, p2.vel) = (p2.vel, p1.vel)

        # angle = 0.3 * math.pi + tangent
        # p1.pos.x += math.sin(angle)
        # p1.pos.y -= math.cos(angle)
        # p2.pos.x -= math.sin(angle)
        # p2.pos.y += math.cos(angle)
        # p1.pos2rect()

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
