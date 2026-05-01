import pygame
from constants import SCREEN_HEIGHT,SCREEN_WIDTH
from logger import log_state
print(f"starting asteroids with pygame version:{pygame.version.ver}")
print(SCREEN_WIDTH)
print(SCREEN_HEIGHT)
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    while True:
        log_state()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        screen.fill("black")
        pygame.display.flip()
main()