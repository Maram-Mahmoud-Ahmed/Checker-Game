import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import time
import copy
import random

TARGET_BOARD_SIZE = 600
WIN_WIDTH = TARGET_BOARD_SIZE + 250
WIN_HEIGHT = TARGET_BOARD_SIZE
HIGHLIGHT_COLOR = "lime green"
POSSIBLE_MOVE_COLOR = "yellow"

selected_piece = None
turn = "black"
board_matrix = [[None] * 8 for _ in range(8)]
pieces = []
possible_moves_indicators = []
must_jump = False
can_multi_jump = False
game_running = False

GAME_MODE = "PvP"
AI_COLOR = "white"
AI_DEPTH = 3

win = tk.Tk()
win.title("Checkers Game")
win.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
win.resizable(False, False)

bg_image_full = Image.open("checkers_Table.png")
bg_image = bg_image_full.resize((TARGET_BOARD_SIZE, TARGET_BOARD_SIZE))
bg_photo = ImageTk.PhotoImage(bg_image)

canvas = tk.Canvas(win, width=TARGET_BOARD_SIZE, height=TARGET_BOARD_SIZE, highlightthickness=0)
canvas.pack(side="left")

canvas.create_image(0, 0, image=bg_photo, anchor="nw")

square_size = TARGET_BOARD_SIZE // 10
board_start_x = square_size
board_start_y = square_size

def create_piece_image(filename, size):
    img = Image.open(filename).convert("RGBA")
    return ImageTk.PhotoImage(img.resize((size, size)))

piece_size = int(square_size)
white_piece = create_piece_image("White.png", piece_size)
black_piece = create_piece_image("Black.png", piece_size)
white_king_piece = create_piece_image("White_King.png", piece_size)
black_king_piece = create_piece_image("Black_King.png", piece_size)

side_panel = tk.Frame(win, width=250, height=TARGET_BOARD_SIZE, bg="light gray")
side_panel.pack(side="right")
side_panel.pack_propagate(False)

white_count = 12
black_count = 12
white_label = tk.Label(side_panel, text=f"White Pieces: {white_count}", font=("Arial", 14, "bold"), bg="light gray", fg="white")
white_label.pack(pady=20)
black_label = tk.Label(side_panel, text=f"Black Pieces: {black_count}", font=("Arial", 14, "bold"), bg="light gray", fg="black")
black_label.pack(pady=20)

timer_label = tk.Label(side_panel, text="Time: 00:00", font=("Arial", 16, "bold"), bg="light gray", fg="dark blue")
timer_label.pack(pady=40)

current_player = tk.StringVar(value="Black's Turn")
player_label = tk.Label(side_panel, textvariable=current_player, font=("Arial", 14, "bold"), bg="light gray", fg="red")
player_label.pack(pady=20)

mode_label = tk.Label(side_panel, text="Game Mode:", font=("Arial", 12, "bold"), bg="light gray")
mode_label.pack(pady=(20, 5))
mode_var = tk.StringVar(value="PvP")
mode_display = tk.Label(side_panel, textvariable=mode_var, font=("Arial", 12), bg="light gray", fg="green")
mode_display.pack()

start_time = 0

def update_timer():
    if not game_running:
        return
        
    elapsed = int(time.time() - start_time)
    minutes = elapsed // 60
    seconds = elapsed % 60
    
    timer_label.config(text=f"Time: {minutes:02d}:{seconds:02d}")
    win.after(1000, update_timer)

def get_canvas_center(row, col):
    x = board_start_x + col * square_size + square_size // 2
    y = board_start_y + row * square_size + square_size // 2
    return x, y

def get_board_coords(x, y):
    col = (x - board_start_x) // square_size
    row = (y - board_start_y) // square_size
    return row, col

def get_piece_at(row, col, piece_list=None):
    target_list = piece_list if piece_list is not None else pieces
    for piece in target_list:
        if piece["row"] == row and piece["col"] == col:
            return piece
    return None

def update_counts():
    white_label.config(text=f"White Pieces: {white_count}")
    black_label.config(text=f"Black Pieces: {black_count}")

