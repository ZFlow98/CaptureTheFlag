# CTF Day 1 筆記（ctfshow misc4 ~ misc8）

## 一、核心觀念總整理

### 1. 副檔名 ≠ 檔案本質
- 副檔名只是給作業系統「預設用哪個軟體開啟」的標籤，檔案真正的身分由**檔案頭（Magic Bytes）**決定。
- 許多看圖軟體（BandiView、Honeyview）具備容錯機制，會自動讀取真實 Header 來渲染，所以就算副檔名亂改也能開圖 —— 這也是為什麼很多人「暴力全改 png/jpg」也能過關的原因。

### 2. 常見檔案 Magic Bytes（不用死背，混熟即可）

| 格式 | Hex 開頭 | ASCII 特徵 |
|---|---|---|
| PNG | `89 50 4E 47` | `.PNG` |
| JPEG | `FF D8 FF`結尾為`FF D9` | `ÿØÿ` |
| GIF | `47 49 46 38` | `GIF8` |
| BMP | `42 4D` | `BM` |
| TIFF | `49 49 2A 00` / `4D 4D 00 2A` | — |
| WebP | `52 49 46 46 ... 57 45 42 50` | `RIFF...WEBP` |
| ZIP | `50 4B 03 04` | `PK..` |
| RAR | `52 61 72 21` | `Rar!` |

查不熟的格式：直接用 `file` 指令、Google 搜尋 hex 開頭，或丟進 010 Editor 讓範本自動判斷即可，不需要硬背。

### 3. 常見隱寫手法
- **附加數據（Append）**：把 Flag 直接寫在檔案結尾標記之後（如 PNG 的 `IEND` 之後、JPEG 的 `EOI (FF D9)` 之後）。
- **偽裝格式**：檔案本體其實是 ZIP，副檔名卻改成 png/txt。
- **改寬高（IHDR 竄改）**：故意改小 PNG 的 Height/Width，讓下半部圖被裁切，出現 CRC Mismatch 即為訊號。
- **圖中圖 / 多檔拼接**：兩張 PNG（或多個檔案）直接黏在一起，第二個 Header（`89 50 4E 47`）出現在檔案中段。
- **縮圖藏字（Thumbnail / Exif）**：Flag 藏在 JPEG 內嵌的縮圖或 Exif／Comment 區塊，一般文字編輯器因 NUL byte 截斷或編碼問題根本看不到。
- **Base64 特徵**：大量重複字元（如 `TUUUUUU...`）通常代表 Base64 編碼內容，需要 `base64 -d` 解碼。

### 4. 為什麼記事本/Notepad++常常找不到東西
- 純文字編輯器會用 UTF-8/ANSI 強制解讀整個檔案，遇到 `00`（NUL）或控制字元容易把字串截斷、跳過或顯示亂碼。
- 二進位檔案本身就不是給文字編輯器讀的，用它來搜尋隱藏字串不可靠。
- **解法**：改用 Hex Editor（010 Editor / HxD）用 ASCII 字串模式搜尋，或直接用終端機 `strings` + `grep`。

---

## 二、各題重點紀錄

### misc4：六個 txt，其實是六種圖片格式
- 六個檔案 Header 分別對應：PNG / JPEG / BMP / GIF / TIFF / WebP。
- 正解：用 Hex 工具辨識各檔案頭，改回正確副檔名，依序打開拼出完整 Flag。
- 大部分玩家的「暴力解」：全改成 png 或 jpg，直接丟進看圖軟體也能開（因為軟體會自動判斷真實格式）。
- **Flag**：`ctfshow{4314e2b15ad9a960e7d9d8fc2ff902da}`

### misc5：PNG 尾端附加數據
- 圖片本身故意顯示「there is no flag」，是誘餌。
- 真正 Flag 藏在 PNG 的 `IEND` 標記**之後**（附加數據），一般看圖軟體畫到 IEND 就停止繪圖，看不到。
- 解法：用記事本/010 Editor/WinHex 拉到檔案最底端；或該檔案其實是 ZIP，需先解壓才能看到內部 PNG。
- **Flag**：`ctfshow{2a476b4011805f1a8e4b906c8f84083e}`

### misc6：JPEG 內部資料藏字串
- 一樣是「there is no flag」誘餌圖。
- Flag 不在畫面上，而是以純文字直接寫在 JPEG 內部資料/Exif 區段中（非結尾附加）。
- 快速解法（終端機一行搞定）：
  ```bash
  strings ./misc6.jpg | grep -E 'flag|ctf'
  ```
  - `strings`：從二進位檔案中提取可印刷 ASCII 字串。
  - `grep -E 'flag|ctf'`：篩選出含關鍵字的行。
- **Flag**：`ctfshow{d5e937aefb091d38e70d927b80e1e2ea}`

