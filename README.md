# buyTokenOnDex - Buy token quickly

Buying and selling tokens on EVM (Ethereum Virtual Machine) compatible blockchain can be slow for end users. Connecting to metamask, to the DEX, going to swap page, selecting contract you want to buy, setting slippage etc. All theses tasks takes time and you can waste easily 30-60 seconds setting all your swap parameters, which is an eternity during a token launch. 

## What is this tool ? 

This tool allows users to set parameters before sending a BUY transaction to a DEX. 

## How does it work ? 
1) Select the DEX you want to connect to - it will connect directly to the blockchain you want to interact with
2) Select the multiplier of gas price you want to set (1 if it is a normal transaction, 2 multiply gas price by 2 etc. 
3) Select the number of native tokens you want to swap (e.g amount of BNB you want to swap if you decided to connect to pancakeswap)
4) Select the slippage you want to set (allows user to set a slippage between 0.1 and 99.9) 
5) Paste the address of the token you want to buy
6) Enjoy buying token fast

## How to set up your python environment ? 

1) Download the repository
2) Install requirements : pip install -r requirements.txt
3) Change the variables "private" and "sender_address" in the file config.py with the wallet you want to use (you can use a different wallet if you feel like it )

