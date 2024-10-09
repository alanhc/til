---
title: 20240212-linkedin-private-api
date: 2024-02-12
tags:
  - linkedin
  - web_scraping
updated: 2024-02-12
up:
  - "[[工作]]"
---
思路：先用playwright 取得cookies，觀察network直接打API

先取得 geoid (地點id)
```python
q_keywords = "software engineer"
q_location = "taiwan"
r = requests.get(f"https://www.linkedin.com/jobs/search?keywords={q_keywords}&location={q_location}&trk=public_jobs_jobs-search-bar_search-submit")
soup = BeautifulSoup(r.text, "html.parser")
geo_id_inputs = soup.select("input[name='geoId']")
geoid = geo_id_inputs[0].get("value")
```

```python
start_n = 0
job_search_link = f"https://www.linkedin.com/voyager/api/voyagerJobsDashJobCards?decorationId=com.linkedin.voyager.dash.deco.jobs.search.JobSearchCardsCollection-192&count=25&q=jobSearch&query=(origin:JOB_SEARCH_PAGE_SEARCH_BUTTON,keywords:software%20engineer,locationUnion:(geoId:{geoid}),spellCorrectionEnabled:true)&start={start_n}"
headers = [{
'Authority': 'www.linkedin.com',
'Method': 'GET',
'Scheme': 'https',
'Accept': 'application/vnd.linkedin.normalized+json+2.1',
'Accept-Encoding': 'gzip, deflate, br',
'Accept-Language': 'en-US,en;q=0.9',
'Cookie': "; ".join([f"{key}={value}" for key, value in session.cookies.items()]),
'Csrf-Token': session.cookies.get('JSESSIONID').strip('"'),
'User-Agent': 'OOOO',
'X-Li-Track': 'OOOO'
} for session in [s]]

r = s.get(job_search_link,headers=headers[0])
```
後記：結果發現github有人做了 [linkedin api](https://github.com/tomquirk/linkedin-api)QQ，當作練習吧
	- https://github.com/tomquirk/linkedin-api
	- 
- 這裡有說明如何運作 https://github.com/tomquirk/linkedin-api?tab=readme-ov-file#how-it-works
```python
from linkedin_api import Linkedin

api = Linkedin('acc', 'pass')

profile = api.get_profile('alanhc316')

contact_info = api.get_profile_contact_info('username')

connections = api.get_profile_connections('username')
```
- [官方API](https://github.com/linkedin-developers/linkedin-api-python-client)
## Ref
