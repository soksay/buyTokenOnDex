import pandas as pd
from web3 import Web3
import config
import time
import datetime

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
        global contract
        global web3
        global nativeTokenAddress
        global nameNativeContract
        global symbolNativeContract
        global humanReadableBalance
        global DexChosen

        DexChosen = df.loc[df['Dex'] == choiceDex]

        web3 = Web3(Web3.HTTPProvider(DexChosen["Rpc"].values[0]))
        nativeTokenAddress = web3.toChecksumAddress(DexChosen["NativeTokenAddress"].values[0])
        contract = web3.eth.contract(nativeTokenAddress, abi=DexChosen["NativeTokenAbi"].values[0])
        nameNativeContract = contract.functions.name().call()
        symbolNativeContract = contract.functions.symbol().call()
        balance = web3.eth.get_balance(config.sender_address)
        humanReadableBalance = web3.fromWei(balance, 'ether')

        print("Verifying connection ", DexChosen["Blockchain"].values[0], " : ", web3.isConnected())
        print("Native token of the blockchain is ", nameNativeContract, "(", symbolNativeContract,
              "), address is : ", nativeTokenAddress)

        contract = web3.eth.contract(
            address=web3.toChecksumAddress(DexChosen["RouterAddress"].values[0]),
            abi=DexChosen["RouterAddressAbi"].values[0])

        print("You have chosen DEX : ", DexChosen["Dex"].values[0])
    else:
        print("Incorrect value. Please select a DEX in the following list ", liste_dex )
        print("")
        choice_dex()


def param_tx():

    def gasPriceChoice():
        global choiceGasPrice
        global finalGasPrice
        global gasPrice
        global gasPriceGwei
        choiceGasPrice = None
        print("Current gas price is :",  web3.fromWei(web3.eth._gas_price(),"gwei") ,"gwei on the blockchain",
            DexChosen["Blockchain"].values[0])

        choiceGasPrice = input(("Please select a multiplier on the current gas price : "))
        gasPrice = web3.eth._gas_price()
        gasPriceGwei = web3.fromWei(gasPrice, "gwei")
        finalGasPrice = float(gasPriceGwei) * float(choiceGasPrice)
        print("Timestamp : ", datetime.datetime.now(), " - Gas price of your transaction will be ", finalGasPrice, "gwei.")

    def setAmountTokenToSpend():
        global amountTokenToSpend
        print("You have ", humanReadableBalance, " ", symbolNativeContract, " in your wallet")
        print("How many ", nameNativeContract, "(", symbolNativeContract, ") do you want to spend ?")
        amountTokenToSpend = input("Select the amount here : ")
        if float(amountTokenToSpend) >= float(humanReadableBalance):
            print("The value selected must be inferior to : ", humanReadableBalance )
            print("")
            setAmountTokenToSpend()

    def setSlippage():
        slippage = float(input("Select the slippage (between 0.1 and 99.9): "))
        if 0.1 <= slippage <= 99.9:
            global slippage_percent
            slippage_percent = slippage / 100
        else:
            print("Slippage must be set between 0.1 and 99.9. Retry.")
            print("")
            setSlippage()

    def setTokenToBuy():
        global tokenToBuy
        print("/!\ the transaction will be sent directly after this step /!\ ")
        tokenAddressChosen = input("Type the address of the token you want to buy : ")
        if Web3.isAddress(tokenAddressChosen):
            tokenToBuy = Web3.toChecksumAddress(tokenAddressChosen)
        else:
            print("The token address that you typed is not a token address. Retry.")
            print("")
            setTokenToBuy()

    ### Call parameters functions
    gasPriceChoice()
    setAmountTokenToSpend()
    setSlippage()
    setTokenToBuy()

    # Cake = 0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82 - BsC
    # Solar = 0x6bD193Ee6D2104F14F94E2cA6efefae561A4334B - Moonriver
    # Joe = 0x6e84a6216eA6dACC71eE8E6b0a5B7322EEbC0fDd - Avalanche
    # Spirit = 0x5Cc61A78F164885776AA610fb0FE1257df78E59B - Fantom
    # Boo = 0x841fad6eae12c286d1fd18d1d525dffa75c7effe - Fantom
    # Quick = 0x831753DD7087CaC61aB5644b308642cc1c33Dc13 - Polygon
    # Trisolaris = 0xFa94348467f64D5A457F75F8bc40495D33c65aBB - Aurora
    # VVS = 0x2D03bECE6747ADC00E1a131BBA1469C15fD11e03 - Cronos

