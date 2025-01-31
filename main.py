import time
from secret_sdk.core.wasm import MsgExecuteContract
from secret_sdk.client.lcd import LCDClient
from secret_sdk.key.mnemonic import MnemonicKey
from secret_sdk.client.lcd.wallet import Wallet
from secret_sdk.core.broadcast import SyncTxBroadcastResult
from secret_sdk.core.tx import TxInfo
from typing import Dict
from shade import msgBuyScrt

# Hardcoded values from config.yaml
LCD_URL = "https://lcd.mainnet.secretsaturn.net"
CHAIN_ID = "secret-4"
MNEMONIC = ""
SSCRT_ADDRESS = "secret1k0jntykt7e4g3y88ltc60czgjuqdy4c9e8fzek"
SUSDC_ADDRESS = "secret1vkq022x4q8t8kx9de3r84u669l65xnwf2lg3e6"
SSCRT_VIEWING_KEY = "e6bcf58eb88fc42f421b060f0f313e9f2b2779d4314f77fac1c813bbf239ae50"
SUSDC_VIEWING_KEY = "52c233dc18acd133a2743e2afe7e0006fe952dd0329fbdfa2ccaf32e3d026478"
FEES = "3500000"
GAS_LIMIT = 900_000

# Initialize Secret Network client and wallet
mk = MnemonicKey(MNEMONIC)
secret = LCDClient(LCD_URL, CHAIN_ID)
wallet: Wallet = secret.wallet(mk)

def _msgQuerySnip20Balance(address: str, viewing_key: str) -> Dict[str, Dict[str, str]]:
    """Construct a query for SNIP-20 token balance."""
    return {'balance': {'address': address, 'key': viewing_key}}

def _get_balance_sSCRT() -> Dict:  # {'balance': {'amount': 'x in uscrt'}}
    return wallet.lcd.wasm.contract_query(SSCRT_ADDRESS, _msgQuerySnip20Balance(wallet.key.acc_address, SSCRT_VIEWING_KEY))

def _get_balance_sUSDC() -> Dict:  # {'balance': {'amount': 'x in usdc'}}
    return wallet.lcd.wasm.contract_query(SUSDC_ADDRESS, _msgQuerySnip20Balance(wallet.key.acc_address, SUSDC_VIEWING_KEY))

def execute_buy_transaction(amount: str) -> Dict:
    """Executes a buy transaction for SCRT using sUSDC."""
    try:
        tx_execute = wallet.create_and_broadcast_tx(
            [msgBuyScrt(wallet.key.acc_address, secret.encrypt_utils, amount)],
            gas=FEES,
        )
        txhash = tx_execute.txhash
        print(f'Tx Code:{tx_execute.code} | Hash:{txhash}')
        
        time.sleep(5)  # Wait for transaction confirmation

        txinfo: TxInfo = secret.tx.get_tx(txhash)
        return txinfo.to_data()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Query and print balances
    balance_sSCRT = _get_balance_sSCRT()
    print("sSCRT Balance:", balance_sSCRT)

    balance_sUSDC = _get_balance_sUSDC()
    print("sUSDC Balance:", balance_sUSDC)


