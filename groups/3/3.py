
import sys
import select
import time
import random

def placeWall(coins, currentX, currentY, toX, toY) -> bool:
  global TWALL_COST
  if (coins < TWALL_COST): return False
  
  if (currentX < toX):
    print(f"comment attempted {currentX} {currentY} l")
    print(f"block {currentX} {currentY} l")
  if (currentX > toX):
    print(f"comment attempted {currentX} {currentY} r")
    print(f"block {currentX} {currentY} r")
  if (currentY > toY):
    print(f"comment attempted {currentX} {currentY} d")
    print(f"block {currentX} {currentY} d")
  if (currentY > toY):
    print(f"comment attempted {currentX} {currentY} u")
    print(f"block {currentX} {currentY} u")
  

def deadDetect(x,y, direction) -> bool:
  # Defined by the top left point that you are going to
  match direction:
    case "left":
      # Top wall                   Bottom wall                  1 deep wall                     2 -deep top                bottom                           left
      if ((x-1,y,x,y) in walls and (x-1,y+1,x,y+1) in walls and (((x-1,y,x-1,y+1) in walls)  or ((x-2,y,x-1,y) in walls and (x-2,y+1,x-1,y+1) in walls and (x-2,y,x-2,y+1) in walls))):
        print("comment left") 
        return True
      else:
        return False
    case "right":
      # Top wall                   Bottom wall                  1 deep wall                     2 -deep top                bottom                           right
      if ((x,y,x+1,y) in walls and (x,y+1,x+1,y+1) in walls and (((x+1,y,x+1,y+1) in walls)  or ((x+1,y,x+2,y) in walls and (x+1,y+1,x+2,y+1) in walls and (x+2,y,x+2,y+1) in walls))):
        print(f"comment right {x,y}") 
        print(f"comment walls {walls}")
        print(f"comment {(x+1,y,x+1,y+1) in walls} {(x+2,y,x+2,y+1) in walls}")
        return True
      else:
        return False
    case "up":
      # Left wall                   right wall                    1 up wall                       2 up left wall            2 up right wall                 2 up top
      if ((x,y-1,x,y) in walls and (x+1,y-1,x+1,y) in walls and (((x-1,y-1,x,y-1) in walls)  or ((x,y-2,x,y-1) in walls and (x+1,y-2,x+1,y-1) in walls and (x-1,y-2,x,y-2) in walls))):
        print("comment up") 
        return True
      else:
        return False
    case "down":
      # Left wall                   right wall                    1 down wall                       2 down left wall            2 down right wall                 2 down top
      if ((x,y+1,x,y+2) in walls and (x+1,y+1,x+1,y+2) in walls and (((x-1,y+2,x,y+2) in walls)  or ((x,y+2,x,y+3) in walls and (x+1,y+2,x+1,y+3) in walls and (x-1,y+3,x,y+3) in walls))):
        print("comment down") 
        return True
      else:
        return False
    case _:
      return False

def reducePathWithWalls(path: list):
# [(0, 0), (0, 1), (1, 1), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (6, 1), (6, 2), (5, 2), (5, 3), (5, 4), (4, 4), (3, 4), (3, 3), (4, 3), (4, 2), (3, 2), (2, 2), (1, 2), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (1, 6), (1, 5), (2, 5), (3, 5), (4, 5), (4, 6), (3, 6), (2, 6), (2, 7), (1, 7), (1, 8), (1, 9), (0, 9), (0, 10), (1, 10), (2, 10), (3, 10), (4, 10), (5, 10), (6, 10), (7, 10), (8, 10), (9, 10), (10, 10)]
  # This should operate as line segments and the current point should always remain the same and the last point should also remain the same, only reduce what is in between
    if len(path) < 2:
        return path

    reduced_path = [path[0]]
    prev_direction = (path[1][0] - path[0][0], path[1][1] - path[0][1])

    for i in range(1, len(path) - 1):
        current_direction = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])

        if current_direction != prev_direction:
            reduced_path.append(path[i])
            prev_direction = current_direction

    reduced_path.append(path[-1])

    return reduced_path
    # reduced_path = [path[0]]

    # for i in range(1, len(path) - 1):
    #     current_point = path[i]
    #     next_point = path[i + 1]

    #     if current_point[0] == next_point[0] or current_point[1] == next_point[1]:
    #         # The current point and next point are in a straight line
    #         reduced_path.append(next_point)
    #     else:
    #         # They are not in a straight line, so add the current point to the reduced path
    #         reduced_path.append(current_point)

    # reduced_path.append(path[-1])
      

# current exact position
x = 0.5
y = 0.5
home_x,home_y = 0,0

# last tile "reached" (i.e., being close enough to center)
ty = -1
tx = -1

# set of walls known
walls = set()
for i in range(0,11):
  walls |= {(i,0,i+0,0), (i,11,i+1,11), (0,i,0,i+1), (11,i,11,i+1)}

# DFS tree
plan = []
backupPlan = []
backupActive = False
iterator = 0
TWALL_COST = 6
coins = 0
startTime = time.time()
lastSquare = ()
firstParse = True
seen = set()
dead = set()

# introduce ourselves, all friendly like
print("himynameis adderall-bot", flush=True)

# Wait a few seconds for some initial sense data
time.sleep(0.25)

