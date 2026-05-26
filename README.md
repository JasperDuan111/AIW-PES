# AI辅助工作心理体验量表 (AIW-PES) v1.1

> 高校学生AI心理影响调查系统
> 主题：人工智能辅助工作，给人带来的是负面情绪（焦虑/压力）还是积极体验（轻松/从容）

---

## 📦 压缩包内容

| 文件 | 说明 |
|------|------|
| `setup.sh` | **⭐ 一键启动脚本（建议先看这个）** |
| `app.py` | Flask Web主程序（问卷+数据库+后台管理） |
| `visualize.py` | 数据可视化脚本（生成6张图表+分析报告） |
| `run.sh` | 服务管理脚本（start/stop/status/logs） |
| `daemonize.py` | 后台保活启动脚本 |
| `templates/` | 前端HTML模板（index.html/result.html/admin.html/login.html） |
| `static/` | 静态资源（二维码、字体等） |
| `README.md` | 本说明文档 |
| `Reference1.md` | 参考量表A：AIPI-US（25题6维度） |
| `Reference2.md` | 参考量表B：AIAS-CS-40（40题8维度） |

---

## 🚀 快速启动

### 第一步：Windows 环境准备

如果你在 Windows 上运行，不使用 `setup.sh`，建议直接用 Conda 或 Python 虚拟环境启动。

# 创建并激活 Conda 虚拟环境
conda create -n aiw-pes python=3.10 -y
conda activate aiw-pes

# 安装依赖
pip install -r requirements.txt

# 启动服务（默认端口 8650）
python app.py

# 如果想指定端口
$env:APP_PORT = "8080"
python app.py
```

启动后，程序会自动完成：
- ✅ 检查 Python 环境
- ✅ 初始化 SQLite 数据库
- ✅ 生成二维码图片
- ✅ 启动问卷服务
- ✅ 打印本地访问地址和二维码地址

### 第二步：打开网页

启动后，在浏览器打开脚本输出的地址：

```
http://服务器IP:8650/
```

例如：`http://192.168.1.100:8650/`

### 第三步：开始收集数据

- 手机扫码（`static/qrcode.png`）也可访问
- 答卷数据自动保存到 SQLite 数据库和 TXT 文件

---

## 📊 查看数据

### 1. 实时数据（TXT表格）

```powershell
Get-Content responses.txt
```

格式为制表符分隔表格，可直接复制到 Excel/WPS：
```
编号    提交时间    性别    年级    专业    AI频率  焦虑均分  从容均分  平衡指数  结果类型
AIW20...  2025-06-01  男    博士    凝聚态物理  每天使用  3.50  4.20  +0.70  轻微从容型
```

### 2. 图表可视化

```powershell
python visualize.py
```

生成6张分析图表 + 1份HTML报告：
- `charts/01_balance_distribution.png` — 平衡类型分布饼图
- `charts/02_avg_comparison.png` — 焦虑vs从容对比柱状图
- `charts/03_dimension_radar.png` — 六维度雷达图
- `charts/04_grade_comparison.png` — 不同年级对比
- `charts/05_major_comparison.png` — 不同专业对比
- `charts/06_balance_scatter.png` — 个体分布散点图
- `report.html` — 综合分析报告

双击 `report.html` 即可在浏览器查看所有图表。

### 3. 管理面板

访问管理后台查看所有答卷数据：

```
http://服务器IP:8650/admin/login
```

**🔑 管理员密码：`123456`**

在管理面板可以：
- 查看每份答卷的详细数据
- 按类型筛选（从容主导/平衡型/焦虑主导）
- 搜索特定专业或年级
- 查看统计数据摘要

### 4. 数据API

```
http://服务器IP:8650/api/stats
```

返回 JSON 格式统计数据，可用于二次开发。

---

## 🔧 常用命令

```powershell
# 查看服务是否运行
Get-Process python

# 查看当前控制台输出日志
# 如果你是前台运行 app.py，直接看当前终端窗口即可

# 停止服务
# 在运行 app.py 的终端里按 Ctrl+C

# 重新生成二维码
python -c "from app import generate_qrcode; generate_qrcode()"

# 手动同步 TXT
python -c "from app import sync_to_txt; sync_to_txt()"
```

