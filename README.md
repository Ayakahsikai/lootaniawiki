# LOOTANIA Wiki

原始檔放在 `wiki/`，由 GitHub Actions 發佈到網站根目錄：`https://<帳號>.github.io/<repo>/`。

```
.github/workflows/pages.yml   自動部署（push 到 main 就會更新網站）
tools/check_data.py           部署前的資料檢查（本機也可執行：python tools/check_data.py）
wiki/
  index.html                  Wiki 頁面
  data/
    versions.js               資料版本清單（手動維護）
    home.js                   首頁賽季資訊（不分版本）
    v0.10.5/                  一個版本一個資料夾
      skills.js、skills.json  技能資料（技能編輯器存出的兩個檔案）
      runes.js、runes.json    符文資料（符文編輯器存出的兩個檔案）
      skill-icons.png         技能圖示表
      rune-icons.png          符文圖示表
```

## 部署設定
- Settings → Pages → Build and deployment → **Source 選「GitHub Actions」**（不要選建議的 Jekyll / Static HTML 範本）。
- 預設分支如果叫 `master`，把 `pages.yml` 裡的 `branches: [main]` 改成 `master`。

## 日常更新（同一個版本改資料）
- 用技能／符文編輯器開啟 `wiki/data/<版本資料夾>/` 存檔（`.js` 和 `.json` 會一起更新），有改圖示時圖示表也一起覆蓋，push 後自動部署。

## 新增版本
1. 複製最新的版本資料夾，例如 `v0.10.5` → `v0.10.5`，之後在新資料夾裡編輯。
2. 編輯 `wiki/data/versions.js`：在 `versions` **最前面**加一筆，並把 `latest` 改成新版本名稱：
```js
window.LOOTANIA_VERSIONS = {
  "latest": "LOOTANIA Beta v 0.10.5",
  "versions": [
    { "version": "LOOTANIA Beta v 0.10.5", "dir": "v0.10.5", "note": "" },
    { "version": "LOOTANIA Beta v 0.10.5", "dir": "v0.10.5", "note": "" }
  ]
};
```
- `version` 要和天賦模擬的天賦版本名稱**完全相同**，天賦模擬才抓得到對應資料。
- 舊版本資料夾請保留，網頁右上角可以切換查看，舊流派也才對得上舊資料。
- 網頁預設顯示 `latest`；網址加 `?v=v0.10.5` 可以直接開指定版本。

## 部署前自動檢查
`versions.js` 格式、`latest` 是否在清單裡、版本名稱／資料夾是否重複、每個版本資料夾是否存在；
每個版本的 `skills.js`／`runes.js` 格式、編號是否重複、是否有名稱、圖示表是否存在、圖示編號是否超出範圍、`.json` 與 `.js` 是否一致；
`home.js` 的日期時間格式。檢查失敗會停止部署，線上網站維持上一版。檢查通過後會自動產生 `data/versions.json`。

## 天賦模擬讀取資料
```
1. 讀 https://<帳號>.github.io/<repo>/data/versions.json
     → { "latest": "...", "versions": [ { "version": "...", "dir": "..." }, ... ] }
2. 找 version 和天賦版本名稱相同的那一筆；找不到就用 latest 那一筆
3. 讀 data/<dir>/skills.json、data/<dir>/runes.json
```

## 更新首頁賽季資訊
網站上不提供編輯。在電腦上直接雙擊 `wiki/index.html`，首頁資訊欄右上角會出現「編輯」，
填好後按「儲存到 home.js」，選擇 `wiki/data/home.js` 覆蓋，再 push。
