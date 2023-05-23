# NSC HW 6

109550206 陳品劭

### HTTP/2 Under the Packet-dropping Condition

![image-20230523110236111](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230523110236111.png)

測試結果如上圖，stream ID = 1 應該會是去要隨機三個檔案位置出來，然後 stream ID = 3, 5, 7 在此次測試中分別為 file 07, 08, 06 ，而此環境會將 stream ID = 5 的 header 封包丟掉，因此 stream ID = 5 的物件應該不會成功送達，然後因為 HTTP 2.0 底下使用 TCP ，而 TCP 會幫忙排好順序再回傳給我們，並 CK 已經完整接收到的位置，因此其中一個沒收到，會卡住在其之後的所有東西，即使其已送達，也會卡著不 ACK 和回傳，因此我們同樣也收不到 stream ID = 7 的物件。根據 `ls -al target/` 的結果可以看到，確實 file 08, 06 大小為 0 ，沒有成功傳送。

### HTTP/3 Under the Packet-dropping Condition

![nsc_hw6_http3](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\nsc_hw6_http3.png)

測試結果如上圖，stream ID = 1 應該會是去要隨機三個檔案位置出來，然後 stream ID = 3, 5, 7 在此次測試中分別為 file 00, 04, 01 ，而我們在 http 3.0 client 調用 QUIC 時，指定了 `client_socket.drop(5)` ，因此 stream ID = 5 的物件應該不會成功送達，而此次底層使用的是 QUIC ，其每個 stream 是獨立檢察、回傳、 ACK 的，且其機制，若中間一個封包掉了，不會因此卡住告知對面後面的已送達，因此當 5 之後的物件收完了，就會先回傳，QUIC 則繼續等 5 丟掉的封包送達。根據 `ls -al target/` 的結果可以看到，確實只有 file 04 大小為 0 ，沒有成功傳送。

另外 QUIC 使用上會有一些問題，當一端關掉 socket 時沒有告知對面的手段，因此 server 沒有判斷 client 已經關閉的方法，此時再開一個 client 會撞到 assert INIT packet，另外傳送上可能會大量先收到某特定 stream 的封包，且傳輸較慢，因此不能設置 timeout，且偶爾可能發生一些奇怪不明原因的問題，其中若遺失的是 request，可以發現等待 server 收到會等非常久，所以若發現 server 的 output `Start handle...` 沒有全部出來，可以重試一次，放著等，是會傳完，但真的頗久，沒特別去看都會覺得是哪裡寫爛了。

### HTTP/1.0

![image-20230523062727558](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230523062727558.png)

### HTTP/1.1

![image-20230523062807890](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230523062807890.png)

### HTTP/2.0

![image-20230523062649541](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230523062649541.png)

### HTTP/3.0

![image-20230523071338252](C:\Users\user.DESKTOP-VP23IAB\AppData\Roaming\Typora\typora-user-images\image-20230523071338252.png)



