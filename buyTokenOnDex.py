import pandas as pd
from web3 import Web3
import config
import const
import time
import datetime

"""

Utility functions 
"""

def checkPairExist(contract_factory,token_a,symb_a,token_b, symb_b): #Return boom
    token_a = token_a
    token_b = token_b

    symb_a = symb_a
    symb_b = symb_b

    pair = contract_factory.functions.getPair(token_a, token_b).call()
    if pair == "0x0000000000000000000000000000000000000000":
        bool = False
    else:
        bool = True
    print(f"Timestamp {datetime.datetime.now()} Checking existence of token pair on factory :{symb_a}/{symb_b} : {bool}")
    return bool


def waitForTxResponse(tx):
    global tx_status
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


def checkApproval(contract_token,token_symbol,router,sender,): # return bool
    # approval max constants
    max_approval_check_hex = f"0x{15 * '0'}{49 * 'f'}"
    max_approval_check_int = int(max_approval_check_hex, 16)

    # check allowance of the token to spend
    print("Checking " + token_symbol + " allowance on router...")
    token_allowance = contract_token.functions.allowance(sender, router).call()
    if token_allowance <= max_approval_check_int:
        print(token_symbol,"is not approved.")
        return False
    else:
        print(token_symbol, "already approved.")
        return True

def approve(contract_token,token_symbol,router,sender):
    getGasPrice(gas_price_multiplier)
    max_approval_hex = f"0x{64 * 'f'}"
    max_approval_int = int(max_approval_hex, 16)
    print("Now approving " + token_symbol,"...")
    tx = contract_token.functions.approve(router, max_approval_int).buildTransaction({
        'from': sender,
        'nonce': web3.eth.get_transaction_count(sender),
        'gasPrice': web3.toWei(gas_price_final_gwei ,"gwei")
    })
    return tx

def getNativeTokenPrice(pair_exist):
    global native_token_price
    global native_token_price_readable

    if pair_exist == True:
        native_token_price = getAmountOut(dex=dex_chosen["Dex"].values[0], amount_token_spend=1,
                                          decimals=native_token_decimals,
                                          token_to_spend=native_token_address, token_to_buy=stable_coin_token_address)

        native_token_price_readable = float(native_token_price[1]) / (10 ** float(stable_coin_decimals))
    else:
        print("There is no trading pair between " + native_token_symbol + "and" + stable_coin_symbol)
        print("Something is wrong please check and retry.")
        exit()

def chooseToken(method):
    token_chosen = input("Enter the address of the token you want to " + method + " : ")
    if Web3.isAddress(token_chosen):
        token_chosen_address = Web3.toChecksumAddress(token_chosen)
    else:
        print("The token address that you typed is not a token address. Retry.")
        print("")
        chooseToken()
    return token_chosen_address

def swapExactNativeForTokens(dex,token_spend,token_buy,sender_address,amount_to_spend,gas_price, decimals):

    amount_to_spend = int(float(amount_to_spend) * (10 ** float(decimals)))

    if dex == "traderjoe":
        tx = contract_router.functions.swapExactAVAXForTokens(
            0,
            # set to 0 or specify the minimum amount of tokens you want to receive -- consider decimals
            [token_spend, token_buy],
            sender_address,
            (int(time.time()) + 10000)
        ).buildTransaction({
            'from': config.sender_address,
            'value': amount_to_spend,
            # This is the token BNB amount you want to swap from
            # 'gas': 1000000,
            'gasPrice': web3.toWei(gas_price, 'gwei'),
            'nonce': nonce
        })
    elif dex == "netswap":
        tx = contract_router.functions.swapExactMetisForTokens(
            0, # set to 0 or specify the minimum amount of tokens you want to receive -- consider decimals
            [token_spend, token_buy],
            sender_address,
            (int(time.time()) + 10000)
        ).buildTransaction({
            'from': config.sender_address,
            'value': amount_to_spend,
            # This is the token BNB amount you want to swap from
            'gas': 1000000,
            'gasPrice': web3.toWei(gas_price, 'gwei'),
            'nonce': nonce
        })
    else:
        tx = contract_router.functions.swapExactETHForTokens(
            0, # set to 0 or specify the minimum amount of tokens you want to receive -- consider decimals
            [token_spend, token_buy],
            sender_address,
            (int(time.time()) + 10000)
        ).buildTransaction({
            'from': config.sender_address,
            'value': amount_to_spend,
            # This is the token BNB amount you want to swap from
            'gas': 1000000,
            'gasPrice': web3.toWei(gas_price, 'gwei'),
            'nonce': nonce
        })
    return tx

def swapExactTokensForNative(dex,token_spend,token_buy,sender_address,amount_spend,gas_price,decimals):

    amount_to_spend = int(float(amount_spend) * (10 ** float(decimals)))

    if dex == "traderjoe":
        tx = contract_router.functions.swapExactTokensForAVAX(
            amount_to_spend,
            0,
            # set to 0 or specify the minimum amount of tokens you want to receive -- consider decimals
            [token_spend, token_buy],
            sender_address,
            (int(time.time()) + 10000)
        ).buildTransaction({
            'from': config.sender_address,
            'gas': 1000000,
            'gasPrice': web3.toWei(gas_price, 'gwei'),
            'nonce': nonce
        })
    elif dex == "netswap":
        tx = contract_router.functions.swapExactTokensForMetis(
            amount_to_spend,
            0,
            # set to 0 or specify the minimum amount of tokens you want to receive -- consider decimals
            [token_spend, token_buy],
            sender_address,
            (int(time.time()) + 10000)
        ).buildTransaction({
            'from': config.sender_address,
            'gas': 1000000,
            'gasPrice': web3.toWei(gas_price, 'gwei'),
            'nonce': nonce
        })
    else:
        tx = contract_router.functions.swapExactTokensForETH(
            amount_to_spend,
            0,
            # set to 0 or specify the minimum amount of tokens you want to receive -- consider decimals
            [token_spend, token_buy],
            sender_address,
            (int(time.time()) + 10000)
        ).buildTransaction({
            'from': config.sender_address,
            'gas': 1000000,
            'gasPrice': web3.toWei(gas_price, 'gwei'),
            'nonce': nonce
        })
    return tx

