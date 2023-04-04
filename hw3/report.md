# NSC HW 3

109550206 陳品劭

## Code Test

```python
test_setting = Setting(host_num=3, total_time=100, packet_num=4, max_colision_wait_time=20, p_resend=0.3, packet_size=3, link_delay=1, seed=109550206)
```

![image-20230404163413231](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230404163413231.png)

## Questions

### 1.

| ![](https://i.imgur.com/tFNkUyy.png)| ![](https://i.imgur.com/72g7kgi.png) | ![](https://i.imgur.com/1E4FnTp.png) |
| -------- | -------- | -------- |

### 2.

```
# max_colision_wait_time
self.max_colision_wait_time = host_num * self.packet_time * coefficient
# p_resend
self.p_resend = 1 / (host_num * coefficient)
```

### 3.

| ![](https://i.imgur.com/pc5tvEL.png) | ![](https://i.imgur.com/grtXw7z.png) | ![](https://i.imgur.com/xnP22PT.png) |
| ------------------------------------ | ------------------------------------ | ------------------------------------ |

由 Q1 與 Q3 圖表來看，可以發現隨著 Host Num 增加， Success Rate 不再有明顯遞減少、 Collision Rate  不再有明顯增加，針對 Aloha 、 CSMA 、CSMA/CD ，我們更改 max collision wait time 使其與 Host Num 、 Packet Time 成正相關，因為隨著 Host Num 增加，多個 Packet 同時碰撞機率變高，而 Packet Time 增加，占用網路時間增加，因此需要因此調整 max collision wait time ，使各 Host 有更多重送的時間可以選擇，避免更多的碰撞，而 Idle Rate 也因此趨於平緩。另外對於 Slotted Aloha 而言， Packet Time 已經變成 Slote Size 因此已經不具影響，剩下 Host Num ，我們會希望其越多時，對每個 Host 而言每個 Slote 重送的機率變小，使其減少碰撞，其影響於前述相同。

### 4.

| ![](https://i.imgur.com/QaPIbGU.png) | ![](https://i.imgur.com/3eQCCvu.png) | ![](https://i.imgur.com/Ia0gwSU.png) |
| ------------------------------------ | ------------------------------------ | ------------------------------------ |

Coefficient 增加表示 max collision wait time 增加，對每個 Host 而言可以選擇重送的時間變多會大量減少碰撞，並增加 Success，但過大的 wait time 反而會些許增加 idle time 。 

### 5.

| ![](https://i.imgur.com/2ppIniq.png) | ![](https://i.imgur.com/7snDwFk.png) | ![](https://i.imgur.com/odif5TN.png) |
| ------------------------------------ | ------------------------------------ | ------------------------------------ |

隨著 Packet Num 增加，增加網路使用率，原本可以 Idle 的時間變少，使 Success 、 Collosion 增加，而 CSMA 、 CSMA/CD 則因為 carrier sense 使其 Idle 較多變為 Success。

### 6.

| ![](https://i.imgur.com/SJWZS1E.png) | ![](https://i.imgur.com/m6qOzWZ.png) | ![](https://i.imgur.com/lrLdLej.png) |
| ------------------------------------ | ------------------------------------ | ------------------------------------ |

增加 Host Num 與前述情況相同，都是增加網路使用率，差異為 Packet 是由更多個 Host 來分配而已，原本可以 Idle 的時間變少，使 Success 、 Collision 增加，而 CSMA 、 CSMA/CD 則因為 carrier sense 使其 Idle 較多變為 Success。

### 7.

| ![](https://i.imgur.com/Vl6msAM.png) | ![](https://i.imgur.com/21GoD7G.png) | ![](https://i.imgur.com/2UjQaex.png) |
| ------------------------------------ | ------------------------------------ | ------------------------------------ |

增加 Packet Size 與前述情況相似，隨著每個 Paccket 占用網路時間變多，自然會減少 Idle ，並增加 Success 。

### 8.

| ![](https://i.imgur.com/6BRXxEe.png) | ![](https://i.imgur.com/5TRBLqW.png) | ![](https://i.imgur.com/3hUXiOO.png) |
| ------------------------------------ | ------------------------------------ | ------------------------------------ |

雖然 Packet Time 相同，但當其較多部分為 Link Delay 時，會影響到各 Host 檢測到其他 Packet 或 Collision 的時間，使其發生更多以為沒人在使用，卻碰撞的事情發生，且發現碰撞的時間也會因此延後，進而降低 Success ，增加 Collision，而因此發生更多 wait time 則會增加 Idle。
