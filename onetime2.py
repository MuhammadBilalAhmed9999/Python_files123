import sqlite3
import random
from config import Config  # Import Config from your config.py

# Use the DATABASE path from the Config class
DATABASE = Config.DATABASE

# Sample Pakistani names
employee_names = [
    "Ahmed Ali", "Sara Khan", "Usman Malik", "Ayesha Iqbal", "Bilal Shah",
    "Sana Tariq", "Omar Hassan", "Fatima Raza", "Ali Akbar", "Hassan Ali",
    "Nadia Shah", "Adeel Khan", "Zainab Bhatti", "Asim Farooq", "Iqra Gul",
    "Fahad Raza", "Mehwish Ali", "Tariq Jameel", "Sadaf Naeem", "Junaid Aslam",
    "Rimsha Khan", "Hassan Shahzad", "Ali Raza", "Saira Ahmed", "Kashan Ali",
    "Imran Anwar", "Shiza Ashraf", "Waleed Baig", "Sabeen Iqbal", "Owais Khan",
    "Shazia Nawaz", "Adnan Rasheed", "Muneeb Shah", "Amina Sadiq", "Furqan Farid",
    "Sania Malik", "Hamza Iqbal", "Mahnoor Shah", "Yasir Ali", "Sadiya Qureshi",
    "Ahmad Riaz", "Noreen Khan", "Maliha Javed", "Salman Tariq", "Arshad Ali",
    "Komal Mehmood", "Mujtaba Ali", "Zubair Shah", "Raza Ali", "Ayesha Malik",
    "Asma Akram", "Hassan Shams", "Kiran Azhar", "Umer Gul", "Hira Raza",
    "Bilal Iqbal", "Faizan Javed", "Sumaira Jamil", "Sufyan Shah", "Areeba Bashir",
    "Nashit Bukhari", "Rafay Ali", "Sana Shaikh", "Jamil Hassan", "Irfan Naseem",
    "Kiran Tariq", "Farhan Saleem", "Hassan Ali", "Mariam Baig", "Taimoor Anwar",
    "Zain Shams", "Kashifa Usman", "Arslan Jamil", "Adeel Tariq", "Maham Javed",
    "Nashit Mehmood", "Fatima Noor", "Bilal Mehmood", "Uzma Tariq", "Farah Nadeem",
    "Hassan Zafar", "Afsheen Arif", "Alina Sadiq", "Asad Rashid", "Kiran Shabbir",
    "Sohail Jameel", "Nida Nasir", "Ahmed Usman", "Dania Faisal", "Bisma Kausar",
    "Hassan Nawaz", "Anum Sohail", "Bilal Ahmed", "Ayesha Batool", "Faisal Usman",
    "Hassan Nasir", "Samiya Raza", "Musa Zubair", "Amna Aziz", "Adeel Khan",
    "Shan Ali", "Bushra Farooq", "Omer Zubair", "Rabia Kamran", "Areeba Sadiq",
    "Fahad Khan", "Khan Bilal", "Faiza Raza", "Osman Nasir", "Arfa Jamil",
    "Sobia Shah", "Aqsa Khan", "Muneeb Malik", "Fawad Zubair", "Mehwish Baig",
    "Ansa Yousuf", "Khurram Bukhari", "Yasmin Afzal", "Umer Shahzad", "Faizan Shah",
    "Saira Shabbir", "Nashit Malik", "Ubaid Tariq", "Umar Riaz", "Farhan Mehmood",
    "Aisha Naseem", "Isha Tariq", "Imran Jamil", "Ahmad Baig", "Mariam Usman",
    "Ali Gul", "Sana Bukhari", "Hassan Shams", "Nabeela Mehmood", "Mahreen Shah",
    "Imran Ali", "Amna Qureshi", "Shahzaib Bukhari", "Sadaf Jameel", "Fatima Yousuf",
    "Asim Khan", "Sarmad Malik", "Mariam Khokhar", "Dua Hasan", "Bilal Zafar"
]


def update_employee_names(cursor):
    # Fetch Employee IDs
    cursor.execute("SELECT EmployeeID FROM Employees")
    employee_ids = cursor.fetchall()

    # Randomly update names
    for employee_id in employee_ids:
        name = random.choice(employee_names)
        cursor.execute("UPDATE Employees SET FullName = ? WHERE EmployeeID = ?", (name, employee_id[0]))

def main():
    print("Updating employee names to Pakistani names...")

    # Connect to the database using the path from Config
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Update employee names
    update_employee_names(cursor)

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    print("Employee names updated successfully!")

if __name__ == '__main__':
    main()
