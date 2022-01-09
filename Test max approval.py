from web3 import Web3
import config
import time
from buyTokenOnDex import waitForTxResponse, getGasPrice

erc20_abi = '[ { "constant": true, "inputs": [], "name": "name", "outputs": [ { "name": "", "type": "string" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "symbol", "outputs": [ { "name": "", "type": "string" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "decimals", "outputs": [ { "name": "", "type": "uint8" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": false, "inputs": [ { "name": "spender", "type": "address" }, { "name": "value", "type": "uint256" } ], "name": "approve", "outputs": [ { "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": true, "inputs": [], "name": "totalSupply", "outputs": [ { "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": false, "inputs": [ { "name": "from", "type": "address" }, { "name": "to", "type": "address" }, { "name": "value", "type": "uint256" } ], "name": "transferFrom", "outputs": [ { "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": false, "inputs": [ { "name": "spender", "type": "address" }, { "name": "addedValue", "type": "uint256" } ], "name": "increaseAllowance", "outputs": [ { "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": true, "inputs": [ { "name": "owner", "type": "address" } ], "name": "balanceOf", "outputs": [ { "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": false, "inputs": [ { "name": "spender", "type": "address" }, { "name": "subtractedValue", "type": "uint256" } ], "name": "decreaseAllowance", "outputs": [ { "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": false, "inputs": [ { "name": "to", "type": "address" }, { "name": "value", "type": "uint256" } ], "name": "transfer", "outputs": [ { "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": true, "inputs": [ { "name": "owner", "type": "address" }, { "name": "spender", "type": "address" } ], "name": "allowance", "outputs": [ { "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "anonymous": false, "inputs": [ { "indexed": true, "name": "from", "type": "address" }, { "indexed": true, "name": "to", "type": "address" }, { "indexed": false, "name": "value", "type": "uint256" } ], "name": "Transfer", "type": "event" }, { "anonymous": false, "inputs": [ { "indexed": true, "name": "owner", "type": "address" }, { "indexed": true, "name": "spender", "type": "address" }, { "indexed": false, "name": "value", "type": "uint256" } ], "name": "Approval", "type": "event" } ]'
web3 = Web3(Web3.HTTPProvider("https://rpc.ftm.tools"))
token_to_spend = web3.toChecksumAddress("0x841fad6eae12c286d1fd18d1d525dffa75c7effe")
contract_token_to_spend = web3.eth.contract(address=token_to_spend, abi =erc20_abi)

token_to_spend_symbol = contract_token_to_spend.functions.symbol().call()
router_address = web3.toChecksumAddress("0xF491e7B69E4244ad4002BC14e878a34207E38c29")
gas_price_wei = web3.eth._gas_price()
gas_price_gwei = web3.fromWei(gas_price_wei, "gwei")
gas_price_final_gwei = float(gas_price_gwei) * float(1)

nonce = web3.eth.get_transaction_count(config.sender_address)

max_approval_hex = f"0x{64 * 'f'}"
max_approval_int = int(max_approval_hex, 16)
max_approval_check_hex = f"0x{15 * '0'}{49 * 'f'}"
max_approval_check_int = int(max_approval_check_hex, 16)


# check allowance of the token to spend
print("Checking " + token_to_spend_symbol + " allowance on router")
token_to_spend_allowance = contract_token_to_spend.functions.allowance(config.sender_address, router_address).call()
token_to_spend_balance = contract_token_to_spend.functions.balanceOf(config.sender_address).call()






