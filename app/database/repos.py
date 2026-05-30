from datetime import datetime
from .db import get_db

class UserRepo:
    @staticmethod
    def by_email(email: str):
        return get_db().execute(
            """SELECT u.*, r.role_name FROM users u
               JOIN roles r ON r.role_id = u.role_id
               WHERE u.email = ?""", (email,)
        ).fetchone()

    @staticmethod
    def by_id(uid: int):
        return get_db().execute(
            """SELECT u.*, r.role_name FROM users u
               JOIN roles r ON r.role_id = u.role_id
               WHERE u.user_id = ?""", (uid,)
        ).fetchone()

    @staticmethod
    def clients():
        return get_db().execute(
            """SELECT u.* FROM users u JOIN roles r USING(role_id)
               WHERE r.role_name = 'client' ORDER BY u.full_name"""
        ).fetchall()

    @staticmethod
    def trainers():
        return get_db().execute(
            """SELECT u.* FROM users u JOIN roles r USING(role_id)
               WHERE r.role_name = 'trainer' ORDER BY u.full_name"""
        ).fetchall()

    @staticmethod
    def all_with_roles():
        return get_db().execute(
            """SELECT u.user_id, u.email, u.full_name, u.phone, u.card_id_skud,
                      r.role_name
               FROM users u JOIN roles r USING(role_id)
               ORDER BY r.role_name, u.full_name"""
        ).fetchall()

    @staticmethod
    def roles():
        return get_db().execute(
            "SELECT role_id, role_name FROM roles ORDER BY role_name"
        ).fetchall()

    @staticmethod
    def set_role(user_id: int, role_name: str) -> None:
        db = get_db()
        row = db.execute("SELECT role_id FROM roles WHERE role_name=?",
                         (role_name,)).fetchone()
        if row is None:
            return
        db.execute("UPDATE users SET role_id=? WHERE user_id=?",
                   (row["role_id"], user_id))
        db.commit()

    @staticmethod
    def delete(user_id: int) -> None:
        db = get_db()
        db.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        db.commit()

    @staticmethod
    def next_client_card_id() -> str:
        rows = get_db().execute(
            "SELECT card_id_skud FROM users WHERE card_id_skud LIKE 'RFID-C%'"
        ).fetchall()
        used = set()
        for r in rows:
            try:
                used.add(int(r["card_id_skud"].split("RFID-C")[-1]))
            except (ValueError, AttributeError):
                continue
        n = 1
        while n in used:
            n += 1
        return f"RFID-C{n:03d}"

    @staticmethod
    def create(email, password_hash, role_name, full_name, phone=None, card=None):
        db = get_db()
        role = db.execute("SELECT role_id FROM roles WHERE role_name=?", (role_name,)).fetchone()
        cur = db.execute(
            """INSERT INTO users(email, password_hash, role_id, full_name, phone, card_id_skud)
               VALUES (?,?,?,?,?,?)""",
            (email, password_hash, role["role_id"], full_name, phone, card),
        )
        db.commit()
        return cur.lastrowid

