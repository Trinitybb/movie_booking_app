from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_connection
import random
import string

app = Flask(__name__)
app.secret_key = "super-secret-key-change-me"  # needed for flash messages


def generate_confirmation_code(length=8):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.route("/")
def home():
    """Main screen: show all movies and let the user pick one."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM movies ORDER BY title;")
    movies = cur.fetchall()
    conn.close()

    if not movies:
        return "No movies found. Did you run init_db.py?", 500

    return render_template("home.html", movies=movies)



@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM movies WHERE id = ?;", (movie_id,))
    movie = cur.fetchone()

    cur.execute(
        "SELECT * FROM showtimes WHERE movie_id = ? ORDER BY start_time;",
        (movie_id,),
    )
    showtimes = cur.fetchall()

    conn.close()

    if movie is None:
        return "Movie not found", 404

    return render_template("movie.html", movie=movie, showtimes=showtimes)


@app.route("/showtime/<int:showtime_id>/seats", methods=["GET", "POST"])
def showtime_seats(showtime_id):
    conn = get_connection()
    cur = conn.cursor()

    # Get showtime and movie info
    cur.execute("SELECT * FROM showtimes WHERE id = ?;", (showtime_id,))
    showtime = cur.fetchone()

    if showtime is None:
        conn.close()
        return "Showtime not found", 404

    cur.execute("SELECT * FROM movies WHERE id = ?;", (showtime["movie_id"],))
    movie = cur.fetchone()

    if request.method == "POST":
        selected_seat_ids = request.form.getlist("seats")
        customer_name = request.form.get("customer_name", "").strip() or "Guest"

        if not selected_seat_ids:
            flash("Please select at least one seat.", "error")
        else:
            # Check that seats are still available
            placeholders = ",".join("?" for _ in selected_seat_ids)
            query = f"""
                SELECT id, is_booked
                FROM seats
                WHERE id IN ({placeholders}) AND showtime_id = ?;
            """
            cur.execute(query, (*selected_seat_ids, showtime_id))
            seats = cur.fetchall()

            # verify none already booked
            already_booked = [s for s in seats if s["is_booked"] == 1]

            if already_booked:
                flash("One or more selected seats were just booked. Please try again.", "error")
            else:
                confirmation = generate_confirmation_code()

                for seat in seats:
                    # mark seat as booked
                    cur.execute(
                        "UPDATE seats SET is_booked = 1 WHERE id = ?;",
                        (seat["id"],),
                    )
                    # insert booking
                    cur.execute(
                        """
                        INSERT INTO bookings (showtime_id, seat_id, customer_name, confirmation_code)
                        VALUES (?, ?, ?, ?);
                        """,
                        (showtime_id, seat["id"], customer_name, confirmation),
                    )

                conn.commit()
                conn.close()
                return redirect(url_for("booking_success", confirmation_code=confirmation))

    # GET or failed POST → show seats
    cur.execute(
        """
        SELECT * FROM seats
        WHERE showtime_id = ?
        ORDER BY row_label, seat_number;
        """,
        (showtime_id,),
    )
    seats = cur.fetchall()
    conn.close()

    # group seats by row for display
    rows = {}
    for seat in seats:
        row_label = seat["row_label"]
        rows.setdefault(row_label, []).append(seat)

    return render_template("seats.html", movie=movie, showtime=showtime, rows=rows)


@app.route("/booking/<string:confirmation_code>")
def booking_success(confirmation_code):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT b.confirmation_code,
               b.customer_name,
               s.row_label,
               s.seat_number,
               st.start_time,
               st.screen_name,
               m.title
        FROM bookings b
        JOIN seats s ON b.seat_id = s.id
        JOIN showtimes st ON b.showtime_id = st.id
        JOIN movies m ON st.movie_id = m.id
        WHERE b.confirmation_code = ?;
        """,
        (confirmation_code,),
    )
    bookings = cur.fetchall()
    conn.close()

    if not bookings:
        return "Booking not found", 404

    # All rows share same confirmation & showtime info
    header = bookings[0]

    return render_template(
        "booking_success.html",
        header=header,
        bookings=bookings,
    )


@app.route("/analytics")
def analytics():
    """Simple analysis: show how many seats are booked vs available per showtime."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT st.id,
               st.start_time,
               m.title,
               COUNT(s.id) AS total_seats,
               SUM(CASE WHEN s.is_booked = 1 THEN 1 ELSE 0 END) AS booked_seats
        FROM showtimes st
        JOIN movies m ON st.movie_id = m.id
        JOIN seats s ON s.showtime_id = st.id
        GROUP BY st.id, st.start_time, m.title
        ORDER BY st.start_time;
        """
    )
    rows = cur.fetchall()
    conn.close()

    # Prepare data for chart/summary
    analytics_data = []
    for r in rows:
        total = r["total_seats"]
        booked = r["booked_seats"]
        available = total - booked
        occupancy_rate = round((booked / total) * 100, 2) if total > 0 else 0.0

        analytics_data.append(
            {
                "showtime_id": r["id"],
                "start_time": r["start_time"],
                "movie_title": r["title"],
                "total_seats": total,
                "booked": booked,
                "available": available,
                "occupancy_rate": occupancy_rate,
            }
        )

    return render_template("analytics.html", analytics_data=analytics_data)


if __name__ == "__main__":
    app.run(debug=True)
