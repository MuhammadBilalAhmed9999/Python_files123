# app.py
import os
from flask import Flask, render_template, redirect, url_for, flash, request, current_app
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
#from werkzeug.security import check_password_hash
from config import Config, BUS_CATEGORY_LAYOUTS
from utils import get_db, query_db, has_permission, close_db
from models import User, load_user
from forms import LoginForm
from werkzeug.security import generate_password_hash, check_password_hash

hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

app = Flask(__name__)
app.config.from_object(Config)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        password = request.form["password"]

        hashed_password = generate_password_hash(
            password,
            method="pbkdf2:sha256"
        )

        # save hashed_password into database
        # NOT raw password

        return "User registered successfully"


@login_manager.user_loader
def user_loader_func(user_id):
    return load_user(user_id)

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

# ---------------------------
# Authentication
# ---------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db = get_db()
        row = db.execute("SELECT * FROM Users WHERE Username = ?", (form.username.data,)).fetchone()
        # debug prints (remove in production)
        current_app.logger.debug("DEBUG DB PATH: %s", current_app.config.get("DATABASE"))
        current_app.logger.debug("DEBUG row: %s", row)
        if row and check_password_hash(row["PasswordHash"], form.password.data):
            user = User(row)
            login_user(user)
            flash("Logged in successfully", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for("login"))

# ---------------------------
# Dashboard (analytics)
# ---------------------------
@app.route("/")
@login_required
def dashboard():
    # KPI stats
    db = get_db()
    total_buses_row = db.execute("SELECT COUNT(*) AS c FROM Buses").fetchone()
    total_employees_row = db.execute("SELECT COUNT(*) AS c FROM Employees").fetchone()
    today_trips_row = db.execute(
        "SELECT COUNT(*) AS c FROM Trips WHERE date(DepartureDateTime) = date('now')"
    ).fetchone()
    completed_trips_row = db.execute("SELECT COUNT(*) AS c FROM Trips WHERE Status = 'Completed'").fetchone()

    stats = {
        "active_buses": int(db.execute("SELECT COUNT(*) AS c FROM Buses WHERE Status='Active'").fetchone()["c"] or 0),
        "total_employees": int(total_employees_row["c"] or 0),
        "today_trips": int(today_trips_row["c"] or 0),
        "completed_trips": int(completed_trips_row["c"] or 0),
    }

    # Chart: trips per route
    route_rows = db.execute("""
        SELECT r.RouteName, COUNT(t.TripID) AS trips
        FROM Routes r
        LEFT JOIN Trips t ON r.RouteID = t.RouteID
        GROUP BY r.RouteID
        ORDER BY trips DESC
    """).fetchall()
    route_names = [r["RouteName"] for r in route_rows]
    route_trip_counts = [r["trips"] for r in route_rows]

    # Chart: bus status
    active_count = db.execute("SELECT COUNT(*) AS c FROM Buses WHERE Status='Active'").fetchone()["c"] or 0
    inactive_count = db.execute("SELECT COUNT(*) AS c FROM Buses WHERE Status!='Active'").fetchone()["c"] or 0
    bus_status_data = [int(active_count), int(inactive_count)]

    # Chart: driver workload (trips per driver)
    driver_rows = db.execute("""
        SELECT e.FullName AS name, COUNT(t.TripID) AS cnt
        FROM Employees e
        LEFT JOIN Trips t ON e.EmployeeID = t.DriverID
        GROUP BY e.EmployeeID
        ORDER BY cnt DESC
        LIMIT 10
    """).fetchall()
    driver_names = [d["name"] for d in driver_rows]
    driver_trips = [d["cnt"] for d in driver_rows]

    charts = {
        "route_names": route_names,
        "route_trip_counts": route_trip_counts,
        "bus_status_data": bus_status_data,
        "driver_names": driver_names,
        "driver_trips": driver_trips,
    }

    return render_template("dashboard.html", stats=stats, charts=charts)

