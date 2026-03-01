# src/user_database.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id               = db.Column(db.Integer, primary_key=True)
    username         = db.Column(db.String(80), unique=True, nullable=False)
    email            = db.Column(db.String(120), unique=True, nullable=False)
    password_hash    = db.Column(db.String(128), nullable=False)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    # Премиум
    is_premium       = db.Column(db.Boolean, default=False)
    premium_until    = db.Column(db.DateTime, nullable=True)

    # Счётчики поисков
    searches_count   = db.Column(db.Integer, default=0)   # бесплатные (сбрасывается при входе)
    searches_left    = db.Column(db.Integer, default=0)   # платные (списываются по одному)

    # -------------------------------------------------------
    #  Пароль
    # -------------------------------------------------------
    def set_password(self, password: str):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), salt
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    # -------------------------------------------------------
    #  Можно ли делать поиск?
    # -------------------------------------------------------
    def can_search(self) -> bool:
        # Премиум истёк?
        if self.is_premium and self.premium_until:
            if self.premium_until < datetime.utcnow():
                self.is_premium   = False
                self.searches_left = 0
                # commit делается снаружи (в app.py)
                return False

        if self.is_premium:
            return self.searches_left > 0

        # Бесплатный: 3 поиска в день (сбрасываются при каждом входе)
        return self.searches_count < 3

    # -------------------------------------------------------
    #  Удобные свойства
    # -------------------------------------------------------
    @property
    def premium_expired(self) -> bool:
        if not self.is_premium:
            return False
        if self.premium_until and self.premium_until < datetime.utcnow():
            return True
        return False

    @property
    def free_searches_left(self) -> int:
        return max(0, 3 - self.searches_count)

    def __repr__(self):
        return f'<User {self.username} premium={self.is_premium}>'


class SearchHistory(db.Model):
    __tablename__ = 'search_history'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vin         = db.Column(db.String(50), nullable=False)
    searched_at = db.Column(db.DateTime, default=datetime.utcnow)
    source      = db.Column(db.String(20), default='local')  # 'local' или 'api'

    user = db.relationship('User', backref=db.backref('searches', lazy=True))

    def __repr__(self):
        return f'<SearchHistory user={self.user_id} vin={self.vin}>'