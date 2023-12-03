from pathlib import Path
from typing import List
from itertools import combinations
import docker
import random
import queue, time
from timeit import default_timer as timer
import os
def run_container(name: str, command: List[str]):
    # Create a docker client
    client = docker.from_env()
    print(f"docker run -v /home/sowmith/maze-game/videos:/root/videos -d --name {name} tournament:latest {command}")
    os.system(f"docker run -v /home/sowmith/maze-game/videos:/root/videos -d --name {name} tournament:latest {command}")

    container = client.containers.get(name)
    print(container.status)
    return container

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
        self.maze = maze
        self.start_time = None
        self.match_title = f"{self.player1.group_num}_vs_{self.player2.group_num}"
        self.run_cmd = self.gen_run_cmd()
        self.winner = False
        self.player1_pid = False
        self.player2_pid = False
        self.container = None
        self.comment = ""
        self.stop = False
        self.TSLU = 0 # time since last update to output
    
    # Takes the players and creates the ./server command
    def gen_run_cmd(self):
        # return ["./server", f"{self.maze.path_to_maze}", f"/root/videos/{self.match_title}", f"python3 {self.player1.path_to_agent}", f"python3 {self.player2.path_to_agent}"]
        return f"./server {self.maze.path_to_maze} /root/videos/{self.match_title} 'python3 {self.player1.path_to_agent}' 'python3 {self.player2.path_to_agent}'"
    
    def deploy(self):
        print(self.match_title+" is being started")
        self.start_time = timer()
        self.container = run_container(self.match_title, self.run_cmd)
        self.update_stats()
    
    def update_stats(self):
        time.sleep(1)
        self.container.reload()
        if(self.container.attrs['State']['Running'] and not self.container.exec_run("cat /root/maze-game/pidfile.txt")[0]):
            exit_code, pid_output = self.container.exec_run("cat /root/maze-game/pidfile.txt")
            pid_output = pid_output.decode('utf-8')
            pids = pid_output.split('\n')
            self.player1_pid = pids[0]
            self.player2_pid = pids[1]
        if(not (self.player1_pid and self.player2_pid)):
            if(timer()-self.start_time < 30):
                self.update_stats()
            else:
                self.comment = "No pids were generated after 30 seconds"
                self.stop = True
    
    def check_server(self):
        if(not self.container.attrs['State']['Running']):
            self.stop = True
            self.comment += " Server exited "
            return False
        return True
    
    def get_TSLU(self):
        if(self.container.attrs['State']['Running']):
            e, o = self.container.exec_run("stat -c %Y /root/maze-game/out")
            e, o2 = self.container.exec_run(r"date +%s")
            self.TSLU = int(o2.decode('utf-8')) - int(o.decode('utf-8'))

    def __eq__(self, other):
        distinct_players = set([self.player1.group_num, self.player2.group_num, other.player1.group_num, other.player2.group_num])
        if len(distinct_players) <= 2:
            return True
        else:
            return False

    # if out.txt exist, readit and update the winner, and 
    def get_out_txt(self):
        winner = None # -1 for draw, 0 for p1 and 1 for p2
        outfile = Path(f"./videos/{self.match_title}.txt")
        if(outfile.exists()):
            with open(outfile, "r") as outfile_:
                winner = int(outfile_.read())
            if winner == -1:
                self.winner = -1
                self.comment += "Draw"
            elif winner == 0:
                self.winner = 1
                self.comment += f"{self.player1.group_num} won"
            elif winner == 1:
                self.winner = 2
                self.comment += f"{self.player2.group_num} won"
    
    def check_player(self):
        if(self.container.attrs['State']['Running']):
            p1_exitcode, p1_output = self.container.exec_run(f"ps -p {self.player1_pid}")
            p2_exitcode, p2_output = self.container.exec_run(f"ps -p {self.player2_pid}")
            if p1_exitcode: # meaning the bot has exited
                self.stop = True
                self.winner = 2
                self.comment += f" player from {self.player1.group_num} exited "
                if p2_exitcode:
                    self.comment += f" player from {self.player2.group_num} exited "
                    self.winner = -1
                return (False, False)
            elif p2_exitcode:
                self.stop = True
                self.winner = 1
                self.comment += f" player from {self.player2.group_num} exited "
                return (False, False)
            return (True, True)
        return (False, False)
    
    def __str__(self):
        return f"""Match between {self.player1.group_num} and {self.player2.group_num} on maze {self.maze.maze_num}
        Player1 pid: {self.player1_pid} and Player2 pid: {self.player2_pid}
        Winner: {self.winner}
        Comment: {self.comment}
        TSLU: {self.TSLU}
        STOP: {self.stop}
                """

