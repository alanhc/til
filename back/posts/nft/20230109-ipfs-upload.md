---
title: '實作ipfs上傳的前端'
date: '2023-01-09'
tag: ['notes', 'ipfs', 'ethereum']
---
1. import package
```js
import { NFTStorage, File, Blob } from 'nft.storage'
const API_KEY = process.env.NFT_STORAGE_API_KEY
const client = new NFTStorage({ token: API_KEY })
```
2. 
```js
function dataURItoBlob(dataURI) {
    // convert base64 to raw binary data held in a string
    // doesn't handle URLEncoded DataURIs - see SO answer #6850276 for code that does this
    var byteString = atob(dataURI.split(',')[1]);
    // separate out the mime component
    var mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0]
    // write the bytes of the string to an ArrayBuffer
    var ab = new ArrayBuffer(byteString.length);
    // create a view into the buffer
    var ia = new Uint8Array(ab);
    // set the bytes of the buffer to the correct values
    for (var i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    // write the ArrayBuffer to a blob, and you're done
    var blob = new Blob([ab], {type: mimeString});
    return blob;  
}
```
3. 
```js
    ...
    const [dataUri, setDataUri] = useState("")
    const [ipfs, setIpfs] = useState("")

    const onChange = (file) => {
        if (!file) {
            setDataUri('');
            return;
        }
        fileToDataUri(file)
            .then(dataUri => {
                setDataUri(dataUri)
            })
    }
    const handle_mint = () => {
        const upload_ipfs  = async() => {
            const img_blob = await dataURItoBlob(dataUri)
            //const img_cid = await client.storeBlob(img_blob)
            const metadata = await client.store({
                name: 'My sweet NFT',
                description: 'Just try to funge it. You can\'t do it.',
                image: img_blob
            })
            console.log(metadata.url)
            setIpfs(metadata.url)
        }
        upload_ipfs()
    }
```
4. 
```js
return (
        <Layout>
           ...
            <img width="100" height="100" src={dataUri} alt="avatar"/>
            <input type="file" onChange={(event) => onChange(event.target.files[0] || null)} ></input>
            <Button onClick={handle_mint}>Create</Button>
            {ipfs}
        </Layout>
    )
```
- https://github.com/alanhc/aka-ticket/blob/main/frontend/pages/event/index.js