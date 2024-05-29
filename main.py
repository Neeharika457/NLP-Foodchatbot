from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

app = FastAPI()

# Backend code is written for the intents where fulfillment is enabled. Fulfillment option is enabled only for those which really need to hit the db.
# To clearly explain, welcome intent doesn't need fulfillment option enabled because 'hey' message doesn't need db. Dialogflow is enough
# If you press 'New order' also, no db needs to be hit based on the responses(because we show only menu which is in the Dialogflow) - no need to enable fulfillment here

# But to 'Add order', we need to store what the person is ordering to db - we need to enable fulfillment here
# Similarly, to track order we need order_id stored in db - we need to enable fulfillment here


inprogress_orders = {}  # new order has started ==> a new session_id is created, then the customer places his order. This is stored in inprogress_orders.


# Once the customer says his order is complete, then we will push his order into db.

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    # It is in the DiagonisticInfo in the dialogFlow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = generic_helper.extract_session_id(output_contexts[0]["name"])

    # if intent == '7.1. TrackMultipleOrder - context: ongoing-tracking':
    #     return track_order(parameters)
    # elif intent == '4. AddOrder - context: ongoing-order':
    #     return add_to_order(parameters)
    # elif intent == '5. RemoveOrder - context: ongoing-order':
    #     return remove_from_order(parameters)
    # elif intent == '6. CompleteOrder - context: ongoing-order':
    #     return complete_order(parameters)

    intent_handler_dict = {
        # Instead of all the elifs, dict looks cleaner and better way to call the respective functions
        '4. AddOrder - context: ongoing-order': add_to_order,
        '5. RemoveOrder - context: ongoing-order': remove_from_order,
        '6. CompleteOrder - context: ongoing-order': complete_order,
        '7.1. TrackMultipleOrder - context: ongoing-tracking': track_order,
        '8. CancelOrder': cancel_order,
        '3. NewOrder': new_order
    }

    return intent_handler_dict[intent](parameters, session_id)


def add_to_order(parameters: dict, session_id: str):
    food_items = parameters["FoodItem-AddOrder"]
    quantities = parameters['number']

    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry, I didn't get that. Please specify the quantities clearly."
    else:
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            for item, quantity in new_food_dict.items():
                if item in current_food_dict:
                    current_food_dict[item] += quantity
                else:
                    current_food_dict[item] = quantity
        else:
            inprogress_orders[session_id] = new_food_dict

        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else? If yes, please specify item name and quantity."

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def save_to_db(order: dict):
    next_order_id = db_helper.get_next_order_id()

    # Insert individual items along with quantity in orders table
    ### order_of_1_person = {"pizza":2, "biryani":1,"bhature":3}. Each item has to be inserted in to DB. So, a for loop
    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return -1

    # Now insert order tracking status
    db_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id


### Step 1: Locate session_id record
### Step 2: get the order/ values from the dict {"pizza":2, "biryani":1,"bhature":3}
### Step 3: remove the food items

