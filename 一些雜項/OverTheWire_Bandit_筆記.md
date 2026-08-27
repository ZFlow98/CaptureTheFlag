# OverTheWire Bandit 筆記（Level 0 ~ 33）

Bandit 是 OverTheWire 提供的入門級 Linux / 資安 wargame，透過 SSH 一關關破解拿到下一關密碼。目標是熟悉 Linux 指令、檔案系統、權限、基礎網路工具與簡單的逆向/腳本操作。

**連線方式（每一關通用）**：
```bash
ssh banditN@bandit.labs.overthewire.org -p 2220
```
把 `N` 換成關卡編號，密碼則是上一關破解出來的字串（Level 0 密碼是 `bandit0`）。

---

## 一、核心觀念總整理

### 1. 遊戲機制
- 每過一關，該關家目錄下（或用指定方式）會藏著**下一關的密碼**，用該密碼 SSH 登入下一個帳號即可晉級。
- 練習重點分佈：
  - Level 0~9：基礎檔案操作、隱藏檔、萬用字元、`find`、`grep`
  - Level 10~15：編碼/加密（Base64、ROT13、Hexdump、Gzip/Bzip2 多層壓縮、SSL/TLS）
  - Level 16~19：Port scanning（`nmap`）、資料庫連線、setuid 程式、`diff`
  - Level 20~26：網路程式（`nc`）、cron 排程、限制型 shell 逃逸、SSH 金鑰
  - Level 27~33：Git 版本控制歷史挖掘、進階逃逸與環境變數/工具鏈操作

### 2. 幾個貫穿全程的核心技能
- **善用 `man` 與 `--help`**：幾乎每一關都能靠翻手冊找到對應指令的正確用法，這是本遊戲最想訓練的習慣。
- **`find` 是萬用鑰匙**：搭配各種篩選條件（大小、權限、時間、檔案類型）能快速定位「藏起來的那個檔案」。
- **善用管線 `|` 組合指令**：`find | xargs`、`cat | grep`、`sort | uniq` 等組合貫穿整個遊戲。
- **檔名陷阱**：以 `-` 開頭、含空白、含特殊符號的檔名，需要用 `./檔名`、加引號、或用 `find -name` 定位再操作，不能直接 `cat 檔名`。
- **限制型環境的逃逸思路**：rbash（restricted bash）、指定執行檔（如只能跑某程式）等限制，重點在於找到能讓你「執行任意指令」的突破口（例如某些指令內建的 shell escape、或透過該程式讀寫任意檔案）。

---

## 二、各關重點紀錄

### Level 0 → 1：SSH 登入
- 目標：學會用 SSH 登入遠端主機。
```bash
ssh bandit0@bandit.labs.overthewire.org -p 2220
```
- 登入密碼固定為 `bandit0`。

### Level 0 → 1：讀取 readme
- 密碼藏在家目錄的 `readme` 檔案裡。
```bash
ls
cat readme
```

### Level 1 → 2：檔名是單一個 `-`
- 檔名為 `-` 會被 shell 誤判成「從標準輸入讀取」的參數，需要用相對路徑或 `--` 結尾參數規避：
```bash
cat ./-
# 或
cat < -
```

### Level 2 → 3：檔名含空白字元
- 檔名裡有空白（如 `spaces in this filename`），要加引號或用萬用字元：
```bash
cat "spaces in this filename"
# 或
cat spaces*
```

### Level 3 → 4：隱藏檔案（以 `.` 開頭）
- `ls` 預設不顯示隱藏檔，需加 `-a`：
```bash
cd inhere
ls -a
cat .hidden
```

### Level 4 → 5：用 `file` 判斷真正的檔案類型
- 資料夾裡有多個檔案，只有一個是純文字，其餘是誘餌（二進位/亂碼）：
```bash
cd inhere
file ./*
cat ./<真正是ASCII文字的那個檔名>
```

### Level 5 → 6：用 `find` 篩選條件定位檔案
- 提示：檔案大小恰好 1033 bytes、權限為 `-rw-r--r--`，且藏在多層目錄中：
```bash
find . -type f -size 1033c
```

### Level 6 → 7：全系統範圍搜尋，忽略錯誤訊息
- 提示：檔案位於系統任何地方，擁有者為 bandit7、群組為 bandit6、大小 33 bytes：
```bash
find / -user bandit7 -group bandit6 -size 33c 2>/dev/null
```
- `2>/dev/null` 把權限不足產生的錯誤訊息（Permission denied）丟棄，避免洗版。