def swapExactTokensForTokens(amount_spend,spend_address,buy_address,sender,gas_price,decimals):

    amount_to_spend = int(float(amount_spend) * (10 ** float(decimals)))

    tx = contract_router.functions.swapExactTokensForTokens(
        amount_to_spend,
        0,
        [spend_address, buy_address],
        sender,
        (int(time.time()) + 10000)
    ).buildTransaction({
        'from': sender,
        'gas': 1000000,
        'gasPrice': web3.toWei(gas_price, 'gwei'),

        #'maxFeePerGas': web3.toWei(gas_price, 'gwei'),
        #'maxPriorityFeePerGas': web3.toWei(gas_price, 'gwei'),
        'nonce': nonce
    })
    return tx

def getPairLiquidity(token_a,token_b,contract_factory,asset_to_scan, amount_asset_to_scan):
    global token0_symbol
    global token1_symbol
    global pair
    global token0_symbol
    global reserve_token0_readable
    global token1_symbol
    global reserve_token1_readable

    pair = web3.toChecksumAddress(contract_factory.functions.getPair(token_a,token_b).call())

    pair_contract = web3.eth.contract(address = pair, abi = const.lp_abi )
    token0_address = web3.toChecksumAddress(pair_contract.functions.token0().call())
    token1_address = web3.toChecksumAddress(pair_contract.functions.token1().call())

    token0_contract = web3.eth.contract(address = token0_address , abi =const.erc20_abi)
    token1_contract = web3.eth.contract(address= token1_address, abi=const.erc20_abi)

    token0_symbol = token0_contract.functions.symbol().call()
    token1_symbol = token1_contract.functions.symbol().call()

    token0_decimals = token0_contract.functions.decimals().call()
    token1_decimals = token1_contract.functions.decimals().call()

    pair_reserve = pair_contract.functions.getReserves().call()

    reserve_token_0 = pair_reserve[0]
    reserve_token_1 = pair_reserve[1]

    reserve_token0_readable = float(reserve_token_0) / 10 ** float(token0_decimals)
    reserve_token1_readable = float(reserve_token_1) / 10 ** float(token1_decimals)

    if asset_to_scan == token0_symbol:
        reserve_token_to_scan = reserve_token_0
        #reserve_token_to_scan_readable = reserve_token0_readable
        amount_asset_to_scan = int(amount_asset_to_scan * (10 ** token0_decimals))
    elif asset_to_scan == token1_symbol:
        reserve_token_to_scan = reserve_token_1
        #reserve_token_to_scan_readable = reserve_token1_readable
        amount_asset_to_scan = int(amount_asset_to_scan * (10 ** token1_decimals))

    if reserve_token_to_scan <= amount_asset_to_scan:
        return False
    else:
        return True


"""
End utility functions 
"""

"""
Execution functions
"""

#1) choose the dex and initiate parameters
def choice_dex():
    global contract_router
    global contract_factory

    global web3
    global contract
    global native_token_address
    global native_token_name
    global native_token_symbol
    global native_token_balance_readable
    global native_token_balance
    global native_token_decimals
    global native_token_abi

    global stable_coin_token_address
    global stable_coin_name
    global stable_coin_symbol
    global stable_coin_decimals
    global dex_chosen

    global router_address
    global factory_address

    global exist_pair_native_stable

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

        dex_chosen = df.loc[df['Dex'] == choiceDex]

        web3 = Web3(Web3.HTTPProvider(dex_chosen["Rpc"].values[0]))

        stable_coin_token_address = web3.toChecksumAddress(dex_chosen["StablecoinTokenAddress"].values[0])
        stable_coin_name = dex_chosen["StablecoinName"].values[0]
        stable_coin_symbol = dex_chosen["StablecoinSymbol"].values[0]
        stable_coin_decimals = dex_chosen["StablecoinDecimals"].values[0]

        native_token_address = web3.toChecksumAddress(dex_chosen["NativeTokenAddress"].values[0])
        native_token_abi = dex_chosen["NativeTokenAbi"].values[0]
        contract = web3.eth.contract(native_token_address, abi=native_token_abi)
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

        router_address = web3.toChecksumAddress(dex_chosen["RouterAddress"].values[0])

        contract_factory = web3.eth.contract(
            address=web3.toChecksumAddress(dex_chosen["FactoryAddress"].values[0]),
            abi=dex_chosen["FactoryAddressAbi"].values[0])

        factory_address = web3.toChecksumAddress(dex_chosen["FactoryAddress"].values[0])

        exist_pair_native_stable = checkPairExist(contract_factory, native_token_address, native_token_symbol,
                                                  stable_coin_token_address, stable_coin_symbol)
        getNativeTokenPrice(exist_pair_native_stable)
        print("Timestamp : ", datetime.datetime.now(), "- the price for 1", native_token_symbol, "is",
              native_token_price_readable, stable_coin_symbol)

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

