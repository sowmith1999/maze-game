
import sys, select, time, random, queue, copy
import re

def l2(xi, yi, xf, yf):
  return ((xi - xf)**2 + (yi - yf)**2)**0.5

def l1(xi, yi, xf, yf):
  return(abs(xi - xf) + abs(yi - yf))


class Robot:

    def __init__(self, x, y):
        # store robot position
        self.x = x
        self.y = y    

    def __eq__(self, other):  # TODO: not sure if this is all that should be compared
        return self.x == other.x and self.y == other.y   

    def __str__(self):
        return f"robot pos: ({self.x},{self.y})" 
    
    def __hash__(self):
        h = 0  # TODO: clean this up
        h*= 3
        h ^= hash(self.robot.x)
        h*= 3
        h ^= hash(self.robot.y)
        return h

    # TODO: should this be direction? (and then change robot positin within method) - currently handling in Maze
    def move(self, x, y):  
        self.x = x
        self.y = y   

    def update_pos(self, x, y):
        self.move(x,y)

    def get_pos(self):
        return self.x, self.y

    def actions(self, walls): 
        a = frozenset()
        x, y = int(self.x), int(self.y)

        #down
        if ((x, y+1, x+1, y+1) not in walls): # len(seen) > 0 and   and ((lx,ly+1) not in dead|seen) 
            a |= {"D"}
        if (x+1, y, x+1, y+1) not in walls:   # len(seen) > 0 and   and ((lx+1,ly) not in dead|seen)
            a |= {"R"}
        # up
        if (x, y, x+1, y) not in walls:       # len(seen) > 0 and   and ((lx,ly-1) not in dead|seen)
            a |= {"U"}
        #left 
        if ((x, y, x, y+1) not in walls):     # len(seen) > 0 and   and ((lx-1,ly) not in dead|seen)    and \
            a |= {"L"}
        
        return a    
    
    
class Maze:

    def __init__(self, x, y, goal_x, goal_y, walls) -> None:
        self.robot = Robot(x,y)

        self.goal_x = goal_x
        self.goal_y = goal_y

        self.h = l1(self.robot.x, self.robot.y, goal_x, goal_y)  # TODO: is this used?

        # store wall positions
        self.walls = copy.deepcopy(walls) 
        
    def __lt__(self, other):  # TODO: nto sure if this is correct
        return self.h < other.h

    def __eq__(self, other):
        # return self.x == other.x and self.y == other.y

        # for wall in self.walls:
        #     if wall[0] != wall[0]: return False

        # TODO: test goal check
        if self.goal_x != other.goal_x or self.goal_y != other.goal_y:
            return False

        return self.robot == other.robot  # TODO: should compare walls?
    
    def __hash__(self):
        h = 0
        for wall in self.walls:   # was commented out
                h*= 3
                h ^= hash(wall[0])
                h*= 3
                h ^= hash(wall[1])

        h*= 3
        h ^= hash(self.robot.x)
        h*= 3
        h ^= hash(self.robot.y)

        h*= 3
        h ^= hash(self.goal_x)
        h*= 3
        h ^= hash(self.goal_y)

        return h
       
    def get_robo_pos(self):
        return (self.robot.x, self.robot.y)

    def update_walls(self, new_walls):
        self.walls = copy.deepcopy(new_walls).union(self.walls)
    
    # def update_goal(self, goal, goal_x, goal_y):
    #     self.goal_x = goal_x
    #     self.goal_y = goal_y

    #     self.h = l1(self.robot.x, self.robot.y, goal_x, goal_y)

    def at_goal(self):  # TODO: is this too exact of a position check, does it need a range?
        if self.robot.x == self.goal_x and self.robot.y == self.goal_y:
            return True
        else:
            return False
    
    # return new maze resulting from action
    def step(self, action):  
        assert(action is not None)
        
        new_maze = copy.deepcopy(self)
        x,y = new_maze.robot.x, new_maze.robot.y
        
        # TODO: should moving the robot be within robot?
        #       could be done in the robot move method

        if action == "D":    # (tx,ty+1)  # move down
            new_maze.robot.move(x, y+1)
        elif action == "R":  # (tx+1,ty)  # move right
            new_maze.robot.move(x+1, y)
        elif action == "U":  # (tx,ty-1)  # move up
            new_maze.robot.move(x, y-1)
        elif action == "L":  # (tx-1,ty)  # move left
            new_maze.robot.move(x-1, y)

        return new_maze

    def actions(self):
        # TODO: what if actions returned is empty?
        return self.robot.actions(self.walls)  
        
        

