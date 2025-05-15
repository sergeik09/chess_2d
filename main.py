import pygame
import sys
from typing import List, Tuple, Optional, Set
import math
import pygame_menu
import random
import os

# Initialize Pygame
pygame.init()

# Constants
WINDOW_SIZE = 600
BOARD_SIZE = 8
SQUARE_SIZE = WINDOW_SIZE // BOARD_SIZE
MESSAGE_BOX_HEIGHT = 60
TOTAL_HEIGHT = WINDOW_SIZE + MESSAGE_BOX_HEIGHT

# Load font
FONT_PATH = os.path.join('assets', 'fonts', 'new_font.ttf')
FONT_SIZE = 16
MENU_FONT_SIZE = 24

# Загрузка шрифта
try:
    GAME_FONT = pygame.font.Font(FONT_PATH, FONT_SIZE)
except Exception as e:
    print(f"Error loading font: {e}")
    GAME_FONT = pygame.font.SysFont('Arial', FONT_SIZE)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
HIGHLIGHT = (255, 255, 0, 128)
RED_HIGHLIGHT = (255, 0, 0, 128)
BLUE = (0, 0, 255)
MOVE_HIGHLIGHT = (0, 255, 0, 128)
MESSAGE_BOX_COLOR = (50, 50, 50)
MESSAGE_BOX_BORDER = (100, 100, 100)

# Game text translations
COLORS = {
    'white': 'White',
    'black': 'Black'
}

MESSAGES = {
    'turn': "{}'s turn",
    'check': '{} is in check!',
    'checkmate': 'Checkmate! {} wins!',
}

# Загрузка изображений
PIECES_IMAGES = {}
BOARD_IMAGE = None

def load_images():
    global PIECES_IMAGES, BOARD_IMAGE
    pieces = ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']
    colors = ['white', 'black']
    
    piece_width = int(SQUARE_SIZE * 0.6)  # Width remains at 60% of square
    piece_height = int(SQUARE_SIZE * 0.7)  # Height is 70% of square for slight vertical stretch
    
    for piece in pieces:
        for color in colors:
            path = os.path.join('assets', 'chess_green', f'{color}_{piece}.png')
            img = pygame.image.load(path)
            img = pygame.transform.scale(img, (piece_width, piece_height))
            PIECES_IMAGES[f'{color}_{piece}'] = img
    
    # Загрузка изображения доски
    board_path = os.path.join('assets', 'chess_green', 'board.png')
    BOARD_IMAGE = pygame.image.load(board_path)
    BOARD_IMAGE = pygame.transform.scale(BOARD_IMAGE, (WINDOW_SIZE, WINDOW_SIZE))

# Initialize the screen
screen = pygame.display.set_mode((WINDOW_SIZE, TOTAL_HEIGHT))
pygame.display.set_caption('Chess')

class Piece:
    def __init__(self, color: str, piece_type: str, position: Tuple[int, int]):
        self.color = color
        self.piece_type = piece_type
        self.position = position
        self.has_moved = False

    def draw(self, surface: pygame.Surface):
        piece_key = f'{self.color}_{self.piece_type}'
        if piece_key in PIECES_IMAGES:
            piece_img = PIECES_IMAGES[piece_key]
            piece_width = piece_img.get_width()
            piece_height = piece_img.get_height()
            # Calculate center position
            x = self.position[1] * SQUARE_SIZE + (SQUARE_SIZE - piece_width) // 2
            y = self.position[0] * SQUARE_SIZE + (SQUARE_SIZE - piece_height) // 2
            surface.blit(piece_img, (x, y))

