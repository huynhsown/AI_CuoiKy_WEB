import numpy as np
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, Button, Div, Select
from bokeh.layouts import column as bokeh_column, row as bokeh_row, gridplot
from bokeh.plotting import figure
from bokeh.driving import linear
from easyAI import Negamax
from TwoPlayers import TwoPlayerGame
from Players import AI_Player, Human_Player
import time
from functools import partial

# Constants
WIDTH = 7
HEIGHT = 6
LEN_WIN = 4
COLORS = ['white', 'yellow', 'red']

class ConnectFourGame(TwoPlayerGame):
    def __init__(self, players, board=None):
        self.players = players
        self.board = board if board is not None else np.zeros((HEIGHT, WIDTH), dtype=int)
        self.current_player = 1

    def possible_moves(self):
        return [i for i in range(WIDTH) if self.board[:, i].min() == 0]

    def make_move(self, column):
        if self.board[HEIGHT-1, column] != 0:
            return False
        line = np.argmax(self.board[:, column] == 0)
        self.board[line, column] = self.current_player
        return True

    def show(self):
        print('\n' + '\n'.join([
            ' '.join([['.', 'O', 'X'][self.board[HEIGHT - 1 - j][i]] for i in range(WIDTH)]) for j in
            range(HEIGHT)]))

    def check_winner(self, player):
        # Check horizontal, vertical, and diagonal lines for a win
        for row in range(HEIGHT):
            for col in range(WIDTH - LEN_WIN + 1):
                if all(self.board[row, col + i] == player for i in range(LEN_WIN)):
                    return True

        for row in range(HEIGHT - LEN_WIN + 1):
            for col in range(WIDTH):
                if all(self.board[row + i, col] == player for i in range(LEN_WIN)):
                    return True

        for row in range(HEIGHT - LEN_WIN + 1):
            for col in range(WIDTH - LEN_WIN + 1):
                if all(self.board[row + i, col + i] == player for i in range(LEN_WIN)):
                    return True

        for row in range(LEN_WIN - 1, HEIGHT):
            for col in range(WIDTH - LEN_WIN + 1):
                if all(self.board[row - i, col + i] == player for i in range(LEN_WIN)):
                    return True

        return False

    def loss_condition(self):
        return self.check_winner(self.opponent_index)

    def is_over(self):
        return self.check_winner(1) or self.check_winner(2) or (self.board.min() > 0)

    def scoring(self):
        return -100 if self.loss_condition() else 0

    def reset(self, players):
        self.__init__(players)


