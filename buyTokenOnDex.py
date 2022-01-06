import pandas as pd
from web3 import Web3
import config
import time
import datetime

"""
Utility functions 
"""


def waitForTxResponse(tx):
    signed_txn = web3.eth.account.sign_transaction(tx, private_key=config.private)
    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    tx_link = dex_chosen["Explorer"].values[0] + "tx/" + web3.toHex(tx_token)
    print("Transaction link : ", tx_link)
    beginning_tx = time.time()
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_token)
    ending_tx = time.time()
    time_tx = ending_tx - beginning_tx
    print("Time to execute the transaction : ", time_tx, "seconds.")

    if tx_receipt.status == 1:
        tx_status = "sent"
    else:
        tx_status = "not sent"

    print("Status of the transaction : ", tx_status)


def getAmountOut(dex, amount_token_spend,decimals, token_to_spend, token_to_buy):

    if decimals == 18:
        amount_token_spend_wei = web3.toWei(amount_token_spend, "ether")
    elif decimals == 9:
        amount_token_spend_wei = web3.toWei(amount_token_spend, "gwei")
    elif decimals == 6:
        amount_token_spend_wei = web3.toWei(amount_token_spend, "mwei")

    if dex == "solarbeam":
        amount_out = contract_router.functions.getAmountsOut(
        amount_token_spend_wei,
        [token_to_spend, token_to_buy],  # [SELL, BUY]
        0
        ).call()

    else:
        amount_out = contract_router.functions.getAmountsOut(
            amount_token_spend_wei,
            [token_to_spend, token_to_buy] # [SELL, BUY]
        ).call()

    return amount_out

def returnEtherValue(input_value , decimals):
    if decimals == 18:
        amount_token_out_ether = web3.fromWei(input_value, "ether")
    elif decimals == 9:
        amount_token_out_ether = web3.fromWei(input_value, "gwei")
    elif decimals == 6:
        amount_token_out_ether = web3.fromWei(input_value, "mwei")
    return amount_token_out_ether

def getGasPrice(multiplier):
    global gas_price_final_gwei
    global gas_price_wei
    global gas_price_gwei

    gas_price_wei = web3.eth._gas_price()
    gas_price_gwei = web3.fromWei(gas_price_wei, "gwei")
    gas_price_final_gwei = float(gas_price_gwei) * float(multiplier)
    print("Timestamp : ", datetime.datetime.now(), " - Gas price of your transactions will be ", gas_price_final_gwei, "gwei.")

def getNativeTokenPrice():
    global native_token_price
    global native_token_price_readable
    native_token_price = getAmountOut(dex=dex_chosen["Dex"].values[0], amount_token_spend=1,
                                      decimals=native_token_decimals,
                                      token_to_spend=native_token_address, token_to_buy=stable_coin_token_address)

    native_token_price_readable = float(native_token_price[1]) / (10 ** float(stable_coin_decimals))
    print("Timestamp : ", datetime.datetime.now(),"- the price for 1", native_token_symbol, "is",
          native_token_price_readable, stable_coin_symbol)

def chooseToken(method):
    token_chosen = input("Enter the address of the token you want to " + method + " : ")
    if Web3.isAddress(token_chosen):
        token_chosen_address = Web3.toChecksumAddress(token_chosen)
    else:
        print("The token address that you typed is not a token address. Retry.")
        print("")
        chooseToken()
    return token_chosen_address

"""
End utility functions 
"""

"""
Execution functions
"""