#3) Set choice swap method
def choiceSwapMethod():
    global swap_method_chosen
    print("Choose your swap method : ")
    print(" - Type 1 if you want to swap exact number of " + native_token_symbol + " for token")
    print(" - Type 2 if you want to swap exact number of token A for token B ")
    print(" - Type 3 if you want to swap exact number of a token for " + native_token_symbol )
    #print(" - Type 4 if you want to swap token A for exact number of token B ")

    swap_method_chosen = input("Type your choice here : ")

    if (swap_method_chosen == "1" or swap_method_chosen == "2" or swap_method_chosen == "3"):
        print("You have chosen method " + swap_method_chosen)
    else:
        print("You have to choose between the options proposed. Retry.")
        choiceSwapMethod()


#4) Set token to spend parameters depending on swap method chosen

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

    elif swap_method_chosen == "2" or swap_method_chosen == "3": # Here token to spend parameters have to be requested

        token_to_spend_address = chooseToken(method="spend")
        token_to_spend_abi = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"value","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
        contract_token_to_spend = web3.eth.contract(token_to_spend_address, abi=token_to_spend_abi)
        token_to_spend_balance = contract_token_to_spend.functions.balanceOf(config.sender_address).call()
        token_to_spend_decimals = contract_token_to_spend.functions.decimals().call()
        token_to_spend_symbol = contract_token_to_spend.functions.symbol().call()
        token_to_spend_balance_readable = float(token_to_spend_balance) / (10 ** float(token_to_spend_decimals))

        token_to_spend_approval = checkApproval(contract_token_to_spend,token_to_spend_symbol,router_address
                                                ,config.sender_address)
        if token_to_spend_approval == False:
            tx = approve(contract_token_to_spend,token_to_spend_symbol,router_address
                                                ,config.sender_address)
            waitForTxResponse(tx)

def choiceScanLiquidityAdded():
    global choice_scan_liq
    choice_scan_liq = ""
    print("Do you want to buy only if liquidity is added ? ")
    choice_scan_liq = input("Type yes or no : ")
    if choice_scan_liq.lower() != "yes" and choice_scan_liq.lower() != "no":
        print("Choice might be yes or no")
        choiceScanLiquidityAdded()

def choiceStopPrice():
    global choice_stop_price
    choice_stop_price = ""
    print("Do you want to set a stop price on your swap")
    choice_stop_price = input("Type yes or no : ")
    if choice_stop_price.lower() != "yes" and choice_stop_price.lower() != "no":
        print("Choice might be yes or no")
        choiceStopPrice()


# 5) choose token to spend amount
def choiceAmountToSpend():
    global amount_token_to_spend
    if swap_method_chosen == "3" and choice_stop_price.lower() == "no":
        print("/!\ the script will run directly after this step /!\ ")

    print("You have ", "{:.18f}".format(token_to_spend_balance_readable) , " ", token_to_spend_symbol, " in your wallet")
    print("How many", token_to_spend_symbol, "do you want to spend ?")
    print("Type :")
    print(" - '1' if you want to spend a fixed amount ")
    print(" - '2' if you want to spend a percentage of your token balance ")
    choice_amount_to_spend = input("Type your selection here : ")

    if choice_amount_to_spend == "1":
        amount_token_to_spend = input("Select the amount of token that you want to sell : ")
        if 0 > float(amount_token_to_spend) >= float(token_to_spend_balance_readable):
            print("The value selected must be inferior to : ", token_to_spend_balance_readable, ", nor negative.")
            print("")
            choiceAmountToSpend()
    elif choice_amount_to_spend == "2":

        def selectAmountSpendPercent():
            global amount_token_to_spend
            percentage_base_100 = input("Select percentage of your token balance you want to sell (between 0.1 to 100): ")
            if 0.1 <= float(percentage_base_100) <= 100:
                percentage = float(percentage_base_100) / 100
                amount_token_to_spend = float(token_to_spend_balance_readable) * float(percentage)
                print("You gonna spend :", amount_token_to_spend , token_to_spend_symbol)
            else:
                print("Please select a correct percentage.")
                selectAmountSpendPercent()
        selectAmountSpendPercent()

    else:
        print("Please choose between the option proposed.")
        choiceAmountToSpend()

def setStopLoss():
    global stop_loss_set

    print("Do you want to set a stop loss ? Type 'yes' or 'no'")
    stop_loss_choice = input("Type your answer here : ")
    if stop_loss_choice == "yes":
        stop_loss_set = True

        def selectStopLoss():
            global stop_loss_percentage
            print("At which % of your entry price do you want to set your stop loss?")
            print("(e.g : if you want to set your stop loss at -50% of your entry price, type 50)")
            stop_loss_percentage_base_100 = input("Type your answer here (must be between 0 and 99.9 ) : ")
            if 0 <= float(stop_loss_percentage_base_100) <= 99.9:
                stop_loss_percentage = float(stop_loss_percentage_base_100) / float(100)
                print("Stop loss gonna be set at",stop_loss_percentage_base_100,"% of your entry price.")
            else:
                print("Percentage entered should be between 0 and 99.9. Retry")
                selectStopLoss()

        selectStopLoss()

    elif stop_loss_choice == "no":
        stop_loss_set = False
        print("No stop loss gonna be set.")

    else:
        print("Answer should be 'yes' or 'no'")
        setStopLoss()

