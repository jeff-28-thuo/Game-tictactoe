import os
import random
import time
import sys
import select
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional

# ============== CONSTANTS AND CONFIGURATION ==============
class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BRIGHT_RED = '\033[1;91m'
    BRIGHT_GREEN = '\033[1;92m'
    BRIGHT_YELLOW = '\033[1;93m'
    BRIGHT_BLUE = '\033[1;94m'
    BRIGHT_MAGENTA = '\033[1;95m'
    BRIGHT_CYAN = '\033[1;96m'
    BRIGHT_WHITE = '\033[1;97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

GAME_CONFIG = {
    'BOARD_WIDTH': 10,
    'BOARD_HEIGHT': 20,
    'INITIAL_DROP_INTERVAL': 1.0,
    'MIN_DROP_INTERVAL': 0.05,
    'LEVEL_SPEED_INCREASE': 0.1,
    'LINES_PER_LEVEL': 10,
    'SCORE_MULTIPLIERS': [100, 200, 500, 1000]  # 1, 2, 3, 4 lines
}

# ============== DATA MODELS ==============
@dataclass
class Position:
    """Represents a position on the game board"""
    y: int
    x: int

class PieceType(Enum):
    """Types of Tetris pieces"""
    I = 'I'
    O = 'O'
    T = 'T'
    S = 'S'
    Z = 'Z'
    J = 'J'
    L = 'L'

class Piece:
    """Represents a Tetris piece with its shape and color"""
    SHAPES = {
        PieceType.I: ([[1, 1, 1, 1]], Colors.CYAN),
        PieceType.O: ([[1, 1], [1, 1]], Colors.YELLOW),
        PieceType.T: ([[0, 1, 0], [1, 1, 1]], Colors.MAGENTA),
        PieceType.S: ([[0, 1, 1], [1, 1, 0]], Colors.GREEN),
        PieceType.Z: ([[1, 1, 0], [0, 1, 1]], Colors.RED),
        PieceType.J: ([[1, 0, 0], [1, 1, 1]], Colors.BLUE),
        PieceType.L: ([[0, 0, 1], [1, 1, 1]], Colors.BRIGHT_RED),
    }
    
    def __init__(self, piece_type: PieceType):
        self.type = piece_type
        self.shape, self.color = self.SHAPES[piece_type]
        self.rotation = 0
    
    def rotate(self):
        """Rotate the piece 90 degrees clockwise"""
        rows = len(self.shape)
        cols = len(self.shape[0])
        rotated = [[self.shape[rows - 1 - y][x] for y in range(rows)] 
                  for x in range(cols)]
        self.shape = rotated
    
    def get_cells(self, position: Position) -> List[Tuple[int, int]]:
        """Get all occupied cells for this piece at given position"""
        cells = []
        for y in range(len(self.shape)):
            for x in range(len(self.shape[y])):
                if self.shape[y][x]:
                    cells.append((position.y + y, position.x + x))
        return cells
    
    def copy(self) -> 'Piece':
        """Create a copy of this piece"""
        new_piece = Piece(self.type)
        new_piece.shape = [row[:] for row in self.shape]
        new_piece.color = self.color
        new_piece.rotation = self.rotation
        return new_piece

