import sys, select, time
import random
from group4astar import ASTAR, Maze, load_walls

def l2(xi, yi, xf, yf):
  return ((xi - xf)**2 + (yi - yf)**2)**0.5

def l1(xi, yi, xf, yf):
  return(abs(xi - xf) + abs(yi - yf))

class RobotSimulation:
    def __init__(self) -> None:
        # current exact position
        self.lost    = True
        self.finding = False
        self.x       = 0.5
        self.y       = 0.5

        self.home_x = self.x
        self.home_y = self.y

        self.goalx = 10.5  # astar does not work with incorrect coordinates
        self.goaly = 10.5

        self.runs_made = 0
        self.prev_time = time.time()

        # set of walls known
        self.walls = set()
        self.inner_walls = set()
        for i in range(0,11):
            self.walls |= {(i,0,i+1,0), (i,11,i+1,11), (0,i,0,i+1), (11,i,11,i+1)} # (i,0,i+0,0)
        self.blocking_walls = set([(0, 1, 1, 1), (1, 0, 1, 1), (1, 1, 0, 1), (1, 1, 1, 0)])

        # last tile "reached" (i.e., being close enough to center)
        self.tx = -1
        self.ty = -1
        self.last2moves = [(-5.0, -5.0), (-5.0, -5.0)]
        self.last_move = (-5.0, -5.0)

        #JUMP
        self.power_level  = 0
        self.is_jumping   = False
        self.coin_hopping = False

        #COINS
        self.coin_count   = 0
        self.coins        = set()
        #self.last_coins   = set()
        self.closest_coin = (-5.0, -5.0)

        #OPPOSITION
        self.oppx              = -5.0
        self.oppy              = -5.0
        self.seen_opp          = False
        self.oppt              = time.time() #time in real time processing seconds since last opp sighting (not game seconds)
        self.oppt_close        = time.time() #same but for opp is within 1 tile
        self.walls_shouted     = set() #Keeps track of walls shouted in comments
        self.walls_not_dropped = set() #Keeps track of walls decided not to drop shouted in comments

        astar = ASTAR(Maze(self.x,self.y,self.goalx,self.goaly,self.walls))
        self.next_moves = astar.run()

    def recalc(self):
        midx = int(self.x) #+ 0.5
        midy = int(self.y) #+ 0.5
        astar = ASTAR(Maze(midx,midy,self.goalx,self.goaly,self.walls))
        self.next_moves = astar.run()

    def reset_coins(self):
        #self.last_coins  |= self.coins
        self.coins        = set()
        self.closest_coin = (-5, -5)

    def forget_opp(self):
        self.oppx  = -5.0
        self.oppy  = -5.0

    def update_lastmoves(self, m):
        self.last2moves.append(m)
        self.last2moves = self.last2moves[1:]

    def run(self):
        # introduce ourselves, all friendly like
        print("himynameis UNCLE-STEVE", flush=True)
        #lost = True

        # Wait a few seconds for some initial sense data
        time.sleep(0.25)

        while True:
            # sense the surrounding (position, walls, coins, etc)
            #self.reset_coins()
            self.forget_opp()
            self.sense_env() # env
            if (time.time() - self.prev_time) > ((self.power_level+3) * 7): #If greater than 7 realtime seconds per move plus 2(accounting for jump)
                self.lost=True

            if self.lost:
                print("comment LOST", flush=True)
                self.find_yourself()

            # update once at goal
            dist2goal = l1(self.x,self.y,self.goalx,self.goaly)
            if dist2goal < 0.2:
                tmp_x, tmp_y= self.home_x, self.home_y
                self.home_x, self.home_y = self.goalx, self.goaly
                self.goalx, self.goaly = tmp_x, tmp_y
                print(f'comment self.home_x == {self.home_x}, self.home_y == {self.home_y}')
                print(f'comment self.goalx ==  {self.goalx},  self.goaly ==  {self.goaly}')
                self.runs_made += 1
                self.reset_coins()
                #self.last_coins = set()

            
            if l1(self.x,self.y,self.next_moves[0][0],self.next_moves[0][1]) < 0.2 and self.finding==False: #if close to center of target tile and not lost
                self.tx = int(self.x) + 0.5
                self.ty = int(self.y) + 0.5
                self.is_jumping = False
                self.coin_hopping = False
                # print("comment arrived", self.tx, self.ty, flush=True)
                # print("comment COINS: ", flush=True)
                # if len(self.coins) == 0:
                #     print("comment NONE", flush=True)
                # for c in self.coins:
                #     print("comment     c", c, flush=True)
                # self.coins.discard((self.tx, self.ty))

                if ((self.tx, self.ty) == (1.5, 0.5)) and dist2goal>5 and self.coin_count >= 6:
                    if (1, 0, 1, 1) not in self.walls and (1, 1, 1, 0) not in self.walls:
                        print("block 1.5 0.5 l")
                elif ((self.tx, self.ty) == (0.5, 1.5)) and dist2goal>5 and self.coin_count >= 6:
                    if (0, 1, 1, 1) not in self.walls and (1, 1, 0, 1) not in self.walls:
                        print("block 0.5 1.5 u")


                if self.coin_audible():
                    if self.closest_coin != None:
                        #print("comment moves_pre ", self.next_moves, flush=True)
                        self.next_moves.insert(0, (self.tx, self.ty))
                        self.next_moves.insert(0, self.closest_coin)
                        self.coins.remove(self.closest_coin)
                        print("comment MR STEAL YO COIN", flush=True)
                        #print("comment moves_post", self.next_moves, flush=True)
                        #print("comment coin", self.closest_coin, flush=True)


                else:
                    astar = ASTAR(Maze(self.x,self.y,self.goalx,self.goaly,self.walls))
                    self.next_moves = astar.run()
                    #move = self.next_moves[0] #MAYBE DELETE THIS, DALLIN DIDN"T HAVE IT HERE
                    #move = self.last2moves[0]
                    self.jump(self.last_move) # turbo time
                    #print(f'comment next_move: {move}',flush=True)

                move = self.next_moves[0]
                #self.block_check() #See if can drop temp wall

                #Check if stuck
                if move == self.last2moves[0] == self.last2moves[1]:
                    self.lost=True
                    self.recalc()
                    move = self.next_moves[0]

                print("toward %s %s" % (move[0], move[1]), flush=True)
                # print("comment coin_hopping", self.coin_hopping, flush=True)
                # print("comment jumping     ", self.is_jumping, flush=True)
                # print("comment coins", self.coins, flush=True)
                self.prev_time = time.time()
                self.update_lastmoves(move)
                self.last_move = move
                # print("comment ----------------------", flush=True)
                # time.sleep(0.125)

            elif self.finding==True: #make it to the middle of your tile
                # print("comment xy ",  self.x, self.y, flush=True)
                # print("comment txy",  self.tx, self.ty, flush=True)
                tile_mid_x = int(self.x)+0.5
                tile_mid_y = int(self.y)+0.5
                if l1(self.x, self.y, tile_mid_x, tile_mid_y) < 0.1:
                    self.finding=False
                    self.recalc()
                    move = self.next_moves[0]
                    print("toward %s %s" % (move[0], move[1]), flush=True)
                    self.last_move = move
                    self.prev_time = time.time()
                else:
                    self.next_moves[0] = (tile_mid_x, tile_mid_y)

            print("", flush=True)
            time.sleep(0.125)

    def coin_audible(self):
        if len(self.coins) == 0: return False
        if self.is_jumping: return False
        else:
            for c in self.coins:
                coin_blocked = False
                if l1(self.tx, self.ty, c[0], c[1]) >= 1.35: #diagonal move bad too
                    print("comment too far", c, flush=True)
                    coin_blocked = True
                else:
                    potential_walls = walls_from_path((self.tx, self.ty), c)
                    for pot_w in potential_walls:
                        if pot_w in self.inner_walls:
                            print("comment I SMELL A COIN", flush=True)
                            print("comment Blocked:", pot_w, flush=True)
                            coin_blocked = True
                    if coin_blocked == False:
                        print("comment Closest coin:", c, flush=True)
                        self.closest_coin = c
                        self.coin_hopping = True
                        return True
            return False               

    def find_yourself(self):
        # print("comment LOST: ",  flush=True)
        # print("comment xy ",  self.x, self.y, flush=True)
        # print("comment txy",  self.tx, self.ty, flush=True)
        #self.reset_coins()
        if (self.x < 1) and (self.y < 1): #If top left
            print("comment Found top left", flush=True)
            self.goalx  = 10.5
            self.goaly  = 10.5
            self.home_x =  0.5
            self.home_y =  0.5
            self.tx     =  0.5
            self.ty     =  0.5
            if (-5.0, -5.0) not in self.last2moves: #Dummy coords used in init (/IF IS NOT BEGINNING OF GAME)
                self.recalc()
            
        elif (self.x > 10) and (self.y > 10): #If bottom right
            print("comment Found bot right", flush=True)
            self.goalx  =  0.5
            self.goaly  =  0.5
            self.home_x = 10.5
            self.home_y = 10.5
            self.tx     = 10.5
            self.ty     = 10.5
            self.recalc()

        else:
            self.recalc()
            self.tx = int(self.x) + 0.5
            self.ty = int(self.y) + 0.5
            self.next_moves.insert(0, (self.tx, self.ty))

        self.lost = False
        self.finding = True
        move = self.next_moves[0]
        print("toward %s %s" % (move[0], move[1]), flush=True)
        self.last_move = move
        self.prev_time = time.time()
        
        # move = self.next_moves[0]
        # print("toward %s %s" % (move[0], move[1]), flush=True)
        # print("", flush=True)
        # time.sleep(0.125)

    def jump(self,last_move):
        if (-5.0, -5.0) in self.last2moves:
            print("comment no jump at start", flush=True)
            self.power_level = 0
            return

        if self.coin_hopping:
            print("comment no jump coin_hop", flush=True)
            self.power_level = 0
            return

        if l2(last_move[0],last_move[1],self.x,self.y) > 1:
            print("comment no jump last_move", flush=True)
            print("comment", last_move[0], flush=True)
            print("comment", last_move[1], flush=True)
            self.power_level = 0
            return
        
        if l2(self.home_x, self.home_y, self.x, self.y)<1 or l2(self.goalx, self.goaly, self.x, self.y)<1: #Concept of last_move breaks down here
            print("comment no jump at home", flush=True)
            self.power_level = 0
            return

        #check direction of first move
        xchg = last_move[0] - self.next_moves[0][0]
        ychg = last_move[1] - self.next_moves[0][1]
            
        num = 0
        power_level = 0
        if xchg == 0: #verticle Jump
            if ychg > 0:
                wall_dir = 'd'
            else:
                wall_dir = 'u'

            for i in range(len(self.next_moves)):
                if i == len(self.next_moves) - 1: 
                    break
                if i < len(self.next_moves)-1 and self.next_moves[i][0] != self.next_moves[i+1][0]: 
                    break
                num += 1

        else: # y is const, moving left or right
            if xchg > 0:
                wall_dir = 'l'
            else:
                wall_dir = 'r'

            for i in range(len(self.next_moves)):
                if i == len(self.next_moves) - 1: 
                    break
                if i < len(self.next_moves)-1 and self.next_moves[i][1] != self.next_moves[i+1][1]: 
                    break
                num += 1
        
        if self.runs_made < 4: #Limit jumps to vision distance until 2 flags capped
            power_level = min(4, num)
        else: power_level = min(6, num) #Momentum issues if higher than 6

        if power_level > 4 and l2(self.x, self.y, self.oppx, self.oppy) < 7:
            print("comment EAT MY SHORTS", flush=True)
            print("block", self.tx, self.ty, wall_dir, flush=True)

        if num != 0 and not self.coin_hopping:
            print("comment TURBOTIME!", flush=True)
            print("comment POWERLEVEL:", power_level, flush=True)
            #self.reset_coins()
            self.is_jumping = True
        self.power_level = power_level

        for c in range(power_level):
            self.coins.discard(self.next_moves[c])
        self.next_moves = self.next_moves[power_level:]

    def block_check(self):
        if self.oppx == -5.0: return

        now = time.time()
        seen_opp = (now - self.oppt) < 7 #True if it's been less than 7 real time seconds since last opp sighting
        self.oppt = now

        if not seen_opp:
            print("comment OPP ON SITE", flush=True)

        if opp_is_close(self.x, self.y, self.oppx, self.oppy):
            seen_opp_close = (now - self.oppt_close) < 10 #True if it's been less than 10 real time seconds since last opp sighting
            self.oppt_close = now
            if not seen_opp_close:
                print("comment OPP IN RANGE", flush=True)
            
            if self.coin_count >= 6:
                if not seen_opp_close:
                    print("comment I GOT BANDS", flush=True)
                my_walls = list(walls_to_place(self.oppx, self.oppy, self.walls))
                
                for w in my_walls:
                    if w not in self.walls_shouted:
                        print("comment BET YOUD HATE THIS: ", flush=True)
                        print("comment ", w, flush=True)
                        self.walls_shouted |= set([w])

                    if not blocks_my_path(self.x, self.y, w, self.next_moves):
                        print("BOUTA DROP ONE NERD", flush=True)
                        print("block ", w, flush=True)
                        print("comment WALL DROPPED SUCKA", flush=True)
                    else:
                        if w not in self.walls_not_dropped:
                            print("comment SAME THO NGL: ", flush=True)
                            self.walls_not_dropped |= set([w])
            else:
                print("comment AINT NO BREAD THO", flush=True)

    def sense_env(self):  # ,sensed
        # while there is new input on stdin:
        while select.select([sys.stdin,],[],[],0.0)[0]:
            # read and process the next 1-line observation
            obs = sys.stdin.readline()
            obs = obs.split(" ")
            if obs == []: pass
            
            elif obs[0] == "bot":
                # update our own position
                self.x = float(obs[1])
                self.y = float(obs[2])
                # print("comment now at: %s %s" % (x,y), flush=True)
                self.coin_count = int(obs[3])

            elif obs[0] == "wall":
                # ensure every wall we see is tracked in our walls set
                x0 = int(float(obs[1]))
                y0 = int(float(obs[2]))
                x1 = int(float(obs[3]))
                y1 = int(float(obs[4]))
                self.walls       |= {(x0,y0,x1,y1)}
                self.inner_walls |= {(x0,y0,x1,y1)}

            elif obs[0] == "coin":
                cx = float(obs[1])
                cy = float(obs[2])
                new_coin = (cx, cy)

                if new_coin not in self.coins:
                    print("comment NEW COIN", new_coin, flush=True)
                self.coins |= set([new_coin])
                #if new_coin not in self.last_coins:
                    #print("comment COIN: ", cx, cy, flush=True) #OUTPUT IS: red coin at: 8.500000 5.500000
                #pass

            elif obs[0] == "opponent":
                ox = int(float(obs[1])) + 0.5   #Force opp position to a tile, this is an assumption
                oy = int(float(obs[2])) + 0.5
                if l1(self.tx, self.ty, ox, oy) == 1:
                    self.oppx = ox
                    self.oppy = oy

            elif obs[0] == "twall":
                pass
                #interesting