#1) choose the dex and initiate parameters
def choice_dex():
    df = pd.read_excel("dex_parameters.xlsx")
    liste_dex = df["Dex"].values

    print("Choose a dex in the following list :", liste_dex)
    choiceDex = input("Type your choice here : ")

    validation = None
    for j in range(0, len(liste_dex)):
        if choiceDex.lower() == liste_dex[j].lower():
            validation = True
            break
        else:
            validation = False
    if validation == True:
        global contract_router
        global contract_factory

        global web3
        global native_token_address
        global native_token_name
        global native_token_symbol
        global native_token_balance_readable
        global native_token_balance
        global native_token_decimals

        global stable_coin_token_address
        global stable_coin_name
        global stable_coin_symbol
        global stable_coin_decimals
        global dex_chosen


        dex_chosen = df.loc[df['Dex'] == choiceDex]

        web3 = Web3(Web3.HTTPProvider(dex_chosen["Rpc"].values[0]))

        stable_coin_token_address = web3.toChecksumAddress(dex_chosen["StablecoinTokenAddress"].values[0])
        stable_coin_name = dex_chosen["StablecoinName"].values[0]
        stable_coin_symbol = dex_chosen["StablecoinSymbol"].values[0]
        stable_coin_decimals = dex_chosen["StablecoinDecimals"].values[0]

        native_token_address = web3.toChecksumAddress(dex_chosen["NativeTokenAddress"].values[0])
        contract = web3.eth.contract(native_token_address, abi=dex_chosen["NativeTokenAbi"].values[0])
        native_token_name = contract.functions.name().call()
        native_token_symbol = contract.functions.symbol().call()
        native_token_decimals = contract.functions.decimals().call()

        native_token_balance = web3.eth.get_balance(config.sender_address)
        native_token_balance_readable = web3.fromWei(native_token_balance, 'ether')

        print("Verifying connection ", dex_chosen["Blockchain"].values[0], " : ", web3.isConnected())
        print("Native token of the blockchain is ", native_token_name, "(", native_token_symbol,
              "), address is : ", native_token_address)

        contract_router = web3.eth.contract(
            address=web3.toChecksumAddress(dex_chosen["RouterAddress"].values[0]),
            abi=dex_chosen["RouterAddressAbi"].values[0])

        contract_factory = web3.eth.contract(
            address=web3.toChecksumAddress(dex_chosen["FactoryAddress"].values[0]),
            abi=dex_chosen["FactoryAddressAbi"].values[0])

        getNativeTokenPrice()

        print("You have chosen DEX : ", dex_chosen["Dex"].values[0])

    else:
        print("Incorrect value. Please select a DEX in the following list ", liste_dex )
        print("")
        choice_dex()

#2) Set gas price multiplier
def gasPriceChoice():
    global gas_price_multiplier
    print("Current gas price is :",  web3.fromWei(web3.eth._gas_price(),"gwei") ,"gwei on the blockchain",
        dex_chosen["Blockchain"].values[0])

    gas_price_multiplier = input(("Please select a multiplier on the current gas price : "))
    getGasPrice(gas_price_multiplier)

#3) Set slippage parameters (up to 99%)
def setSlippage():
    slippage = float(input("Select the slippage (between 0.1 and 99.9): "))
    if 0.1 <= slippage <= 99.9:
        global slippage_percent
        slippage_percent = slippage / 100
    else:
        print("Slippage must be set between 0.1 and 99.9. Retry.")
        print("")
        setSlippage()

#4) Set choice swap method
def choice_swap_method():
    global swap_method_chosen
    print("Choose your swap method : ")
    print(" - Type 1 if you want to swap exact number of " + native_token_symbol + " for token")
    print(" - Type 2 if you want to swap exact number of token A for token B ")
    #print(" - Type 3 if you want to swap " + symbolNativeContract + " for exact number of token")
    #print(" - Type 4 if you want to swap token A for exact number of token B ")

    swap_method_chosen = input("Type your choice here : ")

    if (swap_method_chosen == "1" or swap_method_chosen == "2"):
        print("You have chosen method " + swap_method_chosen)
    else:
        print("You have to choose between the options proposed. Retry.")
        choice_swap_method()


#5) Set token to spend parameters depending on swap method chosen

