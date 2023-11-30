
import sys
import select
import time
import random
import copy
import queue
import threading

# current exact position
x = 0.5
y = 0.5
# last tile "reached" (i.e., being close enough to center)
ty = -1
tx = -1

# LOS distance
LOS_dist = 5

#goal - home variables
home_x,home_y = 0,0
goal_x,goal_y = 10,10 

#last seen opponent position
ox = -100.0
oy = -100.0
# last tile opponent "reached"
oty = -100
otx = -100

# number of signals before start:
start_timeout_signals = 15
# idling signals
idling_timeout_signals = 100
idle_index = 0

# set of walls known
processed_walls = set()
unprocessed_walls = set()
twalls = set()
twall_discovered = False
twall_forgot = False

# D*L
opt_plan = []
exec_index = 0
target_index = 0
# coin_value = 1 #steps offset to get grab coin
grab_coins = set()
saw_coins = set()
coin_discovered = False
coin_count = 0
wait_state = False
opponent_discovered = False

for i in range(0,11):
  processed_walls |= {(i,0,i+0,0), (i,11,i+1,11), (0,i,0,i+1), (11,i,11,i+1)}

# walls functions
def up_wall(x, y):
  return (x,y,x+1,y) 
def down_wall(x, y):   
  return (x,y+1,x+1,y+1)
def right_wall(x, y):
  return (x+1,y,x+1,y+1)
def left_wall(x, y):
  return (x,y,x,y+1)

def find_fault_step(plan, step, wall_set):
  for i in range(step, len(plan) - 1):
    if (is_blocked(plan[i], plan[i+1], wall_set)): 
      return i
  return 0

def is_blocked(from_pos, to_pos, wall_set):
  return (
    ((to_pos[0] - from_pos[0] == 1) and right_wall(from_pos[0],from_pos[1]) in wall_set) or 
    ((to_pos[1] - from_pos[1] == 1) and down_wall(from_pos[0],from_pos[1]) in wall_set) or
    ((to_pos[0] - from_pos[0] == -1) and left_wall(from_pos[0],from_pos[1]) in wall_set) or 
    ((to_pos[1] - from_pos[1] == -1) and up_wall(from_pos[0],from_pos[1]) in wall_set))

def process_walls():
  global processed_walls, unprocessed_walls, twalls, twall_discovered
  processed_walls.update(unprocessed_walls) # add walls to processed
  twalls = set()
  twall_discovered = False
  unprocessed_walls = set() #reset the new walls set
  
def add_twall(twall, time):
  global processed_walls, twalls
  processed_walls.add(twall)
  twalls.add(twall)
  threading.Timer(time, forget_twall, twall).start() #forget the twall
  
def forget_twall(twall_x, twall_y, twall_x1, twall_y1):
  global processed_walls, twall_forgot
  processed_walls.discard((twall_x, twall_y, twall_x1, twall_y1))
  twall_forgot = True
  
def add_coin(coin):
  global saw_coins
  saw_coins.add(coin)
  threading.Timer(4.0, forget_coin, coin).start() #forget the coin
  
def forget_coin(coin_x, coin_y):
  global saw_coins
  saw_coins.discard((coin_x, coin_y))

class Plan:
  def __init__(self, x, y, gx, gy):
    self.x = x
    self.y = y
    self.gx = gx
    self.gy = gy
    self.plan = []
    self.cost = 0
  def actions(self):
    actions_set = []
    if down_wall(self.x, self.y) not in processed_walls:
      actions_set.append((self.x,self.y+1))  # move down
    if right_wall(self.x,self.y) not in processed_walls:
      actions_set.append((self.x+1,self.y))  # move right
    if left_wall(self.x, self.y) not in processed_walls:
      actions_set.append((self.x-1,self.y))  # move left
    if up_wall(self.x, self.y) not in processed_walls:
      actions_set.append((self.x,self.y-1))  # move up
      
    return actions_set
  def move(self, action):
    next = copy.deepcopy(self)
    next.x = action[0]
    next.y = action[1]
    next.cost = self.cost + 1
    next.plan.append((action[0],action[1]))
    return next
  
  def successors(self):
    successor_set = []
    for action in self.actions():
      successor_set.append(self.move(action))
    return successor_set
  
  def goal_distance(self):
    distance = abs(self.gx - self.x) + abs(self.gy - self.y)
    return distance
  
  def __lt__(self, other):
    return self.eval() < other.eval()
  
  def eval(self): #evaluate 
    return  self.cost + self.goal_distance()

def planning(start, end): # getting optimal plan with A* and mahattan distance heuristic
  planner = Plan(start[0], start[1], end[0], end[1])
  checked_set = set()
  frontier = queue.PriorityQueue()
  frontier.put(planner)
  while not frontier.empty():
    current_speculation = frontier.get()
    if current_speculation.goal_distance() == 0:
      return current_speculation
    
    checked_set.add((current_speculation.x, current_speculation.y))
    
    for successor in current_speculation.successors():
      if (successor.x, successor.y) not in checked_set:
        frontier.put(successor)
  return None
  
