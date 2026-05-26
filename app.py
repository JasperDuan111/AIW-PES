#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI辅助工作心理体验量表 (AIW-PES) - Flask Web应用
主题：人工智能辅助工作，给人带来的是负面情绪(焦虑/压力)还是积极体验(轻松/从容)
"""

import os
import sqlite3
import json
import datetime
import functools
from pathlib import Path

from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# ============================================================
# 配置
# ============================================================
BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / 'survey.db'
TXT_PATH = BASE_DIR / 'responses.txt'
QR_PATH = BASE_DIR / 'static' / 'qrcode.png'
HOST = '0.0.0.0'
PORT = int(os.environ.get('APP_PORT', os.environ.get('PORT', 8650)))
ADMIN_PASSWORD = '123456'

app = Flask(__name__)
app.secret_key = 'aiwpes-survey-secret-key-2025'

# ============================================================
# 量表定义 - 人口学变量（已取消专业大类）
# ============================================================
SCALE_INFO = {
    'name': 'AI辅助工作心理体验量表',
    'short_name': 'AIW-PES',
    'version': '1.0',
    'description': '本量表旨在评估高校学生在使用人工智能辅助学习和工作时，'
                   '心理层面更倾向于负面情绪（焦虑、压力）还是积极体验（轻松、从容）。'
}

DEMOGRAPHICS = [
    {
        'id': 'gender',
        'label': '性别',
        'type': 'radio',
        'required': True,
        'options': ['男', '女', '其他', '不愿透露']
    },
    {
        'id': 'grade',
        'label': '年级/学历',
        'type': 'radio',
        'required': True,
        'options': [
            '本科低年级（大一、大二）',
            '本科高年级（大三、大四）',
            '硕士',
            '博士'
        ]
    },
    {
        'id': 'major_detail',
        'label': '专业名称',
        'type': 'text',
        'required': True,
        'placeholder': '请输入您的专业全称（如：计算机科学与技术）'
    },
    {
        'id': 'ai_frequency',
        'label': '您使用AI工具（如ChatGPT、文心一言、Kimi、DeepSeek等）的频率',
        'type': 'radio',
        'required': True,
        'options': ['从不使用', '偶尔使用（每月几次）', '经常使用（每周几次）', '每天使用']
    },
    {
        'id': 'ai_tools',
        'label': '您最常使用的AI工具有哪些？（可多选）',
        'type': 'checkbox',
        'required': False,
        'options': [
            'ChatGPT/GPT系列', '文心一言', '通义千问/Qwen', 'Kimi',
            'DeepSeek', '豆包', 'Gemini', 'Claude', 'Copilot/GitHub Copilot',
            '其他（请在下题中说明）'
        ]
    },
    {
        'id': 'ai_tools_other',
        'label': '其他AI工具（如有请填写）',
        'type': 'text',
        'required': False,
        'placeholder': '例如：Midjourney, Cursor, 讯飞星火等'
    }
]

# 维度定义
DIMENSIONS = [
    {
        'id': 'perceived_impact',
        'name': '工作影响',
        'direction': 'positive',
        'questions': [
            '使用AI后，我能更深入理解复杂概念，而不是只得到表面答案',
            'AI 帮助我把时间从重复性任务中解放出来，用于更具创造性的工作',
            '在借助AI完成任务后，我仍能对结果进行批判性反思并改进自己的方法'
        ]
    },
    {
        'id': 'control_competence',
        'name': '个人掌控',
        'direction': 'positive',
        'questions': [
            '我能评估 AI 建议的可靠性并据此做出判断',
            '在使用AI时，我能灵活调整策略以获得更合适的结果',
            '我对学习和掌握新的AI工具感到自信并愿意投入时间'
        ]
    },
    {
        'id': 'emotional_response',
        'name': '情绪反应',
        'direction': 'negative',
        'questions': [
            '面对需要使用AI的任务时，我有时会感到焦虑或压力',
            '当AI给出不确定或错误的建议时，我会感到沮丧或无助',
            '我担心频繁依赖AI会削弱我的独立判断能力'
        ]
    },
    {
        'id': 'ethical_concerns',
        'name': '风险与担忧',
        'direction': 'negative',
        'questions': [
            '我担心AI的广泛使用会带来职业不安全感或替代风险',
            '我担心AI系统可能引入偏见或产生不公平的结果',
            '我对长期依赖AI可能改变学习和工作价值观感到担忧'
        ]
    }
]

# 展平所有题目
def get_all_items():
    items_list = []
    for dim in DIMENSIONS:
        for q_text in dim['questions']:
            items_list.append({
                'dim_id': dim['id'],
                'dim_name': dim['name'],
                'direction': dim['direction'],
                'text': q_text
            })
    return items_list

ALL_ITEMS = get_all_items()
TOTAL_ITEMS = len(ALL_ITEMS)  # 24

SCALE_OPTIONS = [
    {'value': 1, 'label': '完全不同意'},
    {'value': 2, 'label': '比较不同意'},
    {'value': 3, 'label': '中立/不确定'},
    {'value': 4, 'label': '比较同意'},
    {'value': 5, 'label': '完全同意'}
]


# ============================================================
# 数据库
# ============================================================
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            response_id TEXT UNIQUE NOT NULL,
            submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            gender TEXT NOT NULL,
            grade TEXT NOT NULL,
            major_detail TEXT NOT NULL,
            ai_frequency TEXT NOT NULL,
            ai_tools TEXT DEFAULT '',
            ai_tools_other TEXT DEFAULT '',
            item_scores TEXT NOT NULL,
            negative_total REAL DEFAULT 0,
            positive_total REAL DEFAULT 0,
            negative_avg REAL DEFAULT 0,
            positive_avg REAL DEFAULT 0,
            balance_score REAL DEFAULT 0,
            balance_type TEXT DEFAULT '',
            level_label TEXT DEFAULT '',
            dimension_scores TEXT DEFAULT '{}'
        )
    ''')

    # 兼容旧表（如果有major_category列）
    try:
        conn.execute('SELECT major_category FROM responses LIMIT 1')
        # 如果存在旧列但不需要了，我们不删除它，只是忽略
    except Exception:
        pass

    conn.commit()
    conn.close()


# ============================================================
# 评分计算
# ============================================================
def calculate_scores(item_scores_dict):
    dim_scores = {}
    start_idx = 0
    for dim in DIMENSIONS:
        dim_id = dim['id']
        q_count = len(dim['questions'])
        scores = []
        for k in range(q_count):
            idx = start_idx + k
            key = str(idx)
            if key in item_scores_dict:
                scores.append(int(item_scores_dict[key]))
        dim_scores[dim_id] = {
            'total': sum(scores),
            'avg': round(sum(scores) / len(scores), 2) if scores else 0,
            'count': len(scores),
            'direction': dim['direction']
        }
        start_idx += q_count

    negative_total = sum(dim_scores[d['id']]['total'] for d in DIMENSIONS[:3])
    negative_count_m = sum(dim_scores[d['id']]['count'] for d in DIMENSIONS[:3])
    negative_avg = round(negative_total / negative_count_m, 2) if negative_count_m else 0

    positive_total = sum(dim_scores[d['id']]['total'] for d in DIMENSIONS[3:])
    positive_count_m = sum(dim_scores[d['id']]['count'] for d in DIMENSIONS[3:])
    positive_avg = round(positive_total / positive_count_m, 2) if positive_count_m else 0

    balance_score = round(positive_avg - negative_avg, 2)

    if balance_score >= 1.0:
        balance_type = '从容主导型'
        level_label = '积极体验为主'
    elif balance_score >= 0.3:
        balance_type = '轻微从容型'
        level_label = '略偏积极体验'
    elif balance_score >= -0.3:
        balance_type = '基本平衡型'
        level_label = '焦虑与从容相平衡'
    elif balance_score >= -1.0:
        balance_type = '轻微焦虑型'
        level_label = '略偏负面情绪'
    else:
        balance_type = '焦虑主导型'
        level_label = '负面情绪为主'

    return {
        'dimension_scores': dim_scores,
        'negative_total': negative_total,
        'positive_total': positive_total,
        'negative_avg': negative_avg,
        'positive_avg': positive_avg,
        'balance_score': balance_score,
        'balance_type': balance_type,
        'level_label': level_label,
        'total_items': negative_count_m + positive_count_m
    }


# ============================================================
# TXT 同步 - 简单表格格式
# ============================================================
def sync_to_txt():
    conn = get_db()
    rows = conn.execute('SELECT * FROM responses ORDER BY submit_time DESC').fetchall()
    conn.close()

    # CSV表头（制表符分隔）
    headers = ['编号', '提交时间', '性别', '年级', '专业', 'AI频率',
               '焦虑均分', '从容均分', '平衡指数', '结果类型']

    lines = ['\t'.join(headers)]

    for row in rows:
        # 简化年级显示
        grade_simple = row['grade'].replace('本科低年级（', '').replace('本科高年级（', '').replace('）', '')
        grade_simple = grade_simple.replace('硕士研究生', '硕士').replace('博士研究生', '博士')

        # 简单提取AI工具
        ai_tools_raw = row['ai_tools']
        try:
            tools_list = json.loads(ai_tools_raw) if ai_tools_raw else []
            tools_str = ';'.join(tools_list)
        except Exception:
            tools_str = ai_tools_raw[:30] if ai_tools_raw else ''
        if row['ai_tools_other']:
            tools_str += ';' + row['ai_tools_other'][:20]

        line = '\t'.join([
            row['response_id'][-12:],
            row['submit_time'][:16],
            row['gender'],
            grade_simple,
            row['major_detail'],
            row['ai_frequency'][:6],
            f"{row['negative_avg']:.2f}",
            f"{row['positive_avg']:.2f}",
            f"{row['balance_score']:+.2f}",
            row['balance_type']
        ])
        lines.append(line)

    with open(TXT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return len(rows)


# ============================================================
# Flask 路由
# ============================================================
@app.route('/')
def index():
    return render_template('index.html',
                         scale_info=SCALE_INFO,
                         demographics=DEMOGRAPHICS,
                         dimensions=DIMENSIONS,
                         all_items=ALL_ITEMS,
                         scale_options=SCALE_OPTIONS,
                         total_items=TOTAL_ITEMS)


@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.form
        response_id = datetime.datetime.now().strftime('AIW%Y%m%d%H%M%S%f')

        gender = data.get('gender', '')
        grade = data.get('grade', '')
        major_detail = data.get('major_detail', '')
        ai_frequency = data.get('ai_frequency', '')
        ai_tools = json.dumps(data.getlist('ai_tools'), ensure_ascii=False)
        ai_tools_other = data.get('ai_tools_other', '')

        item_scores = {}
        for j in range(TOTAL_ITEMS):
            key = f'item_{j}'
            val = data.get(key)
            item_scores[str(j)] = int(val) if val else 0

        results = calculate_scores(item_scores)

        conn = get_db()
        conn.execute('''
            INSERT INTO responses
            (response_id, gender, grade, major_detail,
             ai_frequency, ai_tools, ai_tools_other,
             item_scores, negative_total, positive_total,
             negative_avg, positive_avg, balance_score,
             balance_type, level_label, dimension_scores)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            response_id, gender, grade, major_detail,
            ai_frequency, ai_tools, ai_tools_other,
            json.dumps(item_scores, ensure_ascii=False),
            results['negative_total'], results['positive_total'],
            results['negative_avg'], results['positive_avg'],
            results['balance_score'],
            results['balance_type'], results['level_label'],
            json.dumps(results['dimension_scores'], ensure_ascii=False)
        ))
        conn.commit()
        conn.close()

        sync_to_txt()

        return jsonify({
            'status': 'success',
            'response_id': response_id,
            'results': results
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/result/<response_id>')
def result(response_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM responses WHERE response_id = ?',
                      (response_id,)).fetchone()
    conn.close()

    if not row:
        return "记录不存在", 404

    results = {
        'response_id': row['response_id'],
        'submit_time': row['submit_time'],
        'gender': row['gender'],
        'grade': row['grade'],
        'major_detail': row['major_detail'],
        'negative_total': row['negative_total'],
        'positive_total': row['positive_total'],
        'negative_avg': row['negative_avg'],
        'positive_avg': row['positive_avg'],
        'balance_score': row['balance_score'],
        'balance_type': row['balance_type'],
        'level_label': row['level_label'],
        'dimension_scores': json.loads(row['dimension_scores']),
        'item_scores': json.loads(row['item_scores'])
    }

    return render_template('result.html',
                         r=results,
                         scale_info=SCALE_INFO,
                         dimensions=DIMENSIONS,
                         all_items=ALL_ITEMS)


# ============================================================
# 管理员登录保护
# ============================================================
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='密码错误，请重试')
    return render_template('login.html', error=None)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin():
    conn = get_db()
    rows = conn.execute('''
        SELECT response_id, submit_time, gender, grade, major_detail,
               ai_frequency, negative_avg, positive_avg,
               balance_score, balance_type, level_label
        FROM responses ORDER BY submit_time DESC
    ''').fetchall()
    count = conn.execute('SELECT COUNT(*) as c FROM responses').fetchone()['c']
    conn.close()
    return render_template('admin.html', rows=rows, count=count, scale_info=SCALE_INFO)


@app.route('/api/stats')
def api_stats():
    conn = get_db()
    rows = conn.execute('SELECT * FROM responses').fetchall()
    conn.close()

    if not rows:
        return jsonify({'count': 0})

    balance_dist = {}
    grade_dist = {}
    gender_dist = {}
    negative_scores = []
    positive_scores = []
    balance_scores = []

    for row in rows:
        bt = row['balance_type']
        balance_dist[bt] = balance_dist.get(bt, 0) + 1

        gr = row['grade'].replace('本科低年级（', '').replace('本科高年级（', '').replace('）', '')
        gr = gr.replace('硕士研究生', '硕士').replace('博士研究生', '博士')
        grade_dist[gr] = grade_dist.get(gr, 0) + 1
        gender_dist[row['gender']] = gender_dist.get(row['gender'], 0) + 1
        negative_scores.append(row['negative_avg'])
        positive_scores.append(row['positive_avg'])
        balance_scores.append(row['balance_score'])

    avg_negative = round(sum(negative_scores) / len(negative_scores), 2)
    avg_positive = round(sum(positive_scores) / len(positive_scores), 2)
    avg_balance = round(sum(balance_scores) / len(balance_scores), 2)

    return jsonify({
        'count': len(rows),
        'balance_distribution': balance_dist,
        'grade_distribution': grade_dist,
        'gender_distribution': gender_dist,
        'avg_negative': avg_negative,
        'avg_positive': avg_positive,
        'avg_balance': avg_balance,
        'avg_balance_type': '从容主导' if avg_balance > 0 else '焦虑主导' if avg_balance < 0 else '平衡',
        'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    })


@app.route('/health')
def health():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) as c FROM responses').fetchone()['c']
    conn.close()
    return jsonify({
        'status': 'ok',
        'records': count,
        'db_size': os.path.getsize(DB_PATH) if DB_PATH.exists() else 0
    })


# ============================================================
# 生成二维码
# ============================================================
def generate_qrcode():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()

    url = f'http://{ip}:{PORT}/'
    print(f'  📡 问卷地址: {url}')

    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=6,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='#1a237e', back_color='white')
        img.save(str(QR_PATH))
        print(f'  ✅ 二维码已生成: {QR_PATH}')
    except Exception as e:
        print(f'  ⚠️ 二维码生成失败: {e}')

    return url


# ============================================================
# 启动
# ============================================================
if __name__ == '__main__':
    print('')
    print('  ╔══════════════════════════════════════════════════╗')
    print('  ║     AI辅助工作心理体验量表 (AIW-PES) v1.1        ║')
    print('  ║     高校学生AI心理影响调查系统                    ║')
    print('  ╚══════════════════════════════════════════════════╝')
    print('')

    # 可选：删除旧数据库重建新表（仅在设置 RESET_DB=1 时启用）
    if os.environ.get('RESET_DB', '') == '1':
        if DB_PATH.exists():
            os.remove(DB_PATH)
            print('  ✅ 已删除旧数据库，重建新结构')

    init_db()
    print(f'  ✅ 数据库初始化完成: {DB_PATH}')

    url = generate_qrcode()

    print(f'')
    print(f'  🌐 启动Web服务...')
    print(f'  📌 本地访问: http://127.0.0.1:{PORT}/')
    print(f'  📌 远程访问: {url}')
    print(f'  📌 管理员需访问: {url}admin/login')
    print(f'  📌 管理员密码: {ADMIN_PASSWORD}')
    print(f'')
    print(f'  ⏹️  按 Ctrl+C 停止服务')
    print(f'')
    app.run(host=HOST, port=PORT, debug=False)
