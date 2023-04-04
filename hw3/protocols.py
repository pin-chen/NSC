import copy
import random

def print_history(setting, packets_status, actions):
    for h in range(setting.host_num):
        print('    ',end='')
        for tmp in packets_status[h]:
            print(tmp,end='')
        print()
        print('h{}: '.format(h),end='')
        for tmp in actions[h]:
            print(tmp,end='')
        print()

def rate_caculate(setting, actions):
    tmp = 0
    idle_time = 0
    success_time = 0
    collision_time = 0
    for t in range(setting.total_time):
        isidle = True
        for h in range(setting.host_num):
            if actions[h][t] == '.':
                continue
            if isidle:
                tmp += 1
            isidle = False
            if actions[h][t] == '|':
                collision_time += tmp
                tmp = 0
                break
            elif actions[h][t] == '>':
                success_time += tmp
                tmp = 0
                break
        if isidle:
            idle_time += 1
    collision_time += tmp
    success_rate = success_time / setting.total_time
    idle_rate = idle_time / setting.total_time
    collision_rate = collision_time / setting.total_time
    return success_rate, idle_rate, collision_rate

def aloha(setting, show_history=False):
    packets = setting.gen_packets()
    packets_init = [' ' for i in range(setting.total_time)]
    actions_init = ['.' for i in range(setting.total_time)]
    packets_status = [copy.deepcopy(packets_init) for i in range(setting.host_num)]
    actions = [copy.deepcopy(actions_init) for i in range(setting.host_num)]
    queue = [0 for i in range(setting.host_num)]
    status = [-1 for i in range(setting.host_num)]
    collision = [False for i in range(setting.host_num)]
    wait_time = [0 for i in range(setting.host_num)]

    # -1 idle, >0 sending, 0 stop
    for h in range(setting.host_num):
        for p in packets[h]:
            packets_status[h][p] = 'V'

    for t in range(setting.total_time):
        for h in range(setting.host_num):
            if packets_status[h][t] == 'V':
                queue[h] += 1
            if status[h] != -1:
                continue
            if wait_time[h] > 0:
                wait_time[h] -= 1
                continue
            if queue[h] == 0:
                continue
            status[h] = setting.packet_time - 1
            queue[h] -= 1

        for h in range(setting.host_num):
            if status[h] == -1:
                continue
            if status[h] == 0:
                actions[h][t] = '>'
            elif status[h] == setting.packet_time - 1:
                actions[h][t] = '<'
            else:
                actions[h][t] = '-'
            status[h] -= 1

        for h in range(setting.host_num):
            if collision[h] == True:
                continue
            if actions[h][t] == '.':
                continue
            for other in range(setting.host_num):
                if h == other:
                    continue
                if actions[other][t] != '.':
                    collision[h] = True
                    break
        
        for h in range(setting.host_num):
            if actions[h][t] == '>' and collision[h] == True:
                actions[h][t] = '|'
                collision[h] = False
                wait_time[h] = random.randint(0, setting.max_colision_wait_time)
                queue[h] += 1

    if show_history:
        # Show the history of each host
        print_history(setting, packets_status, actions)
    return rate_caculate(setting, actions)
    

def slotted_aloha(setting, show_history=False):
    packets = setting.gen_packets()
    packets_init = [' ' for i in range(setting.total_time)]
    actions_init = ['.' for i in range(setting.total_time)]
    packets_status = [copy.deepcopy(packets_init) for i in range(setting.host_num)]
    actions = [copy.deepcopy(actions_init) for i in range(setting.host_num)]
    queue = [0 for i in range(setting.host_num)]
    status = [-1 for i in range(setting.host_num)]
    collision = [False for i in range(setting.host_num)]
    isresend = [False for i in range(setting.host_num)]

    # -1 idle, >0 sending, 0 stop
    for h in range(setting.host_num):
        for p in packets[h]:
            packets_status[h][p] = 'V'

    for t in range(setting.total_time):
        for h in range(setting.host_num):
            if packets_status[h][t] == 'V':
                queue[h] += 1
            if status[h] != -1:
                continue
            if t % setting.packet_time != 0:
                continue
            if queue[h] == 0:
                continue
            if isresend[h] and random.random() > setting.p_resend:
                continue
            isresend[h] = False
            status[h] = setting.packet_time - 1
            queue[h] -= 1

        for h in range(setting.host_num):
            if status[h] == -1:
                continue
            if status[h] == 0:
                actions[h][t] = '>'
            elif status[h] == setting.packet_time - 1:
                actions[h][t] = '<'
            else:
                actions[h][t] = '-'
            status[h] -= 1

        for h in range(setting.host_num):
            if collision[h] == True:
                continue
            if actions[h][t] == '.':
                continue
            for other in range(setting.host_num):
                if h == other:
                    continue
                if actions[other][t] != '.':
                    collision[h] = True
                    break
        
        for h in range(setting.host_num):
            if actions[h][t] == '>' and collision[h] == True:
                actions[h][t] = '|'
                collision[h] = False
                isresend[h] = True
                queue[h] += 1

    if show_history:
        # Show the history of each host
        print_history(setting, packets_status, actions)
    return rate_caculate(setting, actions)

