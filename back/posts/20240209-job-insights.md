---
title: 20240209-job-insights
date: 2024-02-09
tags:
  - job
  - linkedin
  - level_fyi
updated: 2024-02-09
up:
  - "[[增加收入]]"
  - "[[工作]]"
---
# system design
## 1. Scope the problem
- 可以知道現在有什麼工作機會、該公司位於總體的薪水級距
- 可以知道最近就業市場中需要的工作技能
- 如何讓自己更搶手、薪水更高？
	- 技能vs薪水級距
## 2. Reasonable Assumptions
- 雇主資料每天會更新一次
- 刪除大於半年以上的 job
- 高價值產業、薪水頻繁更新，其餘不一定

## 3.  Key Component


# 探索資料
- Taiwan 資料：[[20240211-taiwan-job-insights]]


## 全球
找地區
- [(reddit) Do most software engineers eventually make $200K+](https://www.reddit.com/r/cscareerquestions/comments/12zon6k/do_most_software_engineers_eventually_make_200k/)
	- [Occupational Employment and Wages, May 2022 (bls.gov)](https://www.bls.gov/oes/current/oes151252.htm)
- [(reddit) Aren't EU salaries are too low compared to Eastern European?](https://www.reddit.com/r/cscareerquestionsEU/comments/w0kpml/arent_eu_salaries_are_too_low_compared_to_eastern/)
## 全球公司產業排名
![](https://i.imgur.com/zAmZZCd.png)

## 全球公司薪資排名
![](https://i.imgur.com/BoeEMzo.png)
## 全球 yoe <= 2 的公司薪資排行
"Citadel", "Nvidia", "Hudson River Trading", "Facebook", "Google", "Optiver", "Amazon", "Snap", "The D. E. Shaw Group", "Lenovo", "Jane Street", "Adobe", "DoorDash", "Snowflake", "MongoDB", "Pinterest", "ByteDance", "JPMorgan Chase", "Apple", "XPeng Motors", "Goosk", "Twitch", "Scale AI", "Walmart Global Tech", "Palantir", "Maven Securities", "Netflix", "Udemy", "Stripe", "Microsoft", "Uber", "Robinhood", "The Boring Company", "Roblox", "Wintermute", "Oracle", "InnoPeak Technology", "SpaceX", "StubHub", "Mailchimp", "Rokt", "Coinbase", "Qualcomm", "MNTN", "Anduril Industries", "Two Sigma", "Bloomberg", "Broadcom", "Block", "Epic", "TuSimple", "eBay", "Salesforce", "Bridgewater Associates", "Marshall Wace", "Lyft", "Affirm", "LinkedIn", "Ramp", "Australian Government", "Samsung", "Lucid Motors", "ServiceNow", "Flexport", "SAP", "C3.ai", "CoreWeave", "Tesla", "Intel", "Hive", "Indeed", "Zillow", "Nextdoor", "Cresta", "Wish", "Tableau Software", "MetaData", "QuantCo", "Slack", "Confluent", "Peraton", "Generate Biomedicines", "Qualtrics", "McKinsey", "Atlassian", "Millennium", "Johnson & Johnson", "ZipRecruiter", "Arista Networks", "Yahoo", "Nutanix", "Nike", "Asana", "Electronic Arts", "Datadog", "Goldman Sachs", "Twitter", "Cue Health", "Cisco", "Booz Allen Hamilton", "Intuit", "XTX Markets", "Alithya", "American Express", "GoodRx", "Criteo", "DFINITY", "Marqeta", "Accenture", "Gopuff", "Verily", "Workday", "EOG Resources", "Viasat", "Wealthfront", "IBM", "AppFolio", "Path Robotics", "Deloitte", "Walmart", "Interactive Brokers", "Pleasant Pediatrics", "Toast
## 全球 yoe <= 2 的產業薪資排行
"Data", "Full Stack", "AI", "ML / AI", "API Development (Back-End)", "Distributed Systems (Back-End)", "OR", "AR / VR", "Web Development (Front-End)", null, "iOS", "Site Reliability (SRE)", "Networking", "Supply Chain", "Production", "Security", "Mobile (iOS + Android)", "Systems Engineering", "Shop", "Multimedia", "Analytics", "General", "ML", false, "DS", "Testing (SDET)", "DevOps", "sec", "IV", "Android", "Machining Learning", "Salesforce", "AI / ML", "Camera Systems", "Wireless Engineer", "Machine Learning", "AI/ML", "Other", "Risk & Resilience", "Software QA", "Cyber", "Linux Kernel", "Backend", "Data Science", "Hardware", "GPU", "Computer Vision", "Modem", "Modem Software", "Graduate", "Embedded", "Azure", "Wallet Payments Commerce", "Statistics", "Camera", "Blockchain", "Systems", "Marketing", "NLP", "Firmware", "Biotech", "Cloud", "Product", "Cybersecurity", "Compiler", "Data Scientist", "Cellular", "Research", "Finance", "Anon", "1", "Ads", "Tech", "Quant", "Speech", "IT", "Operations", "Mandiant", "Performance", "TSE", "Security Reseearcher", "Risk Management"
## 全球產業薪資排行
"Distributed Systems (Back-End)", "ML / AI", "Full Stack", "iOS", "AR / VR", "Science", "Data", false, "Trading", "Web Development (Front-End)", "Site Reliability (SRE)", "Networking", "Infra", "Android", "Production", "AI / ML", "Security", "Malware", "Data Science", "Mobile (iOS + Android)", "Satellite Software", "API Development (Back-End)", null, "AI Infra", "Org Leader", "Trust and Safety", "Backend", "Cyber Security", "Machine Learning", "Operating Systems", "Backend Infra", "DevOps", "Hardware", "Front End", "Product Analytics", "General", "CoreOS", "Economics", "System", "Testing (SDET)", "Cloud Security", "Developer Experience", "Specialist", "Marketing", "Equity", "Healthcare", "System Software", "Desktop", "Product", "Infrastructure", "Manager Security Engineer", "Embedded Systems", "Applied Scientist", "Security, Architect, Lead, L7, E7", "Analyst", "Linux", "Information Security", "Analytics", "Chipset", "ML", "Game Development", "Artificial Intelligence", "Applied Science", "Firmware", "Robotics", "AR/VR", "Quant Research", "Quantum", "Tag", "Research", "AWS", "Chrome OS", "Other", "Experimentation", "Satellites", "Microcontrollers", "Confidential", "Fuchsia", "Distributed Storage", "Performance", "Fraud", "search ads", "AI", "EDA",
## 全球公司薪資排行
"Uber", "Facebook", "Figma", "Google", "Roblox", "Stripe", "Amazon", "ByteDance", "Snowflake", "LinkedIn", "OpenAI", "Apple", "Millennium", "Coupang", "Brex", "Broadcom", "Snap", "Oracle", "PingCAP", "SAP", "Signzy", "Slack", "Plaid", "Salesforce", "Cruise", "Nuro", "Citadel", "SoFi", "Block", "SpaceX", "Netflix", "Robinhood", "Workday", "Pinterest", "Verily", "Hudson River Trading", "BlackRock", "Microsoft", "Atlassian", "Thumbtack", "DoorDash", "Class Technologies", "ClickUp", "Huawei", "Waymo", "Tesla", "Twilio", "Pinduoduo", "Rebellion Defense", "Nvidia", "Goldman Sachs", "Coinbase", "Walmart Global Tech", "AMD", "Cisco", "Visa", "Jane Street", "Square", "Samsara", "Flexport", "Lyft", "Anduril Industries", "T. Rowe Price", "Lockheed Martin", "Instacart", "Adobe", "Databricks", "Dropbox", "Two Sigma", "Anduril", "Intuit", "eBay", "StubHub", "Tower Research Capital", "CloudKitchens", "GoDaddy", "Grammarly", "Carta", "GitHub", "PayPal", "Akamai", "SandboxAQ", "Reddit", "City Storage Systems", "Albert", "Zynga", "Pure Storage", "American Century Investments", "Epic", "Respawn Entertainment", "Upstart", "Neo Financial", "Qualcomm", "Dune", "Applied Intuition", "GLMX", "Palantir", "C3.ai", "Noom", "Zillow", "Palo Alto Networks", "Spotify", "Cloudera", "Indeed", "Hopper", "Airbnb", "Opendoor", "Cisco Equipment", "Optiver", "Meta Platform", "ServiceNow", "Gopuff", "Firebolt", "MongoDB", "Benchling", "Fireblocks", "Niantic", "UiPath", "The Boring Company", "Discord", "Twitter", "Intel", "ecoATM", "Roku", "Splunk", "Ultra Mobile", "Brava", "Riot Games", "Warner Bros. Discovery", "Alibaba", "Micron Technology", "Epic Sys", "AppFolio", "T-Mobile", "Aamzon", "HoneyBook", "Qualtrics", "SmartNews", "Synopsys", "Affirm", "Schonfeld", "Glean", "Stealth Computer", "Datadog", "Activision", "Disney", "Chronosphere", "Binance",
### 全球 軟體工程師 比台灣好的國家稅後收入
![](https://i.imgur.com/uri6UUL.png)
### 全球 軟體工程師 比台灣好的國家 扣除12月房租
- 假設台灣不需租房
#### 郊區
![](https://i.imgur.com/Y6Fmemn.png)
- 美國（Seattle, Bay Area, NY, , San Diego, Texas, Boulder, LA, New Hampshire, Montana, Utah, Santa Barbara, Wisconsin, Minnesota, Baltimore Area, Ohio, Kansas, Denmark, London, Singapore, Toronto, UK, Canada）、歐洲(Switzerland, Israel,Norway)、大洋洲（Australia）、亞洲（China）
#### 市區
![](https://i.imgur.com/pmGZV7d.png)
- 美國（Bay Area, Seattle ,Montana, Boulder,  LA, New Hampshire, San Diego,  Texas, NY, Utah,  Wisconsin, Santa Barbara, Baltimore Area,  Minnesota, Ohio, Kansas, Denmark, London, Singapore, Toronto, UK, Canada）、歐洲(Switzerland, Israel,Norway,Denmark)、大洋洲（Australia）
### 全球 軟體工程師 薪資比較（中位數排序）
![](https://i.imgur.com/6XSWQug.png)

### 軟體工程師去哪個地區工作？
- 假設在台灣不需租房
#### 郊區
![](https://i.imgur.com/wu00ebJ.png)
- 比台灣高組：
	- 歐洲(Switzerland, Israel, Norway, Demank)、美國（S F Bay Area, Seattle, New Hampshire, Montana, Texas, Boulder, Utah, Wisconsin, LA, Minnesota, San Diego, Baltimore Area, Ohio, Kansas）
- 接近台灣
	- 

#### 市區
![](https://i.imgur.com/FBABous.png)




### 全球 軟體工程師 (淨收入-12月房租)
- 台灣軟體工程師年薪 (p25, p50, p75) = (108, 159, 221)
- 台大資訊工程所畢業 年薪（聽學長說）100-200w
	- [米一粒](https://drive.google.com/file/d/1nwSRuODXhM-l0ham5vdDbNgLAmPZwoWx/view)，年薪 168 資工所在學 140w+
- 假設在台北不用負擔房租
### 租市區
![](https://i.imgur.com/cw0X5HC.png)

### 租郊區
![](https://i.imgur.com/L0kBsgd.png)


### 其他支出
- prompt
- **日常開銷**：包括房租、水電費、伙食費、交通費、通訊費等費用。
- **安家費用**：
    - 租房：租房的費用會因城市、地段、房屋大小等因素而有所不同。一般來說，在美國的大城市，一套一室一廳的公寓的月租金在 1,500 美元以上。
    - 購置家具家電：家具家電的費用會因品牌、型號等因素而有所不同。一般來說，一套基本的家具家電需要花費幾千美元。
    - 生活用品：生活用品的費用會因個人需求而有所不同。一般來說，需要準備一些基本的衣物、洗漱用品、廚房用品等。
## Notes
nltk: 舊方法
有錯誤需要
import nltk
nltk.download()
bert tokenizer

https://github.com/saffsd/langid.py: 辨別語系
https://www.numbeo.com/cost-of-living/compare_cities.jsp: 查看物價、房租
## Ref
- https://github.com/ArshKA/LinkedIn-Job-Scraper

- `helper/create_levels_map.py`
	- input: `*_salary.json`
	- output: `helper/levelsfyi.json`
```json
{
    "all_contryIds": [],
    "all_cityIds": [],
    "all_dmaIds": [],
    "mp_country": {
        "14": [
            "Melbourne, VI, Australia",
        ]
    },
    "mp_city": {},
    "mp_dma": {}
}
```
- `create_keywords_from_levels_data.py`
	- Input: `../out/*_salary.json`
	- Output: `../helper/focusTag_keywords.json`
```json
{
	"raw":[],
	"s":[]
}
```
- `notebooks/worldwide_jobs.ipynb`
	- 全球EDA
- `notebooks/taiwan_jobs.ipynb`
	- 台灣資料EDA
- `notebooks/taiwan_jobs.ipynb`
	- 生活、薪資換算
- `linkedin_get_jobs.py`
	- input: keywords, locations
	- output: `out/{keyword}_{location}_jobs.json`
```json
[
    {
        "trackingUrn": "urn:li:jobPosting:3839104661",
        "repostedJob": false,
        "title": "Forex / Crypto Trader - Work From Home",
        "$recipeTypes": [
            "com.linkedin.deco.recipe.anonymous.Anon1578943416"
        ],
        "posterId": "966281264",
        "$type": "com.linkedin.voyager.dash.jobs.JobPosting",
        "contentSource": "JOBS_PREMIUM_OFFLINE",
        "entityUrn": "urn:li:fsd_jobPosting:3839104661"
    },
]
```
- `linkedin/process.py `
	- input: `../out/*_jobs.json`
	- output: `../out/process_details.json`
```json
{
  
  "3729512725": {
    "description": "...",
    "title": "Quantitative Developer",
    "formattedLocation": "New York, United States",
    "listedAt": 1708703570000,
    "applyUrls": [
      "https://www.linkedin.com/job-apply/3729512725"
    ],
    "salary_paragraphs": [
      "...."
    ],
    "salary_matches": [
      "$24"
    ],
    "workplaceType": [
      "Hybrid"
    ]
  },
```


由於 Linkedin api好像沒有 following 的entry points，因此要自己寫
思路
https://www.linkedin.com/mynetwork/network-manager/people-follow/following/
request
```
https://www.linkedin.com/voyager/api/graphql?variables=(start:50,count:10,origin:CurationHub,query:(flagshipSearchIntent:MYNETWORK_CURATION_HUB,includeFiltersInResponse:true,queryParameters:List((key:resultType,value:List(PEOPLE_FOLLOW)))))&queryId=voyagerSearchDashClusters.a6589bc963659630adee73df22e9384c
```