# CTF Day 3 筆記（ctfshow misc14、misc16 ~ misc21）

延續 Day1（misc4~8 檔案頭/附加資料）、Day2（misc9~13 PNG 結構隱寫）的基礎，Day3 開始接觸 **JPEG 多檔拼接**、**壓縮檔特徵碼手動提取**、**EXIF 元數據隱寫**，以及各種「數值轉換 / 諧音編碼」的腦洞題。

---

## 一、核心觀念總整理

### 1. 檔案「身份證字號」再複習：Magic Bytes 判斷法
- 電腦判斷檔案種類不是看副檔名，是看檔案內部固定的**開頭特徵碼**。工具（binwalk、zsteg 等）都是靠掃描這些特徵碼來「考古」出藏在檔案內部的其他格式資料。
- 本篇新增的常見特徵碼：

| 格式 | Hex 開頭 | ASCII |
|---|---|---|
| JPEG 開頭 | `FF D8 FF` | — |
| JPEG 結尾 | `FF D9` | — |
| BZ2 壓縮檔 | `42 5A 68 [31~39]` | `BZh[1-9]`（數字代表壓縮區塊大小，9 為最高 900k） |
| ZIP 壓縮檔 | `50 4B 03 04` | `PK..` |

- **亂碼檔案為什麼 binwalk 能找到東西**：文字編輯器用 UTF-8/ANSI 硬解二進位資料才會顯示亂碼，不代表檔案壞掉；binwalk 不管檔名與外觀，直接逐位元組掃描找特徵碼，只要內部殘留某種格式的 Magic Bytes 就能定位出來。常見情境：①副檔名被刻意改掉偽裝成別的格式；②多個檔案被直接拼接（黏在一起）。

### 2. JPEG 多檔拼接隱寫（misc14 手法）
- 概念與 Day2 的 PNG 多 IDAT 類似，但換成 JPEG：一個檔案裡藏了多張 JPEG，每張都有自己的 `FF D8`（開頭）與 `FF D9`（結尾）。
- **binwalk / foremost 有時會失效**（作者故意動過手腳讓自動分離工具「看得到抓不下來」），此時需要換手動或指定參數的做法：
  - `binwalk -D=jpeg misc14.jpg`：強制指定用 jpeg 的規則掃描提取，比預設的 `-e` 更準。
  - `dd if=misc14.jpg of=flag.jpg skip=<偏移量> bs=1`：用 binwalk 掃出的偏移量（十進位），直接用 `dd` 從該位置切到檔案結尾。
  - 010 Editor / WinHex 手動法：搜尋所有 `FF D8`，注意**不是第一個就是答案**，要逐一檢查（本題是第三個），找到正確位置後把它之前的資料全部刪除、另存新檔。
- 心法與 Day2「連刪 8 個 IDAT」相同：真正的隱藏圖不一定緊跟在第一個標記後面，可能前面還有干擾用的假標記或殘留資料，要用位移量或逐一嘗試來確認正確切點。
- **Flag**：`ctfshow{ce520f767fc465b0787cdb936363e694}`

### 3. IDAT 補充定義（延續 Day2）
- **IDAT（Image Data Chunk）**：PNG 中真正存放像素圖像資料的區塊，內容是經過 zlib（Deflate）壓縮過的資料。
- 一張圖可以有多個連續 IDAT 塊，解碼器會自動依序拼接、解壓還原成畫面。
- CTF 常見考法：①插入異常/多餘的 IDAT 塊藏第二張圖（Day2 misc11、12）；②在 IDAT 資料**最尾端**（zlib 串流結束後）直接附加額外資料，形成「圖片檔尾巴多黏了一段東西」的隱寫（本篇 misc16、17 屬於此類）；③把 `IDAT` 標籤名稱本身竄改（如改成 `idat`）讓圖片無法開啟，需手動改回。

