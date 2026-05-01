import pygame
from constants import SCREEN_HEIGHT,SCREEN_WIDTH
from logger import log_state
print(f"starting asteroids with pygame version:{pygame.version.ver}")
print(SCREEN_WIDTH)
print(SCREEN_HEIGHT)
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    dt = 0
    while True:
        dt = clock.tick(60)/1000
        log_state()
        print(dt)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 
        screen.fill("black")
        pygame.display.flip()
main()