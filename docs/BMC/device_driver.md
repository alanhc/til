
## pmbus

```
user space（例如：sensors） 
   ↓
PMBus core
   ↓
mpc42013_read_word_data(client, page, reg)
   ↓
底層實際透過 I2C 傳送 command code（reg） → 取得 word 資料
```