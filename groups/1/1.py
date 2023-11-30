import copy
import math
import queue
import random
import select
import sys
import time
from timeit import default_timer as timer

PATHS_BEFORE_DTP = 2

class Bot:
    def __init__(self, W):
        # Bot knows the width of the maze  
        self.W = W
        self.goalTile = self.W - 1
        
        self.last_move_time = timer()

        # last tile "reached" (i.e., being close enough to center)
        self.tile_x = 0
        self.tile_y = 0

        self.pathcost = 0
        self.coinCount = 0
        
        self.seen = set()
        self.dead = set()
        self.walls = set()
        self.coins = set()
        self.paths = []
        self.numPaths = 0
        
        for i in range(0, 11):
            self.walls |= {(i, 0, i + 1, 0), (i, 11, i + 1, 11), (0, i, 0, i + 1), (11, i, 11, i + 1)}

        # We keep a list of valid moves to backtrack
        self.moves = []

        self.minPath = []
        self.minPathIndx = 0
        self.searching = True

        self.centerAttempt = 0

    def currentTile(self):
        return (self.tile_x, self.tile_y)

    def goal(self):
        return self.tile_x == self.goalTile and self.tile_y == self.goalTile

    def changeGoal(self):
        if self.goalTile == self.W - 1: self.goalTile = 0
        else: self.goalTile = self.W - 1
        return
    
    def centerSelf(self,):
        self.centerAttempt += 1
        print(f"comment inside centerSelf:",flush=True)
        print("toward %s %s" % (self.currentTile()[0]+0.5,self.currentTile()[1]+0.5), flush=True)

        # print("toward %s %s" % (self.tile_x+0.5,self.tile_y+0.5), flush=True)
        time.sleep(0.1)
        # print("toward %s %s" % (self.minPath[self.minPathIndx]), flush=True)
        self.last_move_time = timer()

    def cacheMoves(self):
        if len(self.moves) > 2:
            if abs(self.moves[0][0] - self.moves[1][0]) > 1:
                self.moves.remove(self.moves[0])
                self.pathcost -= 1
            moves = (self.moves).copy()
            if [moves, self.pathcost, 0] not in self.paths and [moves[::-1], self.pathcost, 0] and [moves[::-1], self.pathcost, self.W-1] and [moves, self.pathcost, self.W-1] not in self.paths:
                self.paths.append([moves, self.pathcost, self.goalTile])
                print(f"comment added path to self.path: {moves}")
            else: print("comment ############### REMOVED DUPLICATE FROM SELF.PATH ###############", flush=True)
            # print(f"comment self.paths: {self.paths}")
            self.pathcost = 0
            self.numPaths += 1
            self.moves.clear()
            self.seen.clear()
            frontier.queue.clear()
        # print(f"comment self.paths after clear: {self.paths}")
        return

    def step(self, new_tile):

        self.tile_x = new_tile[0]
        self.tile_y = new_tile[1]
        if not (self.tile_x==new_tile[0]) and not (self.tile_y==new_tile[1]): self.pathcost += 1
        self.centerAttempt = 0
        if new_tile in self.coins:
            # print(f"comment coins before: {self.coins}")
            self.coins = self.coins.difference({new_tile})
            # print(f"comment coins after: {self.coins}")
        self.last_move_time = timer()

    def checkMove(self, dir):
        assert dir in ["R", "L", "U", "D", "RD", "RU", "LD", "LU"], "Invalid direction given"

        if dir == "D":
            x = self.tile_x
            y = self.tile_y + 1
            wall_x1 = self.tile_x
            wall_y1 = self.tile_y + 1
            wall_x2 = self.tile_x + 1
            wall_y2 = self.tile_y + 1
        elif dir == "R":
            x = self.tile_x + 1
            y = self.tile_y 
            wall_x1 = self.tile_x + 1
            wall_y1 = self.tile_y 
            wall_x2 = self.tile_x + 1
            wall_y2 = self.tile_y + 1
        elif dir == "L":
            x = self.tile_x - 1
            y = self.tile_y 
            wall_x1 = self.tile_x
            wall_y1 = self.tile_y 
            wall_x2 = self.tile_x 
            wall_y2 = self.tile_y + 1
        elif dir == "U":
            x = self.tile_x 
            y = self.tile_y -1 
            wall_x1 = self.tile_x
            wall_y1 = self.tile_y 
            wall_x2 = self.tile_x + 1
            wall_y2 = self.tile_y

        elif dir == "RD":
            x = self.tile_x + 1
            y = self.tile_y + 1
            wall1 = (self.tile_x, self.tile_y+1, self.tile_x+1, self.tile_y+1)
            wall2 = (self.tile_x+1, self.tile_y+1, self.tile_x+2, self.tile_y+1)
            wall3 = (self.tile_x+1, self.tile_y, self.tile_x+1, self.tile_y+1)
            wall4 = (self.tile_x+1, self.tile_y+1, self.tile_x+1, self.tile_y+2)
        elif dir == "RU":
            x = self.tile_x + 1
            y = self.tile_y - 1
            wall1 = (self.tile_x, self.tile_y, self.tile_x+1, self.tile_y)
            wall2 = (self.tile_x+1, self.tile_y, self.tile_x+2, self.tile_y)
            wall3 = (self.tile_x+1, self.tile_y, self.tile_x+1, self.tile_y+1)
            wall4 = (self.tile_x+1, self.tile_y-1, self.tile_x+1, self.tile_y)
        elif dir == "LD":
            x = self.tile_x - 1
            y = self.tile_y + 1
            wall1 = (self.tile_x, self.tile_y+1, self.tile_x+1, self.tile_y+1)
            wall2 = (self.tile_x-1, self.tile_y+1, self.tile_x, self.tile_y+1)
            wall3 = (self.tile_x, self.tile_y, self.tile_x, self.tile_y+1) 
            wall4 =(self.tile_x, self.tile_y+1, self.tile_x, self.tile_y+2)
        else:
            x = self.tile_x - 1
            y = self.tile_y - 1
            wall1 = (self.tile_x, self.tile_y, self.tile_x+1, self.tile_y) 
            wall2 = (self.tile_x-1, self.tile_y, self.tile_x, self.tile_y)
            wall3 = (self.tile_x, self.tile_y, self.tile_x, self.tile_y+1)
            wall4 = (self.tile_x, self.tile_y-1, self.tile_x, self.tile_y)


        if dir in ["R", "L", "U", "D"]:
            return (x, y) not in self.dead|self.seen and (wall_x1, wall_y1, wall_x2, wall_y2) not in self.walls
        else:
            return (x,y) not in self.dead|self.seen and wall1 not in self.walls and wall2 not in self.walls and wall3 not in self.walls and wall4 not in self.walls

    # def slowDownForTurn(self, actions):
    #     slowed_actions = []

    #     for i in range(1,len(actions) - 1):
    #         prev_x, prev_y = actions[i-1]
    #         current_x, current_y = actions[i]
    #         next_x, next_y = actions[i + 1]

    #         # check if the bot is making a turn @ CURRENT
    #         dx = next_x - prev_x
    #         dy = next_y - prev_y
    #         is_turn = (dx != 0 and dy != 0)


    #         if is_turn:
    #             slowdown_moves = 3
    #             slowdown_distance = 0.10

    #             for j in range(slowdown_moves,0,-1):
    #                 slowed_x = current_x - (j + 1) * (current_x - prev_x) / (slowdown_moves + 1) * slowdown_distance
    #                 slowed_y = current_y - (j + 1) * (current_y - prev_y) / (slowdown_moves + 1) * slowdown_distance
    #                 slowed_actions.append((slowed_x, slowed_y))
    
    #             slowed_actions.append((current_x, current_y))

    #     slowed_actions.append(actions[-1])
    #     print(f"comment slowed actions: {slowed_actions}",flush=True)

    #     return slowed_actions

    def actions(self):
        actions = []
        # MOVEMENT
        rand = random.uniform(0, 1)
        if self.goalTile == self.W - 1:
            if rand < 0.5:
                # Move Down
                if self.checkMove("D"):
                    actions.append((self.tile_x, self.tile_y + 1))
                # Move Right
                if self.checkMove("R"):
                    actions.append((self.tile_x + 1, self.tile_y))
                # Move Left
                if self.checkMove("L"):
                    actions.append((self.tile_x - 1, self.tile_y))
                # Move Up
                if self.checkMove("U"):
                    actions.append((self.tile_x, self.tile_y - 1))
                # diagonal right down
                if self.checkMove("RD"):
                    actions.append((self.tile_x + 1, self.tile_y + 1)) 
                # diagonal right up
                if self.checkMove("RU"):
                    actions.append((self.tile_x+1, self.tile_y-1)) 
                # diagonal left down
                if self.checkMove("LD"):
                    actions.append((self.tile_x-1, self.tile_y+1)) 
                # diagonal left up
                if self.checkMove("LU"):
                    actions.append((self.tile_x-1, self.tile_y-1))
                
            else:
                # Move Right
                if self.checkMove("R"):
                    actions.append((self.tile_x + 1, self.tile_y))
                # Move Down
                if self.checkMove("D"):
                    actions.append((self.tile_x, self.tile_y + 1))
                # Move Up
                if self.checkMove("U"):
                    actions.append((self.tile_x, self.tile_y - 1))
                # Move Left
                if self.checkMove("L"):
                    actions.append((self.tile_x - 1, self.tile_y))
                # right down
                if self.checkMove("RD"):
                    actions.append((self.tile_x + 1, self.tile_y + 1)) 
                # left down
                if self.checkMove("LD"):
                    actions.append((self.tile_x-1, self.tile_y+1)) 
                # right up
                if self.checkMove("RU"):
                    actions.append((self.tile_x+1, self.tile_y-1)) 
                # left up
                if self.checkMove("LU"):
                    actions.append((self.tile_x-1, self.tile_y-1))
        else:
            if rand < 0.5:
                # Move Up
                if self.checkMove("U"):
                    actions.append((self.tile_x, self.tile_y - 1))
                # Move Left
                if self.checkMove("L"):
                    actions.append((self.tile_x - 1, self.tile_y))
                # Move Right
                if self.checkMove("R"):
                    actions.append((self.tile_x + 1, self.tile_y))
                # Move Down
                if self.checkMove("D"):
                    actions.append((self.tile_x, self.tile_y + 1))
                # right down
                if self.checkMove("RD"):
                    actions.append((self.tile_x + 1, self.tile_y + 1)) 
                # right up
                if self.checkMove("RU"):
                    actions.append((self.tile_x+1, self.tile_y-1))
                # left down 
                if self.checkMove("LD"):
                    actions.append((self.tile_x-1, self.tile_y+1)) 
                # left up
                if self.checkMove("LU"):
                    actions.append((self.tile_x-1, self.tile_y-1))
                
            else:
                # Move Left
                if self.checkMove("L"):
                    actions.append((self.tile_x - 1, self.tile_y))
                # Move Up
                if self.checkMove("U"):
                    actions.append((self.tile_x, self.tile_y - 1))
                # Move Down
                if self.checkMove("D"):
                    actions.append((self.tile_x, self.tile_y + 1))
                # Move Right
                if self.checkMove("R"):
                    actions.append((self.tile_x + 1, self.tile_y))
                # right down
                if self.checkMove("RD"):
                    actions.append((self.tile_x + 1, self.tile_y + 1)) 
                # right up
                if self.checkMove("RU"):
                    actions.append((self.tile_x+1, self.tile_y-1)) 
                # left up
                if self.checkMove("LU"):
                    actions.append((self.tile_x-1, self.tile_y-1))
                #left down
                if self.checkMove("LD"):
                    actions.append((self.tile_x-1, self.tile_y+1))

        return actions
    
    def successors(self):
        successors = []

        for move in self.actions():
            new_bot = copy.deepcopy(self)
            # print(f"comment new bot curr tile: {new_bot.currentTile()}", flush=True)
            new_bot.seen |= {new_bot.currentTile()}
            # print(f"comment newbot move: {move} | move.actions before move: {new_bot.actions()}", flush=True)
            new_bot.step(move)
            actions_after_move = new_bot.actions()
            # print(f"comment newbot move: {move} | move.actions after move: {actions_after_move} | is goal? {new_bot.goal()}", flush=True)

            if new_bot.goal():
                successors.append(new_bot.currentTile())
                return frozenset(successors)

            if (len(actions_after_move) > 0 and move not in new_bot.seen|new_bot.dead):

                for action in actions_after_move:
                    new_bot2 = copy.deepcopy(new_bot)
                    # print(f"comment new bot 2 curr tile: {new_bot2.currentTile()}", flush=True)
                    new_bot2.seen |= {new_bot2.currentTile()}
                    # print(f"comment newbot 2 move: {action} | move.actions before move: {new_bot2.actions()}", flush=True)
                    new_bot2.step(action)
                    actions_after_move2 = new_bot2.actions()
                    # print(f"comment newbot 2 move: {action} | move.actions after move: {actions_after_move2}", flush=True)

                    if new_bot2.goal():
                        # print(f"comment RETURNING move: {new_bot.currentTile()}", flush=True)

                        # if already on same x or y, run straight to flag
                        if (self.tile_x == self.goalTile) or (self.tile_y == self.goalTile):
                            successors.append((self.goalTile,self.goalTile))
                            return frozenset(successors)                        
                        else:
                            successors.append(new_bot.currentTile())
                            return frozenset(successors)
                    
                    if (len(actions_after_move2) > 0 and action not in new_bot2.seen|new_bot2.dead):
                        successors.append(move)
                    elif action not in self.seen|self.dead and action not in [(0,0),(10,10)] and move not in [(0,0),(10,10)]:
                        print(f"comment removing lvl 2 dead-move: {action}", flush=True)
                        new_bot.dead |= {new_bot2.currentTile()}
                        self.dead |= {new_bot2.currentTile()}


            else:
                print(f"comment removing dead-move: {move}", flush=True)
                self.dead |= {new_bot.currentTile()} 

        # cannot advance, backtrack
        if len(successors) == 0:
            print(f"comment removing dead tile during backtracking: {self.currentTile()} ")
            self.dead |= {self.currentTile()}

            # get rid of the blocking move
            self.moves = self.moves[:-1]
            
            self.pathcost -= 2

            # go back to the last valid tile
            if self.moves != []: successors.append(self.moves[-1])
            elif self.moves ==[]:
                print(f"comment issue")
                tile = abs(self.goalTile-10)
                successors.append((tile,tile))

        # print(f"comment returning successors: {set(successors)}", flush=True)
        return frozenset(successors)

    def eval(self, new_tile):
        x = new_tile[0]
        y = new_tile[1]

        euclid = math.sqrt((abs(self.goalTile - x)**2) + (abs(self.goalTile - y)**2))
        # manhat = abs(self.goalTile - x) + abs(self.goalTile - y)

        # h_cost = (manhat+euclid)/2
        # print(f"comment tile ({x}, {y}), h-cost {h_cost}", flush=True)

        if new_tile in self.coins:
            # print(f"comment eval reduced for tile {new_tile}",flush=True)
            return self.pathcost + max(euclid - 1, 1)
        else:
            return self.pathcost + euclid

    ############ take pre-determined best route ###########
    def deterministicPath(self):
        actions = []

        # init min cost, location in list of paths, and path itself
        self.minPathIndx = 0
        minCost = float('inf')
        minIndex = 0
        minPath = []

        for i in range(self.numPaths):
            if self.paths[i][1] < minCost and len(self.paths[i][0]) > self.W-1:
                minCost = self.paths[i][1] # !!
                minIndex = i
                minPath = self.paths[i][0]
            print(f"comment minPath in dPath: {minPath}",flush=True)
        
        # need path in correct orientation (either 0,0 to 10,10 or vice versa)
        if self.goalTile == self.paths[minIndex][2]:
            print(f"comment front-facing")
            actions = minPath

            if actions[-1] != (self.goalTile, self.goalTile):
                print("comment  ############### appending goal tile ###############", flush=True)
                actions.append((self.goalTile, self.goalTile))
            
            if actions[0] == (self.tile_x, self.tile_y):
                print(f"comment ############### removing first tile ###############", flush=True)
                actions = actions[1:] # already at first tile
            
            # slowedActions = self.slowDown(actions)

            # print(f"comment actions: {actions} vs. slowed: {slowedActions}")

            return actions
        else:
            print(f"comment reverse-facing")
            actions = minPath[::-1]
            if actions[-1] != (self.goalTile, self.goalTile):
                print("comment  ############### appending goal tile ###############", flush=True)
                actions.append((self.goalTile, self.goalTile))

            if actions[0] == (self.tile_x, self.tile_y):
                print(f"comment ############### removing first tile ###############", flush=True)
                actions = actions[1:] # already at first tile

            # slowedActions = self.slowDown(actions)

            # print(f"comment actions: {actions} vs. slowed: {slowedActions}")

            return actions
    #######################################################

    def condensePath(self,path):

        # init moves
        moves = path
        if len(moves) < 3:
            return moves

        # retain first move 
        condensed_moves = [moves[0]]
        prev_direction = (moves[1][0] - moves[0][0], moves[1][1] - moves[0][1])

        # iterate moves, condense same slope into one 
        for i in range(1, len(moves) - 1):
            current_direction = (moves[i + 1][0] - moves[i][0], moves[i + 1][1] - moves[i][1])

            if current_direction != prev_direction:
                condensed_moves.append(moves[i])
                prev_direction = current_direction

        condensed_moves.append(moves[-1])
        self.minPath = condensed_moves
    
        return self.minPath

    def swapToSearch(self):
        print("toward %s %s" % (self.currentTile()[0]+0.5,self.currentTile()[1]+0.5), flush=True)
        # print("toward %s %s" % (self.minPath[self.minPathIndx][0]+0.5,self.minPath[self.minPathIndx][1]+0.5), flush=True)
        self.searching = True
        self.moves = self.minPath[:self.minPathIndx:]
        self.pathcost = len(self.moves)
        self.step(self.currentTile())
        print(f"comment bot moves[] after swapping: {self.moves} | pathcost: {self.pathcost}",flush=True)
        for successor in bot.successors():
            # if successor not in self.moves and successor not in self.dead:
            frontier.put((self.eval(successor),successor))
        self.last_move_time = timer()

            
