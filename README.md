# LOOTANIA Wiki

原始檔放在 `wiki/`，由 GitHub Actions 發佈到網站根目錄：`https://<帳號>.github.io/<repo>/`。

```
.github/workflows/pages.yml   自動部署（push 到 main 就會更新網站）
wiki/
  index.html                  Wiki 頁面（首頁賽季資訊、技能 ▾ 主動技能／被動技能／符文）
  data/
    skills.js                 技能資料（技能編輯器存出的 skills.js）
    runes.js                  符文資料（符文編輯器存出的 runes.js）
    home.js                   首頁賽季資訊
    skill-icons.png           技能圖示表
    rune-icons.png            符文圖示表
```

## 部署設定
- Settings → Pages → Build and deployment → **Source 選「GitHub Actions」**（不要選建議的 Jekyll / Static HTML 範本）。
- 預設分支如果叫 `master`，把 `pages.yml` 裡的 `branches: [main]` 改成 `master`。

## 日常更新
- 只換 `wiki/` 裡的檔案，push 後自動部署；也可以在 Actions 分頁手動按「Run workflow」重新部署。
- 技能、符文：用編輯器存檔後，把 `skills.js`／`runes.js` 和圖示表覆蓋到 `wiki/data/`。

部署前會自動檢查：`index.html` 是否存在；`skills.js`、`runes.js` 格式是否正確、編號是否重複、每筆是否有名稱、圖示表是否存在、圖示編號是否超出範圍；`home.js` 的日期格式。檢查失敗會停止部署，線上網站維持上一版。

## 更新首頁賽季資訊
網站上不提供編輯。在電腦上直接雙擊 `wiki/index.html`，首頁資訊欄右上角會出現「編輯」，
填好後按「儲存到 home.js」，選擇 `wiki/data/home.js` 覆蓋，再 push。