# helper functions
def ccw(Ax, Ay, Bx, By, Cx, Cy):
    return((Cy-Ay)*(Bx-Ax) > (By-Ay)*(Cx-Ax))  #https://bryceboe.com/2006/10/23/line-segment-intersection-algorithm/

def intsct(Ax, Ay, Bx, By, Cx, Cy, Dx, Dy):
    return ccw(Ax, Ay, Cx, Cy, Dx, Dy) != ccw(Bx, By, Cx, Cy, Dx, Dy) and ccw(Ax, Ay, Bx, By, Cx, Cy) != ccw(Ax, Ay, Bx, By, Dx, Dy)

def midpoint(pt1, pt2):
    midx = (pt1[0] + pt2[0]) * 0.5
    midy = (pt1[1] + pt2[1]) * 0.5
    return (midx, midy)

def walls_from_path(p1, p2):
    a = int(p1[0])
    b = int(p1[1])
    c = int(p2[0])
    d = int(p2[1])
    rlist = [d, c, b, a]

    clist = list(set([a, b, c, d]))
    i = clist[0]
    j = clist[1]

    w = [0, 0, 0, 0]
    for k in range(len(w)):
        if rlist[k] == i:
            w[k] = j
        else: w[k] = i

    w2 = [w[2], w[3], w[0], w[1]]

    return set([tuple(w), tuple(w2)])

