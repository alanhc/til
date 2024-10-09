---
title: "在mongodb裡面將兩個group merge成一個結果"
date: "2023-08-31"
tags: ["mongodb", "python"]
---
## 結果
```json
{
  "results": [
    {
      "path": "/mcu/course/2D動畫實務",
      "id": "2D動畫實務"
    },
    ...
	{
      "path": "/mcu/professor/楊健貴",
      "id": "楊健貴"
    },
    ...
}
```
原本資料
![](https://i.imgur.com/pG8t7xo.png)
## 使用facet+project
```js
Col_course.aggregate([
  {
    $facet: {
      teacher_subject: [
        { $group: { _id: { teacher: "$teacher", subject: "$subject" } } },
        {
          $project: {
            _id: 0,
            path: {
              $concat: ["/mcu/ratings/", "$_id.teacher", "/", "$_id.subject"],
            },
            id: {
              $concat: ["$_id.teacher", " ", "$_id.subject"],
            },
          },
        },
      ],
      teacher: [
        { $group: { _id: { teacher: "$teacher" } } },
        {
          $project: {
            _id: 0,
            path: {
              $concat: ["/mcu/professor/", "$_id.teacher"],
            },
            id: {
              $concat: ["$_id.teacher"],
            },
          },
        },
      ],
      subject: [
        { $group: { _id: { subject: "$subject" } } },
        {
          $project: {
            _id: 0,
            path: {
              $concat: ["/mcu/course/", "$_id.subject"],
            },
            id: {
              $concat: "$_id.subject",
            },
          },
        },
      ],
    },
  },
  {
    $project: {
      results: { $setUnion: ["$teacher_subject", "$teacher", "$subject"] },
    },
  },
  { $unwind: "$results" },
  { $replaceRoot: { newRoot: "$results" } },
]);

```



## Ref
- 
