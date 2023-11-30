import sys
import select
import time
import random
import copy
import queue

# Current exact position
current_x = 0.5
current_y = 0.5

# Last tile "reached" (i.e., being close enough to the center)
last_tile_y = -1
last_tile_x = -1

# Goal tile position
goal_x = 10
goal_y = 10

# Set of walls known
walls = set()
for i in range(0, 11):
    walls |= {(i, 0, i + 1, 0), (i, 11, i + 1, 11), (0, i, 0, i + 1), (11, i, 11, i + 1)}

# DFS tree
plan = []
visited_tiles = set()
dead_ends = set()

# Coin handling and temporary walls
coins = 0
temp_walls = set()
set_wall = 0

class AstarBot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.plan = []
        self.cost = 0

    def available_actions(self):
        action_set = []
        if (self.x, self.y - 1) not in dead_ends | visited_tiles and (self.x, self.y, self.x + 1, self.y) not in walls:
            action_set.append((self.x, self.y - 1))  # Move up
        if (self.x, self.y + 1) not in dead_ends | visited_tiles and (self.x, self.y + 1, self.x + 1, self.y + 1) not in walls:
            action_set.append((self.x, self.y + 1))  # Move down
        if (self.x - 1, self.y) not in dead_ends | visited_tiles and (self.x, self.y, self.x, self.y + 1) not in walls:
            action_set.append((self.x - 1, self.y))  # Move left
        if (self.x + 1, self.y) not in dead_ends | visited_tiles and (self.x + 1, self.y, self.x + 1, self.y + 1) not in walls:
            action_set.append((self.x + 1, self.y))  # Move right
        return action_set

    def generate_successors(self):
        successor_set = []
        for action in self.available_actions():
            successor_set.append(self.bot_move(action[0], action[1]))
        return successor_set

    def bot_move(self, new_x, new_y):
        bot_movement = copy.deepcopy(self)
        bot_movement.x = new_x
        bot_movement.y = new_y
        bot_movement.cost = self.cost + 1
        bot_movement.plan.append((new_x, new_y))
        return bot_movement

    def __lt__(self, other):
        return self.eval() < other.eval()

    def heurestics(self):
        distance = abs(goal_x - self.x) + abs(goal_y - self.y)
        return distance

    def eval(self):
        return self.cost + self.heurestics()

def path_planning(start_position):
    global dead_ends
    bot = AstarBot(start_position[0], start_position[1])
    frontier = queue.PriorityQueue()
    frontier.put(bot)
    while not frontier.empty():
        current_bot_movement = frontier.get()
        if current_bot_movement.heurestics() == 0:
            return current_bot_movement

        if len(current_bot_movement.available_actions()) == 0:
            dead_ends |= {(current_bot_movement.x, current_bot_movement.y)}
            continue

        for successor in current_bot_movement.generate_successors():
            frontier.put(successor)
    return None

def is_move_invalid(from_position, to_position):
    from_x, from_y = from_position[0], from_position[1]
    to_x, to_y = to_position[0], to_position[1]

    if (to_y - from_y == 1) and (from_x, from_y + 1, from_x + 1, from_y + 1) in walls:
        return True
    elif (to_x - from_x == 1) and (from_x + 1, from_y, from_x + 1, from_y + 1) in walls:
        return True
    elif (to_y - from_y == -1) and (from_x, from_y, from_x + 1, from_y) in walls:
        return True
    elif (to_x - from_x == -1) and (from_x, from_y, from_x, from_y + 1) in walls:
        return True
    else:
        return False
    
# Introduce ourselves, all friendly-like
print("himynameis DFS-bot", flush=True)

# Wait for some initial sense data
time.sleep(0.25)

while True:
    # While there is new input on stdin:
    while select.select([sys.stdin, ], [], [], 0.0)[0]:
        # Read and process the next 1-line observation
        observation = sys.stdin.readline()
        observation = observation.split(" ")
        if observation == []:
            pass
        elif observation[0] == "bot":
            # Update bot's position and coins count
            current_x = float(observation[1])
            current_y = float(observation[2])
            coins = int(observation[3])
            # Update the latest tile reached once firmly on the inside of the tile
            if (
                (int(current_x) != last_tile_x or int(current_y) != last_tile_y)
                and ((current_x - (int(current_x) + 0.5)) ** 2 + (current_y - (int(current_y) + 0.5)) ** 2) ** 0.5 < 0.2
            ):
                last_tile_x = int(current_x)
                last_tile_y = int(current_y)
                if plan == []:
                    plan = [(last_tile_x, last_tile_y)]
                    visited_tiles = set(plan)
        elif observation[0] == "wall":
            # Update set of walls
            x0 = int(float(observation[1]))
            y0 = int(float(observation[2]))
            x1 = int(float(observation[3]))
            y1 = int(float(observation[4]))
            walls |= {(x0, y0, x1, y1)}
        elif observation[0] == "twall":
            # Handle temporary walls
            if float(observation[3]) > 12 and set_wall == 0:
                x = int(float(observation[1]))
                y = int(float(observation[2]))
                temp_walls |= {(x, y)}

    # If we've achieved our goal, update our plan and issue a new command
    if len(plan) > 0 and plan[-1] == (last_tile_x, last_tile_y):
        if visited_tiles > set() or len(plan) == 1:
            visited_tiles |= {(last_tile_x, last_tile_y)}

        if abs(plan[-1][0] - plan[0][0]) == abs(plan[-1][1] - plan[0][1]) == 10:
            planset = set(plan)
            for i in range(11):
                for j in range(11):
                    if (i, j) not in planset:
                        dead_ends |= {(i, j)}
            visited_tiles = set()

        if len(visited_tiles) > 0:
            grid_bot = path_planning((last_tile_x, last_tile_y))
            if grid_bot is not None:
                plan.append((grid_bot.plan[0]))
            else:
                visited_tiles.discard(plan[-1])
                plan = plan[:-1]

        print("toward %s %s" % (plan[-1][0] + 0.5, plan[-1][1] + 0.5), flush=True)
    elif len(plan) > 1 and (is_move_invalid(plan[-2], plan[-1])):
        plan = plan[:-1]
    print("", flush=True)
    time.sleep(0.125)