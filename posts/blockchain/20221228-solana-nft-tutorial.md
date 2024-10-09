---
title: '在solana上mint NFT'
date: '2022-12-28'
tag: ['notes', 'solana']
---
1. 下載 solana cli: `sh -c "$(curl -sSfL https://release.solana.com/v1.14.11/install)"`
2. 新增帳號 `solana-keygen new --outfile ~/.config/solana/devnet.json`
3. 設定 devnet `solana config set --url <https://metaplex.devnet.rpcpool.com/>`
4. 檢查設定 `solana config get`

    ```
    Config File: ~/.config/solana/cli/config.yml
    RPC URL: https://metaplex.devnet.rpcpool.com/
    WebSocket URL: wss://metaplex.devnet.rpcpool.com/ (computed)
    Keypair Path: ~/.config/solana/devnet.json
    Commitment: confirmed
    ```

5. 拿測試token: `solana airdrop 2`
6. sugar launch
- https://nft.storage/manage/
- https://github.com/metaplex-foundation/sugar
- https://docs.metaplex.com/deprecated/candy-machine-js-cli/getting-started#solana-wallet
![](https://i.imgur.com/5Z75hh4.png)