def switch_turn():
    global turn, must_jump, can_multi_jump, game_running
    
    if can_multi_jump: return
    
    turn = "white" if turn == "black" else "black"
    current_player.set(f"{turn.capitalize()}'s Turn")
    
    if white_count == 0:
        game_running = False
        messagebox.showinfo("Game Over", "🎉 Black Wins! 🎉")
        start_game_screen()
        return
    elif black_count == 0:
        game_running = False
        messagebox.showinfo("Game Over", "🎉 White Wins! 🎉")
        start_game_screen()
        return
    if turn == 'white' and not get_all_moves(pieces , board_matrix , 'white'):
        game_running = False
        messagebox.showinfo("Game Over", "🎉 Black Wins! 🎉")
        start_game_screen()
        return
    if turn == 'black' and not get_all_moves(pieces , board_matrix , 'black'):
        game_running = False
        messagebox.showinfo("Game Over", "🎉 White Wins! 🎉")
        start_game_screen()
        return
            
    check_for_mandatory_jumps()
    
    if GAME_MODE == "PvC" and turn == AI_COLOR:
        win.after(500, ai_make_move) 

def check_for_mandatory_jumps():
    global must_jump
    if can_multi_jump:
        must_jump = True
        return
    must_jump = False
    
    for piece in pieces:
        if piece['type'] == turn:
            if calculate_valid_moves(piece, jump_only=True):
                must_jump = True
                break

def calculate_valid_moves(piece, jump_only=False, piece_list=None, board=None):
    valid_targets = []
    
    current_board = board if board is not None else board_matrix
    current_pieces = piece_list if piece_list is not None else pieces
    
    def find_piece_in_list(r, c):
        for p in current_pieces:
            if p['row'] == r and p['col'] == c: return p
        return None

    if piece['king']:
        directions = [-1, 1]
    else:
        directions = [1] if piece['type'] == 'white' else [-1]

    for r_dir in directions:
        for c_dir in [-1, 1]:
            mid_r, mid_c = piece['row'] + r_dir, piece['col'] + c_dir
            tgt_r, tgt_c = piece['row'] + 2*r_dir, piece['col'] + 2*c_dir
            
            if 0 <= tgt_r < 8 and 0 <= tgt_c < 8:
                if current_board[tgt_r][tgt_c] is None:
                    mid_piece = find_piece_in_list(mid_r, mid_c)
                    if mid_piece and mid_piece['type'] != piece['type']:
                        valid_targets.append((tgt_r, tgt_c, (mid_r, mid_c)))

    if valid_targets: return valid_targets

    if not jump_only:
        if piece_list is None and must_jump:
            return []

        for r_dir in directions:
            for c_dir in [-1, 1]:
                tgt_r, tgt_c = piece['row'] + r_dir, piece['col'] + c_dir
                if 0 <= tgt_r < 8 and 0 <= tgt_c < 8:
                    if current_board[tgt_r][tgt_c] is None:
                        valid_targets.append((tgt_r, tgt_c, None))
    return valid_targets

def move_piece(piece, r, c, captured_coords):
    global selected_piece, can_multi_jump, white_count, black_count
    
    if captured_coords:
        cap_piece = get_piece_at(*captured_coords)
        if cap_piece:
            canvas.delete(cap_piece['id'])
            pieces.remove(cap_piece)
            board_matrix[captured_coords[0]][captured_coords[1]] = None
            if cap_piece['type'] == 'white': white_count -= 1
            else: black_count -= 1
            update_counts()

    board_matrix[piece['row']][piece['col']] = None
    piece['row'], piece['col'] = r, c
    board_matrix[r][c] = piece['type']
    nx, ny = get_canvas_center(r, c)
    canvas.coords(piece['id'], nx, ny)
    canvas.tag_raise(piece['id'])

    if not piece['king']:
        if (piece['type'] == 'white' and r == 7) or (piece['type'] == 'black' and r == 0):
            piece['king'] = True
            print(f"{piece['type']} promoted to King!")
            new_img = white_king_piece if piece['type'] == 'white' else black_king_piece
            canvas.itemconfig(piece['id'], image=new_img)

    canvas.delete(selected_piece.pop('highlight_id', None))
    for x in possible_moves_indicators: canvas.delete(x)
    possible_moves_indicators.clear()

    if captured_coords and calculate_valid_moves(piece, jump_only=True):
        can_multi_jump = True
        selected_piece = piece
        highlight_piece(piece)
        show_moves(calculate_valid_moves(piece, jump_only=True))
        
        if GAME_MODE == "PvC" and turn == AI_COLOR:
            win.after(500, ai_make_move)
    else:
        can_multi_jump = False
        selected_piece = None
        switch_turn()

