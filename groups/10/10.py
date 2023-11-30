import sys
import select
import time
import random

def initialize():
    data = {
        'x': 0.5,
        'y': 0.5,
        'home_x': 0,
        'home_y': 0,
        'tx': -1,
        'ty': -1,
        'walls': set([(i, 0, i, 0) for i in range(11)] +
                     [(i, 11, i+1, 11) for i in range(11)] +
                     [(0, i, 0, i+1) for i in range(11)] +
                     [(11, i, 11, i+1) for i in range(11)]),
        'plan': [],
        'seen': set(),
        'dead': set(),
        'flag': True,
        'bestMove': (0, 0),
        'p_flag': False
    }
    return data

def process_input(data):
    while select.select([sys.stdin,],[],[],0.0)[0]:
        obs = sys.stdin.readline().split(" ")
        if not obs: 
            continue
        if obs[0] == "bot":
            data['x'] = float(obs[1])
            data['y'] = float(obs[2])
            if ((int(data['x']) != data['tx'] or int(data['y']) != data['ty']) and
                ((data['x']-(int(data['x'])+0.5))**2 + (data['y']-(int(data['y'])+0.5))**2)**0.5 < 0.2):
                data['tx'] = int(data['x'])
                data['ty'] = int(data['y'])
                if data['plan'] == []:
                    data['plan'] = [(data['tx'], data['ty'])]
                    data['home_x'] = data['tx']
                    data['home_y'] = data['ty']
                    data['seen'] = set(data['plan'])
        elif obs[0] == "wall":
            x0 = int(float(obs[1]))
            y0 = int(float(obs[2]))
            x1 = int(float(obs[3]))
            y1 = int(float(obs[4]))
            data['walls'].add((x0, y0, x1, y1))
    return data

def is_valid_move(data, tx, ty):
    # check if the move is valid
    if (tx, ty) in data['dead'] | data['seen']:
        return False

    # check if the move is valid
    for wall in data['walls']:
        # get the coordinates of the wall
        x0, y0, x1, y1 = wall
        # check if the move is valid
        if x0 == x1:  # wall is vertical
            if min(y0, y1) <= ty < max(y0, y1) and min(data['tx'], tx) < x0 <= max(data['tx'], tx):
                return False
        elif y0 == y1:  # wall is horizontal
            if min(x0, x1) <= tx < max(x0, x1) and min(data['ty'], ty) < y0 <= max(data['ty'], ty):
                return False

    return True

def calculate_distance(data, tx, ty, bias=1.0):
    # calculate the distance between the next position and the target position
    return abs(data['tx'] - tx) + abs(data['ty'] - ty) * bias

def calculate_distance2(data, next_x, next_y, target_x, target_y, bias):
    # calculate the distance between the next position and the target position
    dx = abs(next_x - target_x)
    dy = abs(next_y - target_y)
    return dx + dy * bias  # return the distance

def heruistic(data, manDis, newMove, bestMove):
    # target_x, target_y = 10, 10  # the target position
    if len(data['seen']) > 0:
        directions = [(0, 1, 1.0), (1, 0, 1.0), (0, -1, 1.5), (-1, 0, 1.0)]
        for dx, dy, bias in directions:
            next_x, next_y = data['tx'] + dx, data['ty'] + dy
            if (next_x, next_y) not in data['dead'] | data['seen'] and is_valid_move(data, next_x, next_y):


                """
                ##############################################
                ############## modify bias here ##############
                ##############################################
                """
                # bias = -0.5
                curDis = calculate_distance(data, next_x, next_y, bias)
                if curDis < manDis:
                    manDis, newMove, bestMove = curDis, True, (next_x, next_y)
    return manDis, newMove, bestMove


def update_plan_and_command(data):
    bestMove = None
    newMove = False
    data['p_flag'] = False

    if len(data['plan']) > 0 and data['plan'][-1] == (data['tx'], data['ty']):
        data['seen'].add((data['tx'], data['ty']))  # Marking the tile as seen
        if (data['plan'][-1][0] == data['home_x']) and (data['plan'][-1][1] == data['home_y']):
            if (10, 10) in data['dead']:
                data['dead'].remove((10, 10))
            data['seen'] = {(data['tx'], data['ty'])}

        if (data['plan'][-1][0] == 10) and (data['plan'][-1][1] == 10):
            # Mark all other tiles dead, this is our final path, backtrack
            planset = set(data['plan'])
            data['dead'] = set()
            for i in range(11):
                for j in range(11):
                    if (i, j) not in planset:
                        data['dead'].add((i, j))

            data['seen'] = set()

        manDis = float('inf')
        newMove = False

        # duplicate data
        data1 = data.copy()
        manDis, newMove, bestMove = heruistic(data1, manDis, newMove, bestMove)

        if newMove:
            data['flag'] = True
            data['plan'].append(bestMove)
        else:
            data['dead'].add((data['tx'], data['ty']))
            if data['plan']:
                data['plan'].pop()

        if data['plan']:
            data['p_flag'] = True

    return data, bestMove, newMove

def move_command(data):
    if data['p_flag']:
        print("toward %s %s" % (data['plan'][-1][0] + 0.5, data['plan'][-1][1] + 0.5), flush=True)

def deployWall(data, percent):
    """
    Attempts to deploy a wall in all directions based on a given probability.
    
    :param data: The current state of the game.
    :param percent: The probability (0-100) of deploying a wall in each direction.
    """
    directions = ['u', 'd', 'l', 'r']  # up, down, left, right

    for direction in directions:
        if random.randint(1, 100) <= percent:
            #if can_deploy_wall(data, direction):
            print(f"block {data['tx']} {data['ty']} {direction}", flush=True)

def main():
    data = initialize()
    print("himynameis dfs-bot", flush=True)
    time.sleep(0.25)

    while True:
        data = process_input(data)
        data, bestMove, newMove = update_plan_and_command(data)
        move_command(data)
        print("", flush=True)
        if data['flag']:
            data['flag'] = False
            #deployWall(data, 100)
        time.sleep(0.125)

if __name__ == "__main__":
    main()