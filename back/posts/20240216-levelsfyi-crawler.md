---
title: 20240216-levelsfyi-crawler
date: 2024-02-17
tags:
  - web_scraping
updated: 2024-02-17
up:
  - "[[工作]]"
---
## Background
- from a [stack overflow question](https://stackoverflow.com/questions/76496884/how-levels-fyi-is-encoding-the-api-response) , level.fyi encrypt its response
- request
```javascript
GET https://api.levels.fyi/v3/salary/search?countryIds[]=197&offset=10&limit=50&sortBy=offer_date&sortOrder=DESC&jobFamilySlug=software-engineer
```
- response
```json
{
    "payload": "EofXi7jF2t63a..."
}
```
## solution
- Go to [levels.fyi](https://www.levels.fyi/)> Inspect>Network>JS tab>commonUtils.js>CryptoJS.AES.decrypt
- I wrote a python script : 

```python
from Crypto.Cipher import AES
from Crypto.Hash import MD5
from base64 import b64encode, b64decode
import zlib
class ResponseUtil:
    def __init__(self):
        self.key = "levelstothemoon!!"
        self.n = 16

    def parse(self, t):
        if "payload" not in t:
            return t
        r = t["payload"]
        a = MD5.new(self.key.encode()).digest()
        a_base64 = b64encode(a)[: self.n]
        cipher = AES.new(a_base64, AES.MODE_ECB)

        decrypted_data = cipher.decrypt(b64decode(r))
        
        decompressed_data = zlib.decompress(decrxypted_data)

        return json.loads(decompressed_data.decode())

# Example usage:
response_util = ResponseUtil()
parsed_data = response_util.parse(ans)
print(parsed_data)

```

```json
{
    "total": 1000,
    "hidden": 2,
    "rows": [
        {
            "uuid": "079fb0cf-d9ff-4b58-bb08-70f3a8447521",
            "title": "Software Engineer",
            "jobFamily": "Software Engineer",
            "level": "E7",
            "focusTag": "General",
            "yearsOfExperience": 5,
            "yearsAtCompany": 2,
            "yearsAtLevel": 2,
            "offerDate": "2024-01-27T02:02:19.682Z",
            "location": "Hsin-chu, TP, Taiwan",
            "workArrangement": "office",
            "compPerspective": "employee",
            "cityId": 17410,
            "dmaId": 10064,
            "countryId": 236,
            "exchangeRate": 31.2881,
            "baseSalary": 42188.5583,
            "baseSalaryCurrency": "TWD",
            "totalCompensation": 67757.3815,
            "avgAnnualStockGrantValue": null,
            "stockGrantCurrency": null,
            "avgAnnualBonusValue": 25568.8232,
            "bonusCurrency": "TWD",
            "salesComp": null,
            "negotiatedAmount": null,
            "gender": null,
            "ethnicity": null,
            "education": null,
            "otherDetails": null,
            "companyInfo": {
                "registered": true,
                "icon": "https://logo.clearbit.com/mediatek.com",
                "name": "MediaTek",
                "slug": "mediatek"
            },
            "vestingSchedule": null,
            "tags": null,
            "stockType": null
        },
        ...
```

- https://hackmd.io/DXNwbKGJRWamrYYFv6LT_Q

## contract
If you have any questions or needs, please contract me at alan.tseng.cs@gmail.com