def highlight_piece(piece):
    x, y = get_canvas_center(piece['row'], piece['col'])
    pid = canvas.create_oval(x-35, y-35, x+35, y+35, outline=HIGHLIGHT_COLOR, width=3)
    piece['highlight_id'] = pid

def show_moves(moves):
    for r, c, _ in moves:
        x, y = get_canvas_center(r, c)
        pid = canvas.create_oval(x-10, y-10, x+10, y+10, fill=POSSIBLE_MOVE_COLOR)
        possible_moves_indicators.append(pid)

def on_click(event):
    global selected_piece
    
    if GAME_MODE == "PvC" and turn == AI_COLOR:
        return

    r, c = get_board_coords(event.x, event.y)
    
    if not (0 <= r < 8 and 0 <= c < 8):
        if selected_piece and not can_multi_jump:
            canvas.delete(selected_piece.pop('highlight_id', None))
            selected_piece = None
            for x in possible_moves_indicators: canvas.delete(x)
            possible_moves_indicators.clear()
        return

    clicked = get_piece_at(r, c)

    if selected_piece:
        moves = calculate_valid_moves(selected_piece)
        for mr, mc, cap in moves:
            if mr == r and mc == c:
                move_piece(selected_piece, r, c, cap)
                return
    
    if can_multi_jump: return

    if clicked and clicked['type'] == turn:
        if must_jump and not calculate_valid_moves(clicked, jump_only=True):
            return 
            
        if selected_piece: canvas.delete(selected_piece.pop('highlight_id', None))
        for x in possible_moves_indicators: canvas.delete(x)
        possible_moves_indicators.clear()

        selected_piece = clicked
        highlight_piece(clicked)
        show_moves(calculate_valid_moves(clicked))

canvas.bind("<Button-1>", on_click)

def evaluate_board(temp_pieces):
    score = 0
    for p in temp_pieces:
        val = 5 if p['king'] else 1
        if p['type'] == AI_COLOR:
            score += val
        else:
            score -= val
    return score

def simulate_move(piece, move, temp_pieces, temp_board):
    new_pieces = copy.deepcopy(temp_pieces)
    new_board = copy.deepcopy(temp_board)
    
    tgt_r, tgt_c, captured_coords = move
    
    moving_piece = None
    for p in new_pieces:
        if p['row'] == piece['row'] and p['col'] == piece['col']:
            moving_piece = p
            break
            
    if captured_coords:
        cap_r, cap_c = captured_coords
        for p in new_pieces:
            if p['row'] == cap_r and p['col'] == cap_c:
                new_pieces.remove(p)
                new_board[cap_r][cap_c] = None
                break
    
    new_board[moving_piece['row']][moving_piece['col']] = None
    moving_piece['row'] = tgt_r
    moving_piece['col'] = tgt_c
    new_board[tgt_r][tgt_c] = moving_piece['type']
    
    if not moving_piece['king']:
        if (moving_piece['type'] == 'white' and tgt_r == 7) or \
           (moving_piece['type'] == 'black' and tgt_r == 0):
            moving_piece['king'] = True
            
    return new_pieces, new_board

def get_all_moves(temp_pieces, temp_board, player_color):
    moves = []
    jumps_available = False
    possible_jumps = []
    
    for p in temp_pieces:
        if p['type'] == player_color:
            valid_moves = calculate_valid_moves(p, jump_only=True, piece_list=temp_pieces, board=temp_board)
            if valid_moves:
                jumps_available = True
                for m in valid_moves:
                    possible_jumps.append((p, m))
    
    if jumps_available:
        return possible_jumps
        
    for p in temp_pieces:
        if p['type'] == player_color:
            valid_moves = calculate_valid_moves(p, jump_only=False, piece_list=temp_pieces, board=temp_board)
            for m in valid_moves:
                moves.append((p, m))
                
    return moves