def setTakeProfit():
    global take_profit_set

    print("Do you want to set a take profit ? Type 'yes' or 'no'")
    take_profit_choice = input("Type your answer here : ")
    if take_profit_choice == "yes":
        take_profit_set = True

        def selectTakeProfit():
            global take_profit_percentage
            print("At which % of the entry price do you want to set your take profit")
            print("(e.g : if you want to set your take profit at +50% of your entry price, type 50)")
            take_profit_percentage_base_100 = input("Type your answer here (must be between 0 and 99.9 ) : ")
            if 0 < float(take_profit_percentage_base_100):
                take_profit_percentage = float(take_profit_percentage_base_100) / 100
                print("Take profit gonna be set at", take_profit_percentage_base_100, "% from your entry price.")
            else:
                print("Percentage entered should be superior to 0. Retry")
                selectTakeProfit()

        selectTakeProfit()

    elif take_profit_choice == "no":
        take_profit_set = False
        print("No take profit gonna be set.")

    else:
        print("Answer should be 'yes' or 'no'")
        setTakeProfit()

# 6) set parameters for token to buy
def setTokenToBuyParameters():
    global token_to_buy_address
    global token_to_buy_balance
    global token_to_buy_decimals
    global token_to_buy_symbol
    global token_to_buy_balance_readable
    global contract_token_to_buy


    if swap_method_chosen != "3" :
        if choice_stop_price.lower() == "no":
            print("/!\ the script will run directly after this step /!\ ")
        token_to_buy_address = chooseToken(method="buy")
        token_to_buy_abi = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"value","type":"uint256"}],"name":"burn","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"subtractedValue","type":"uint256"}],"name":"decreaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"addedValue","type":"uint256"}],"name":"increaseAllowance","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"sender","type":"address"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
        contract_token_to_buy = web3.eth.contract(token_to_buy_address, abi=token_to_buy_abi)
        token_to_buy_balance = contract_token_to_buy.functions.balanceOf(config.sender_address).call()
        token_to_buy_decimals = contract_token_to_buy.functions.decimals().call()
        token_to_buy_symbol = contract_token_to_buy.functions.symbol().call()
        token_to_buy_balance_readable = float(token_to_buy_balance) / (10 ** float(token_to_buy_decimals))
    elif swap_method_chosen == "3":
        token_to_buy_address = native_token_address
        token_to_buy_abi = native_token_abi
        contract_token_to_buy = contract
        token_to_buy_decimals = native_token_decimals
        token_to_buy_balance = native_token_balance
        token_to_buy_symbol = native_token_symbol
        token_to_buy_balance_readable =native_token_balance_readable



def setStopPrice():
    global token_to_stop_symbol
    global token_to_stop_price
    if choice_stop_price.lower() == "yes":

        print(f"On which asset do you want to set a stop price : {token_to_spend_symbol} or {token_to_buy_symbol}")
        token_to_stop_symbol = input(f"Type your choice here : ").upper()
        if token_to_stop_symbol.lower() == token_to_spend_symbol.lower()\
                or token_to_stop_symbol.lower() == token_to_buy_symbol.lower():
            print("/!\ the script will run directly after this step /!\ ")
            token_to_stop_price = float(input(f"Type the stop price (in $) of {token_to_stop_symbol} : "))
            if token_to_stop_price <= 0:
                print("Stop price must be > 0")
                setStopPrice()
        else:
            print(f"You have to choose between {token_to_spend_symbol} or {token_to_buy_symbol}")
            setStopPrice()




def checkExistingPairs():
    global exist_pair_token_to_buy_native
    global exist_pair_token_to_spend_token_to_buy
    global exist_pair_token_to_spend_native

    exist_pair_token_to_buy_native = checkPairExist(contract_factory,
                                                    native_token_address , native_token_symbol
                                                     , token_to_buy_address, token_to_buy_symbol )

    exist_pair_token_to_spend_native = checkPairExist(contract_factory,
                                                      native_token_address , native_token_symbol
                                                      , token_to_spend_address, token_to_spend_symbol)

    exist_pair_token_to_spend_token_to_buy = checkPairExist(contract_factory,
                                                            token_to_buy_address, token_to_buy_symbol,
                                                            token_to_spend_address, token_to_spend_symbol)


def scanLiquidity():
    if choice_scan_liq.lower() == "yes":
        asset_scan_liq = input(f"Select the asset that must be scanned between {token_to_spend_symbol} "
                               f"and {token_to_buy_symbol} : ")
        if asset_scan_liq == token_to_spend_symbol or asset_scan_liq == token_to_buy_symbol:
            amount_asset_scan_liq = float(input(f"Type the amount of {asset_scan_liq}"
                                                f" that must be added in the liquidity pool : "))
            if amount_asset_scan_liq < 0:
                print(f"Please select an amount > 0")
                scanLiquidity()
        else:
            print(f"Please select between {token_to_spend_symbol} or {token_to_buy_symbol}")
            scanLiquidity()

        exist_pair_token_to_spend_token_to_buy = checkPairExist(contract_factory,
                                                               token_to_buy_address, token_to_buy_symbol,
                                                               token_to_spend_address, token_to_spend_symbol)
        while exist_pair_token_to_spend_token_to_buy == False:
            exist_pair_token_to_spend_token_to_buy = checkPairExist(contract_factory,
                                                                    token_to_buy_address, token_to_buy_symbol,
                                                                    token_to_spend_address, token_to_spend_symbol)

        if exist_pair_token_to_spend_token_to_buy == True:
            pair_liquidity = getPairLiquidity(token_a=token_to_spend_address,
                                              token_b=token_to_buy_address,
                                              contract_factory=contract_factory,
                                              asset_to_scan = asset_scan_liq,
                                              amount_asset_to_scan =amount_asset_scan_liq )

            print(f'Timestamp : ≈ {datetime.datetime.now()} - pair {token0_symbol} / {token1_symbol}'
                  f'Token pair : {pair}'
                  f'Reserve {token0_symbol} : {reserve_token0_readable}'
                  f'Reserve {token1_symbol} : {reserve_token1_readable}')

            last_reserve_0 = reserve_token0_readable
            last_reserve_1 = reserve_token1_readable
            while pair_liquidity == False:
                pair_liquidity = getPairLiquidity(token_a=token_to_spend_address,
                                              token_b=token_to_buy_address,
                                              contract_factory=contract_factory,
                                              asset_to_scan = asset_scan_liq,
                                              amount_asset_to_scan = amount_asset_scan_liq)
                if last_reserve_0 != reserve_token0_readable and last_reserve_1 !=reserve_token1_readable:
                    print(f'Timestamp : ≈ {datetime.datetime.now()} - pair {token0_symbol} / {token1_symbol}'
                          f'Token pair : {pair}'
                          f'Reserve {token0_symbol} : {reserve_token0_readable}'
                          f'Reserve {token1_symbol} : {reserve_token1_readable}')

                if pair_liquidity == True:
                    print(f"Timestamp {datetime.datetime.now()} - "
                          f"{asset_scan_liq} liquidity is equal or above {amount_asset_scan_liq}")

                last_reserve_0 = reserve_token0_readable
                last_reserve_1 = reserve_token1_readable