def follow_plan():
  global exec_index, target_index, opt_plan, goal_x, goal_y
  max_squash = 2  #max squash, code looks ok,but server get clunky with the 'speed' 'n 'bounce' mechanic
  max_index = exec_index + max_squash
  curr_step = opt_plan[exec_index]
  target_index = exec_index + 1
  next_step = opt_plan[target_index]
  
  x_diff = next_step[0] - curr_step[0]
  y_diff = next_step[1] - curr_step[1]
  
  while target_index < max_index:
    if opt_plan[target_index][0] == goal_x and opt_plan[target_index][1] == goal_y: break # reach end of plan
    if opt_plan[target_index][0] == 2 and opt_plan[target_index][1] == 2: break # weird bug
    curr_step = next_step
    next_step = opt_plan[target_index + 1]
    if ((next_step[0] - curr_step[0] != x_diff) or (next_step[1] - curr_step[1] != y_diff)):  # not moving straight
      break
    target_index += 1
      
  print("toward %s %s" % (opt_plan[target_index][0]+0.5, opt_plan[target_index][1]+0.5), flush=True)

def flip_goal():
  global home_x,home_y,goal_y,goal_x
  home_x,goal_x = goal_x,home_x
  home_y,goal_y = goal_y,home_y
  
def update_bot(obs: list):
  global x, y, coin_count, tx, ty, saw_coins
  # update our own position
  x = float(obs[1])
  y = float(obs[2])
  coin_count = int(obs[3])
  # print("comment now at: %s %s" % (x,y), flush=True)
  # update our latest tile reached once we are firmly on the inside of the tile
  if ((int(x) != tx or int(y) != ty) and ((x-(int(x)+0.5))**2 + (y-(int(y)+0.5))**2)**0.5 < 0.2):
    tx = int(x)
    ty = int(y)
    if (tx, ty) in saw_coins:
      saw_coins.discard((tx,ty))
    # print("comment now at: %s %s" % (tx,ty), flush=True)
    # if (len(opt_plan) > 0):
    #   print("comment expected at: %s %s" % (opt_plan[target_index][0],opt_plan[target_index][1]), flush=True)
    
def update_walls(obs: list):
  global unprocessed_walls, processed_walls
  # print("comment wall: %s %s %s %s" % (obs[1],obs[2],obs[3],obs[4]), flush=True)
  x0 = int(float(obs[1]))
  y0 = int(float(obs[2]))
  x1 = int(float(obs[3]))
  y1 = int(float(obs[4]))
  if (x0,y0,x1,y1) not in processed_walls and (x0,y0,x1,y1) not in unprocessed_walls: 
    unprocessed_walls.add((x0,y0,x1,y1))  #added to new walls first to check if they affect the plan
    
def update_twall(obs: list):
  global processed_walls, twall_discovered
  x0 = int(float(obs[1]))
  y0 = int(float(obs[2]))
  x1 = int(float(obs[3]))
  y1 = int(float(obs[4]))
  time = int(float(obs[5]))
  if (x0,y0,x1,y1) not in processed_walls:
    add_twall((x0,y0,x1,y1), time)
    twall_discovered = True
    
def update_coins(obs: list):
  global saw_coins, coin_discovered
  cx = int(float(obs[1]))
  cy = int(float(obs[2]))
  if (cx,cy) not in saw_coins :
    add_coin((cx,cy)) 
    coin_discovered = True
    
def update_opponent(obs: list):
  global ox, oy, otx, oty, opponent_discovered, saw_coins
  opponent_discovered = True
  ox = float(obs[1])
  oy = float(obs[2])
  otx = int(ox)
  oty = int(oy)
  if ((int(ox) != otx or int(oy) != oty) and ((ox-(int(ox)+0.5))**2 + (oy-(int(oy)+0.5))**2)**0.5 < 0.2):
    if (otx, oty) in saw_coins:
      saw_coins.discard((otx,oty))
      
def observer():
  while True:
    while select.select([sys.stdin,],[],[],0.0)[0]:
      # read and process the next 1-line observation
      obs = sys.stdin.readline()
      obs = obs.split(" ")
      if obs == []: pass
      elif obs[0] == "bot": update_bot(obs)
      elif obs[0] == "wall": update_walls(obs)
      elif obs[0] == "twall": update_twall(obs)
      elif obs[0] == "coin": update_coins(obs)
      elif obs[0] == "opponent": update_opponent(obs)
    
    print("", flush=True)
    time.sleep(0.05)
    
def new_environment_discovered():
  global unprocessed_walls, twall_discovered, coin_discovered
  return len(unprocessed_walls) > 0 or twall_discovered or coin_discovered