class SubscriptionRepo:
    @staticmethod
    def active_for_client(client_id: int):
        return get_db().execute(
            """SELECT s.*, t.name AS type_name, t.visit_limit, t.freeze_days_allowed
               FROM subscriptions s
               JOIN subscription_types t ON t.type_id = s.type_id
               WHERE s.client_id = ? AND s.status != 'cancelled'
               ORDER BY s.end_date DESC LIMIT 1""", (client_id,)
        ).fetchone()

    @staticmethod
    def all_for_client(client_id: int):
        return get_db().execute(
            """SELECT s.*, t.name AS type_name FROM subscriptions s
               JOIN subscription_types t USING(type_id)
               WHERE s.client_id=? ORDER BY s.start_date DESC""", (client_id,)
        ).fetchall()

    @staticmethod
    def all_with_clients(status: str | None = None):
        sql = """SELECT s.*, t.name AS type_name, u.full_name, u.phone
                 FROM subscriptions s
                 JOIN subscription_types t USING(type_id)
                 JOIN users u ON u.user_id = s.client_id"""
        args = ()
        if status:
            sql += " WHERE s.status = ?"; args = (status,)
        sql += " ORDER BY s.end_date DESC"
        return get_db().execute(sql, args).fetchall()

    @staticmethod
    def types():
        return get_db().execute("SELECT * FROM subscription_types ORDER BY price").fetchall()

    @staticmethod
    def freeze(sub_id: int):
        get_db().execute("UPDATE subscriptions SET status='frozen' WHERE sub_id=?", (sub_id,))
        get_db().commit()

    @staticmethod
    def unfreeze(sub_id: int):
        get_db().execute("UPDATE subscriptions SET status='active' WHERE sub_id=?", (sub_id,))
        get_db().commit()

    @staticmethod
    def cancel(sub_id: int):
        get_db().execute(
            "UPDATE subscriptions SET status='cancelled' WHERE sub_id=?", (sub_id,))
        get_db().commit()

    @staticmethod
    def delete(sub_id: int):
        get_db().execute("DELETE FROM subscriptions WHERE sub_id=?", (sub_id,))
        get_db().commit()

    @staticmethod
    def sell(client_id: int, type_id: int, start_date: str, end_date: str,
             balance, pay_type: str, amount: float):
        db = get_db()
        cur = db.execute(
            """INSERT INTO subscriptions(client_id, type_id, start_date, end_date, balance, status)
               VALUES (?,?,?,?,?,'active')""",
            (client_id, type_id, start_date, end_date, balance))
        sub_id = cur.lastrowid
        db.execute(
            """INSERT INTO payments(client_id, sub_id, amount, pay_type) VALUES (?,?,?,?)""",
            (client_id, sub_id, amount, pay_type))
        db.commit()
        return sub_id

class SubscriptionRequestRepo:

    @staticmethod
    def create(client_id: int, type_id: int) -> int:
        db = get_db()
        cur = db.execute(
            """INSERT INTO subscription_requests(client_id, type_id) VALUES (?,?)""",
            (client_id, type_id))
        db.commit()
        return cur.lastrowid

    @staticmethod
    def pending_for_client(client_id: int):
        return get_db().execute(
            """SELECT r.*, t.name AS type_name, t.price
               FROM subscription_requests r
               JOIN subscription_types t USING(type_id)
               WHERE r.client_id=? ORDER BY r.requested_at DESC""", (client_id,)
        ).fetchall()

    @staticmethod
    def all_with_clients(status: str | None = "pending"):
        sql = """SELECT r.*, t.name AS type_name, t.price, t.duration_days,
                        t.visit_limit, t.freeze_days_allowed,
                        u.full_name, u.phone
                 FROM subscription_requests r
                 JOIN subscription_types t USING(type_id)
                 JOIN users u ON u.user_id = r.client_id"""
        args = ()
        if status:
            sql += " WHERE r.status = ?"; args = (status,)
        sql += " ORDER BY r.requested_at DESC"
        return get_db().execute(sql, args).fetchall()

    @staticmethod
    def count_pending() -> int:
        row = get_db().execute(
            "SELECT COUNT(*) AS n FROM subscription_requests WHERE status='pending'"
        ).fetchone()
        return row["n"]

    @staticmethod
    def approve(req_id: int) -> int | None:
        from datetime import date, timedelta
        db = get_db()
        req = db.execute(
            """SELECT r.*, t.duration_days, t.visit_limit, t.price
               FROM subscription_requests r
               JOIN subscription_types t USING(type_id)
               WHERE r.req_id=? AND r.status='pending'""", (req_id,)
        ).fetchone()
        if req is None:
            return None
        start = date.today().isoformat()
        end = (date.today() + timedelta(days=req["duration_days"])).isoformat()
        sub_id = SubscriptionRepo.sell(
            req["client_id"], req["type_id"], start, end,
            req["visit_limit"], "full", req["price"])
        db.execute(
            """UPDATE subscription_requests SET status='approved',
                      resolved_at=datetime('now') WHERE req_id=?""", (req_id,))
        db.commit()
        return sub_id

    @staticmethod
    def reject(req_id: int) -> None:
        db = get_db()
        db.execute(
            """UPDATE subscription_requests SET status='rejected',
                      resolved_at=datetime('now')
               WHERE req_id=? AND status='pending'""", (req_id,))
        db.commit()


