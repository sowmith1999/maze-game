from pathlib import Path
from typing import List
from itertools import combinations
class Player:
    def __init__(self, path, group_num):
        self.path_to_agent = Path(path)
        self.group_num = group_num
    def __str__(self):
        # return f"GroupNum: {self.group_num} and Path to the agent is : {self.path_to_agent}"
        return f"GroupNum: {self.group_num}"

class Maze:
    def __init__(self, maze_path, maze_num):
        self.path_to_maze = maze_path
        self.maze_num = maze_num

class Match:
    def __init__(self, player1: Player, player2: Player, maze: Maze):
        self.player1: Player = player1
        self.player2: Player = player2
        self.match_title = f"{self.player1.group_num}_vs_{self.player2.group_num}"
        self.winner = None
        self.maze = maze
        self.player1_status = True
        self.player2_status = True
        self.server_status = True
        self.run_cmd = self.gen_run_cmd()
    
    # Takes the players and creates the ./server command
    def gen_run_cmd(self):
        return f"./server \"{self.maze.path_to_maze}\" \"videos/{self.match_title}\" \"python3 {self.player1.path_to_agent}\" \"python3 {self.player2.path_to_agent}\""
    # checks the status of two players and the server and sets the status variables.
    def status_check(self):
        pass
    
    # # read the out.txt from the server and declare the winner, return 0 for tie, 1 for player1 and 2 for player2.
    # def get_winner():


class Roster:
    # this is supposed to intialize all the players and then create the queue of all the games, that are to be played.
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.players: List[Player] = []
        self.get_players()
        self.combos = self.make_roster()
        print(self.combos)
        print(len(self.combos))
    
    def get_players(self):
        for group in self.root_dir.iterdir():
            group_num = int(group.name)
            agent_path = group.joinpath(Path(f"{group_num}.py"))
            temp_player = Player(agent_path, group_num)
            self.players.append(temp_player)
    # Looks at the players and generates the league stage roster.
    def make_roster(self):
        player_combinations = list(combinations(self.players, 2))
        return player_combinations

def main():
    roster = Roster(Path("/root/my_game/groups"))
    # for player in roster.players:
    #     print(player)
    # match = Match(roster.players[0], roster.players[1])
    # print(match.run_cmd)

if __name__ == "__main__":
    main()
    