while True:
  # while there is new input on stdin:
  while select.select([sys.stdin,],[],[],0.0)[0]:
    # read and process the next 1-line observation

      
    obs = sys.stdin.readline()
    obs = obs.split(" ")
    if obs == []: pass
    elif obs[0] == "bot":
      # update our own position
      # print(f"comment {obs}") 
      x = float(obs[1])
      y = float(obs[2])
      coins = float(obs[3])
      if firstParse:
        firstParse = False
        if x == y == 10.5:
          # print("dsf")
          home_x = 10
          home_y = 10
      # print("comment now at: %s %s" % (x,y), flush=True)
      # update our latest tile reached once we are firmly on the inside of the tile
      if ((int(x) != tx or int(y) != ty) and
          ((x-(int(x)+0.5))**2 + (y-(int(y)+0.5))**2)**0.5 < 0.2):
        tx = int(x)
        ty = int(y)
        lastSquare = (tx, ty)
        if time.time() - startTime > 15 and lastSquare == (tx,ty):
          print("comment stuck",flush=True)

          print(f"toward {tx+.5} {ty+.5}", flush=True)
          time.sleep(1)
          startTime = time.time()
          print("toward %s %s" % (plan[-1][0]+0.5, plan[-1][1]+0.5), flush=True)
        if plan == []:
          plan = [(tx,ty)]
          home_x = tx
          home_y = ty
          seen = set(plan)
        #print("comment now at tile: %s %s" % (tx,ty), flush=True)
    elif obs[0] == "wall":
      #print("comment wall: %s %s %s %s" % (obs[1],obs[2],obs[3],obs[4]), flush=True)
      # ensure every wall we see is tracked in our walls set
      x0 = int(float(obs[1]))
      y0 = int(float(obs[2]))
      x1 = int(float(obs[3]))
      y1 = int(float(obs[4]))
      walls |= {(x0,y0,x1,y1)}

  # if we've achieved our goal, update our plan and issue a new command
  if (len(plan) > 0 and plan[-1] == (tx,ty)) or (len(backupPlan) >= 1 and len(plan) > 0 and plan[-1] == (tx,ty) and backupActive == False):
    seen |= {(tx,ty)} # marking the tile as seen
    if (len(backupPlan) >= 1 and len(plan) > 0 and plan[-1] == (tx,ty) and backupActive == False):
      iterator += 1
    # returned back to origin
    if(tx == home_x) and (ty == home_y):
      if home_x == home_y == 0:
        dead -= {(10,10)}

      elif home_x == home_y == 10:
        dead -= {(0,0)}  
      seen = {(tx,ty)}
      # print("comment tad")
      if len(backupPlan) >= 1:
        plan = []
        plan.append(backupPlan[0])
        backupActive = False
        iterator = 1
    

    # if we've hit our opposing corner:
    if ((home_x == home_y == 0) and (tx == 10) and (tx == 10)) or ((home_x == home_y == 10) and (tx == 0) and (ty == 0)) :
      # mark all other tiles dead, this is our final path, backtrack
      # print(f"comment MAIN: {str(plan)}")
      backupPlan = reducePathWithWalls(plan)
      # plan = backupPlan
      # print("comment your bitch is my backup plan")
      print(f"comment {str(backupPlan)}")
      backupActive = True
      planset = set(plan)
      dead = set()
      for i in range(11):
        for j in range(11):
          if (i,j) not in planset:
            dead |= {(i,j)} # also means, there is only one way to move
      seen = set()

    # if pathing, search through lower, right, top, left children, in that order
    # assumes sufficient sense data, but that may not strictly be true  
    planSize = len(plan)
    # print(f"comment equal: {plan == backupPlan} - {backupActive}")
    if len(backupPlan) >= 1 and backupActive == False:
      # print(f"comment plan: {str(plan)}")
      plan.append(backupPlan[iterator])
      print("toward %s %s" % (plan[-1][0]+0.5, plan[-1][1]+0.5), flush=True)

    else:
      if len(seen) > 0 and (tx,ty+1) not in dead|seen and (tx,ty+1,tx+1,ty+1) not in walls and planSize == len(plan):
        if not deadDetect(tx, ty+1, "down"): plan.append((tx,ty+1))  # move down
      if len(seen) > 0 and (tx+1,ty) not in dead|seen and (tx+1,ty,tx+1,ty+1) not in walls and planSize == len(plan) :

        if not deadDetect(tx+1, ty, "right"): plan.append((tx+1,ty)) # move right
      if len(seen) > 0 and (tx,ty-1) not in dead|seen and (tx,ty,tx+1,ty) not in walls and planSize == len(plan) :
        if not deadDetect(tx, ty-1, "up"): plan.append((tx,ty-1))  # move up
      if len(seen) > 0 and (tx-1,ty) not in dead|seen and (tx,ty,tx,ty+1) not in walls and planSize == len(plan):
        if not deadDetect(tx-1, ty, "left"): plan.append((tx-1,ty))  # move left
      
      if planSize == len(plan):
      # if we cannot advance or are not pathing currently, backtrack
        dead |= {(tx,ty)}

        plan = plan[:-1]
        print("comment backtracking")
        # backtrack further, in one command, if we're
        #   returning to start AND its in a straight line:
        #while seen == set() and (plan[-1][0] == tx or plan[-1][1] == ty):
        #  plan = plan[:-1]
        
      # issue a command for the latest plan
      # print(f"comment walls {walls}")
      if (len(plan) > 0):
        startTime = time.time()
        # if backupActive and random.random() < 0.05:
        #   placeWall(coins, tx, ty, plan[-1][0], plan[-1][1])
        print("toward %s %s" % (plan[-1][0]+0.5, plan[-1][1]+0.5), flush=True)
  
  print("", flush=True)
  time.sleep(0.125)
  
