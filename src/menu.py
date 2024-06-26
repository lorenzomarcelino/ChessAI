import pygame
import sys

# Inicialização do pygame
pygame.init()

# Configurações da tela
info = pygame.display.Info()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
pygame.display.set_caption("Chess Game")

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Fonte
font = pygame.font.Font(None, 74)

# Função para desenhar o menu
def draw_menu():
    screen.fill(WHITE)
    title_text = font.render("Chess Game", True, BLACK)
    play_text = font.render("Play", True, BLACK)
    quit_text = font.render("Quit", True, BLACK)
    screen.blit(title_text, (info.current_w // 2 - title_text.get_width() // 2, 150))
    screen.blit(play_text, (info.current_w // 2 - play_text.get_width() // 2, 250))
    screen.blit(quit_text, (info.current_w // 2 - quit_text.get_width() // 2, 350))

# Função principal do menu
def main_menu(main_game_loop):
    while True:
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if info.current_w // 2 - 50 <= mouse_pos[0] <= info.current_w // 2 + 50 and 250 <= mouse_pos[1] <= 300:
                    main_game_loop()
                if info.current_w // 2 - 50 <= mouse_pos[0] <= info.current_w // 2 + 50 and 350 <= mouse_pos[1] <= 400:
                    pygame.quit()
                    sys.exit()
        pygame.display.flip()