class ChessBoard:
    def __init__(self):
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.selected_piece = None
        self.valid_moves = []
        self.current_turn = 'white'
        self.initialize_board()
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
        self.is_check = False
        self.is_checkmate = False
        self.game_over = False
        self.ai_move_from = None
        self.ai_move_to = None
        self.ai_move_display_time = 0

    def initialize_board(self):
        # Initialize pawns
        for col in range(BOARD_SIZE):
            self.board[1][col] = Piece('black', 'pawn', (1, col))
            self.board[6][col] = Piece('white', 'pawn', (6, col))

        # Initialize other pieces
        piece_order = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']
        for col in range(BOARD_SIZE):
            self.board[0][col] = Piece('black', piece_order[col], (0, col))
            self.board[7][col] = Piece('white', piece_order[col], (7, col))

    def draw(self, surface: pygame.Surface):
        # Отрисовка доски
        if BOARD_IMAGE:
            surface.blit(BOARD_IMAGE, (0, 0))
        
        # Отрисовка фигур
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece:
                    piece.draw(surface)

        current_time = pygame.time.get_ticks()
        if self.ai_move_from and self.ai_move_to and current_time - self.ai_move_display_time < 1000:
            # Подсветка начальной позиции ИИ
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(s, (*BLUE[:3], 128), s.get_rect())
            surface.blit(s, (self.ai_move_from[1] * SQUARE_SIZE, self.ai_move_from[0] * SQUARE_SIZE))
            
            # Подсветка конечной позиции ИИ
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(s, (*RED_HIGHLIGHT[:3], 128), s.get_rect())
            surface.blit(s, (self.ai_move_to[1] * SQUARE_SIZE, self.ai_move_to[0] * SQUARE_SIZE))
        elif current_time - self.ai_move_display_time >= 1000:
            self.ai_move_from = None
            self.ai_move_to = None
            
        if self.selected_piece and not (self.ai_move_from and self.ai_move_to):
            row, col = self.selected_piece.position
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(s, HIGHLIGHT, s.get_rect())
            surface.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

            for move in self.valid_moves:
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(s, MOVE_HIGHLIGHT, s.get_rect())
                surface.blit(s, (move[1] * SQUARE_SIZE, move[0] * SQUARE_SIZE))

        if self.is_check:
            king_pos = self.white_king_pos if self.current_turn == 'white' else self.black_king_pos
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(s, RED_HIGHLIGHT, s.get_rect())
            surface.blit(s, (king_pos[1] * SQUARE_SIZE, king_pos[0] * SQUARE_SIZE))

    def get_piece_at(self, pos: Tuple[int, int]) -> Optional[Piece]:
        row, col = pos
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return self.board[row][col]
        return None

    def is_valid_position(self, pos: Tuple[int, int]) -> bool:
        row, col = pos
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def get_all_valid_moves(self, piece: Piece, check_for_check: bool = True) -> List[Tuple[int, int]]:
        valid_moves = []
        row, col = piece.position

        def add_move(new_row: int, new_col: int, continuous: bool = False) -> bool:
            if not self.is_valid_position((new_row, new_col)):
                return False
            
            target_piece = self.board[new_row][new_col]
            if target_piece is None:
                valid_moves.append((new_row, new_col))
                return True
            elif target_piece.color != piece.color:
                valid_moves.append((new_row, new_col))
                return False
            return False

        if piece.piece_type == 'pawn':
            direction = 1 if piece.color == 'black' else -1
            
            # Move forward
            if self.is_valid_position((row + direction, col)) and not self.board[row + direction][col]:
                valid_moves.append((row + direction, col))
                # Initial two-square move
                if not piece.has_moved and not self.board[row + 2*direction][col]:
                    valid_moves.append((row + 2*direction, col))
            
            # Capture diagonally
            for dcol in [-1, 1]:
                new_col = col + dcol
                new_row = row + direction
                if self.is_valid_position((new_row, new_col)):
                    target = self.board[new_row][new_col]
                    if target and target.color != piece.color:
                        valid_moves.append((new_row, new_col))

        elif piece.piece_type == 'rook':
            for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                current_row = row + direction[0]
                current_col = col + direction[1]
                while self.is_valid_position((current_row, current_col)):
                    if not add_move(current_row, current_col, True):
                        break
                    current_row += direction[0]
                    current_col += direction[1]

        elif piece.piece_type == 'knight':
            moves = [
                (row + 2, col + 1), (row + 2, col - 1),
                (row - 2, col + 1), (row - 2, col - 1),
                (row + 1, col + 2), (row + 1, col - 2),
                (row - 1, col + 2), (row - 1, col - 2)
            ]
            for move in moves:
                if self.is_valid_position(move):
                    target = self.board[move[0]][move[1]]
                    if not target or target.color != piece.color:
                        valid_moves.append(move)

        elif piece.piece_type == 'bishop':
            for direction in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                current_row = row + direction[0]
                current_col = col + direction[1]
                while self.is_valid_position((current_row, current_col)):
                    if not add_move(current_row, current_col, True):
                        break
                    current_row += direction[0]
                    current_col += direction[1]

        elif piece.piece_type == 'queen':
            # Combine rook and bishop moves
            for direction in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                current_row = row + direction[0]
                current_col = col + direction[1]
                while self.is_valid_position((current_row, current_col)):
                    if not add_move(current_row, current_col, True):
                        break
                    current_row += direction[0]
                    current_col += direction[1]

        elif piece.piece_type == 'king':
            for drow in [-1, 0, 1]:
                for dcol in [-1, 0, 1]:
                    if drow == 0 and dcol == 0:
                        continue
                    new_row, new_col = row + drow, col + dcol
                    if self.is_valid_position((new_row, new_col)):
                        target = self.board[new_row][new_col]
                        if not target or target.color != piece.color:
                            valid_moves.append((new_row, new_col))

        # Filter moves that would put or leave the king in check
        if check_for_check:
            valid_moves = [move for move in valid_moves if not self.would_be_in_check(piece, move)]

        return valid_moves

    def would_be_in_check(self, piece: Piece, move: Tuple[int, int]) -> bool:
        # Make a temporary move
        original_pos = piece.position
        captured_piece = self.board[move[0]][move[1]]
        self.board[move[0]][move[1]] = piece
        self.board[original_pos[0]][original_pos[1]] = None
        piece.position = move

        # Update king position if moving king
        if piece.piece_type == 'king':
            if piece.color == 'white':
                self.white_king_pos = move
            else:
                self.black_king_pos = move

        # Check if the king is in check
        king_pos = self.white_king_pos if piece.color == 'white' else self.black_king_pos
        in_check = self.is_position_under_attack(king_pos, piece.color)

        # Undo the move
        self.board[original_pos[0]][original_pos[1]] = piece
        self.board[move[0]][move[1]] = captured_piece
        piece.position = original_pos

        # Restore king position if we moved it
        if piece.piece_type == 'king':
            if piece.color == 'white':
                self.white_king_pos = original_pos
            else:
                self.black_king_pos = original_pos

        return in_check

    def is_position_under_attack(self, pos: Tuple[int, int], friendly_color: str) -> bool:
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece and piece.color != friendly_color:
                    # Get valid moves without checking for check (to avoid infinite recursion)
                    moves = self.get_all_valid_moves(piece, check_for_check=False)
                    if pos in moves:
                        return True
        return False

    def is_in_checkmate(self) -> bool:
        # Get all pieces of the current player
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece and piece.color == self.current_turn:
                    # If any piece has valid moves, it's not checkmate
                    if self.get_all_valid_moves(piece):
                        return False
        return True

    def check_pawn_promotion(self, piece: Piece, end_row: int):
        """Check if a pawn should be promoted and promote it to a queen if necessary"""
        if piece.piece_type == 'pawn':
            # Check if white pawn reached top row (0) or black pawn reached bottom row (7)
            if (piece.color == 'white' and end_row == 0) or (piece.color == 'black' and end_row == 7):
                # Promote to queen
                print(f"Превращение пешки в ферзя на позиции {(end_row, piece.position[1])}")
                return Piece(piece.color, 'queen', (end_row, piece.position[1]))
        return piece

    def move_piece(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board[start_row][start_col]
        
        if piece and (end_row, end_col) in self.valid_moves:
            piece = self.check_pawn_promotion(piece, end_row)
            
            captured_piece = self.board[end_row][end_col]
            if captured_piece:
                print(f"Взятие: {piece.piece_type} берет {captured_piece.piece_type} на {(end_row, end_col)}")
            
            self.board[end_row][end_col] = piece
            self.board[start_row][start_col] = None
            piece.position = (end_row, end_col)
            piece.has_moved = True

            if piece.piece_type == 'king':
                if piece.color == 'white':
                    self.white_king_pos = (end_row, end_col)
                else:
                    self.black_king_pos = (end_row, end_col)

            self.current_turn = 'black' if self.current_turn == 'white' else 'white'

            king_pos = self.black_king_pos if self.current_turn == 'black' else self.white_king_pos
            self.is_check = self.is_position_under_attack(king_pos, self.current_turn)
            
            if self.is_check:
                print(f"{COLORS[self.current_turn]} под шахом!")
                self.is_checkmate = self.is_in_checkmate()
                if self.is_checkmate:
                    winner = 'white' if self.current_turn == 'black' else 'black'
                    print(f"Мат! {COLORS[winner]} победили!")
                    self.game_over = True

            return True
        return False

class ChessAI:
    def __init__(self, board: 'ChessBoard', color: str):
        self.board = board
        self.color = color
        print(f"AI initialized. Playing as {COLORS[color]}")

    def make_move(self) -> bool:
        if self.board.current_turn != self.color:
            print(f"Not AI's turn. Current turn: {COLORS[self.board.current_turn]}")
            return False
            
        print("\nAI starts searching for possible moves...")
        all_moves = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.board[row][col]
                if piece and piece.color == self.color:
                    valid_moves = self.board.get_all_valid_moves(piece)
                    if valid_moves:
                        print(f"Found moves for {piece.piece_type} at position {piece.position}: {valid_moves}")
                        all_moves.append((piece, valid_moves))
        
        print(f"Total pieces with possible moves found: {len(all_moves)}")
        
        if all_moves:
            piece, valid_moves = random.choice(all_moves)
            end = random.choice(valid_moves)
            start = piece.position
            print(f"AI chose move: {piece.piece_type} from {start} to {end}")
            
            self.board.selected_piece = piece
            self.board.valid_moves = valid_moves
            
            success = self.board.move_piece(start, end)
            if success:
                self.board.ai_move_from = start
                self.board.ai_move_to = end
                self.board.ai_move_display_time = pygame.time.get_ticks()
                self.board.selected_piece = None
                self.board.valid_moves = []
                print("Move successfully executed")
            else:
                print("Error executing move")
            return success
        else:
            print("AI found no possible moves")
            return False

class ChessGame:
    def __init__(self, screen):
        self.screen = screen
        self.board = None
        self.ai = None
        self.game_mode = None
        self.clock = pygame.time.Clock()
        self.font = GAME_FONT
        self.paused = False
        self.running = True
        self.create_menus()

    def create_menus(self):
        mytheme = pygame_menu.themes.THEME_DARK.copy()
        mytheme.background_color = (50, 50, 50)
        mytheme.title_background_color = (0, 0, 0)
        mytheme.title_font_size = MENU_FONT_SIZE
        mytheme.widget_font_size = FONT_SIZE
        mytheme.widget_padding = 25
        
        # Используем тот же шрифт для меню
        mytheme.widget_font = FONT_PATH
        mytheme.title_font = FONT_PATH

        self.main_menu = pygame_menu.Menu(
            height=TOTAL_HEIGHT,
            theme=mytheme,
            title='Chess',
            width=WINDOW_SIZE
        )

        self.main_menu.add.button('Local Game', self.start_local_game)
        self.main_menu.add.button('Play vs AI', self.start_ai_game)
        self.main_menu.add.button('Exit', pygame_menu.events.EXIT)

        self.pause_menu = pygame_menu.Menu(
            height=TOTAL_HEIGHT,
            theme=mytheme,
            title='Pause',
            width=WINDOW_SIZE
        )

        self.pause_menu.add.button('Continue', self.unpause)
        self.pause_menu.add.button('Main Menu', self.to_main_menu)
        self.pause_menu.add.button('Exit', pygame_menu.events.EXIT)

    def start_local_game(self):
        self.game_mode = 'local'
        self.board = ChessBoard()
        self.ai = None
        self.paused = False
        self.running = True
        self.run_game()

    def start_ai_game(self):
        self.game_mode = 'ai'
        self.board = ChessBoard()
        self.ai = ChessAI(self.board, 'black')
        self.paused = False
        self.running = True
        self.run_game()

    def unpause(self):
        self.paused = False
        self.pause_menu.disable()
        return

    def to_main_menu(self):
        self.board = None
        self.ai = None
        self.paused = False
        self.running = False
        self.main_menu.mainloop(self.screen)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = True
                    return

            if not self.board.game_over and event.type == pygame.MOUSEBUTTONDOWN and not self.paused:
                mouse_pos = pygame.mouse.get_pos()
                if mouse_pos[1] > MESSAGE_BOX_HEIGHT:
                    col = mouse_pos[0] // SQUARE_SIZE
                    row = (mouse_pos[1] - MESSAGE_BOX_HEIGHT) // SQUARE_SIZE
                    
                    clicked_piece = self.board.get_piece_at((row, col))
                    
                    if self.board.selected_piece:
                        if self.board.move_piece(self.board.selected_piece.position, (row, col)):
                            self.board.selected_piece = None
                            self.board.valid_moves = []
                        elif clicked_piece and clicked_piece.color == self.board.current_turn:
                            self.board.selected_piece = clicked_piece
                            self.board.valid_moves = self.board.get_all_valid_moves(clicked_piece)
                        else:
                            self.board.selected_piece = None
                            self.board.valid_moves = []
                    elif clicked_piece and clicked_piece.color == self.board.current_turn:
                        if self.game_mode == 'ai' and clicked_piece.color == 'black':
                            return
                        self.board.selected_piece = clicked_piece
                        self.board.valid_moves = self.board.get_all_valid_moves(clicked_piece)

    def draw_game(self):
        self.screen.fill(BLACK)
        
        current_color = COLORS[self.board.current_turn]
        if self.board.is_check and not self.board.is_checkmate:
            message = MESSAGES['check'].format(current_color)
        elif self.board.is_checkmate:
            winner_color = COLORS['white'] if self.board.current_turn == "black" else COLORS['black']
            message = MESSAGES['checkmate'].format(winner_color)
        else:
            message = MESSAGES['turn'].format(current_color)
        
        draw_message_box(self.screen, message, self.font)
        
        board_surface = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        self.board.draw(board_surface)
        self.screen.blit(board_surface, (0, MESSAGE_BOX_HEIGHT))
        
        pygame.display.flip()

    def run_game(self):
        self.running = True
        while self.running:
            if self.paused:
                self.pause_menu.enable()
                self.pause_menu.mainloop(self.screen, disable_loop=False)
                continue
            
            self.handle_events()
            
            if self.board and self.game_mode == 'ai' and not self.board.game_over and not self.paused:
                if self.board.current_turn == 'black':
                    self.ai.make_move()
            
            if self.board:
                self.draw_game()
            self.clock.tick(60)

def draw_message_box(surface: pygame.Surface, message: str, font: pygame.font.Font):
    # Draw message box background
    pygame.draw.rect(surface, MESSAGE_BOX_COLOR, (0, 0, WINDOW_SIZE, MESSAGE_BOX_HEIGHT))
    
    # Draw border
    pygame.draw.rect(surface, MESSAGE_BOX_BORDER, (0, 0, WINDOW_SIZE, MESSAGE_BOX_HEIGHT), 2)
    
    # Draw message
    text = font.render(message, True, WHITE)
    text_rect = text.get_rect(center=(WINDOW_SIZE // 2, MESSAGE_BOX_HEIGHT // 2))
    surface.blit(text, text_rect)

def main():
    load_images()  # Load images before starting the game
    game = ChessGame(screen)
    game.main_menu.mainloop(screen)

if __name__ == "__main__":
    main()
