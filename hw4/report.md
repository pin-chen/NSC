# NSC HW 4

109550206 陳品劭

## For OSPF

### 1. Show how you implement the flooding algorithm. (Do not just use direct transmission from all nodes to all other nodes) (10%)

對於每一個 Router 而言，會傳 link state 給相鄰的 Router (link cost < 999) (flood) ，且收到其他 Router 的 link state 時，確認自己是否已經存過了 (收到過) ：是，不做事；否，forward 給相鄰的 Router (link cost < 999) (flood) 。

實作上，依照順序持續重複確認每個 Router 自己存著的每一個 link state 是否已經 flood 過，是，不做事；否，forward 給相鄰的 Router (link cost < 999) (flood) 。另外需紀錄 link state 是在哪一輪存著的，避免同一輪 forward 兩次或以上。

### 2. What factor will affect the convergence time of OSPF? (10%)

Topology 中，相距最遠的兩個 Router 的距離會影響收斂時間。因為只要 Router 收到 Topology 中所有 Router 的 link state ，即可透過 dijkstra 計算最短路徑，並安排路游，而 Router 收到 Topology 中所有 Router 的 link state 的時間取決於最遠那個傳來所需的時間。

另外 dijkstra 的時間複雜度為 O(n^2) ，因此 Router 的數量也有影響。以及一些基本因素：網速、Router 效能、some waiting time of OSPF 等。

## For RIP

### 1. Show how you implement the distance vector exchange mechanism. (10%)

對於每一個 Router 而言，更新自己的 distance vector 時，將更新完的傳給相鄰的 Router (link cost < 999) (flood) ，且收到其他 Router 的 distance vector 時，將其跟自己與該 Router 的 cost 加上去，再與自己的 distance vector 比對，當有更小值時，更新自己的 distance vector 。

實作上，依照順序持續重複確認自己的 distance vector 是否有更新：是，傳給相鄰的 Router (link cost < 999) (flood)；否，不做事。而收到 distance vector ，依照上述比對，發現要更新時，先更新至一個 temp distance vector ，以避免更新完的 distance vector 被同輪 Forward 出去，並於每一輪開始前，先對所有 Router 更新 distance vector from temp distance vector 。

### 2. What factor will affect the convergence time of RIP? (10%)

Router 的數量以及連線 (Link) 的數量會影響收斂時間。因為當有越多 Router 和 Link ，會產生更多 Router 上 distance vector 的變動，且每一次變動會影響的 Router 數量同樣更多。也就表示網路拓譜的樣貌都會對其有一定影響，以及一些基本因素：網速、Router 效能、 distance vector exchange waiting time等。
