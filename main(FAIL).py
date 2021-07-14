import os
import csv
import sys
import copy
import math
import time
import random
import pygame
import threading
import pandas as pd

os.environ['SDL_VIDEO_CENTERED'] = "True"

Version = 'Alpha'
Title = 'Physics Simulation '+Version
screen_width = 1900
screen_height = 995
Fps = float("inf")

simul_speed = 1

G = 100

vector = pygame.math.Vector2

def loadify(imgname):
	return pygame.image.load(imgname).convert_alpha()

class Hole(pygame.sprite.Sprite):
	def __init__(self, game):
		pygame.sprite.Sprite.__init__(self)
		self.game = game
		self.image = pygame.transform.scale(loadify('data/planet.png'), (300, 300))
		self.image.set_colorkey((0, 255, 0))
		self.mask = pygame.mask.from_surface(self.image)
		self.rect = self.image.get_rect()
		self.rect.center = (screen_width/2, screen_height/2)
		self.m = 300
		self.current_angle = 0

		self.pos = vector(screen_width/2, screen_height/2)
		self.vel = vector(0, 0)
		self.acc = vector(0, 0)

class Planet(pygame.sprite.Sprite):

	def __init__(self, game, pos, m):
		pygame.sprite.Sprite.__init__(self)
		self.game = game
		self.image = pygame.transform.scale(loadify('data/planet.png'), (m, m))
		self.image.set_colorkey((0, 255, 0))
		self.mask = pygame.mask.from_surface(self.image)
		self.rect = self.image.get_rect()
		self.rect.center = pos
		self.m = m
		self.current_angle = 0

		self.pos = vector(pos[0], pos[1])
		self.vel = vector(0, 0)
		self.acc = vector(0, 0)

	def attract(self, otpl):
		force = vector(0, 0)
		if not otpl == self:
			force = self.pos - otpl.pos
			distance = force.magnitude()
			if distance > otpl.m*50:
				return vector(0, 0)
			if distance == 0:
				return vector(0, 0)
			force = force.normalize()
			F = (G * self.m * otpl.m) / (distance*distance)
			force = vector(F*force, F*force)
		return force

	def applyForce(self, force):
		re_force = vector(force.x/self.m, force.y/self.m)
		self.acc += re_force

	def move(self):
		self.acc += self.vel * -1
		self.vel += self.acc
		#if abs(self.vel.x) > 10:
		#	self.vel.x = math.copysign(self.vel.x, 1)
		#if abs(self.vel.y) > 10:
		#	self.vel.y = math.copysign(self.vel.y, 1)
		self.pos += self.vel * self.game.dt

		#r = self.m/2
		#if self.pos.x+r > self.game.screen.get_size()[0]:
		#	self.pos.x = self.game.screen.get_size()[0]-r
		#	self.vel.x = self.vel.x * -1
		#elif self.pos.x-r < 0:
		#	self.vel.x = self.vel.x * -1
		#	self.pos.x = r
		#if self.pos.y+r > self.game.screen.get_size()[1]:
		#	self.pos.y = self.game.screen.get_size()[1]-r
		#elif self.pos.y-r < 0:
		#	self.vel.y = self.vel.y * -1
		#	self.pos.y = r
		#	self.acc = vector(0, 0)

	def update(self):
		self.move()
		self.rect.center = self.pos
		v = -self.attract(self.game.hole)
		self.applyForce(v)

		self.move()
				#back = vector(self.rect.center[0], self.rect.center[1])
				#self.rect.center = self.pos
				#if pygame.sprite.collide_mask(self, otpl):
				#	self.rect.center = back
				#	if (self.pos.x == self.rect.center[0]) and (self.pos.y == self.rect.center[1]):
				#		self.kill()

				#collides = pygame.sprite.spritecollide(self, self.game.all_sprites, False, pygame.sprite.collide_mask)
				#for environment in collides:
				#	if environment != self:
				#		overlap = self.pos - environment.pos
				#		angle = 180-math.degrees(math.atan2(overlap.y, overlap.x))
				#		self.rect.center = (self.rect.center[0]+math.cos(math.radians(angle)), self.rect.center[1]+math.sin(math.radians(angle)))

class Simulation:

	def __init__(self):
		pygame.init()
		icon = pygame.image.load('data/icon.png') # By Djhé
		pygame.display.set_icon(icon)
		flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE
		self.screen = pygame.display.set_mode((screen_width, screen_height), flags, vsync=1)
		pygame.display.set_caption(Title)
		self.clock = pygame.time.Clock()
		self.running = True
		self.dt = 0
		self.m = 100

	def new(self):
		self.all_sprites = pygame.sprite.Group()
		self.hole = Hole(self)
		self.all_sprites.add(self.hole)
		self.run()

	def run(self):
		self.playing = True
		while self.playing:
			self.dt = self.clock.tick(Fps)*simul_speed
			self.events()
			up_t = threading.Thread(target=self.update)
			up_t.start()
			up_t.join()
			dr_t = threading.Thread(target=self.draw)
			dr_t.start()
			dr_t.join()
			#self.update()
			#self.draw()

	def update(self):
		self.all_sprites.update()
		self.all_sprites.add(Planet(self, pygame.mouse.get_pos(), self.m))
		pl1 = self.hole
		for pl2 in self.all_sprites:
			if pl1 == pl2:
				continue

			distan = pl1.pos - pl2.pos
			distanceBetween = distan.magnitude()
			combinedHitbox = pl1.m/2 + pl2.m/2
			overlap = vector(combinedHitbox, combinedHitbox)

			if combinedHitbox >= distanceBetween:
				pl2.kill()

	def events(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				if self.playing:
					self.playing = False
				self.running = False
			#elif event.type == pygame.MOUSEBUTTONDOWN:
			#	self.all_sprites.add(Planet(self, event.pos, self.m))
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_LEFT:
					self.m += 10
					if self.m > 500:
						self.m = 500
				if event.key == pygame.K_RIGHT:
					self.m -= 10
					if self.m < 10:
						self.m = 10

	def draw(self):
		self.screen.fill((20, 20, 20))
		self.all_sprites.draw(self.screen)
		self.draw_text('FPS : '+str(round(self.clock.get_fps(), 1)), 22, (0, 255, 0), 100, 10)
		pygame.display.flip()

	def draw_text(self, text, size, color, x, y):
		font = pygame.font.Font(pygame.font.match_font('malgungothic'), size)
		text_surface = font.render(text, True, color)
		text_rect = text_surface.get_rect()
		text_rect.midtop = (x, y)
		self.screen.blit(text_surface, text_rect)
		return text_rect

if __name__ == '__main__':

	try:
		os.chdir(sys._MEIPASS)
	except:
		os.chdir(os.getcwd())

	simul = Simulation()
	while simul.running:
		simul.new()
	pygame.quit()
	sys.exit()