# 7) Set buy amount
def getTokenPrices():
    global trading_pair_exist
    global token_to_buy_price_fiat
    global token_to_spend_price_fiat

    getNativeTokenPrice(exist_pair_native_stable) #On actualise les données de prix du token

    if token_to_spend_address != native_token_address:
        #Token to spend is not the native token
        if exist_pair_token_to_spend_native == True and exist_pair_token_to_spend_token_to_buy == True :
            # Get token price A and B given A
            def getTokensPriceFromTokenA():
                global buy_amount_ether
                global token_to_spend_price_fiat
                global token_to_buy_price_fiat
                buy_amount_native_token = getAmountOut(dex=dex_chosen["Dex"].values[0],
                                                       amount_token_spend=amount_token_to_spend,
                                                       decimals=token_to_spend_decimals,
                                                       token_to_spend=token_to_spend_address,
                                                       token_to_buy=native_token_address)
                buy_amount = getAmountOut(dex=dex_chosen["Dex"].values[0],
                                          amount_token_spend=amount_token_to_spend,
                                          decimals=token_to_spend_decimals,
                                          token_to_spend=token_to_spend_address, token_to_buy=token_to_buy_address)
                buy_amount_native_token_ether = returnEtherValue(buy_amount_native_token[1], native_token_decimals)
                buy_amount_ether = returnEtherValue(buy_amount[1], token_to_buy_decimals)

                token_to_spend_price_fiat = (float(buy_amount_native_token_ether) /float(amount_token_to_spend)) * \
                                            float(native_token_price_readable)
                token_to_buy_price_fiat = (float(amount_token_to_spend) / float(buy_amount_ether)) * \
                                          float(token_to_spend_price_fiat)


            getTokensPriceFromTokenA()

        elif  exist_pair_token_to_buy_native == True and exist_pair_token_to_spend_token_to_buy == True :
            # Get token price A and B given B
            def getTokensPriceFromTokenB():
                global buy_amount_ether
                global token_to_spend_price_fiat
                global token_to_buy_price_fiat

                buy_amount = getAmountOut(dex=dex_chosen["Dex"].values[0],
                                          amount_token_spend=amount_token_to_spend,
                                          decimals=token_to_spend_decimals,
                                          token_to_spend=token_to_spend_address, token_to_buy=token_to_buy_address)
                buy_amount_native_token = getAmountOut(dex=dex_chosen["Dex"].values[0],
                                                   amount_token_spend=returnEtherValue(buy_amount[1], token_to_buy_decimals),
                                                   decimals=token_to_buy_decimals,
                                                   token_to_spend=token_to_buy_address,
                                                   token_to_buy=native_token_address)
                buy_amount_ether = returnEtherValue(buy_amount[1], token_to_buy_decimals)
                buy_amount_native_token_ether = returnEtherValue(buy_amount_native_token[1], native_token_decimals)

                token_to_buy_price_fiat = (float(buy_amount_native_token_ether) / float(buy_amount_ether)) * \
                                          float(native_token_price_readable)

                token_to_spend_price_fiat = (float(buy_amount_ether) / float(amount_token_to_spend)) * \
                                            float(token_to_buy_price_fiat)


            getTokensPriceFromTokenB()


        elif exist_pair_token_to_spend_token_to_buy == False and  exist_pair_token_to_buy_native == True and  exist_pair_token_to_spend_native == True :
            # Case when token to buy and token to spend don't have a LP but both of them have a pair with native token
            def getTokensPriceFromNative():
                global buy_amount_ether
                global token_to_spend_price_fiat
                global token_to_buy_price_fiat
                buy_amount_native_token = getAmountOut(dex=dex_chosen["Dex"].values[0],
                                                       amount_token_spend=amount_token_to_spend,
                                                       decimals=token_to_spend_decimals,
                                                       token_to_spend=token_to_spend_address,
                                                       token_to_buy=native_token_address)
                # Amount in native blockchain token converted to token we want to spend
                buy_amount = getAmountOut(dex=dex_chosen["Dex"].values[0],
                                          amount_token_spend=web3.fromWei(buy_amount_native_token[1], "ether"),
                                          decimals=native_token_decimals,
                                          token_to_spend=native_token_address, token_to_buy=token_to_buy_address)

                buy_amount_native_token_ether = returnEtherValue(buy_amount_native_token[1], native_token_decimals)
                buy_amount_ether = returnEtherValue(buy_amount[1], token_to_buy_decimals)
                token_to_spend_price_fiat = (float(buy_amount_native_token_ether) * float(
                    native_token_price_readable)) / float(amount_token_to_spend)
                token_to_buy_price_fiat = (float(buy_amount_native_token_ether) * float(
                    native_token_price_readable)) / float(buy_amount_ether)

            getTokensPriceFromNative()

        else:
            print("There is no liquidity pair at all between the tokens you want to swap")
            print("Impossible to fetch price")
            ending()

    else:
        #Token to spend is native
        def getTokenPriceFromNative():
            global buy_amount_ether
            global token_to_spend_price_fiat
            global token_to_buy_price_fiat

            buy_amount = getAmountOut(dex=dex_chosen["Dex"].values[0],
                                      amount_token_spend=amount_token_to_spend,
                                      decimals=native_token_decimals,
                                      token_to_spend=native_token_address, token_to_buy=token_to_buy_address)
            buy_amount_ether = returnEtherValue(buy_amount[1], token_to_buy_decimals)
            token_to_spend_price_fiat = float(native_token_price_readable)
            token_to_buy_price_fiat = (float(native_token_price_readable) * float(amount_token_to_spend)) / float(buy_amount_ether)

        getTokenPriceFromNative()