class ConnectFourApp:
    def __init__(self):
        self.game_started = False
        self.algo_neg = Negamax(5)
        self.human_player = Human_Player()
        self.game = None
        self.board = None

        self.setup_bokeh()

    def setup_bokeh(self):
        self.p = figure(x_range=(-0.5, WIDTH + 0.5), y_range=(-0.5, HEIGHT + 0.5),
                        width=700, height=600, tools="", toolbar_location=None,
                        styles={'transform': 'translate(50px, 10px)', 'border': '1px solid black', 'background-color': '#8B4513'})
        self.p.grid.visible = False
        self.p.axis.visible = False
        self.p.background_fill_color = "#2C7B4A"

        self.circles = ColumnDataSource(data=dict(x=[], y=[], color=[]))

        for row in range(HEIGHT):
            for col in range(WIDTH):
                self.circles.data['x'].append(col + 0.5)
                self.circles.data['y'].append(row + 0.5)
                self.circles.data['color'].append(COLORS[0])

        self.p.scatter('x', 'y', source=self.circles, size=50, color='color', line_color="black")

        self.notification_div = Div(text="Welcome to Connect Four!", width=200, height=100)
        self.notification_div.styles = {'background-color': '#95BFB0', 'border': '1px solid black', 'color': 'white',
                                        'text-align': 'center', 'font-size': '20px'}

        self.start_button = Button(label="Start Game", width=200, height=50, button_type="success")
        self.start_button.on_click(self.start_game)

        self.reset_button = Button(label="Reset", width=150, height=50, button_type="primary",
                                   styles={'transform': 'translate(25px, 0px)'})
        self.reset_button.on_click(self.reset_game)

        self.difficulty_select = Select(title="Difficulty", options=["Easy", "Medium", "Hard"], value="Medium",
                                        styles={'color': 'white', 'font-size': '15px'})
        self.difficulty_select.on_change('value', self.update_difficulty)

        self.image_div = Div(
            text="<img src='https://tse2.mm.bing.net/th?id=OIP.8YELn0KiSXXEgbZraTqtugHaHa&pid=Api&P=0&h=180' width='100' height='100'>",
            width=200, height=100, styles={'transform': 'translate(50px, 5px)'})

        self.title_div = Div(text="""
        <h1 style="
            text-align: center; 
            color: white; 
            font-family: 'Arial Black', Gadget, sans-serif;
            font-size: 25px;
            text-shadow: 3px 3px 5px black;
        ">Connect Four</h1>""", width=200, height=50)

        self.buttons_and_notification_layout = bokeh_column(self.image_div, self.title_div, self.start_button,
                                                            self.reset_button, self.difficulty_select, self.notification_div)
        self.buttons_and_notification_layout.styles = {'background-color': '#1E5938', 'border': '1px solid black',
                                                       'transform': 'translate(20px, 20px)'}

        self.grid_layout = gridplot([[bokeh_row(self.buttons_and_notification_layout, self.p)]], toolbar_location=None, sizing_mode='scale_width',
                                    merge_tools=False)

        self.p.on_event('tap', self.on_click)

        curdoc().add_root(self.grid_layout)
        curdoc().title = "Connect Four with Bokeh"

    def start_game(self):
        self.game_started = True
        self.start_button.visible = False
        self.p.visible = True
        self.game = ConnectFourGame([self.human_player, AI_Player(self.algo_neg)])
        self.board = self.game.board
        self.update_board()
        self.notification_div.text = "Game started! Your turn!"

    def reset_game(self):
        self.game.reset([self.human_player, AI_Player(self.algo_neg)])
        self.board = self.game.board
        self.update_board()
        self.notification_div.text = "Welcome to Connect Four!"

    def update_difficulty(self, attr, old, new):
        if new == "Easy":
            self.algo_neg.depth = 3
        elif new == "Medium":
            self.algo_neg.depth = 5
        elif new == "Hard":
            self.algo_neg.depth = 7

    def update_board(self):
        self.circles.data['color'] = [COLORS[self.board[row, col]] for row in range(HEIGHT) for col in range(WIDTH)]

    def make_move(self, column):
        if not self.game.is_over() and self.game.current_player == 1:
            if self.game.make_move(column):
                self.game.show()
                self.animate_fall(column, np.argmax(self.game.board[:, column] == 0) - 1, COLORS[1])
                if self.game.is_over():
                    if self.game.check_winner(1):
                        self.notification_div.text = "Game over! You won!"
                    elif self.game.check_winner(2):
                        self.notification_div.text = "Game over! AI won!"
                    else:
                        self.notification_div.text = "Game over! It's a draw!"
                else:
                    self.game.switch_player()
                    self.notification_div.text = "Waiting For AI...!"
                    curdoc().add_timeout_callback(partial(self.make_ai_move, column), 2000)

    def make_ai_move(self, column):
        ai_move = self.game.players[1].ask_move(self.game)
        self.game.make_move(ai_move)
        self.game.show()
        self.animate_fall(ai_move, np.argmax(self.game.board[:, ai_move] == 0) - 1, COLORS[2])
        if self.game.is_over():
            if self.game.check_winner(1):
                self.notification_div.text = "Game over! You won!"
            elif self.game.check_winner(2):
                self.notification_div.text = "Game over! AI won!"
            else:
                self.notification_div.text = "Game over! It's a draw!"
        else:
            self.game.switch_player()
            self.notification_div.text = "Your turn!"

    def animate_fall(self, col, target_row, color):
        current_y = HEIGHT - 0.5
        final_y = target_row + 0.5
        disc = self.p.scatter(x=[col + 0.5], y=[current_y], color=[color], size=50, line_color="black")

        @linear()
        def update(step):
            nonlocal current_y
            if current_y > final_y:
                current_y -= 1
                disc.data_source.data['y'] = [current_y]
                time.sleep(0.1)

        curdoc().add_periodic_callback(update, 50)

    def on_click(self, event):
        col = int(event.x)
        if 0 <= col < WIDTH:
            self.make_move(col)


connect_four_app = ConnectFourApp()
