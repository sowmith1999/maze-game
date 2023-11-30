"""
Group 9 - Isabelle S. Brown
CS 660 - Artificial Intelligence
Final Project - Maze Game
11/28/23
"""

# Libraries
import sys
import select
import time
import random

# Current exact position
x = 0.5
y = 0.5
home_x,home_y = 0,0

# Last tile "reached" (i.e., being close enough to center)
ty = -1
tx = -1

# Set of walls known
walls = set()
for i in range(0,11):
    walls |= {(i,0,i+0,0), (i,11,i+1,11), (0,i,0,i+1), (11,i,11,i+1)}

# DFS tree
plan = []
seen = set()
dead = set()

# Heuristic, blocking, and coin variables
pathCost = 0
coins = 0
tempWalls = set()
tempDead = set()
tempCost = 0
temp = False
setWall = 0
block = False
wait = True

# Introduce ourselves, all friendly like
print("himynameis a-star-bot-group9", flush=True)

# Wait a few seconds for some initial sense data
time.sleep(0.25)

while True:
    # While there is new input on stdin:
    while select.select([sys.stdin,],[],[],0.0)[0]:
        # Read and process the next 1-line observation
        obs = sys.stdin.readline()
        obs = obs.split(" ")
        # If nothing, pass
        if obs == []: pass
        # If bot, update position
        elif obs[0] == "bot":
            if wait:
                wait = False
                continue
            # Update our own position
            x = float(obs[1])
            y = float(obs[2])
            coins = int(obs[3])
            # Update our latest tile reached once we are firmly on the inside of the tile
            if ((int(x) != tx or int(y) != ty) and ((x-(int(x)+0.5))**2 + (y-(int(y)+0.5))**2)**0.5 < 0.2):
                tx = int(x)
                ty = int(y)
                if plan == []:
                    plan = [(tx,ty)]
                    home_x = tx
                    home_y = ty
                    seen = set(plan)
        # If wall, update set of walls
        elif obs[0] == "wall":
            # Ensure every wall we see is tracked in our walls set
            x0 = int(float(obs[1]))
            y0 = int(float(obs[2]))
            x1 = int(float(obs[3]))
            y1 = int(float(obs[4]))
            walls |= {(x0,y0,x1,y1)}
        # If twall, update set of temporary walls
        elif obs[0] == "twall":
            # Check if the wall will be there a long time and if it is from opponent
            if float(obs[3]) > 12 and setWall == 0:
                temp = True
                x = int(float(obs[1]))
                y = int(float(obs[2]))
                tempWalls |= {(x,y)}

    # If we've achieved our goal, update our plan and issue a new command
    if len(plan) > 0 and plan[-1] == (tx,ty):
        # Decrease as we move away from wall we set
        if setWall > 0:
            setWall -= 1
        seen |= {(tx,ty)} # Marking the tile as seen
        # Returned back to origin
        if(plan[-1][0] == home_x) and (plan[-1][1] == home_y):
            seen = {(tx,ty)}
            # Remove goal time from dead set based on home location
            if home_x == 0:
                dead -= {(10,10)}
            else:
                dead -= {(0,0)}
            # Reset if temporarily pathing due to a temporary wall in place
            tempDead = set()
            tempWalls = set()
            tempCost = 0
            temp = False

        # Check if we got to either our home location or flag location and leave a wall to block opponent
        if len(plan) > 2:
            # Leave wall when at the flag location
            if block:
                # Check that we have enough coins
                if coins > 5:
                    # Leave wall based on current location
                    if(plan[-1][0] == 1) and (plan[-1][1] == 0):
                        setWall = 5
                        print("block %s %s l" % (plan[-1][0], plan[-1][1]), flush=True)
                    if(plan[-1][0] == 0) and (plan[-1][1] == 1):
                        setWall = 5
                        print("block %s %s u" % (plan[-1][0], plan[-1][1]), flush=True)
                    if(plan[-1][0] == 10) and (plan[-1][1] == 9):
                        setWall = 5
                        print("block %s %s d" % (plan[-1][0], plan[-1][1]), flush=True)
                    if(plan[-1][0] == 9) and (plan[-1][1] == 10):
                        setWall = 5
                        print("block %s %s r" % (plan[-1][0], plan[-1][1]), flush=True)
                block = False
            # Leave wall when at home location (0,0)
            if(plan[-2][0] == 0) and (plan[-2][1] == 0):
                # Check that we have enough coins
                if coins > 5:
                    # Leave wall based on current location
                    if(plan[-1][0] == 1) and (plan[-1][1] == 0):
                        setWall = 5
                        print("block %s %s l" % (plan[-1][0], plan[-1][1]), flush=True)
                    if(plan[-1][0] == 0) and (plan[-1][1] == 1):
                        setWall = 5
                        print("block %s %s u" % (plan[-1][0], plan[-1][1]), flush=True)
            # Leave wall when at home location (10,10)
            if(plan[-2][0] == 10) and (plan[-2][1] == 10):
                # Check that we have enough coins
                if coins > 5:
                    # Leave wall based on current location
                    if(plan[-1][0] == 10) and (plan[-1][1] == 9):
                        setWall = 5
                        print("block %s %s d" % (plan[-1][0], plan[-1][1]), flush=True)
                    if(plan[-1][0] == 9) and (plan[-1][1] == 10):
                        setWall = 5
                        print("block %s %s r" % (plan[-1][0], plan[-1][1]), flush=True)

        # If we've hit our opposing corner:
        if home_x == 0:
            if(plan[-1][0] == 10) and (plan[-1][1] == 10):
                # Mark all other tiles dead, this is our final path, backtrack
                planset = set(plan)
                dead = set()
                for i in range(11):
                    for j in range(11):
                        if (i,j) not in planset:
                            dead |= {(i,j)} # Also means, there is only one way to move
                seen = set()
                block = True

            # Normal pathing, no temporary walls to consider
            if not temp:
                manDis = float('inf')
                newMove = False
                # Evaluating moving down
                if len(seen) > 0 and (tx,ty+1) not in dead|seen and (tx,ty+1,tx+1,ty+1) not in walls:
                    curDis = pathCost + ((abs(tx - 10) + abs((ty+1) - 10)) * 0.7)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx, ty+1)
                # Evaluating moving right
                if len(seen) > 0 and (tx+1,ty) not in dead|seen and (tx+1,ty,tx+1,ty+1) not in walls:
                    curDis = pathCost + ((abs((tx+1) - 10) + abs(ty - 10)) * 0.7)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx+1, ty)
                # Evaluating moving up
                if len(seen) > 0 and (tx,ty-1) not in dead|seen and (tx,ty,tx+1,ty) not in walls:
                    curDis = pathCost + ((abs(tx - 10) + abs((ty-1) - 10)) * 1.3)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx, ty-1)
                # Evaluating moving left
                if len(seen) > 0 and (tx-1,ty) not in dead|seen and (tx,ty,tx,ty+1) not in walls:
                    curDis = pathCost + ((abs((tx-1) - 10) + abs(ty - 10)) * 1.3)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx-1, ty)
                
                # Do best possible move if there is one, or backtrack if not
                if newMove:
                    plan.append(bestMove)
                else:
                    # If we cannot advance or are not pathing currently, backtrack
                    dead |= {(tx,ty)}
                    plan = plan[:-1]
                
                # Increment current path cost
                pathCost += 1

            # Need to redo pathing, consider temporary walls
            if temp:
                manDis = float('inf')
                newMove = False
                # Evaluating moving down
                if len(seen) > 0 and (tx,ty+1) not in tempDead|seen|tempWalls and (tx,ty+1,tx+1,ty+1) not in walls:
                    curDis = tempCost + ((abs(tx - 10) + abs((ty+1) - 10)) * 0.7)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx, ty+1)
                # Evaluating moving right
                if len(seen) > 0 and (tx+1,ty) not in tempDead|seen|tempWalls and (tx+1,ty,tx+1,ty+1) not in walls:
                    curDis = tempCost + ((abs((tx+1) - 10) + abs(ty - 10)) * 0.7)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx+1, ty)
                # Evaluating moving up
                if len(seen) > 0 and (tx,ty-1) not in tempDead|seen|tempWalls and (tx,ty,tx+1,ty) not in walls:
                    curDis = tempCost + ((abs(tx - 10) + abs((ty-1) - 10)) * 1.3)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx, ty-1)
                # Evaluating moving left
                if len(seen) > 0 and (tx-1,ty) not in tempDead|seen|tempWalls and (tx,ty,tx,ty+1) not in walls:
                    curDis = tempCost + ((abs((tx-1) - 10) + abs(ty - 10)) * 1.3)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx-1, ty)
                
                # Do best possible move if there is one, or backtrack if not
                if newMove:
                    plan.append(bestMove)
                else:
                    # If we cannot advance or are not pathing currently, backtrack
                    tempDead |= {(tx,ty)}
                    plan = plan[:-1]

                # Increment current path cost
                tempCost += 1

        # If we've hit our opposing corner:
        if home_x == 10:
            if(plan[-1][0] == 0) and (plan[-1][1] == 0):
                # Mark all other tiles dead, this is our final path, backtrack
                planset = set(plan)
                dead = set()
                for i in range(11):
                    for j in range(11):
                        if (i,j) not in planset:
                            dead |= {(i,j)} # Also means, there is only one way to move
                seen = set()
                block = True

            # Normal pathing, no temporary walls to consider
            if not temp:
                manDis = float('inf')
                newMove = False
                # Evaluating moving down
                if len(seen) > 0 and (tx,ty+1) not in dead|seen and (tx,ty+1,tx+1,ty+1) not in walls:
                    curDis = pathCost + ((abs(tx - 0) + abs((ty+1) - 0)) * 1.3)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx, ty+1)
                # Evaluating moving right
                if len(seen) > 0 and (tx+1,ty) not in dead|seen and (tx+1,ty,tx+1,ty+1) not in walls:
                    curDis = pathCost + ((abs((tx+1) - 0) + abs(ty - 0)) * 1.3)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx+1, ty)
                # Evaluating moving up
                if len(seen) > 0 and (tx,ty-1) not in dead|seen and (tx,ty,tx+1,ty) not in walls:
                    curDis = pathCost + ((abs(tx - 0) + abs((ty-1) - 0)) * 0.7)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx, ty-1)
                # Evaluating moving left
                if len(seen) > 0 and (tx-1,ty) not in dead|seen and (tx,ty,tx,ty+1) not in walls:
                    curDis = pathCost + ((abs((tx-1) - 0) + abs(ty - 0)) * 0.7)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx-1, ty)
                
                # Do best possible move if there is one, or backtrack if not
                if newMove:
                    plan.append(bestMove)
                else:
                    # If we cannot advance or are not pathing currently, backtrack
                    dead |= {(tx,ty)}
                    plan = plan[:-1]

                # Increment current path cost
                pathCost += 1

            # Need to redo pathing, consider temporary walls
            if temp:
                manDis = float('inf')
                newMove = False
                # Evaluating moving down
                if len(seen) > 0 and (tx,ty+1) not in tempDead|seen|tempWalls and (tx,ty+1,tx+1,ty+1) not in walls:
                    curDis = tempCost + ((abs(tx - 0) + abs((ty+1) - 0)) * 1.3)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx, ty+1)
                # Evaluating moving right
                if len(seen) > 0 and (tx+1,ty) not in tempDead|seen|tempWalls and (tx+1,ty,tx+1,ty+1) not in walls:
                    curDis = tempCost + ((abs((tx+1) - 0) + abs(ty - 0)) * 1.3)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx+1, ty)
                # Evaluating moving up
                if len(seen) > 0 and (tx,ty-1) not in tempDead|seen|tempWalls and (tx,ty,tx+1,ty) not in walls:
                    curDis = tempCost + ((abs(tx - 0) + abs((ty-1) - 0)) * 0.7)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx, ty-1)
                # Evaluating moving left
                if len(seen) > 0 and (tx-1,ty) not in tempDead|seen|tempWalls and (tx,ty,tx,ty+1) not in walls:
                    curDis = tempCost + ((abs((tx-1) - 0) + abs(ty - 0)) * 0.7)
                    if curDis < manDis:
                        newMove = True
                        manDis = curDis
                        bestMove = (tx-1, ty)
                
                # Do best possible move if there is one, or backtrack if not
                if newMove:
                    plan.append(bestMove)
                else:
                    # If we cannot advance or are not pathing currently, backtrack
                    tempDead |= {(tx,ty)}
                    plan = plan[:-1]

                # Increment current path cost
                tempCost += 1
        
        # Issue a command for the latest plan
        print("toward %s %s" % (plan[-1][0]+0.5, plan[-1][1]+0.5), flush=True)
        
    print("", flush=True)
    time.sleep(0.125)

"""
Group 9 - Isabelle S. Brown
CS 660 - Artificial Intelligence
Final Project - Maze Game
11/28/23
"""