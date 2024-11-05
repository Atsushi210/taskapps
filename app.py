from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta  # timedeltaをインポート


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # フラッシュメッセージに必要な秘密鍵

# SQLite データベースの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# データベース初期化
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Flask-Migrateの設定

# タスクモデルの定義
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    complete = db.Column(db.Boolean, default=False)
    deadline = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(10), nullable=True)

# データベース作成
with app.app_context():
    db.create_all()

# タスクリストの表示と追加
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        task_name = request.form.get('task')
        task_deadline = request.form.get('deadline')
        task_priority = request.form.get('priority')

        if task_name:
            if task_deadline:
                task_deadline = datetime.strptime(task_deadline, '%Y-%m-%d').date()
            new_task = Task(name=task_name, deadline=task_deadline, priority=task_priority)
            db.session.add(new_task)
            db.session.commit()
            flash(f"タスク '{task_name}' を追加しました", 'success')
        return redirect('/')

    # 並び替え基準を取得
    sort_by = request.args.get('sort_by', 'priority_high')
    filter_by = request.args.get('filter_by', 'all')

    # 並び替えロジック
    if sort_by == 'priority_high':
        query = Task.query.order_by(Task.priority.desc(), Task.deadline.asc())
    elif sort_by == 'priority_low':
        query = Task.query.order_by(Task.priority.asc(), Task.deadline.asc())
    elif sort_by == 'date_new':
        query = Task.query.order_by(Task.deadline.desc())
    elif sort_by == 'date_old':
        query = Task.query.order_by(Task.deadline.asc())
    else:
        query = Task.query

    # フィルタリングロジック
    if filter_by == 'high_priority':
        query = query.filter(Task.priority == '高')
    elif filter_by == 'low_priority':
        query = query.filter(Task.priority == '低')
    elif filter_by == 'complete':
        query = query.filter(Task.complete == True)
    elif filter_by == 'incomplete':
        query = query.filter(Task.complete == False)

    tasks = query.all()

    today = datetime.today().date()

    # 各タスクの期限状態をチェック
    for task in tasks:
        if task.deadline:
            if task.deadline < today:
                task.status = 'overdue'  # 期限切れ
            elif task.deadline == today:
                task.status = 'due_today'  # 今日が期限
            elif task.deadline <= today + timedelta(days=1):
                task.status = 'due_soon'  # 期限が近い
            else:
                task.status = 'normal'  # 通常の状態
        else:
            task.status = 'no_deadline'  # 期限が設定されていない

    reminders = [task for task in tasks if task.deadline and task.deadline <= today and not task.complete]

    return render_template('index.html', tasks=tasks, reminders=reminders, sort_by=sort_by, filter_by=filter_by)

# タスク削除
@app.route('/delete/<int:id>')
def delete_task(id):
    task_to_delete = Task.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return "タスクの削除中にエラーが発生しました。"

# タスク完了状態の更新
@app.route('/complete/<int:id>')
def complete_task(id):
    task = Task.query.get_or_404(id)
    try:
        task.complete = not task.complete
        db.session.commit()
        return redirect('/')
    except:
        return "タスクの更新中にエラーが発生しました。"

if __name__ == '__main__':
    app.run(debug=True)