class ScheduleRepo:
    @staticmethod
    def upcoming_classes(limit: int = 30):
        return get_db().execute(
            """SELECT gc.*, c.name AS category, r.name AS room, u.full_name AS trainer,
                      (SELECT COUNT(*) FROM class_bookings b
                         WHERE b.class_id = gc.class_id AND b.status != 'cancelled') AS booked_count
               FROM group_classes gc
               JOIN class_categories c USING(cat_id)
               JOIN rooms r USING(room_id)
               JOIN users u ON u.user_id = gc.trainer_id
               WHERE gc.start_time >= datetime('now','-1 hour')
               ORDER BY gc.start_time LIMIT ?""", (limit,)
        ).fetchall()

    @staticmethod
    def trainer_schedule(trainer_id: int):
        return get_db().execute(
            """SELECT gc.*, c.name AS category, r.name AS room,
                      u.full_name AS trainer,
                      (SELECT COUNT(*) FROM class_bookings b
                         WHERE b.class_id = gc.class_id AND b.status != 'cancelled') AS booked_count
               FROM group_classes gc
               JOIN class_categories c USING(cat_id)
               JOIN rooms r USING(room_id)
               JOIN users u ON u.user_id = gc.trainer_id
               WHERE gc.trainer_id = ? AND gc.start_time >= datetime('now','-1 day')
               ORDER BY gc.start_time""", (trainer_id,)
        ).fetchall()

    @staticmethod
    def add_class(cat_id: int, trainer_id: int, room_id: int, title: str,
                  start_time: str, end_time: str, capacity: int = 20):
        db = get_db()
        cur = db.execute(
            """INSERT INTO group_classes(cat_id, trainer_id, room_id, title,
                                          start_time, end_time, capacity)
               VALUES (?,?,?,?,?,?,?)""",
            (cat_id, trainer_id, room_id, title, start_time, end_time, capacity))
        db.commit()
        return cur.lastrowid

    @staticmethod
    def delete_class(class_id: int) -> None:
        db = get_db()
        db.execute("DELETE FROM group_classes WHERE class_id=?", (class_id,))
        db.commit()

    @staticmethod
    def categories():
        return get_db().execute("SELECT * FROM class_categories ORDER BY name").fetchall()

    @staticmethod
    def rooms():
        return get_db().execute("SELECT * FROM rooms ORDER BY name").fetchall()

    @staticmethod
    def class_participants(class_id: int):
        return get_db().execute(
            """SELECT u.user_id, u.full_name, b.status FROM class_bookings b
               JOIN users u ON u.user_id = b.client_id
               WHERE b.class_id = ? ORDER BY u.full_name""", (class_id,)
        ).fetchall()

    @staticmethod
    def book(class_id: int, client_id: int):
        db = get_db()
        try:
            db.execute("INSERT INTO class_bookings(class_id, client_id) VALUES (?,?)",
                       (class_id, client_id))
            db.commit()
            return True
        except Exception:
            return False

    @staticmethod
    def cancel_booking(class_id: int, client_id: int):
        get_db().execute(
            "UPDATE class_bookings SET status='cancelled' WHERE class_id=? AND client_id=?",
            (class_id, client_id))
        get_db().commit()

    @staticmethod
    def kick_client(class_id: int, client_id: int):
        get_db().execute(
            "DELETE FROM class_bookings WHERE class_id=? AND client_id=?",
            (class_id, client_id))
        get_db().commit()

    @staticmethod
    def mark_attendance(class_id: int, client_id: int, attended: bool):
        new_status = 'attended' if attended else 'no_show'
        db = get_db()
        db.execute(
            "UPDATE class_bookings SET status=? WHERE class_id=? AND client_id=?",
            (new_status, class_id, client_id))
        if attended:
            sub = db.execute(
                """SELECT sub_id, balance FROM subscriptions
                   WHERE client_id=? AND status='active' AND balance IS NOT NULL AND balance > 0
                   ORDER BY end_date LIMIT 1""", (client_id,)).fetchone()
            if sub:
                db.execute("UPDATE subscriptions SET balance = balance - 1 WHERE sub_id=?",
                           (sub["sub_id"],))
        db.commit()

    @staticmethod
    def client_bookings(client_id: int):
        return get_db().execute(
            """SELECT gc.*, c.name AS category, r.name AS room, u.full_name AS trainer, b.status AS bk_status
               FROM class_bookings b
               JOIN group_classes gc ON gc.class_id = b.class_id
               JOIN class_categories c USING(cat_id)
               JOIN rooms r USING(room_id)
               JOIN users u ON u.user_id = gc.trainer_id
               WHERE b.client_id = ? AND gc.start_time >= datetime('now','-1 day')
               ORDER BY gc.start_time""", (client_id,)
        ).fetchall()

