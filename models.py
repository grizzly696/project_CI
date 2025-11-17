from extensions import db
from datetime import datetime

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), default='word')
    text = db.Column(db.String(200), nullable=False)
    translation = db.Column(db.String(200), nullable=False)
    tags = db.Column(db.String(200), default='')
    score = db.Column(db.Integer, default=0)
    interval_days = db.Column(db.Integer, default=0)
    next_review = db.Column(db.DateTime, nullable=True)
    last_review = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
