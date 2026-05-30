import hashlib


def _hash(pw: str) -> str:
    try:
        import bcrypt
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    except Exception:
        return "sha256$" + hashlib.sha256(pw.encode()).hexdigest()


def seed_demo_data(conn) -> None:
    cur = conn.cursor()

    roles = ["admin", "trainer", "client"]
    cur.executemany("INSERT INTO roles(role_name) VALUES (?)", [(r,) for r in roles])
    role_id = {r: i + 1 for i, r in enumerate(roles)}

    cur.execute(
        """INSERT INTO users(email, password_hash, role_id, full_name, phone, card_id_skud)
           VALUES (?,?,?,?,?,?)""",
        ("admin@gym.ua", _hash("admin123"), role_id["admin"],
         "Адміністратор", "+380501112233", None),
    )

    sub_types = [
        ("Місячний безліміт",   30,  None, 1200.0, 7),
        ("Квартальний",         90,  None, 3200.0, 14),
        ("Річний",             365,  None, 9900.0, 30),
        ("8 відвідувань",       60,    8,  900.0,  0),
        ("12 відвідувань",      90,   12, 1300.0,  0),
    ]
    cur.executemany(
        """INSERT INTO subscription_types(name, duration_days, visit_limit, price, freeze_days_allowed)
           VALUES (?,?,?,?,?)""",
        sub_types,
    )

    rooms = [("Великий зал", 30), ("Зал йоги", 18),
             ("Кардіо-студія", 20), ("Басейн", 12)]
    cur.executemany("INSERT INTO rooms(name, capacity) VALUES (?,?)", rooms)

    cats = ["Йога", "Пілатес", "Функціональний",
            "Аеробіка", "Бойові мистецтва", "Плавання"]
    cur.executemany("INSERT INTO class_categories(name) VALUES (?)", [(c,) for c in cats])

    vcats = ["HIIT", "Силові", "Йога", "Кардіо", "Розтяжка", "CrossFit", "Прес"]
    cur.executemany("INSERT INTO video_categories(name) VALUES (?)", [(c,) for c in vcats])

    eq = [
        ("Бігова доріжка Technogym",     6, "ok"),
        ("Велотренажер Matrix",          8, "ok"),
        ("Силова рама",                  2, "ok"),
        ("Гантельний ряд 2-30 кг",       1, "ok"),
        ("Кросовер",                     1, "ok"),
        ("Степ-платформа",              15, "ok"),
    ]
    cur.executemany("INSERT INTO equipment(name, quantity, status) VALUES (?,?,?)", eq)

    conn.commit()
