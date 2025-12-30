import random
import time
import json
import threading
import socket
import select
import sys
import os
from datetime import datetime

# ANSI color codes for colorful output
class Colors:
    # Text colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BLACK = '\033[30m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    BG_BLACK = '\033[40m'
    
    # Styles
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    
    # Reset
    RESET = '\033[0m'

class TicTacToeGame:
    """Core Tic Tac Toe Game Logic"""
    
    def __init__(self, player1="Player 1", player2="Player 2"):
        self.board = [' ' for _ in range(9)]
        self.players = {'X': player1, 'O': player2}
        self.player_colors = {'X': Colors.CYAN, 'O': Colors.YELLOW}
        self.current_player = 'X'
        self.moves_history = []
        self.game_over = False
        self.winner = None
        
    def get_board_position_map(self):
        """Return visual position map for reference"""
        position_map = [
            "╔════════════════════════════════════════════╗",
            "║           POSITION REFERENCE               ║",
            "╠═══════════╦═══════════╦═══════════╣",
            "║    1      ║    2      ║    3      ║",
            "╠═══════════╬═══════════╬═══════════╣",
            "║    4      ║    5      ║    6      ║",
            "╠═══════════╬═══════════╬═══════════╣",
            "║    7      ║    8      ║    9      ║",
            "╚═══════════╩═══════════╩═══════════╝"
        ]
        return "\n".join(position_map)
    
    def print_board_ascii(self, show_positions=False):
        """Create ASCII art board with colors and no numbers in boxes"""
        board_display = []
        
        # Top border with title
        board_display.append(Colors.CYAN + "╔══════════════════════════════════════════════════════════╗" + Colors.RESET)
        board_display.append(Colors.CYAN + "║" + Colors.BOLD + Colors.MAGENTA + "                    TIC TAC TOE ARENA                  " + Colors.RESET + Colors.CYAN + "║" + Colors.RESET)
        board_display.append(Colors.CYAN + "╠═══════════╦═══════════╦═══════════╣" + Colors.RESET)
        
        # Board rows
        for row in range(3):
            row_display = Colors.CYAN + "║" + Colors.RESET
            for col in range(3):
                idx = row * 3 + col
                cell = self.board[idx]
                
                # Create cell content with colors
                if cell == 'X':
                    cell_content = f"{Colors.BOLD}{Colors.CYAN}   X   {Colors.RESET}"
                elif cell == 'O':
                    cell_content = f"{Colors.BOLD}{Colors.YELLOW}   O   {Colors.RESET}"
                else:
                    cell_content = "       "  # Empty cell
                
                row_display += f"{Colors.WHITE}{cell_content}{Colors.RESET}{Colors.CYAN}║" + Colors.RESET
            
            board_display.append(row_display)
            
            # Add separator between rows (not after last row)
            if row < 2:
                board_display.append(Colors.CYAN + "╠═══════════╬═══════════╬═══════════╣" + Colors.RESET)
        
        # Bottom border
        board_display.append(Colors.CYAN + "╚═══════════╩═══════════╩═══════════╝" + Colors.RESET)
        
        # Add player info
        board_display.append("")
        x_color = Colors.CYAN
        o_color = Colors.YELLOW
        
        # Current player indicator with blinking effect
        if self.current_player == 'X':
            current_indicator = f"{Colors.BLINK}{Colors.GREEN}➤{Colors.RESET}"
            x_display = f"{current_indicator} {x_color}X: {self.players['X']}{Colors.RESET}"
            o_display = f"  {o_color}O: {self.players['O']}{Colors.RESET}"
        else:
            current_indicator = f"{Colors.BLINK}{Colors.GREEN}➤{Colors.RESET}"
            x_display = f"  {x_color}X: {self.players['X']}{Colors.RESET}"
            o_display = f"{current_indicator} {o_color}O: {self.players['O']}{Colors.RESET}"
        
        board_display.append(f"{Colors.BOLD}Players:{Colors.RESET}")
        board_display.append(x_display)
        board_display.append(o_display)
        
        return "\n".join(board_display)
    
    def make_move(self, position, player=None):
        """Make a move on the board"""
        if player is None:
            player = self.current_player
            
        if self.game_over or position not in self.available_moves():
            return False
            
        self.board[position] = player
        
        # Add visual effect to move
        self.moves_history.append({
            'player': player,
            'position': position,
            'time': datetime.now().strftime("%H:%M:%S")
        })
        
        # Check for winner
        self.check_game_status()
        
        # Switch player if game not over
        if not self.game_over:
            self.current_player = 'O' if self.current_player == 'X' else 'X'
            
        return True
    
    def available_moves(self):
        """Get list of available moves"""
        return [i for i, spot in enumerate(self.board) if spot == ' ']
    
    def check_game_status(self):
        """Check if game is won or tied"""
        # Winning combinations
        win_patterns = [
            [0,1,2], [3,4,5], [6,7,8],  # Rows
            [0,3,6], [1,4,7], [2,5,8],  # Columns
            [0,4,8], [2,4,6]            # Diagonals
        ]
        
        for pattern in win_patterns:
            a, b, c = pattern
            if self.board[a] != ' ' and self.board[a] == self.board[b] == self.board[c]:
                self.winner = self.board[a]
                self.game_over = True
                return
        
        # Check for tie
        if ' ' not in self.board:
            self.game_over = True
            self.winner = 'Tie'
    
    def get_game_state(self):
        """Get complete game state for serialization"""
        return {
            'board': self.board,
            'current_player': self.current_player,
            'players': self.players,
            'game_over': self.game_over,
            'winner': self.winner,
            'moves_history': self.moves_history
        }
    
    def animate_move(self, position, player):
        """Animate placing a move on the board"""
        original_board = self.board.copy()
        
        # Flash the position
        for _ in range(3):
            self.board[position] = f"{Colors.BLINK}{Colors.GREEN}*{Colors.RESET}"
            time.sleep(0.1)
            self.board[position] = ' '
            time.sleep(0.1)
        
        self.board[position] = player
        return original_board

