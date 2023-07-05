# NSC HW 7

109550206 陳品劭

### 1. When h1 ping h2, what will happen?

ARP:

h1 sent request

h2 received and replied

h1 received the reply

ICMP:

h1 sent request

h2 received and replied

h1 received the reply

![image-20230605022930888](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605022930888.png)

![image-20230605023025311](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605023025311.png)

![image-20230605023046581](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605023046581.png)

### 2. When h1 ping h3, what will happen?

ARP:

h1 sent request

h3 received and replied

h1 received the reply

ICMP:

h1 sent request

h3 received and replied

s1 drop the reply

h1 did not receive the reply

![image-20230605023454342](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605023454342.png)

![image-20230605023511134](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605023511134.png)

![image-20230605023531524](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605023531524.png)

### 3. When h3 ping h2, what will happen?

ARP:

h3 sent request

h2 received and replied

h3 received the reply

ICMP:

h3 sent request

s1 drop the request

h2 id not receive the request

![image-20230605023857160](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605023857160.png)

![image-20230605023931108](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605023931108.png)

![image-20230605023943711](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605023943711.png)

### 4. When h1 ping h5, what will happen?

ARP:

h1 sent request

h1 sent request

h1 sent request

h5 did not receive the request

![image-20230605024253469](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605024253469.png)

![image-20230605024311921](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605024311921.png)

![image-20230605024324590](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605024324590.png)

#### --------------------------------------------------(gre)------------------------------------------------------------

### 5. When h1 ping h5, what will happen?

ARP:

h1 sent request

h5 received and replied

h1 received the reply

ICMP:

h1 sent request

h5 received and replied

h1 received the reply

![image-20230605024610542](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605024610542.png)

![image-20230605024625549](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605024625549.png)

![image-20230605024639690](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605024639690.png)

### 6. When h1 ping h7, what will happen?

ARP:

h1 sent request

h7 received and replied

h1 received the reply

ICMP:

h1 sent request

h7 received and replied

s2 drop the reply

h1 did not receive the reply

![image-20230605024955528](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605024955528.png)

![image-20230605025016297](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605025016297.png)

![image-20230605025035949](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605025035949.png)

### 7. When h7 ping h1, what will happen?

ARP:

h7 sent request

h1 received and replied

h7 received the reply

ICMP:

h7 sent request

s2 drop the request

h1 did not receive the request

![image-20230605025258373](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605025258373.png)

![image-20230605025311700](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605025311700.png)

![image-20230605025324137](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605025324137.png)



### 8. If the packet in question 6 or 7 is dropped in some part of the network, are the outcome and explanation the same as that of question 4? (use screenshot to prove)

不同，因為在 Q4 時兩者不連通，所以連 ARP 都收不到，因此會判斷成 unreachable，而 Q6, Q7 則是連通的且 ARP 收得到，因此他只覺得是 packet loss 不是 unreachable。

![image-20230605024253469](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605024253469.png)

![image-20230605024955528](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605024955528.png)

![image-20230605025258373](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230605025258373.png)

### 9. Change filter_table2 rule

- From: packets coming from port_3 or port_4 will be dropped, while other packets will be allowed to pass.
  To: packets coming from port_1 or port_2 will be allowed to pass, while other packets will be dropped.
- Will the outcome of questions 5, 6, and 7 differ? (no need to print screenshot)
  explain why or why not

Q5, Q6, Q7 都會 packet loss

因為 gre tunnel 對 switch 來講，在這個 case 中是 port_5，新舊規則差異於這個情境下是 port_5 進來的 ICMP 會不會 drop 掉。因此都會在經過 tunnel，被 switch drop 掉。
