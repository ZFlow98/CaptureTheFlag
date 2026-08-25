# CTF Day 2 筆記（ctfshow misc9 ~ misc13）

延續 Day1（misc4~misc8）的隱寫基礎，Day2 進一步深入 **PNG 內部結構隱寫**：從單純的元數據，到多重 IDAT 塊、乃至字元間隔插入的高階手法。

---

## 一、核心觀念總整理

### 1. PNG 資料塊（Chunk）結構複習
每個 Chunk 組成：`[4 bytes 長度] + [4 bytes 類型] + [資料] + [4 bytes CRC]`

- `IHDR`：圖片寬高、色彩資訊（第一個 Chunk）
- `tEXt` / `iTXt`：文字元數據，可直接放明文字串
- `IDAT`：實際像素資料，**可以有多個**，解碼器會依序拼接
- `IEND`：結尾標記

### 2. 「刪 IDAT 找隱藏圖」的正確心法
- PNG 允許把像素資料切成多個 IDAT 塊，正常圖片只是被「切段」，不代表每段都是獨立完整的圖。
- 若一張圖裡藏了「表面圖 + 隱藏 Flag 圖」兩張圖，通常結構是：
  - 表面圖的資料可能橫跨**多個** IDAT 塊（不一定只占 1 個）
  - 隱藏圖從下一個 IDAT 塊開始
- **常見誤區**：只刪第一個 IDAT 就想看到 Flag，結果畫面全黑或報錯 → 代表表面圖其實佔了不只 1 個 IDAT 塊，必須**連續刪除到正確的數量**，讓隱藏圖的第一個 IDAT 塊變成新檔案裡的第一個 IDAT，解碼器才讀得對。
- 判斷刪幾個的方法：
  - 圖形化工具（TweakPNG）一個一個試刪 + 存檔預覽
  - 用 binwalk 看兩個 zlib 資料流的位移量（offset），反推第一段資料的總長度，再回頭在工具中計算對應要刪除的 IDAT 數量

### 3. 「隔位插入」隱寫（字元交錯藏字串）
- 出題者把正確 Flag 字串中的每個字元之間，插入一個雜訊字元（例如 `ctfshow{...}` 變成 `c?t?f?s?h?o?w{...}`），破壞直接搜尋 `ctfshow` 的特徵。
- 為了混淆視聽，常在檔案裡放入**多組**類似結構的假 Flag（干擾項），必須逐一嘗試才能找到真的。
- 解法：正則表達式抓出 `c.t.f.s.h.o.w.\{.*?\}` 這種間隔模式，再用切片 `match[::2]`（取偶數位元）還原成乾淨字串。

### 4. 不依賴 Kali 的 Windows 替代工具鏈
不是每次隱寫題都得開虛擬機跑 binwalk / foremost，Windows 本機也有對應方案：

| 需求 | Kali 做法 | Windows 替代 |
|---|---|---|
| 分離內嵌檔案（附加資料） | `binwalk -e` / `foremost` | 010 Editor / WinHex 手動定位 `IEND` 後資料另存新檔；或 Foremost for Windows 版；或直接嘗試用 7-Zip 開啟（常是 zip/zlib 資料） |
| 解壓 zlib 附加資料 | Linux 指令流 | 簡單 Python 腳本 `zlib.decompress()` |
| 找 PNG 內文字（tEXt 塊） | `strings \| grep` | 記事本 / Notepad++ 直接 `Ctrl+F` 搜尋；或 010/WinHex 用 ASCII 字串搜尋 |
| 檢視/刪除 Chunk（多 IDAT） | 010 Editor 手動算長度 | **TweakPNG**：圖形化列出所有 Chunk，選取刪除、`Ctrl+S` 會自動重算 CRC，不會像手動刪字節那樣容易搞壞檔案 |
| 一站式無腦分析 | 整套 Kali 工具鏈 | **隨波逐流**（CTF 綜合隱寫工具）：拖入檔案一鍵跑 binwalk/foremost/IDAT 異常偵測/上百種編碼解碼 |
| 拖拉式解碼／格式轉換 | 命令列指令組合 | **CyberChef**（線上免安裝，GCHQ 開源）：把 Extract Files、From Base64 等模組像積木一樣拼接處理 |

### 5. 010 Editor 手動刪 Chunk 常見坑
- 刪除一段資料後，檔案的位移量（offset）已經改變，但 010 的 `.bt` 模板還在用舊位址解析，容易報錯或誤判。
- **解法**：每刪完一段就存檔後按 **F5 重新載入模板（Refresh Template）**，讓解析結果對齊新的檔案結構。
- 對新手來說，010 Editor 學習曲線陡，建議把它當「最後手術刀」，優先用 TweakPNG / 隨波逐流等圖形化工具處理常見情境。

