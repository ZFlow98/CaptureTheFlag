# CTF Day 4 筆記（ctfshow misc27、31、32、36、39 + 圖片寬高隱寫總論）

延續 Day1~3 的檔案結構與元數據隱寫，Day4 主題聚焦在**「圖片寬高被竄改」**這一大類考點：BMP / PNG / JPG / GIF 四種格式的寬高隱寫原理各不相同，本篇做一次完整總整理，並補充 GIF 幀延遲時間隱寫與 AI 輔助解題的心得。

---

## 一、核心觀念總整理：四大格式寬高隱寫全解析

### 1. 為什麼「改寬高」是熱門考點？
- 圖片解碼器是照著檔頭記錄的寬高去「切」像素資料流的。出題者只要把寬或高改小，畫面就會被裁掉一截，剩下的資料其實還完整躺在檔案裡，只是「沒被畫出來」。
- 判斷是否為此類題目的直覺線索：
  - 圖片顯示怪異的比例（過矮、過扁）
  - **檔案大小與畫面內容明顯不成比例**（這是最客觀、無法造假的證據）
  - 縮圖能隱約看到下方有東西，但點開看不到

### 2. 四種格式的判斷與還原方法總表

| 格式 | 隱寫機制 | 是否有校驗碼 | 還原方法 |
|---|---|---|---|
| **BMP** | 未壓縮，資料量與寬高呈**精確線性關係** | 無 | 用檔案大小公式反推正確寬或高 |
| **PNG** | 寬高存在 `IHDR` 塊，並有 **CRC32** 校驗碼保護 | 有（除非被竄改） | 爆破 CRC32；若 CRC 也被改，改用 IDAT 解壓後的資料長度反推 |
| **JPG** | 寬高存在 `SOF0`（`FF C0`）標記中，**完全沒有校驗機制** | 無 | 直接暴力把高度改大即可，不會損毀圖片；寬度改錯則需逐一試（會產生斜向錯位） |
| **GIF** | 寬高存在 **LSD（Logical Screen Descriptor）**，同樣沒有校驗機制 | 無 | 直接改大或用腳本批次生成不同寬度版本比對 |

### 3. BMP：靠算術公式反推（無壓縮的優勢）
- BMP 規定每一列資料必須補齊為 4 bytes 的倍數（記憶體對齊 / Padding）：
  ```
  RowSize  = floor((Width × BitCount + 31) / 32) × 4
  ImageSize = RowSize × Height
  ```
- **不用死背整條公式**，理解本質即可：24-bit 全彩 BMP 每個像素固定占 **3 bytes**（R+G+B 各 1 byte），忽略 padding 誤差時可直接用：
  ```
  ImageSize（bytes） ≈ Width × Height × 3
  ```
- **常見換算誤區**：「24-bit」指的是每像素 24 個 **bit**（= 3 bytes），不是 24 bytes！檔案大小顯示的 KB/MB 也全是以 **byte** 為單位，不要跟 bit 搞混。
- 實戰口訣：「算位元組數，全彩除以 3；算位元數，全彩乘以 24。」
- 步驟：
  1. 在 010 Editor 查看 `biSizeImage`（圖像資料區精確大小，不含 54 bytes 檔頭）
  2. 已知其中一邊（寬或高）時，用 `另一邊 = biSizeImage ÷ 3 ÷ 已知邊` 反推，結果通常有小數，**無條件進位取整**即為答案（因為 padding 的緣故）
  3. 010 Editor 改回正確數值（小端序）存檔

### 4. PNG：CRC32 爆破 / IDAT 解壓矩陣反推（雙保險）

