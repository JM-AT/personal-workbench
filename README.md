# 个人工作台（AI 工作台 · 本地多模型桌面应用）

一个**纯本地运行**的 AI 工作台桌面应用，所有数据（配置、知识库向量）都保存在你本机，不上云。

## 核心功能

1. 💬 **智能体对话** —— 多模型可切换（OpenAI / DeepSeek / 通义千问 / Ollama 本地…），统一 OpenAI 兼容接口
2. 📚 **知识库问答（RAG）** —— 上传 `.txt/.md/.pdf`，自动切分 + 向量化（LanceDB），基于资料作答并给出来源
3. 📅 **每日工作安排** —— 从飞书拉取每日日程/任务（当前为可一键切换的模拟数据，接真实飞书只需填凭证）

## 技术栈

**Tauri 2（桌面外壳）+ React + Vite + TypeScript（前端）+ Python FastAPI（本地后端）**

## 目录结构

```
个人工作台/
├── 01_文档/              # 项目文档与 PyInstaller 打包配置
│   ├── README.md         # 详细开发文档
│   └── ai-workbench.spec
├── 02_前端源码/           # React + Vite + TypeScript 前端
│   ├── src/views/        # Chat / Knowledge / Roles / Schedule / Connectors / Settings
│   └── src/api.ts
├── 03_后端源码/           # Python FastAPI 本地后端
│   ├── app.py            # 路由入口（对话/知识库/日程/配置）
│   ├── chat.py           # 多模型对话
│   ├── kb.py             # LanceDB 向量检索
│   ├── embeddings.py     # 可插拔嵌入：hash(离线)/fastembed/openai
│   ├── schedule.py       # 飞书日程（mock / real）
│   └── requirements.txt
└── 04_桌面外壳/           # Tauri 2 桌面外壳配置
    ├── Cargo.toml
    ├── tauri.conf.json
    └── src/main.rs       # 启动本地后端并加载前端
```

> 注：`05_打包产物`、`06_依赖`、运行时目录等大体积内容不纳入版本管理，按下方步骤可随时在本地重新构建。

---

## 一、下载本仓库

**方式 1：Git 克隆（推荐）**

```bash
git clone https://github.com/JM-AT/个人工作台.git
cd 个人工作台
```

**方式 2：下载 ZIP**

点击仓库页面绿色 **`<> Code`** 按钮 → **`Download ZIP`**，解压到任意目录即可。

---

## 二、本地运行（Web 模式，最快上手）

> 前置要求：Python 3.11+ 与 Node.js 18+

**1）启动后端**（终端 A）

```bash
cd 03_后端源码
pip install -r requirements.txt    # 建议先创建虚拟环境
python app.py                      # 启动在 http://127.0.0.1:8000
```

**2）启动前端**（终端 B）

```bash
cd 02_前端源码
npm install
npm run dev                        # 开发服务器 http://localhost:5173
```

浏览器打开 **http://localhost:5173** 即可使用。前端通过 Vite 代理把 `/api` 请求转发到后端 `:8000`。

> 知识库嵌入默认用 `hash`（纯离线、无需下载模型）。要更高检索质量，在「模型设置 → 知识库嵌入方式」改为 `fastembed`（首次会自动下载一个小模型）。

---

## 三、配置多模型 / 填入 API Key

打开左侧 **⚙️ 模型设置**：

- 每个模型可填 `Base URL`、`模型名`、`API Key`；本地模型（Ollama）Key 可留空
- 类型选 `OpenAI 兼容` 即可接入绝大多数厂商（DeepSeek、通义、智谱、Moonshot 等都提供 OpenAI 兼容端点）
- 选 `Ollama 本地`，`Base URL` 填 `http://localhost:11434/v1`、模型名填本地模型（如 `qwen2.5:7b`），即可完全离线对话
- 设置 `默认模型`，对话/知识库默认走它

---

## 四、知识库问答（RAG）

1. 在「📚 知识库问答」上传文档（`.txt/.md/.pdf`）
2. 等待向量化完成（显示「切分 N 段」）
3. 在下半部分提问，回答会附带「来源」文档名

> 切换嵌入方式（hash ↔ fastembed ↔ openai）后向量维度会变化；若检索异常，删除 `03_后端源码/data/lancedb` 目录重新上传即可。

---

## 五、打包成桌面应用（.exe）

### 方案 A（推荐，无需 Rust）：pywebview + PyInstaller

**1）先构建前端静态资源**

```bash
cd 02_前端源码 && npm install && npm run build && cd ..
```

**2）打包**

```bash
cd 03_后端源码
bash build_exe.sh
```

**3）产物**

`03_后端源码/dist/ai-workbench/ai-workbench.exe`（连同同目录所有文件一起拷贝即可运行）。

- **运行要求**：Windows 需 **WebView2 运行时**（Win10/11 一般已自带，没有则从微软官网下载）
- **数据位置**：配置与知识库向量保存在 exe 所在目录的 `data/` 下，可随身带走
- **无界面校验**：设置环境变量 `AIWB_HEADLESS=1` 再运行，仅启动本地服务（不弹窗），便于自动化测试 `/api`

### 方案 B（需 Rust）：Tauri 2

若想要更小安装包 / 原生体验，可用 Tauri 外壳（`04_桌面外壳/`）。本机需准备：

- Rust 工具链（https://rustup.rs ）
- C/C++ 链接器（Visual Studio 构建工具，必需）
- WebView2 运行时、Node 18+

```bash
cd 02_前端源码 && npm install && npm run build && cd ..
npm install && npx tauri build
```

---

## 六、已知说明

- 对话默认非流式（一次性返回），如需打字机效果可在 `03_后端源码/app.py` 改为 SSE
- 所有数据均存于本地 `03_后端源码/data/`，删除该目录即可清空
- 接入真实飞书日程的方法见 `01_文档/README.md` 第四节
