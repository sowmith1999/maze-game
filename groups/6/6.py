import sys
import select
import time
import copy
import queue

# Constants for initial positions
x, y = 0.5, 0.5
home_x, home_y = 0, 0
goal_x, goal_y = 10, 10

# last tile "reached" (i.e., being close enough to center)
ty = -1
tx = -1

# Wall manager class for handling walls
class WallManager:
    def __init__(self):
        self.processed = set()
        self.curr_walls = set()
        self.initialize_walls()

    def initialize_walls(self):
        for i in range(11):
            self.curr_walls.update({
                (i, 0, i, 0), (i, 11, i + 1, 11),
                (0, i, 0, i + 1), (11, i, 11, i + 1)
            })

    def update_walls(self):
        self.processed.update(self.curr_walls)
        self.curr_walls.clear()

    @staticmethod
    def up(x, y):
        return (x, y, x + 1, y)

    @staticmethod
    def down(x, y):
        return (x, y + 1, x + 1, y + 1)

    @staticmethod
    def right(x, y):
        return (x + 1, y, x + 1, y + 1)

    @staticmethod
    def left(x, y):
        return (x, y, x, y + 1)

wall_manager = WallManager()
curr_plan = []
just_in_case = []
idx = 0
traversed = set()
dead = set()

# Plan class for handling robot movements
class Plan:
    def __init__(self, x, y, goal_x, goal_y):
        self.x = x
        self.y = y
        self.goal_x = goal_x
        self.goal_y = goal_y
        self.plan = []
        self.cost = 0

    def actions(self):
        actions_set = []
        if (self.x + 1, self.y) not in dead | traversed and wall_manager.right(
            self.x, self.y
        ) not in wall_manager.processed:
            actions_set.append((self.x + 1, self.y))  # move right
        if (self.x - 1, self.y) not in dead | traversed and wall_manager.left(
            self.x, self.y
        ) not in wall_manager.processed:
            actions_set.append((self.x - 1, self.y))  # move left
        if (self.x, self.y + 1) not in dead | traversed and wall_manager.down(
            self.x, self.y
        ) not in wall_manager.processed:
            actions_set.append((self.x, self.y + 1))  # move down
        if (self.x, self.y - 1) not in dead | traversed and wall_manager.up(
            self.x, self.y
        ) not in wall_manager.processed:
            actions_set.append((self.x, self.y - 1))  # move up
        return actions_set

    def move(self, action):
        new_plan = copy.deepcopy(self)
        new_plan.x, new_plan.y = action
        new_plan.cost += 1
        new_plan.plan.append(action)
        return new_plan

    def successors(self):
        return [self.move(action) for action in self.actions()]

    def goal_distance(self):
        return abs(self.goal_x - self.x) + abs(self.goal_y - self.y)

    def eval(self):
        return self.cost + self.goal_distance()

    def __lt__(self, other):
        return self.eval() < other.eval()

# Planning function using A* algorithm
def planning(tup):
    global dead, goal_x, goal_y
    planner = Plan(tup[0], tup[1], goal_x, goal_y)
    checked = set()
    frontier = queue.PriorityQueue()
    frontier.put(planner)
    while not frontier.empty():
        current_speculation = frontier.get()
        if current_speculation.goal_distance() == 0:
            return current_speculation

        checked |= {(current_speculation.x, current_speculation.y)}

        for successor in current_speculation.successors():
            if (successor.x, successor.y) not in checked:
                frontier.put(successor)
    return None

def back_track():
    global just_in_case
    next_step = just_in_case[0]
    print("toward %s %s" % (next_step[0] + 0.5, next_step[1] + 0.5), flush=True)

def flip_goal():
    global home_x, home_y, goal_y, goal_x
    home_x, goal_x = goal_x, home_x
    home_y, goal_y = goal_y, home_y

def to_follow():
    global idx, curr_plan
    idx += 1
    next_step = curr_plan[idx]
    print("toward %s %s" % (next_step[0] + 0.5, next_step[1] + 0.5), flush=True)

