# Final Project Proposal

109550206  陳品劭

目前尚未確定題目，先列出幾個暫時有的想法。

## 1
#### 主題

防火牆、頻寬控制器

#### 預期功能

此主題基於自我使用需求而生，想要一個方便的小工具，可以透過簡易指令或操作，對防火牆進行調整，主要是想對 Port forwarding 進行一個方便的操作。以及對符合特定規則的流量進行操作，限制某些應用的流量上限或下限。

#### 詳細說明

由於不想碰 Windows 防火牆設定、想把 Windows 放在內網，因為現行 Windows 開遠端桌面 (RDP) Port 到 public IP 有點危險，想把它移到內網，再架一個 VPN server ，來遠端 Windows 桌面，因此架構會變成下圖：

| ![](https://i.imgur.com/zDXr6sm.png) | ![](https://i.imgur.com/WQ9UxMu.png) |
| :----------------------------------: | :----------------------------------: |
|               系統架構               |            邏輯上網路架構            |

然後在 wsl 上放一個工具調用 Router 設定對防火牆進控制。

另外一個則是有時候下載檔案或同時開 YouTube 、遊戲時，可能會希望某些應用的網路更為穩定或保留一定限度的頻寬，希望可以有這樣的功能，此部分的實現尚未尋找過方法，不過應該會是一個 Router 上的功能，或是跑在 Router 上的程式。

#### 實驗/開發環境

Windows 11、Hyper-V



















## 2
#### 主題

STP 、 RSTP 模擬

#### 預期功能

模擬 STP 的行為：選出 root switch 、 root port ... 。

#### 詳細說明

類似 Project 2 方式，透過 Python 來模擬 Switch 交換資訊，建出生成樹。

#### 實驗/開發環境

Ubuntu 22.04 、 Python3

## 3

#### 主題

DHCP Server

#### 預期功能

將其 Run 在某一台機器上，即可使其成為 DHCP Server。

#### 詳細說明

透過 Socket Programing 根據 RFC 說明來傳送、接受封包來分配 IP，並透過讀設定檔來知道可分配的 subnet。

#### 實驗/開發環境

Ubuntu 22.04 、 C++ or Python3