# ---------------------------
# User Profile
# ---------------------------
@app.route("/profile")
@login_required
def profile_view():
    """Displays the current authenticated user's profile information."""
    # Since current_user object already holds all necessary info (like username, email), 
    # we just need to render the template.
    return render_template("profile.html") # We will create this template next

# ----------------------------------------
# Employees CRUD
# ----------------------------------------

@app.route("/employees")
@login_required
def employees_view():
    if not has_permission("view_employees"):
        flash("Permission denied", "danger")
        return redirect(url_for("dashboard"))

    search = request.args.get("search", "").strip()

    if search:
        employees = query_db("""
            SELECT * FROM Employees
            WHERE FullName LIKE ? OR Phone LIKE ? OR CNIC LIKE ?
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        employees = query_db("SELECT * FROM Employees")

    return render_template("employees.html", employees=employees)


@app.route("/employees/add", methods=["GET", "POST"])
@login_required
def employee_add():
    if not has_permission("add_employee"):
        flash("Permission denied", "danger")
        return redirect(url_for("employees_view"))

    if request.method == "POST":
        form = request.form
        db = get_db()

        db.execute("""
            INSERT INTO Employees (FullName, CNIC, Phone, Address, JobID, ShiftID, Status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            form.get("FullName"),
            form.get("CNIC"),
            form.get("Phone"),
            form.get("Address") or "",
            form.get("JobID") or None,
            form.get("ShiftID") or None,
            form.get("Status") or "Active",
        ))

        db.commit()
        flash("Employee added successfully", "success")
        return redirect(url_for("employees_view"))

    return render_template("employee_add.html")

@app.route("/employees/edit/<int:employee_id>", methods=["GET", "POST"])
@login_required
def employee_edit(employee_id):
    if not has_permission("edit_employee"):
        flash("Permission denied", "danger")
        return redirect(url_for("employees_view"))

    db = get_db()
    employee = db.execute("SELECT * FROM Employees WHERE EmployeeID = ?", (employee_id,)).fetchone()

    if not employee:
        flash("Employee not found", "danger")
        return redirect(url_for("employees_view"))

    if request.method == "POST":
        form = request.form

        db.execute("""
            UPDATE Employees
            SET FullName = ?, CNIC = ?, Phone = ?, Address = ?, JobID = ?, ShiftID = ?, Status = ?
            WHERE EmployeeID = ?
        """, (
            form.get("FullName"),
            form.get("CNIC"),
            form.get("Phone"),
            form.get("Address") or "",
            form.get("JobID") or None,
            form.get("ShiftID") or None,
            form.get("Status") or "Active",
            employee_id,
        ))

        db.commit()
        flash("Employee updated successfully", "success")
        return redirect(url_for("employees_view"))

    return render_template("employee_edit.html", employee=employee)


@app.route("/employees/delete/<int:employee_id>", methods=["POST"])
@login_required
def employee_delete(employee_id):
    if not has_permission("delete_employee"):
        flash("Permission denied", "danger")
        return redirect(url_for("employees_view"))

    db = get_db()
    db.execute("DELETE FROM Employees WHERE EmployeeID = ?", (employee_id,))
    db.commit()

    flash("Employee deleted successfully", "info")
    return redirect(url_for("employees_view"))

# ---------------------------
# Buses CRUD
# ---------------------------
@app.route("/buses")
@login_required
def buses_view():
    if not has_permission("view_buses"):
        flash("Permission denied", "danger")
        return redirect(url_for("dashboard"))
    buses = query_db("""
        SELECT b.*, bc.CategoryName AS Category
        FROM Buses b
        LEFT JOIN BusCategories bc ON b.CategoryID = bc.CategoryID
    """)
    return render_template("buses.html", buses=buses)

@app.route("/buses/add", methods=["GET", "POST"])
@login_required
def bus_add():
    if not has_permission("add_bus"):
        flash("Permission denied", "danger")
        return redirect(url_for("buses_view"))
    db = get_db()
    categories = db.execute("SELECT * FROM BusCategories").fetchall()
    if request.method == "POST":
        f = request.form
        db.execute(
            "INSERT INTO Buses (BusNumber, Model, Capacity, RouteID, CategoryID, Status) VALUES (?, ?, ?, ?, ?, ?)",
            (f.get("BusNumber"), f.get("Model"), f.get("Capacity") or None, f.get("RouteID") or None, f.get("CategoryID") or None, "Active"),
        )
        db.commit()
        flash("Bus added", "success")
        return redirect(url_for("buses_view"))
    return render_template("bus_add.html", categories=categories)

