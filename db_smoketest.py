from database import get_db_cursor

print("Starting DB smoke test...")

with get_db_cursor() as cursor:
    cursor.execute("SELECT DATABASE() AS db;")
    print("Connected to database:", cursor.fetchone()["db"])

    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()

    print("Tables found:")
    for t in tables:
        print(" -", list(t.values())[0])

print("DB smoke test PASSED.")
