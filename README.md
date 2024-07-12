# NLP-Foodchatbot
Build a chatbot for food orders online delivery using Google's Dialogflow ES. This bot supports two options,

1. New Order
2. Track Order
3. Cancel Order

New Order: Sample Conversation

Bot: How can I help you? You can say things like (1) New Order (2) Track Order
User: New Order
Bot: What would you like to have? You can say things like 2 pizzas, one vada pav.
     Only order from this list: Vada Pav, Pav Bhaji, Mango Lassi, Pizza, Rava Dosa, Masala Dosa, Samosa

User: I would like to have 2 Rava Dosa and one plate of samosa

Bot: Added 2 Rava Dosa and 1 Samosa. Anything else?

User: Oh yes, add one mango lassi, please

Bot: Sure. Now we have 2 Rava Dosa, 1 Samosa and 1 Mango Lassi. Anything else?

User: Well, you know my cholesterol came high so let's remove Samosa

Bot: Sure. Now we have 2 Rava Dosa, and 1 Mango Lassi. Anything else?

User: Nope. That's it

Bot: Awesome. Your order is placed. Order id # 45. Your total bill is 19$ which you can pay at the time of delivery!

Track Order: Sample Conversation

User: Track Order
Bot: What is your order id?
User: 45
Bot: Order # 45, is in transit
User: How about 41
Bot: Order # 41 is delivered

Cancel Order: Sample Conversation (Cancel order only works when the order status is in 'in progress')

User: Cancel my order

Bot: Please enter your order ID

User: 42

Bot: Your order #42 has been successfully canceled



User: Cancel Order

Bot: What is your order id?

User: 45

Bot: Order # 45, is in transit. It cannot be canceled.


**To start fastapi backend server**
Run this command: uvicorn main:app --reload


**ngrok for https tunneling**
1. To install ngrok, go to https://ngrok.com/download and install ngrok version that is suitable for your OS
2. Extract the zip file and place ngrok.exe in a folder.
3. Open windows command prompt, go to that folder and run this command: ngrok http 8000
NOTE: ngrok can timeout. you need to restart the session if you see session expired message.