class RobotAI:
    """AI Player for Tic Tac Toe"""
    
    def __init__(self, difficulty='medium'):
        self.difficulty = difficulty
        self.name = "🤖 Robot"
        self.difficulty_levels = {
            'easy': '🎮 Novice Bot',
            'medium': '⚡ Pro Bot',
            'hard': '👑 Master Bot',
            'impossible': '🤖 Terminator Bot'
        }
        self.difficulty_colors = {
            'easy': Colors.GREEN,
            'medium': Colors.YELLOW,
            'hard': Colors.MAGENTA,
            'impossible': Colors.RED
        }
        
    def get_move(self, game):
        """Get AI move based on difficulty"""
        available = game.available_moves()
        
        if self.difficulty == 'easy':
            return self.easy_move(available)
        elif self.difficulty == 'medium':
            return self.medium_move(game, available)
        elif self.difficulty == 'hard':
            return self.hard_move(game, available)
        else:  # impossible
            return self.impossible_move(game, available)
    
    def easy_move(self, available):
        """Random moves"""
        time.sleep(1)  # Think time
        return random.choice(available)
    
    def medium_move(self, game, available):
        """Try to win or block"""
        time.sleep(1.5)  # Think time
        
        # Try to win
        for move in available:
            test_board = game.board.copy()
            test_board[move] = 'O'
            if self.check_win(test_board, 'O'):
                return move
        
        # Block player
        for move in available:
            test_board = game.board.copy()
            test_board[move] = 'X'
            if self.check_win(test_board, 'X'):
                return move
        
        # Prefer center
        if 4 in available:
            return 4
        
        # Prefer corners
        corners = [0, 2, 6, 8]
        random.shuffle(corners)
        for corner in corners:
            if corner in available:
                return corner
        
        return random.choice(available)
    
    def hard_move(self, game, available):
        """More strategic AI"""
        time.sleep(2)  # Think time
        return self.minimax(game.board, 'O', available)['position']
    
    def impossible_move(self, game, available):
        """Perfect AI using minimax"""
        time.sleep(0.5)  # Quick thinking for Terminator
        return self.minimax(game.board, 'O', available, True)['position']
    
    def minimax(self, board, player, available, perfect=False):
        """Minimax algorithm for optimal moves"""
        # Check terminal states
        if self.check_win(board, 'O'):
            return {'score': 10}
        if self.check_win(board, 'X'):
            return {'score': -10}
        if ' ' not in board:
            return {'score': 0}
        
        moves = []
        for move in available:
            board[move] = player
            result = self.minimax(board, 
                                 'O' if player == 'X' else 'X',
                                 [i for i in range(9) if board[i] == ' '],
                                 perfect)
            board[move] = ' '
            result['position'] = move
            moves.append(result)
        
        # Choose best move
        if player == 'O':
            best_score = -float('inf')
            for move in moves:
                if move['score'] > best_score:
                    best_score = move['score']
                    best_move = move
        else:
            best_score = float('inf')
            for move in moves:
                if move['score'] < best_score:
                    best_score = move['score']
                    best_move = move
        
        return best_move
    
    def check_win(self, board, player):
        """Check if player has won"""
        win_patterns = [
            [0,1,2], [3,4,5], [6,7,8],
            [0,3,6], [1,4,7], [2,5,8],
            [0,4,8], [2,4,6]
        ]
        return any(all(board[i] == player for i in pattern) for pattern in win_patterns)
    
    def get_difficulty_display(self):
        """Get colored difficulty display"""
        color = self.difficulty_colors.get(self.difficulty, Colors.WHITE)
        return f"{color}{self.difficulty_levels[self.difficulty]}{Colors.RESET}"

