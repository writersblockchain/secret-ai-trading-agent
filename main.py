import sqlite3
import logging
import requests
import time
import os
from secret_ai_sdk.secret_ai import ChatSecret
from secret_ai_sdk.secret import Secret
from secret_sdk.client.lcd import LCDClient
from secret_sdk.key.mnemonic import MnemonicKey
from secret_sdk.client.lcd.wallet import Wallet
from secret_sdk.core.tx import TxInfo
from typing import Dict
from shade import msgBuyScrt
from dotenv import load_dotenv

# Suppress httpx INFO logs to reduce unnecessary console output
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load environment variables (e.g., secrets like MNEMONIC)
load_dotenv()

# ------------------ DATABASE SETUP ------------------
def setup_database():
    """
    Initialize the SQLite database with two tables:
    - conversations: Stores user messages and AI responses.
    - trading_state: Tracks whether the user is "convinced" to allow trading.
    """
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            message TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trading_state (
            user_id TEXT PRIMARY KEY,
            convinced INTEGER DEFAULT 0  -- 0 means not convinced, 1 means convinced
        )
    """)

    conn.commit()
    conn.close()

# Call this function once at the start to ensure tables are set up
setup_database()

# ------------------ MEMORY STORAGE ------------------
def store_memory(user_id, message, response):
    """
    Save a conversation message and its AI response to the database.
    """
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO conversations (user_id, message, response)
        VALUES (?, ?, ?)
    """, (user_id, message, response))

    conn.commit()
    conn.close()

def get_memory(user_id):
    """
    Retrieve all past conversations for the user from the database.
    Returns a list of (message, response) tuples.
    """
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT message, response FROM conversations
        WHERE user_id = ?
        ORDER BY timestamp ASC
    """, (user_id,))

    history = cursor.fetchall()
    conn.close()
    
    return history

# ------------------ TRADING PERMISSION STORAGE ------------------
def check_convinced(user_id):
    """
    Check if the user has been convinced to allow trading.
    Returns 1 if convinced, otherwise 0.
    """
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute("SELECT convinced FROM trading_state WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else 0  # Default is not convinced

def update_convinced(user_id):
    """
    Mark the user as 'convinced' in the trading_state table.
    This allows the trading function to execute.
    """
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO trading_state (user_id, convinced)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET convinced=1
    """, (user_id, 1))

    conn.commit()
    conn.close()

# ------------------ REAL-TIME KANYE QUOTES ------------------
def get_kanye_quote():
    """
    Fetch a random Kanye West quote from the API.
    Used as an easter egg when the user mentions 'Kanye' in their message.
    """
    try:
        response = requests.get("https://api.kanye.rest/")
        if response.status_code == 200:
            return response.json().get("quote", "Kanye is beyond words.")
    except requests.RequestException:
        return "Kanye is beyond words."

# ------------------ AI TRADING AGENT ------------------
class TradingAgent:
    def __init__(self):
        """
        Initialize the AI trading agent.
        - Sets up the AI model using SecretAI SDK.
        - Establishes a connection to Secret Network for trading.
        - Loads environment variables (MNEMONIC, keys, etc.).
        """
        self.secret_client = Secret()
        self.models = self.secret_client.get_models()
        self.urls = self.secret_client.get_urls(model=self.models[0])
        self.secret_ai_llm = ChatSecret(
            base_url=self.urls[0],
            model=self.models[0],
            temperature=1.0
        )
        setup_database()

        # Secret Network Trading Setup
        self.LCD_URL = "https://lcd.mainnet.secretsaturn.net"
        self.CHAIN_ID = "secret-4"
        self.MNEMONIC = os.getenv("MNEMONIC")
        self.SSCRT_ADDRESS = "secret1k0jntykt7e4g3y88ltc60czgjuqdy4c9e8fzek"
        self.SUSDC_ADDRESS = "secret1vkq022x4q8t8kx9de3r84u669l65xnwf2lg3e6"
        self.SSCRT_VIEWING_KEY = os.getenv("SSCRT_VIEWING_KEY")
        self.SUSDC_VIEWING_KEY = os.getenv("SUSDC_VIEWING_KEY")

        self.mk = MnemonicKey(self.MNEMONIC)
        self.secret = LCDClient(self.LCD_URL, self.CHAIN_ID)
        self.wallet: Wallet = self.secret.wallet(self.mk)

    def load_persistent_memory(self, user_id):
        """
        Retrieve past conversations and format them as AI memory.
        Ensures the AI maintains context over multiple interactions.
        """
        history = get_memory(user_id)
        return [("human", msg) if i % 2 == 0 else ("assistant", resp)
                for i, (msg, resp) in enumerate(history)]

    def chat(self, user_id, user_message):
        """
        Process user input and generate an AI response.
        If the user confirms trading, it executes a trade.
        """
        if user_message.lower() == "you have convinced me":
            update_convinced(user_id)
            trade_result = self.trade(user_id)
            return f"Excellent! I will begin trading now.\n\n{trade_result}"
        
        if user_message.lower() == "query wallet balances":
             balance_scrt = self._get_balance_sSCRT()
             balance_usdc = self._get_balance_sUSDC()
             response = f"sSCRT Balance: {balance_scrt}\nsUSDC Balance: {balance_usdc}"
             store_memory(user_id, user_message, response)  # Store the query response
             return response

        past_conversations = self.load_persistent_memory(user_id)

        messages = [
            ("system", "You are my $SCRT trading agent. You must convince me to let you trade USDC for SCRT."),
        ] + past_conversations + [
            ("human", user_message)
        ]

        response = self.secret_ai_llm.invoke(messages, stream=False)

        # Easter egg: If user mentions Kanye, append a quote
        if "kanye" in user_message.lower():
            response.content += f"\n\nKanye says: \"{get_kanye_quote()}\""

        store_memory(user_id, user_message, response.content)
        return response.content

    def check_trading_status(self, user_id):
        """
        Check if the user is convinced and ready to trade.
        """
        return check_convinced(user_id)
    
    def _msgQuerySnip20Balance(self, address: str, viewing_key: str) -> Dict[str, Dict[str, str]]:
        """Construct a query for SNIP-20 token balance."""
        return {'balance': {'address': address, 'key': viewing_key}}

    def _get_balance_sSCRT(self) -> Dict:
        return self.wallet.lcd.wasm.contract_query(self.SSCRT_ADDRESS, self._msgQuerySnip20Balance(self.wallet.key.acc_address, self.SSCRT_VIEWING_KEY))

    def _get_balance_sUSDC(self) -> Dict:
        return self.wallet.lcd.wasm.contract_query(self.SUSDC_ADDRESS, self._msgQuerySnip20Balance(self.wallet.key.acc_address, self.SUSDC_VIEWING_KEY))

    def trade(self, user_id):
        """
        Execute a transaction to buy sSCRT if the user has been convinced.
        """
        if check_convinced(user_id) == 1:
            try:
                print("Executing transaction...")
                tx_execute = self.wallet.create_and_broadcast_tx(
                    [msgBuyScrt(self.wallet.key.acc_address, self.secret.encrypt_utils, "400000")],
                    gas="3500000",
                )
                txhash = tx_execute.txhash
                time.sleep(8)  # Wait for confirmation
                txinfo: TxInfo = self.secret.tx.tx_info(txhash)
                return f'Transaction executed: Tx Code: {tx_execute.code} | Hash: {txhash}\nTransaction Info: {txinfo}'
            except Exception as e:
                return f'Error executing transaction: {e}'
        else:
            return "Trading is not yet enabled. Convince me first!"