@app.route("/buses/edit/<int:id>", methods=["GET", "POST"])
@login_required
def bus_edit(id):
    if not has_permission("edit_bus"):
        flash("Permission denied", "danger")
        return redirect(url_for("buses_view"))
    db = get_db()
    bus = db.execute("SELECT * FROM Buses WHERE BusID = ?", (id,)).fetchone()
    if not bus:
        flash("Bus not found", "danger")
        return redirect(url_for("buses_view"))
    categories = db.execute("SELECT * FROM BusCategories").fetchall()
    if request.method == "POST":
        f = request.form
        db.execute(
            "UPDATE Buses SET BusNumber=?, Model=?, Capacity=?, RouteID=?, CategoryID=?, Status=? WHERE BusID=?",
            (f.get("BusNumber"), f.get("Model"), f.get("Capacity") or None, f.get("RouteID") or None, f.get("CategoryID") or None, f.get("Status") or "Active", id),
        )
        db.commit()
        flash("Bus updated", "success")
        return redirect(url_for("buses_view"))
    return render_template("bus_edit.html", bus=bus, categories=categories)

@app.route("/buses/delete/<int:id>", methods=["POST"])
@login_required
def bus_delete(id):
    if not has_permission("delete_bus"):
        flash("Permission denied", "danger")
        return redirect(url_for("buses_view"))
    db = get_db()
    db.execute("DELETE FROM Buses WHERE BusID = ?", (id,))
    db.commit()
    flash("Bus deleted", "info")
    return redirect(url_for("buses_view"))

# ---------------------------
# Routes CRUD
# ---------------------------
@app.route("/routes")
@login_required
def routes_view():
    if not has_permission("view_routes"):
        flash("Permission denied", "danger")
        return redirect(url_for("dashboard"))
    routes = query_db("SELECT * FROM Routes")
    return render_template("routes.html", routes=routes)

@app.route("/routes/add", methods=["GET", "POST"])
@login_required
def route_add():
    if not has_permission("add_route"):
        flash("Permission denied", "danger")
        return redirect(url_for("routes_view"))
    if request.method == "POST":
        f = request.form
        db = get_db()
        db.execute(
            "INSERT INTO Routes (RouteName, DistanceKm, EstimatedMinutes, Active) VALUES (?, ?, ?, ?)",
            (f.get("RouteName"), f.get("DistanceKm") or None, f.get("EstimatedMinutes") or None, int(f.get("Active", "1"))),
        )
        db.commit()
        flash("Route added", "success")
        return redirect(url_for("routes_view"))
    return render_template("route_add.html")

@app.route("/routes/edit/<int:id>", methods=["GET", "POST"])
@login_required
def route_edit(id):
    if not has_permission("edit_route"):
        flash("Permission denied", "danger")
        return redirect(url_for("routes_view"))
    db = get_db()
    route = db.execute("SELECT * FROM Routes WHERE RouteID = ?", (id,)).fetchone()
    if not route:
        flash("Route not found", "danger")
        return redirect(url_for("routes_view"))
    if request.method == "POST":
        f = request.form
        db.execute(
            "UPDATE Routes SET RouteName=?, DistanceKm=?, EstimatedMinutes=?, Active=? WHERE RouteID=?",
            (f.get("RouteName"), f.get("DistanceKm") or None, f.get("EstimatedMinutes") or None, int(f.get("Active", "1")), id),
        )
        db.commit()
        flash("Route updated", "success")
        return redirect(url_for("routes_view"))
    return render_template("route_edit.html", route=route)