**情境一：CRC32 沒被動過（最常見）**
- 原理：出題者只改了 `IHDR` 裡的寬高數值，卻忘了（或懶得）同步更新 `IHDR` 對應的 CRC32 校驗碼，因此可以用「已知正確 CRC32、反推哪組寬高能算出同樣的 CRC32」來爆破。
- 基礎腳本（雙層迴圈，較慢）：
  ```python
  import zlib, struct
  with open('flag.png', 'rb') as f:
      bin_data = f.read()
  ihdr = bin_data[12:29]
  expected_crc = struct.unpack('>I', bin_data[29:33])[0]
  for w in range(1, 2000):
      for h in range(1, 2000):
          new_ihdr = ihdr[:4] + struct.pack('>I', w) + struct.pack('>I', h) + ihdr[12:]
          if zlib.crc32(new_ihdr) == expected_crc:
              print(f"寬:{w} 高:{h}")
              exit(0)
  ```
- **效能優化**：CTF 題目 90% 只改了「高度」，寬度維持正確。只爆破高度可以把迴圈量從 400 萬次降到 4000 次，秒級完成：
  ```python
  width = struct.unpack('>I', bin_data[16:20])[0]  # 讀取原本正確的寬度
  for h in range(1, 4000):
      new_ihdr = ihdr[:4] + struct.pack('>I', width) + struct.pack('>I', h) + ihdr[12:]
      if zlib.crc32(new_ihdr) == expected_crc:
          print(f"高度: {h} (Hex: {hex(h)})")
          break
  ```

**情境二：CRC32 也被出題者竄改了（進階陷阱）**
- 現象：CRC32 爆破腳本完全跑不出結果，因為驗證基準本身是假的。
- **解法：繞過標頭校驗，直接用 IDAT 解壓後的原始資料長度反推**。這是本篇最重要的技巧：
  - PNG 的 `IDAT` 資料經 zlib 解壓後，每一列（Row）像素資料前面都會多 1 個 **Filter Byte**。24-bit RGB 圖片的關係式為：
    ```
    Raw Data Size = Height × (Width × 3 + 1)
    ```
  - 只要拿到解壓後的總 byte 數，配合「已知寬度大於某個值」等限定條件，用**整除**去反推唯一合法的寬高組合：
  ```python
  import zlib, struct
  with open('flag.png', 'rb') as f:
      bin_data = f.read()
  idat_data = b''
  p = 8
  while p < len(bin_data):
      length = struct.unpack('>I', bin_data[p:p+4])[0]
      chunk_type = bin_data[p+4:p+8]
      if chunk_type == b'IDAT':
          idat_data += bin_data[p+8:p+8+length]
      p += 12 + length
  raw_data = zlib.decompress(idat_data)
  total_bytes = len(raw_data)

  bytes_per_pixel = 3  # RGBA 則改成 4
  for w in range(901, 3000):          # 已知寬度 > 900
      row_bytes = w * bytes_per_pixel + 1
      if total_bytes % row_bytes == 0:
          h = total_bytes // row_bytes
          print(f"寬:{w} 高:{h}")
          new_png = bin_data[:16] + struct.pack('>I', w) + struct.pack('>I', h) + bin_data[24:]
          with open('flag_fixed.png', 'wb') as f_out:
              f_out.write(new_png)
          break
  ```
  - **這個方法的威力**：完全無視 CRC32 是否被竄改，直接問底層資料「你需要排成多寬的矩陣才能剛好湊成一個完整長方形」，答案具有數學唯一性。

**不會寫程式也能解（PNG 版）**：
- **010 Editor 拉大法**：已知寬度下限（如 >900），直接把 Width/Height 改成一個夠大的數值（如 1200）存檔開圖，即使有些錯位歪斜，Flag 文字通常仍可辨識，再微調數值到不歪斜為止。
- **隨波逐流 / PCRT（PNG Check & Repair Tool）**：圖形化一鍵修復工具，多數基礎題型可以直接「一把梭」出結果。

