import select
import sys
import time
from typing import List
import datetime
import logging
from pathlib import Path,PurePath
from queue import Queue 

# Uses Flood Fill, makes one walk to goal, picks the optimum path based on that,
# squishes the path and makes a run back and forth
# ~45 seconds for intial exploration to goal
# then on ~40 for back and forth run.

# decorator, logs the function call, input to the function
# @log_in_out
def log_in_out(func):

    def decorated_func(*args, **kwargs):
        saved_args = locals()
        logging.info("[LOG:] Entered the function {}".format(func.__name__))
        logging.info(
            "[LOG:] Details of function and the arguments passed: {}".format(saved_args))
        try:
            result = func(*args, **kwargs)
            logging.info(
                f"[LOG:] Leaving the function {format(func.__name__)}")
            return result
        except:
            raise

    return decorated_func

class CellTree:
    def __init__(self,cell):
        self.cell = cell
        self.children=[]
    
    def insert(self,child):
        self.children.append(child)


class Cell:
    def __init__(self, value,x,y):
        self.x = x
        self.y = y
        self.value = value
        self.visited = False
        self.dead = False
        self.top = False
        self.left = False
        self.right = False
        self.bottom = False
    
    def __str__(self):
        wall_str = ""
        # if self.left:
        #     wall_str+="|"
        # if self.top:
        #     wall_str+="--"
        if self.visited:
            wall_str += str(self.value).zfill(2) + "*"
        else:
            wall_str += str(self.value).zfill(2)
        # if self.bottom:
        #     wall_str+="__"
        # if self.right:
        #     wall_str+="|"
        return wall_str
    
    def update_value(self, val):
        self.value = val
    
class Maze:
    def __init__(self,W):
        self.W = W
        self.maze = []
        ref_vale = 2*W -2
        for row in range(W):
            self.maze.append([])
            for col in range(W):
                self.maze[row].append(Cell(ref_vale-(row+col), col, row))
        self.outer_walls()
        
    def get_cell(self,col,row):
        return self.maze[row][col]

        
    def update_value(self, col,row, value):
        self.maze[row][col].value = value

    def get_neighbours(self, col, row):
        bottom = self.get_cell(col, row+1) if row<10 else False
        right = self.get_cell(col+1, row) if col<10 else False
        left = self.get_cell(col-1, row) if col>0 else False
        top = self.get_cell(col, row-1) if row>0 else False
        return [x for x in (bottom, right, left, top) if (x and x.value!=0)]

    def outer_walls(self):
        for row in range(self.W):
            self.maze[row][0].left = True
            self.maze[row][self.W-1].right = True
        for col in range(self.W):
            self.maze[0][col].top = True
            self.maze[self.W-1][col].bottom =True

    def get_open_neighbours(self, col, row) -> List[Cell]:
        cell = self.maze[row][col]
        opn=[]
        logging.info(f"cell is {str(cell)}")
        if not cell.bottom:
            opn.append(self.get_cell(col,row+1))
        if not cell.right:
            opn.append(self.get_cell(col+1,row))
        if not cell.left:
            opn.append(self.get_cell(col-1,row))
        if not cell.top:
            opn.append(self.get_cell(col, row-1))
        logging.info(f"opn is {' '.join([f'{str(x)},{x.x}.{x.y}' for x in opn])}")
          
        return opn

    # Assumes the x,y point to a valid cell
    def min_dist(self, x, y):
        return sorted(self.get_open_neighbours(x,y), key=lambda p: p.value)[0].value

    def add_wall(self,is_vertical,col,row):
        if(is_vertical):
            if(col==self.W):
                self.maze[row][col-1].right=True
            elif(col==0):
                self.maze[row][col].left=True
            else:
                self.maze[row][col].left=True
                self.maze[row][col-1].right=True
        else:
            if(row==self.W):
                self.maze[row-1][col].bottom=True
            elif(row==0):
                self.maze[row][col].top=True
            else:
                self.maze[row][col].top=True
                self.maze[row-1][col].bottom=True
    
    def __str__(self):
        return "\n".join([" ".join([str(val) for val in row]) for row in self.maze])