@app.route("/routes/delete/<int:id>", methods=["POST"])
@login_required
def route_delete(id):
    if not has_permission("delete_route"):
        flash("Permission denied", "danger")
        return redirect(url_for("routes_view"))
    db = get_db()
    db.execute("DELETE FROM Routes WHERE RouteID = ?", (id,))
    db.commit()
    flash("Route deleted", "info")
    return redirect(url_for("routes_view"))

# ---------------------------
# Trips CRUD
# ---------------------------
@app.route("/trips")
@login_required
def trips_view():
    if not has_permission("view_trips"):
        flash("Permission denied", "danger")
        return redirect(url_for("dashboard"))
    db = get_db()
    trips = db.execute("""
        SELECT t.TripID, t.RouteID, t.BusID, t.DriverID, t.DepartureDateTime AS DepartureTime,
               t.ArrivalDateTime AS ArrivalTime, t.Status,
               b.BusNumber, r.RouteName,
               e.FullName AS EmployeeName
        FROM Trips t
        LEFT JOIN Buses b ON t.BusID = b.BusID
        LEFT JOIN Routes r ON t.RouteID = r.RouteID
        LEFT JOIN Employees e ON t.DriverID = e.EmployeeID
        ORDER BY t.DepartureDateTime DESC
    """).fetchall()
    return render_template("trips.html", trips=trips)

@app.route("/trips/add", methods=["GET", "POST"])
@login_required
def trip_add():
    if not has_permission("add_trip"):
        flash("Permission denied", "danger")
        return redirect(url_for("trips_view"))
    db = get_db()
    buses = db.execute("SELECT BusID, BusNumber FROM Buses WHERE Status='Active'").fetchall()
    routes = db.execute("SELECT RouteID, RouteName FROM Routes WHERE Active=1").fetchall()
    employees = db.execute("SELECT EmployeeID, FullName AS Name FROM Employees WHERE Status='Active'").fetchall()
    if request.method == "POST":
        f = request.form
        db.execute(
            "INSERT INTO Trips (RouteID, BusID, DriverID, DepartureDateTime, ArrivalDateTime, Status) VALUES (?, ?, ?, ?, ?, ?)",
            (f.get("RouteID"), f.get("BusID"), f.get("DriverID") or None, f.get("DepartureTime"), f.get("ArrivalTime"), f.get("Status") or "Scheduled"),
        )
        db.commit()
        flash("Trip created", "success")
        return redirect(url_for("trips_view"))
    return render_template("trip_add.html", buses=buses, routes=routes, employees=employees)

@app.route("/trips/edit/<int:id>", methods=["GET", "POST"])
@login_required
def trip_edit(id):
    if not has_permission("edit_trip"):
        flash("Permission denied", "danger")
        return redirect(url_for("trips_view"))
    db = get_db()
    trip = db.execute("SELECT * FROM Trips WHERE TripID = ?", (id,)).fetchone()
    if not trip:
        flash("Trip not found", "danger")
        return redirect(url_for("trips_view"))
    buses = db.execute("SELECT BusID, BusNumber FROM Buses WHERE Status='Active'").fetchall()
    routes = db.execute("SELECT RouteID, RouteName FROM Routes WHERE Active=1").fetchall()
    employees = db.execute("SELECT EmployeeID, FullName AS Name FROM Employees WHERE Status='Active'").fetchall()
    if request.method == "POST":
        f = request.form
        db.execute(
            "UPDATE Trips SET RouteID=?, BusID=?, DriverID=?, DepartureDateTime=?, ArrivalDateTime=?, Status=? WHERE TripID=?",
            (f.get("RouteID"), f.get("BusID"), f.get("DriverID") or None, f.get("DepartureTime"), f.get("ArrivalTime"), f.get("Status") or "Scheduled", id),
        )
        db.commit()
        flash("Trip updated", "success")
        return redirect(url_for("trips_view"))
    return render_template("trip_edit.html", trip=trip, buses=buses, routes=routes, employees=employees)

