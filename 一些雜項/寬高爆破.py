import zlib
import struct

filename = 'misc34.png'

with open(filename, 'rb') as f:
    bin_data = f.read()

# 1. 提取 IHDR 數據塊（從第 12 到 29 字節，共 17 個字節）
ihdr = bin_data[12:29]

# 2. 提取 PNG 中原始紀錄的 CRC32 校驗碼（從第 29 到 33 字節，轉換為大端序 32 位無符號整數）
expected_crc = struct.unpack('>I', bin_data[29:33])[0]

print(f"[*] 讀取檔案: {filename}")
print(f"[*] 目標 CRC32: {hex(expected_crc)}")
print("[*] 開始爆破寬度和高度...")

# 3. 雙重迴圈爆破 (可根據需求調整範圍，如 1~3000)
found = False
for w in range(1, 2500):
    for h in range(1, 2500):
        # 構造新的 IHDR：[Chunk Name "IHDR"] + [Width (4 bytes)] + [Height (4 bytes)] + [Depth, ColorType, etc. (5 bytes)]
        # ihdr[:4] 為 b'IHDR'，ihdr[12:] 為後續的 5 個標頭設定字節
        new_ihdr = ihdr[:4] + struct.pack('>I', w) + struct.pack('>I', h) + ihdr[12:]
        
        # 計算當前構造 IHDR 的 CRC32 值
        if zlib.crc32(new_ihdr) == expected_crc:
            print(f"\n[+] 爆破成功！")
            print(f"[*] 正確寬度 (Width) : {w} (Hex: {hex(w)})")
            print(f"[*] 正確高度 (Height): {h} (Hex: {hex(h)})")
            
            # 自動修復圖片並存檔
            new_png = bin_data[:16] + struct.pack('>I', w) + struct.pack('>I', h) + bin_data[24:]
            with open('flag_fixed.png', 'wb') as f_out:
                f_out.write(new_png)
            print("[+] 已自動修復並存檔為 flag_fixed.png！")
            
            found = True
            break
    if found:
        break

if not found:
    print("[-] 未在指定範圍內找到正確的寬高，請嘗試擴大爆破範圍。")
