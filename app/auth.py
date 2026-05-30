import hashlib
from .database.repos import UserRepo

class Session:
    user_id: int | None = None
    role: str | None = None
    full_name: str | None = None
    email: str | None = None

    @classmethod
    def login(cls, user_row):
        cls.user_id   = user_row["user_id"]
        cls.role      = user_row["role_name"]
        cls.full_name = user_row["full_name"]
        cls.email     = user_row["email"]

    @classmethod
    def logout(cls):
        cls.user_id = cls.role = cls.full_name = cls.email = None

    @classmethod
    def is_authenticated(cls) -> bool:
        return cls.user_id is not None

def hash_password(password: str) -> str:
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    except Exception:
        return "sha256$" + hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith("$2"):
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode(), stored_hash.encode())
        except Exception:
            return False
    if stored_hash.startswith("sha256$"):
        return stored_hash == "sha256$" + hashlib.sha256(password.encode()).hexdigest()
    return False

def authenticate(email: str, password: str):
    row = UserRepo.by_email(email)
    if row is None:
        return None
    if verify_password(password, row["password_hash"]):
        Session.login(row)
        return row
    return None