class PaymentRepo:
    @staticmethod
    def recent(limit: int = 50):
        return get_db().execute(
            """SELECT p.*, u.full_name FROM payments p
               JOIN users u ON u.user_id = p.client_id
               ORDER BY p.paid_at DESC LIMIT ?""", (limit,)
        ).fetchall()

    @staticmethod
    def total_today():
        row = get_db().execute(
            """SELECT COALESCE(SUM(amount),0) AS total FROM payments
               WHERE date(paid_at) = date('now')""").fetchone()
        return row["total"] or 0

class EquipmentRepo:
    @staticmethod
    def all():
        return get_db().execute("SELECT * FROM equipment ORDER BY name").fetchall()

    @staticmethod
    def faults():
        return get_db().execute(
            """SELECT m.*, e.name AS eq_name, u.full_name AS reporter
               FROM maintenance_records m
               JOIN equipment e ON e.eq_id = m.eq_id
               JOIN users u ON u.user_id = m.reported_by
               WHERE m.resolved_at IS NULL ORDER BY m.critical DESC, m.reported_at"""
        ).fetchall()

    @staticmethod
    def resolve_fault(mr_id: int) -> None:
        db = get_db()
        row = db.execute(
            "SELECT eq_id FROM maintenance_records WHERE mr_id=?", (mr_id,)
        ).fetchone()
        if row is None:
            return
        eq_id = row["eq_id"]
        db.execute(
            "UPDATE maintenance_records SET resolved_at=datetime('now') WHERE mr_id=?",
            (mr_id,))
        still_open = db.execute(
            "SELECT 1 FROM maintenance_records WHERE eq_id=? AND resolved_at IS NULL",
            (eq_id,)).fetchone()
        if not still_open:
            db.execute(
                "UPDATE equipment SET status='ok', last_maintenance=datetime('now') WHERE eq_id=?",
                (eq_id,))
        db.commit()

    @staticmethod
    def report_fault(eq_id: int, reported_by: int, description: str, critical: bool):
        db = get_db()
        db.execute(
            """INSERT INTO maintenance_records(eq_id, reported_by, description, critical)
               VALUES (?,?,?,?)""",
            (eq_id, reported_by, description, 1 if critical else 0))
        db.execute("UPDATE equipment SET status='fault' WHERE eq_id=?", (eq_id,))
        db.commit()