def setTokenToSpendParameters():
    global amountTokenToSpend
    global token_to_spend_balance
    global token_to_spend_decimals
    global token_to_spend_symbol
    global token_to_spend_balance_readable
    global token_to_spend_address

    if swap_method_chosen == "1": # Here token to spend parameters are just native token parameters

        token_to_spend_address = native_token_address
        token_to_spend_balance = native_token_balance
        token_to_spend_decimals = native_token_decimals
        token_to_spend_symbol = native_token_symbol
        token_to_spend_balance_readable = native_token_balance_readable

    elif swap_method_chosen == "2": # Here token to spend parameters have to be requested

        token_to_spend_address = chooseToken(method="spend")
        token_to_spend_abi = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"value","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
        contract_token_to_spend = web3.eth.contract(token_to_spend_address, abi=token_to_spend_abi)
        token_to_spend_balance = contract_token_to_spend.functions.balanceOf(config.sender_address).call()
        token_to_spend_decimals = contract_token_to_spend.functions.decimals().call()
        token_to_spend_symbol = contract_token_to_spend.functions.symbol().call()
        token_to_spend_balance_readable = float(token_to_spend_balance) / (10 ** float(token_to_spend_decimals))

        #check allowance of the token to spend
        print("Checking " + token_to_spend_symbol + " allowance")
        token_to_spend_allowance = contract_token_to_spend.functions.allowance(config.sender_address,
                                               web3.toChecksumAddress(dex_chosen["RouterAddress"].values[0])).call()

        if token_to_spend_allowance == 0:
            # approve if no allowance
            print("Now approving " + token_to_spend_symbol)
            tx = contract_token_to_spend.functions.approve(config.sender_address, native_token_balance).buildTransaction({
                'from': config.sender_address,
                'gasPrice': web3.toWei(gas_price_final_gwei, 'gwei'),
                'nonce': web3.eth.get_transaction_count(config.sender_address)
                })
            waitForTxResponse(tx)
        else:
            print(token_to_spend_symbol + " already approved : ")

# 6) choose token to spend amount
def choice_amount_to_spend():
    global amount_token_to_spend
    print("You have ", "{:.5f}".format(token_to_spend_balance_readable) , " ", token_to_spend_symbol, " in your wallet")
    print("How many", token_to_spend_symbol, "do you want to spend ?")
    amount_token_to_spend = input("Select the amount here : ")
    """
    if float(amount_token_to_spend) >= float(token_to_spend_balance_readable):
        print("The value selected must be inferior to : ", token_to_spend_balance_readable)
        print("")
        choice_amount_to_spend()
    """

# 7) set parameters for token to buy
def setTokenToBuyParameters():
    global token_to_buy_address
    global token_to_buy_balance
    global token_to_buy_decimals
    global token_to_buy_symbol
    global token_to_buy_balance_readable

    print("/!\ the transaction will be sent directly after this step /!\ ")
    token_to_buy_address = chooseToken(method="buy")
    token_to_buy_abi = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"value","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
    contract_token_to_buy = web3.eth.contract(token_to_buy_address, abi=token_to_buy_abi)
    token_to_buy_balance = contract_token_to_buy.functions.balanceOf(config.sender_address).call()
    token_to_buy_decimals = contract_token_to_buy.functions.decimals().call()
    token_to_buy_symbol = contract_token_to_buy.functions.symbol().call()
    token_to_buy_balance_readable = float(token_to_buy_balance) / (10 ** float(token_to_buy_decimals))

