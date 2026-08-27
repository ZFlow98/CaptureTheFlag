# MISC（雜項）CTF 學習筆記

> MISC 的本質：**觀察力 + 資料還原能力 + 自動化腳本編寫**
> 除了「找 flag 的技巧／隱寫手法」之外，還需要具備底層的通用技術能力，才能把觀察到的線索真正「解出來」。

---

## 一、核心心法

MISC 題目通常是「線索 → 工具/腳本 → 還原數據 → 找到 flag」的鏈條。
真正卡關的地方，往往不是「不知道哪裡藏了東西」，而是「知道藏在哪，但沒有能力把它還原出來」。
所以除了熟悉各種隱寫手法之外，以下五大類技術是必修項目。

---

## 二、你自己必須具備的能力（除了找 flag 技巧之外）

### 1. 靈活的 Python 自動化腳本能力 ★★★★★（最重要）

- **資料處理與轉碼**
  - 位元（Bit）與位元組（Byte）互轉
  - Hex（十六進位）、Base64、Base32、Base85、URL encode
  - ASCII 碼轉換、進制轉換（2/8/10/16 進位）
- **爆破與自動化**
  - 字典爆破（ZIP 密碼、Hash 破解）
  - 自動發送 HTTP 請求與 Server 互動（例如遠端解題環境）
  - 批次處理大量檔案（例如上百張圖片找異常）
  - **常用函式庫** 
  - `pwntools`：通訊與腳本控制（連遠端、收發封包）
  - `Pillow (PIL)`：圖像讀寫、像素操作
  - `struct`：處理二進位數據（binary unpack/pack）
  - `pyzipper` / `zipfile`：ZIP 相關處理
  - `hashlib`：Hash 計算與比對

> 建議：MISC 幾乎每一題最後都要「寫一小段 Python 腳本」把手動發現的規律自動化還原，這是與純靠工具點一點的最大差異。

---

### 2. 二進位與檔案結構分析（File Format）★★★★★

- **Magic Bytes（檔案頭/尾識別）**
  - 熟悉常見檔案格式的十六進位開頭與結尾
    - PNG：`89 50 4E 47`
    - JPG：`FF D8 FF`
    - ZIP：`50 4B 03 04`
    - PCAP：`D4 C3 B2 A1`
    - ELF：`7F 45 4C 46`
    - PDF：`25 50 44 46`
- **Hex Editor 操作**
  - 精通 010 Editor / HxD / CyberChef
  - 能手動修復損毀的檔案頭（File Header Repair）
  - 能修改圖片的長寬像素數據（IHDR chunk 竄改，是常見藏 flag 手法）
  - 能計算並修正 CRC 校驗碼（PNG chunk 常考）
- **檔案分離／提取**
  - `binwalk`：掃描並提取複合檔案中的隱藏內容
  - `foremost`：依 Magic Bytes 自動切割還原檔案
  - `dd`：手動依 offset 切割二進位檔案
  - `zsteg`：專門找 PNG/BMP 中的 LSB 隱寫

---

### 3. 網路封包與流量分析（Traffic Analysis）★★★★☆

- **Wireshark / TShark**
  - 看懂 TCP/UDP、HTTP、DNS、FTP、USB 等常見協定
  - 過濾語法（filter）要熟練，例如 `http.request`、`tcp.stream eq 0`
- **流量提取**
  - 從 `.pcap` / `.pcapng` 中匯出傳輸檔案（File → Export Objects）
  - 追蹤 TCP 串流（Follow TCP Stream）還原對話內容
  - 分析 ICMP / DNS 隧道中夾帶的隱藏資料
  - USB 封包分析（還原鍵盤/滑鼠輸入內容）

---

### 4. 鑑識與系統基礎（Forensics）★★★☆☆

- **記憶體鑑識（Memory Forensics）**
  - 掌握 `Volatility` / `Volatility3`
  - 能從記憶體 dump（.raw/.vmem）中提取：
    - 密碼、剪貼簿內容
    - 正在執行的程序（process list）
    - 網路連線紀錄