---

## 二、各題重點紀錄

### misc9：Flag 藏在 PNG 的 tEXt 文字元數據塊
- 不需要分離檔案，Flag 直接以明文寫在 PNG 的 `tEXt` 元數據塊中。
- 解法（任一皆可）：
  - 記事本/Notepad++ 直接打開圖片檔，`Ctrl+F` 搜尋 `ctfshow` 或 `ctf`
  - 010 Editor / WinHex：搜尋模式選 **ASCII 字串**，輸入 `ctfshow`
  - 終端機：`strings misc9.png | grep ctfshow`
  - PowerShell：`Select-String -Path "misc9.png" -Pattern "ctfshow" -Encoding ascii`
- **Flag**：`ctfshow{5c5e819508a3ab1fd823f11e83e93c75}`

### misc10：PNG 尾端附加壓縮資料（需分離提取）
- 010/WinHex 直接搜關鍵字通常找不到，因為附加資料是壓縮過的（zlib/zip），不是明文。
- **Kali 解法（主流）**：
  ```bash
  binwalk -e misc10.png
  # 若權限不足：
  binwalk -e misc10.png --run-as=root
  ```
  分離出的檔案（如 `10E5`）本身沒有副檔名，改成 `.txt` 或用記事本直接打開即可看到 Flag。
- **Windows 免 Kali 替代方案**：
  1. 010 Editor / WinHex：搜尋 hex `49 45 4E 44`（即 `IEND`），定位其後 4 bytes CRC 校驗碼，之後的資料即為附加內容，另存新檔。
  2. Foremost for Windows 版：`foremost.exe misc10.png`，看 `output/` 資料夾。
  3. 隨波逐流：拖入檔案點「一鍵隱寫分析」。
  4. Python 腳本手動解壓 zlib：
     ```python
     import zlib
     with open("misc10.png", "rb") as f:
         data = f.read()
     iend_index = data.find(b"IEND") + 8
     extra_data = data[iend_index:]
     decompressed = zlib.decompress(extra_data)
     print(decompressed.decode("utf-8", errors="ignore"))
     ```
- **Flag**：`ctfshow{353252424ac69cb64f643768851ac790}`

### misc11：PNG 含兩個 IDAT 塊，刪掉第一個即可
- 圖片本身只有 1 個表面圖 + 1 個隱藏圖，恰好各佔一個 IDAT 塊，難度較低。
- **解法：TweakPNG**
  1. 拖入 `misc11.png`，列表可見兩個 IDAT 塊。
  2. 選取第一個（表面圖）IDAT，按 `Delete` 刪除。
  3. `Ctrl+S` 存檔（會自動重算 CRC），或按 `F7` 直接預覽。
- **常見錯誤**：不小心刪成第二個 IDAT，或用 010 手動選取範圍沒對齊 Chunk 邊界 → 圖片只剩上半部或損毀。判斷準則：**留下能顯示完整 Flag 圖的那個 IDAT**，本題是刪掉第一個。
- 替代解法：010 Editor 精算 Chunk 邊界手動刪除；Python 腳本自動過濾指定 IDAT；CyberChef 網頁版。
- **Flag**：`ctfshow{44620176948fa759d3eeafeac99f1ce9}`

### misc12：進階版多重 IDAT，需連續刪除前 8 個
- 表面圖的像素資料被系統切成了 **前 8 個 IDAT 塊**，隱藏的 Flag 圖從第 9 個 IDAT 才開始。
- 只刪第 1 個 IDAT 會導致表面圖資料不完整（缺開頭解碼資訊），圖片直接變黑或報錯，容易誤以為做法錯了。
- **解法**：用 TweakPNG 依序刪除，直到刪掉前 8 個 IDAT 後存檔才能看到 Flag。
- **科學判斷刪幾個的方式**：用 binwalk 看檔案內兩段 zlib 資料的位移量（offset）差值，反推第一張圖的資料總長度，再回頭在 TweakPNG 中對照各 IDAT 長度加總，確認要刪除的數量。
- **自動化 Python 腳本**（依序嘗試刪除前 N 個 IDAT，全部輸出到資料夾比對）：
  ```python
  import os
  with open("misc12.png", "rb") as f:
      data = f.read()
  header, rest = data[:8], data[8:]
  chunks, idx = [], 0
  while idx < len(rest):
      length = int.from_bytes(rest[idx:idx+4], "big")
      chunk_type = rest[idx+4:idx+8]
      chunks.append((chunk_type, rest[idx:idx+12+length]))
      idx += 12 + length
  idat_indices = [i for i, c in enumerate(chunks) if c[0] == b"IDAT"]
  os.makedirs("output", exist_ok=True)
  for k in range(1, len(idat_indices)):
      skip = set(idat_indices[:k])
      new_chunks = [c[1] for i, c in enumerate(chunks) if i not in skip]
      with open(f"output/del_first_{k}_idats.png", "wb") as f:
          f.write(header + b"".join(new_chunks))
  ```
