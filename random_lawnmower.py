import json
import math
import socket
import sys
import time
import os

DATA_SIZE = 4096
STARTING_TIME = 120
SCALE = 10
RANGES = [-250, 250], [-200, 1200]

def area(r1, r2, d):
    if r1 + r2 < d:
        return 0
    if r1 + d < r2:
        return math.pi * r1 ** 2
    if r2 + d < r1:
        return math.pi * r2 ** 2
    return r1 ** 2 * math.acos((d ** 2 + r1 ** 2 - r2 ** 2) / (2 * d * r1)) + \
        r2 ** 2 * math.acos((d ** 2 - r1 ** 2 + r2 ** 2) / (2 * d * r2)) - \
        ((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2)) ** 0.5 / 2

def circum(r11, r12, r21, r22, d):
    return area(r12, r22, d) - area(r12, r21, d) - area(r11, r22, d) + area(r11, r21, d)

def taken(attachment, prior, d, rope):
    lower = max([i for i in prior if i <= attachment] or [0])
    higher = min([i for i in prior if i >= attachment] or [rope])
    return circum(lower, attachment, rope - higher, rope - attachment, d)

def get_socket(s, timed=False, time_limit=None):
    t0 = time.time()
    while True:
        data = s.recv(DATA_SIZE).decode('utf-8')
        if data:
            if timed:
                return data, time.time() - t0, True
            else:
                return data
        if timed and time.time() - t0 >= time_limit:
            return None, time_limit, False
        time.sleep(0.01)

def send_socket(s, data):
    s.sendall(data.encode('utf-8'))

def get_move(s, rope, time_limit):
    data, time_used, within_time = get_socket(s, timed=True, time_limit=time_limit)
    if not within_time:
        return None, time_used
    return [parse_move(i, rope) for i in data.split(' ')], time_used

def parse_move(s, rope):
    try:
        f = float(s)
        assert 0 <= f <= rope
        return f
    except (ValueError, AssertionError):
        return None

def r(x, y):
    return round(x, y)