### 5. JPG：完全沒有校驗機制，最好破解
- JPG 資料是流式壓縮，`SOF0`（`FF C0`）標記後緊接著 **2 bytes 高度 + 2 bytes 寬度**（大端序），且**沒有任何校驗碼**。
- **只改高度**：無腦把高度改到極大（例如改成 2000），圖片絕不會損毀，只會把底部原本沒畫出來的區域露出來。
  ```python
  with open('flag.jpg', 'rb') as f:
      data = bytearray(f.read())
  sof0_idx = data.find(b'\xff\xc0')          # 若找不到，改找 b'\xff\xc2'（漸進式 JPG, SOF2）
  data[sof0_idx+5] = 0x07                     # 高度改為 2000 (0x07D0)
  data[sof0_idx+6] = 0xD0
  with open('flag_fixed.jpg', 'wb') as f:
      f.write(data)
  ```
- **寬度也被改了**：因為 JPG 用 8×8/16×16 的 MCU 區塊解碼，寬度一旦錯誤，畫面會出現**斜向撕裂/花屏**，而不是單純裁切。此時無法用公式算，只能批次生成不同寬度的圖片，用肉眼挑出「文字沒有歪斜」的那一張：
  ```python
  import os
  with open('flag.jpg', 'rb') as f:
      data = bytearray(f.read())
  sof_idx = data.find(b'\xff\xc0')
  if sof_idx == -1:
      sof_idx = data.find(b'\xff\xc2')
  data[sof_idx+5] = (1500 >> 8) & 0xFF   # 高度先統一拉大，確保畫面完整露出
  data[sof_idx+6] = 1500 & 0xFF
  os.makedirs('jpg_output', exist_ok=True)
  for w in range(901, 1500):             # 已知寬度 > 900
      data[sof_idx+7] = (w >> 8) & 0xFF
      data[sof_idx+8] = w & 0xFF
      with open(f'jpg_output/w_{w}.jpg', 'wb') as f_out:
          f_out.write(data)
  # 打開 jpg_output 資料夾切換「大圖示」檢視模式，目測找出文字沒有歪斜的那張
  ```
  - 這裡不需要 PIL/Pillow，純用內建的 `open`/`bytearray` 讀寫即可；只有想直接把圖片拼接、批次處理縮圖時才需要額外安裝 `pip install pillow`。

### 6. GIF：改寬高原理與 JPG 類似，也沒有校驗機制
- GIF 檔頭第 6~9 個 byte（偏移量 6）是 **LSD（Logical Screen Descriptor）**，記錄畫布的寬與高，皆為小端序 2 bytes。
- 批次爆破寬度腳本範例：
  ```python
  import struct
  with open("misc36.gif", 'rb') as f:
      all_b = f.read()
  for i in range(920, 951):
      im = all_b[:38] + struct.pack('>h', i)[::-1] + all_b[40:]
      with open(f"{i}.gif", "wb") as f1:
          f1.write(im)
  # 產生 920.gif ~ 950.gif，逐一打開比對哪張寬度正確、文字沒有錯位
  ```
- **重要觀念：為什麼「寬度」錯會花屏，「高度」錯只是裁切？**
  - 圖像資料本質上是一維連續的像素流，解碼器靠「寬度」決定何時換行。
  - **寬度錯**：假設真實寬度 100px，若被改成 101px，解碼器每數 101 個像素才換行，導致每一行都比上一行多偏移 1 像素，累積起來造成**斜向撕裂**。
  - **高度錯**：高度只決定「畫多少行就停」，不影響每一行內部的排列順序。改小 → 底部被裁掉；改大 → 資料流讀完後补黑邊/透明，上方內容完全正常。
  - **結論表**：

    | 修改對象 | 視覺表現 | 解法策略 |
    |---|---|---|
    | 高度錯誤 | 圖像正常，只是下半部被裁掉 | 直接改大即可，無需精算 |
    | 寬度錯誤 | 斜向撕裂、花屏 | 需要精確爆破或用資料長度反推，改錯一點點都不行 |

