# nsp_pack_gui

> 把「转换器输出的 game 目录」一键打包成 Switch 可安装的 `.nsp`。

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)]()
[![Output](https://img.shields.io/badge/output-.nsp-orange)]()

打包器**内置引擎骨架**（exefs 引擎 + romfs 运行库 + 任天堂 logo + 占位图标），开箱即用，你只需要指定 game 目录、填好标题，点一下就能出包。

---

## 特性

| 能力 | 说明 |
|---|---|
| 引擎骨架内置 | 工具自带了通用引擎（已修崩溃）、运行库、logo、占位图标，不用再单独找 |
| 一键打包 | 点「打包 NSP」自动完成：复制骨架 → 放入游戏内容 → 替换图标 / 引擎 → 调用 hacbrewpack |
| 图标自定义 | 可指定一个 256×256 的 JPEG 作为游戏图标；留空则用占位图标 |
| 引擎可选替换 | 换内核时可指定一个 NSO，覆盖内置引擎 |
| titleid 校验 | 自动检查是否 16 位十六进制，防止填错 |
| 实时日志 | 显示完整打包过程，出错可定位 |

一个 `.nsp` 里装了什么（这些都已内置，不用你操心）：

```text
xxx.nsp
├── exefs/main            ← 引擎可执行文件（已内置）
├── exefs/main.npdm       ← 程序元数据（已内置）
├── romfs/Contents/game/  ← ★游戏内容（你指定的 game 目录）
├── romfs/Contents/renpy/ ← 引擎运行库（已内置）
├── control/              ← 图标 + NACP（已内置，图标可换）
└── logo/                 ← Nintendo Logo（已内置）
```

---

## 快速开始

```bash
# 1. 打开打包工具
py packer/nsp_pack_gui.py
```

打开后：

1. 「游戏目录」点浏览，选转换器输出的 game 目录（例如 `.../输出/game`）。
2. 「Title ID」填一个全新的 16 位十六进制（比如 `0100abcdef123456`）。
3. 「游戏名称」填游戏名（如 `勾指婚约`）。
4. （可选）图标、引擎 NSO 留空即可。
5. 点「▶ 打包 NSP」，等日志跑完，弹出「打包完成」后点「打开输出目录」取走 `.nsp`。

**完整链路**（配合转换器）：

```text
converter（转换器）          packer（打包器）
.ks 剧本 ──▶ out/game/ ──▶ 选 game 目录 ──▶ 一键打包 ──▶ .nsp
```

---

## 环境要求

只需要一个：**Python 3.x 完整版（含 tkinter）**。

1. 打开 <https://www.python.org/downloads/>，下载最新 Windows 安装包。
2. 运行安装程序，**务必勾选「Add python.exe to PATH」**。
3. 验证：

```bash
py --version
py -c "import tkinter"    # 无报错即成功
```

> 无需 `pip install` 任何第三方库。

依赖文件已随工具附带，与 `nsp_pack_gui.py` 放在同一目录：

- `hacbrewpack.exe` + `msys-2.0.dll` + `msys-gcc_s-seh-1.dll` —— 打包程序及运行库
- `prod.keys` —— Switch 密钥
- `template/` —— 引擎骨架（exefs 引擎 + romfs 运行库 + logo + 占位图标）

---

## 配置

打开工具后需要填：

| 字段 | 说明 |
|---|---|
| 游戏目录（转换器输出） | 转换器产出的 `game/` 目录（含 `script/`、`screens.rpy`、`options.rpy` 等）。**必填** |
| 引擎骨架目录 | 已内置，指向 `packer/template/`，一般不用改 |
| Title ID | 16 位十六进制；每款唯一；**不能以 01-0f 开头**（官方应用保留范围），建议 10 开头以上 |
| 游戏名称 | 显示在系统里的名字 |
| 发行商 | 如 `CCB` |
| 图标文件（可选） | 256×256 的 JPEG；留空用占位图标 |
| 引擎 NSO（可选） | 留空用内置引擎（已修崩溃） |
| NSP 输出目录 | 打包产物放哪（默认 `packer/NSP`） |

---

## 常见问题

### 1. 提示「游戏目录不存在」

→ 你填的路径不对。游戏目录应是转换器输出的 `game/` 目录，里面能看到 `script/`、`screens.rpy`、`options.rpy` 这些。

### 2. 提示「Title ID 必须是 16 位十六进制」或「不能以 01-0f 开头」

→ Title ID 有两个硬性要求：
1. 必须是 **16 个字符**、只含 0-9 和 a-f（如 `11452656e7071140` 就是 16 位）。
2. **不能以 `01`-`0f` 开头**——这是 Switch 官方应用的保留范围，自制游戏不能用。建议用 `10` 开头以上（洛丽塔就是 `11` 开头）。

例如 `0100...`、`0545...` 都会报错；`1145...`、`abcdef...` 才合法。

### 3. 打包后装上又崩溃 / 还是旧行为

→ 内置引擎已经是修过崩溃的版本，一般不会。如果你手动指定了「引擎 NSO」，确认那个 NSO 是正确的修复版。

### 4. 提示「缺少 hacbrewpack.exe / prod.keys」

→ 正常情况下已随工具附带在 `packer/` 目录。若被误删，把它们放回 `packer/` 目录。

### 5. 打包失败、退出码非 0

→ 看日志里 hacbrewpack 的输出。常见原因：`prod.keys` 不对 / 过期、Title ID 格式错、`game` 目录里有非法文件名或路径过长。

### 6. 改完剧本 / 界面，打包后没变化

→ 先确认 game 目录里是最新的（转换器重新输出后要重新选）；再用 Ren'Py SDK `compile` 重新编译 `.rpyc`（改了 `.rpy` **必须**重编）。

---

## 与转换器的配合

- 转换器产出 `out/game/`，打包器把它和内置引擎骨架合起来打成 `.nsp`。
- 两个工具独立，但顺序固定：**先转换，后打包**。
- 每款新游戏只需重复：转换（得到 game 目录）→ 打包器选 game 目录 + 填新 titleid → 打包。