### Level 7 → 8：用 `grep` 在大檔案中找關鍵字
- 密碼藏在一個很大的 `data.txt` 裡，關鍵字前面有個提示字串（如 `millionth`）：
```bash
grep millionth data.txt
```

### Level 8 → 9：找出檔案中「唯一出現一次」的那一行
- 用 `sort` + `uniq -u` 組合找出不重複的那一行：
```bash
sort data.txt | uniq -u
```

### Level 9 → 10：從二進位垃圾檔案中萃取可讀字串
- 檔案裡混雜了大量亂碼，密碼是其中含有特定格式（如多個 `=` 結尾，暗示 Base64 特徵）的可讀字串：
```bash
strings data.txt | grep '='
```

### Level 10 → 11：Base64 解碼
```bash
cat data.txt | base64 --decode
```

### Level 11 → 12：ROT13 解碼（字母位移 13）
```bash
cat data.txt | tr 'A-Za-z' 'N-ZA-Mn-za-m'
```

### Level 12 → 13：Hexdump 還原 + 多層壓縮解包
- `data.txt` 是一份被 `xxd` 轉成十六進位文字的檔案，且原始資料被**重複壓縮多次**（可能混合 gzip / bzip2 / tar 等格式）。
- 建議在 `/tmp` 建立工作目錄，避免弄亂家目錄：
```bash
mkdir /tmp/myworkdir123
cp data.txt /tmp/myworkdir123
cd /tmp/myworkdir123
xxd -r data.txt > data.bin       # 十六進位還原成二進位
file data.bin                     # 確認實際格式（會顯示 gzip/bzip2/...）
mv data.bin data.gz               # 依 file 判斷結果補上正確副檔名
gunzip data.gz                    # 解壓，會產生下一層檔案，重複 file→mv→解壓 直到得到純文字
```
- 核心心法：**「用 `file` 判斷真正格式 → 補上對應副檔名 → 用對應工具解壓 → 重複」**，直到 `file` 顯示 ASCII text 為止。

### Level 13 → 14：用私鑰 SSH 登入到自己
- 家目錄下有一把私鑰 `sshkey.private`，用它以 bandit14 身分登入 localhost 讀取密碼：
```bash
ssh -i sshkey.private bandit14@localhost -p 2220
cat /etc/bandit_pass/bandit14
```

### Level 14 → 15：用 `nc` 送出密碼給本機服務取得下一關密碼
- 某埠口的服務會在收到目前密碼後回傳下一關密碼：
```bash
nc localhost 30000
# 貼上目前密碼後按 Enter
```
- 或一行完成：
```bash
echo "目前密碼" | nc localhost 30000
```

### Level 15 → 16：改用 SSL/TLS 加密連線（`openssl s_client`）
- 這次的服務需要 SSL 連線，`nc` 無法直接用：
```bash
openssl s_client -connect localhost:30001 -quiet
```
輸入目前密碼後取得下一關密碼。

### Level 16 → 17：`nmap` 找出正確的服務埠口
- 只知道密碼藏在某個開放埠口（範圍 31000~32000）背後的 SSL 服務裡，需要先掃描找出正確埠口：
```bash
nmap -p 31000-32000 localhost --open
```
- 找到開放埠口後逐一測試哪個接受 SSL、哪個回傳的是私鑰（本題最終拿到的是一把 RSA 私鑰，而非明文密碼）：
```bash
openssl s_client -connect localhost:<埠口> -quiet
```
- 拿到私鑰後存成檔案（記得設定權限 `chmod 600`），再用它登入下一關：
```bash
chmod 600 sshkey.private
ssh -i sshkey.private bandit17@localhost -p 2220
```

### Level 17 → 18：`diff` 比對兩個版本檔案找出差異
- 家目錄有 `passwords.old` 與 `passwords.new` 兩個檔案，密碼是被修改過的那一行：
```bash
diff passwords.old passwords.new
```

### Level 18 → 19：登入時就被登出（`.bashrc` 陷阱），用非互動指令繞過
- 這關的 `.bashrc` 被設定成一登入就自動登出，導致沒辦法用一般方式互動操作。
- 解法：用 SSH 的**遠端指令執行**功能，不進入互動 shell，直接執行指令並拿到輸出：
```bash
ssh bandit18@bandit.labs.overthewire.org -p 2220 cat readme
```

### Level 19 → 20：setuid 二進位程式，以更高權限執行指令
- 家目錄有一個 setuid 執行檔（如 `bandit20-do`），執行時會以 bandit20 的身分跑指令：
```bash
./bandit20-do cat /etc/bandit_pass/bandit20
```