### 7. GIF 幀延遲時間（Delay Time）隱寫（misc39 屬於此類）
- 提示語常帶有「忽快忽慢」「像水流」之類的暗示，代表隱寫媒介不是像素，而是**每一幀的播放間隔時間**。
- GIF 每幀的 `GCE`（Graphic Control Extension）區塊格式固定為：
  ```
  21 F9 04 [Flags 1byte] [Delay Time 2bytes 小端序] [Transparent Color 1byte] 00
  ```
- 純原生 Python（**不需要安裝 PIL**）即可掃描所有 `21 F9 04` 標記、抓出每幀延遲時間：
  ```python
  import struct
  with open('misc39.gif', 'rb') as f:
      data = f.read()
  delays = []
  p = 0
  while True:
      p = data.find(b'\x21\xf9\x04', p)
      if p == -1:
          break
      delay = struct.unpack('<H', data[p+4:p+6])[0]
      delays.append(delay)
      p += 3
  ```
- 拿到 `delays` 陣列後，觀察規律：
  - 若數值差異很大、接近 ASCII 範圍（如 99、116、102...）→ 很可能直接是 **ASCII 碼**
  - 若只有兩種相近數值（如本題的 360 / 370）→ 是**二進位編碼（0/1）**，較小值和較大值分別對應 0 和 1（正反兩種假設都要各跑一次，因為方向不確定）
  - 二進位每 8 位元一組，可轉成 **ASCII 字元**，若結果是亂碼，改成轉 **16 進位（Hex）** 輸出，因為隱藏內容可能是加密後的二進位資料而非明文：
    ```python
    def bin_to_hex(b_str):
        hex_str = ""
        for i in range(0, len(b_str), 8):
            byte = b_str[i:i+8]
            if len(byte) == 8:
                hex_str += f"{int(byte, 2):02x}"
        return hex_str
    ```
  - 拿到 16 進位結果後，丟進 **CyberChef** 嘗試 `From Hex` 接 `XOR`（爆破單字節金鑰）、`From Base64`，或檢查開頭是否符合已知檔案格式的 Magic Bytes（如 `50 4B 03 04` = ZIP、`89 50 4E 47` = PNG）。

---

## 二、各題重點紀錄

### misc27：JPG SOF0 高度隱寫
- 010 Editor 打開後直接使用內建 **JPG 模板**（Templates → Image → JPG，或按 F5），展開 `sof0` 結構，直接找到 `imageHeight` 欄位改大即可，**JPG 沒有 CRC 校驗，隨便改多大都不會損毀圖片**。
- 若沒有模板，手動搜尋 `FF C0`，其後第 5、6 個 byte 即為高度（大端序）。
- **Flag**：`ctfshow{5cc4f19eb01705b99bf41492430a1a14}`

### misc31：BMP 寬度隱寫，靠算術公式反推
- 010 查看得知高度 150px 正確，寬度有誤。
- 用 `biSizeImage`（如 487202）代入公式：`Width = biSizeImage ÷ 3 ÷ Height ≈ 1081.49`，取整（向上）得 **1082**。
- **Flag**：`ctfshow{fb09dcc9005fe3feeefb73646b55efd5}`

### misc32：PNG 寬度隱寫，CRC32 也被竄改（進階陷阱）
- 提示「高度正確，寬度有問題」，且已知**寬度大於 900**。
- 一般的 CRC32 爆破腳本、TweakPNG、隨波逐流基礎修復功能可能都無效，因為出題者連 CRC32 都一併改成假的。
- 正解：改用「IDAT 解壓資料長度反推」法（見上方總論第 4 節情境二），完全繞開 CRC 校驗，直接用矩陣整除關係算出唯一合法的寬高。
- **Flag**：`ctfshow{685082227bcf70d17d1b39a5c1195aa9}`

### misc36：GIF 寬度隱寫，批次生成比對
- 用 Python 腳本批次修改 LSD 寬度欄位（範圍 920~950），一次產生 31 張測試圖，肉眼挑出文字沒有錯位的那張。
- **心法**：GIF 寬度錯誤與 JPG 一樣會造成花屏撕裂，無法用公式精算，只能批次生成後比對。