### 4. PNG 尾端附加壓縮檔（misc16、17 手法，比 Day1 misc5 更進階）
- Day1 的 misc5 是附加**未壓縮**的明文資料在 `IEND` 之後；本篇進階版是附加**已壓縮**的檔案（7z / bz2 等），必須先正確切出、再解壓才看得到內容。
- **最簡單情境（misc16）**：`binwalk -e` 或直接用 7-Zip／WinRAR 對 png 檔「解壓縮到...」就能抓出附加的壓縮包，因為壓縮軟體會自動忽略前面的圖片資料、找到壓縮檔起始位置。
- **較棘手情境（misc17）**：`binwalk -e` 切出來的壓縮檔（如 `.bz2`）打不開、顯示毀損，常見原因：
  1. **binwalk 切割位置不準**：把 PNG 正文的尾巴一起切了進去，導致壓縮檔開頭不乾淨。
  2. **誤報（False Positive）**：zlib 壓縮過的隨機位元剛好被誤判成其他壓縮格式的特徵碼。
  3. **標頭被刻意竄改**：作者手動改掉了壓縮檔開頭幾個位元組。
- **正確解法（zsteg）**：`zsteg` 能明確標出「zlib 串流結束後還有多少額外資料（extra data）」，並且可以乾淨地把這段資料單獨匯出，不會像 binwalk 那樣誤切：
  ```bash
  zsteg -a misc17.png          # 先確認訊息：xxxx bytes of extra data after zlib stream
  zsteg -E 'extradata:0' misc17.png > flag_data   # 乾淨匯出額外資料
  binwalk flag_data             # 確認裡面藏的是什麼格式
  binwalk -e flag_data          # 二次分離，取得內部檔案
  ```
  - 若二次分離後的檔案本身沒有副檔名、打開仍是亂碼，用十六進位編輯器檢查開頭 Magic Bytes（例如發現是 `89 50 4E 47` = PNG），手動補上正確副檔名即可打開。
- **這題的兩條可行路線**：
  - 路線 A（Linux）：`zsteg` 匯出乾淨資料 → `binwalk -e` 二次分離 → 依 Magic Bytes 改副檔名。
  - 路線 B（Windows GUI）：TweakPNG 開圖 → `Edit → Combine All IDAT` 合併所有 IDAT 塊 → 存檔 → 再用 binwalk 分離出隱藏圖片。
- **Flag（misc16）**：`ctfshow{a7e32f131c011290a62476ae77190b52}`
- **Flag（misc17）**：`ctfshow{325d60c208f728ac17e5f02d4cf5a839}` / `ctfshow{0fe61fc42e8bbe55b9257d251749ae45}`（不同版本題目 Flag 略有差異，依實際解出結果為準）

### 5. EXIF／元數據隱寫（misc18、19、21）
- 圖片除了 PNG 的 `tEXt` 塊，JPEG／TIFF 格式還有一種常見的隱寫位置：**EXIF 元數據**（相機型號、作者、標題、解析度、序號等欄位）。
- 讀取工具：
  - Linux：`exiftool 檔名`
  - Windows：隨波逐流拖入圖片直接看 Metadata 面板；或用 `strings 檔名 | grep ctf` 抓明文片段
- **常見出題套路**：Flag 被拆成好幾段，分別塞進不同的 EXIF 欄位，需要**按正確順序**把各欄位內容拼接起來：
  - misc18：分別藏在標題（Title）、作者（Author）、相機型號（Model）等欄位。
  - misc19：分別藏在 `DocumentName`（文件名稱）與 `HostComputer`（主機電腦）兩個欄位，各佔 Flag 的前後半段。
- **進階版：數值需要轉換再拼接（misc21）**：EXIF 裡的 `X Resolution`、`Y Resolution`、`X Position`、`Y Position` 四個欄位裡的**十進位數字**，要先各自轉成**十六進位（小寫）**，再依序拼接成完整 Flag。這題純粧文字或序號直接套用都不對，必須動手做進制轉換。
- 心法：拿到 EXIF 資訊後，先看有沒有直接是 `ctfshow{...}` 格式的明文片段；如果只看到零散數字/序號，要考慮「這些數字是否需要進制轉換（十進位→十六進位）」再重新排列。
- **Flag（misc18）**：`ctfshow{325d60c208f728ac17e5f02d5749ae45}`
- **Flag（misc19）**：`ctfshow{dfdcf08038cd446a5eb50782f8d3605d}`
- **Flag（misc21）**：`ctfshow{e8a221498d5c073b4084eb51b1a1686d}`

