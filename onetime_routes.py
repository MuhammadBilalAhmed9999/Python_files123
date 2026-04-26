import sqlite3
import random
from config import Config  # Import Config from config.py

# Use the DATABASE path from Config
DATABASE = Config.DATABASE

# Sample Pakistani route names
route_names = [
    "Karachi to Lahore", "Islamabad to Rawalpindi", "Peshawar to Mardan",
    "Karachi to Quetta", "Lahore to Multan", "Faisalabad to Sargodha",
    "Sialkot to Gujranwala", "Lahore to Bahawalpur", "Karachi to Sukkur",
    "Islamabad to Abbottabad"
    # Add more routes as needed
]

def update_route_names(cursor):
    # Fetch Route IDs
    cursor.execute("SELECT RouteID FROM Routes")
    route_ids = cursor.fetchall()

    # Randomly update route names
    for route_id in route_ids:
        name = random.choice(route_names)
        cursor.execute("UPDATE Routes SET RouteName = ? WHERE RouteID = ?", (name, route_id[0]))

def main():
    print("Updating route names to Pakistani routes...")

    # Connect to the database using the path from Config
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Update route names
    update_route_names(cursor)

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    print("Route names updated successfully!")

if __name__ == '__main__':
    main()
