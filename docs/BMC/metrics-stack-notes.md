# Shell Collector / VictoriaMetrics / Grafana — 這是什麼、為什麼重要

> 一句話：這三個東西組成一條「指標管線」— **採集 → 儲存 → 視覺化**。
> 它把你日常工作裡那些「感覺上變慢了」「好像最近比較常壞」的模糊印象，變成可以查詢、可以畫圖、可以設警報的數字。

---

## 1. 整體架構

```
 你的 script / CI job              時序資料庫               儀表板
┌──────────────────┐          ┌──────────────────┐    ┌─────────────┐
│  Shell Collector │  ──push/ │ VictoriaMetrics  │ ←─ │   Grafana   │
│  (採集)          │   scrape │ (儲存 + 查詢)     │PromQL│ (視覺化/告警)│
└──────────────────┘   ──────→└──────────────────┘    └─────────────┘
        │
        ├─ build duration
        ├─ image size
        ├─ test pass rate
        └─ log error count
```

---

## 2. Shell Collector（採集層）

泛指「用 shell script 去抓數字」的採集器。實務上最常見兩種形態：

### (a) node_exporter textfile collector

你寫一個 script，把結果寫成 **Prometheus exposition 格式**的 `.prom` 檔，放到指定目錄；
node_exporter 每次被抓取時，會順便把該目錄的檔案內容一起吐出來。

```bash
#!/bin/bash
# /usr/local/bin/collect_build_metrics.sh
OUT=/var/lib/node_exporter/textfile_collector/ci_build.prom
TMP=$OUT.$$

{
  echo "# HELP ci_build_duration_seconds Last build wall time"
  echo "# TYPE ci_build_duration_seconds gauge"
  echo "ci_build_duration_seconds{project=\"tablet\",branch=\"main\"} ${BUILD_SEC}"

  echo "# HELP ci_image_size_bytes Output image size"
  echo "# TYPE ci_image_size_bytes gauge"
  echo "ci_image_size_bytes{project=\"tablet\"} $(stat -c%s out/system.img)"
} > "$TMP"

mv "$TMP" "$OUT"   # atomic，避免 exporter 讀到寫到一半的檔案
```

### (b) Telegraf / vmagent 的 `exec` input

定期執行你的 script，直接收 stdout，不用落地成檔案。

```toml
[[inputs.exec]]
  commands = ["/usr/local/bin/collect_build_metrics.sh"]
  interval = "60s"
  data_format = "prometheus"
```

### 重點

> 它讓「**本來沒有 metrics endpoint 的東西**」也能進監控系統。

CI build time、image size、測試 pass rate、log 裡某個 error 出現幾次、
`adb shell` 抓到的裝置狀態 — 全都能變成時序指標。

**成本極低**：你手上已經有的 script，只要多輸出幾行文字就成了資料來源，不用改動 CI 架構。

---

## 3. VictoriaMetrics（儲存層）

時序資料庫（TSDB），與 Prometheus 高度相容。

| 面向 | 說明 |
|---|---|
| 查詢語言 | PromQL（另有超集 MetricsQL） |
| 寫入協議 | Prometheus remote write、Influx、Graphite、OpenTSDB、自行 scrape |
| 優勢 | 壓縮率高、記憶體用量低、單機就能扛很大的量 |
| 部署形態 | 單機版（一個 binary）／ cluster 版（vminsert / vmselect / vmstorage） |
| 常見用法 | 當 Prometheus 的長期儲存後端，或直接整組取代 Prometheus |
| 配套元件 | `vmagent`（採集轉發）、`vmalert`（告警規則）、`vmbackup` |

資料進來之後，就可以問這種問題：

```promql
# 過去 90 天，各 branch 的 build time 中位數趨勢
quantile_over_time(0.5, ci_build_duration_seconds[1d])

# 這週相對上週，image 大了多少
ci_image_size_bytes - ci_image_size_bytes offset 7d

# 測試失敗率
rate(ci_test_failed_total[1h]) / rate(ci_test_total[1h])
```

---

## 4. Grafana（視覺化 / 告警層）

儀表板層。把 VictoriaMetrics 設為 datasource（型別選 Prometheus 即可），然後：

- 用 PromQL 畫趨勢圖、heatmap、stat panel
- 設 alert rule（或用 vmalert 在後端設）
- 開 TV dashboard 掛在團隊牆上
- Annotation 標上 release / 重大 commit，讓「哪次改動造成的」一目了然

---

## 5. 為什麼重要

CI 維護、build triage、log analysis 這類工作的真正痛點，
**通常不是「這次為什麼壞」，而是「沒有歷史基準」。**

有了這條管線之後：

| 情境 | 沒有指標 | 有指標 |
|---|---|---|
| Build 變慢 | 某天突然被抱怨「最近好慢」 | 圖上看得出從哪一週、對應哪個 commit 開始爬升 |
| Flaky test | 「好像偶爾會壞」 | 失敗率是 2% 還是 15%，用數字討論 |
| Log warning 暴增 | 變成 P1 才發現 | Alert 在惡化前就通知 |
| Image size 膨脹 | 互相推諉 | 指著趨勢圖說明是哪個模組、哪一天 |
| 跨團隊溝通 | 靠印象與口頭 | 有共同的事實基礎 |

另外一個常被低估的價值：**這些圖表本身就是改善成果的證據**。
「CI build time 從 45 分鐘降到 22 分鐘」配上一張趨勢圖，
比任何文字描述都有說服力。

---

## 6. 最小可跑的 PoC（約半天）

```bash
# 1. 起 VictoriaMetrics 單機版
docker run -d --name vm -p 8428:8428 \
  -v vmdata:/victoria-metrics-data \
  victoriametrics/victoria-metrics \
  -retentionPeriod=12

# 2. 起 Grafana
docker run -d --name grafana -p 3000:3000 grafana/grafana

# 3. Grafana 加 datasource：
#    Type = Prometheus, URL = http://<host>:8428
```

CI job 結尾直接 push 一筆（不需要 exporter，最快的做法）：

```bash
# 在 build script 最後
cat <<EOF | curl -s --data-binary @- \
  'http://vm-host:8428/api/v1/import/prometheus'
ci_build_duration_seconds{project="tablet",branch="$BRANCH",result="$RESULT"} $DURATION
ci_image_size_bytes{project="tablet",branch="$BRANCH"} $IMG_SIZE
EOF
```

**建議的推進順序**

1. 先只收 **一個** 指標（build duration），跑一週
2. 有了一週資料，畫第一張圖 — 這時候才會真正知道你想看什麼
3. 再逐步加：test pass rate → image size → log error count
4. 最後才設 alert（太早設 alert 只會製造噪音，反而讓人關掉通知）

> 不要一開始就想設計完整的 metric schema。先收，再整理。
> 早期最常見的失敗模式是：花兩週設計 taxonomy，結果一筆資料都沒進去。

---

## 7. 幾個實務注意事項

- **Label cardinality**：不要把 commit hash、build number 當 label，會炸掉 TSDB。
  那些放進 Grafana annotation 或另外存，metric label 只放低基數的維度（project / branch / result）。
- **Atomic write**：textfile collector 一定要 `write to tmp → mv`，否則會讀到半成品。
- **Retention**：CI 指標建議留 12 個月以上，才看得到年度趨勢。VictoriaMetrics 的壓縮讓這件事很便宜。
- **不要用 counter 記錄「最後一次的值」**：build duration 是 gauge，累計次數才是 counter。
