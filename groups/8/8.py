from sys import stdin
from select import select
from time import sleep
from math import inf

TOP = 0
END = -1

class AstarBot:
    def __init__(self):
        # initializing bot position.
        self.x = 0.5
        self.y = 0.5
        self.tx = -1
        self.ty = -1
        self.home_x = 0
        self.home_y = 0
        
        # storing bot's plan.
        self.plan = []
        
        # tracking dead_ends, walls. visited tiles
        
        self.seen = set()
        self.dead = set()
        self.walls = set()
        
        # initilatize pathcost,coinhandling,temp walls
        
        self.path_cost = 0
        self.coins_collected = 0
        self.timed_walls = set()
        self.timed_dead_ends = set()
        self.temp_cost = 0
        self.temp_wall_placed = False
        self.wall_set_ago = 0
        self.wall_available = False
    
    def start_bot(self):
        #start the bot and enter the main loop
        #Introduce ourselves, all friendly like
        print("himynameis aStarBot", flush=True)
        sleep(0.25)
        self.main()
    
    def read_input(self):
        # read the inp from the stdin
        while select([stdin,],[],[],0.0)[0]:
            obs = stdin.readline()
            obs = obs.split(" ")
            if obs == []:
                continue
            # 
            if obs[0] == "bot":
                #update our own position
                self.x = float(obs[1])
                self.y = float(obs[2])
                self.coins_collected = int(obs[3])
                if not ((int(self.x) != self.tx or int(self.y) != self.ty) and ((self.x-(int(self.x)+0.5))**2 + (self.y-(int(self.y)+0.5))**2)**0.5 < 0.2):
                    continue
                self.tx = int(self.x)
                self.ty = int(self.y)
                if self.plan != []:
                    continue
                self.plan = [(self.tx,self.ty)]
                self.home_x = self.tx
                self.home_y = self.ty
                self.seen = set(self.plan)
                continue

            if obs[0] == "wall":
                #ensure every wall we see is tracked in our walls set.
                x0 = int(float(obs[1]))
                y0 = int(float(obs[2]))
                x1 = int(float(obs[3]))
                y1 = int(float(obs[4]))
                self.walls |= {(x0,y0,x1,y1)}
                continue

            if obs[0] == "twall":
                if float(obs[3]) <= 12 or self.wall_set_ago != 0:
                    continue
                
                self.temp_wall_placed = True
                self.x = int(float(obs[1]))
                self.y = int(float(obs[2]))
                self.timed_walls |= {(self.x,self.y)}
                continue
    
    def block_enemy(self):
        if self.coins_collected < 6:
            return
        wall_set = False
        
        end_x, end_y = self.plan[END]
        prev_x, prev_y = self.plan[END-1]
        
        def create_temp_wall(direction):
            match direction:
                case "u":
                    print("block {0} {1} u".format(end_x, end_y), flush=True)
                case "d":
                    print("block {0} {1} d".format(end_x, end_y), flush=True)
                case "l":
                    print("block {0} {1} l".format(end_x, end_y), flush=True)
                case "r":
                    print("block {0} {1} r".format(end_x, end_y), flush=True)
            
            nonlocal wall_set
            wall_set = True
                    
        
        if self.wall_available:
            if(end_x == 1) and (end_y == 0):
                create_temp_wall("l")
            if(end_x == 0) and (end_y == 1):
                create_temp_wall("u")
            if(end_x == 10) and (end_y == 9):
                create_temp_wall("d")
            if(end_x == 9) and (end_y == 10):
                create_temp_wall("r")
            self.wall_available = False

        if(prev_x == 0) and (prev_y == 0):
            if(end_x == 1) and (end_y == 0):
                create_temp_wall("l")
            if(end_x == 0) and (end_y == 1):
                create_temp_wall("u")
        
        if(prev_x == 10) and (prev_y == 10):
            if(end_x == 10) and (end_y == 9):
                create_temp_wall("d")
            if(end_x == 9) and (end_y == 10):
                create_temp_wall("r")
        
        if wall_set:
            self.wall_set_ago = 5
    
    def update_deadend(self):
        planset = set(self.plan)
        self.dead = set()
        for i in range(11):
            for j in range(11):
                if (i,j) not in planset:
                    self.dead |= {(i,j)}
        self.seen = set()
        self.wall_available = True
    
    def eval_move1(self):
        possible_moves = [
            (self.tx, self.ty + 1, 0.5, self.tx, self.ty+1, self.tx+1, self.ty+1),
            (self.tx + 1, self.ty, 0.5, self.tx+1, self.ty, self.tx+1, self.ty+1),
            (self.tx, self.ty - 1, 1, self.tx, self.ty, self.tx+1, self.ty),
            (self.tx - 1, self.ty, 1, self.tx, self.ty, self.tx, self.ty+1)
        ]

        best_move = None
        minimum_distance = inf

        for move in possible_moves:
            new_tx, new_ty, factor, wall1, wall2, wall3, wall4 = move
            if len(self.seen) > 0 and (new_tx, new_ty) not in self.dead.union(self.seen) and (
                    wall1, wall2, wall3, wall4) not in self.walls:
                current_distance = (self.path_cost * 3) + (
                        ((new_tx - 10)**2 + (new_ty - 10)**2) * factor)
                if current_distance < minimum_distance:
                    minimum_distance = current_distance
                    best_move = (new_tx, new_ty)

        return best_move if best_move is not None else False

    def eval_move2(self):
        possible_moves = [
            (self.tx, self.ty + 1, 0.5, self.tx, self.ty+1, self.tx+1, self.ty+1),
            (self.tx + 1, self.ty, 0.5, self.tx+1, self.ty, self.tx+1, self.ty+1),
            (self.tx, self.ty - 1, 1, self.tx, self.ty, self.tx+1, self.ty),
            (self.tx - 1, self.ty, 1, self.tx, self.ty, self.tx, self.ty+1)
        ]
        
        best_move = None
        minimum_distance = inf
        
        for move in possible_moves:
            new_tx, new_ty, factor, wall1, wall2, wall3, wall4 = move
            if len(self.seen) > 0 and (new_tx, new_ty) not in self.timed_dead_ends.union(self.seen).union(self.timed_walls) and (
                    wall1, wall2, wall3, wall4) not in self.walls:
                current_distance = (self.temp_cost * 3) + (
                        ((new_tx - 10)**2 + (new_ty - 10)**2) * factor)
                if current_distance < minimum_distance:
                    minimum_distance = current_distance
                    best_move = (new_tx, new_ty)
        
        return best_move if best_move is not None else False

    def eval_move3(self):
        possible_moves = [
            (self.tx, self.ty + 1, 1, self.tx, self.ty+1, self.tx+1, self.ty+1),
            (self.tx + 1, self.ty, 1, self.tx+1, self.ty, self.tx+1, self.ty+1),
            (self.tx, self.ty - 1, 0.5, self.tx, self.ty, self.tx+1, self.ty),
            (self.tx - 1, self.ty, 0.5, self.tx, self.ty, self.tx, self.ty+1)
        ]
        
        best_move = None
        minimum_distance = inf
        
        for move in possible_moves:
            new_tx, new_ty, factor, wall1, wall2, wall3, wall4 = move
            if len(self.seen) > 0 and (new_tx, new_ty) not in self.dead.union(self.seen) and (
                    wall1, wall2, wall3, wall4) not in self.walls:
                current_distance = (self.path_cost * 3) + (
                        (new_tx**2 + new_ty**2) * factor)
                if current_distance < minimum_distance:
                    minimum_distance = current_distance
                    best_move = (new_tx, new_ty)

        return best_move if best_move is not None else False

    def eval_move4(self):
        possible_moves = [
            (self.tx, self.ty + 1, 1, self.tx, self.ty+1, self.tx+1, self.ty+1),
            (self.tx + 1, self.ty, 1, self.tx+1, self.ty, self.tx+1, self.ty+1),
            (self.tx, self.ty - 1, 0.5, self.tx, self.ty, self.tx+1, self.ty),
            (self.tx - 1, self.ty, 0.5, self.tx, self.ty, self.tx, self.ty+1)
        ]
        
        best_move = None
        minimum_distance = inf
        
        for move in possible_moves:
            new_tx, new_ty, factor, wall1, wall2, wall3, wall4 = move
            if len(self.seen) > 0 and (new_tx, new_ty) not in self.timed_dead_ends.union(self.seen).union(self.timed_walls) and (
                    wall1, wall2, wall3, wall4) not in self.walls:
                current_distance = (self.temp_cost * 3) + (
                        (new_tx**2 + new_ty**2) * factor)
                if current_distance < minimum_distance:
                    minimum_distance = current_distance
                    best_move = (new_tx, new_ty)
        
        return best_move if best_move is not None else False

    def actions(self):
        if len(self.plan) == 0:
            return
        if self.plan[END] != (self.tx,self.ty):
            return
        

        if self.wall_set_ago > 0:
            self.wall_set_ago -= 1
        self.seen |= {(self.tx,self.ty)}

        if(self.plan[END][0] == self.home_x) and (self.plan[END][1] == self.home_y):
            self.seen = {(self.tx,self.ty)}
            if self.home_x == 0:
                self.dead -= {(10,10)}
            else:
                self.dead -= {(0,0)}
            self.timed_dead_ends = set()
            self.timed_walls = set()
            self.temp_cost = 0
            self.temp_wall_placed = False


        if len(self.plan) > 2:
            self.block_enemy()
        if self.home_x == 0:
            if(self.plan[END][0] == 10) and (self.plan[END][1] == 10):
                self.update_deadend()
            if not self.temp_wall_placed:
                
                best_move = self.eval_move1()
                if best_move:
                    self.plan.append(best_move)
                else:
                    self.dead |= {(self.tx,self.ty)}
                    self.plan = self.plan[:-1]
                self.path_cost += 1


            if self.temp_wall_placed:
                
                best_move = self.eval_move2()
                if best_move:
                    self.plan.append(best_move)
                else:
                    self.timed_dead_ends |= {(self.tx,self.ty)}
                    self.plan = self.plan[:-1]
                self.temp_cost += 1


        if self.home_x == 10:
            if(self.plan[END][0] == 0) and (self.plan[END][1] == 0):
                self.update_deadend()
            if not self.temp_wall_placed:
                
                best_move = self.eval_move3()
                if best_move:
                    self.plan.append(best_move)
                else:
                    self.dead |= {(self.tx,self.ty)}
                    self.plan = self.plan[:-1]
                self.path_cost += 1


            if self.temp_wall_placed:
                
                best_move = self.eval_move4()
                if best_move:
                    self.plan.append(best_move)
                else:
                    self.timed_dead_ends |= {(self.tx,self.ty)}
                    self.plan = self.plan[:-1]
                self.temp_cost += 1
            

        print("toward {0} {1}".format(self.plan[END][0]+0.5, self.plan[END][1]+0.5), flush=True)
    
    def main(self):
        while True:
            self.read_input()
            self.actions()
            
            print("", flush=True)
            sleep(0.125)


bl = AstarBot()
bl.start_bot()