def minimax(temp_pieces, temp_board, depth, maximizing_player, alpha, beta):
    if depth == 0:
        return evaluate_board(temp_pieces), None
    
    current_color = AI_COLOR if maximizing_player else ("black" if AI_COLOR == "white" else "white")
    all_moves = get_all_moves(temp_pieces, temp_board, current_color)
    
    if not all_moves:
        return evaluate_board(temp_pieces), None 
        
    best_move = None
    
    if maximizing_player:
        max_eval = -float('inf')
        for piece, move in all_moves:
            new_pieces, new_board = simulate_move(piece, move, temp_pieces, temp_board)
            eval_score, _ = minimax(new_pieces, new_board, depth - 1, False, alpha, beta)
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (piece, move)
            
            alpha = max(alpha, eval_score)
            if beta <= alpha: break 
        return max_eval, best_move

    else:
        min_eval = float('inf')
        for piece, move in all_moves:
            new_pieces, new_board = simulate_move(piece, move, temp_pieces, temp_board)
            eval_score, _ = minimax(new_pieces, new_board, depth - 1, True, alpha, beta)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (piece, move)
                
            beta = min(beta, eval_score)
            if beta <= alpha: break
        return min_eval, best_move

def ai_make_move():
    global selected_piece
    
    if can_multi_jump and selected_piece:
        moves = calculate_valid_moves(selected_piece, jump_only=True)
        if moves:
            move_piece(selected_piece, moves[0][0], moves[0][1], moves[0][2])
        return

    temp_pieces = copy.deepcopy(pieces)
    temp_board = copy.deepcopy(board_matrix)
    
    _, best_move_data = minimax(temp_pieces, temp_board, AI_DEPTH, True, -float('inf'), float('inf'))
    
    if best_move_data:
        sim_piece, move = best_move_data
        real_piece = get_piece_at(sim_piece['row'], sim_piece['col'])
        
        if real_piece:
            selected_piece = real_piece
            move_piece(real_piece, move[0], move[1], move[2])
    else:
        pass

def start_game_screen():
    start_win = tk.Toplevel(win)
    start_win.title("Select Game Mode")
    start_win.geometry("300x200")
    
    tk.Label(start_win, text="Welcome to Checkers", font=("Arial", 16, "bold")).pack(pady=20)
    
    def set_pvp():
        global GAME_MODE
        GAME_MODE = "PvP"
        mode_var.set("PvP")
        start_win.destroy()
        place_pieces()
        
    def set_pvc():
        global GAME_MODE
        GAME_MODE = "PvC"
        mode_var.set("Player vs AI")
        start_win.destroy()
        place_pieces()
        
    tk.Button(start_win, text="Player vs Player", command=set_pvp, width=20).pack(pady=5)
    tk.Button(start_win, text="Player vs Computer", command=set_pvc, width=20).pack(pady=5)
    
    win.wait_window(start_win)

def place_pieces():
    global white_count, black_count, board_matrix, turn, selected_piece, can_multi_jump, start_time, game_running, must_jump, possible_moves_indicators
    
    canvas.delete("all")
    canvas.create_image(0, 0, image=bg_photo, anchor="nw")
    
    pieces.clear()
    possible_moves_indicators.clear()
    for r in range(8):
        for c in range(8):
            board_matrix[r][c] = None
            
    white_count = 0
    black_count = 0
    selected_piece = None
    can_multi_jump = False
    must_jump = False
    turn = "black"
    current_player.set("Black's Turn")

    for row in range(3):
        for col in range(8):
            if (row + col) % 2 == 1:
                create_piece(row, col, "white")
                white_count += 1

    for row in range(5, 8):
        for col in range(8):
            if (row + col) % 2 == 1:
                create_piece(row, col, "black")
                black_count += 1
    
    update_counts()

    def start_new_timer():
        global game_running, start_time
        game_running = True
        start_time = time.time()
        update_timer()

    win.after(100, start_new_timer)

def create_piece(r, c, color):
    x, y = get_canvas_center(r, c)
    img = white_piece if color == "white" else black_piece
    pid = canvas.create_image(x, y, image=img, anchor="center")
    pieces.append({"id": pid, "row": r, "col": c, "type": color, "king": False})
    board_matrix[r][c] = color


restart_button = tk.Button(side_panel, text="Restart / New Game", font=("Arial", 12), command=start_game_screen)
restart_button.pack(pady=20)

win.after(100, start_game_screen)
win.mainloop()
