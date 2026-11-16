"""
database.py - SQLite storage for favourite routes, search history and settings.
Owner: Member 2 (Data & Logic)
"""
import os
import sqlite3
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metromate.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS favourites (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname    TEXT NOT NULL,
    from_st     TEXT NOT NULL,
    to_st       TEXT NOT NULL,
    created     TEXT NOT NULL,
    UNIQUE (from_st, to_st)
);
CREATE TABLE IF NOT EXISTS history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    from_st     TEXT NOT NULL,
    to_st       TEXT NOT NULL,
    minutes     INTEGER NOT NULL,
    fare        INTEGER NOT NULL,
    searched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path=DB_FILE):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def _q(self, sql, args=()):
        return self.conn.execute(sql, args).fetchall()

    def _x(self, sql, args=()):
        cur = self.conn.execute(sql, args)
        self.conn.commit()
        return cur.lastrowid

    # settings
    def get_setting(self, key, default=""):
        r = self._q("SELECT value FROM settings WHERE key = ?", (key,))
        return r[0]["value"] if r else default

    def set_setting(self, key, value):
        self._x("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", (key, str(value)))

    # favourites
    def add_favourite(self, nickname, from_st, to_st):
        """Returns False if this route is already saved."""
        try:
            self._x("INSERT INTO favourites(nickname, from_st, to_st, created) VALUES (?,?,?,?)",
                    (nickname, from_st, to_st, datetime.now().strftime("%Y-%m-%d %H:%M")))
            return True
        except sqlite3.IntegrityError:
            return False

    def rename_favourite(self, fav_id, nickname):
        self._x("UPDATE favourites SET nickname = ? WHERE id = ?", (nickname, fav_id))

    def delete_favourite(self, fav_id):
        self._x("DELETE FROM favourites WHERE id = ?", (fav_id,))

    def get_favourites(self):
        return self._q("SELECT * FROM favourites ORDER BY nickname COLLATE NOCASE")

    # history
    def add_history(self, from_st, to_st, minutes, fare, when=None):
        when = when or datetime.now().strftime("%Y-%m-%d %H:%M")
        self._x("INSERT INTO history(from_st, to_st, minutes, fare, searched_at) VALUES (?,?,?,?,?)",
                (from_st, to_st, minutes, fare, when))

    def get_history(self, limit=50):
        return self._q("SELECT * FROM history ORDER BY searched_at DESC, id DESC LIMIT ?", (limit,))

    def clear_history(self):
        self._x("DELETE FROM history")

    def top_stations(self, limit=5):
        return self._q("""SELECT st, COUNT(*) AS n FROM (
                              SELECT from_st AS st FROM history UNION ALL SELECT to_st FROM history)
                          GROUP BY st ORDER BY n DESC, st LIMIT ?""", (limit,))
