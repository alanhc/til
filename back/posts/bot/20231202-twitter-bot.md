---
title: 20231202-twitter-bot
date: 2023-12-02
tags:
  - bot
  - twitter
  - api
---
## 1. 使用 twitter API
1. 先去 [dashboard]( https://developer.twitter.com/en/portal/dashboard )建立App，並在User authentication settings > 設定
![](https://i.imgur.com/zzfs8d9.png)
2. 複製 Keys and tokens 
![](https://i.imgur.com/ifnkpvQ.png)


## 建立tweet
```python
import tweepy

bearer_token = ""


consumer_key = ""

consumer_secret = ""

  
access_token = ""

access_token_secret = ""


client = tweepy.Client(

consumer_key=consumer_key, consumer_secret=consumer_secret,

access_token=access_token, access_token_secret=access_token_secret

)

response = client.create_tweet(

text="This Tweet was Tweeted using Tweepy and Twitter API v2!"

)
print(f"https://twitter.com/user/status/{response.data['id']}")
# return
# Response(data={'edit_history_tweet_ids': ['1730651881314414696'], 'id': '1730651881314414696', 'text': 'This Tweet was Tweeted using Tweepy and Twitter API v2!1'}, includes={}, errors=[], meta={})
  
# get me
response = client.get_me()

response
```
免費版只有幾個 API
https://developer.twitter.com/en/docs/twitter-api/getting-started/about-twitter-api
## 2. 使用 seleium
```python
  

from selenium import webdriver
from selenium.webdriver.common.by import By
driver = webdriver.Chrome()
driver.get('https://twitter.com/i/flow/login')

username = driver.find_element(By.TAG_NAME, 'input')
username.send_keys("")

all_btn = driver.find_elements(By.XPATH, "//div[@role='button']")
all_btn[-2].click()

password = driver.find_element(By.XPATH, '//input[@type="password"]')

password.send_keys("")

all_btn = driver.find_elements(By.XPATH, "//div[@role='button']")
all_btn[-1].click()

keyword = "cat"
driver.get(f"https://twitter.com/search?q={keyword}&src=typed_query")

retweet = driver.find_elements(By.XPATH, "//div[@data-testid='retweet']")
retweet[0].click()

quote_tweet = driver.find_elements(By.XPATH, "//a[@role='menuitem']")

quote_tweet[0].click()
  

quote = driver.find_element(By.XPATH, "//div[contains(@class, 'public-DraftStyleDefault-block')]")

quote.send_keys("OMG!")

tweet = driver.find_element(By.XPATH, "//div[@data-testid='tweetButton']")

tweet.click()

driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")

```
## Ref
https://developer.twitter.com/en/portal/dashboard
https://github.com/tweepy/tweepy/blob/master/examples/API_v2/create_tweet.py