def csma(setting, show_history=False):
    packets = setting.gen_packets()
    packets_init = [' ' for i in range(setting.total_time)]
    actions_init = ['.' for i in range(setting.total_time)]
    packets_status = [copy.deepcopy(packets_init) for i in range(setting.host_num)]
    actions = [copy.deepcopy(actions_init) for i in range(setting.host_num)]
    queue = [0 for i in range(setting.host_num)]
    status = [-1 for i in range(setting.host_num)]
    collision = [False for i in range(setting.host_num)]
    wait_time = [0 for i in range(setting.host_num)]

    # -1 idle, >0 sending, 0 stop
    for h in range(setting.host_num):
        for p in packets[h]:
            packets_status[h][p] = 'V'

    for t in range(setting.total_time):
        '''
        print("    ",end="")
        for i in range(t):
            print(" ",end='')
        print("$")
        print_history(setting, packets_status, actions)
        print("\n------------------------------------------------------\n")
        '''
        for h in range(setting.host_num):
            if packets_status[h][t] == 'V':
                queue[h] += 1
            if status[h] != -1:
                continue
            if wait_time[h] > 0:
                wait_time[h] -= 1
                continue
            if queue[h] == 0:
                continue
            cs = False
            for other in range(setting.host_num):
                if h == other:
                    continue
                if t - setting.link_delay - 1 < 0:
                    continue
                if actions[other][t - setting.link_delay - 1] != '.' and actions[other][t - setting.link_delay - 1] != '>':
                    cs = True
                    break
            if cs:
                wait_time[h] = random.randint(0, setting.max_colision_wait_time)
                continue
            status[h] = setting.packet_time - 1
            queue[h] -= 1

        for h in range(setting.host_num):
            if status[h] == -1:
                continue
            if status[h] == 0:
                actions[h][t] = '>'
            elif status[h] == setting.packet_time - 1:
                actions[h][t] = '<'
            else:
                actions[h][t] = '-'
            status[h] -= 1

        for h in range(setting.host_num):
            if collision[h] == True:
                continue
            if actions[h][t] == '.':
                continue
            for other in range(setting.host_num):
                if h == other:
                    continue
                if actions[other][t] != '.':
                    collision[h] = True
                    break
        
        for h in range(setting.host_num):
            if actions[h][t] == '>' and collision[h] == True:
                actions[h][t] = '|'
                collision[h] = False
                wait_time[h] = random.randint(0, setting.max_colision_wait_time)
                queue[h] += 1

    if show_history:
        # Show the history of each host
        print_history(setting, packets_status, actions)
    return rate_caculate(setting, actions)

def csma_cd(setting, show_history=False):
    packets = setting.gen_packets()
    packets_init = [' ' for i in range(setting.total_time)]
    actions_init = ['.' for i in range(setting.total_time)]
    packets_status = [copy.deepcopy(packets_init) for i in range(setting.host_num)]
    actions = [copy.deepcopy(actions_init) for i in range(setting.host_num)]
    queue = [0 for i in range(setting.host_num)]
    status = [-1 for i in range(setting.host_num)]
    collision = [False for i in range(setting.host_num)]
    wait_time = [0 for i in range(setting.host_num)]

    # -1 idle, >0 sending, 0 stop
    for h in range(setting.host_num):
        for p in packets[h]:
            packets_status[h][p] = 'V'

    for t in range(setting.total_time):
        '''
        print("    ",end="")
        for i in range(t):
            print(" ",end='')
        print("$")
        print_history(setting, packets_status, actions)
        print("\n------------------------------------------------------\n")
        '''
        for h in range(setting.host_num):
            if packets_status[h][t] == 'V':
                queue[h] += 1
            if status[h] != -1:
                continue
            if wait_time[h] > 0:
                wait_time[h] -= 1
                continue
            if queue[h] == 0:
                continue
            cs = False
            for other in range(setting.host_num):
                if h == other:
                    continue
                if t - setting.link_delay - 1 < 0:
                    continue
                if actions[other][t - setting.link_delay - 1] != '.' and actions[other][t - setting.link_delay - 1] != '>':
                    cs = True
                    break
            if cs:
                wait_time[h] = random.randint(0, setting.max_colision_wait_time)
                continue
            status[h] = setting.packet_time - 1
            queue[h] -= 1

        for h in range(setting.host_num):
            if status[h] == -1:
                continue
            if status[h] == 0:
                actions[h][t] = '>'
            elif status[h] == setting.packet_time - 1:
                actions[h][t] = '<'
            else:
                actions[h][t] = '-'
            status[h] -= 1

        for h in range(setting.host_num):
            if collision[h] == True:
                continue
            if actions[h][t] == '.':
                continue
            for other in range(setting.host_num):
                if h == other:
                    continue
                if t - setting.link_delay - 1 < 0:
                    continue
                if actions[other][t - setting.link_delay - 1] != '.' and actions[other][t - setting.link_delay - 1] != '>':
                    collision[h] = True
                    break
        
        for h in range(setting.host_num):
            if collision[h] == True:
                actions[h][t] = '|'
                collision[h] = False
                wait_time[h] = random.randint(0, setting.max_colision_wait_time)
                queue[h] += 1
                status[h] = -1

    if show_history:
        # Show the history of each host
        print_history(setting, packets_status, actions)
    return rate_caculate(setting, actions)