class State:
  
    def __init__(self, maze, moves, pathcost):
        self.maze = maze
        self.moves = moves
        self.path_cost = pathcost
    
    def __eq__(self, other):
        # if len(self.moves) != len(other.moves): return False

        # for i in range(len(self.moves)):
        #     if self.moves[i] != other.moves[i]: return False

        return self.maze == other.maze # and self.path_cost == other.path_cost
    
    def __hash__(self):
        # TODO: appropriate hash function  ? base on moves?

        h = 0
        for i in range(len(self.moves)):
            h *= 3
            h ^= hash(self.moves[i][0])
            h *= 3
            h ^= hash(self.moves[i][1])
        # return h ^ hash(self.maze) ^ hash(self.path_cost)
        return hash(self.maze) # TODO: this might need to be just the robot location?

    def __lt__(self, other):
        return self.eval() < other.eval()
    
    def get_moves(self):
        return self.moves
    
    def step(self, act):    # TODO: should moves, store direction or position or both?
        
        x,y = self.maze.robot.x, self.maze.robot.y   #TODO: test working correctly

        if act == "D":    # (tx,ty+1)  # move down
            move = (x, y+1)
        elif act == "R":  # (tx+1,ty)  # move right
            move = (x+1, y)
        elif act == "U":  # (tx,ty-1)  # move up
            move = (x, y-1)
        elif act == "L":  # (tx-1,ty)  # move left
            move = (x-1, y)
        
        return State(self.maze.step(act),self.moves+[move],self.path_cost+1) # self.moves+[act]
        
    def successors(self):
        successors_set = frozenset({})
        actions = self.maze.actions() # get possible actions
        # print(actions) # debug

        # create a new successor state for every possible action
        for act in actions:
            successors_set |= {self.step(act)}
        return successors_set

    def at_goal(self):
        # goal is specifieed in maze intialized with
        return self.maze.at_goal()   # TODO verify no exceptions to this

    def eval(self):
        
        x1, y1 = self.maze.get_robo_pos()
        x2 = self.maze.goal_x
        y2 = self.maze.goal_y

        heu = l1(x1,y1,x2,y2)

        return self.path_cost + heu


class ASTAR:

    def __init__(self, start_maze):
        
        self.frontier = queue.PriorityQueue()
        self.astar_seen = set()

        # shifts robot position to center of tile for astar calculation
        x,y = start_maze.robot.get_pos()
        start_maze.robot.update_pos(int(x)+0.5, int(y)+0.5)

        #  startx, starty, goalx, goaly included in starting board
        self.start = State(start_maze, [], 0) # TODO: testing [(0.5,0.5)] instead of [], 

        self.frontier.put(self.start)

        self.goal_state = None

    def __str__(self) -> str:
        
        if self.goal_state is None:
            return "An end state was either not found or evaluated"
        
        moves = list(self.goal_state.moves)

        move_string = ''
        for move in moves:
            entry = ''.join(('(',str(move[0]),',', str(move[1]),') '))
            move_string = ''.join([move_string, entry])

        return move_string  # ' '.join(self.goal_state.moves) 

    def run(self):

        # init takes care of intial setup

        while self.frontier:
            if self.frontier.empty(): return None
            state = self.frontier.get()

            if state.at_goal(): 
                self.goal_state = state
                return state.get_moves()        # what should normally be returned 

            sucessors = state.successors()      # find sucessors 
            for suc in sucessors:               # add unseen sucessors to frontier
                if state in self.astar_seen:    # don't add seen nodes to frontier
                    continue            
                self.frontier.put(suc)       
            
            self.astar_seen.add(state) 

        return None  # only returns None if gets stuck and no solution
    
def load_walls(filename):

    # set of known walls 
    maze_walls = set()
    for i in range(0,11):
        maze_walls |= {(i,0,i+1,0), (i,11,i+1,11), (0,i,0,i+1), (11,i,11,i+1)}
    
    # load walls from maze
    pattern = re.compile(r"\w\w\w\w (?P<x1>\d+) (?P<y1>\d+) (?P<x2>\d+) (?P<y2>\d+)")
    with open (filename) as maze_in:
        for line in maze_in:
            line = line.rstrip('\r\n')

            m = pattern.search(line)
            x1,y1,x2,y2 = m.group('x1'), m.group('y1'), m.group('x2'), m.group('y2')
            # print(f"{x1} {y1} {x2} {y2}")

            maze_walls |= {(int(x1),int(y1),int(x2),int(y2))}
    # print()
    return maze_walls

# helper functions
def print_cmd_line(obs, bot=True, walls=True,ebwb=False,empty=False):

    # see only bot
    if len(obs) <= 1:  # skips empty outputs by checking len(obs) > 1
        pass
    # print bot
    elif bot == True and obs[0:3] == 'bot':         
        print(f"comment bot == {obs}", flush=True)
    # print walls
    elif walls == True and obs[0:4] == 'wall':      
        print(f"comment bot == {obs}", flush=True)
    # print everything else
    elif ebwb == True and len(obs) > 1 and obs[0:4] != 'wall' and \
        obs[0:3] != 'bot':
        print(f"comment bot == {obs}", flush=True)  

    # # see everything but walls using regualar expressions
    # pattern = re.compile(r'wall')
    # if not pattern.search(obs) and len(obs)>1:
    #     print(f"comment obs == {obs}", flush=True)