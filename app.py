from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
from extensions import db
from models import Word, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///language_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'change-this-secret-to-a-secure-random-value'

db.init_app(app)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('register'))
        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            flash('User with that username or email already exists.', 'error')
            return redirect(url_for('register'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session['user'] = user.username
        flash('Registration successful. You are now logged in.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        if not user or not user.check_password(password):
            flash('Неверное имя пользователя или пароль', 'error')
            return redirect(url_for('login'))
        session['user'] = user.username
        flash('Вы вошли в систему', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/')
def index():
    total = Word.query.count()
    due = Word.query.filter((Word.next_review == None) | (Word.next_review <= datetime.utcnow())).count()
    recent_reviews = Word.query.order_by(Word.last_review.desc()).limit(10).all()

    # --- Прогресс по дням ---
    from sqlalchemy import func
    progress = (
        db.session.query(func.date(Word.last_review), func.count(Word.id))
        .group_by(func.date(Word.last_review))
        .order_by(func.date(Word.last_review))
        .all()
    )
    labels = [p[0] if isinstance(p[0], str) else p[0].strftime("%d.%m") for p in progress]
    values = [p[1] for p in progress]

    return render_template(
        'index.html',
        total=total,
        due=due,
        recent=recent_reviews,
        labels=labels,
        values=values
    )

@app.route('/vocab')
def vocab():
    q = request.args.get('q', '')
    if q:
        words = Word.query.filter(
            (Word.text.ilike(f'%{q}%')) |
            (Word.translation.ilike(f'%{q}%')) |
            (Word.tags.ilike(f'%{q}%'))
        ).all()
    else:
        words = Word.query.order_by(Word.created_at.desc()).all()
    return render_template('vocab.html', words=words, q=q)

@app.route('/add', methods=['POST'])
def add_word():
    text = request.form.get('text')
    translation = request.form.get('translation')
    tags = request.form.get('tags')
    type_ = request.form.get('type')
    if text and translation:
        new_word = Word(text=text, translation=translation, tags=tags, type=type_)
        db.session.add(new_word)
        db.session.commit()
    return redirect(url_for('vocab'))

@app.route('/delete/<int:id>')
def delete_word(id):
    w = Word.query.get_or_404(id)
    db.session.delete(w)
    db.session.commit()
    return redirect(url_for('vocab'))

@app.route('/review/<int:id>/<result>')
def review_word(id, result):
    w = Word.query.get_or_404(id)
    correct = result == 'true'
    now = datetime.utcnow()
    if correct:
        w.score += 1
        w.interval_days = max(1, w.interval_days + 1)
    else:
        w.score = max(0, w.score - 1)
        w.interval_days = max(1, w.interval_days // 2)
    w.next_review = now + timedelta(days=w.interval_days)
    w.last_review = now
    db.session.commit()
    return redirect(url_for('vocab'))

@app.route('/quiz')
def quiz():
    words = Word.query.order_by(db.func.random()).limit(10).all()
    return render_template('quiz.html', words=words)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
