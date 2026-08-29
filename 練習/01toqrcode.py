from PIL import Image

with open(r"C:\Users\BensonDC\Desktop\hint.txt",'r') as f:
    lines = f.readlines()
    length = len(lines)-1
    img = Image.new('1', (length,length)) # Image創建圖片的方法，1表示黑白兩色
    pixels = img.load() # 載入像素至記憶體，pixels是二維陣列
    for i in range (length):
        for j in range (length):
            if lines[i][j]=='1':
                pixels[j,i]=0
            else:
                pixels[j,i]=255

    img.save(r"C:\Users\BensonDC\Desktop\qrcode.png")
    
            
            