def stopPrice():
    if choice_stop_price.lower() == "yes" and exist_pair_token_to_spend_token_to_buy == True:
        if exist_pair_token_to_spend_token_to_buy == True:
            # We initiate the while loop that is coming after
            getTokenPrices()
            if token_to_stop_symbol == token_to_spend_symbol.upper():
                token_to_stop_price_fiat = token_to_spend_price_fiat  # token to spend price FIAT
            elif token_to_stop_symbol == token_to_buy_symbol.upper() :
                token_to_stop_price_fiat = token_to_buy_price_fiat  # token to buy price FIAT

            if token_to_stop_price < token_to_stop_price_fiat:
                print(f"Timestamp : {datetime.datetime.now()} - "
                      f"When {token_to_spend_symbol} price drop below {token_to_stop_price} $"
                      f" current price is {token_to_stop_price_fiat}$")
                stop_side = "below"
            elif token_to_stop_price > token_to_stop_price_fiat:
                print(f"Setting stop on {token_to_stop_symbol} when price is above {token_to_stop_price}"
                      f" current price is {token_to_stop_price_fiat}$")
                stop_side = "above"
            else:
                print("The stop price that you have set is already equal to the current token price")
                ending()

            # initiate condition for while loop
            condition = False
            token_to_stop_price_fiat_last = 0
            while condition == False:

                getTokenPrices()
                if token_to_stop_symbol == token_to_spend_symbol.upper():
                    token_to_stop_price_fiat = token_to_spend_price_fiat  # token to spend price FIAT
                elif token_to_stop_symbol == token_to_buy_symbol.upper():
                    token_to_stop_price_fiat = token_to_buy_price_fiat  # token to buy price FIAT

                if stop_side == "below":
                    delta = (1 - (token_to_stop_price / token_to_stop_price_fiat)) * 100
                if stop_side == "above":
                    delta = ((token_to_stop_price / token_to_stop_price_fiat) - 1) * 100

                delta_formatted = f"{delta:.2f}"
                if token_to_stop_price_fiat_last != token_to_stop_price_fiat:
                    print(f"Timestamp {datetime.datetime.now()} - Current price of {token_to_stop_symbol} "
                          f"is {token_to_stop_price_fiat} $ - {delta_formatted}% before swap is executed")


                if stop_side == "below" and token_to_stop_price_fiat <= token_to_stop_price:
                    print(f"The price is below {token_to_stop_price_fiat}, swap engaged")
                    condition = True

                elif stop_side == "above" and token_to_spend_price_fiat >= token_to_stop_price_fiat:
                    print(f"The price is above {token_to_stop_price_fiat}, swap engaged")
                    condition = True
                token_to_stop_price_fiat_last = token_to_stop_price_fiat


def tradePreview():
    global stop_loss_value
    global take_profit_value

    print(f"FIAT price of {token_to_spend_symbol}  : {token_to_spend_price_fiat}")
    print(f"FIAT price of {token_to_buy_symbol} : {token_to_buy_price_fiat}")

    print("You will receive ", "{:.5f}".format(buy_amount_ether), token_to_buy_symbol, "for", amount_token_to_spend,
          token_to_spend_symbol)
    print("Your fiat entry  price on",token_to_buy_symbol,"is :",token_to_buy_price_fiat)

    if stop_loss_set == True:
        stop_loss_value = float(token_to_buy_price_fiat) * (1 - float(stop_loss_percentage))
        print("Stop loss is set at : ", stop_loss_value)
    if take_profit_set == True:
        take_profit_value = float(token_to_buy_price_fiat) * (1 + float(take_profit_percentage))
        print("Take profit is set at : ", take_profit_value)

    if  exist_pair_token_to_spend_token_to_buy == True:
        pair = contract_factory.functions.getPair(token_to_buy_address, token_to_spend_address).call()
        link = "https://dexscreener.com/" + dex_chosen["Blockchain"].values[0] + "/" + pair
        print("Chart link : ", link)
    else:
        pair_to_spend = contract_factory.functions.getPair(token_to_buy_address, native_token_address).call()
        link_spend = "https://dexscreener.com/" + dex_chosen["Blockchain"].values[0] + "/" + pair_to_spend

        pair_to_buy = contract_factory.functions.getPair(token_to_spend_address, native_token_address).call()
        link_to_buy = "https://dexscreener.com/" + dex_chosen["Blockchain"].values[0] + "/" + pair_to_buy

        print("Chart link token to spend : ", link_spend)
        print("Chart link token to buy : ", link_to_buy)