### misc7：藏在 JPEG 縮圖（Thumbnail）裡
- Flag 藏在 JPEG 內嵌的縮圖資料（`ifd1ThumbnailImage`），且關鍵字故意沒寫全 `ctfshow`，只搜 `flag` 才找得到。
- 010 Editor 搜尋設定重點：`Ctrl+F` → 搜尋模式要選 **ASCII 字符**，不要選「十六進制字節」（否則打英文字會報「無效的尋找值」）。
- 記事本找不到的原因：NUL byte / 控制碼截斷、編碼強制換行，破壞了連續字串。
- **Flag**：`ctfshow{c5e77c9c289275e3f307362e1ed86bbj}`

### misc8：兩張 PNG 黏在一起（圖中圖）
- 010 Editor 的 PNG Template 解析到一半報錯（`ERROR: 聲明中的數組大小無效`），代表 Chunk 數異常 → 通常是檔案裡塞了第二個 PNG。
- **解法 A（Kali / WSL，最主流）**：
  ```bash
  binwalk misc8.png      # 先確認是否有內嵌檔案
  foremost misc8.png -o output/   # 自動分離出多個檔案
  ```
  分離後在 `output/png/` 資料夾會看到兩張圖，第二張才是 Flag。
- **解法 B（純 Windows，010 Editor / HxD 手動裁切）**：
  1. `Ctrl+F` 搜尋 Hex Bytes：`89 50 4E 47`（PNG 開頭），會搜到兩筆。
  2. 定位第二筆位置，把「第二筆之前」的所有 Byte 全部刪除。
  3. 另存新檔為 `flag.png` 打開查看。
- **Flag**：`ctfshow{1df0a9a3f709a2605803664b55783687}`

---

## 三、工具與環境筆記

### 1. Hex Editor 選擇
| 工具 | 特點 | 建議情境 |
|---|---|---|
| 記事本 / Notepad++ | 快速搜文字，但會被二進位資料破壞/截斷 | 只是想搜個關鍵字時堪用 |
| HxD | 免費、輕量、純十六進位顯示 | 偶爾看 Hex、不想處理授權 |
| 010 Editor | 付費（30天試用），有 Binary Template 自動拆解檔案結構、標紅 CRC 錯誤 | 長期刷 CTF misc 首選 |

### 2. 常用指令 / 工具速查

```bash
# 判斷真實檔案格式
file 檔名

# 看檔案開頭 hex
head -c 16 檔名 | xxd

# 批次依 header 重新命名（Bash）
for f in {1..6}.txt; do
    header=$(hexdump -n 4 -e '1/1 "%02X"' "$f")
    case "$header" in
        "89504E47") ext="png" ;;
        "FFD8FF"*)  ext="jpg" ;;
        "424D"*)    ext="bmp" ;;
        "47494638") ext="gif" ;;
        "49492A00"|"4D4D002A") ext="tif" ;;
        "52494646") ext="webp" ;;
        *)          ext="bin" ;;
    esac
    mv "$f" "${f%.txt}.$ext"
done

# 提取檔案中可讀字串並篩選關鍵字
strings 檔名 | grep -E 'flag|ctf'

# 檢查是否有內嵌／隱藏檔案
binwalk 檔名
binwalk -e 檔名     # 嘗試自動解壓

# 分離拼接在一起的多個檔案（圖中圖常用）
foremost 檔名 -o output/

# PNG 專用隱寫掃描（LSB、Alpha 通道等）
zsteg -a 檔名.png

# JPG/WAV 隱寫嘗試空密碼提取
steghide extract -sf 檔名.jpg -p ""
```

### 3. Linux 環境選擇
- **Kali Linux（虛擬機）**：工具最齊全，開箱即用，適合照著 Writeup 打指令。
- **WSL2 + Ubuntu**：輕量、不用開整台虛擬機，可搭配 Windows 上的 010 Editor 一起用，是進階玩家常見組合。
- **純 Windows 手動流**：靠 010 Editor / HxD 手動裁切，適合還沒建好 Linux 環境時應急。
- 結論：**重點是熟悉 Linux 指令與工具鏈本身**，不是一定要用 Kali 這套系統。

---

## 四、學習方法心得
1. **卡關超過 20 分鐘就去看 Writeup**——先看別人用了「什麼工具/關鍵詞」，不要看完整答案，自己動手做一次再記錄下來。
2. 遇到新題目的檢查 SOP：
   - `file` 確認真實格式
   - `binwalk` / `zsteg` / `foremost` 檢查是否有隱藏檔案
   - 010 Editor 打開看 Template 結果，注意 CRC 錯誤、多個 Header
   - `strings | grep` 找明文 Flag
   - 都沒有 → 查 Writeup 找思路
3. CTF 本質是**累積工具箱與套路庫**，不需要背魔術標頭或死記工具用法，用多了自然熟練。
