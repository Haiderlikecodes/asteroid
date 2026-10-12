import math
import random

import pygame

from constants import (
    ASTEROID_START_COUNT,
    BULLET_SPEED,
    FPS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIP_ROTATION_SPEED,
    SHIP_THRUST,
    STARTING_LIVES,
)
from logger import log_event, log_state


def wrap_position(position, radius=0):
    if position.x > SCREEN_WIDTH + radius:
        position.x = -radius
    elif position.x < -radius:
        position.x = SCREEN_WIDTH + radius

    if position.y > SCREEN_HEIGHT + radius:
        position.y = -radius
    elif position.y < -radius:
        position.y = SCREEN_HEIGHT + radius

    return position


class Ship:
    def __init__(self):
        self.position = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.velocity = pygame.Vector2(0, 0)
        self.angle = -90
        self.radius = 18
        self.fire_cooldown = 0.0
        self.invulnerable_time = 0.0

    def reset(self):
        self.position = pygame.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.velocity = pygame.Vector2(0, 0)
        self.angle = -90
        self.fire_cooldown = 0.0
        self.invulnerable_time = 2.0

    def update(self, dt, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle -= SHIP_ROTATION_SPEED * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle += SHIP_ROTATION_SPEED * dt

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            thrust = pygame.Vector2(0, -1).rotate(self.angle) * SHIP_THRUST
            self.velocity += thrust * dt

        self.velocity *= 0.992
        self.position += self.velocity * dt
        wrap_position(self.position, self.radius)

        if self.fire_cooldown > 0:
            self.fire_cooldown = max(0, self.fire_cooldown - dt)
        if self.invulnerable_time > 0:
            self.invulnerable_time = max(0, self.invulnerable_time - dt)

    def shoot(self):
        if self.fire_cooldown > 0:
            return None

        self.fire_cooldown = 0.18
        muzzle = self.position + pygame.Vector2(0, -self.radius - 8).rotate(self.angle)
        bullet_velocity = pygame.Vector2(0, -BULLET_SPEED).rotate(self.angle) + self.velocity
        log_event("ship_fired", direction=self.angle)
        return Bullet(muzzle, bullet_velocity)

    def draw(self, screen, is_thrusting=False):
        if self.invulnerable_time > 0 and int(self.invulnerable_time * 10) % 2 == 0:
            return

        triangle = [
            pygame.Vector2(0, -self.radius),
            pygame.Vector2(self.radius * 0.8, self.radius * 0.8),
            pygame.Vector2(0, self.radius * 0.45),
            pygame.Vector2(-self.radius * 0.8, self.radius * 0.8),
        ]
        points = [self.position + point.rotate(self.angle) for point in triangle]
        pygame.draw.polygon(screen, "white", [(p.x, p.y) for p in points], 2)

        if is_thrusting:
            flame = [
                pygame.Vector2(-4, self.radius * 0.8),
                pygame.Vector2(0, self.radius * 1.4),
                pygame.Vector2(4, self.radius * 0.8),
            ]
            flame_points = [self.position + point.rotate(self.angle) for point in flame]
            pygame.draw.polygon(screen, "orange", [(p.x, p.y) for p in flame_points])


class Bullet:
    def __init__(self, position, velocity):
        self.position = position
        self.velocity = velocity
        self.radius = 3
        self.life = 1.4

    def update(self, dt):
        self.position += self.velocity * dt
        self.life -= dt
        wrap_position(self.position, self.radius)

    def draw(self, screen):
        pygame.draw.circle(screen, "white", (int(self.position.x), int(self.position.y)), self.radius)


class Asteroid:
    def __init__(self, size=3, position=None, velocity=None):
        self.size = size
        self.radius = {3: 42, 2: 24, 1: 14}[size]
        self.position = position if position is not None else pygame.Vector2(random.randrange(0, SCREEN_WIDTH), random.randrange(0, SCREEN_HEIGHT))
        self.velocity = velocity if velocity is not None else pygame.Vector2(random.uniform(-90, 90), random.uniform(-90, 90))
        self.rotation = random.uniform(0, 360)
        self.spin = random.uniform(-50, 50)
        self.vertices = self._generate_vertices()

    def _generate_vertices(self):
        points = []
        for index in range(8):
            angle = math.radians(index * 45 + random.uniform(-8, 8))
            radius = self.radius * random.uniform(0.7, 1.25)
            points.append(pygame.Vector2(math.cos(angle) * radius, math.sin(angle) * radius))
        return points

    def update(self, dt):
        self.position += self.velocity * dt
        self.rotation += self.spin * dt
        wrap_position(self.position, self.radius)

    def draw(self, screen):
        points = [self.position + point.rotate(self.rotation) for point in self.vertices]
        pygame.draw.polygon(screen, "gray40", [(p.x, p.y) for p in points], 2)


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.ship = Ship()
        self.bullets = []
        self.asteroids = []
        self.score = 0
        self.lives = STARTING_LIVES
        self.game_over = False
        self._spawn_asteroids(ASTEROID_START_COUNT)

    def _spawn_asteroids(self, count):
        for _ in range(count):
            while True:
                pos = pygame.Vector2(random.randrange(0, SCREEN_WIDTH), random.randrange(0, SCREEN_HEIGHT))
                if pos.distance_to(self.ship.position) > 180:
                    self.asteroids.append(Asteroid(size=3, position=pos))
                    break

    def split_asteroid(self, asteroid):
        self.score += {3: 20, 2: 50, 1: 100}[asteroid.size]
        if asteroid.size == 1:
            return

        new_size = asteroid.size - 1
        for _ in range(2):
            offset = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
            new_position = asteroid.position + offset * asteroid.radius * 0.8
            new_velocity = asteroid.velocity + offset * random.uniform(30, 120)
            self.asteroids.append(Asteroid(size=new_size, position=new_position, velocity=new_velocity))

    def handle_ship_collision(self):
        if self.ship.invulnerable_time > 0:
            return

        self.lives -= 1
        self.ship.reset()
        log_event("ship_hit", lives=self.lives, score=self.score)

        if self.lives <= 0:
            self.game_over = True
            log_event("game_over", score=self.score)

    def update(self, dt, keys):
        if self.game_over:
            return

        self.ship.update(dt, keys)

        if keys[pygame.K_SPACE]:
            bullet = self.ship.shoot()
            if bullet is not None:
                self.bullets.append(bullet)

        for bullet in self.bullets[:]:
            bullet.update(dt)
            if bullet.life <= 0:
                self.bullets.remove(bullet)
                continue

            for asteroid in self.asteroids[:]:
                if bullet.position.distance_to(asteroid.position) <= bullet.radius + asteroid.radius:
                    self.bullets.remove(bullet)
                    self.asteroids.remove(asteroid)
                    self.split_asteroid(asteroid)
                    log_event("asteroid_destroyed", size=asteroid.size, score=self.score)
                    break

        for asteroid in self.asteroids:
            asteroid.update(dt)

        if not self.asteroids:
            self._spawn_asteroids(ASTEROID_START_COUNT)
            log_event("wave_started", asteroids=len(self.asteroids))

        for asteroid in self.asteroids:
            if asteroid.position.distance_to(self.ship.position) <= asteroid.radius + self.ship.radius:
                self.handle_ship_collision()
                break

    def draw(self, screen):
        for bullet in self.bullets:
            bullet.draw(screen)
        for asteroid in self.asteroids:
            asteroid.draw(screen)

        thrusting = pygame.key.get_pressed()[pygame.K_UP] or pygame.key.get_pressed()[pygame.K_w]
        self.ship.draw(screen, is_thrusting=thrusting)

        score_text = pygame.font.SysFont("consolas", 28).render(f"Score: {self.score}", True, "white")
        lives_text = pygame.font.SysFont("consolas", 28).render(f"Lives: {self.lives}", True, "white")
        screen.blit(score_text, (18, 18))
        screen.blit(lives_text, (SCREEN_WIDTH - 180, 18))

        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))

            title = pygame.font.SysFont("consolas", 72, bold=True).render("GAME OVER", True, "white")
            restart = pygame.font.SysFont("consolas", 32).render("Press Enter to restart", True, "white")
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
            screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, SCREEN_HEIGHT // 2 + 20))


def main():
    print(f"starting asteroids with pygame version: {pygame.version.ver}")
    pygame.init()
    pygame.display.set_caption("Asteroids")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    game = Game()

    while True:
        dt = clock.tick(FPS) / 1000
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and game.game_over:
                game.reset()

        if not game.game_over:
            game.update(dt, keys)

        screen.fill("black")
        game.draw(screen)
        pygame.display.flip()
        log_state()


if __name__ == "__main__":
    main()