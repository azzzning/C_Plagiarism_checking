from flask import Flask, render_template, request, redirect, flash
import os, hashlib, sqlite3
from werkzeug.utils import secure_filename
from pygments import lex
from pygments.lexers import CLexer
from itertools import combinations

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
DB_FILE = 'data/plagiarism_checking.db'
ALLOWED_EXTENSIONS = {'txt', 'c'}
PER_PAGE = 10
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

# 初始化数据库和表
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class TEXT NOT NULL,
            filename TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 工具函数
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_submissions():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT name, class, filename FROM submissions')
    rows = cursor.fetchall()
    conn.close()
    return [{'name': row[0], 'class': row[1], 'filename': row[2]} for row in rows]

def save_submission(name, cls, filename):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO submissions (name, class, filename) VALUES (?, ?, ?)', (name, cls, filename))
    conn.commit()
    conn.close()

def preprocess(code):
    return [val for typ, val in lex(code, CLexer()) if 'Comment' not in str(typ) and val.strip()]

def generate_kgrams(tokens, k=5):
    return [' '.join(tokens[i:i+k]) for i in range(len(tokens)-k+1)]

def rabin(s): return hashlib.sha256(s.encode()).hexdigest()

def compare_files(code1, code2, k=5):
    tokens1 = preprocess(code1)
    tokens2 = preprocess(code2)
    grams1 = generate_kgrams(tokens1)
    grams2 = generate_kgrams(tokens2)
    h1 = {rabin(g): g for g in grams1}
    h2 = {rabin(g): g for g in grams2}
    common = set(h1) & set(h2)
    sim = len(common) / max(len(h1), len(h2)) if common else 0
    matches = [h1[h] for h in common][:5] if sim >= 0.7 else []
    return round(sim * 100, 2), matches

def get_level(score):
    if score >= 85:
        return "高度相似"
    elif score >= 70:
        return "可能抄袭"
    return "相似度低"

@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    submissions = load_submissions()
    total = len(submissions)
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    page_data = submissions[(page - 1) * PER_PAGE : page * PER_PAGE]
    all_filenames = [item['filename'] for item in submissions]
    return render_template('index.html',
                           submissions=page_data,
                           total=total,
                           page=page,
                           total_pages=total_pages,
                           all_filenames=all_filenames)

@app.route('/student', methods=['GET', 'POST'])
def student():
    if request.method == 'POST':
        name = request.form['name']
        cls = request.form['class']
        file = request.files['file']
        if file and allowed_file(file.filename):
            safe_name = secure_filename(file.filename)
            fname = f"{name}_{safe_name}"
            file.save(os.path.join(UPLOAD_FOLDER, fname))
            save_submission(name, cls, fname)
            flash("✅ 提交成功")
            return redirect('/student')
    return render_template("student.html")

@app.route('/upload_teacher', methods=['POST'])
def upload_teacher():
    files = request.files.getlist('files')
    teacher_class = request.form.get('class', '教师上传')
    count = 0
    for f in files:
        if f and allowed_file(f.filename):
            safe_name = secure_filename(f.filename)
            fname = f"教师_{safe_name}"
            f.save(os.path.join(UPLOAD_FOLDER, fname))
            save_submission("教师上传", teacher_class, fname)
            count += 1
    flash(f"✅ 教师端成功上传 {count} 份文件")
    return redirect('/')

@app.route('/view/<filename>')
def view_file(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return f"文件 {filename} 不存在", 404
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return render_template("view_file.html", filename=filename, content=content)

@app.route('/process', methods=['POST'])
def process():
    selected = request.form.getlist('selected')
    action = request.form.get('action')

    if not selected:
        flash("⚠️ 未选择任何文件")
        return redirect('/')

    if action == 'compare':
        files = load_submissions()
        info_map = {f['filename']: f for f in files}

        # 过滤出实际存在的文件
        valid_files = []
        for fname in selected:
            path = os.path.join(UPLOAD_FOLDER, fname)
            if os.path.exists(path):
                valid_files.append(fname)
            else:
                flash(f"⚠️ 文件 {fname} 不存在，已跳过", "warning")

        # 如果有效文件少于2个，无法进行查重
        if len(valid_files) < 2:
            flash("⚠️ 有效文件数量不足（至少需要2个文件进行查重）", "error")
            return redirect('/')

        # 读取文件内容
        content_map = {}
        for fname in valid_files:
            path = os.path.join(UPLOAD_FOLDER, fname)
            with open(path, 'r', encoding='utf-8') as f:
                content_map[fname] = f.read()

        suspicious = []
        summary = []
        for f1, f2 in combinations(valid_files, 2):
            sim, matches = compare_files(content_map[f1], content_map[f2])
            if sim >= 70:
                suspicious.append({
                    'file1': f1,
                    'file2': f2,
                    'name1': info_map[f1]['name'],
                    'name2': info_map[f2]['name'],
                    'class1': info_map[f1]['class'],
                    'class2': info_map[f2]['class'],
                    'similarity': sim,
                    'level': get_level(sim),
                    'matches': matches
                })
                summary.append(f"{info_map[f1]['name']}（{info_map[f1]['class']}） 与 {info_map[f2]['name']}（{info_map[f2]['class']}）")

        if not suspicious:
            flash("✅ 没有发现相似度超过70%的文件", "info")
        return render_template("compare.html", results=suspicious, summary=summary)

    elif action == 'delete':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        count = 0
        for fname in selected:
            cursor.execute('DELETE FROM submissions WHERE filename = ?', (fname,))
            path = os.path.join(UPLOAD_FOLDER, fname)
            if os.path.exists(path):
                os.remove(path)
                count += 1
        conn.commit()
        conn.close()
        flash(f"🗑 已成功删除 {count} 个文件")
        return redirect('/')

# 修改后的启动代码，支持本地和 Render 环境
if __name__ == '__main__':
    print("✅ 系统已启动：http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # Render 环境会设置 PORT 环境变量
    port = int(os.getenv("PORT", 5000))
    print(f"✅ 系统已启动：端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=False)