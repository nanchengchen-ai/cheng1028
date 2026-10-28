# 手勢相簿

以瀏覽器攝影機辨識手掌左右移動，切換相簿照片。應用程式使用 Streamlit 與 OpenCV，不需下載手勢模型或載入外部辨識 CDN。

## 功能

- 以手掌向左或向右移動切換照片。
- 使用相簿下方按鈕切換上一張、下一張、第一張與最後一張。
- 顯示 `assets/images/` 中的範例照片，也可在頁面上傳圖片。
- 支援 JPG、JPEG、PNG、WEBP 與 BMP。

## 本機執行

需要 Python 3.14。

```powershell
uv sync --locked
uv run streamlit run main.py
```

在瀏覽器開啟 Streamlit 顯示的網址，允許攝影機權限，按「開啟攝影機」。將手掌放在畫面下半部並左右移動即可切換照片。辨識狀態與收到的影格數會顯示在相機區下方。

攝影機影格會傳送到執行 Streamlit 的應用程式伺服器，以 OpenCV 進行手部位置辨識；影格不會寫入磁碟。瀏覽器上傳的照片只保留在目前的 Streamlit 工作階段。透過網路部署時，請使用 HTTPS，並允許瀏覽器使用攝影機。

## 範例相片

四張範例照片已放在 `assets/images/`，會隨專案部署。其他個人照片不會自動加入版本控制。

## Render 部署

專案根目錄的 `render.yaml` 已設定 Python Web Service。將專案推送到 GitHub 後，在 Render 建立 Blueprint 並連接該 repository；Render 會安裝 `requirements.txt` 中的依賴，並以 `$PORT` 啟動 Streamlit。

## 相依套件

`requirements.txt` 是 Render 使用的執行期依賴清單；`pyproject.toml` 與 `uv.lock` 提供本機 uv 環境的依賴與版本鎖定。
