# Random Lawnmower Architecture
### '; DROP TABLE teams;

des480@nyu.edu

Game description: [https://cs.nyu.edu/courses/fall20/CSCI-GA.2965-001/randomower.html]

### Driver

The driver is random_lawnmower.py. It is written in Python 3 and should be called as
```
python3 random_lawnmower.py --dist 1000 --rope 1100 --turns <turns per player> --site localhost:8000
```
The distance between posts and length of the rope can be changed by passing different arguments after `--dist` and `--rope`. The number of turns per player is defined as the number of attachments each player makes per round (which, as we have been told in class, will be an even number between 2 and 10 inclusive). The site can be changed; if there is an error in your program while you are testing (or in the driver, but those are hopefully gone) and you get an error that the socket is used, you can replace `--site` by, for example, `localhost:8001` (the socket should be usable a few minutes later). However, `localhost:8000` will be used in the actual competition. The program will run one round with each player going first and draw ASCII diagrams showing the game state in the terminal (your window may need to be made wider, and the ASCII diagrams have only been tested with distance between posts 1000 and length of rope 1100).

In the process of running a round, the driver will first wait for each player to create a socket connecting to `localhost:8000` (or the site given), then for each player to send a string of the form `1 <player name>` if they are the first player (thus making the first move, fourth move, etc. in the first round) or `2 <player name>` if they are the second player (thus making the second move, third move, etc. in the first round). Player names may have spaces or other special characters. Players should only send in a string of this form at the start of the whole game. After receiving these strings, the driver will start a round in which the first player goes first and the second player goes second, then following the turn order given in the problem description. After that round concludes, the driver will start a round in which player order reverses.

On each player's turn, that player will be sent through their socket connection a JSON object representing the current game state, of the form (without newlines or spaces except for a single space after each colon or comma)
```
{
    "player_number": <1 if first, 2 if second>,
    "moves": <list of prior attachments in round>,
    "makers": <who made each attachment in round, in attachment order, each entry 1 or 2>,
    "player_1_score": <total score of player 1 in current round>,
    "player_2_score": <total score of player 2 in current round>,
    "player_1_total_score": <total score of player 1 in all rounds so far>,
    "player_2_total_score": <total score of player 1 in all rounds so far>,
    "current_turn": <turn it is for player to play, goes from 1 to turns each player gets>,
    "round": <round number, either 1 if first round or 2 if second round>,
    "turns_each": <turns each player gets per round>
}
```
Note that in the second round, which player is player 1 and which is player 2 will be reversed compared to the first round. The player is expected to send back a floating-point number between 0 and the rope length (inclusive) indicating where they will make an attachment.

A player may send several space-separated floating-point numbers at once. If a player does this, their moves will be at those attachment locations, in order, until they have made an attachment at each location. For example, if a player sent "364.5 573.2", they would first make an attachment at 364.5 and then make one at 573.2. If a player sends several moves at once in this way, they will not be sent a JSON object representing the current game state until their moves are all made. If a player has leftover unmade moves that were sent in previously but the round ends, these leftover unmade moves will be ignored and not happen. This rule is here to allow a player to send in two consecutive moves at once but not require it. Sending moves in if the opponent makes intervening moves is also allowed, but seems like a bad idea.

### Example client

The example client is random_lawnmower_example.py. It is written in Python 3 and should be called as
```
python3 random_lawnmower_example.py --dist 1000 --rope 1100 --turns <turns per player> --site localhost:8000 --name <player name> --tries <number of moves to consider per turn> <-f if first otherwise not>
```
If the player name to give to the example has spaces, it must be surrounded with quotes, due to terminal argument parsing. (There is no such needed handling of custom player names, which will presumably be hardcoded.) The algorithm used by random_lawnmower_example.py is to take the greedy choice from a certain number of attempts (the number of moves to consider per turn passed in). Thus, increasing this number of attempts will make random_lawnmower_example.py slightly better (but, especially after 20 attempts or so, not that much better).

### Submissions

Send me an email before noon Monday October 19th with your code and instructions on how to compile it (if needed) and how to run it as the first or second player and with a given even number of turns between 2 and 10 inclusive. Your code should be able to connect to a socket on `localhost:8000` and do the input and output described above (output its play order and player name, take in a JSON game state object in the format described above, output a floating point move).