# Setup bot
bot = Bot(11)

# Setup A*
frontier = queue.PriorityQueue()
for successor in bot.successors():
    # print(f"comment successor: {successor}")
    frontier.put((bot.eval(successor), successor))

frontier.get()
if random.uniform(0,1) > 0.5:
    dq = frontier.get()[1]
    frontier.put((bot.eval(dq)+1,dq))

# Wait a few seconds for some initial sense data
print("himynameis Icarus-Bot", flush=True)
# time.sleep(0.25)

init = True

while True:

    # while there is new input on stdin:
    while select.select([sys.stdin,],[],[],0.0)[0]:

        _timeDif = timer() - bot.last_move_time         # 8 for pc 15 for laptop?
        # read and process the next 1-line observation
        obs = sys.stdin.readline()
        # print(f"comment obs {obs}")
        obs = obs.split(" ")
        # print(f"comment obs {obs}")
        # print("comment obs: %s" % obs, flush=True)
        if obs == []:
            pass
    
        elif obs[0] == "bot":
            if init:
                init = False
                continue
            
            x = float(obs[1])
            y = float(obs[2])
            bot.coinCount = int(obs[3])
            # update our own position
            # bot.tile_x = x
            # bot.tile_y = y
            # print("comment now at: %s %s" % (x,y), flush=True)
            # print('comment Queue: %s' % frontier.queue, flush=True)
            if bot.searching:
                if _timeDif > 20 and (frontier.qsize()!=0):
                    print(f"comment searching timeDIF: {_timeDif} seconds, trying next move",flush=True)
                    move = bot.successors()[1] # isn't corrrect but not fixing yet
                    print("toward %s %s" % (move[0]+0.5,move[1]+0.5), flush=True)
                    bot.last_move_time = timer()
                elif _timeDif > 20 and (bot.currentTile()==(int(x),int(y))):
                    print(f"comment inside same tile, adding successors to queue")
                    frontier.queue.clear()
                    for successor in bot.successors():
                        # print(f"comment successor: {successor}")
                        frontier.put((bot.eval(successor), successor))
                    bot.last_move_time = timer()
                    
                elif _timeDif > 20 and (frontier.qsize()==0):
                    print(f"comment searching timeDIF: {_timeDif} seconds, trying freeze move",flush=True)
                    # if bot.currentTile() != bot.moves[-1]: print("toward %s %s" % (bot.moves[-1][0]+0.5,bot.moves[-1][1]+0.5), flush=True)
                    # else: bot.centerSelf()
                    print("toward %s %s" % (x,y), flush=True)
                    time.sleep(0.25)
                    
                    if bot.currentTile() in [(0,0),(10,10)]:
                        frontier.queue.clear()
                        for successor in bot.successors():
                            # print(f"comment successor: {successor}")
                            frontier.put((bot.eval(successor), successor))
                    bot.last_move_time = timer()

            # update our latest tile reached once we are firmly on the inside of the tile
            if ((int(x) != bot.tile_x or int(y) != bot.tile_y) and
                ((x-(int(x)+0.5))**2 + (y-(int(y)+0.5))**2)**0.5 < 0.2):
                bot.tile_x = int(x)
                bot.tile_y = int(y)
                currentTile = (int(x), int(y))
                bot.step(currentTile)
                  
                if bot.goal():
                    if bot.goalTile == 10: print("comment Reached the flag! Congrats!", flush=True)
                    if bot.goalTile == 0: print("comment Captured the flag! Congrats!", flush=True)
                    frontier.queue.clear()
                    bot.cacheMoves()
                    bot.changeGoal()
                    print("comment New goal: %s" % bot.goalTile, flush=True)

                    
                    if bot.numPaths >= PATHS_BEFORE_DTP:
                        dPath = bot.deterministicPath()
                        frontier.queue.clear()
                        print(f"comment adding dpath: {dPath}", flush=True)
                        bot.searching = False
                        condensedPath = bot.condensePath(dPath)
                        print(f"comment condensed minPath: {condensedPath}", flush=True)
                        bot.minPath = condensedPath

                if bot.searching:
                    # remove 0,0 tile if starting on 10,10
                    if (bot.goalTile,bot.goalTile) in bot.seen: bot.seen.remove((bot.goalTile,bot.goalTile))
                    # init on either side
                    for successor in bot.successors():
                    #   print(f"comment IS THIS A TUPLE? {successor}",flush=True)
                        frontier.put((bot.eval(successor), successor))

                    if bot.currentTile() in [(0,0),(10,10)] and bot.moves==[]:
                        if bot.paths==[]: frontier.get()
                        if frontier.qsize() > 1 and random.random() < 0.5:
                            dq = frontier.get()[1]
                            print(f"comment {dq}",flush=True)
                            frontier.put((bot.eval(dq)+1,dq))
                            # print("comment red trying from here",flush=True)

                else:

                    print(f"comment current location: {(x,y)}",flush=True)

                    if bot.minPathIndx < len(bot.minPath): 
                        successor = bot.minPath[bot.minPathIndx]


                        # if not initial move, aiming for next checkpoint tile
                        if bot.minPathIndx != 0:
                            curr = bot.minPath[bot.minPathIndx-1]

                            if bot.goalTile == 0:
                                if (abs(curr[0] - x) > 0.80) or (abs(curr[1] - y) > 0.80):
                                    print(f"comment waiting to send next command....current location: {(x,y)} until next: {curr}",flush=True)
                                    bot.last_move_time = timer()
                                    
                                else:
                                    # print("comment sitting here 1",flush=True)
                                    # print(f"comment inner current location: {(x,y)}", flush=True)
                                    print("toward %s %s" % (successor[0]+0.5,successor[1]+0.5), flush=True)
                                    # print("toward %s %s" % successor, flush=True)
                                    bot.last_move_time = timer()
                                    bot.minPathIndx += 1
                                    # print(f"comment new index: {bot.minPathIndx}",flush=True)
                            else:
                                if (abs(curr[0]+1 - x) > 0.80) or (abs(curr[1]+1 - y) > 0.80):
                                    print(f"comment waiting to send next command....current location: {(x,y)} until next: {curr}",flush=True)
                                    bot.last_move_time = timer()
                                else:
                                    # print("comment sitting here 1",flush=True)
                                    # print(f"comment inner current location: {(x,y)}", flush=True)
                                    print("toward %s %s" % (successor[0]+0.5,successor[1]+0.5), flush=True)
                                    # print("toward %s %s" % successor, flush=True)
                                    bot.last_move_time = timer()
                                    bot.minPathIndx += 1

                        # move to first tile     
                        else:
                            # print(f"comment outer current location: {(x,y)}",flush=True)
                            # frontier.put((bot.eval(successor), successor))
                            print("toward %s %s" % (successor[0]+0.5,successor[1]+0.5), flush=True)

                            # print("toward %s %s" % (successor[0]+0.5,successor[1]+0.5), flush=True)
                            bot.last_move_time = timer()
                            bot.minPathIndx += 1
                            # print(f"comment new outer index: {bot.minPathIndx}",flush=True)
                
            
        elif obs[0] == "wall":
            # ensure every wall we see is tracked in our walls set
            x0 = int(float(obs[1]))
            y0 = int(float(obs[2]))
            x1 = int(float(obs[3]))
            y1 = int(float(obs[4]))
            bot.walls |= {(x0,y0,x1,y1)}

        elif obs[0] == "coin":
            x = int(float(obs[1]))
            y = int(float(obs[2]))
            bot.coins |= {(x,y)}
            # print(f"comment coin added: {bot.coins}")
        
        if obs == "close": 
            exit(0)
    
        if not frontier.empty():
            # print("comment %s" % str(frontier.queue))
            item = frontier.get()
            # print("comment %s" % str(item))
            next_tile = item[1]
            # print(f"comment current position: {bot.tile_x}, {bot.tile_y}")
            # print(f"comment next_tile frontier: {item[1]}")


            # print(f"comment next tile = {next_tile[0]} , {next_tile[1]}")
            # We've now seen the tile we're on
            if bot.currentTile() != (bot.goalTile,bot.goalTile):
                bot.seen |= {(bot.tile_x, bot.tile_y)}
            x = next_tile[0] + 0.5
            y = next_tile[1] + 0.5

            frontier.queue.clear() # commented out to enable new moves on init

            if len(bot.moves) == 0 or bot.moves[-1] != (next_tile[0], next_tile[1]):
                bot.moves.append((next_tile[0], next_tile[1]))
            
            print("toward %s %s" % (x,y), flush=True)
            bot.last_move_time = timer()
            # print(f"comment moves: {bot.moves} | pathcost: {bot.pathcost}")
            # print("comment ", flush=True)

    
    if not bot.searching:
        if bot.minPathIndx == 0: continue
        # if not (bot.minPathIndx < len(bot.minPath)):
            # bot.step(bot.minPath[len(bot.minPath)-1])
        if not (bot.minPathIndx < len(bot.minPath)):
            move = bot.minPath[len(bot.minPath)-1]
            print("toward %s %s" % (move[0]+0.5,move[1]+0.5), flush=True)
            time.sleep(1)
            bot.last_move_time = timer()

        _time = timer()
        print(f"comment TSLC: {(_time - bot.last_move_time)} seconds",flush=True)
        if (_time - bot.last_move_time) > 15:
            # print(f"comment EMERGENCY SWAPPING TO SEARCHING",flush=True)
            # bot.searching = True
            # bot.moves = bot.minPath[:bot.minPathIndx:]

            if bot.centerAttempt < 3:
                print(f"comment EMERGENCY: TRYING TO CENTER SELF ATTEMPT #{bot.centerAttempt+1}",flush=True)
                bot.centerSelf()

                if bot.currentTile() != bot.minPath[bot.minPathIndx]:
                    print("toward %s %s" % (bot.minPath[bot.minPathIndx][0]+0.5,bot.minPath[bot.minPathIndx][1]+0.5), flush=True)
                    bot.last_move_time = timer()
                else:
                    bot.minPathIndx +=1
                    print("toward %s %s" % (bot.minPath[bot.minPathIndx][0]+0.5,bot.minPath[bot.minPathIndx][1]+0.5), flush=True)
                    bot.last_move_time = timer()
            else:
                bot.centerAttempt = 0
                print(f"comment EMERGENCY: SWAPPING TO SEARCHING",flush=True)
                bot.swapToSearch()


    if bot.goal():
        time.sleep(1)
        if bot.goalTile == 10: print("comment Reached the flag! Congrats!", flush=True)
        if bot.goalTile == 0: print("comment Captured the flag! Congrats!", flush=True)
        frontier.queue.clear()
        bot.cacheMoves()
        bot.changeGoal()
        print("comment New goal: %s" % bot.goalTile, flush=True)

        if bot.numPaths >= PATHS_BEFORE_DTP:
            dPath = bot.deterministicPath()
            frontier.queue.clear()
            print(f"comment adding dpath: {dPath}", flush=True)
            bot.searching = False
            condensedPath = bot.condensePath(dPath)
            print(f"comment condensed minPath: {condensedPath}", flush=True)
            bot.minPath = condensedPath
                        

        # need to send command to stdin here maybe??
    time.sleep(0.15)
        
    if bot.searching:
        print("", flush=True)
        time.sleep(0.175)