# ============== GAME LOGIC ==============
class GameBoard:
    """Manages the Tetris game board and pieces"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        self.current_piece: Optional[Piece] = None
        self.current_pos: Optional[Position] = None
        self.next_piece: Optional[Piece] = None
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self._initialize_pieces()
    
    def _initialize_pieces(self):
        """Initialize the first pieces"""
        self.next_piece = self._create_random_piece()
        self._spawn_new_piece()
    
    def _create_random_piece(self) -> Piece:
        """Create a random Tetris piece"""
        return Piece(random.choice(list(PieceType)))
    
    def _spawn_new_piece(self):
        """Spawn a new piece at the top center of the board"""
        self.current_piece = self.next_piece
        self.next_piece = self._create_random_piece()
        
        # Start position (top center)
        start_x = self.width // 2 - len(self.current_piece.shape[0]) // 2
        self.current_pos = Position(0, start_x)
        
        # Check if game over
        if self._check_collision():
            self.game_over = True
    
    def _check_collision(self, piece: Optional[Piece] = None, 
                        position: Optional[Position] = None) -> bool:
        """Check if a piece would collide at the given position"""
        if piece is None:
            piece = self.current_piece
        if position is None:
            position = self.current_pos
        
        cells = piece.get_cells(position)
        for y, x in cells:
            # Check boundaries
            if x < 0 or x >= self.width or y >= self.height:
                return True
            # Check if cell is occupied
            if y >= 0 and self.grid[y][x]:
                return True
        return False
    
    def move_piece(self, dx: int, dy: int) -> bool:
        """Move the current piece by dx, dy"""
        if self.game_over:
            return False
        
        new_pos = Position(self.current_pos.y + dy, self.current_pos.x + dx)
        
        if not self._check_collision(self.current_piece, new_pos):
            self.current_pos = new_pos
            return True
        elif dy > 0:  # Collision while moving down
            self._merge_piece()
            self._clear_lines()
            self._spawn_new_piece()
        return False
    
    def rotate_piece(self) -> bool:
        """Rotate the current piece"""
        if self.game_over:
            return False
        
        rotated_piece = self.current_piece.copy()
        rotated_piece.rotate()
        
        if not self._check_collision(rotated_piece, self.current_pos):
            self.current_piece = rotated_piece
            return True
        return False
    
    def drop_piece(self):
        """Drop the current piece to the bottom"""
        if self.game_over:
            return
        
        while self.move_piece(0, 1):
            pass
    
    def _merge_piece(self):
        """Merge the current piece into the grid"""
        cells = self.current_piece.get_cells(self.current_pos)
        for y, x in cells:
            if y >= 0:  # Only place if on the board
                self.grid[y][x] = self.current_piece.color
    
    def _clear_lines(self):
        """Clear completed lines and update score"""
        lines_to_clear = []
        
        for y in range(self.height):
            if all(cell != 0 for cell in self.grid[y]):
                lines_to_clear.append(y)
        
        # Clear lines from bottom to top
        for line in reversed(lines_to_clear):
            del self.grid[line]
            self.grid.insert(0, [0 for _ in range(self.width)])
        
        # Update game stats
        if lines_to_clear:
            lines_count = len(lines_to_clear)
            self.lines_cleared += lines_count
            
            # Calculate score based on number of lines cleared
            multiplier_index = min(lines_count - 1, len(GAME_CONFIG['SCORE_MULTIPLIERS']) - 1)
            self.score += GAME_CONFIG['SCORE_MULTIPLIERS'][multiplier_index] * self.level
            
            # Update level
            self.level = self.lines_cleared // GAME_CONFIG['LINES_PER_LEVEL'] + 1
    
    def get_drop_interval(self) -> float:
        """Get current drop interval based on level"""
        base_interval = GAME_CONFIG['INITIAL_DROP_INTERVAL']
        speed_increase = GAME_CONFIG['LEVEL_SPEED_INCREASE']
        min_interval = GAME_CONFIG['MIN_DROP_INTERVAL']
        
        interval = max(min_interval, base_interval - (self.level - 1) * speed_increase)
        return interval
    
    def get_game_state(self) -> dict:
        """Get current game state for rendering"""
        return {
            'grid': self.grid,
            'current_piece': self.current_piece,
            'current_pos': self.current_pos,
            'next_piece': self.next_piece,
            'score': self.score,
            'level': self.level,
            'lines_cleared': self.lines_cleared,
            'game_over': self.game_over,
            'width': self.width,
            'height': self.height
        }

# ============== RENDERER ==============
class GameRenderer:
    """Handles rendering of the game to the terminal"""
    
    @staticmethod
    def clear_screen():
        """Clear the terminal screen"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    @staticmethod
    def draw_title():
        """Draw the Tetris title screen"""
        print(f"{Colors.BRIGHT_GREEN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}")
        print("  _______ ______ _______ ___ ___ _______ ______  ")
        print(" |__   __|  ____|__   __|__ \__ \__   __|  ____| ")
        print("    | |  | |__     | |     ) | ) | | |  | |__    ")
        print("    | |  |  __|    | |    / / / /  | |  |  __|   ")
        print("    | |  | |____   | |   / /_/ /_ _| |_ | |____  ")
        print("    |_|  |______|  |_|  |____|____|_____|______| ")
        print(f"{Colors.RESET}")
        print(f"{Colors.YELLOW}           Programmed by Jeff{Colors.RESET}")
        print(f"{Colors.BRIGHT_GREEN}{'='*60}{Colors.RESET}")
        print()
    
    @staticmethod
    def draw_board(game_state: dict):
        """Draw the game board with current pieces"""
        grid = game_state['grid']
        width = game_state['width']
        height = game_state['height']
        current_piece = game_state['current_piece']
        current_pos = game_state['current_pos']
        
        board_str = f"{Colors.WHITE}  +{'-' * (width * 2)}+{Colors.RESET}\n"
        
        for y in range(height):
            board_str += f"{Colors.WHITE}  |{Colors.RESET}"
            
            for x in range(width):
                # Check if current piece occupies this cell
                cell_occupied = False
                piece_color = None
                
                if current_piece and not game_state['game_over']:
                    cells = current_piece.get_cells(current_pos)
                    if (y, x) in cells:
                        cell_occupied = True
                        piece_color = current_piece.color
                
                if cell_occupied:
                    board_str += f"{piece_color}██{Colors.RESET}"
                elif grid[y][x]:
                    board_str += f"{grid[y][x]}██{Colors.RESET}"
                else:
                    board_str += "  "
            
            board_str += f"{Colors.WHITE}|{Colors.RESET}\n"
        
        board_str += f"{Colors.WHITE}  +{'-' * (width * 2)}+{Colors.RESET}\n"
        return board_str
    
    @staticmethod
    def draw_next_piece(next_piece: Piece):
        """Draw the next piece preview"""
        next_piece_str = f"\n{Colors.BOLD}Next piece:{Colors.RESET}\n"
        shape = next_piece.shape
        
        for row in shape:
            next_piece_str += " " * 8
            for cell in row:
                if cell:
                    next_piece_str += f"{next_piece.color}██{Colors.RESET}"
                else:
                    next_piece_str += "  "
            next_piece_str += "\n"
        
        return next_piece_str
    
    @staticmethod
    def draw_game_info(game_state: dict):
        """Draw game information and controls"""
        info_str = f"""
{Colors.BOLD}Game Information:{Colors.RESET}
{Colors.GREEN}Score: {Colors.BRIGHT_GREEN}{game_state['score']}{Colors.RESET}
{Colors.BLUE}Level: {Colors.BRIGHT_BLUE}{game_state['level']}{Colors.RESET}
{Colors.MAGENTA}Lines: {Colors.BRIGHT_MAGENTA}{game_state['lines_cleared']}{Colors.RESET}

{Colors.BOLD}Controls:{Colors.RESET}
{Colors.YELLOW}A / ←{Colors.RESET} - Move Left
{Colors.YELLOW}D / →{Colors.RESET} - Move Right
{Colors.YELLOW}W / ↑{Colors.RESET} - Rotate
{Colors.YELLOW}S / ↓{Colors.RESET} - Move Down
{Colors.YELLOW}Space{Colors.RESET} - Drop
{Colors.YELLOW}P{Colors.RESET} - Pause
{Colors.YELLOW}Q{Colors.RESET} - Quit
"""
        return info_str
    
    @staticmethod
    def draw_game_over(score: int):
        """Draw game over screen"""
        print(f"\n{Colors.BRIGHT_RED}{'*'*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.RED}GAME OVER!{Colors.RESET}")
        print(f"{Colors.BRIGHT_RED}{'*'*60}{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Final Score: {Colors.BRIGHT_YELLOW}{score}{Colors.RESET}")
        print(f"\n{Colors.CYAN}Press any key to exit...{Colors.RESET}")
    
    def render(self, game_state: dict):
        """Render the complete game screen"""
        self.clear_screen()
        self.draw_title()
        
        # Get all render components
        board = self.draw_board(game_state)
        next_piece = self.draw_next_piece(game_state['next_piece'])
        game_info = self.draw_game_info(game_state)
        
        # Combine all elements
        left_part = board
        right_part = next_piece + game_info
        
        # Split into lines for side-by-side display
        board_lines = left_part.split('\n')
        info_lines = right_part.split('\n')
        
        max_lines = max(len(board_lines), len(info_lines))
        
        for i in range(max_lines):
            board_line = board_lines[i] if i < len(board_lines) else ""
            info_line = info_lines[i] if i < len(info_lines) else ""
            print(f"{board_line.ljust(30)}  {info_line}")