### Level 20 → 21：`suconnect` 程式，需自架監聽服務配合驗證
- 家目錄的 `suconnect` 程式會連到你指定的埠口，讀一行文字比對是否等於目前密碼，正確的話回傳下一關密碼。
- 解法：先用 `nc` 在背景啟動一個監聽埠口並回傳目前密碼，再執行 `suconnect` 連過去：
```bash
echo "目前密碼" | nc -l -p 12345 &
./suconnect 12345
```

### Level 21 → 22：檢查 `cron` 排程找出自動執行的腳本
- 提示密碼由 cron 定期任務產生，去 `/etc/cron.d/` 找出對應設定與腳本：
```bash
cat /etc/cron.d/cronjob_bandit22
cat /usr/bin/cronjob_bandit22.sh
```
- 讀懂腳本邏輯（通常會把下一關密碼寫到某個 `/tmp` 底下的暫存檔），直接去讀那個暫存檔即可：
```bash
cat /tmp/<腳本產生的暫存檔名>
```

### Level 22 → 23：cron 腳本用變數/雜湊值動態產生暫存檔名
- 比上一關更進階，腳本裡用 `whoami` 加上 `md5sum` 之類的方式動態計算暫存檔名，需要自己手動照腳本邏輯算一次：
```bash
echo -n "bandit23" | md5sum
```
再去 `/tmp` 底下找出對應檔名讀取密碼。

### Level 23 → 24：cron 腳本會執行 `/var/spool/bandit24` 底下每個人放的腳本
- 觀察腳本行為（會把該資料夾內所有檔案當作 bandit24 身分執行，然後刪除），寫一個腳本把密碼複製出來、放進該資料夾等待被自動執行：
```bash
mkdir /tmp/mywork24
cd /tmp/mywork24
cat > script.sh << 'EOF'
#!/bin/bash
cat /etc/bandit_pass/bandit24 > /tmp/mywork24/result.txt
chmod 666 /tmp/mywork24/result.txt
EOF
chmod 777 script.sh
cp script.sh /var/spool/bandit24/
# 等待一分鐘讓 cron 執行
cat /tmp/mywork24/result.txt
```

### Level 24 → 25：暴力窮舉 4 位數 PIN（配合密碼一起送出）
- 有個服務監聽在某埠口，需要送出「目前密碼 + 4 位數字 PIN」的組合，PIN 正確才會回傳下一關密碼；用腳本窮舉所有 0000~9999 組合：
```bash
for i in $(seq -w 0000 9999); do
  echo "目前密碼 $i"
done > pins.txt

cat pins.txt | nc localhost <埠口> > result.txt
grep -i "Correct" result.txt
```

### Level 25 → 26：限制型 Shell 逃逸（用私鑰 + 特殊終端設定）
- 私鑰登入後的 shell 會直接執行某個限制程式（如 `more` 分頁一個檔案）就自動登出。
- 解法：把終端機視窗縮小，讓 `more` 顯示內容時觸發「分頁等待」，此時按 `v` 進入 `vi` 編輯器（`more`/`less` 內建的呼叫外部編輯器功能），再從 `vi` 內部逃出到正常 shell：
```bash
ssh -i bandit26.sshkey bandit26@localhost -p 2220
# 畫面顯示分頁等待時按 v 進入 vi
:set shell=/bin/bash
:shell
```

### Level 26 → 27：逃出限制 shell 後利用 setuid 程式跳到下一關
- 進入正常 shell 後，家目錄有個屬於 bandit27 的 setuid 程式（如 `bandit27-do`），用它以 bandit27 身分執行指令：
```bash
./bandit27-do cat /etc/bandit_pass/bandit27
```

### Level 27 → 28：Git repository，直接 clone 出來就有密碼
```bash
git clone ssh://bandit27-git@localhost:2220/home/bandit27-git/repo /tmp/repo27
cat /tmp/repo27/README
```

### Level 28 → 29：密碼被後續 commit 覆蓋，需翻 Git log 找歷史版本
```bash
git clone ssh://bandit28-git@localhost:2220/home/bandit28-git/repo /tmp/repo28
cd /tmp/repo28
git log --all
git show <某個較舊的commit hash>
```

### Level 29 → 30：密碼藏在其他分支（branch）
```bash
git clone ssh://bandit29-git@localhost:2220/home/bandit29-git/repo /tmp/repo29
cd /tmp/repo29
git branch -a
git checkout <分支名稱>
cat README
```

