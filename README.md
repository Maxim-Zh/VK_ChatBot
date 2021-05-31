# VK_ChatBot
My first ChatBot based on VK API
This bot uses long polling technology that allows the receiving of information about new events with the help of "long requests". 
The server receives the request but it doesn't immediately send the answer but rather when some event will happen (for example, receiving a new incoming message), 
or waiting period is over. By using this approach, you can instantly display in your app the most important events.
Bot recieved messages and send back invitation ticket with uniqe avatar based on user's email address.
