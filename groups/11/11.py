
import sys
import select
import time
import random


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
  walls |= {(i,0,i+1,0), (i,11,i+1,11), (0,i,0,i+1), (11,i,11,i+1)}

# DFS tree
plan = [] 
seen = set()
dead = set()

# introduce ourselves, all friendly like
print("himynameis Akshar", flush=True)

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
      x = float(obs[1])
      y = float(obs[2])
      # print("comment now at: %s %s" % (x,y), flush=True)
      # update our latest tile reached once we are firmly on the inside of the tile
      if ((int(x) != tx or int(y) != ty) and
          ((x-(int(x)+0.5))**2 + (y-(int(y)+0.5))**2)**0.5 < 0.2):
        tx = int(x)
        ty = int(y)
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
  if len(plan) > 0 and plan[-1] == (tx,ty):
    seen |= {(tx,ty)} # marking the tile as seen
    # returned back to origin
    if(plan[-1][0] == home_x) and (plan[-1][1] == home_y):
      dead -= {(10,10)}
      seen = {(tx,ty)}

    # if we've hit our opposing corner:
    if(plan[-1][0] == 10) and (plan[-1][1] == 10):
      # mark all other tiles dead, this is our final path, backtrack
      planset = set(plan)
      dead = set()
      for i in range(11):
        for j in range(11):
          if (i,j) not in planset:
            dead |= {(i,j)} # also means, there is only one way to move
      seen = set()
    # for wall in wal`ls:
    #   print("comment ",  wall[0], wall[1], wall[2], wall[3])
    def g():
      return len(plan)
    
    def h(tup):
      return abs((10 - tup[0])) + abs((10 - tup[1]))
    
    def f(tup):
      return h(tup) + g()

    moves = {("down",tx,ty+1),("right",tx+1,ty),("up",tx,ty-1),("left",tx-1,ty)}
    best = None
    for move in moves:
      wall = None
      if move[0] == "down":
        wall = (tx,ty+1,tx+1,ty+1)
      elif move[0] == "right":
        wall = (tx+1,ty,tx+1,ty+1)
      elif move[0] == "up":
        wall = (tx,ty,tx+1,ty)
      elif move[0] == "left":
        wall = (tx,ty,tx,ty+1)

      if move not in dead|seen and wall not in walls:
        if best == None:
          best = move[1:]
        elif f(move[1:]) < f(best):
          best = move[1:]
      
    if best != None:
      plan.append(best)
    else:
    # if we cannot advance or are not pathing currently, backtrack
      dead |= {(tx,ty)}
      plan = plan[:-1]
      # backtrack further, in one command, if we're
      #   returning to start AND its in a straight line:
      # while seen == set() and (plan[-1][0] == tx or plan[-1][1] == ty):
      #   plan = plan[:-1]
    
        


    # issue a command for the latest plan
    print("toward %s %s" % (plan[-1][0]+0.5, plan[-1][1]+0.5), flush=True)
  
  print("", flush=True)
  time.sleep(0.125)
  