def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
        })

    food_items = parameters["FoodItem-AddOrder"]
    quantities = parameters.get("number",
                                [1] * len(food_items))  # Default to removing one of each item if no quantity specified
    current_order = inprogress_orders[session_id]

    removed_items = []
    no_such_items = []
    # insufficient_quantity = []

    if isinstance(quantities, float):  # Convert to list if quantities is a float
        quantities = [quantities]

    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry, I didn't get that. Please specify the quantities clearly."

    for item, qty_to_remove in zip(food_items, quantities):
        if item not in current_order:
            no_such_items.append(item)
        else:
            if current_order[item] > qty_to_remove:
                current_order[item] -= qty_to_remove
                removed_items.append(f"{int(qty_to_remove)} {item}")
            elif current_order[item] == qty_to_remove:
                del current_order[item]
                removed_items.append(f"{qty_to_remove} {item}")
            else:
                removed_qty = min(current_order[item], qty_to_remove)
                current_order[item] -= removed_qty
                removed_qty = int(removed_qty)
                removed_items.append(f"{removed_qty} {item}")

                # insufficient_quantity.append((item, current_order[item]))

    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulfillment_text = f' Your current order does not have {",".join(no_such_items)}'

    # if insufficient_quantity:
    #     insufficient_str = ", ".join([f"{item} (only {qty} left)" for item, qty in insufficient_quantity])
    #     fulfillment_text += f'Insufficient quantity for {insufficient_str}. '

    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    # print(fulfillment_text)

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = f"Couldn't find your order. Please place your order again."
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)

        if order_id == -1:
            fulfillment_text = "Sorry I couldn't process your order due to some error." \
                               " Please place a new order again"

        else:

            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome. We have placed your order. " \
                               f"Here is your order id # {order_id}. " \
                               f"Your order total is {order_total} which you can pay at the time of delivery!"

        # When the order is placed, remove the order from inprogress dictionary (since the entire order is stored in DB and the order is complete)
        del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def track_order(parameters: dict, session_id: str):  ## parameters in Diagonistic Infor from dialog flow is a dictionary

    # To track the order, we need order ID. The order ID is in Diagonstic Info
    order_id = int(parameters['number'])
    order_status = db_helper.get_order_status(order_id)
    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"

    # Now, we have order ID. Now call the database and retrieve the order information.
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# @app.post("/cancel_order")
def cancel_order(parameters: dict, session_id: str):
    order_id = parameters.get('number')
    print(f"CancelOrder called with order_id: {order_id}")

    if not order_id:
        fulfillment_text = "Please enter a valid order ID."
        return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

    try:
        order_status = db_helper.get_order_status(order_id)
        print(f"Order status for order_id {order_id}: {order_status}")

        if not order_status:
            fulfillment_text = f"No order found with order id: {order_id}"
        elif order_status != 'in progress':
            fulfillment_text = f"Order {order_id} cannot be canceled as its status is '{order_status}'."
        else:
            cancel = db_helper.cancel_the_order(order_id)
            print(f"Cancel result for order_id {order_id}: {cancel}")
            if cancel:
                fulfillment_text = f"Order {order_id} has been successfully canceled."
            else:
                fulfillment_text = "Some backend error. Please try again."
    except Exception as e:
        print(f"Exception occurred while canceling order {order_id}: {str(e)}")
        fulfillment_text = "Some backend error. Please try again."

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

# this is the scenario
# User: new order
# Bot: Tell me
# User: 2 pizza
# Bot:  2 pizza. Do you need anything else
# User: New order
# Bot: Tell me
# User: 2 rava dosa
# Bot: Your order has 2 pizza, 2 rava dosa. Do you need anything else?

# Here after saying new order the cache has to be cleared. It has to be new order completely.
# Dialogflow has NewOrder intent.
# All I need is if user is saying new order without completing the previous order, delete his previous chat and begin a new order again
# The simple approach is deleting the session_id in inprogress_orders


def new_order(parameters: dict, session_id: str):
    # Clear the in-progress order for the session
    cleared_items = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
    if session_id in inprogress_orders:
        del inprogress_orders[session_id]

    # Prompt the user to start a new order
    fulfillment_text = f"Your previous order {cleared_items} has been cleared. Please tell me what you would like to order."

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

# # Mock of parameters and session_id for testing
# parameters = {
#     "FoodItem-AddOrder": ["pav bhaji", "mango lassi"],
#     "number": [1, 1]
# }
# session_id_1 = "example_session_id"
# number = 12345
# # print(type(order_id))
#
# # Mock order
# inprogress_orders[session_id_1] = {"pav bhaji": 2, "mango lassi": 1}
#
# # Test the function
# response = remove_from_order(parameters, session_id_1)
#
# # Mock parameters for testing
# parameters = {
#     "number": 12345
# }
#
# # Test the cancel_order function
# print(cancel_order(parameters, session_id_1))