class Game:
    def __init__(self, d, rope, attachments_per_player, clients, client_names):
        self.d = d
        self.rope = rope
        self.attachments_per_player = attachments_per_player
        self.clients = clients
        self.client_names = client_names
        self.total_score = [0, 0]
        self.time_left = [STARTING_TIME] * 2
    
    def start_round(self):
        self.player_moves = []
        self.scores = []
        self.prior = []
        self.move_buffers = [[], []]
    
    def get_score(self, x):
        return sum(i for (i, j) in zip(self.scores, self.player_moves) if j == x)
    
    def get_total_score(self, x):
        return self.total_score[x - 1] + self.get_score(x)
    
    def info_dict(self, index, round, turn):
        return {
            'player_number': index + 1,
            'moves': self.prior,
            'makers': self.player_moves,
            'player_1_score': self.get_score(1),
            'player_2_score': self.get_score(2),
            'player_1_total_score': self.get_total_score(1),
            'player_2_total_score': self.get_total_score(2),
            'current_turn': turn,
            'round': round,
            'turns_each': self.attachments_per_player
        }
    
    def update_screen(self, index, rnd, turn, message=None):
        x = [[0 for j in range(RANGES[1][0], RANGES[1][1] + SCALE, SCALE)]
            for i in range(RANGES[0][0], RANGES[0][1] + SCALE, SCALE)]
        x[int(-RANGES[0][0] // SCALE)][int(-RANGES[1][0] // SCALE)] = -2
        x[int(-RANGES[0][0] // SCALE)][int(self.d // SCALE - RANGES[1][0] // SCALE)] = -2
        for i in range(RANGES[0][0], RANGES[0][1] + SCALE, SCALE):
            for j in range(RANGES[1][0], RANGES[1][1] + SCALE, SCALE):
                i1, j1 = int(i // SCALE - RANGES[0][0] // SCALE), int(j // SCALE - RANGES[1][0] // SCALE)
                if sum((k - l) ** 2 for (k, l) in zip((i, j), (0, 0))) ** 0.5 + \
                    sum((k - l) ** 2 for (k, l) in zip((i, j), (0, self.d))) ** 0.5 > self.rope:
                    x[i1][j1] = -1
        for (p, pl) in zip(self.prior, self.player_moves):
            possible_range = [j for j in range(RANGES[1][0], RANGES[1][1] + SCALE, SCALE) if p + self.d - self.rope <= j <= p]
            for i in range(RANGES[0][0], RANGES[0][1] + SCALE, SCALE):
                for j in possible_range:
                    i1, j1 = int(i // SCALE - RANGES[0][0] // SCALE), int(j // SCALE - RANGES[1][0] // SCALE)
                    if x[i1][j1] == 0 and sum((k - l) ** 2 for (k, l) in zip((i, j), (0, 0))) <= p ** 2 and \
                        sum((k - l) ** 2 for (k, l) in zip((i, j), (0, self.d))) <= (self.rope - p) ** 2:
                        x[i1][j1] = pl
        if round == 2:
            x = [[{1: 2, 2: 1}[j] if j in (1, 2) else j for j in i] for i in x]
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
        color_key = ['\033[92m.', '\033[91m1', '\033[94m2', '\033[0mX', '\033[37m#']
        print('\n'.join(''.join(color_key[j] for j in i) for i in x))
        print(f'\033[91m1\033[0m = {self.client_names[(rnd + 1) % 2]}, \033[92m2\033[0m = {self.client_names[rnd % 2]}')
        if message:
            print(message)
        else:
            print(f'round {rnd}, turn {turn}, ' +
                f'{self.client_names[(rnd + 1) % 2]}: {r(self.get_total_score(1 + (rnd + 1) % 2), 3)}, {self.client_names[rnd % 2]}: {r(self.get_total_score(1 + rnd % 2), 3)} ' +
                f'(this round: {self.client_names[(rnd + 1) % 2]}: {r(self.get_score(1 + (rnd + 1) % 2), 3)}, {self.client_names[rnd % 2]}: {r(self.get_score(1 + rnd % 2), 3)})')
            print(f'{self.client_names[index]} just made an attachment with score {taken(self.prior[-1], self.prior[:-1], self.d, self.rope)}')
    
    def make_move(self, index, round, turn):
        if self.move_buffers[index]:
            attachment = self.move_buffers[index][0]
            self.move_buffers[index] = self.move_buffers[index][1:]
        else:
            send_socket(self.clients[index], json.dumps(self.info_dict(index, round, turn)))
            moves, diff = get_move(self.clients[index], self.rope, self.time_left[index])
            self.time_left[index] -= diff
            if self.time_left[index] <= 0:
                self.update_screen(index, round, turn, f'{self.client_names[index]} ran out of time.')
                return False
            if moves == []:
                # No, this shouldn't happen, but if it did it would be a mess without self.
                self.update_screen(index, round, turn, f'{self.client_names[index]} did not send back any moves.')
                return False
            attachment = moves[0]
            self.move_buffers[index] += moves[1:]
        if attachment == None:
            self.update_screen(index, round, turn, f'{self.client_names[index]} made an illegal attachment.')
            return False
        self.player_moves.append(index + 1)
        self.scores.append(taken(attachment, self.prior, self.d, self.rope))
        self.prior.append(attachment)
        self.update_screen(index, round, turn)
        return True
    
    def swap(self):
        self.client_names = self.client_names[::-1]
        self.clients = self.clients[::-1]
        self.total_score = self.total_score[::-1]
        self.time_left = self.time_left[::-1]
    
    def run_round(self, round):
        for turn in range(1, self.attachments_per_player + 1):
            first_index, second_index = (turn + 1) % 2, turn % 2
            r1 = self.make_move(first_index, round, turn)
            if not r1:
                return second_index, None, None
            r2 = self.make_move(second_index, round, turn)
            if not r2:
                return first_index
        self.total_score[0] += self.get_score(1)
        self.total_score[1] += self.get_score(2)
    
    def play(self):
        for round in [1, 2]:
            self.start_round()
            self.run_round(round)
            self.swap()
        if self.total_score[0] > self.total_score[1]:
            return 1, self.total_score[0], self.total_score[1]
        elif self.total_score[1] > self.total_score[0]:
            return 2, self.total_score[1], self.total_score[0]
        else:
            return None, None, None

def run_with_socket(d, rope, attachments_per_player, s):
    clients = []
    while len(clients) < 2:
        clients.append(s.accept()[0])
    raw_client_info = [get_socket(i) for i in clients]
    for i in raw_client_info:
        if i[:2] not in ('1 ', '2 '):
            print(f'Improperly formatted initial player output: {i}')
            return
    if raw_client_info[0][:2] == raw_client_info[1][:2]:
        print(f'Both players claim to play in same position initially: player {raw_client_info[0][0]}')
        return
    if raw_client_info[0][:2] == '2 ':
        clients = clients[::-1]
        raw_client_info = raw_client_info[::-1]
    client_names = [i[2:] for i in raw_client_info]
    winner, winner_score, loser_score = Game(d, rope, attachments_per_player, clients, client_names).play()
    if winner is None:
        print('It was a tie! (Both teams got exactly the same area covered)')
    elif winner_score is None:
        print(f'{client_names[winner - 1]} won due to the other team making an illegal move or running out of time!')
    else:
        print(f'{client_names[winner - 1]} won ({winner_score} to {loser_score})')


def get_argv(x):
    return sys.argv[sys.argv.index(x) + 1]

def main():
    d, rope, attachments_per_player, site = float(get_argv('--dist')), float(get_argv('--rope')), int(get_argv('--turns')), get_argv('--site')
    HOST = site.split(':')[0]
    PORT = int(site.split(':')[1])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    run_with_socket(d, rope, attachments_per_player, s)

if __name__ == '__main__':
    main()
