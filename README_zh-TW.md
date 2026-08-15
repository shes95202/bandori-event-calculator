# Bandori Event Calculator

[English](README.md) | [繁體中文](README_zh-TW.md)

一款 Windows 桌面版的 **BanG Dream! 少女樂團派對** 活動計算工具，使用 [Bestdori](https://bestdori.com/) 的即時活動資料來追蹤活動進度與排名目標。

程式會取得活動分數線與 Bestdori 預測資料，再根據玩家輸入的目前分數與一場平均分數，計算為了追上指定排名或應有進度還需要多少活動分數、場次、火、星石與遊玩時間。

當目前沒有進行中的活動時，程式會自動顯示最近一個已結束的活動，讓你仍然可以查看最終分數線，並與自己的最終成績比較。

## 功能

- 使用 PySide6 製作的 Windows 桌面 GUI
- 支援 JP（日服）與 TW（台服）
- 自動偵測目前進行中的活動
- 沒有進行中活動時，自動顯示最近一個已結束的活動
- 啟動時自動整理 Bestdori 資料
- 支援手動重新整理 Bestdori
- 快取 JP / TW 資料，可快速切換伺服器
- 顯示目前分數線
- 進行中活動顯示 Bestdori 預測分數線
- 已結束活動顯示最終分數線
- 自動計算活動進度
- 活動結束倒數，每秒更新
- 活動開始與結束時間依照電腦目前所在時區顯示
- 根據目前 Pace 預估最終活動分數
- 排名目標計算
- 區間 / Pace 目標計算
- 顯示目前相對目標「超前」或「落後」多少分與多少場
- 計算還需要多少場
- 計算需要多少火
- 計算需要多少次回火
- 計算需要多少星石
- 預估需要的遊玩時間
- JP 與 TW 分開儲存玩家進度
- 關閉程式後仍會保留玩家設定
- 使用可攜式 `settings.json`，適合搭配 Synology Drive 或其他雲端同步服務

## 支援的排名目標

### JP（日服）

排名目標：

- T500
- T1000
- T2000

Pace 基準：

- T2000
- T500 與 T1000 預測分數線的平均

### TW（台服）

排名目標：

- T100
- T500
- T1000

Pace 基準：

- T100 與 T500 預測分數線的平均
- T100 與 T500 之間的 Q1

## 畫面

![Bandori Event Calculator](docs/screenshot.png)

## 運作方式

程式會從 Bestdori 取得活動資訊，並搭配玩家輸入的兩個數值：

- **目前分數**：目前累積的活動分數（Event Points）
- **一場平均分數**：平均每打一場可獲得的活動分數

對於正在進行中的活動，程式會計算兩種類型的目標。

### 區間 / Pace 目標

區間目標主要回答：

> 以目前活動進度來看，我現在需要打到多少分，才能追上該目標應有的進度？

預期應有分數會使用：

```text
預測最終分數 × 目前活動進度
```

程式接著會顯示：

- 目前分數線
- 預測分數線
- 目前活動進度下應有的分數
- 目前是超前還是落後
- 相差多少活動分數
- 相當於超前 / 落後多少場
- 需要多少火
- 需要多少次回火
- 需要多少星石
- 預估遊玩時間

如果你已經超前目標，程式仍會保留差距並顯示約等於超前多少場，讓你可以直接知道目前有多少緩衝。

### 排名目標

排名目標主要回答：

> 活動結束前，我還需要打多少才能到達預測的最終排名分數線？

這部分會直接以 Bestdori 的預測最終分數作為目標。

### 活動結束倒數

活動進行中時，「活動狀態」區域會顯示即時倒數，例如：

```text
3 天 3 小時 12 分 31 秒
```

倒數每秒更新一次，但不會每秒重新向 Bestdori 抓取資料。

活動結束後會顯示：

```text
已結束
```

### 已結束活動

如果目前選擇的伺服器沒有進行中的活動，程式會自動顯示最近一個已結束的活動，而且維持與進行中活動相同的完整計算介面。

對於已結束活動：

- 活動進度顯示為 `100.0%`
- 活動倒數顯示為 `已結束`
- 使用 Bestdori 最終分數線取代未來的預測分數線
- 可以輸入自己的最終活動分數，直接與該活動的最終排名分數線比較
- 超前 / 落後、等效場數、火、回火次數、星石與預估時間等計算仍然保留

因此即使活動已從進行中活動列表消失，仍然可以回頭查看自己最後的成績與上一個活動排名分數線的差距。

## 本地時區支援

活動開始與結束時間會轉換成**電腦目前設定的本地時區**。

例如 Windows 設定為台灣時區時，程式就會顯示台灣時間。如果出國後 Windows 自動切換成其他地區的時區，程式顯示的活動開始與結束時間也會跟著改變。

活動進度與倒數本身使用絕對時間戳記計算，因此切換時區不會改變活動真正剩餘的時間。

## 玩家設定

玩家輸入的資料會自動儲存到：

```text
settings.json
```

這個檔案會放在 `BandoriEventCalculator.exe` 的旁邊。

例如：

```json
{
    "JP": {
        "current_score": 1243245,
        "average_score": 20235
    },
    "TW": {
        "current_score": 0,
        "average_score": 0
    }
}
```

因為設定檔是可攜式的，所以可以把程式放在 Synology Drive 等同步資料夾中：

```text
Synology Drive/
└── Bandori Event Calculator/
    ├── BandoriEventCalculator.exe
    └── settings.json
```

這樣就能在多台電腦之間同步目前分數與平均分數。

> 不建議同時在多台電腦修改同一份 `settings.json`，否則可能產生同步衝突。

## 下載

預先打包好的 Windows 版本可從 GitHub 的 **Releases** 頁面下載。

下載：

```text
BandoriEventCalculator.exe
```

使用預先打包的 Windows 版本不需要另外安裝 Python。

程式啟動後會自動從 Bestdori 取得最新的 JP 與 TW 活動資訊。

## 開發環境

### 需求

- Python 3.10+
- PySide6
- Playwright
- Chromium
- requests

Clone repository：

```powershell
git clone https://github.com/shes95202/bandori-event-calculator.git
cd bandori-event-calculator
```

建立 virtual environment：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

安裝專案：

```powershell
pip install -e .
```

安裝 Playwright Chromium：

```powershell
playwright install chromium
```

啟動 GUI：

```powershell
bandori-event-calculator-gui
```

或：

```powershell
python run_gui.py
```

## 測試

如有需要，先安裝開發用 dependencies：

```powershell
pip install -e ".[dev]"
```

執行測試：

```powershell
pytest
```

## 打包 Windows 執行檔

安裝 PyInstaller：

```powershell
pip install pyinstaller
```

將 Playwright 使用的 Chromium 一併準備好：

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH="0"
playwright install chromium
```

打包程式：

```powershell
pyinstaller --noconfirm --clean --onefile --windowed `
    --name BandoriEventCalculator `
    --icon assets/icon.ico `
    --add-data "assets/icon.ico:assets" `
    run_gui.py
```

完成後的執行檔會位於：

```text
dist/BandoriEventCalculator.exe
```

發布新版本之前，建議直接執行 `dist/` 內打包完成的 EXE，確認 Bestdori 資料讀取、JP / TW 切換、各項計算、活動倒數與應用程式 icon 都能正常運作。

## 應用程式資料

程式會依照資料用途儲存在不同位置。

### 玩家進度

儲存在執行檔旁：

```text
settings.json
```

這個檔案可以在不同電腦之間同步。

### Playwright 瀏覽器設定檔

Bestdori 使用的 Chromium profile 會儲存在每台 Windows 電腦的本機：

```text
%LOCALAPPDATA%\BandoriEventCalculator\playwright-profile
```

這個瀏覽器 profile 不會放在執行檔旁，也不需要進行同步。

## 已知限制

- 尚未實作 Challenge Live 專用計算邏輯。
- Bestdori 預測資料的取得方式依賴目前 Bestdori Event Tracker 的網站結構，若網站結構改動可能需要更新程式。
- 目前預先打包的版本以 Windows 為主。
- 取得 Bestdori 資料時需要網路連線。

## 資料來源

活動資訊、排名分數線與預測資料來自：

**Bestdori**

本專案為獨立開發工具，與 Bestdori、Bushiroad、Craft Egg 或 BanG Dream! 官方均無關。

## 版本

目前版本：

```text
v0.3.0
```