### 6. 中文諧音編碼（misc20，純腦洞題）
- 檔案內容用**簡體中文同音字**唸出 Flag 的每個英文字母/數字/符號（例如「西替爱抚秀」= ctfshow、「大括号」= `{`）。
- 沒有固定工具可以解，純粹靠**讀音聯想**逐字翻譯回英數字元，是 Misc 領域「知識點零碎、無標準解法」的典型例子。
- **Flag**：`ctfshow{c97964b1aecf06e1d79c21ddad593e42}`

---

## 二、各題重點紀錄

### misc14：JPEG 多檔拼接，自動工具失效需手動/指定參數提取
- 檔案內藏了不只一張 JPEG，`binwalk -e` 預設無法自動分離。
- 解法三選一：
  1. `binwalk -D=jpeg misc14.jpg`（指定格式強制提取）
  2. `dd if=misc14.jpg of=flag.jpg skip=<偏移量> bs=1`（依 binwalk 掃出的位移量切割）
  3. 010/WinHex 手動搜尋所有 `FF D8`，找到正確的一組（本題是第 3 個）刪除其前方資料
- **Flag**：`ctfshow{ce520f767fc465b0787cdb936363e694}`

### misc16：PNG 尾端附加 7z（LZMA）壓縮包，工具能直接分離
- 出題手法：Flag 檔案先用 LZMA 壓縮成 7z，再直接黏在 PNG 檔案尾端。
- 這題沒有刻意反制自動化工具，直接 `binwalk -e misc16.png` 就能生成 `_misc16.png.extracted` 資料夾，內含無副檔名檔案（如 `DD4`），用記事本打開即為 Flag。
- 替代解法：直接用 7-Zip / WinRAR 對 png 檔案「解壓縮到...」，一樣能抓出附加壓縮包。
- **Flag**：`ctfshow{a7e32f131c011290a62476ae77190b52}`

### misc17：PNG 尾端附加壓縮檔，但 binwalk 直接分離會損毀
- `binwalk -e` 切出的壓縮檔打不開，因為切割位置不準或格式誤判。
- 正確解法：`zsteg` 先確認 zlib 串流後的額外資料量，用 `zsteg -E 'extradata:0'` 乾淨匯出，再交給 `binwalk -e` 做二次分離；分離出的無副檔名檔案要靠十六進位開頭判斷真實格式（本題其實是 PNG）後手動改副檔名。
- 替代解法（Windows）：TweakPNG 合併所有 IDAT 塊後存檔，再用 binwalk 分離。
- **安裝 zsteg 補充**（Kali 常見坑）：
  ```bash
  sudo apt update
  sudo apt install ruby ruby-dev build-essential -y
  sudo gem install zsteg
  zsteg misc17.png
  ```
- **Flag**：`ctfshow{325d60c208f728ac17e5f02d4cf5a839}`

### misc18：Flag 拆散藏在多個 EXIF 欄位
- 畫面顯示 `{there_is_no_flag_here}` 是誘餌，真正 Flag 被拆成好幾段分別放在標題、作者、相機型號等 EXIF 欄位。
- 用隨波逐流或 `exiftool` 查看各欄位內容，按順序拼接。
- **Flag**：`ctfshow{325d60c208f728ac17e5f02d5749ae45}`

### misc19：Flag 兩段式藏在 TIFF 的 DocumentName / HostComputer
- `exiftool misc19.tif` 直接印出兩個關鍵欄位：
  - `Document Name`: 前半段
  - `Host Computer`: 後半段