# Main execution function
def execute_robot():
    global tx
    global ty
    global curr_plan
    global just_in_case
    global idx
    global traversed
    global dead

    print("himynameis group6", flush=True)
    time.sleep(0.5)
    think = 10
    atbottom = False

    while True:
    # while there is new input on stdin:
        while select.select(
            [
                sys.stdin,
            ],
            [],
            [],
            0.0,
        )[0]:
            # read and process the next 1-line observation
            obs = sys.stdin.readline()
            obs = obs.split(" ")
            if obs == []:
                pass
            elif obs[0] == "bot":
                # update our own position
                x = float(obs[1])
                y = float(obs[2])
                # print(f"comment at {x} and {y}")
                if x > 9 and y > 9 and atbottom == False:
                    flip_goal()
                    atbottom = True
                # update when inside the tiles or something like that
                if (int(x) != tx or int(y) != ty) and (
                    (x - (int(x) + 0.5)) ** 2 + (y - (int(y) + 0.5)) ** 2
                ) ** 0.5 < 0.2:
                    tx = int(x)
                    ty = int(y)
                    # print("comment now at tile: %s %s" % (tx,ty), flush=True)
            elif obs[0] == "wall":
                # print("comment wall: %s %s %s %s" % (obs[1],obs[2],obs[3],obs[4]), flush=True)
                x0 = int(float(obs[1]))
                y0 = int(float(obs[2]))
                x1 = int(float(obs[3]))
                y1 = int(float(obs[4]))
                if (x0, y0, x1, y1) not in wall_manager.processed:
                    wall_manager.curr_walls |= {
                        (x0, y0, x1, y1)
                    }  

        if think > 0:
            think -= 1
            pass

        if len(curr_plan) == 0 and think == 0:
            traversed = {(tx, ty)}
            wall_manager.update_walls()
            planner = planning((tx, ty))
            # initial plan
            if planner is not None and len(planner.plan) > 0:
                curr_plan = [(tx, ty)] + planner.plan
                to_follow()

        if len(curr_plan) > 0 and len(just_in_case) > 0 and just_in_case[0] == (tx, ty):
            just_in_case = just_in_case[1:]
            if len(just_in_case) > 0:
                back_track()
            elif curr_plan[idx] == (tx, ty): 
                to_follow()

        elif len(curr_plan) > 0 and curr_plan[idx] == (tx, ty):
            if (curr_plan[idx][0] == goal_x) and (curr_plan[idx][1] == goal_y):
                flip_goal()
                curr_plan = []
                idx = 0
                traversed = set()
                continue

            if (
                len(wall_manager.curr_walls) == 0
            ): 
                traversed |= {(tx, ty)}
                to_follow()
            else:
                fault_index = 0
                for i in range(idx, len(curr_plan) - 1):
                    if (
                        (
                            (curr_plan[i + 1][0] - curr_plan[i][0] == 1)
                            and wall_manager.right(curr_plan[i][0], curr_plan[i][1]) in wall_manager.curr_walls
                        )
                        or (
                            (curr_plan[i + 1][1] - curr_plan[i][1] == 1)
                            and wall_manager.down(curr_plan[i][0], curr_plan[i][1]) in wall_manager.curr_walls
                        )
                        or (
                            (curr_plan[i + 1][0] - curr_plan[i][0] == -1)
                            and wall_manager.left(curr_plan[i][0], curr_plan[i][1]) in wall_manager.curr_walls
                        )
                        or (
                            (curr_plan[i + 1][1] - curr_plan[i][1] == -1)
                            and wall_manager.up(curr_plan[i][0], curr_plan[i][1]) in wall_manager.curr_walls
                        )
                    ):
                        fault_index = i
                        break
                wall_manager.update_walls()
                if fault_index == 0:  
                    to_follow()
                else:  
                    while True:
                        planner = planning(
                            curr_plan[idx]
                        )  
                        if planner is not None:
                            curr_plan = curr_plan[
                                : idx + 1 :
                            ]  
                            curr_plan = curr_plan + planner.plan  
                            break
                        else: 
                            while True:
                                current_step = curr_plan[idx]
                                bt_planner = Plan(current_step[0], current_step[0][1])
                                if (
                                    len(bt_planner.actions()) > 0 or idx == 0
                                ): 
                                    break
                                idx -= 1
                                just_in_case.append[
                                    curr_plan[idx]
                                ]  
                                dead |= {current_step}
                    if (tx, ty) == curr_plan[idx]:
                        to_follow()
                    elif len(just_in_case) > 0:
                        back_track()
        print("", flush=True)
        time.sleep(0.1)
execute_robot()