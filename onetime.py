import sqlite3
import random
from datetime import datetime, timedelta
from config import Config

DB = Config.DATABASE
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def table_count(name):
    return cur.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]

def random_date(days=60):
    d = datetime.now() + timedelta(days=random.randint(1, days))
    return d.strftime("%Y-%m-%d"), d.strftime("%Y-%m-%d %H:%M")

print("📦 EXTENDING DATABASE DATA...\n")

# -------------------------------------------------
# ROUTES → ADD 30 MORE
# -------------------------------------------------
existing_routes = table_count("Routes")
for i in range(30):
    cur.execute("""
        INSERT INTO Routes (RouteName, DistanceKm, EstimatedMinutes)
        VALUES (?,?,?)
    """, (
        f"Extended Route {existing_routes + i + 1}",
        random.randint(100, 900),
        random.randint(120, 1200)
    ))
print("✓ Added 30 Routes")

# -------------------------------------------------
# EMPLOYEES → ADD 80 MORE
# -------------------------------------------------
existing_employees = table_count("Employees")
for i in range(80):
    cur.execute("""
        INSERT INTO Employees
        (FullName, CNIC, Phone, Address, JobID, ShiftID, Status)
        VALUES (?,?,?,?,?,?,?)
    """, (
        f"Extra Employee {existing_employees + i + 1}",
        f"35202-{random.randint(1000000,9999999)}-1",
        f"03{random.randint(100000000,999999999)}",
        "Extension City",
        random.randint(1, 4),
        random.randint(1, 3),
        "Active"
    ))
print("✓ Added 80 Employees")

# -------------------------------------------------
# BUSES → ADD 25 MORE
# -------------------------------------------------
existing_buses = table_count("Buses")
for i in range(25):
    cur.execute("""
        INSERT INTO Buses
        (BusNumber, Model, Capacity, RouteID, CategoryID, Status)
        VALUES (?,?,?,?,?,?)
    """, (
        f"EXT-BUS-{existing_buses + i + 1}",
        random.choice(["Volvo", "Daewoo", "Hino"]),
        random.randint(30, 50),
        random.randint(1, table_count("Routes")),
        random.randint(1, 4),
        "Active"
    ))
print("✓ Added 25 Buses")

# -------------------------------------------------
# TRIPS → ADD 100 MORE
# -------------------------------------------------
existing_trips = table_count("Trips")
for i in range(100):
    trip_date, trip_dt = random_date()

    cur.execute("""
        INSERT INTO Trips
        (RouteID, BusID, DriverID, DepartureDateTime,
         ArrivalDateTime, Status, TripDate)
        VALUES (?,?,?,?,?,?,?)
    """, (
        random.randint(1, table_count("Routes")),
        random.randint(1, table_count("Buses")),
        random.randint(1, table_count("Employees")),
        trip_dt,
        (datetime.strptime(trip_dt, "%Y-%m-%d %H:%M") +
         timedelta(hours=random.randint(3, 8))).strftime("%Y-%m-%d %H:%M"),
        "Scheduled",
        trip_date
    ))
print("✓ Added 100 Trips")

# -------------------------------------------------
# TICKETS + SEATS → ADD 200 MORE
# -------------------------------------------------
existing_tickets = table_count("Tickets")
for i in range(200):
    cur.execute("""
        INSERT INTO Tickets
        (TripID, FromStation, ToStation, Fare, PaymentMethod)
        VALUES (?,?,?,?,?)
    """, (
        random.randint(1, table_count("Trips")),
        "City A",
        "City B",
        random.randint(900, 3500),
        random.choice(["Cash", "Card"])
    ))
    ticket_id = cur.lastrowid

    seat = f"{random.choice('ABCD')}{random.randint(1,20)}"
    cur.execute("""
        INSERT INTO TicketSeats (TicketID, SeatLabel)
        VALUES (?,?)
    """, (ticket_id, seat))
print("✓ Added 200 Tickets + Seats")

# -------------------------------------------------
# SALARIES → ADD 120 MORE
# -------------------------------------------------
existing_salaries = table_count("Salaries")
for i in range(120):
    basic = random.randint(30000, 90000)
    allow = random.randint(3000, 15000)
    ded = random.randint(0, 6000)

    cur.execute("""
        INSERT INTO Salaries
        (EmployeeID, Month, Year, BasicPay, Allowances, Deductions, NetSalary)
        VALUES (?,?,?,?,?,?,?)
    """, (
        random.randint(1, table_count("Employees")),
        random.randint(1, 12),
        2025,
        basic,
        allow,
        ded,
        basic + allow - ded
    ))
print("✓ Added 120 Salaries")

# -------------------------------------------------
conn.commit()
conn.close()
print("\n✅ DATABASE EXTENSION COMPLETE — EXISTING DATA PRESERVED")