- 替代解法：`strings misc19.tif | grep ctf`；或用記事本/010 直接搜尋 `ctf` 找到分成兩截的字串再手動拼接。
- **Flag**：`ctfshow{dfdcf08038cd446a5eb50782f8d3605d}`

### misc20：中文諧音字謎題
- 檔案內容是一串中文同音字，需逐字對照讀音還原成 `ctfshow{...}` 格式。
- 無固定解題工具，純粹腦筋急轉彎 / 讀音聯想。
- **Flag**：`ctfshow{c97964b1aecf06e1d79c21ddad593e42}`

### misc21：EXIF 座標值需轉十六進位再拼接
- `exiftool misc21.jpg` 查看四個欄位（依序）：
  1. X Resolution
  2. Y Resolution
  3. X Position
  4. Y Position
- 每個欄位的十進位數字各自轉換成十六進位（英文小寫），依序拼接進 `ctfshow{}` 中。
- 卡關重點：光看到序號或原始十進位數字直接套用一定是錯的，必須先做進制轉換這一步。
- **Flag**：`ctfshow{e8a221498d5c073b4084eb51b1a1686d}`

---

## 三、工具與指令補充速查

```bash
# 指定格式強制提取（binwalk 預設分離失效時）
binwalk -D=jpeg misc14.jpg

# 用偏移量手動切割檔案
dd if=misc14.jpg of=flag.jpg skip=<偏移量> bs=1

# 安裝並使用 zsteg（PNG 專用隱寫分析，能看 extra data 大小）
sudo apt install ruby ruby-dev build-essential -y
sudo gem install zsteg
zsteg -a 檔名.png
zsteg -E 'extradata:0' 檔名.png > 匯出檔名

# 讀取 EXIF 元數據（找拆分藏字段的 Flag）
exiftool 檔名

# 直接用壓縮軟體嘗試解壓（PNG/JPG 尾端常附加合法壓縮檔）
# Windows：右鍵檔案 → 7-Zip/WinRAR → 解壓縮到...
```

### 工具選用心法（延續 Day2）
| 情境 | 優先工具 |
|---|---|
| 檔案尾端有沒有附加資料，且想知道確切大小 | `zsteg -a`（PNG）優於 `binwalk`，因為它會明確報出 extra data 位元數 |
| 附加資料是常見壓縮格式（zip/7z） | 直接嘗試用壓縮軟體開啟，比手動切割省事 |
| 自動分離工具切出來的檔案損毀 | 別急著放棄，先確認是「切割位置不準」還是「誤判格式」，換用更精準的工具（zsteg）重新乾淨匯出 |
| 多檔拼接但自動工具失效 | 換成指定格式參數（`-D=`）或用位移量手動 `dd` 切割 |
| Flag 找不到明顯的圖片異常 | 檢查 EXIF／元數據，注意是否分段藏放、是否需要進制轉換 |

---

## 四、學習方法心得（延續 Day1、Day2）
1. 這幾題再次印證：**同一個外觀問題（PNG 尾端有附加資料）可能有難度分層**——misc16 是明碼可直接分離，misc17 則刻意讓自動工具失敗，逼你換更精確的工具（zsteg）或改用手動切割思路。遇到自動工具失效時，不要死磕同一個指令，先確認「是工具切錯位置」還是「格式判斷錯誤」，再對症換工具。
2. **進制轉換是新手容易漏掉的一步**（misc21）：EXIF/序號類題目除了直接讀取文字，也要留意欄位裡的「數字」是否需要先做十進位→十六進位等轉換，才是最終答案的一部分。
3. Misc 題目有一類**沒有固定工具解法**，純靠觀察與聯想（misc20 諧音字），提醒自己不要每題都優先想「該用哪個工具」，有時候答案就是直接讀字面內容去理解。
4. 持續執行 Day1 提出的 SOP：`file` 確認格式 → `binwalk`/`zsteg`/`foremost` 找隱藏資料 → 檢查 Chunk/Magic Bytes 異常 → `strings`/`exiftool` 找明文或元數據 → 卡關 20 分鐘看 Writeup 破題句。