def midwall(wall):
    midx = (wall[0] + wall[2]) * 0.5
    midy = (wall[1] + wall[3]) * 0.5
    return (midx, midy)

def blocks_my_path(x, y, w, path):
    curr = (int(x)+0.5, int(y)+0.5)
    path.insert(0, curr)
    midw = midwall(w)

    for p in range(len(path)-1):
        midp = midpoint(path[p], path[p+1])
        if midp == midw:
            return False

    return True

def opp_is_close(x, y, x2, y2):
    if (int(x) - int(x2)) + (int(y) - int(y2)) == 0:
        #print("comment L1 Opp distance used", flush=True)
        return True
    elif l2(x, y, x2, y2) <= 1:
        #print("comment L2 Opp distance used", flush=True)
        return True

def walls_to_place(oppx, oppy, walls):
    opp_moves = ["A", "B", "L", "R"]
    my_walls = set()

    #build walls that surround opposition bot
    left  = {(int(oppx),   int(oppy),   int(oppx),   int(oppy)+1)}
    right = {(int(oppx)+1, int(oppy),   int(oppx)+1, int(oppy)+1)}
    above = {(int(oppx),   int(oppy),   int(oppx)+1, int(oppy)  )}
    below = {(int(oppx),   int(oppy)+1, int(oppx)+1, int(oppy)+1)}

    #Reverse order of point1 and point2 from above
    left2  = {(int(oppx),   int(oppy)+1, int(oppx),   int(oppy)  )}
    right2 = {(int(oppx)+1, int(oppy)+1, int(oppx)+1, int(oppy)  )}
    above2 = {(int(oppx)+1, int(oppy),   int(oppx),   int(oppy)  )}
    below2 = {(int(oppx)+1, int(oppy)+1, int(oppx),   int(oppy)+1)}

    if left in walls or left2 in walls:
        opp_moves.pop("L")
    elif right in walls or right2 in walls:
        opp_moves.pop("R")
    elif above in walls or above2 in walls:
        opp_moves.pop("A")
    elif below in walls or below2 in walls:
        opp_moves.pop("B")

    for w in opp_moves:
        if w == "A":
            my_walls |= above
        elif w == "B":
            my_walls |= below
        elif w == "L":
            my_walls |= left
        elif w == "R":
            my_walls |= right
        
    return my_walls

def print_cmd_line(obs, bot=True, walls=True,empty=False):

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
    elif len(obs) > 1 and obs[0:4] != 'wall' and obs[0:3] != 'bot':
        print(f"comment bot == {obs}", flush=True)  

    # # see everything but walls using regualar expressions
    # pattern = re.compile(r'wall')
    # if not pattern.search(obs) and len(obs)>1:
    #     print(f"comment obs == {obs}", flush=True)

if __name__ == "__main__":
    sim = RobotSimulation()
    sim.run()