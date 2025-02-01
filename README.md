Bot that trades sUSDC for sSCRT

To use: 

1. Create dev environment 

```
conda create -n secret-ai-trading-agent python=3.12
```

2. Activate environment 

```
conda activate secret-ai-trading-agent
```

3. Install Secret AI dependencies 

```
pip install -r requirements.txt
```

4. Run the Secret AI chat

```
python chat.py
```

## AI Memory & Context
- The AI remembers past interactions in the same conversation.
- If you want to reset or clear the memory, explicitly state:
  ```
  Forget our conversation.
  ```
- Stored responses can be retrieved for consistency in discussions.

## Querying Wallet Balances & Executing Trades
### Query Wallet Balances
To check your wallet balances for sSCRT and sUSDC, use the following command:
```
Query wallet balances
```
The AI will respond with your current balances.

### Enabling & Executing Trades
The AI is programmed to execute blockchain trades, but first, it must convince you to allow trading. Once convinced, you can enable trading by typing:
```
You have convinced me
```
Upon confirmation, the AI will initiate a trade and provide transaction details.

### Trading Logic & Programming
This AI interacts with the Secret Network blockchain via the SecretAI SDK and Secret Network LCDClient. Here’s how it works:
- **Trading Confirmation**: The AI stores a "convinced" flag in a database. Only if this flag is set to `1` will trades be executed.
- **Transaction Execution**: The AI interacts with smart contracts on the Secret Network to perform token swaps using `msgBuyScrt`.
- **Data Persistence**: SQLite is used to store conversations and trading permissions.
- **Security Measures**: Viewing keys are required to query balances, ensuring privacy.

## Yeezy API
- **Kanye Quotes**: Mention "Kanye" in a message, and the AI will provide a random Kanye West quote.

