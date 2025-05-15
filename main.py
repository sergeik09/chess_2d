import pygame
import sys
from typing import List, Tuple, Optional, Set
import math
import pygame_menu
import random

# Initialize Pygame
pygame.init()

# Constants
WINDOW_SIZE = 600
BOARD_SIZE = 8
SQUARE_SIZE = WINDOW_SIZE // BOARD_SIZE
MESSAGE_BOX_HEIGHT = 50
TOTAL_HEIGHT = WINDOW_SIZE + MESSAGE_BOX_HEIGHT

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
    'white': 'Белые',
    'black': 'Черные'
}

MESSAGES = {
    'turn': '{} ходят',
    'check': '{} под шахом!',
    'checkmate': 'Мат! {} победили!',
}

# Initialize the screen
screen = pygame.display.set_mode((WINDOW_SIZE, TOTAL_HEIGHT))
pygame.display.set_caption('Шахматы')

class Piece:
    def __init__(self, color: str, piece_type: str, position: Tuple[int, int]):
        self.color = color
        self.piece_type = piece_type
        self.position = position
        self.has_moved = False

    def draw(self, surface: pygame.Surface):
        x = self.position[1] * SQUARE_SIZE + SQUARE_SIZE // 2
        y = self.position[0] * SQUARE_SIZE + SQUARE_SIZE // 2
        
        # Draw different shapes for different pieces with improved visuals
        if self.piece_type == 'pawn':
            if self.color == 'white':
                pygame.draw.circle(surface, WHITE, (x, y), SQUARE_SIZE // 4)
                pygame.draw.circle(surface, BLACK, (x, y), SQUARE_SIZE // 4, 2)
            else:
                pygame.draw.circle(surface, BLACK, (x, y), SQUARE_SIZE // 4)
                pygame.draw.circle(surface, WHITE, (x, y), SQUARE_SIZE // 4, 1)
        
        elif self.piece_type == 'rook':
            rect_size = SQUARE_SIZE // 2
            if self.color == 'white':
                pygame.draw.rect(surface, WHITE, (x - rect_size//2, y - rect_size//2, rect_size, rect_size))
                pygame.draw.rect(surface, BLACK, (x - rect_size//2, y - rect_size//2, rect_size, rect_size), 2)
                # Add details
                pygame.draw.rect(surface, BLACK, (x - rect_size//4, y - rect_size//3, rect_size//2, rect_size//6), 1)
            else:
                pygame.draw.rect(surface, BLACK, (x - rect_size//2, y - rect_size//2, rect_size, rect_size))
                pygame.draw.rect(surface, WHITE, (x - rect_size//2, y - rect_size//2, rect_size, rect_size), 1)
                pygame.draw.rect(surface, WHITE, (x - rect_size//4, y - rect_size//3, rect_size//2, rect_size//6), 1)
        
        elif self.piece_type == 'knight':
            size = SQUARE_SIZE // 3
            points = [
                (x - size, y + size),
                (x - size//2, y - size),
                (x + size//2, y - size),
                (x + size, y + size),
                (x, y + size//2)
            ]
            if self.color == 'white':
                pygame.draw.polygon(surface, WHITE, points)
                pygame.draw.polygon(surface, BLACK, points, 2)
            else:
                pygame.draw.polygon(surface, BLACK, points)
                pygame.draw.polygon(surface, WHITE, points, 1)
        
        elif self.piece_type == 'bishop':
            size = SQUARE_SIZE // 3
            points = [
                (x, y - size),
                (x - size, y + size),
                (x + size, y + size)
            ]
            if self.color == 'white':
                pygame.draw.polygon(surface, WHITE, points)
                pygame.draw.polygon(surface, BLACK, points, 2)
                pygame.draw.circle(surface, BLACK, (x, y), size//3, 1)
            else:
                pygame.draw.polygon(surface, BLACK, points)
                pygame.draw.polygon(surface, WHITE, points, 1)
                pygame.draw.circle(surface, WHITE, (x, y), size//3, 1)
        
        elif self.piece_type == 'queen':
            if self.color == 'white':
                pygame.draw.circle(surface, WHITE, (x, y), SQUARE_SIZE // 3)
                pygame.draw.circle(surface, BLACK, (x, y), SQUARE_SIZE // 3, 2)
                # Add crown details
                points = [(x + (SQUARE_SIZE//6) * math.cos(math.pi/6 * i),
                          y + (SQUARE_SIZE//6) * math.sin(math.pi/6 * i))
                         for i in range(6)]
                pygame.draw.polygon(surface, BLACK, points, 1)
            else:
                pygame.draw.circle(surface, BLACK, (x, y), SQUARE_SIZE // 3)
                pygame.draw.circle(surface, WHITE, (x, y), SQUARE_SIZE // 3, 1)
                points = [(x + (SQUARE_SIZE//6) * math.cos(math.pi/6 * i),
                          y + (SQUARE_SIZE//6) * math.sin(math.pi/6 * i))
                         for i in range(6)]
                pygame.draw.polygon(surface, WHITE, points, 1)
        
        elif self.piece_type == 'king':
            if self.color == 'white':
                pygame.draw.circle(surface, WHITE, (x, y), SQUARE_SIZE // 3)
                pygame.draw.circle(surface, BLACK, (x, y), SQUARE_SIZE // 3, 2)
                # Add cross
                size = SQUARE_SIZE // 4
                pygame.draw.line(surface, BLACK, (x, y - size), (x, y + size), 2)
                pygame.draw.line(surface, BLACK, (x - size, y), (x + size, y), 2)
            else:
                pygame.draw.circle(surface, BLACK, (x, y), SQUARE_SIZE // 3)
                pygame.draw.circle(surface, WHITE, (x, y), SQUARE_SIZE // 3, 1)
                size = SQUARE_SIZE // 4
                pygame.draw.line(surface, WHITE, (x, y - size), (x, y + size), 2)
                pygame.draw.line(surface, WHITE, (x - size, y), (x + size, y), 2)

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
        # Draw the chess board
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = WHITE if (row + col) % 2 == 0 else GRAY
                pygame.draw.rect(surface, color, 
                               (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        # Draw the pieces
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece:
                    piece.draw(surface)

        # Highlight selected piece and valid moves
        if self.selected_piece:
            row, col = self.selected_piece.position
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(s, HIGHLIGHT, s.get_rect())
            surface.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

            for move in self.valid_moves:
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(s, MOVE_HIGHLIGHT, s.get_rect())
                surface.blit(s, (move[1] * SQUARE_SIZE, move[0] * SQUARE_SIZE))

        # Highlight king in check
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
                return Piece(piece.color, 'queen', (end_row, piece.position[1]))
        return piece

    def move_piece(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board[start_row][start_col]
        
        if piece and (end_row, end_col) in self.valid_moves:
            # Move the piece
            # Check for pawn promotion
            piece = self.check_pawn_promotion(piece, end_row)
            
            self.board[end_row][end_col] = piece
            self.board[start_row][start_col] = None
            piece.position = (end_row, end_col)
            piece.has_moved = True

            # Update king position if moving king
            if piece.piece_type == 'king':
                if piece.color == 'white':
                    self.white_king_pos = (end_row, end_col)
                else:
                    self.black_king_pos = (end_row, end_col)

            # Switch turns
            self.current_turn = 'black' if self.current_turn == 'white' else 'white'

            # Check if the opponent is in check
            king_pos = self.black_king_pos if self.current_turn == 'black' else self.white_king_pos
            self.is_check = self.is_position_under_attack(king_pos, self.current_turn)

            # Check for checkmate
            if self.is_check:
                self.is_checkmate = self.is_in_checkmate()
                if self.is_checkmate:
                    self.game_over = True

            return True
        return False

class ChessAI:
    def __init__(self, board: 'ChessBoard', color: str):
        self.board = board
        self.color = color

    def make_move(self):
        all_moves = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.board[row][col]
                if piece and piece.color == self.color:
                    valid_moves = self.board.get_all_valid_moves(piece)
                    for move in valid_moves:
                        all_moves.append((piece.position, move))
        
        if all_moves:
            start, end = random.choice(all_moves)
            self.board.move_piece(start, end)

class ChessGame:
    def __init__(self, screen):
        self.screen = screen
        self.board = None
        self.ai = None
        self.game_mode = None
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 32)
        self.paused = False
        self.running = True
        self.create_menus()

    def create_menus(self):
        theme = pygame_menu.themes.Theme(
            background_color=(50, 50, 50),
            title_background_color=(0, 0, 0),
            title_font_size=30,
            widget_padding=25
        )

        self.main_menu = pygame_menu.Menu(
            height=TOTAL_HEIGHT,
            theme=theme,
            title='Шахматы',
            width=WINDOW_SIZE
        )

        self.main_menu.add.button('Игра с собой', self.start_local_game)
        self.main_menu.add.button('Игра с ИИ', self.start_ai_game)
        self.main_menu.add.button('Выход', pygame_menu.events.EXIT)

        self.pause_menu = pygame_menu.Menu(
            height=TOTAL_HEIGHT,
            theme=theme,
            title='Пауза',
            width=WINDOW_SIZE
        )

        self.pause_menu.add.button('Продолжить', self.unpause)
        self.pause_menu.add.button('В главное меню', self.to_main_menu)
        self.pause_menu.add.button('Выход', pygame_menu.events.EXIT)

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
                            if self.game_mode == 'ai' and not self.board.game_over:
                                self.ai.make_move()
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
    game = ChessGame(screen)
    game.main_menu.mainloop(screen)

if __name__ == "__main__":
    main()
