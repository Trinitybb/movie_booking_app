from database import get_connection


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS bookings;")
    cur.execute("DROP TABLE IF EXISTS seats;")
    cur.execute("DROP TABLE IF EXISTS showtimes;")
    cur.execute("DROP TABLE IF EXISTS movies;")

    cur.execute("""
        CREATE TABLE movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            rating TEXT,
            duration_minutes INTEGER
        );
    """)

    cur.execute("""
        CREATE TABLE showtimes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            screen_name TEXT,
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        );
    """)

    cur.execute("""
        CREATE TABLE seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            showtime_id INTEGER NOT NULL,
            row_label TEXT NOT NULL,
            seat_number INTEGER NOT NULL,
            is_booked INTEGER DEFAULT 0,
            FOREIGN KEY (showtime_id) REFERENCES showtimes(id)
        );
    """)

    cur.execute("""
        CREATE TABLE bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            showtime_id INTEGER NOT NULL,
            seat_id INTEGER NOT NULL,
            customer_name TEXT,
            confirmation_code TEXT NOT NULL,
            FOREIGN KEY (showtime_id) REFERENCES showtimes(id),
            FOREIGN KEY (seat_id) REFERENCES seats(id)
        );
    """)

    conn.commit()
    conn.close()


def seed_data():
    conn = get_connection()
    cur = conn.cursor()

    # 1) Insert Avatar
    cur.execute(
        """
        INSERT INTO movies (title, description, rating, duration_minutes)
        VALUES (?, ?, ?, ?);
        """,
        (
            "Avatar",
            "A paraplegic Marine dispatched to the moon Pandora on a unique mission "
            "becomes torn between following his orders and protecting the world he feels is his home.",
            "PG-13",
            162,
        ),
    )
    avatar_id = cur.lastrowid

    # 2) Insert Twilight
    cur.execute(
        """
        INSERT INTO movies (title, description, rating, duration_minutes)
        VALUES (?, ?, ?, ?);
        """,
        (
            "Twilight",
            "A teenage girl risks everything when she falls in love with a vampire.",
            "PG-13",
            122,
        ),
    )
    twilight_id = cur.lastrowid

    # Inserted Wicked: For Good
    cur.execute(
        """
        INSERT INTO movies (title, description, rating, duration_minutes)
        VALUES (?, ?, ?, ?);
        """,
        (
            "Wicked: For Good",
            "Now demonized as the Wicked Witch of the West, Elphaba lives in exile in the Ozian forest, while Glinda resides at the palace in Emerald City, reveling in the perks of fame and popularity. As an angry mob rises against the Wicked Witch, she'll need to reunite with Glinda to transform herself, and all of Oz, for good.",
            "PG",
            138,
        ),
    )
    wicked_id = cur.lastrowid

    # 3) Insert showtimes for both movies
    showtimes_data = [
        # Avatar showtimes
        (avatar_id,   "2025-12-10 19:30", "Screen 1"),
        (avatar_id,   "2025-12-10 21:30", "Screen 2"),
        (avatar_id,   "2025-12-11 18:00", "Screen 1"),

        # Twilight showtimes
        (twilight_id, "2025-12-10 20:00", "Screen 3"),
        (twilight_id, "2025-12-11 19:00", "Screen 2"),
        (twilight_id, "2025-12-12 21:15", "Screen 1"),

        #Wicked showtimes
        (wicked_id, "2025-12-10 22:30", "Screen 3"),
        (wicked_id, "2025-12-11 17:45", "Screen 2"),
        (wicked_id, "2025-12-12 20:20", "Screen 1"),
    ]

    showtime_ids = []
    for movie_id_fk, start_time, screen_name in showtimes_data:
        cur.execute(
            """
            INSERT INTO showtimes (movie_id, start_time, screen_name)
            VALUES (?, ?, ?);
            """,
            (movie_id_fk, start_time, screen_name),
        )
        showtime_ids.append(cur.lastrowid)

    # 4) Generate seats: rows A–D, seats 1–10 for each showtime (same as before)
    rows = ["A", "B", "C", "D"]
    seats_per_row = 10

    for st_id in showtime_ids:
        for row_label in rows:
            for seat_number in range(1, seats_per_row + 1):
                cur.execute(
                    """
                    INSERT INTO seats (showtime_id, row_label, seat_number, is_booked)
                    VALUES (?, ?, ?, 0);
                    """,
                    (st_id, row_label, seat_number),
                )

    conn.commit()
    conn.close()



if __name__ == "__main__":
    create_tables()
    seed_data()
    print("Database initialized and seeded with Avatar movie + showtimes + seats.")
