from config import Config
from secret_sdk.client.lcd import LCDClient
from secret_sdk.exceptions import LCDResponseError
from secret_sdk.key.mnemonic import MnemonicKey
from secret_sdk.client.localsecret import LocalSecret, main_net_chain_id
from secret_sdk.core.coins import Coins
from secret_sdk.client.lcd.wallet import Wallet
from secret_sdk.core.broadcast import SyncTxBroadcastResult
from secret_sdk.core.tx import TxInfo
from shade import msgBuyScrt, msgSellScrt
from colorama import Fore, Back
import json
from typing import Tuple, Dict
import time

def querySnip20Balance(address, viewing_key):
    return {'balance': {'address': address, 'key': viewing_key}}
if __name__ == "__main__":
    cfg = Config.load_config()
    lcd = cfg.get_value('blockchain.secret.network.lcd')
    chain_id = cfg.get_value('blockchain.secret.network.chain_id')
    mnemonic = cfg.get_value('blockchain.secret.network.mnemonic')
    sscrt_address = cfg.get_value('blockchain.secret.network.sscrt_address')
    susdc_address = cfg.get_value('blockchain.secret.network.susdc_address')
    sscrt_viewing_key = cfg.get_value('blockchain.secret.network.sscrt_viewing_key')
    susdc_viewing_key = cfg.get_value('blockchain.secret.network.susdc_viewing_key')
    mk = MnemonicKey(mnemonic)
    secret = LCDClient(lcd, chain_id)
    node_info = secret.tendermint.node_info()
    node_ver = node_info.get('application_version', {}).get('version', 'Unknown')
    cosmos_ver = node_info.get('application_version', {}).get('cosmos_sdk_version', 'Unknown')
    wallet: Wallet = secret.wallet(mk)
    sent_funds = Coins('10000000uscrt')
    handle_msg = {'deposit': {}}
    tx_rc = wallet.execute_tx(sscrt_address, handle_msg, transfer_amount=sent_funds)
    print(tx_rc)
    time.sleep(15)
    txinfo = secret.tx.tx_info(tx_rc.txhash)
    print(f'{txinfo.code} - {json.dumps(txinfo.rawlog, indent=4)}')
    wallet_balance: Tuple = secret.bank.balance(wallet.key.acc_address)
    coin: Coins = wallet_balance[0]
    print(wallet.lcd.wasm.contract_query(sscrt_address, querySnip20Balance(wallet.key.acc_address, sscrt_viewing_key)))
    print(wallet.lcd.wasm.contract_query(susdc_address, querySnip20Balance(wallet.key.acc_address, susdc_viewing_key)))
    print(f'{Back.WHITE}{Fore.BLACK}Node:{Back.RESET}{Fore.RESET}\n{node_ver}:{cosmos_ver}')
    print(f'{Back.WHITE}{Fore.BLACK}Wallet:{Back.RESET}{Fore.RESET}{wallet.key.acc_address}')
    print(f'{Back.WHITE}{Fore.BLACK}Wallet:{Back.RESET}{Fore.RESET}{coin}')
    tx_execute: SyncTxBroadcastResult = wallet.create_and_broadcast_tx(
        [msgSellScrt(wallet.key.acc_address, secret.encrypt_utils, "10000000")],
        gas="3500000",
    )
    txhash = tx_execute.txhash
    print(f'Tx Code:{tx_execute.code} | Hash:{txhash}')
    time.sleep(5)
    txinfo: TxInfo = secret.tx.tx_info(txhash)
    print(f'{txinfo.code} - {json.dumps(txinfo.rawlog, indent=4)}')
    tx_execute = wallet.create_and_broadcast_tx(
        [msgBuyScrt(wallet.key.acc_address, secret.encrypt_utils, "400000")],
        gas="3500000",
    )
    txhash = tx_execute.txhash
    print(f'Tx Code:{tx_execute.code} | Hash:{txhash}')
    time.sleep(5)
    txinfo: TxInfo = secret.tx.get_tx(txhash)
    print(txinfo)