class VideoRepo:
    @staticmethod
    def feed(category_id: int | None = None):
        sql = """SELECT v.*, u.full_name AS trainer, c.name AS category,
                        (SELECT COUNT(*) FROM video_likes l WHERE l.video_id=v.video_id) AS likes,
                        (SELECT COUNT(*) FROM comments cm WHERE cm.video_id=v.video_id) AS comments_count
                 FROM videos v
                 JOIN users u ON u.user_id = v.trainer_id
                 JOIN video_categories c ON c.vcat_id = v.vcat_id"""
        args = ()
        if category_id:
            sql += " WHERE v.vcat_id = ?"; args = (category_id,)
        sql += " ORDER BY v.uploaded_at DESC"
        return get_db().execute(sql, args).fetchall()

    @staticmethod
    def by_id(video_id: int):
        return get_db().execute(
            """SELECT v.*, u.full_name AS trainer, c.name AS category,
                      (SELECT COUNT(*) FROM video_likes l WHERE l.video_id=v.video_id) AS likes
               FROM videos v
               JOIN users u ON u.user_id = v.trainer_id
               JOIN video_categories c ON c.vcat_id = v.vcat_id
               WHERE v.video_id = ?""", (video_id,)
        ).fetchone()

    @staticmethod
    def upload(trainer_id: int, vcat_id: int, title: str, description: str,
               file_path: str, thumbnail_path: str, duration_sec: int):
        db = get_db()
        cur = db.execute(
            """INSERT INTO videos(trainer_id, vcat_id, title, description, file_path, thumbnail_path, duration_sec)
               VALUES (?,?,?,?,?,?,?)""",
            (trainer_id, vcat_id, title, description, file_path, thumbnail_path, duration_sec))
        db.commit()
        return cur.lastrowid

    @staticmethod
    def set_thumbnail(video_id: int, thumbnail_path: str):
        db = get_db()
        db.execute("UPDATE videos SET thumbnail_path=? WHERE video_id=?",
                   (thumbnail_path, video_id))
        db.commit()

    @staticmethod
    def delete(video_id: int) -> bool:
        from pathlib import Path as _P
        db = get_db()
        row = db.execute(
            "SELECT file_path, thumbnail_path FROM videos WHERE video_id=?",
            (video_id,)).fetchone()
        if row is None:
            return False
        root = _P(__file__).resolve().parents[2]
        for rel in (row["file_path"], row["thumbnail_path"]):
            if not rel:
                continue
            p = root / rel
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        db.execute("DELETE FROM videos WHERE video_id=?", (video_id,))
        db.commit()
        return True

    @staticmethod
    def liked_by(video_id: int, user_id: int) -> bool:
        row = get_db().execute(
            "SELECT 1 FROM video_likes WHERE video_id=? AND user_id=?",
            (video_id, user_id)).fetchone()
        return row is not None

    @staticmethod
    def toggle_like(video_id: int, user_id: int) -> bool:
        db = get_db()
        existing = db.execute(
            "SELECT 1 FROM video_likes WHERE video_id=? AND user_id=?",
            (video_id, user_id)).fetchone()
        if existing:
            db.execute("DELETE FROM video_likes WHERE video_id=? AND user_id=?",
                       (video_id, user_id))
            db.commit()
            return False
        db.execute("INSERT INTO video_likes(video_id, user_id) VALUES (?,?)",
                   (video_id, user_id))
        db.commit()
        return True

    @staticmethod
    def categories():
        return get_db().execute("SELECT * FROM video_categories ORDER BY name").fetchall()

class CommentRepo:
    @staticmethod
    def for_video(video_id: int):
        rows = get_db().execute(
            """SELECT c.*, u.full_name, r.role_name FROM comments c
               JOIN users u ON u.user_id = c.user_id
               JOIN roles r ON r.role_id = u.role_id
               WHERE c.video_id = ? ORDER BY c.created_at""", (video_id,)
        ).fetchall()
        tops = [dict(r) for r in rows if r["parent_comment_id"] is None]
        replies_by_parent = {}
        for r in rows:
            if r["parent_comment_id"] is not None:
                replies_by_parent.setdefault(r["parent_comment_id"], []).append(dict(r))
        for t in tops:
            t["replies"] = replies_by_parent.get(t["comment_id"], [])
        return tops

    @staticmethod
    def add(video_id: int, user_id: int, text: str, parent_id: int | None = None) -> int:
        db = get_db()
        cur = db.execute(
            """INSERT INTO comments(video_id, user_id, parent_comment_id, text) VALUES (?,?,?,?)""",
            (video_id, user_id, parent_id, text))
        db.commit()
        return cur.lastrowid

class AnalyticsRepo:
    @staticmethod
    def kpi_overview():
        db = get_db()
        active = db.execute(
            "SELECT COUNT(*) AS n FROM subscriptions WHERE status='active'").fetchone()["n"]
        total = db.execute(
            """SELECT COUNT(*) AS n FROM users u JOIN roles r USING(role_id)
               WHERE r.role_name='client'""").fetchone()["n"]
        revenue_month = db.execute(
            """SELECT COALESCE(SUM(amount),0) AS s FROM payments
               WHERE date(paid_at) >= date('now','start of month')""").fetchone()["s"]
        retention = round((active / total) * 100, 1) if total else 0.0
        visits_today = db.execute(
            "SELECT COUNT(*) AS n FROM visit_logs WHERE date(timestamp)=date('now') AND event_type=0"
        ).fetchone()["n"]
        return {
            "active_subs": active,
            "total_clients": total,
            "retention_pct": retention,
            "revenue_month": revenue_month,
            "visits_today": visits_today,
        }