- **磁碟與檔案系統鑑識**
  - 了解 FAT32 / NTFS / EXT4 基本結構
  - 使用 FTK Imager / Autopsy 尋找被刪除的檔案、還原分割區
- **Git 歷史還原**
  - `git log` / `git reflog`：找回被覆蓋或刪除的 commit
  - `GitHack`：從洩漏的 `.git` 資料夾還原原始碼與敏感資訊

---

### 5. 音訊與頻譜分析（Audio Analysis）★★★☆☆

- **Audacity / Sonic Visualiser**
  - 將 `.wav`/`.mp3` 轉為頻譜圖（Spectrogram）觀察隱藏圖像/文字
  - 辨識摩斯密碼（Morse Code）
  - 辨識 DTMF（電話按鍵音）
  - 判斷是否有隱藏的高頻/低頻訊號軌道

---

## 三、額外建議補強的知識點（進階，可依需求慢慢補）

以下是原本清單之外，實務上也很常遇到、值得列入學習雷達的項目：

| 分類 | 知識點 |
|---|---|
| 編碼/密碼學 | 摩斯密碼、培根密碼、凱撒/維吉尼亞密碼、進制轉換、QR Code/條碼辨識、腦筋急轉彎編碼（Brainfuck、Emoji Cipher 等） |
| 圖像隱寫進階 | LSB（最低有效位）隱寫原理、EXIF metadata 分析（`exiftool`）、多圖 XOR 疊加找 flag |
| 壓縮檔攻擊 | 已知明文攻擊（Known-plaintext attack, `bkcrack`）、偽加密（Fake Encryption）判斷與修復、CRC 碰撞暴力破解單字元密碼 |
| Linux 基礎工具 | `strings`、`grep`、`file`、`xxd`、`base64`、`diff`（比對兩個相似檔案找差異） |
| 壓縮與封裝格式 | tar/gzip/7z 結構、多層壓縮巢狀解包腳本化 |
| CyberChef 熟練度 | Recipe 串接思維（多步驟自動解碼鏈）、Magic 功能自動猜測編碼 |
| Web/其他交叉知識 | 有些 MISC 題會混雜簡單 Web（例如與 Server 互動拿 flag），需要基礎的 HTTP request 概念 |
| QR Code / 條碼修復 | 部分題目會故意破壞 QR code 定位角，需要手動用 Hex/圖像工具修復 |

---

## 四、學習路線建議（由淺入深）

1. **CyberChef**：熟悉各種編碼轉換的「感覺」，建立對 Hex/Base64/URL encode 的直覺。
2. **Linux 常用指令**：`strings`、`grep`、`file`、`xxd` 練到肌肉記憶。
3. **Python 基礎 + 上述常用 Lib**：能自己寫腳本轉碼、批次處理檔案。
4. 完成以上三步 → **可解決 70% 以上入門 MISC 題**。
5. 接著再依興趣/題目遇到的頻率，逐步深入：
   - 圖像/檔案結構（Hex Editor + binwalk）
   - 流量分析（Wireshark）
   - 音訊分析（Audacity）
   - 鑑識（Volatility / Git 還原）→ 難度較高，可放最後

---

## 五、常用工具速查表

| 用途 | 工具 |
|---|---|
| 線上編碼解碼 | CyberChef |
| Hex 編輯 | 010 Editor, HxD |
| 檔案分離 | binwalk, foremost, dd |
| 圖片 LSB 隱寫 | zsteg, stegsolve |
| 圖片 metadata | exiftool |
| 封包分析 | Wireshark, tshark |
| 記憶體鑑識 | Volatility / Volatility3 |
| 磁碟鑑識 | FTK Imager, Autopsy |
| 音訊分析 | Audacity, Sonic Visualiser |
| ZIP 密碼攻擊 | bkcrack, fcrackzip, John the Ripper |
| Git 洩漏還原 | GitHack, git log/reflog |

---

*筆記可持續補充：每次解題遇到新手法或新工具，都建議記錄「題目特徵 → 對應手法 → 使用工具/腳本」，累積成自己的 checklist。*
