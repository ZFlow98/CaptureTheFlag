# Nmap 必考知識點整理

## 一、基本概念

- **Nmap（Network Mapper）**：開源網路掃描與安全檢測工具，用於「探測網路架構」與「評估系統安全性」。
- 核心五大功能：
  1. **主機發現（Host Discovery）**：找出網路上有哪些主機在線。
  2. **連接埠掃描（Port Scanning）**：偵測 TCP/UDP 開放的連接埠。
  3. **服務與版本偵測（Service/Version Detection）**：辨識服務軟體及版本。
  4. **作業系統偵測（OS Detection）**：透過封包指紋推測作業系統。
  5. **腳本自動化（NSE, Nmap Scripting Engine）**：自動化漏洞檢測、資訊蒐集、簡易爆破。

---

## 二、TCP 三向交握（必考基礎）

正常連線建立過程：
1. Client → Server：**SYN**（請求連線）
2. Server → Client：**SYN-ACK**（同意連線）
3. Client → Server：**ACK**（確認，正式建立連線）

---

## 三、掃描類型（-s 系列）

| 參數 | 名稱 | 說明 |
|---|---|---|
| `-sS` | SYN Scan（半開放/隱密掃描） | 只完成前兩步（SYN→SYN-ACK）後立刻送 **RST** 切斷，不完成三向交握。速度快、較不易留下應用層日誌。**需要 Root/管理員權限**（要建構 Raw Packets）。 |
| `-sT` | TCP Connect Scan | 完整三向交握（呼叫作業系統的 connect()）。無 Root 權限時的替代方案，速度較慢、易留日誌。 |
| `-sU` | UDP Scan | 掃描 UDP 埠（如 DNS 53、SNMP 161）。速度慢，依賴 ICMP Unreachable 回應判斷埠狀態。 |
| `-sV` | Version Detection | 偵測服務名稱與精確版本號（如 Apache 2.4.41）。 |
| `-sC` | Script Scan | 等同 `--script=default`，對開放埠自動執行預設 NSE 腳本，蒐集資訊（如 HTTP Title、SSH 指紋、SMB 匿名存取等）。 |
| `-sn` | No Port Scan（Ping Scan） | 僅做主機發現，不掃埠。 |

**考點**：`-sS` 常被誤以為是完整 TCP 連線，但它**不是**——這是常考的觀念題。

---

## 四、常見組合參數

| 參數 | 說明 |
|---|---|
| `-O` | OS Detection，依 TCP/IP 封包指紋推測作業系統。 |
| `-A` | Aggressive Scan，等同同時開啟 `-O` + `-sV` + `-sC` + `--traceroute`。 |
| `-Pn` | 跳過 Ping 檢查，將所有主機視為在線（目標擋 ICMP 時使用）。 |
| `-p <port>` | 指定埠範圍。例：`-p 80,443`、`-p 1-100`、`-p-`（全部 65535 埠）。 |

---

## 五、時序控制 -T（速度 vs 隱密度，必考）

| 等級 | 名稱 | 特性 |
|---|---|---|
| `-T0` | Paranoid | 極慢，最隱密，用於規避 IDS |
| `-T1` | Sneaky | 極慢，隱密 |
| `-T2` | Polite | 降速節省頻寬、降低目標負擔 |
| `-T3` | Normal | **預設值** |
| `-T4` | Aggressive | 常用，速度快，適合穩定網路 |
| `-T5` | Insane | 最快，容易漏報或造成衝擊 |

**口訣**：數字越大越快、越容易被發現；數字越小越慢、越隱密。

---

## 六、規避防火牆 / IDS（Evasion，考試常出情境題）

| 參數 | 說明 |
|---|---|
| `-f` | 封包碎片化，繞過簡單封包過濾防火牆 |
| `-D <decoy1,decoy2,...>` | 誘餌掃描，混入假來源 IP 混淆記錄 |
| `--source-port` | 偽裝來源埠（如偽裝成 DNS 的 53 埠） |

---

## 七、輸出格式

| 參數 | 說明 |
|---|---|
| `-oN <file>` | 一般文字格式 |
| `-oX <file>` | XML 格式（可匯入其他工具） |
| `-oA <basename>` | 同時輸出 Normal + XML + Grepable 三種格式 |

---

## 八、Port 狀態（必考觀念）

Nmap 回報的連接埠狀態常見有：
- **Open**：埠有服務在監聽並回應
- **Closed**：埠可達但無服務監聽
- **Filtered**：無法判斷是否開放，通常被防火牆擋掉（無回應或收到過濾訊息）
- **Unfiltered**：埠可達，但無法確定開放或關閉（常見於 `-sA`）

---

## 九、NSE（Nmap Scripting Engine）

- 使用 **Lua** 語言撰寫腳本。
- 腳本分類（常考分類名稱）：
  - `auth`：身分驗證相關檢測
  - `vuln`：已知漏洞（CVE）檢測
  - `exploit`：漏洞利用
  - `discovery`：資訊蒐集
- 常用指令：
  - `--script=default`（同 `-sC`）
  - `--script=vuln`：直接掃描已知 CVE 漏洞

---

## 十、常用組合範例（實作必背）

```bash
# 全面掃描：OS + 服務版本 + 預設腳本，速度快
nmap -A -T4 192.168.1.1

# 目標擋 Ping 時，指定埠掃描並抓版本
nmap -Pn -sV -p 80,443,8080 10.0.0.1

# 隱密掃描 + 預設腳本 + 較快速度
nmap -sS -sC -T4 192.168.11.132

# 最佳實務組合：SYN掃描 + 版本偵測 + 預設腳本
nmap -sS -sV -sC -T4 192.168.11.132
```

---

## 十一、考試常見易混淆點整理

1. **`-sS` ≠ 完整 TCP 連線**：只完成 SYN/SYN-ACK 後立即送 RST，是「半開放掃描」。
2. **`-sS` 需要 Root/管理員權限**，`-sT` 不需要（因為走系統的 connect()）。
3. **`-A` 是組合參數**，不是單一功能，等於 `-O -sV -sC --traceroute`。
4. **`-sC` 和 `--script=default` 完全等價**。
5. **`-Pn` 是跳過 Ping**，`-sn` 是只做 Ping（不掃埠）——兩者容易考混。
6. **`-T` 數字與速度成正比、與隱密度成反比**。

---

如果需要，我可以再幫你做成 Quiz 自我測驗，或針對 OSCP／CEH 考試常見的 Nmap 實務搭配指令做更深入整理。