class Roster:
    # this is supposed to intialize all the players and then create the queue of all the games, that are to be played.
    def __init__(self, group_dir: Path, maze_dir: Path):
        self.group_dir = group_dir
        self.maze_dir = maze_dir
        self.players: List[Player] = []
        self.mazes : List[Maze] = []
        self.get_players()
        self.get_mazes()
        self.matches = []
        self.make_matches()
    
    def get_players(self):
        for group in self.group_dir.iterdir():
            group_num = int(group.name)
            agent_path = group.joinpath(Path(f"{group_num}.py"))
            temp_player = Player(agent_path, group_num)
            self.players.append(temp_player)
    
    def get_player(self, group_num):
        for player in self.players:
            if player.group_num == group_num:
                return player
        return None

    def get_mazes(self):
        for maze in self.maze_dir.iterdir():
            maze_num = int(maze.name.split('.')[0])
            temp_maze = Maze(maze, maze_num)
            self.mazes.append(temp_maze)

    def make_roster(self):
        player_side_count = {}
        combos = []
        player_list =[]
        for player in self.players:
            player_list.append(player.group_num)
        count = 0
        while(count<36):
            p1 = random.choice(player_list)
            p2 = random.choice(player_list)
            if p1 != p2:
                if (p1, p2) not in combos and (p2, p1) not in combos:
                    if(player_side_count.get(p1,0) < 8 and player_side_count.get(p2,0) < 8):
                        combos.append((p1, p2))
                        player_side_count[p1]= player_side_count.get(p1, 0) + 1
                        player_side_count[p2]= player_side_count.get(p2, 0) + 1
                        count += 1
                    if(player_side_count.get(p1)==8):
                        player_list.remove(p1)
                    if(player_side_count.get(p2)==8):
                        player_list.remove(p2)
        return combos
    
    def make_matches(self):
        for combo in self.make_roster():
            temp_match = Match(self.get_player(combo[0]), self.get_player(combo[1]), random.choice(self.mazes))
            self.matches.append(temp_match)

class Manager:
    def __init__(self, roster: Roster, max_workers = 6):
        self.roster = roster
        self.scoreboard = {}  # dictionary of dictionaries
        self.completed = []
        self.q = queue.Queue(36)
        self.monitor: List[Match] = []
        for match in self.roster.matches:
            self.q.put(match)
        for player in self.roster.players:
            self.scoreboard[player] = {}
    
    # Take 5-6 matches from queue and deploy them each and update the match with stuff form the docker
    def render_loop(self):
        while(len(self.monitor)< 1): # max_num_workers == 6
            t_match: Match = self.q.get()
            t_match.deploy()
            self.monitor.append(t_match)
    
    def do_monitor(self):
        # check if the bot has actually ended, is there out.txt, if there is 
        rem_items = []
        for i in range(len(self.monitor)):
            match = self.monitor[i]
            match.get_out_txt() # updates the winner if the renderrind is done
            p1,p2 = match.check_player()
            s = match.check_server()
            if match.stop or match.winner or match.TSLU > 300:
                print(match)
                if(self.monitor[i].container.attrs['State']['Running']):
                    self.monitor[i].container.kill()
                self.completed.append(self.monitor[i])
                rem_items.append(i)
        for x in rem_items:
            self.monitor.pop(x)

            

def main():
    print("Starting the tournament")
    roster = Roster(Path("./groups"), Path("./mazepool"))
    print("Roster is ready")
    manager = Manager(roster)
    print("Manager is ready")
    for x in manager.q:
        manager.render_loop()
        manager.do_monitor()
        time.sleep(0.25)
        

if __name__ == "__main__":
    main()