### misc39：GIF 幀延遲時間隱寫（忽快忽慢）
- 提示「flag 就像水，忽快忽慢地流」點出考點是**播放速度變化**而非畫面本身。
- 提取所有 `21 F9 04` 標記後的 2-byte 延遲時間，發現只有 360 與 370 兩種數值 → 判定為二進位編碼。
- 先嘗試轉 ASCII 得到亂碼，代表底層是**加密後的二進位資料**，改轉 16 進位輸出，再交給 CyberChef 等工具做進一步解密（XOR / Base64 / 檢查檔案格式）。

---

## 三、工具與心法補充

### 1. 「先工具、後手搓」的實戰優先序
1. **第一時間（0~5 秒）**：丟進隨波逐流 / PCRT 等一把梭工具，能出結果直接交
2. **其次（5~30 秒）**：打開 010 Editor 模板，用速算公式手動改（BMP 算式、JPG 直接改高度）
3. **最後（1 分鐘以上）**：遇到 CRC 被竄改、寬高同時錯誤等非標準構造，才手寫 Python 腳本客製化爆破
- 用現成工具不是「偷吃步」，而是把節省下來的時間留給更難的題目；手寫腳本則是工具失效時的「保底防線」，理解底層原理才是重點，不是死記代碼。

### 2. PNG CRC32 爆破會「吃鱉」的 4 種情況
1. 出題者連 CRC32 都一併改掉（爆破基準是假的）→ 改用 IDAT 解壓長度反推
2. 出題者改的是「寬度」而非「高度」，但腳本只寫了單軸爆破 → 需視情況雙軸爆破或調整已知條件
3. `IDAT` 資料本身被截斷或破壞 → 即使寬高修復正確，畫面仍可能顯示損毀
4. 插入了自訂垃圾 Chunk 導致 `IHDR` 位移，腳本按固定 offset 讀取會抓錯位置 → 需動態搜尋 Chunk 而非寫死偏移量

### 3. 关于用 AI 輔助解題
- 使用 AI（或任何現成工具）本身完全不可恥，屬於工具演進的自然延伸，重點在於**是否理解了背後的原理**。
- AI 能快速給出解法的前提，是使用者已經先觀察出關鍵特徵（例如「CRC 被改了」「已知寬度大於 900」），並準確下達戰術指令；沒有這些觀察，AI 也無法給出對的方向。
- 建議把 AI 當成「幫忙寫代碼、查語法的助手」，自己負責發現異常特徵、決定解題策略，才能把每次解題轉化成自己的知識庫，遇到變種題時能舉一反三。

---

## 四、學習方法心得（延續 Day1~3）
1. **同一類考點（寬高隱寫）在不同格式下難度差異很大**：JPG 幾乎無腦可解（沒有任何校驗），PNG 則可能被出題者設下「CRC32 也竄改」的雙重陷阱，BMP 靠純算術、GIF 則兩種修改（寬/高）表現完全不同。遇到「改寬高」類題目時，第一步永遠是先確認格式，再套用對應格式的正確心法。
2. **「寬度錯誤 → 花屏撕裂」vs「高度錯誤 → 單純裁切」** 是本篇最重要的判斷準則，適用於 JPG 與 GIF；先分清楚是哪一邊出問題，能大幅節省嘗試的方向。
3. 遇到工具「爆破不出來」不代表無解，很可能是出題者又加了一層陷阱（如竄改 CRC32），這時候要回頭思考「還有什麼是出題者改不了的底層物理事實」（例如 IDAT 解壓後的資料總長度），繞過表面校驗機制找到真正不變的鐵證。
4. Misc 隱寫的媒介可以無限發散：不只藏在像素或元數據裡，連「播放速度」「音符長短」都能拿來編碼，遇到題目提示語帶有比喻（如「像水流」「像歌」）時，要跳脫「檢查像素」的直覺，改往時間軸、節奏等非視覺維度去思考。
