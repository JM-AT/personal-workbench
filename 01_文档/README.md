# AI 工作台（本地 · 多模型 · 桌面）

一个**纯本地运行**的 AI 工作台桌面应用，当前包含三大核心能力：

1. 💬 **智能体对话** —— 多模型可切换（OpenAI / DeepSeek / 通义千问 / Ollama 本地…），统一 OpenAI 兼容接口。
2. 📚 **知识库问答（RAG）** —— 上传 `.txt/.md/.pdf`，自动切分 + 向量化（LanceDB），基于资料作答并给出来源。
3. 📅 **每日工作安排** —— 从飞书拉取每日日程/任务（当前为可一键切换的模拟数据，接真实飞书只需填凭证）。

技术栈：**Tauri 2（桌面外壳）+ React + Vite + TypeScript（前端）+ Python FastAPI（本地后端）**。
所有数据（配置、知识库向量）都保存在你本机，不上云。

---

## 目录结构

```
ai-workbench/
├── backend/                 # Python FastAPI 本地后端
│   ├── app.py               # 路由入口（对话/知识库/日程/配置）
│   ├── config.py            # 配置读写（data/config.json）
│   ├── embeddings.py        # 可插拔嵌入：hash(离线)/fastembed/openai
│   ├── chat.py              # 多模型对话
│   ├── kb.py                # LanceDB 向量检索
│   ├── schedule.py          # 飞书日程（mock / real）
│   ├── requirements.txt
│   └── data/                # 配置与向量库（自动生成）
├── frontend/                # React + Vite + TS 前端
│   └── src/views/           # Chat / Knowledge / Schedule / Settings
└── src-tauri/               # Tauri 2 桌面外壳配置
    ├── Cargo.toml
    ├── tauri.conf.json
    ├── build.rs
    └── src/main.rs          # 启动本地后端并加载前端
```

---

## 一、本地开发运行（Web 模式，最快验证）

> 需要先安装 Python 3.11+ 与 Node 18+。

**1) 启动后端**（终端 A）

```bash
cd backend
pip install -r requirements.txt      # 安装依赖（或用自己的虚拟环境）
python app.py                        # 启动在 http://127.0.0.1:8000
```

**2) 启动前端**（终端 B）

```bash
cd frontend
npm install
npm run dev                          # 开发服务器 http://localhost:5173
```

浏览器打开 http://localhost:5173 即可使用。前端通过 Vite 代理把 `/api` 转发到后端 `:8000`。

> 知识库嵌入默认用 `hash`（纯离线、无需下载模型，演示够用）。要更高检索质量，在「模型设置 → 知识库嵌入方式」改为 `fastembed`（首次会自动下载一个小模型）。

---

## 二、配置多模型 / 填入 API Key

打开左侧 **⚙️ 模型设置**：

- 每个模型可填 `Base URL`、`模型名`、`API Key`；本地模型（Ollama）Key 可留空。
- 类型选 `OpenAI 兼容` 即可接入绝大多数厂商（DeepSeek、通义、智谱、Moonshot 等都提供 OpenAI 兼容端点）。
- 选 `Ollama 本地` 并把 `Base URL` 填 `http://localhost:11434/v1`、模型名填本地模型（如 `qwen2.5:7b`），即可完全离线对话。
- 设置 `默认模型`，对话/知识库默认走它。

---

## 三、知识库问答（RAG）

1. 在「📚 知识库问答」上传文档（`.txt/.md/.pdf`）。
2. 等待向量化完成（显示「切分 N 段」）。
3. 在下半部分提问，回答会附带「来源」文档名。

> 注意：切换嵌入方式（hash ↔ fastembed ↔ openai）后，向量维度会变化；若检索异常，请删除 `backend/data/lancedb` 目录重新上传。

---

## 四、接入真实飞书日程

当前「📅 每日安排」为模拟数据。接真实数据：

1. 在飞书开放平台创建企业自建应用，开通 **日历 / 任务** 权限，拿到 `App ID` / `App Secret`。
2. 「模型设置 → 飞书工作安排」选 `真实飞书` 并填入上述凭证。
3. 在 `backend/schedule.py` 的 `mode == "real"` 分支补全：用 `app_id/app_secret` 换 `tenant_access_token`，调用
   `https://open.feishu.cn/open-apis/calendar/v4/calendars/...` 拉取当日日程并映射为 `items` 结构返回。
   （代码里已留好 TODO 注释与返回结构。）

---

## 五、打包成桌面应用（.exe）

提供两条路线。仓库里 `backend/lib` 已内置 `pywebview` 与 `pyinstaller`，**方案 A 在本环境已实测可产出 `.exe`**。

### 方案 A（推荐，无需 Rust）：pywebview + PyInstaller

纯 Python 方案，本机只要有 Python 3.11+ 即可打包。成品是一个双击打开的桌面窗口，内嵌前端 + 本地后端（FastAPI）。

**1) 先构建前端静态资源**

```bash
cd frontend && npm install && npm run build && cd ..
```

**2) 打包**

```bash
cd backend
bash build_exe.sh
```

**3) 产物**

`backend/dist/ai-workbench/ai-workbench.exe`（连同同目录所有文件一起拷贝即可运行）。

- **运行要求**：Windows 需 **WebView2 运行时**（Win10/11 一般已自带；没有则从微软下载运行时）。
- **数据位置**：配置与知识库向量保存在 exe 所在目录的 `data/` 下，可随身带走。
- **无界面校验**：设置环境变量 `AIWB_HEADLESS=1` 再运行，仅起本地服务（不弹窗），便于自动化测试 `/api`。

### 方案 B（原方案，需 Rust）：Tauri 2

若想要更小安装包 / 原生体验，可用原本的 Tauri 外壳（`src-tauri/`）。本机需准备：

- Rust 工具链（https://rustup.rs ）
- C/C++ 链接器（Visual Studio 构建工具，必需！）
- WebView2 运行时、Node 22+

```bash
cd frontend && npm install && npm run build && cd ..
npm install && npx tauri build     # 首次会下载并编译 Rust 依赖，较慢
```

> 注意：Tauri 打包在本沙箱内无法执行（缺 Rust 与链接器），需你在本机运行。图标：`npx tauri icon 你的图.png` 生成 `src-tauri/icons/*`。

---

## 六、已知说明

- 本仓库在「无 Rust 的沙箱」中开发：已用 Web 模式完整跑通并验证；桌面 `.exe` 已通过第五节「方案 A（pywebview + PyInstaller）」在本环境实测产出，双击即用（仅需系统具备 WebView2）。如需更小安装包可用第五节「方案 B（Tauri）」在你本机打包。
- 对话默认非流式（一次性返回），如需打字机效果可在 `backend/app.py` 改为 SSE。
- 所有数据均存于本地 `backend/data/`，删除该目录即可清空。
