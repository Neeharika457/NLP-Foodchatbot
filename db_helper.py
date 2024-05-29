import mysql.connector
from mysql.connector import cursor
# from fastapi.responses import JSONResponse

global cnx

cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="pandeyji_eatery"
)


#To save the order to DB
### Step 1: Get the order ID --> get_next_order_id
### Step 2: Get the item ID. For pizza the item ID is 3. Item id is in food_items table
### Step 3: Get the prize of the ordered items.
### Step 4: Save this in orders table (order_id, item_id, quantity, price)

# Function to get the next available order_id
def get_next_order_id():
    cursor = cnx.cursor()

    # Executing the SQL query to get the next available order_id
    query = "SELECT MAX(order_id) FROM orders"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]

    # Closing the cursor
    cursor.close()

    # Returning the next available order_id
    if result is None:
        return 1
    else:
        return result + 1 #Let us say, a new order is started. Now, I need to give order_id to save the order. max Order_id + 1 is my new order_id

# Function to call the MySQL stored procedure and insert an order item
def insert_order_item(food_item, quantity, order_id):
    try:
        cursor = cnx.cursor()

        # Calling the stored procedure, since there is a Function in DB (Next to stored procedure) to add each item to the DB
        cursor.callproc('insert_order_item', (food_item, quantity, order_id))

        # Committing the changes
        cnx.commit()

        # Closing the cursor
        cursor.close()

        print("Order item inserted successfully!")

        return 1

    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")

        # Rollback changes if necessary
        cnx.rollback()

        return -1

    except Exception as e:
        print(f"An error occurred: {e}")
        # Rollback changes if necessary
        cnx.rollback()

        return -1

#Get the total price of an order
def get_total_order_price(order_id):
    cursor = cnx.cursor()

    # Executing the SQL query to get the total order price (get_total_order_price is a user defined function present in SQL DB)
    query = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]

    # Closing the cursor
    cursor.close()

    return result

# Function to insert a record into the order_tracking table. Since the new order is places, we have to track the order as well. So, insert in order_tracking table.
def insert_order_tracking(order_id, status):
    cursor = cnx.cursor()

    # Inserting the record into the order_tracking table
    insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    cursor.execute(insert_query, (order_id, status))

    # Committing the changes
    cnx.commit()

    # Closing the cursor
    cursor.close()

# Function to fetch the order status from the order_tracking table
def get_order_status(order_id):
    cursor = cnx.cursor()

    # Executing the SQL query to fetch the order status
    query = f"SELECT status FROM order_tracking WHERE order_id = {order_id}"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()

    # Closing the cursor
    cursor.close()

    # Returning the order status
    if result:
        return result[0]
    else:
        return None



# #Here I am trying to delete the oder ID entirely from orders, order_tracking tables
# def cancel_the_order(order_id):
#     cursor = cnx.cursor()
#     try:
#         # Check if the order exists
#         cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
#         order = cursor.fetchone()
#
#         if not order:
#             return False  # Order does not exist
#
#         # Delete the order from the orders table
#         cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
#
#         # Delete the order from the order_tracking table
#         cursor.execute("DELETE FROM order_tracking WHERE order_id = %s", (order_id,))
#
#         cnx.commit()
#         return True  # Order successfully canceled
#
#     except Exception as e:
#         print(f"Error: {e}")
#         cnx.rollback()
#         return False
#
#     finally:
#         cursor.close()


#Here I am just changing the status to 'Canceled' instead of deleting the orderID from the tables
def cancel_the_order(order_id):
    try:
        cursor = cnx.cursor()
        # Go to the column 'status' in 'order_tracking' table and you set it to 'canceled'
        cursor.execute("UPDATE order_tracking SET status = 'canceled' WHERE order_id = %s", (order_id,))
        cnx.commit()

        # Delete the order from the orders table
        # cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
        return cursor.rowcount > 0  # Returns True if the order was successfully updated, otherwise False
    except Exception as e:
        print(f"Error while canceling order {order_id}: {str(e)}")
        return False
    finally:
        cursor.close()



def order_exists(order_id):
    cursor = cnx.cursor()
    try:
        cursor.execute("SELECT 1 FROM orders WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()  # Fetch one row from the result set
        return result is not None  # Check if any row exists
        # Consume all remaining results and close the cursor
    finally:
        for _ in cursor:
            pass
        cursor.close()

