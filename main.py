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
    global PIECES_IMAGES
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

# Initialize the screen
screen = pygame.display.set_mode((WINDOW_SIZE, TOTAL_HEIGHT))
pygame.display.set_caption('Chess')

class Piece:
    def __init__(self, color: str, piece_type: str, position: Tuple[int, int]):
        self.color = color
        self.piece_type = piece_type
        self.position = position
        self.has_moved = False

    def draw(self, surface: pygame.Surface, is_flipped: bool = False):
        piece_key = f'{self.color}_{self.piece_type}'
        if piece_key in PIECES_IMAGES:
            piece_img = PIECES_IMAGES[piece_key]
            piece_width = piece_img.get_width()
            piece_height = piece_img.get_height()
            
            # Calculate position based on whether the board is flipped
            if is_flipped:
                x = (7 - self.position[1]) * SQUARE_SIZE + (SQUARE_SIZE - piece_width) // 2
                y = (7 - self.position[0]) * SQUARE_SIZE + (SQUARE_SIZE - piece_height) // 2
            else:
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
        # Animation fields
        self.animating = False
        self.anim_piece = None
        self.anim_start = None
        self.anim_end = None
        self.anim_start_time = 0
        self.anim_duration = 300  # ms
        self.anim_callback = None

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

    def start_animation(self, piece, start, end, callback=None):
        self.animating = True
        self.anim_piece = piece
        self.anim_start = start
        self.anim_end = end
        self.anim_start_time = pygame.time.get_ticks()
        self.anim_callback = callback

    def update_animation(self):
        if not self.animating:
            return
        now = pygame.time.get_ticks()
        elapsed = now - self.anim_start_time
        if elapsed >= self.anim_duration:
            self.animating = False
            if self.anim_callback:
                self.anim_callback()
                self.anim_callback = None

    def draw(self, surface: pygame.Surface, is_flipped: bool = False):
        # Отрисовка доски квадратами
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = WHITE if (row + col) % 2 == 0 else (100, 140, 100) # Зеленые квадраты
                # Учитываем переворот доски для отрисовки квадратов
                display_row = 7 - row if is_flipped else row
                display_col = 7 - col if is_flipped else col
                pygame.draw.rect(surface, color, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        # --- Подсветка выбранной фигуры и возможных ходов ---
        if self.selected_piece and not (self.ai_move_from and self.ai_move_to):
            row, col = self.selected_piece.position
            if is_flipped:
                row, col = 7 - row, 7 - col
            # Если идет анимация и выбранная фигура анимируется, не подсвечивать исходную клетку
            if not (self.animating and self.anim_piece == self.selected_piece):
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                # Используем более темный желтый для выбранной фигуры, чтобы он был менее выразительным
                selected_highlight_color = (200, 200, 0, 128)
                pygame.draw.rect(s, selected_highlight_color, s.get_rect())
                surface.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            for move in self.valid_moves:
                m_row, m_col = move
                if is_flipped:
                    m_row, m_col = 7 - m_row, 7 - m_col
                # Если идет анимация и клетка совпадает с конечной позицией анимируемой фигуры, не подсвечивать (иначе дублирование)
                if not (self.animating and self.anim_end == move and self.anim_piece == self.selected_piece):
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    pygame.draw.rect(s, MOVE_HIGHLIGHT, s.get_rect())
                    surface.blit(s, (m_col * SQUARE_SIZE, m_row * SQUARE_SIZE))
        # Draw all pieces except animating one
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece and (not self.animating or piece != self.anim_piece):
                    piece.draw(surface, is_flipped=is_flipped)
        # Draw animating piece
        if self.animating and self.anim_piece:
            now = pygame.time.get_ticks()
            elapsed = now - self.anim_start_time
            t = min(1, elapsed / self.anim_duration)
            sr, sc = self.anim_start
            er, ec = self.anim_end
            if is_flipped:
                sr, sc = 7 - sr, 7 - sc
                er, ec = 7 - er, 7 - ec
            cur_row = sr + (er - sr) * t
            cur_col = sc + (ec - sc) * t
            piece_img = PIECES_IMAGES[f'{self.anim_piece.color}_{self.anim_piece.piece_type}']
            piece_width = piece_img.get_width()
            piece_height = piece_img.get_height()
            x = cur_col * SQUARE_SIZE + (SQUARE_SIZE - piece_width) // 2
            y = cur_row * SQUARE_SIZE + (SQUARE_SIZE - piece_height) // 2
            surface.blit(piece_img, (x, y))
        current_time = pygame.time.get_ticks()
        if self.ai_move_from and self.ai_move_to and current_time - self.ai_move_display_time < 1000:
            from_row, from_col = self.ai_move_from
            to_row, to_col = self.ai_move_to
            if is_flipped:
                from_row, from_col = 7 - from_row, 7 - from_col
                to_row, to_col = 7 - to_row, 7 - to_col
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(s, (*BLUE[:3], 128), s.get_rect())
            surface.blit(s, (from_col * SQUARE_SIZE, from_row * SQUARE_SIZE))
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(s, (*RED_HIGHLIGHT[:3], 128), s.get_rect())
            surface.blit(s, (to_col * SQUARE_SIZE, to_row * SQUARE_SIZE))
        elif current_time - self.ai_move_display_time >= 1000:
            self.ai_move_from = None
            self.ai_move_to = None
        if self.is_check:
            king_pos = self.white_king_pos if self.current_turn == 'white' else self.black_king_pos
            k_row, k_col = king_pos
            if is_flipped:
                k_row, k_col = 7 - k_row, 7 - k_col
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(s, RED_HIGHLIGHT, s.get_rect())
            surface.blit(s, (k_col * SQUARE_SIZE, k_row * SQUARE_SIZE))

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
            def finish_move():
                nonlocal piece, start_row, start_col, end_row, end_col
                piece2 = self.check_pawn_promotion(piece, end_row)
                captured_piece = self.board[end_row][end_col]
                self.board[end_row][end_col] = piece2
                self.board[start_row][start_col] = None
                piece2.position = (end_row, end_col)
                piece2.has_moved = True
                if piece2.piece_type == 'king':
                    if piece2.color == 'white':
                        self.white_king_pos = (end_row, end_col)
                    else:
                        self.black_king_pos = (end_row, end_col)
                self.current_turn = 'black' if self.current_turn == 'white' else 'white'
                king_pos = self.black_king_pos if self.current_turn == 'black' else self.white_king_pos
                self.is_check = self.is_position_under_attack(king_pos, self.current_turn)
                if self.is_check:
                    self.is_checkmate = self.is_in_checkmate()
                    if self.is_checkmate:
                        winner = 'white' if self.current_turn == 'black' else 'black'
                        self.game_over = True
            self.start_animation(piece, (start_row, start_col), (end_row, end_col), finish_move)
            return True
        return False

class ChessAI:
    def __init__(self, board: 'ChessBoard', color: str):
        self.board = board
        self.color = color
        self.move_count = 0
        # Common chess openings (from black's perspective)
        self.openings = [
            # Sicilian Defense
            [(1, 4), (3, 4)],  # e5
            # French Defense
            [(1, 3), (3, 3)],  # d5
            # Caro-Kann Defense
            [(1, 2), (3, 2)],  # c5
            # Scandinavian Defense
            [(1, 1), (3, 1)],  # b5
        ]
        print(f"AI initialized. Playing as {COLORS[color]}")

    def evaluate_move(self, piece, move):
        score = 0
        target_piece = self.board.get_piece_at(move)
        
        # Prioritize capturing pieces
        if target_piece:
            piece_values = {
                'pawn': 1,
                'knight': 3,
                'bishop': 3,
                'rook': 5,
                'queen': 9,
                'king': 100
            }
            score += piece_values[target_piece.piece_type] * 10
        
        # Bonus for center control
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        if move in center_squares:
            score += 2
            
        # Bonus for developing pieces
        if not piece.has_moved:
            score += 1
            
        # Penalty for moving pieces multiple times in opening
        if self.move_count < 10 and piece.has_moved:
            score -= 1
            
        return score

    def make_move(self) -> bool:
        if self.board.current_turn != self.color:
            print(f"Not AI's turn. Current turn: {COLORS[self.board.current_turn]}")
            return False
            
        print("\nAI starts searching for possible moves...")
        all_moves = []
        
        # Try to use opening book moves in the beginning
        if self.move_count < len(self.openings):
            opening_move = self.openings[self.move_count]
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    piece = self.board.board[row][col]
                    if piece and piece.color == self.color and piece.piece_type == 'pawn':
                        valid_moves = self.board.get_all_valid_moves(piece)
                        if opening_move in valid_moves:
                            print(f"Using opening book move: {piece.piece_type} from {piece.position} to {opening_move}")
                            self.board.selected_piece = piece
                            self.board.valid_moves = valid_moves
                            success = self.board.move_piece(piece.position, opening_move)
                            if success:
                                self.board.ai_move_from = piece.position
                                self.board.ai_move_to = opening_move
                                self.board.ai_move_display_time = pygame.time.get_ticks()
                                self.board.selected_piece = None
                                self.board.valid_moves = []
                                self.move_count += 1
                                return True
        
        # If no opening move is available or we're past the opening phase
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.board[row][col]
                if piece and piece.color == self.color:
                    valid_moves = self.board.get_all_valid_moves(piece)
                    if valid_moves:
                        for move in valid_moves:
                            score = self.evaluate_move(piece, move)
                            all_moves.append((piece, move, score))
        
        if all_moves:
            # Sort moves by score in descending order
            all_moves.sort(key=lambda x: x[2], reverse=True)
            # Choose the best move
            piece, end, _ = all_moves[0]
            start = piece.position
            print(f"AI chose move: {piece.piece_type} from {start} to {end}")
            
            self.board.selected_piece = piece
            self.board.valid_moves = [end]
            
            success = self.board.move_piece(start, end)
            if success:
                self.board.ai_move_from = start
                self.board.ai_move_to = end
                self.board.ai_move_display_time = pygame.time.get_ticks()
                self.board.selected_piece = None
                self.board.valid_moves = []
                self.move_count += 1
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
        self.player_color = 'white'  # Default color
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
        
        mytheme.widget_font = FONT_PATH
        mytheme.title_font = FONT_PATH

        self.main_menu = pygame_menu.Menu(
            height=TOTAL_HEIGHT,
            theme=mytheme,
            title='Chess',
            width=WINDOW_SIZE
        )

        self.main_menu.add.button('Local Game', self.start_local_game)
        self.main_menu.add.button('Play vs AI', self.show_color_selection)
        self.main_menu.add.button('Exit', pygame_menu.events.EXIT)

        self.color_selection_menu = pygame_menu.Menu(
            height=TOTAL_HEIGHT,
            theme=mytheme,
            title='Choose Your Color',
            width=WINDOW_SIZE
        )

        self.color_selection_menu.add.button('Play as White', lambda: self.start_ai_game('white'))
        self.color_selection_menu.add.button('Play as Black', lambda: self.start_ai_game('black'))
        self.color_selection_menu.add.button('Back', lambda: self.main_menu.enable())

        self.pause_menu = pygame_menu.Menu(
            height=TOTAL_HEIGHT,
            theme=mytheme,
            title='Pause',
            width=WINDOW_SIZE
        )

        self.pause_menu.add.button('Continue', self.unpause)
        self.pause_menu.add.button('Main Menu', self.to_main_menu)
        self.pause_menu.add.button('Exit', pygame_menu.events.EXIT)

    def show_color_selection(self):
        self.main_menu.disable()
        self.color_selection_menu.enable()
        self.color_selection_menu.mainloop(self.screen)

    def start_local_game(self):
        self.game_mode = 'local'
        self.player_color = 'white'
        self.board = ChessBoard()
        self.ai = None
        self.paused = False
        self.running = True
        self.run_game()

    def start_ai_game(self, color: str):
        self.game_mode = 'ai'
        self.player_color = color
        self.board = ChessBoard()
        # Initialize AI with the opposite color of the player
        self.ai = ChessAI(self.board, 'black' if color == 'white' else 'white')
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
                    
                    # Adjust row and col based on player color
                    if self.player_color == 'black':
                        row = 7 - row
                        col = 7 - col
                    
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
                        if self.game_mode == 'ai' and clicked_piece.color != self.player_color:
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
        is_flipped = self.player_color == 'black'
        self.board.draw(board_surface, is_flipped=is_flipped)
        
        self.screen.blit(board_surface, (0, MESSAGE_BOX_HEIGHT))
        
        pygame.display.flip()

    def run_game(self):
        self.running = True
        while self.running:
            if self.paused:
                self.pause_menu.enable()
                self.pause_menu.mainloop(self.screen, disable_loop=False)
                continue
            # Обновление анимации
            if self.board:
                self.board.update_animation()
            # Не обрабатывать события и ходы во время анимации
            if self.board and self.board.animating:
                self.draw_game()
                self.clock.tick(60)
                continue
            self.handle_events()
            if self.board and self.game_mode == 'ai' and not self.board.game_over and not self.paused:
                if self.board.current_turn != self.player_color:
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