---

## 🧠 量表说明

### 题目结构
- **12题 · 4维度（精简版）**，5点李克特量表（1=完全不同意 → 5=完全同意）
- **答题过程**：不显示维度标签，保护作答客观性
- **结果页**：展示维度剖面与正/负面指标，便于快速解读

### 维度构成（精简版）

| 类别 | 维度 | 题数 |
|------|------|:----:|
| 😰 负面（情绪/顾虑） | 情绪反应与压力 | 3题 |
| 😰 负面（伦理/长期） | 伦理与长期顾虑 | 3题 |
| 😊 正面（影响/能力） | 感知的学习/工作影响 | 3题 |
| 😊 正面（能力/掌控） | 掌控感与能力 | 3题 |

### 核心指标

- **负面均分（焦虑指数）** = 平均(`情绪反应与压力.avg`, `伦理与长期顾虑.avg`)，范围 1～5（值越大表示越强的负面/顾虑）
- **正面均分（从容/效能指数）** = 平均(`感知的学习/工作影响.avg`, `掌控感与能力.avg`)，范围 1～5（值越大表示越强的正面体验/掌控感）
- **心理平衡指数** = 正面均分 − 负面均分，范围大致为 -4 ～ +4（正数代表偏向正面体验）

推荐结果分类（可按需要微调阈值）：

| 范围 | 类型 | 含义 |
|:----:|------|------|
| >= +0.8 | 明显从容型 | 明显偏向正面体验和掌控感 |
| +0.3 ~ +0.8 | 轻微从容型 | 略偏正面体验 |
| -0.3 ~ +0.3 | 基本平衡型 | 正负面体验相对均衡 |
| -0.8 ~ -0.3 | 轻微焦虑型 | 略偏负面情绪或顾虑 |
| <= -0.8 | 明显焦虑/顾虑型 | 明显偏向负面情绪或长期顾虑 |

实现说明：在数据库中，`dimension_scores` 字段保存各维度的总分与均分（JSON 格式），统计时直接读取对应维度的 `avg` 字段计算上述指标；在前端结果页显示时，建议同时呈现每个维度的 `avg` 及总体 `balance`，并给出简短的解释与建议。

---

## 📋 数据存储

- **数据库**：`survey.db`（SQLite，所有原始数据）
- **文本记录**：`responses.txt`（制表符分隔，可直接用Excel打开）
- 每份答卷提交后自动同步到 TXT 文件

---

## 🔒 隐私说明

- 本问卷采用匿名方式
- 数据仅用于学术研究
- 本量表为研究工具，不构成临床诊断

---

## 🚀 Railway 部署

如果你想让别人一直能扫码访问，而不依赖本地电脑是否开机，推荐部署到 Railway。

### 部署前准备

- 已包含 `requirements.txt`
- 已包含 `Procfile`
- `app.py` 已支持云平台常见的 `PORT` 环境变量
- 如需重置数据库，设置环境变量 `RESET_DB=1`，不要在生产环境默认开启

### Railway 启动命令

Railway 会读取 `Procfile`，启动命令如下：

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

### Railway 部署步骤

1. 把项目推送到 GitHub。
2. 在 Railway 新建项目，选择从 GitHub 导入。
3. Railway 自动识别 Python 项目后，安装依赖并使用 `Procfile` 启动。
4. 在 Railway 的 Variables 里设置可选变量：`RESET_DB=0`。
5. 部署完成后，Railway 会给你一个公网域名，二维码直接指向这个域名即可。

### 二维码怎么用

把 `static/qrcode.png` 对应的网址换成 Railway 提供的公网地址，重新生成二维码后，手机扫码就能访问。

### 数据保存提醒

- 本地停止后，Railway 上的服务仍然在线，所以别人还能继续提交。
- 如果你把服务重新部署到新环境，SQLite 文件可能不会自动迁移；需要把 `survey.db` 另行备份或改成云数据库。

---

## 📝 版本历史

| 版本 | 日期 | 说明 |
|:----:|:----:|------|
| v1.0 | 2025-05 | 初始版本，24题6维度 |
| v1.1 | 2025-05 | 取消专业大类、隐藏答题维度标签、TXT改为表格格式、管理员密码保护 |
