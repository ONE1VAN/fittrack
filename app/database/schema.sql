
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS roles (
    role_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE  
);

CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    email          TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    role_id        INTEGER NOT NULL,
    full_name      TEXT NOT NULL,
    phone          TEXT,
    avatar_path    TEXT,
    card_id_skud   TEXT UNIQUE,           
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id);

CREATE TABLE IF NOT EXISTS subscription_types (
    type_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT NOT NULL UNIQUE,
    duration_days      INTEGER NOT NULL,        
    visit_limit        INTEGER,                
    price              REAL NOT NULL,
    freeze_days_allowed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS subscriptions (
    sub_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id         INTEGER NOT NULL,
    type_id           INTEGER NOT NULL,
    start_date        TEXT NOT NULL,
    end_date          TEXT NOT NULL,
    balance           INTEGER,                
    status            TEXT NOT NULL DEFAULT 'active' 
                       CHECK (status IN ('active','frozen','expired','cancelled')),
    freeze_days_used  INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (client_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (type_id)   REFERENCES subscription_types(type_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_sub_client ON subscriptions(client_id);
CREATE INDEX IF NOT EXISTS idx_sub_status ON subscriptions(status);

CREATE TABLE IF NOT EXISTS subscription_requests (
    req_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id      INTEGER NOT NULL,
    type_id        INTEGER NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','approved','rejected')),
    requested_at   TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at    TEXT,
    FOREIGN KEY (client_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (type_id)   REFERENCES subscription_types(type_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_subreq_status ON subscription_requests(status);

CREATE TABLE IF NOT EXISTS payments (
    pay_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id   INTEGER NOT NULL,
    sub_id      INTEGER,
    amount      REAL NOT NULL,
    paid_at     TEXT NOT NULL DEFAULT (datetime('now')),
    pay_type    TEXT NOT NULL DEFAULT 'full'    
                 CHECK (pay_type IN ('full','partial','debt')),
    FOREIGN KEY (client_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (sub_id)    REFERENCES subscriptions(sub_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS rooms (
    room_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE,
    capacity INTEGER NOT NULL DEFAULT 20
);

CREATE TABLE IF NOT EXISTS class_categories (
    cat_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE    
);

CREATE TABLE IF NOT EXISTS group_classes (
    class_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    cat_id      INTEGER NOT NULL,
    trainer_id  INTEGER NOT NULL,
    room_id     INTEGER NOT NULL,
    title       TEXT NOT NULL,
    start_time  TEXT NOT NULL,                 
    end_time    TEXT NOT NULL,
    capacity    INTEGER NOT NULL DEFAULT 20,
    FOREIGN KEY (cat_id)     REFERENCES class_categories(cat_id) ON DELETE RESTRICT,
    FOREIGN KEY (trainer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id)    REFERENCES rooms(room_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_class_start ON group_classes(start_time);

CREATE TABLE IF NOT EXISTS class_bookings (
    class_id   INTEGER NOT NULL,
    client_id  INTEGER NOT NULL,
    status     TEXT NOT NULL DEFAULT 'booked'  
                CHECK (status IN ('booked','attended','no_show','cancelled')),
    booked_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (class_id, client_id),
    FOREIGN KEY (class_id)  REFERENCES group_classes(class_id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES users(user_id)          ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS personal_trainings (
    pt_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    trainer_id  INTEGER NOT NULL,
    client_id   INTEGER NOT NULL,
    datetime    TEXT NOT NULL,
    duration_min INTEGER NOT NULL DEFAULT 60,
    status      TEXT NOT NULL DEFAULT 'booked'  
                 CHECK (status IN ('booked','done','cancelled')),
    notes       TEXT,
    FOREIGN KEY (trainer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (client_id)  REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS visit_logs (
    log_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id     INTEGER NOT NULL,
    sub_id        INTEGER,
    timestamp     TEXT NOT NULL DEFAULT (datetime('now')),
    event_type    INTEGER NOT NULL,            
    turnstile_id  TEXT,
    FOREIGN KEY (client_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (sub_id)    REFERENCES subscriptions(sub_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_visit_ts ON visit_logs(timestamp);

CREATE TABLE IF NOT EXISTS equipment (
    eq_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT NOT NULL,
    quantity           INTEGER NOT NULL DEFAULT 1,
    last_maintenance   TEXT,
    status             TEXT NOT NULL DEFAULT 'ok'   
                        CHECK (status IN ('ok','fault','maintenance'))
);

CREATE TABLE IF NOT EXISTS maintenance_records (
    mr_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    eq_id         INTEGER NOT NULL,
    reported_by   INTEGER NOT NULL,
    description   TEXT NOT NULL,
    photo_path    TEXT,
    critical      INTEGER NOT NULL DEFAULT 0,  
    reported_at   TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at   TEXT,
    FOREIGN KEY (eq_id)       REFERENCES equipment(eq_id)  ON DELETE CASCADE,
    FOREIGN KEY (reported_by) REFERENCES users(user_id)    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS video_categories (
    vcat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS videos (
    video_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    trainer_id      INTEGER NOT NULL,
    vcat_id         INTEGER NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    file_path       TEXT NOT NULL,
    thumbnail_path  TEXT,
    duration_sec    INTEGER,
    uploaded_at     TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (trainer_id) REFERENCES users(user_id)            ON DELETE CASCADE,
    FOREIGN KEY (vcat_id)    REFERENCES video_categories(vcat_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_video_uploaded ON videos(uploaded_at DESC);

CREATE TABLE IF NOT EXISTS video_likes (
    video_id INTEGER NOT NULL,
    user_id  INTEGER NOT NULL,
    liked_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (video_id, user_id),
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)  REFERENCES users(user_id)   ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comments (
    comment_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id          INTEGER NOT NULL,
    user_id           INTEGER NOT NULL,
    parent_comment_id INTEGER,                    
    text              TEXT NOT NULL,
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (video_id)          REFERENCES videos(video_id)     ON DELETE CASCADE,
    FOREIGN KEY (user_id)           REFERENCES users(user_id)       ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_comments_video ON comments(video_id, created_at);
