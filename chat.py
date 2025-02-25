from main import TradingAgent

agent = TradingAgent()
user_id = "seanrad"  # Choose a unique user ID

print("💬 $SCRT Trading AI - Start chatting! (Type 'exit' to quit)")

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Goodbye!")
        break
    response = agent.chat(user_id, user_input)
    print("AI:", response)
