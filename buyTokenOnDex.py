import pandas as pd
from web3 import Web3
import config
import time

def choice_dex():

    df = pd.read_excel("dex_parameters.xlsx")
    liste_dex = df["Dex"].values

    print("Choisissez un DEX parmi :", liste_dex)
    choiceDex = input("Entrez votre choix ici : ")

    validation = None
    for j in range(0, len(liste_dex)):
        if choiceDex == liste_dex[j]:
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

        print("Vérification de la connexion à la blockchain ", DexChosen["Blockchain"].values[0], " : ", web3.isConnected())
        print("Le token natif de la blockchain est ", nameNativeContract, "(", symbolNativeContract,
              ") son addresse est : ", nativeTokenAddress)

        contract = web3.eth.contract(
            address=web3.toChecksumAddress(DexChosen["RouterAddress"].values[0]),
            abi=DexChosen["RouterAddressAbi"].values[0])

        print("Vous avez choisi le DEX ", DexChosen["Dex"].values[0])
    else:
        print("La valeur entrée est incorrecte. Veuillez saisir un DEX qui figure dans la liste", liste_dex )
        print("")
        choice_dex()


def param_tx():

    def gasPriceChoice():
        global choiceGasPrice
        global finalGasPrice
        global gasPrice
        global gasPriceGwei
        choiceGasPrice = None
        print("Le gas price actuel est de :",  web3.fromWei(web3.eth._gas_price(),"gwei") ,"gwei sur la blockchain",
            DexChosen["Blockchain"].values[0])

        choiceGasPrice = input("Saisissez le multiplicateur à appliquer au gas price pour votre transaction : ")
        gasPrice = web3.eth._gas_price()
        gasPriceGwei = web3.fromWei(gasPrice, "gwei")
        finalGasPrice = gasPriceGwei * int(choiceGasPrice)
        print("Le gas price de votre transaction sera de ", finalGasPrice, "gwei.")

    def setAmountTokenToSpend():
        global amountTokenToSpend
        print("Vous détenez ", humanReadableBalance, " ", symbolNativeContract, " dans votre wallet")
        print("Combien de ", nameNativeContract, "(", symbolNativeContract, ") voulez-vous dépenser ?")
        amountTokenToSpend = input("Saisissez le montant ici : ")
        if float(amountTokenToSpend) >= float(humanReadableBalance):
            print("La valeur entrée doit être inférieure à ", humanReadableBalance )
            print("")
            setAmountTokenToSpend()

    def setSlippage():
        slippage = float(input("Quel est le slippage souhaité (entre 0.1 et 49): "))
        if 0.1 <= slippage <= 49:
            global slippage_percent
            slippage_percent = slippage / 100
        else:
            print("Le slippage doit être compris entre 0.1 et 49.")
            print("")
            setSlippage()

    ### Appelez les fonction paramètres
    gasPriceChoice()
    setAmountTokenToSpend()
    setSlippage()

    global tokenToBuy
    tokenToBuy = web3.toChecksumAddress(input("Entrez l'addresse du token que vous souhaitez acheter: "))
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
    finalGasPrice = gasPriceGwei * int(choiceGasPrice)
    print("UPDATE : Le gas price de votre transaction sera de : ", finalGasPrice)

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
    print("Vous recevrez ", humanReadable_buyamount, " tokens (", minimumTokenReceived, " au minimum) pour",
          amountTokenToSpend, " ", nameNativeContract, "(", symbolNativeContract, ") dépensés")

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
            'gas': 26000000,
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
    print(web3.toHex(tx_token))
    beginning_tx = time.time()
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_token)
    ending_tx = time.time()
    temps_tx = ending_tx - beginning_tx
    print("Temps pour exécuter la transaction : ", temps_tx, "secondes.")
    print("Statut de la tx : ", tx_receipt.status)
    again = input("Envoyer la même transaction ? Ecrivez ok si oui : ")
    if again.lower() == "ok":
        send_tx()
    else:
        print("")
        print("Fin du programme merci d'avoir utiliser, vous pouvez faire un don à l'adresse : 0xd4d1D355B967c6b67F29Fa68F7A3CCcaeF82E90c :) ")
        exit()

def main():
    choice_dex()
    param_tx()
    send_tx()
main()