# 8) Set buy amount
def setBuyAmount():
    global minimum_token_received

    getNativeTokenPrice()

    if token_to_spend_address != native_token_address:
        #Amount of token that we want to spend in native blockchain token
        buy_amount_native_token = getAmountOut(dex=dex_chosen["Dex"].values[0], amount_token_spend=amount_token_to_spend,
                                               decimals=token_to_spend_decimals,
                                             token_to_spend=token_to_spend_address, token_to_buy=native_token_address)
        # Amount in native blockchain token converted to token we want to spend
        buy_amount = getAmountOut(dex=dex_chosen["Dex"].values[0],
                                  amount_token_spend=web3.fromWei(buy_amount_native_token[1], "ether"),
                                  decimals=native_token_decimals,
                                  token_to_spend=native_token_address, token_to_buy=token_to_buy_address)

        buy_amount_native_token_ether = returnEtherValue(buy_amount_native_token[1], native_token_decimals)
        buy_amount_ether = returnEtherValue(buy_amount[1], token_to_buy_decimals)
        exchange_rate_spend_token = (float(buy_amount_native_token_ether) * float(native_token_price_readable) ) / float(amount_token_to_spend)
        exchange_rate_buy_token = (float(buy_amount_native_token_ether) * float(native_token_price_readable)) / float(buy_amount_ether)
        #entry_price = exchange_rate_buy_token :)
        print("Exchange rate for 1", token_to_spend_symbol ,":", "{:.5f}".format(exchange_rate_spend_token) + " dollars")
        print("Exchange rate for 1", token_to_buy_symbol,":", "{:.5f}".format(exchange_rate_buy_token) + " dollars")
    else:
        buy_amount = getAmountOut(dex=dex_chosen["Dex"].values[0],
                                  amount_token_spend=amount_token_to_spend,
                                  decimals=native_token_decimals,
                                  token_to_spend=native_token_address, token_to_buy=token_to_buy_address)
        buy_amount_ether = returnEtherValue(buy_amount[1], token_to_buy_decimals)
        exchange_rate_buy_token = (float(native_token_price_readable) * float(amount_token_to_spend)) / float(buy_amount_ether)
        print("Exchange rate for 1", token_to_buy_symbol,":", "{:.5f}".format(exchange_rate_buy_token) + " dollars")

    buy_amount_readable = float(buy_amount[1]) / (10 ** float(token_to_buy_decimals))
    minimum_token_received = buy_amount_readable * (1 - slippage_percent)
    buy_amount_fiat = float(buy_amount_readable) * float(exchange_rate_buy_token)

    print("You will receive ", "{:.5f}".format(buy_amount_readable), token_to_buy_symbol, "(",
          "{:.5f}".format(minimum_token_received), " at the minimum) for", amount_token_to_spend,
          token_to_spend_symbol, "spent (≃", "{:.5f}".format(buy_amount_fiat), "dollars.)")

    pair = contract_factory.functions.getPair(token_to_buy_address, token_to_spend_address).call()
    link = "https://dexscreener.com/" + dex_chosen["Blockchain"].values[0] + "/" + pair
    print("Chart link : ", link)

def sendTx():
    global nonce
    nonce = web3.eth.get_transaction_count(config.sender_address)
    getGasPrice(gas_price_multiplier)

    if swap_method_chosen == "1":
        if dex_chosen["Dex"].values[0] == "traderjoe":
            tx = contract_router.functions.swapExactAVAXForTokens(
                web3.toWei(minimum_token_received, 'ether'),
                # set to 0 or specify the minimum amount of tokens you want to receive -- consider decimals
                [token_to_spend_address, token_to_buy_address],
                config.sender_address,
                (int(time.time()) + 10000)
            ).buildTransaction({
                'from': config.sender_address,
                'value': web3.toWei(amount_token_to_spend, 'ether'),
                # This is the token BNB amount you want to swap from
                #'gas': 1000000,
                'gasPrice': web3.toWei(gas_price_final_gwei, 'gwei'),
                'nonce': nonce
            })

        else:
            tx = contract_router.functions.swapExactETHForTokens(
                web3.toWei(minimum_token_received, 'ether'),
                # set to 0 or specify the minimum amount of tokens you want to receive -- consider decimals
                [token_to_spend_address, token_to_buy_address],
                config.sender_address,
                (int(time.time()) + 10000)
            ).buildTransaction({
                'from': config.sender_address,
                'value': web3.toWei(amount_token_to_spend, 'ether'),
                # This is the token BNB amount you want to swap from
                #'gas': 1000000,
                'gasPrice': web3.toWei(gas_price_final_gwei, 'gwei'),
                'nonce': nonce
            })
    elif swap_method_chosen == "2":
        tx = contract_router.functions.swapExactTokensForTokens(
            web3.toWei(amount_token_to_spend, 'ether'),
            0,
            #web3.toWei(minimum_token_received, 'ether'),
            [token_to_spend_address, token_to_buy_address],
            config.sender_address,
            (int(time.time()) + 10000)
        ).buildTransaction({
        'from': config.sender_address,
        'gas': 1000000,
        'gasPrice': web3.toWei(gas_price_final_gwei, 'gwei'),
        'nonce': nonce
        })

    waitForTxResponse(tx)

    again = input("Send same transaction ? type 'ok' if you want : ")

    if again.lower() == "ok":
        sendTx()
    else:
        print("")
        print("End of the script, send donations if you feel like it : 0xf444955E4dC892198E8a733ffCf08aaA13Bea096 :) ")
        exit()

def main():
    choice_dex()
    gasPriceChoice()
    setSlippage()
    choice_swap_method()
    setTokenToSpendParameters()
    choice_amount_to_spend()
    setTokenToBuyParameters()
    setBuyAmount()
    #sendTx()
main()