# ============== INPUT HANDLER ==============
class InputHandler:
    """Handles user input for the game"""
    
    @staticmethod
    def get_key():
        """Get a single key press (works in Termux)"""
        try:
            # For Unix-like systems (Linux, macOS, Termux)
            import termios
            import tty
            
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                
                # Handle escape sequences (arrow keys)
                if ch == '\x1b':
                    # Read more characters for arrow keys
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        ch3 = sys.stdin.read(1)
                        if ch3 == 'A': return 'w'    # Up arrow
                        elif ch3 == 'B': return 's'  # Down arrow
                        elif ch3 == 'C': return 'd'  # Right arrow
                        elif ch3 == 'D': return 'a'  # Left arrow
                elif ch == ' ': return ' '           # Space bar
                elif ch == '\n': return 'enter'
                elif ch == '\x03': return 'q'        # Ctrl+C
                elif ch == '\x1b': return 'q'        # Escape
                
                return ch.lower()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except:
            try:
                # For Windows
                import msvcrt
                return msvcrt.getch().decode('utf-8').lower()
            except:
                return ''
    
    @staticmethod
    def wait_for_key(timeout: float = 0.1) -> str:
        """Wait for key press with timeout"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            key = InputHandler.get_key()
            if key:
                return key
            time.sleep(0.01)
        return ''

# ============== GAME CONTROLLER ==============
class TetrisGame:
    """Main game controller that coordinates all components"""
    
    def __init__(self):
        self.board = GameBoard(
            GAME_CONFIG['BOARD_WIDTH'],
            GAME_CONFIG['BOARD_HEIGHT']
        )
        self.renderer = GameRenderer()
        self.input_handler = InputHandler()
        self.last_drop_time = time.time()
        self.paused = False
    
    def handle_input(self, key: str):
        """Process user input"""
        if key == 'a':
            self.board.move_piece(-1, 0)
        elif key == 'd':
            self.board.move_piece(1, 0)
        elif key == 'w':
            self.board.rotate_piece()
        elif key == 's':
            self.board.move_piece(0, 1)
        elif key == ' ':
            self.board.drop_piece()
        elif key == 'p':
            self.toggle_pause()
        elif key == 'q':
            return False  # Signal to quit
        return True  # Continue game
    
    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        if self.paused:
            self.renderer.clear_screen()
            print(f"\n{Colors.YELLOW}Game Paused. Press any key to continue...{Colors.RESET}")
            self.input_handler.get_key()
            self.paused = False
    
    def update(self):
        """Update game state (auto-drop)"""
        if self.paused or self.board.game_over:
            return
        
        current_time = time.time()
        drop_interval = self.board.get_drop_interval()
        
        if current_time - self.last_drop_time > drop_interval:
            self.board.move_piece(0, 1)
            self.last_drop_time = current_time
    
    def run(self):
        """Main game loop"""
        # Countdown before starting
        self.renderer.clear_screen()
        self.renderer.draw_title()
        for i in range(3, 0, -1):
            print(f"\n{Colors.BRIGHT_YELLOW}Game starts in {i}...{Colors.RESET}")
            time.sleep(1)
        
        # Main game loop
        while not self.board.game_over:
            # Update game state
            self.update()
            
            # Render game
            game_state = self.board.get_game_state()
            self.renderer.render(game_state)
            
            # Handle input
            key = self.input_handler.wait_for_key(0.1)
            if key:
                if not self.handle_input(key):
                    print(f"\n{Colors.YELLOW}Thanks for playing!{Colors.RESET}")
                    break
            
            # Small delay to prevent CPU overuse
            time.sleep(0.01)
        
        # Game over screen
        game_state = self.board.get_game_state()
        self.renderer.render(game_state)
        self.renderer.draw_game_over(self.board.score)
        self.input_handler.get_key()

# ============== MAIN ENTRY POINT ==============
def main():
    """Entry point for the Tetris game"""
    try:
        game = TetrisGame()
        game.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Game interrupted. Thanks for playing!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}An error occurred: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}Please ensure your terminal supports ANSI colors.{Colors.RESET}")

if __name__ == "__main__":
    main()
