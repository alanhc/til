---
title: 2021112-upload-large-file
date: 2023-11-12
tags:
  - nextjs
  - file
  - frontend
---
## upload api
```js

import { connectToDb, fileExists } from "@/lib/mongodb";

import { NextResponse } from "next/server";

import { Readable } from "stream";

import formidable, { errors as formidableErrors } from 'formidable';

var fs = require('fs');

var md5 = require('md5');

  

export const config = {

api: {

bodyParser: false,

}

};

type ProcessedFiles = Array<[string, File]>;

export default async function handler(req: any, res: any) {

const { bucket } = await connectToDb();

// get the form data

// const data = await req.formData();

// Access uploaded files directly using req.files

//const files = Array.from(req.files.entries());

  

let status = 200,

resultBody = { status: 'ok', message: 'Files were uploaded successfully' };

  

const form = formidable({ uploadDir: "/tmp" });

let fields;

let files;

try {

form.parse(req, async (err, fields, files) => {

console.log('fields:', fields);

console.log('files:', files);

for (const [key, value] of Object.entries(files)) {

const isFile = typeof value == "object";

if (isFile) {

let file: any = value[0]

let filename = file.originalFilename

let type = file.mimetype

let buffer = fs.readFileSync(file.filepath);

const stream = Readable.from(buffer);

const hash = md5(buffer)

const existing = await fileExists(hash);

if (existing) {

// If file already exists, let's skip it.

// If you want a different behavior such as override, modify this part.

continue;

}

const uploadStream = bucket.openUploadStream(filename, {

// make sure to add content type so that it will be easier to set later.

contentType: type,

metadata: {

hash:hash

}, //add your metadata here if any

});

  

// pipe the readable stream to a writeable stream to save it to the database

await stream.pipe(uploadStream);

res.status(200).json({

hash: hash

})

}

  

}

});

  
  

} catch (err: any) {

// example to check for a very specific error

if (err.code === formidableErrors.maxFieldsExceeded) {

  

}

console.error(err);

res.writeHead(err.httpCode || 400, { 'Content-Type': 'text/plain' });

res.end(String(err));

return;

}

  

return res.json({ success: true });

}
```
## response image
```js
import { MongoClient, ObjectId, GridFSBucket } from 'mongodb';

import clientPromise, { connectToDb } from "@/lib/mongodb";


export default async function handler(req:any, res:any) {

const client = await clientPromise;

const {hash} = req.query;

const db = client.db("fanstick");

const metadata:any = await db

.collection('media.files')

.find({"metadata.hash":hash})

.toArray()

console.log(metadata)

const {bucket}= await connectToDb()

res.writeHead(200, { 'Content-Type': metadata[0].contentType });

bucket.openDownloadStream(metadata[0]._id)

.on('data', (chunk) => {

res.write(chunk);

})

.on('end', () => {

res.end();

})

.on('error', (err) => {

res.status(500).json({ error: err.message });

});

// const file:any = await db

// .collection('media.chunks')

// .find({"files_id":metadata[0]._id})

// .toArray()

// console.log(file[0].data)

// res.setHeader('Content-Type', metadata[0].contentType)

// res.send(file[0].data)

}
```
## Frontend
```js
fetch(`/backend/upload/file`, {

method: "POST",

body: formData

}).then((res) => res.json())

.then(({hash}) => {

const image_url = `${process.env.Deploy_URL}/api/file/${hash}`

setImage(image_url)

form.setFieldValue(field.name,image_url)

})
```
## Ref
- https://github.com/gapon2401/upload-files-nextjs/blob/master/pages/api/upload.ts
- https://reacthustle.com/blog/how-to-upload-retrieve-images-to-mongodb-using-nextjs-13-app-router