@app.route("/trips/delete/<int:id>", methods=["POST"])
@login_required
def trip_delete(id):
    if not has_permission("delete_trip"):
        flash("Permission denied", "danger")
        return redirect(url_for("trips_view"))
    db = get_db()
    db.execute("DELETE FROM Trips WHERE TripID = ?", (id,))
    db.commit()
    flash("Trip deleted", "info")
    return redirect(url_for("trips_view"))

# ---------------------------
# Categories CRUD
# ---------------------------
@app.route("/categories")
@login_required
def categories_view():
    if not has_permission("view_buses"):  # categories are admin-managed; reuse a bus-permission check
        flash("Permission denied", "danger")
        return redirect(url_for("dashboard"))
    categories = query_db("SELECT * FROM BusCategories")
    return render_template("categories.html", categories=categories)

@app.route("/categories/add", methods=["GET", "POST"])
@login_required
def category_add():
    if not has_permission("add_bus"):
        flash("Permission denied", "danger")
        return redirect(url_for("categories_view"))
    if request.method == "POST":
        f = request.form
        db = get_db()
        db.execute("INSERT INTO BusCategories (CategoryName) VALUES (?)", (f.get("CategoryName"),))
        db.commit()
        flash("Category added", "success")
        return redirect(url_for("categories_view"))
    return render_template("category_add.html")

@app.route("/categories/edit/<int:id>", methods=["GET", "POST"])
@login_required
def category_edit(id):
    if not has_permission("edit_bus"):
        flash("Permission denied", "danger")
        return redirect(url_for("categories_view"))
    db = get_db()
    cat = db.execute("SELECT * FROM BusCategories WHERE CategoryID = ?", (id,)).fetchone()
    if not cat:
        flash("Category not found", "danger")
        return redirect(url_for("categories_view"))
    if request.method == "POST":
        f = request.form
        db.execute("UPDATE BusCategories SET CategoryName = ? WHERE CategoryID = ?", (f.get("CategoryName"), id))
        db.commit()
        flash("Category updated", "success")
        return redirect(url_for("categories_view"))
    return render_template("category_edit.html", category=cat)

@app.route("/categories/delete/<int:id>", methods=["POST"])
@login_required
def category_delete(id):
    if not has_permission("delete_bus"):
        flash("Permission denied", "danger")
        return redirect(url_for("categories_view"))
    db = get_db()
    db.execute("DELETE FROM BusCategories WHERE CategoryID = ?", (id,))
    db.commit()
    flash("Category deleted", "info")
    return redirect(url_for("categories_view"))

# ---------------------------
# Tickets Module
# ---------------------------

@app.route("/tickets")
@login_required
def tickets_view():
    if not has_permission("view_tickets"):
        flash("Permission denied", "danger")
        return redirect(url_for("dashboard"))

    tickets = query_db("""
        SELECT
            t.TicketID,
            t.IssuedAt,
            t.PaymentMethod,
            tr.TripID,
            tr.DepartureDateTime,
            r.RouteName,
            GROUP_CONCAT(ts.SeatLabel, ', ') AS Seats
        FROM Tickets t
        JOIN Trips tr ON t.TripID = tr.TripID
        JOIN Routes r ON tr.RouteID = r.RouteID
        LEFT JOIN TicketSeats ts ON t.TicketID = ts.TicketID
        GROUP BY t.TicketID
        ORDER BY tr.DepartureDateTime DESC
    """)

    return render_template("tickets.html", tickets=tickets)