- 010 Editor 手動刪除時的坑：每刪一段資料，Chunk 位移量會變，模板需按 **F5 重新載入**，否則後續解析會全部錯位報錯。
- **Flag**：`ctfshow{10ea26425dd4708f7da7a13c8e256a73}`

### misc13：字元隔位插入隱寫 + 多組干擾 Flag
- 出題者把正確 Flag 的每個字元中間插入一個雜訊字元（如 `c?t?f?s?h?o?w{...}`），破壞直接關鍵字搜尋。
- 檔案末端藏了**多組**（約 4 組）類似結構的假 Flag，需逐一嘗試才能找到正確答案。
- 手動解法：010 Editor 打開圖片，翻找檔案結尾類似 `ctfshow` 的片段，人工隔位挑出偶數位字元還原。
- **自動化 Python 腳本**（正則抓出所有間隔模式，統一隔位還原）：
  ```python
  import re
  with open("misc13.png", "rb") as f:
      content = f.read()
  pattern = re.compile(b"c.t.f.s.h.o.w.\{.*?\}")
  matches = pattern.findall(content)
  for idx, match in enumerate(matches, 1):
      clean_flag = match[::2].decode("utf-8", errors="ignore")
      print(f"[{idx}] {clean_flag}")
  ```
- 跑出多組候選後逐一送出驗證，找到真正正確的那組。
- **Flag**：`ctfshow{ae6e3ea48f518b7e42d7de6f412f839a}`

---

## 三、工具補充筆記

### 1. TweakPNG —— PNG Chunk 專用輕量工具
- 原始用途其實不是給 CTF 用的，是開發者用來檢查/優化 PNG 檔案（清除多餘 ICC、gAMA、tEXt 等元數據以減少體積、確保跨瀏覽器顏色一致）。
- 因為 CTF misc 題目大量圍繞「改 IHDR 寬高」「塞多個 IDAT」等 PNG 協議層級的手法設計，TweakPNG 圖形化列出所有 Chunk、支援直接刪除並自動重算 CRC，因此被 CTF 圈廣泛「借用」成隱寫神器。
- 下載：`https://entropymine.com/jason/tweakpng/`

### 2. 隨波逐流（CTF 綜合隱寫工具，Windows GUI）
- 中文 CTF 圈開發的傻瓜式一站工具，適合新手第一步「無腦掃描」：
  - 拖入檔案自動跑 binwalk / foremost 邏輯，偵測 IDAT 異常
  - 內建上百種編碼格式（Base64、Morse、Brainfuck、Unicode…）一鍵嘗試
  - 密碼爆破等附加功能

### 3. CyberChef（線上免安裝，GCHQ 開源）
- 拖拽式模組（Pipeline）組合操作，例如 `Extract Files`、`From Base64`、`Render Image`，不用背指令。
- 適合臨時無法安裝軟體、只想快速試編碼轉換的情境。

### 4. 新手建議的解題節奏（Windows 環境）
1. **傻瓜掃描**：先丟進「隨波逐流」跑一鍵分析，能直接出 Flag 就不用手動處理。
2. **結構排查**：若是 PNG 且牽涉到 Chunk 增刪，用 TweakPNG 可視化操作。
3. **編碼/文本變換**：遇到加密字串或編碼，丟 CyberChef 網頁版試跑。
4. **最後手術刀**：以上都不行，或需要精準修改 IHDR 寬高、找特定二進位模式時，才動用 010 Editor。

---

## 四、學習方法心得（延續 Day1）
1. 現階段（累積前 50~100 題）每題都要看 Writeup 是**完全正常**的階段，不是能力問題，是 Misc 題本身「知識點零碎、無固定套路」的特性所致。
2. 看 Writeup 的正確方式：
   - 先自己動手嘗試（隨波逐流 + 記事本）至少 10 分鐘
   - 看 Writeup 時只看**第一句/破題思路**（例如「這張圖有兩個 IDAT 塊」），看到關鍵資訊立刻關掉，自己動手完成剩下步驟
   - 建立自己的「工具本」：記錄第一次見到的工具名稱（TweakPNG、Foremost）與第一次學到的機制（PNG 多 IDAT 需連刪、隔位插入藏字串等）
3. 三階段進程參考：
   - **積累期**（現在）：每題都陌生，靠 Writeup 累積工具與套路庫
   - **模仿期**：看到類似題型能想起用過的工具，嘗試先自己做
   - **獨立期**：拿到新題能主動照 SOP 排查（看檔頭 → 隨波逐流分析 → 檢查 Chunk 結構 → 提取文件）