def handling_coins():
  global saw_coins, coin_discovered, opt_plan, exec_index, LOS_dist, processed_walls, goal_x, goal_y
  # check within next LOS_dist steps
  LOS_last_index = min(len(opt_plan) - 1, exec_index + LOS_dist)
  LOS_plan = opt_plan[exec_index :LOS_last_index]
  LOS_plan_before = opt_plan[:exec_index]
  LOS_plan_rest = opt_plan[LOS_last_index:]
  LOS_set = frozenset(LOS_plan)
  checked_coins = set()
  take_coins = 1
  for coin in saw_coins:
    if coin in checked_coins: continue
    if len(LOS_plan_rest) > 0 and coin == LOS_plan_rest[0]:
      checked_coins.add(coin)
      continue
    if coin in LOS_set:
      checked_coins.add(coin)
      continue
    for index in range(len(LOS_plan) -1): 
      path_coin_dist = abs(LOS_plan[index][0] - coin[0]) + abs(LOS_plan[index][1] - coin[1])
      #  if coin within grab range, right now only 1.
      if ((path_coin_dist <= 1) and not is_blocked(LOS_plan[index], coin, processed_walls)): 
        LOS_plan = LOS_plan[:index] + [LOS_plan[index], coin] + LOS_plan[index:]
        checked_coins.add(coin)
        take_coins -= 1
        break
    if take_coins == 0: break
  coin_discovered = False
  opt_plan = LOS_plan_before + LOS_plan + LOS_plan_rest
  
def handling_new_variables():
  global unprocessed_walls, twalls, twall_discovered, coin_discovered, opt_plan, exec_index, wait_state, goal_x, goal_y
  all_new_walls = unprocessed_walls | twalls
  fault_index = find_fault_step(opt_plan, exec_index, all_new_walls)
  process_walls()
  if fault_index == 0: #new walls not affect current plan
    # print("comment New wall not affect plan", flush=True)
    if coin_discovered: handling_coins() #new coins detected
    follow_plan()
      
  else: # walls affected. re-planning
    planner = planning(opt_plan[exec_index], (goal_x, goal_y)) #recalibrate
    if planner is not None:
      opt_plan = opt_plan[:exec_index+1] # cut off the invalid moves
      opt_plan = opt_plan + planner.plan # add the new plan
      if coin_discovered: handling_coins()
      follow_plan()
    else: # cannot solve (trapped)
      wait_state = True

def idling_check():
  global tx, ty, idling_timeout_signals, idle_index, opt_plan, target_index, exec_index
  if idling_timeout_signals == 0:
    idling_timeout_signals = 100
    handling_new_variables()
  if idle_index != exec_index:
    idle_index = exec_index
    idling_timeout_signals = 100
  else : idling_timeout_signals -= 1
    

# introduce ourselves, all friendly like
print("himynameis G5-bot", flush=True)

obs_thread = threading.Thread(target=observer)

# Wait a few seconds for some initial sense data
time.sleep(0.25)
obs_thread.start()

while True:
  # wait for # signals before start
  if start_timeout_signals > 0:
    start_timeout_signals -= 1
    pass
  
  #just start (again)
  # if len(opt_plan) == 0 and (tx, ty) in seen:
  if len(opt_plan) == 0 and start_timeout_signals == 0:
    # print("comment start planning", flush=True)
    # if start at bottom (agent 2)
    if tx == goal_x and ty == goal_y: 
      flip_goal()
    # start planning
    # traversed = {(tx, ty)}
    process_walls()
    planner = planning((tx, ty), (goal_x, goal_y))
    # initial plan
    if planner is not None and len(planner.plan) > 0:
      opt_plan = [(tx, ty)] + planner.plan
      # print("comment got a plan start moving", flush=True)
      follow_plan()
    else:
      # print("comment cannot solve this maze", flush=True)
      wait_state = True # cannot find a path, wait
      pass
  
  # Bot is navigating
  elif len(opt_plan) > 0:
    if not wait_state:
      if opt_plan[target_index] == (tx,ty): # reach the target step.
        exec_index = target_index
        # check if current step is goal:
        if(opt_plan[exec_index][0] == goal_x) and (opt_plan[exec_index][1] == goal_y):
          flip_goal()
          opt_plan = []
          exec_index = 0
          target_index = 0
          saw_coins = set()
          # traversed = set()
          continue      
        # check for new walls:
        if not new_environment_discovered(): 
          # print("comment No new variables, moving on", flush=True)
          follow_plan()
        else: # new elements detected
          handling_new_variables()
      elif opt_plan[exec_index + 1] == (tx,ty) and exec_index < target_index: # reach exec step
        exec_index += 1 
      else: # is moving toward executed step
        idling_check()
    else: # handle wait state
      if twall_forgot:
        twall_forgot = False
        handling_new_variables()
        
  print("", flush=True)
  time.sleep(0.125)
  
