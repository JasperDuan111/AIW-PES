#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI辅助工作心理体验量表 - 数据可视化工具
从 responses.txt 或 survey.db 读取数据，生成分析图表
"""

import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# ============================================================
# 配置
# ============================================================
BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / 'survey.db'
TXT_PATH = BASE_DIR / 'responses.txt'
OUTPUT_DIR = BASE_DIR / 'charts'

# 尝试设置中文字体
def setup_chinese_font():
    """查找并设置中文字体"""
    font_paths = [
        '/share/home/zhaost/CP/IFPA/static/NotoSansSC.ttf',
        '/share/home/zhaost/CP/IFPA/static/NotoSansSC.otf',
        '/share/home/zhaost/CP/IFPA/static/ipaexg.ttf',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                prop = fm.FontProperties(fname=fp)
                plt.rcParams['font.family'] = prop.get_name()
                fm.fontManager.addfont(fp)
                print(f'  使用字体: {fp}')
                return prop
            except Exception:
                continue
    # Fallback: list available CJK-capable fonts
    for f in fm.findSystemFonts():
        try:
            prop = fm.FontProperties(fname=f)
            name = prop.get_name().lower()
            if any(kw in name for kw in ['noto', 'cjk', 'wqy', 'droid', 'simsun', 'simhei', 'ipaex', 'source han']):
                plt.rcParams['font.family'] = prop.get_name()
                fm.fontManager.addfont(f)
                print(f'  使用字体: {f}')
                return prop
        except Exception:
            continue
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    print('  ⚠️ 未找到中文字体，使用 DejaVu Sans（中文将显示为方框）')
    print('  💡 可通过 pip install matplotlib-fontja 安装日文字体（可显示部分中文）')
    return None

FONT_PROP = setup_chinese_font()

# 配色方案
COLORS = {
    'negative': '#e74c3c',
    'positive': '#2ecc71',
    'neutral': '#f39c12',
    'primary': '#667eea',
    'secondary': '#764ba2',
    'gradient_neg': ['#ffcdd2', '#ef9a9a', '#ef5350', '#e53935', '#c62828'],
    'gradient_pos': ['#c8e6c9', '#a5d6a7', '#66bb6a', '#43a047', '#2e7d32'],
}


def get_data_from_db():
    """从数据库获取所有记录"""
    if not DB_PATH.exists():
        print(f'⚠️  数据库不存在: {DB_PATH}')
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM responses ORDER BY submit_time').fetchall()
    conn.close()
    return rows


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 图表1: 平衡类型分布饼图
# ============================================================
def chart_balance_distribution(rows):
    """平衡类型分布"""
    dist = {}
    for row in rows:
        bt = row['balance_type']
        dist[bt] = dist.get(bt, 0) + 1

    labels = list(dist.keys())
    sizes = list(dist.values())
    colors_pie = []
    for l in labels:
        if '从容' in l:
            colors_pie.append(COLORS['positive'])
        elif '焦虑' in l:
            colors_pie.append(COLORS['negative'])
        else:
            colors_pie.append(COLORS['neutral'])

    fig, ax = plt.subplots(figsize=(10, 7))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        colors=colors_pie, startangle=90,
        textprops={'fontsize': 12},
        pctdistance=0.75, labeldistance=1.15
    )
    for at in autotexts:
        at.set_fontsize(11)
        at.set_fontweight('bold')

    centre_circle = plt.Circle((0, 0), 0.55, fc='white')
    fig.gca().add_artist(centre_circle)
    ax.text(0, 0, f'共 {len(rows)} 人', ha='center', va='center',
            fontsize=16, fontweight='bold', color='#333')

    ax.set_title('高校学生AI心理平衡类型分布', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    path = OUTPUT_DIR / '01_balance_distribution.png'
    plt.savefig(str(path), dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  ✅ 图表已生成: {path.name}')
    return path


# ============================================================
# 图表2: 焦虑 vs 从容 均分对比柱状图
# ============================================================
def chart_avg_comparison(rows):
    """总体焦虑与从容均分对比"""
    neg_avgs = [row['negative_avg'] for row in rows]
    pos_avgs = [row['positive_avg'] for row in rows]

    avg_neg = np.mean(neg_avgs)
    avg_pos = np.mean(pos_avgs)

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(['焦虑/压力指数', '轻松/从容指数'],
                  [avg_neg, avg_pos],
                  color=[COLORS['negative'], COLORS['positive']],
                  width=0.5, edgecolor='white', linewidth=1.5)

    for bar, val in zip(bars, [avg_neg, avg_pos]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{val:.2f}', ha='center', va='bottom', fontsize=14, fontweight='bold')

    ax.set_ylim(0, 5.5)
    ax.set_ylabel('平均得分', fontsize=13)
    ax.set_title(f'高校学生AI心理体验总体对比 (n={len(rows)})',
                 fontsize=15, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3)

    # 注释
    diff = avg_pos - avg_neg
    diff_text = f'从容指数高于焦虑指数 {diff:+.2f} 分' if diff > 0 else f'焦虑指数高于从容指数 {diff:+.2f} 分'
    ax.text(0.5, -0.12, diff_text, transform=ax.transAxes, ha='center',
            fontsize=12, color='#555', style='italic')

    plt.tight_layout()
    path = OUTPUT_DIR / '02_avg_comparison.png'
    plt.savefig(str(path), dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  ✅ 图表已生成: {path.name}')
    return path


# ============================================================
# 图表3: 各维度均分雷达图
# ============================================================
def chart_dimension_radar(rows):
    """六维度剖面雷达图"""
    dim_names = ['技术压力\n与适应困难', '能力焦虑\n与替代担忧', '心理社会\n影响',
                 'AI效能感\n与掌控力', '积极体验\n与效率提升', '综合从容\n与乐观态度']
    dim_ids = ['tech_stress', 'competence_anxiety', 'psychosocial_impact',
               'ai_efficacy', 'positive_experience', 'composure_optimism']

    # 计算各维度平均分
    avg_scores = []
    for dim_id in dim_ids:
        scores = []
        for row in rows:
            ds = json.loads(row['dimension_scores'])
            if dim_id in ds:
                scores.append(ds[dim_id].get('avg', 0))
        avg_scores.append(np.mean(scores) if scores else 0)

    # 雷达图
    angles = np.linspace(0, 2 * np.pi, len(dim_names), endpoint=False).tolist()
    scores_closed = avg_scores + [avg_scores[0]]
    angles_closed = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))

    ax.plot(angles_closed, scores_closed, 'o-', linewidth=2.5,
            color=COLORS['primary'], markersize=8, label='平均分')
    ax.fill(angles_closed, scores_closed, alpha=0.15, color=COLORS['primary'])

    # 显示刻度
    ax.set_xticks(angles)
    ax.set_xticklabels(dim_names, fontsize=11, fontweight='bold')
    ax.set_ylim(0, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=9, color='#888')
    ax.grid(True, alpha=0.3)

    # 标注分数
    for i, (angle, score) in enumerate(zip(angles, avg_scores)):
        ax.text(angle, score + 0.3, f'{score:.2f}', ha='center', fontsize=10, fontweight='bold')

    ax.set_title(f'六维度心理剖面图 (n={len(rows)})', fontsize=15, fontweight='bold', pad=25)

    plt.tight_layout()
    path = OUTPUT_DIR / '03_dimension_radar.png'
    plt.savefig(str(path), dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  ✅ 图表已生成: {path.name}')
    return path


# ============================================================
# 图表4: 不同年级的焦虑/从容对比
# ============================================================
def chart_grade_comparison(rows):
    """各年级群体的焦虑与从容对比"""
    grade_map = {}
    for row in rows:
        gr = row['grade'].replace('本科低年级（', '').replace('本科高年级（', '').replace('）', '')
        gr = gr.replace('硕士研究生', '硕士').replace('博士研究生', '博士')
        if gr not in grade_map:
            grade_map[gr] = {'neg': [], 'pos': []}
        grade_map[gr]['neg'].append(row['negative_avg'])
        grade_map[gr]['pos'].append(row['positive_avg'])

    grades = list(grade_map.keys())
    neg_means = [np.mean(grade_map[g]['neg']) for g in grades]
    pos_means = [np.mean(grade_map[g]['pos']) for g in grades]

    x = np.arange(len(grades))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width/2, neg_means, width, label='焦虑/压力指数',
                   color=COLORS['negative'], alpha=0.85)
    bars2 = ax.bar(x + width/2, pos_means, width, label='轻松/从容指数',
                   color=COLORS['positive'], alpha=0.85)

    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.05, f'{h:.2f}',
                ha='center', va='bottom', fontsize=9, color=COLORS['negative'])
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.05, f'{h:.2f}',
                ha='center', va='bottom', fontsize=9, color=COLORS['positive'])

    ax.set_xticks(x)
    ax.set_xticklabels(grades, fontsize=11)
    ax.set_ylim(0, 5.5)
    ax.set_ylabel('平均得分', fontsize=12)
    ax.set_title('不同年级群体的AI心理体验对比', fontsize=15, fontweight='bold', pad=15)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    path = OUTPUT_DIR / '04_grade_comparison.png'
    plt.savefig(str(path), dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  ✅ 图表已生成: {path.name}')
    return path


# ============================================================
# 图表5: 各专业大类的平衡指数分布
# ============================================================
def chart_major_comparison(rows):
    """各专业的平衡指数"""
    major_map = {}
    for row in rows:
        mc = row.get('major_detail', '未填写')[:10]  # 用专业名称前10字
        if mc not in major_map:
            major_map[mc] = []
        major_map[mc].append(row['balance_score'])

    majors = list(major_map.keys())
    means = [np.mean(major_map[m]) for m in majors]
    stds = [np.std(major_map[m]) for m in majors]

    # 按值排序
    sorted_idx = np.argsort(means)
    majors_sorted = [majors[i] for i in sorted_idx]
    means_sorted = [means[i] for i in sorted_idx]
    stds_sorted = [stds[i] for i in sorted_idx]

    colors_bar = [COLORS['positive'] if m > 0 else COLORS['negative'] for m in means_sorted]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(majors_sorted, means_sorted, xerr=stds_sorted,
                   color=colors_bar, alpha=0.85, edgecolor='white', linewidth=1.2,
                   capsize=5, height=0.6)

    for bar, val in zip(bars, means_sorted):
        offset = 0.1 if val >= 0 else -0.1
        ha = 'left' if val >= 0 else 'right'
        ax.text(bar.get_width() + offset if val >= 0 else bar.get_width() + offset,
                bar.get_y() + bar.get_height()/2,
                f'{val:+.2f}', va='center', ha=ha, fontsize=10, fontweight='bold')

    ax.axvline(x=0, color='#333', linewidth=1.5, linestyle='-')
    ax.set_xlabel('心理平衡指数 (正=从容主导, 负=焦虑主导)', fontsize=12)
    ax.set_title('不同专业的AI心理平衡指数对比', fontsize=15, fontweight='bold', pad=15)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    path = OUTPUT_DIR / '05_major_comparison.png'
    plt.savefig(str(path), dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  ✅ 图表已生成: {path.name}')
    return path


# ============================================================
# 图表6: 平衡指数散点分布
# ============================================================
def chart_balance_scatter(rows):
    """每个个体的平衡指数散点图（带分类色）"""
    balance_scores = [row['balance_score'] for row in rows]
    indices = list(range(1, len(rows) + 1))

    colors_scatter = []
    for bs in balance_scores:
        if bs >= 1.0:
            colors_scatter.append('#2e7d32')
        elif bs >= 0.3:
            colors_scatter.append('#66bb6a')
        elif bs >= -0.3:
            colors_scatter.append('#fdd835')
        elif bs >= -1.0:
            colors_scatter.append('#ef5350')
        else:
            colors_scatter.append('#c62828')

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.scatter(indices, balance_scores, c=colors_scatter, s=40, alpha=0.7, edgecolors='white', linewidth=0.5)

    ax.axhline(y=1.0, color='#2e7d32', linestyle='--', alpha=0.5, linewidth=1)
    ax.axhline(y=0.3, color='#66bb6a', linestyle='--', alpha=0.3, linewidth=1)
    ax.axhline(y=0, color='#333', linestyle='-', linewidth=1.5)
    ax.axhline(y=-0.3, color='#ef5350', linestyle='--', alpha=0.3, linewidth=1)
    ax.axhline(y=-1.0, color='#c62828', linestyle='--', alpha=0.5, linewidth=1)

    ax.set_xlabel('答卷编号 (按时间顺序)', fontsize=12)
    ax.set_ylabel('心理平衡指数', fontsize=12)
    ax.set_title('个体心理平衡指数分布 (n={})'.format(len(rows)), fontsize=15, fontweight='bold', pad=15)
    ax.grid(alpha=0.2)

    # 区域标注
    ax.text(len(rows)*0.95, 1.3, '从容主导', fontsize=9, color='#2e7d32', ha='right')
    ax.text(len(rows)*0.95, -1.3, '焦虑主导', fontsize=9, color='#c62828', ha='right')
    ax.text(len(rows)*0.95, 0.5, '轻微从容', fontsize=9, color='#66bb6a', ha='right')
    ax.text(len(rows)*0.95, -0.5, '轻微焦虑', fontsize=9, color='#ef5350', ha='right')

    plt.tight_layout()
    path = OUTPUT_DIR / '06_balance_scatter.png'
    plt.savefig(str(path), dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  ✅ 图表已生成: {path.name}')
    return path


# ============================================================
# 生成报告
# ============================================================
def generate_report(rows, chart_paths):
    """生成分析报告HTML"""
    neg_avgs = [r['negative_avg'] for r in rows]
    pos_avgs = [r['positive_avg'] for r in rows]
    bal_scores = [r['balance_score'] for r in rows]

    total = len(rows)
    mean_neg = np.mean(neg_avgs)
    mean_pos = np.mean(pos_avgs)
    mean_bal = np.mean(bal_scores)
    std_bal = np.std(bal_scores)

    # 统计各类型占比
    type_count = {}
    for r in rows:
        bt = r['balance_type']
        type_count[bt] = type_count.get(bt, 0) + 1

    # 年级分布
    grade_count = {}
    for r in rows:
        gr = r['grade'].replace('本科低年级（', '').replace('本科高年级（', '').replace('）', '')
        grade_count[gr] = grade_count.get(gr, 0) + 1

    report = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>AI心理体验分析报告</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
               background: #f5f7fb; color: #333; padding: 30px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ font-size: 24px; color: #1a237e; text-align: center; margin-bottom: 8px; }}
        .subtitle {{ text-align: center; color: #888; margin-bottom: 30px; font-size: 14px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 12px; margin-bottom: 30px; }}
        .summary-card {{ background: #fff; border-radius: 12px; padding: 20px; text-align: center;
                         box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
        .summary-card .num {{ font-size: 32px; font-weight: 700; }}
        .summary-card .label {{ font-size: 13px; color: #888; margin-top: 4px; }}
        .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
        .chart-item {{ background: #fff; border-radius: 16px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
        .chart-item.full {{ grid-column: 1 / -1; }}
        .chart-item h3 {{ font-size: 14px; color: #555; margin-bottom: 12px; text-align: center; }}
        .chart-item img {{ width: 100%; border-radius: 8px; }}
        table {{ width: 100%; background: #fff; border-radius: 12px; overflow: hidden;
                 box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-collapse: collapse; margin-bottom: 30px; }}
        th {{ background: #f8f9ff; padding: 10px 14px; font-size: 12px; color: #666; text-align: left; }}
        td {{ padding: 8px 14px; font-size: 13px; border-top: 1px solid #f0f0f0; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 20px; }}
        @media (max-width: 768px) {{ .chart-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 AI辅助工作心理体验分析报告</h1>
        <p class="subtitle">生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

        <div class="summary">
            <div class="summary-card">
                <div class="num" style="color:#1a237e;">{total}</div>
                <div class="label">总答卷数</div>
            </div>
            <div class="summary-card">
                <div class="num" style="color:#2e7d32;">{mean_pos:.2f}</div>
                <div class="label">平均从容指数</div>
            </div>
            <div class="summary-card">
                <div class="num" style="color:#c62828;">{mean_neg:.2f}</div>
                <div class="label">平均焦虑指数</div>
            </div>
            <div class="summary-card">
                <div class="num" style="color:{"#2e7d32" if mean_bal > 0 else "#c62828"};">{mean_bal:+.2f}</div>
                <div class="label">平均平衡指数</div>
            </div>
        </div>

        <div class="chart-grid">
            <div class="chart-item">
                <h3>📈 心理平衡类型分布</h3>
                <img src="charts/01_balance_distribution.png" alt="平衡类型分布">
            </div>
            <div class="chart-item">
                <h3>📊 焦虑 vs 从容总体对比</h3>
                <img src="charts/02_avg_comparison.png" alt="总体对比">
            </div>
            <div class="chart-item">
                <h3>🎯 六维度心理剖面图</h3>
                <img src="charts/03_dimension_radar.png" alt="维度雷达图">
            </div>
            <div class="chart-item">
                <h3>🎓 不同年级对比</h3>
                <img src="charts/04_grade_comparison.png" alt="年级对比">
            </div>
            <div class="chart-item">
                <h3>📚 不同专业对比</h3>
                <img src="charts/05_major_comparison.png" alt="专业对比">
            </div>
            <div class="chart-item">
                <h3>👤 个体分布散点图</h3>
                <img src="charts/06_balance_scatter.png" alt="个体分布">
            </div>
        </div>

        <h2 style="font-size:18px; margin-bottom:12px;">📋 类型分布详情</h2>
        <table>
            <tr><th>心理平衡类型</th><th>人数</th><th>占比</th></tr>
''' + '\n'.join(f'            <tr><td>{k}</td><td>{v}</td><td>{v/total*100:.1f}%</td></tr>' for k, v in sorted(type_count.items(), key=lambda x: -x[1])) + '''
        </table>

        <h2 style="font-size:18px; margin-bottom:12px;">🎓 年级分布</h2>
        <table>
            <tr><th>年级</th><th>人数</th><th>占比</th></tr>
''' + '\n'.join(f'            <tr><td>{k}</td><td>{v}</td><td>{v/total*100:.1f}%</td></tr>' for k, v in sorted(grade_count.items(), key=lambda x: -x[1])) + '''
        </table>

        <div class="footer">
            <p>AI辅助工作心理体验量表 (AIW-PES) · 数据分析报告</p>
            <p>本报告由 visualize.py 自动生成</p>
        </div>
    </div>
</body>
</html>'''

    report_path = BASE_DIR / 'report.html'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f'  ✅ 分析报告已生成: {report_path}')
    return report_path


# ============================================================
# 主函数
# ============================================================
def main():
    print('')
    print('  ╔══════════════════════════════════════════════╗')
    print('  ║   AI心理体验数据可视化工具                     ║')
    print('  ║   生成分析图表与报告                          ║')
    print('  ╚══════════════════════════════════════════════╝')
    print('')

    # 检查数据
    rows = get_data_from_db()
    if not rows:
        print('  ⚠️  数据库无数据，无法生成图表')
        print(f'  💡 请先运行 app.py 收集问卷数据')
        return

    print(f'  📊 共读取 {len(rows)} 条问卷记录')
    if len(rows) < 3:
        print('  ⚠️  数据量较少（<3条），部分图表可能效果有限')

    ensure_output_dir()

    # 生成所有图表
    print('')
    print('  🔨 生成图表...')
    print('')

    chart_funcs = [
        ('平衡类型分布', chart_balance_distribution),
        ('焦虑/从容对比', chart_avg_comparison),
        ('维度雷达图', chart_dimension_radar),
        ('年级对比', chart_grade_comparison),
        ('专业对比', chart_major_comparison),
        ('个体分布', chart_balance_scatter),
    ]

    chart_paths = []
    for name, func in chart_funcs:
        try:
            print(f'  🎨 正在生成: {name}')
            path = func(rows)
            chart_paths.append(path)
        except Exception as e:
            print(f'  ❌ {name} 生成失败: {e}')
            import traceback
            traceback.print_exc()

    # 生成报告
    print('')
    print('  📄 生成分析报告...')
    report_path = generate_report(rows, chart_paths)

    print('')
    print(f'  ✅ 全部完成！共生成 {len(chart_paths)} 张图表 + 1 份报告')
    print(f'  📁 图表目录: {OUTPUT_DIR}/')
    print(f'  📁 报告文件: {report_path}')
    print('')


if __name__ == '__main__':
    main()