def sendTxReturn():
    global nonce
    global condition

    amount_token_to_buy_received_readable = float(amount_token_to_buy_received) / (10 ** float(token_to_buy_decimals))

    nonce = web3.eth.get_transaction_count(config.sender_address)
    getGasPrice(gas_price_multiplier)
    if swap_method_chosen == "1":
        tx = swapExactTokensForNative(dex_chosen["Dex"].values[0], token_to_buy_address,
                                      token_to_spend_address, config.sender_address,
                                      amount_token_to_buy_received_readable, gas_price_final_gwei, token_to_buy_decimals)

    elif swap_method_chosen == "2":
        tx = swapExactTokensForTokens(amount_token_to_buy_received_readable,token_to_buy_address, token_to_spend_address,
                                      config.sender_address, gas_price_final_gwei,token_to_buy_decimals)

    elif swap_method_chosen == "3":
        tx = swapExactNativeForTokens(dex_chosen["Dex"].values[0], token_to_buy_address,
                                      token_to_spend_address, config.sender_address,
                                      amount_token_to_buy_received_readable, gas_price_final_gwei, token_to_buy_decimals)
    waitForTxResponse(tx)


def activateStopLossAndTakeProfit():
    condition = False
    token_to_buy_price_fiat_last = 0
    while condition == False:
        getTokenPrices()
        if stop_loss_set == True and take_profit_set == True:
            delta_stop_loss = (1 - (stop_loss_value / token_to_buy_price_fiat)) * 100
            delta_take_profit = ((take_profit_value / token_to_buy_price_fiat) - 1) * 100

            delta_stop_loss_formatted = f"{delta_stop_loss:.2f}"
            delta_take_profit_formatted = f"{delta_take_profit:.2f}"

            if token_to_buy_price_fiat_last != token_to_buy_price_fiat:
                print(
                    f"Timestamp {datetime.datetime.now()} - "
                    f" FIAT price of {token_to_buy_symbol} is {token_to_buy_price_fiat} $ - "
                    f" {delta_stop_loss_formatted}% from current price to stop loss - "
                    f" {delta_take_profit_formatted}% from current price to take profit"
                )

            if token_to_buy_price_fiat <= stop_loss_value or token_to_buy_price_fiat >= take_profit_value:
                if token_to_buy_price_fiat <= stop_loss_value:
                    print("Stop loss activated.")
                if token_to_buy_price_fiat >= take_profit_value:
                    print("Take profit activated.")
                sendTxReturn()
                ending()

        elif stop_loss_set == True and take_profit_set == False:
            delta_stop_loss = (1 - (stop_loss_value / token_to_buy_price_fiat)) * 100

            delta_stop_loss_formatted = f"{delta_stop_loss:.2f}"

            if token_to_buy_price_fiat_last != token_to_buy_price_fiat:
                print(
                    f"Timestamp {datetime.datetime.now()} - "
                    f" FIAT price of {token_to_buy_symbol} is {token_to_buy_price_fiat} $ - "
                    f" {delta_stop_loss_formatted}% from current price to stop loss"
                )
            if token_to_buy_price_fiat <= stop_loss_value:
                print("Stop loss activated.")
                sendTxReturn()
                ending()

        elif stop_loss_set == False and take_profit_set == True:
            delta_take_profit = ((take_profit_value / token_to_buy_price_fiat) - 1) * 100
            delta_take_profit_formatted = f"{delta_take_profit:.2f}"

            if token_to_buy_price_fiat_last != token_to_buy_price_fiat:
                print(
                    f"Timestamp {datetime.datetime.now()} - "
                    f" FIAT price of {token_to_buy_symbol} is {token_to_buy_price_fiat} $ - "
                    f" {delta_take_profit_formatted}% from current price to take profit"
                )
            if token_to_buy_price_fiat >= take_profit_value:
                print("Take profit activated.")
                sendTxReturn()
                ending()
        token_to_buy_price_fiat_last = token_to_buy_price_fiat