### Level 30 → 31：密碼藏在 tag
```bash
git clone ssh://bandit30-git@localhost:2220/home/bandit30-git/repo /tmp/repo30
cd /tmp/repo30
git tag
git show <tag名稱>
```

### Level 31 → 32：需要照 repo 內的規則新增指定檔案並 push 才會揭露密碼
- `README` 說明要新增一個內容為 `May I come in?` 的檔案 `key.txt` 並 push 上去，push 成功後伺服器端會回傳密碼：
```bash
git clone ssh://bandit31-git@localhost:2220/home/bandit31-git/repo /tmp/repo31
cd /tmp/repo31
cat README   # 確認具體要求
echo "May I come in?" > key.txt
git add key.txt
git commit -m "add key"
git push origin master
```
- 若 push 被 `.gitignore` 或既有規則擋下，需要照提示調整（例如強制加入被忽略的檔案 `git add -f key.txt`）。

### Level 32 → 33：逃出 `UPPERCASE SHELL`（一切輸入都被轉大寫）
- 登入後畫面顯示 `THIS IS A SETUID UPPERCASE SHELL`，你輸入的任何指令都會被強制轉成大寫再執行，導致正常小寫指令全部失效。
- 解法：利用 Bash 語法特性，用**不含小寫字母**也能觸發 shell 的技巧，例如透過 `$0`（呼叫自身，通常會啟動一個新的、未受限制的 bash）：
```bash
$0
```
- 進入正常 shell 後即可用一般小寫指令讀取密碼：
```bash
cat /etc/bandit_pass/bandit33
```

### Level 33：最終關（截至目前版本的最後一關）
- 通常會提示你已完成 Bandit 系列，可以繼續挑戰 OverTheWire 的其他 wargame（如 Natas、Leviathan、Krypton 等）。

---

## 三、工具與指令速查表

```bash
# 檔案探索
ls -a                          # 顯示隱藏檔
file 檔名                      # 判斷真實檔案格式
find / -user X -group Y -size Nc 2>/dev/null   # 依擁有者/群組/大小全系統搜尋

# 文字處理
grep 關鍵字 檔名                # 搜尋含關鍵字的行
sort 檔名 | uniq -u             # 找出唯一不重複的行
strings 檔名 | grep 模式        # 從二進位檔案抽取可印字串再篩選

# 編碼/解碼
base64 --decode                # Base64 解碼
tr 'A-Za-z' 'N-ZA-Mn-za-m'      # ROT13
xxd -r                          # 還原 hexdump 為二進位

# 壓縮格式判斷與解壓（依 file 判斷結果選對應指令）
gunzip / gzip -d                # .gz
bunzip2                         # .bz2
tar -xf                         # .tar
unxz                            # .xz

# 網路連線
nc localhost <port>             # 明文 TCP 連線
openssl s_client -connect localhost:<port> -quiet   # SSL/TLS 連線
nmap -p <範圍> localhost --open # 掃描開放埠口

# 權限與身分切換
chmod 600 私鑰檔                # 私鑰權限必須夠嚴格才能被 ssh 接受
ssh -i 私鑰檔 使用者@localhost -p 2220
./setuid程式 指令                # 以程式擁有者身分執行指令

# Git 考古
git log --all                   # 看所有歷史 commit
git show <commit/tag/branch>    # 查看特定版本內容
git branch -a                   # 列出所有分支
git tag                         # 列出所有標籤
```

---

## 四、學習方法心得
1. Bandit 的每一關「Level Goal」說明本身就是最重要的線索，**先仔細讀懂題目在問什麼**，往往能直接猜到該用哪個指令類別（find / grep / nc / cron...）。
2. 這個系列刻意把 Linux 常用指令拆成一關一個技能點，建議搭配 `man 指令名稱` 練習查手冊的習慣，而不是每次都上網查，這樣之後遇到變化題（换個參數、換個情境）也能自己推出解法。
3. Level 12（多層壓縮解包）與 Level 27~31（Git 考古）是很多新手的第一個卡關點，核心心法都是「**建立一套可重複的排查流程**」（`file → mv 副檔名 → 對應工具解壓，重複執行` / `git log、branch、tag 全部翻過一輪`），與 CTF Misc 系列「養成 SOP」的心法是一致的。
4. Level 25~26、32 這類「限制型 shell 逃逸」題，本質上是在訓練「當你被限制只能用某個特定介面時，如何找到該介面本身留下的後門或呼叫外部程式的能力」，這個思路在之後接觸 Web/Pwn 的沙箱逃逸題時會反覆用到。
