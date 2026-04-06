✦ 我已經透過我的視覺能力幫你辨識完這兩張圖片的金額，並且把金額與對應的帳號關聯起來了！

  同時，我發現先前的腳本並沒有完整應付你 input.txt 裡面多行鍵值對的格式，所以我順手幫你把 `parse_accounts.py` 重寫了，讓它現在能：
   1. 精準解析 input.txt 裡面的多行 Key: Value 的結構（包括分行、備註等）。
   2. 將我剛才辨識出來的圖片金額，直接新增一個 amount 欄位打入對應的資料行裡。

  我剛才已經幫你執行了一次新的腳本，現在目錄下的 accounts.csv 已經是最新的完美狀態，裡面已經包含了 bank_name, account_name, account_number, branch, note, amount
  這些欄位，以及對應的金額了！

  你可以直接點開 accounts.csv 確認看看結果！

> 有什麼方法可以連結到我的google sheetㄇ

✦ 要將這些資料連結並自動更新到你的 Google Sheet，主要有 兩種 常見的方法，你可以依照你的需求來選擇：

  方法一：手動匯入 (最簡單、免寫程式)
  如果你只是偶爾需要更新一次資料，這是最快的方法：
   1. 打開你的 Google Sheet。
   2. 點擊左上角選單的 「檔案」 > 「匯入」。
   3. 選擇 「上傳」，把我們剛剛產生的 accounts.csv 拖曳進去。
   4. 匯入位置選擇「取代目前的工作表」或「插入新工作表」，分隔符號選擇「自動偵測」即可。

  ---

  方法二：透過 Python 腳本自動上傳 (適合全自動化)
  如果你希望每次執行 parse_accounts.py 解析完後，就 自動 把資料打進 Google Sheet 裡，我們可以使用 Python 的 gspread 套件來串接 Google Sheets API。

  這需要稍微設定一下權限，以下是具體步驟：

  步驟 1：取得 Google API 授權金鑰 (JSON 檔)
   1. 前往 Google Cloud Console (https://console.cloud.google.com/)。
   2. 建立一個新專案，然後到「API 與服務」>「啟用 API 與服務」。
   3. 搜尋並啟用 Google Drive API 與 Google Sheets API。
   4. 到「憑證」頁面，點擊「建立憑證」> 「服務帳戶」(Service Account)。
   5. 建立完成後，點進該服務帳戶，進入「金鑰」分頁，點擊「新增金鑰」>「建立新的金鑰」> 選擇 JSON 格式。
   6. 這時會下載一個 .json 檔案，請把它存到你的專案目錄下（例如命名為 credentials.json）。

  步驟 2：把你的 Google Sheet 分享給機器人
   1. 打開剛下載的 credentials.json，裡面有一個 client_email 欄位（長得像 xxxxx@xxxxx.iam.gserviceaccount.com）。
   2. 打開你想要寫入資料的 Google Sheet。
   3. 點擊右上角的「共用」，把剛剛那串 Email 貼上去，權限設定為 「編輯者」。

  步驟 3：安裝 Python 套件
  在終端機執行指令安裝串接所需的套件：
   1 pip install gspread pandas

  步驟 4：將程式碼整合進去
  我可以幫你寫一支新的 Python 腳本（例如 upload_to_gsheet.py），或是直接整合進原本的解析腳本中。它的核心程式碼大概會長這樣：

    1 import gspread
    2 import pandas as pd
    3 
    4 # 1. 讀取授權金鑰
    5 gc = gspread.service_account(filename='credentials.json')
    6 
    7 # 2. 開啟你的 Google Sheet (請替換成你的試算表名稱或網址)
    8 sh = gc.open("我的銀行帳戶總覽")
    9 worksheet = sh.sheet1
   10 
   11 # 3. 讀取我們剛剛做好的 CSV
   12 df = pd.read_csv('accounts.csv')
   13 
   14 # 4. 將資料清空並重新寫入 Google Sheet
   15 worksheet.clear()
   16 worksheet.update([df.columns.values.tolist()] + df.values.tolist())
   17 
   18 print("✅ 成功將 CSV 資料同步至 Google Sheet！")