@app.route("/tickets/add", methods=["GET", "POST"])
@login_required
def ticket_add():
    if not has_permission("add_ticket"):
        flash("Permission denied", "danger")
        return redirect(url_for("tickets_view"))

    db = get_db()

    trips = query_db("""
        SELECT tr.TripID, r.RouteName, tr.TripDate
        FROM Trips tr
        JOIN Routes r ON tr.RouteID = r.RouteID
        ORDER BY tr.TripDate DESC
    """)

    if request.method == "POST":
        trip_id = request.form.get("TripID")
        seat = request.form.get("SeatNumber")
        payment = request.form.get("PaymentMethod", "Cash")

        if not trip_id or not seat:
            flash("Trip and seat are required", "danger")
            return redirect(url_for("ticket_add"))

        # 🔒 Check if seat already booked
        seat_exists = db.execute("""
            SELECT 1
            FROM TicketSeats ts
            JOIN Tickets t ON ts.TicketID = t.TicketID
            WHERE t.TripID = ? AND ts.SeatLabel = ?
        """, (trip_id, seat)).fetchone()

        if seat_exists:
            flash("This seat is already booked", "danger")
            return redirect(url_for("ticket_add"))

        try:
            # 🎟️ Create ticket
            cur = db.execute("""
                INSERT INTO Tickets (TripID, PaymentMethod)
                VALUES (?, ?)
            """, (trip_id, payment))

            ticket_id = cur.lastrowid

            # 💺 Assign seat
            db.execute("""
                INSERT INTO TicketSeats (TicketID, SeatLabel)
                VALUES (?, ?)
            """, (ticket_id, seat))

            db.commit()
            flash("Ticket booked successfully", "success")

        except Exception as e:
            db.rollback()
            flash("Booking failed. Please try again.", "danger")

        return redirect(url_for("tickets_view"))

    return render_template("ticket_add.html", trips=trips)


@app.route("/tickets/delete/<int:ticket_id>", methods=["POST"])
@login_required
def ticket_delete(ticket_id):
    if not has_permission("delete_ticket"):
        flash("Permission denied", "danger")
        return redirect(url_for("tickets_view"))

    db = get_db()

    db.execute("DELETE FROM TicketSeats WHERE TicketID=?", (ticket_id,))
    db.execute("DELETE FROM Tickets WHERE TicketID=?", (ticket_id,))
    db.commit()

    flash("Ticket deleted", "info")
    return redirect(url_for("tickets_view"))


@app.route("/tickets/seats/<int:trip_id>")
@login_required
def ticket_seats(trip_id):
    db = get_db()

    # Get bus category for seat layout
    trip = db.execute("""
        SELECT bc.CategoryName
        FROM Trips tr
        JOIN Buses b ON tr.BusID = b.BusID
        JOIN BusCategories bc ON b.CategoryID = bc.CategoryID
        WHERE tr.TripID = ?
    """, (trip_id,)).fetchone()

    if not trip:
        return {"layout": None, "booked": []}

    layout = BUS_CATEGORY_LAYOUTS.get(trip["CategoryName"])

    # Get already booked seats
    seats = db.execute("""
        SELECT ts.SeatLabel
        FROM TicketSeats ts
        JOIN Tickets t ON ts.TicketID = t.TicketID
        WHERE t.TripID = ?
    """, (trip_id,)).fetchall()

    booked_seats = [s["SeatLabel"] for s in seats]

    return {
        "layout": layout,
        "booked": booked_seats
    }


# ---------------------------
# Ticket Analytics
# ---------------------------

@app.route("/tickets/analytics")
@login_required
def ticket_analytics():
    if not has_permission("view_ticket_analytics"):
        flash("Permission denied", "danger")
        return redirect(url_for("dashboard"))

    db = get_db()

    total_tickets = db.execute(
        "SELECT COUNT(*) FROM Tickets"
    ).fetchone()[0]

    route_stats = db.execute("""
        SELECT r.RouteName, COUNT(t.TicketID) AS total
        FROM Tickets t
        JOIN Trips tr ON t.TripID = tr.TripID
        JOIN Routes r ON tr.RouteID = r.RouteID
        GROUP BY r.RouteName
        ORDER BY total DESC
    """).fetchall()

    trip_stats = db.execute("""
        SELECT tr.TripID, tr.TripDate, COUNT(t.TicketID) AS total
        FROM Tickets t
        JOIN Trips tr ON t.TripID = tr.TripID
        GROUP BY tr.TripID
        ORDER BY tr.TripDate DESC
        LIMIT 10
    """).fetchall()

    return render_template(
        "ticket_analytics.html",
        total_tickets=total_tickets,
        route_stats=route_stats,
        trip_stats=trip_stats
    )

# ---------------------------
# Run app
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)

