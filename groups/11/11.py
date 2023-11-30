import sys
import select
import time
import random
import queue

x,y = 0.5, 0.5 # current exact position
ty,tx = -1, -1 # last tile reached, upper left corner of the tile reached
walls = set()
home_x, home_y = 0,0
goal_x,goal_y = 10,10
# DFS tree
plan = []
seen = set()
dead = set()
frontier=queue.PriorityQueue()
going_back=0
reached=0
two_paths=[]
initial_check = 1

def outer_walls():
  global walls
  for i in range(0,11):
    walls |= {(i,0,i+0,0), (i,11,i+1,11), (0,i,0,i+1), (11,i,11,i+1)}

def updatesensedata():
  global x, y, home_x, home_y, tx, ty, walls, plan, seen, dead, goal_x, goal_y, initial_check
  # print("comment : Inside the fuck cond", flush=True)
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

        if initial_check and tx == 10 and ty == 10:
          goal_x, goal_y = 0,0
        elif initial_check:
          goal_x, goal_y = 10,10
        
        initial_check = 0
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
  # print("comment " + "boom" + " ".join([str(x) for x in plan]))

def dfs():
  global x, y, tx, ty, walls, plan, seen, dead
  if len(seen) > 0 and (tx,ty+1) not in dead|seen and (tx,ty+1,tx+1,ty+1) not in walls:
    plan.append((tx,ty+1))  # move down
  elif len(seen) > 0 and (tx+1,ty) not in dead|seen and (tx+1,ty,tx+1,ty+1) not in walls:
    plan.append((tx+1,ty))  # move right
  elif len(seen) > 0 and (tx,ty-1) not in dead|seen and (tx,ty,tx+1,ty) not in walls:
    plan.append((tx,ty-1))  # move up
  elif len(seen) > 0 and (tx-1,ty) not in dead|seen and (tx,ty,tx,ty+1) not in walls:
    plan.append((tx-1,ty))  # move left
  else: #back track
    dead |= {(tx,ty)}
    plan = plan[:-1]

def eval(tX,tY):
  h2 = abs(goal_x-tX)+abs(goal_y-tY)
  return h2

def A_star():
  global tx, ty, walls, seen, dead, frontier, plan
  frontier=queue.PriorityQueue()
  stuck=True

  if len(seen) > 0 and (tx,ty+1) not in dead|seen and (tx,ty+1,tx+1,ty+1) not in walls:
    frontier.put((eval(tx,ty+1),(tx,ty+1)))
    stuck=False
  if len(seen) > 0 and (tx+1,ty) not in dead|seen and (tx+1,ty,tx+1,ty+1) not in walls:
    frontier.put((eval(tx+1,ty),(tx+1,ty)))
    stuck=False
  if len(seen) > 0 and (tx-1,ty) not in dead|seen and (tx,ty,tx,ty+1) not in walls:
    frontier.put((eval(tx-1,ty),(tx-1,ty)))
    stuck=False
  if len(seen) > 0 and (tx,ty-1) not in dead|seen and (tx,ty,tx+1,ty) not in walls:
    frontier.put((eval(tx,ty-1),(tx,ty-1)))
    stuck=False
  
  if stuck:
    return 0
  
  return 1
  
def main():
  global x, y, home_x, home_y, tx, ty, walls, plan, seen, dead, count, goal_x, goal_y, frontier
  outer_walls()
  print("himynameis BirdBot", flush=True)

  time.sleep(0.25)
  
  select.select([sys.stdin,],[],[],0.0)[0]
  while True:
    count=[]
    updatesensedata()
    if len(plan) > 0 and plan[-1] == (tx,ty): # if bot reached latest command location
      seen |= {(tx,ty)} # marking the tile as seen
      print("comment tile: %s %s" % (tx,ty), flush=True)
      # returned back to origin
      if(plan[-1][0] == home_x) and (plan[-1][1] == home_y):
        dead -= {(goal_x,goal_y)}
        seen = {(tx,ty)}
      # if we've hit our opposing corner:
      if(plan[-1][0] == goal_x) and (plan[-1][1] == goal_y):
        # mark all other tiles dead, this is our final path, backtrack
        planset = set(plan)
        dead = set()
        for i in range(11):
          for j in range(11):
            if (i,j) not in planset:
              dead |= {(i,j)} # also means, there is only one way to move
        seen = set()
      # dfs()
      front = A_star()
      if front:
        plan.append(frontier.get()[1])
      else:
        dead |= {(tx,ty)}
        plan=plan[:-1]
      print(f"toward {plan[-1][0]+0.5} {plan[-1][1]+0.5}", flush=True)
      
    print("", flush=True)
    time.sleep(0.125)
main()
