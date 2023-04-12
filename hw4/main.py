import copy

class OSPF_Info():
    def __init__(self, link_state, when, From=None):
        self.link_state = copy.deepcopy(link_state)
        self.when = when
        self.From = From
        self.isloaded = False

class OSPF_Router():
    def __init__(self, index, link_state):
        self.index = index
        self.topology = {index: OSPF_Info(link_state, 0)}
        self.dist = copy.deepcopy(link_state)

    def flood(self, adj, routers, when):
        n = len(adj)
        for i in self.topology.keys():
            if self.topology[i].when != when:
                continue
            self.topology[i].isflooded = True
            src = self.topology[i].From
            data = (i, self.topology[i].link_state)
            for To in range(n):
                if To is self.index or To is src:
                    continue
                if adj[self.index][To] < 999:
                    routers[To].recv(self.index, data, when)
        if len(self.topology) == n:
            return True
        return False
    
    def recv(self, From, data, when):
        Whose = data[0]
        link_state = data[1]
        if Whose not in self.topology:
            self.topology[Whose] = OSPF_Info(link_state, when + 1, From)
    
    def dijkstra(self):
        n = len(self.dist)
        tag = [0 for i in range(n)]
        for i in range(n - 1):
            min = 999
            for j in range(n):
                if tag[j] == 0 and self.dist[j] < min:
                    min = self.dist[j]
                    u = j
            tag[u] = 1
            for v in range(n):
                if self.topology[u].link_state[v] < 999 and self.dist[v] > self.dist[u] + self.topology[u].link_state[v]:
                    self.dist[v] = self.dist[u] + self.topology[u].link_state[v]
    
def run_ospf(link_cost: list) -> tuple[list, list]:
    routers = []
    adj = copy.deepcopy(link_cost)
    n = len(adj)
    for i in range(n):
        routers.append(OSPF_Router(i, adj[i]))
    
    ans2 = []
    when = 0
    while True:
        finish = True
        for router in routers:
            finish = finish & router.flood(adj, routers, when)
        when += 1
        tmp2 = []
        for To in range(n):
            topology = routers[To].topology
            for Whose, info in topology.items():
                if info.From is None or info.isloaded is True:
                    continue
                topology[Whose].isloaded = True
                From = info.From
                tmp2.append((From, Whose, To))
        ans2 += sorted(tmp2)
        if finish:
            break
    
    ans1 = []
    for router in routers:
        router.dijkstra()
        ans1.append(router.dist)
    return (ans1, ans2)


class RIP_Router():
    def __init__(self, index, dist_vector):
        self.index = index
        self.dist_vector = None
        self.new_dist_vector = copy.deepcopy(dist_vector)
        self.when = 0

    def renew(self):
        self.dist_vector = copy.deepcopy(self.new_dist_vector)

    def flood(self, adj, routers, when):
        n = len(adj)
        tmp = []
        if self.when < when:
            return tmp
        for i in range(n):
            if i is self.index:
                continue
            if adj[self.index][i] < 999:
                routers[i].recv(self.dist_vector, when)
                tmp.append((self.index, i))
        return tmp

    def recv(self, data, when):
        for i in range(len(self.dist_vector)):
            if i is self.index:
                continue
            if self.new_dist_vector[i] > data[self.index] + data[i]:
                self.new_dist_vector[i] = data[self.index] + data[i]
                self.when = when + 1
        
def run_rip(link_cost: list) -> tuple[list, list]:
    routers = []
    adj = copy.deepcopy(link_cost)
    n = len(adj)
    for i in range(n):
        routers.append(RIP_Router(i, adj[i]))
    
    when = 0
    ans2 = []
    while True:
        for router in routers:
            router.renew()
        tmp = []
        for router in routers:
            tmp += router.flood(adj, routers, when)
        when += 1
        ans2 += sorted(tmp)
        if len(tmp) == 0:
            break
        
    ans1 = []
    for router in routers:
        ans1.append(router.dist_vector)
    
    return (ans1, ans2)