class TicTacToeTerminal:
    """Main Terminal Interface"""
    
    def __init__(self):
        self.game = None
        self.ai = None
        self.online_client = None
        self.player_name = "Player"
        self.show_positions = True  # Toggle for showing position numbers
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print game header with colors and ASCII art"""
        header = f"""
{Colors.MAGENTA}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║  {Colors.CYAN}▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓    ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓{Colors.MAGENTA}  ║
    ║  {Colors.CYAN}▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓▓▓▓▓▓{Colors.MAGENTA} ║
    ║  {Colors.CYAN}   ▓▓▓▓     ▓▓▓▓   ▓▓▓▓    ▓▓▓▓   ▓▓▓▓  ▓▓▓▓   ▓▓▓▓  ▓▓▓▓   ▓▓▓▓{Colors.MAGENTA}  ║
    ║  {Colors.CYAN}   ▓▓▓▓     ▓▓▓▓▓▓▓▓▓▓▓    ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓{Colors.MAGENTA}  ║
    ║  {Colors.CYAN}   ▓▓▓▓     ▓▓▓▓▓▓▓▓▓▓▓    ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓{Colors.MAGENTA}  ║
    ║  {Colors.CYAN}   ▓▓▓▓     ▓▓▓▓   ▓▓▓▓    ▓▓▓▓   ▓▓▓▓  ▓▓▓▓   ▓▓▓▓  ▓▓▓▓   ▓▓▓▓{Colors.MAGENTA}  ║
    ║  {Colors.CYAN}   ▓▓▓▓     ▓▓▓▓    ▓▓▓▓   ▓▓▓▓   ▓▓▓▓  ▓▓▓▓   ▓▓▓▓  ▓▓▓▓    ▓▓▓▓{Colors.MAGENTA} ║
    ║                                                                           ║
    ║  {Colors.YELLOW}▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓▓▓▓▓▓{Colors.MAGENTA} ║
    ║  {Colors.YELLOW}▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓{Colors.MAGENTA}║
    ║  {Colors.YELLOW}   ▓▓▓▓     ▓▓▓▓   ▓▓▓▓    ▓▓▓▓   ▓▓▓▓  ▓▓▓▓   ▓▓▓▓  ▓▓▓▓   ▓▓▓▓{Colors.MAGENTA}  ║
    ║  {Colors.YELLOW}   ▓▓▓▓     ▓▓▓▓▓▓▓▓▓▓▓    ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓{Colors.MAGENTA}  ║
    ║  {Colors.YELLOW}   ▓▓▓▓     ▓▓▓▓▓▓▓▓▓▓▓    ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓{Colors.MAGENTA}  ║
    ║  {Colors.YELLOW}   ▓▓▓▓     ▓▓▓▓   ▓▓▓▓    ▓▓▓▓   ▓▓▓▓  ▓▓▓▓   ▓▓▓▓  ▓▓▓▓   ▓▓▓▓{Colors.MAGENTA}  ║
    ║  {Colors.YELLOW}   ▓▓▓▓     ▓▓▓▓   ▓▓▓▓    ▓▓▓▓   ▓▓▓▓  ▓▓▓▓   ▓▓▓▓  ▓▓▓▓   ▓▓▓▓{Colors.MAGENTA}  ║
    ║                                                                           ║
    ╠═══════════════════════════════════════════════════════════════════════════╣
    ║                 {Colors.BOLD}{Colors.GREEN}Created and Hosted by Jeff{Colors.RESET}{Colors.MAGENTA}                      ║
    ╚═══════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
        """
        print(header)
    
    def main_menu(self):
        """Display main menu"""
        while True:
            self.clear_screen()
            self.print_header()
            
            menu = f"""
    {Colors.CYAN}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}
    {Colors.CYAN}║{Colors.BOLD}{Colors.MAGENTA}                    MAIN MENU                      {Colors.RESET}{Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}╠═══════════════════════════════════════════════════════════╣{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}1.{Colors.RESET} {Colors.BOLD}🤖  PLAY VS ROBOT{Colors.RESET}                          {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}2.{Colors.RESET} {Colors.BOLD}👥  PLAY VS FRIEND (Local){Colors.RESET}                  {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}3.{Colors.RESET} {Colors.BOLD}🌐  PLAY ONLINE{Colors.RESET}                            {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}4.{Colors.RESET} {Colors.BOLD}⚙️   GAME SETTINGS{Colors.RESET}                         {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}5.{Colors.RESET} {Colors.BOLD}📖  HOW TO PLAY{Colors.RESET}                           {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}6.{Colors.RESET} {Colors.BOLD}🏆  VIEW LEADERBOARD{Colors.RESET}                       {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}7.{Colors.RESET} {Colors.BOLD}🚪  EXIT{Colors.RESET}                                  {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}
    
    {Colors.YELLOW}{Colors.BOLD}Choose option (1-7):{Colors.RESET} """
            
            choice = input(menu).strip()
            
            if choice == '1':
                self.play_vs_robot()
            elif choice == '2':
                self.play_vs_friend()
            elif choice == '3':
                self.play_online()
            elif choice == '4':
                self.game_settings()
            elif choice == '5':
                self.how_to_play()
            elif choice == '6':
                self.view_leaderboard()
            elif choice == '7':
                print(f"\n{Colors.GREEN}Thanks for playing! Goodbye! 👋{Colors.RESET}\n")
                break
            else:
                print(f"{Colors.RED}Invalid choice. Please try again.{Colors.RESET}")
                time.sleep(1)
    
    def game_settings(self):
        """Game settings menu"""
        self.clear_screen()
        print(f"""
    {Colors.CYAN}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}
    {Colors.CYAN}║{Colors.BOLD}{Colors.MAGENTA}                   GAME SETTINGS                    {Colors.RESET}{Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}╠═══════════════════════════════════════════════════════════╣{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}1.{Colors.RESET} Toggle Position Numbers: {Colors.GREEN}{'ON' if self.show_positions else 'OFF'}{Colors.RESET}           {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}2.{Colors.RESET} Change Player Name                            {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}3.{Colors.RESET} Back to Main Menu                             {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}
        """)
        
        choice = input(f"\n{Colors.YELLOW}Choose option (1-3): {Colors.RESET}").strip()
        
        if choice == '1':
            self.show_positions = not self.show_positions
            print(f"\n{Colors.GREEN}Position numbers are now {'ON' if self.show_positions else 'OFF'}{Colors.RESET}")
            time.sleep(1)
        elif choice == '2':
            new_name = input(f"\n{Colors.CYAN}Enter new player name: {Colors.RESET}").strip()
            if new_name:
                self.player_name = new_name
                print(f"{Colors.GREEN}Player name updated to {new_name}{Colors.RESET}")
                time.sleep(1)
        elif choice == '3':
            return
    
    def how_to_play(self):
        """Display game instructions"""
        self.clear_screen()
        print(f"""
    {Colors.CYAN}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}
    {Colors.CYAN}║{Colors.BOLD}{Colors.MAGENTA}                    HOW TO PLAY                     {Colors.RESET}{Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}╠═══════════════════════════════════════════════════════════╣{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║  {Colors.YELLOW}🎯 {Colors.BOLD}OBJECTIVE:{Colors.RESET} Get 3 in a row!                     {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}1.{Colors.RESET} The board has 9 positions numbered 1-9:           {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║        {Colors.WHITE}1   2   3{Colors.RESET}                               {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║        {Colors.WHITE}4   5   6{Colors.RESET}                               {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║        {Colors.WHITE}7   8   9{Colors.RESET}                               {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}2.{Colors.RESET} Enter the number (1-9) to place your mark        {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}3.{Colors.RESET} {Colors.CYAN}X{Colors.RESET} goes first, then {Colors.YELLOW}O{Colors.RESET} alternates              {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}4.{Colors.RESET} {Colors.BOLD}CONTROLS:{Colors.RESET}                                 {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║     • {Colors.GREEN}1-9{Colors.RESET} - Make a move                         {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║     • {Colors.YELLOW}r{Colors.RESET}   - Restart game                       {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║     • {Colors.YELLOW}m{Colors.RESET}   - Main Menu                          {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║     • {Colors.YELLOW}q{Colors.RESET}   - Quit game                          {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║     • {Colors.YELLOW}p{Colors.RESET}   - Toggle position display            {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}
        """)
        input(f"\n{Colors.CYAN}Press Enter to return to main menu...{Colors.RESET}")
    
    def view_leaderboard(self):
        """Display leaderboard with colors"""
        self.clear_screen()
        print(f"""
    {Colors.CYAN}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}
    {Colors.CYAN}║{Colors.BOLD}{Colors.MAGENTA}                   LEADERBOARD                      {Colors.RESET}{Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}╠═══════════════════════════════════════════════════════════╣{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║  {Colors.YELLOW}🥇 {Colors.BOLD}1. 🤖 Terminator Bot{Colors.RESET}                  {Colors.GREEN}W: 999{Colors.RESET}  {Colors.RED}L: 0{Colors.RESET}   {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.WHITE}🥈 {Colors.BOLD}2. 🏆 Champion Player{Colors.RESET}                 {Colors.GREEN}W: 87{Colors.RESET}   {Colors.RED}L: 12{Colors.RESET}  {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.MAGENTA}🥉 {Colors.BOLD}3. ⭐ Star Player{Colors.RESET}                    {Colors.GREEN}W: 65{Colors.RESET}   {Colors.RED}L: 20{Colors.RESET}  {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.BOLD}4. 🎮 Rookie{Colors.RESET}                           {Colors.GREEN}W: 42{Colors.RESET}   {Colors.RED}L: 35{Colors.RESET}  {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.BOLD}5. 👑 King of Tic Tac{Colors.RESET}                  {Colors.GREEN}W: 30{Colors.RESET}   {Colors.RED}L: 15{Colors.RESET}  {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}
        """)
        input(f"\n{Colors.CYAN}Press Enter to return to main menu...{Colors.RESET}")
    
    def choose_difficulty(self):
        """Let player choose AI difficulty with colors"""
        self.clear_screen()
        print(f"""
    {Colors.CYAN}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}
    {Colors.CYAN}║{Colors.BOLD}{Colors.MAGENTA}               CHOOSE AI DIFFICULTY                {Colors.RESET}{Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}╠═══════════════════════════════════════════════════════════╣{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║  {Colors.GREEN}1.{Colors.RESET} {Colors.GREEN}😊 EASY{Colors.RESET}   - Novice Bot (Random moves)       {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.YELLOW}2.{Colors.RESET} {Colors.YELLOW}😐 MEDIUM{Colors.RESET} - Pro Bot (Basic strategy)       {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.MAGENTA}3.{Colors.RESET} {Colors.MAGENTA}🤔 HARD{Colors.RESET}   - Master Bot (Advanced strategy) {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  {Colors.RED}4.{Colors.RESET} {Colors.RED}😱 IMPOSSIBLE{Colors.RESET} - Terminator Bot (Unbeatable)   {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}
        """)
        
        while True:
            choice = input(f"\n{Colors.YELLOW}Choose difficulty (1-4): {Colors.RESET}").strip()
            if choice == '1':
                return 'easy'
            elif choice == '2':
                return 'medium'
            elif choice == '3':
                return 'hard'
            elif choice == '4':
                return 'impossible'
            else:
                print(f"{Colors.RED}Invalid choice. Please enter 1-4.{Colors.RESET}")
    
    def play_vs_robot(self):
        """Play against AI robot"""
        self.clear_screen()
        print(f"\n{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}🤖 PLAY VS ROBOT 🤖{Colors.RESET}")
        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}\n")
        
        # Get player name
        self.player_name = input(f"{Colors.CYAN}Enter your name: {Colors.RESET}").strip() or "Player"
        
        # Choose difficulty
        difficulty = self.choose_difficulty()
        
        # Create game and AI
        self.game = TicTacToeGame(self.player_name, "🤖 Robot")
        self.ai = RobotAI(difficulty)
        
        print(f"\n{Colors.GREEN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}Starting game: {Colors.CYAN}{self.player_name} (X){Colors.RESET} vs {self.ai.get_difficulty_display()} (O)")
        print(f"{Colors.GREEN}{'═' * 60}{Colors.RESET}\n")
        
        self.play_game()
    
    def play_vs_friend(self):
        """Local multiplayer"""
        self.clear_screen()
        print(f"\n{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}👥 PLAY VS FRIEND 👥{Colors.RESET}")
        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}\n")
        
        # Get player names with colors
        player1 = input(f"{Colors.CYAN}Enter {Colors.BOLD}Player 1{Colors.RESET}{Colors.CYAN} name (X): {Colors.RESET}").strip() or "Player 1"
        player2 = input(f"{Colors.YELLOW}Enter {Colors.BOLD}Player 2{Colors.RESET}{Colors.YELLOW} name (O): {Colors.RESET}").strip() or "Player 2"
        
        # Create game
        self.game = TicTacToeGame(player1, player2)
        
        print(f"\n{Colors.GREEN}{'═' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}Starting game: {Colors.CYAN}{player1} (X){Colors.RESET} vs {Colors.YELLOW}{player2} (O){Colors.RESET}")
        print(f"{Colors.GREEN}{'═' * 60}{Colors.RESET}\n")
        
        self.play_game()
    
    def play_online(self):
        """Online multiplayer placeholder"""
        self.clear_screen()
        print(f"""
    {Colors.CYAN}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}
    {Colors.CYAN}║{Colors.BOLD}{Colors.MAGENTA}                    ONLINE PLAY                     {Colors.RESET}{Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}╠═══════════════════════════════════════════════════════════╣{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║        {Colors.BLINK}{Colors.YELLOW}🚧 UNDER CONSTRUCTION 🚧{Colors.RESET}                    {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║  Online multiplayer coming in next update!               {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}║  Features to expect:                                      {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  • Real-time multiplayer                                  {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  • Global leaderboards                                    {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  • Chat with opponents                                    {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║  • Tournament mode                                        {Colors.CYAN}║{Colors.RESET}
    {Colors.CYAN}║                                                           ║{Colors.RESET}
    {Colors.CYAN}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}
        """)
        input(f"\n{Colors.CYAN}Press Enter to return to main menu...{Colors.RESET}")
    
    def play_game(self):
        """Main game loop"""
        while True:
            self.clear_screen()
            
            # Show position reference if enabled
            if self.show_positions:
                print(self.game.get_board_position_map())
                print(f"\n{Colors.CYAN}{'═' * 50}{Colors.RESET}\n")
            
            # Show current game board
            print(self.game.print_board_ascii())
            
            # Check if game is over
            if self.game.game_over:
                self.display_result()
                
                choice = input(f"\n{Colors.YELLOW}Press '{Colors.GREEN}r{Colors.YELLOW}' to restart, '{Colors.GREEN}m{Colors.YELLOW}' for menu, or any key to quit: {Colors.RESET}").lower()
                if choice == 'r':
                    # Restart same game mode
                    if self.ai:
                        difficulty = self.ai.difficulty
                        self.game = TicTacToeGame(self.player_name, "🤖 Robot")
                        self.ai = RobotAI(difficulty)
                    else:
                        player1 = self.game.players['X']
                        player2 = self.game.players['O']
                        self.game = TicTacToeGame(player1, player2)
                    continue
                elif choice == 'm':
                    break
                else:
                    print(f"\n{Colors.GREEN}Thanks for playing! 👋{Colors.RESET}")
                    sys.exit(0)
            
            # Handle input based on game mode
            if self.ai and self.game.current_player == 'O':
                # AI's turn
                ai_display = self.ai.get_difficulty_display()
                print(f"\n{Colors.MAGENTA}{ai_display} {Colors.BLINK}is thinking...{Colors.RESET}")
                
                move = self.ai.get_move(self.game)
                self.game.make_move(move)
                
                # Show AI move animation
                print(f"\n{Colors.GREEN}🤖 Robot placed O at position {move + 1}{Colors.RESET}")
                time.sleep(0.5)
            else:
                # Human's turn
                current_player_name = self.game.players[self.game.current_player]
                player_color = Colors.CYAN if self.game.current_player == 'X' else Colors.YELLOW
                
                print(f"\n{player_color}╔═══════════════════════════════════════════════════════╗{Colors.RESET}")
                print(f"{player_color}║ {Colors.BOLD}{current_player_name}'s turn ({self.game.current_player}) - Make your move!{Colors.RESET} {player_color}║{Colors.RESET}")
                print(f"{player_color}╚═══════════════════════════════════════════════════════╝{Colors.RESET}")
                
                while True:
                    cmd = input(f"\n{Colors.YELLOW}Enter position (1-9) or command (r/m/q/p): {Colors.RESET}").lower().strip()
                    
                    if cmd == 'p':
                        # Toggle position display
                        self.show_positions = not self.show_positions
                        print(f"{Colors.GREEN}Position numbers {'enabled' if self.show_positions else 'disabled'}{Colors.RESET}")
                        break  # Redraw screen
                    
                    elif cmd == 'r':
                        # Restart game
                        if self.ai:
                            difficulty = self.ai.difficulty
                            self.game = TicTacToeGame(self.player_name, "🤖 Robot")
                            self.ai = RobotAI(difficulty)
                        else:
                            player1 = self.game.players['X']
                            player2 = self.game.players['O']
                            self.game = TicTacToeGame(player1, player2)
                        break
                    
                    elif cmd == 'm':
                        return  # Return to main menu
                    
                    elif cmd == 'q':
                        print(f"\n{Colors.GREEN}Thanks for playing! 👋{Colors.RESET}")
                        sys.exit(0)
                    
                    else:
                        # Try to parse as move
                        try:
                            position = int(cmd) - 1
                            if 0 <= position <= 8:
                                if self.game.make_move(position):
                                    # Show move confirmation
                                    print(f"{Colors.GREEN}✓ Move placed at position {cmd}{Colors.RESET}")
                                    time.sleep(0.3)
                                    break
                                else:
                                    print(f"{Colors.RED}❌ Invalid move! Position already taken.{Colors.RESET}")
                            else:
                                print(f"{Colors.RED}❌ Invalid input! Please enter 1-9.{Colors.RESET}")
                        except ValueError:
                            print(f"{Colors.RED}❌ Invalid input! Please enter 1-9, 'r', 'm', 'q', or 'p'.{Colors.RESET}")
    
    def display_result(self):
        """Display game result with ASCII art and colors"""
        self.clear_screen()
        
        # Show final board
        print(self.game.print_board_ascii())
        print(f"\n{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        
        if self.game.winner == 'Tie':
            print(f"""
    {Colors.YELLOW}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}
    {Colors.YELLOW}║{Colors.BOLD}                   GAME OVER!                    {Colors.RESET}{Colors.YELLOW}║{Colors.RESET}
    {Colors.YELLOW}╠═══════════════════════════════════════════════════════════╣{Colors.RESET}
    {Colors.YELLOW}║                                                           ║{Colors.RESET}
    {Colors.YELLOW}║              {Colors.BOLD}{Colors.WHITE}IT'S A TIE! 🤝{Colors.RESET}                     {Colors.YELLOW}║{Colors.RESET}
    {Colors.YELLOW}║          {Colors.WHITE}No winners this time!{Colors.RESET}                 {Colors.YELLOW}║{Colors.RESET}
    {Colors.YELLOW}║                                                           ║{Colors.RESET}
    {Colors.YELLOW}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}
            """)
        
        else:
            winner_name = self.game.players[self.game.winner]
            winner_color = Colors.CYAN if self.game.winner == 'X' else Colors.YELLOW
            
            if self.ai and winner_name == "🤖 Robot":
                print(f"""
    {Colors.RED}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}
    {Colors.RED}║{Colors.BOLD}                   GAME OVER!                    {Colors.RESET}{Colors.RED}║{Colors.RESET}
    {Colors.RED}╠═══════════════════════════════════════════════════════════╣{Colors.RESET}
    {Colors.RED}║                                                           ║{Colors.RESET}
    {Colors.RED}║               {Colors.BOLD}🤖 ROBOT WINS!{Colors.RESET}                     {Colors.RED}║{Colors.RESET}
    {Colors.RED}║          {Colors.YELLOW}Better luck next time! 😢{Colors.RESET}               {Colors.RED}║{Colors.RESET}
    {Colors.RED}║                                                           ║{Colors.RESET}
    {Colors.RED}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}
                """)
            else:
                print(f"""
    {winner_color}╔═══════════════════════════════════════════════════════════╗{Colors.RESET}
    {winner_color}║{Colors.BOLD}                   GAME OVER!                    {Colors.RESET}{winner_color}║{Colors.RESET}
    {winner_color}╠═══════════════════════════════════════════════════════════╣{Colors.RESET}
    {winner_color}║                                                           ║{Colors.RESET}
    {winner_color}║            🎉 {Colors.BOLD}{winner_name:^20} {Colors.RESET}🎉            {winner_color}║{Colors.RESET}
    {winner_color}║               {Colors.BOLD}IS THE WINNER!{Colors.RESET}                    {winner_color}║{Colors.RESET}
    {winner_color}║            {Colors.GREEN}CONGRATULATIONS! 🏆{Colors.RESET}                 {winner_color}║{Colors.RESET}
    {winner_color}║                                                           ║{Colors.RESET}
    {winner_color}╚═══════════════════════════════════════════════════════════╝{Colors.RESET}
                """)
        
        # Show moves history
        print(f"\n{Colors.CYAN}{Colors.BOLD}📝 Moves History:{Colors.RESET}")
        print(f"{Colors.WHITE}  {'─' * 50}{Colors.RESET}")
        
        for i, move in enumerate(self.game.moves_history, 1):
            player_name = self.game.players[move['player']]
            player_color = Colors.CYAN if move['player'] == 'X' else Colors.YELLOW
            
            print(f"  {Colors.WHITE}{i:2}.{Colors.RESET} {player_color}{player_name:15}{Colors.RESET} placed "
                  f"{player_color}{move['player']}{Colors.RESET} at position "
                  f"{Colors.GREEN}{move['position'] + 1}{Colors.RESET} "
                  f"({Colors.MAGENTA}{move['time']}{Colors.RESET})")
        
        print(f"{Colors.WHITE}  {'─' * 50}{Colors.RESET}")

def main():
    """Main entry point"""
    # Clear screen and start
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Check for color support
    try:
        # Initialize game
        game = TicTacToeTerminal()
        
        # Print welcome message
        print(f"\n{Colors.GREEN}{Colors.BOLD}Welcome to Tic Tac Toe Terminal!{Colors.RESET}")
        print(f"{Colors.CYAN}Loading game...{Colors.RESET}")
        time.sleep(1)
        
        # Start main menu
        game.main_menu()
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Game interrupted. Thanks for playing!{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}An error occurred: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}Please ensure your terminal supports ANSI colors.{Colors.RESET}")

if __name__ == "__main__":
    main()