class Robot:
    def __init__(self, home_tile, goal_tile):
        self.home = home_tile
        self.tx = home_tile[0]
        self.ty = home_tile[1]
        self.goal = goal_tile
    
class Game:
    def __init__(self):
        self.bot = Robot((0,0),(10,10))
        self.maze = Maze(11)
        self.walls = set()
    
    def __str__(self):
        return str(self.maze)
    
    def update_walls(self,wall_tup):
        if(wall_tup[0]==wall_tup[2]): # x is same, vertical line
            self.maze.add_wall(True,wall_tup[0],wall_tup[1])
        else:
            self.maze.add_wall(False,wall_tup[0],wall_tup[1])

    # start at the goal and start filling up the maze with M distance - given new walls
    def flood_maze(self):
        fill_stack = Queue()
        cell = self.maze.get_cell(self.bot.goal[0],self.bot.goal[1])
        seen_set = set()
        fill_stack.put(cell)
        count =0
        while(fill_stack.qsize()>0):
            cell = fill_stack.get()
            opn = self.maze.get_open_neighbours(cell.x, cell.y)
            seen_set.add(cell)
            for x in opn:
                if x not in seen_set:
                    count +=1
                    x.update_value(cell.value+1)
                    fill_stack.put(x)

    # updates the flood values, takes a cell to start at
    # not_used
    def mod_flood_maze(self,x,y):
        if((x,y) != self.bot.goal):
            fill_stack = []
            cell = self.maze.get_cell(x,y)
            fill_stack.append(cell)
            while(len(fill_stack)>0):
                cell = fill_stack.pop()
                # cell.visited=True
                md = self.maze.min_dist(cell.x,cell.y)
                if(md!=cell.value-1):
                    self.maze.update_value(cell.x, cell.y, md+1)
                    for n in self.maze.get_neighbours(cell.x,cell.y):
                        fill_stack.append(n)
    
    # generates the next tile to move based on the flood values
    # Looks at open neighbours, and picks the lowest one, B->R->L->T
    def next_move(self):
        return sorted(self.maze.get_open_neighbours(self.bot.tx,self.bot.ty), key=lambda x: x.value)[0]

    def createtree(self, tree):
        cell = tree.cell
        children = list(filter(lambda x: x.value==cell.value+1,self.maze.get_open_neighbours(cell.x, cell.y)))
        for child in children:
            child = CellTree(child)
            self.createtree(child)
            tree.children.append(child)
        return tree
    
    #  does a dfs of the tree, and returns the tree paths that reach 0,0 as lists
    def getbestpath(self, tree):
        b_paths=[]
        if tree.cell.x==0 and tree.cell.y==0:
            return [[(tree.cell.x,tree.cell.y)]]
        for child in tree.children:
            b_path = self.getbestpath(child)
            if(b_path):
                for path in b_path:
                    path.append((tree.cell.x,tree.cell.y))
                    b_paths.append(path)
        return b_paths
            
        

    # Once the final position is reached, we look at the maze-values and follow the path good tiles and make instruction set out of it.
    def extract_path(self):
        tree = self.createtree(CellTree(self.maze.get_cell(self.bot.goal[0],self.bot.goal[1])))
        b_paths = self.getbestpath(tree)
        return sorted(b_paths,key=lambda x: len(x))[0]

    def path_squishing(self,opt_path):
        i=0
        while i<len(opt_path)-2:
            if(opt_path[i][0]==opt_path[i+2][0]):
                opt_path = opt_path[:i+1]+[opt_path[i+2]]+opt_path[i+3:]
            elif(opt_path[i][1]==opt_path[i+2][1]):
                opt_path = opt_path[:i+1]+[opt_path[i+2]]+opt_path[i+3:]
            else:
                i+=1
        return opt_path

    def backandforth(self,opt_path):
        sign=1
        count =len(opt_path)-1
        while True:
            new_tile,new_walls = self.sense()
            if(self.bot.tx==opt_path[count][0] and self.bot.ty==opt_path[count][1]):
                if(self.bot.tx==0 and self.bot.ty==0):
                    sign = 1
                elif(self.bot.tx==self.bot.goal[0] and self.bot.ty==self.bot.goal[1]):
                    sign =-1
                count = count+sign
                print(f"toward {opt_path[count][0]+0.5} {opt_path[count][1]+0.5}",flush=True)
            print("",flush=True)
            time.sleep(0.125)


    # the game logic loop
    def play_loop(self):
        time.sleep(0.25)
        prev_move = (self.bot.tx, self.bot.ty)
        while True:
            new_tile,new_walls = self.sense() # new_tile, makes us send commands, only after initial loc is received.
            if((self.bot.tx, self.bot.ty) == self.bot.goal):
                opt_path = self.extract_path()
                opt_path = self.path_squishing(opt_path)
                self.backandforth(opt_path)
            if((self.bot.tx, self.bot.ty) == prev_move and new_tile):
                self.flood_maze()
                move = self.next_move()
                prev_move=(move.x,move.y)
                logging.info(f"The maze is \n {str(self.maze)}")
                print(f"toward {move.x+0.5} {move.y+0.5}",flush=True)
            print("",flush=True)
            time.sleep(0.125)
    
    # simulation, to do simple testing stuff, without using the server
    def sim_loop(self):
        with open("mazepool/0.maze","r") as f:
            lines = f.readlines()
        for line in lines:
            wall = [int(x) for x in line.split()[1:]]
            game.update_walls(wall)
        count=0
        while ((self.bot.tx,self.bot.ty) != self.bot.goal):
            self.flood_maze()
            move = self.next_move()
            move.visited=True
            self.bot.tx, self.bot.ty = move.x, move.y
            print(self.maze)
            count += 1
            print(f"-----------------------{count}---------------------------------")
            print(f"The (tx,ty) is ({self.bot.tx},{self.bot.ty})")
        if((self.bot.tx, self.bot.ty) == self.bot.goal):
            opt_path = self.extract_path()
            print(opt_path)
            self.backandforth(opt_path)

    # takes sense data and makes calls to update and flood the maze
    def sense(self):
        new_tile = False
        new_walls = False
        while select.select([sys.stdin,],[],[],0.0)[0]:
        # read and process the next 1-line observation
            obs = sys.stdin.readline()
            obs = obs.split(" ")
            if obs == []: pass
            elif obs[0] == "bot":
                new_tile = True
                x = float(obs[1])
                y = float(obs[2])
                if ((int(x) != self.bot.tx or int(y) != self.bot.ty) and
                    ((x-(int(x)+0.5))**2 + (y-(int(y)+0.5))**2)**0.5 < 0.2):
                    self.bot.tx = int(x)
                    self.bot.ty = int(y)
            elif obs[0] == "wall":
                x0 = int(float(obs[1]))
                y0 = int(float(obs[2]))
                x1 = int(float(obs[3]))
                y1 = int(float(obs[4]))
                wall = (x0, y0, x1, y1)
                if wall not in self.walls:
                    self.walls |= {wall}
                    self.update_walls((x0,y0,x1,y1))
                    new_walls = True
        return new_tile,new_walls

if __name__ == "__main__":
    pd_date = datetime.datetime.now().strftime('%Y-%m-%d-%I-%M-%S')
    logfile = "LogScriptProcess-" + pd_date + ".log"
    log_file_path = PurePath(Path.cwd(), "log", str(logfile))
    logging.basicConfig(handlers=[logging.FileHandler(PurePath(Path.cwd(), "log", str(logfile)), 'a', 'utf-8')],
                        level=logging.ERROR,
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info("--------------------------------------x---------------------------------------------")
    game = Game()
    # game.sim_loop()
    game.play_loop()