#8) Send transaction
def sendTx():
    global nonce
    global amount_token_to_buy_received

    nonce = web3.eth.get_transaction_count(config.sender_address)
    getGasPrice(gas_price_multiplier)

    if swap_method_chosen == "1":
        amount_token_to_buy_before_tx = contract_token_to_buy.functions.balanceOf(config.sender_address).call()
        tx = swapExactNativeForTokens(dex_chosen["Dex"].values[0], token_to_spend_address
                                      , token_to_buy_address, config.sender_address, amount_token_to_spend
                                      , gas_price_final_gwei, token_to_spend_decimals)
        waitForTxResponse(tx)

        check_balance = False
        while check_balance == False:
            amount_token_to_buy_after_tx = contract_token_to_buy.functions.balanceOf(config.sender_address).call()
            if (amount_token_to_buy_after_tx - amount_token_to_buy_before_tx) != 0:
                amount_token_to_buy_after_tx = contract_token_to_buy.functions.balanceOf(config.sender_address).call()
                print(f"Timestamp {datetime.datetime.now()} - Balance updated")
                check_balance = True

        amount_token_to_buy_received = amount_token_to_buy_after_tx - amount_token_to_buy_before_tx
        if tx_status == "sent":
            if stop_loss_set == True or take_profit_set == True:
                token_to_buy_approval = checkApproval(contract_token_to_buy, token_to_buy_symbol, router_address
                                                        , config.sender_address)
                if token_to_buy_approval == False:
                    tx = approve(contract_token_to_buy, token_to_buy_symbol, router_address
                                 , config.sender_address)
                    waitForTxResponse(tx)
                activateStopLossAndTakeProfit()
        else:
            print("Stop loss / Take profit not activated because transaction is not sent")
            ending()

    elif swap_method_chosen == "2":
        if exist_pair_token_to_spend_token_to_buy == True:
            amount_token_to_buy_before_tx = contract_token_to_buy.functions.balanceOf(config.sender_address).call()
            tx = swapExactTokensForTokens(amount_token_to_spend, token_to_spend_address,token_to_buy_address,
                                             config.sender_address,gas_price_final_gwei, token_to_spend_decimals)
            waitForTxResponse(tx)

            check_balance = False
            while check_balance == False:
                amount_token_to_buy_after_tx = contract_token_to_buy.functions.balanceOf(config.sender_address).call()
                if (amount_token_to_buy_after_tx - amount_token_to_buy_before_tx) != 0:
                    amount_token_to_buy_after_tx = contract_token_to_buy.functions.balanceOf(config.sender_address).call()
                    print(f"Timestamp {datetime.datetime.now()} - Balance updated")
                    check_balance = True

            amount_token_to_buy_received = amount_token_to_buy_after_tx - amount_token_to_buy_before_tx
            if stop_loss_set == True or take_profit_set == True:
                if tx_status == "sent":
                    token_to_buy_approval = checkApproval(contract_token_to_buy, token_to_buy_symbol, router_address
                                                          , config.sender_address)
                    if token_to_buy_approval == False:
                        tx = approve(contract_token_to_buy, token_to_buy_symbol, router_address
                                     , config.sender_address)
                        waitForTxResponse(tx)
                    activateStopLossAndTakeProfit()
                else:
                    print("Stop loss / Take profit not activated because transaction is not sent")
                    ending()

        elif exist_pair_token_to_spend_token_to_buy == False:
            print("Transaction cannot be sent because trading pair between " + token_to_spend_symbol + " and " +
                  token_to_buy_symbol + " doesn't exist")
            ending()

    elif swap_method_chosen == "3":
        if exist_pair_token_to_spend_token_to_buy == True:
            amount_token_to_buy_before_tx = web3.eth.get_balance(config.sender_address)
            tx = swapExactTokensForNative(dex_chosen["Dex"].values[0],token_to_spend_address,
                                         token_to_buy_address,config.sender_address,
                                        amount_token_to_spend,gas_price_final_gwei , token_to_spend_decimals)
            waitForTxResponse(tx)

            check_balance = False
            while check_balance == False:
                amount_token_to_buy_after_tx = web3.eth.get_balance(config.sender_address)
                if (amount_token_to_buy_after_tx - amount_token_to_buy_before_tx) != 0:
                    amount_token_to_buy_after_tx = web3.eth.get_balance(config.sender_address)
                    print(f"Timestamp {datetime.datetime.now()} - Balance updated")
                    check_balance = True

            amount_token_to_buy_received = amount_token_to_buy_after_tx - amount_token_to_buy_before_tx

            if stop_loss_set == True or take_profit_set == True:
                if tx_status == "sent":
                    token_to_buy_approval = checkApproval(contract_token_to_buy, token_to_buy_symbol, router_address
                                                          , config.sender_address)
                    if token_to_buy_approval == False:
                        tx = approve(contract_token_to_buy, token_to_buy_symbol, router_address
                                     , config.sender_address)
                        waitForTxResponse(tx)
                    activateStopLossAndTakeProfit()
                else:
                    print("Stop loss / Take profit not activated because transaction is not sent")
                    ending()

        elif exist_pair_token_to_spend_token_to_buy == False:
            print("Transaction cannot be sent because trading pair between " + token_to_spend_symbol + " and " +
                  token_to_buy_symbol + " doesn't exist")
            ending()

#9 Ending
def ending():
    if exist_pair_token_to_spend_token_to_buy == True:
        # cas 1 classique
        print("Type : ")
        print(" - 'same' if you want to send the same transaction ")
        print(" - 'restart' if you want to restart")
        print(" - 'quit' if you want to quit")
        next_move = input("Type your choice : ")
        if next_move.lower() == "same":
            print("Sending same transaction...")
            sendTx()
        elif next_move.lower() == "restart":
            print("Reloading script ...")
            main()
        elif next_move.lower() == "quit":
            print("")
            print(
                "End of the script, send donations if you feel like it : 0xf444955E4dC892198E8a733ffCf08aaA13Bea096 :) ")
            exit()

    elif exist_pair_token_to_spend_token_to_buy == False:
        # cas 2 pair inexistante
        print("Type : ")
        print(" - 'restart' if you want to restart")
        print(" - 'quit' if you want to quit")
        next_move = input("Type your choice : ")
        if next_move.lower() == "restart":
            print("Reloading script ...")
            main()
        elif next_move.lower() == "quit":
            print("")
            print(
                "End of the script, send donations if you feel like it : 0xf444955E4dC892198E8a733ffCf08aaA13Bea096 :) ")
            exit()


def main():
    choice_dex()
    gasPriceChoice()
    choiceSwapMethod()
    setTokenToSpendParameters()
    choiceScanLiquidityAdded()
    choiceStopPrice()
    choiceAmountToSpend()
    setStopLoss()
    setTakeProfit()
    setTokenToBuyParameters()
    setStopPrice()
    checkExistingPairs()
    scanLiquidity()
    getTokenPrices()
    stopPrice()
    tradePreview()
    sendTx()
    ending()

main()