def send_tx():
    global nonce
    nonce = web3.eth.get_transaction_count(config.sender_address)
    gasPrice = web3.eth._gas_price()
    gasPriceGwei = web3.fromWei(gasPrice, "gwei")
    finalGasPrice = float(gasPriceGwei) * float(choiceGasPrice)
    print("UPDATE Timestamp : ", datetime.datetime.now(), " - Gas price of your transaction is", finalGasPrice, "gwei.")

    def setBuyAmount():
        global buy_amount
        if DexChosen["Dex"].values[0] == "solarbeam":
            buy_amount = contract.functions.getAmountsOut(
                web3.toWei(amountTokenToSpend, "ether"),
                [nativeTokenAddress, tokenToBuy],  # [SELL, BUY]
                0
            ).call()
        else:
            buy_amount = contract.functions.getAmountsOut(
                web3.toWei(amountTokenToSpend, "ether"),
                [nativeTokenAddress, tokenToBuy]  # [SELL, BUY]
            ).call()

    setBuyAmount()
    humanReadable_buyamount = float(web3.fromWei(buy_amount[1], "ether"))
    global minimumTokenReceived
    minimumTokenReceived = humanReadable_buyamount * (1 - slippage_percent)
    print("You will receive ", humanReadable_buyamount, " tokens (", minimumTokenReceived, " at the minimum) for",
          amountTokenToSpend, " ", nameNativeContract, "(", symbolNativeContract, ") spent")

    if DexChosen["Dex"].values[0] == "traderjoe":
        tx = contract.functions.swapExactAVAXForTokens(
            web3.toWei(minimumTokenReceived, 'ether'),
            # set to 0 or specify the minimum amount of tokens you want to receive -- consider decimals
            [nativeTokenAddress, tokenToBuy],
            config.sender_address,
            (int(time.time()) + 10000)
        ).buildTransaction({
            'from': config.sender_address,
            'value': web3.toWei(amountTokenToSpend, 'ether'),
            # This is the token BNB amount you want to swap from
            'gas': 1000000,
            'gasPrice': web3.toWei(finalGasPrice, 'gwei'),
            'nonce': nonce,
        })

    else:
        tx = contract.functions.swapExactETHForTokens(
            web3.toWei(minimumTokenReceived, 'ether'),
            # set to 0 or specify the minimum amount of tokens you want to receive -- consider decimals
            [nativeTokenAddress, tokenToBuy],
            config.sender_address,
            (int(time.time()) + 10000)
        ).buildTransaction({
            'from': config.sender_address,
            'value': web3.toWei(amountTokenToSpend, 'ether'),
            'gas': 1000000,
            'gasPrice': web3.toWei(finalGasPrice, 'gwei'),
            'nonce': nonce,
        })

    signed_txn = web3.eth.account.sign_transaction(tx, private_key=config.private)
    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print("Transaction ID : ",web3.toHex(tx_token))
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
    again = input("Send same transaction ? type 'ok' if you want : ")
    if again.lower() == "ok":
        send_tx()
    else:
        print("")
        print("End of the script, send donations if you feel like it : 0xf444955E4dC892198E8a733ffCf08aaA13Bea096 :) ")
        exit()

def main():
    choice_dex()
    param_tx()
    send_tx()
main()

