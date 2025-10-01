# Windows Registry Files for Plangothic Font
# Windows 遍黑体注册表安装文件

---

## Overview / 概述

**Plangothic Global Fallback** enables seamless rendering of rare and extended CJK characters across Windows applications by configuring Plangothic as a system-wide fallback font.

**遍黑体全局后备** 通过将遍黑体配置为系统级后备字体，在 Windows 应用程序中实现罕见和扩展 CJK 字符的无缝渲染。

---

## System Requirements / 系统要求

- **Operating System** / **操作系统**: Windows 7/8.1/10/11 (Windows 10+ recommended)
- **Permissions** / **权限**: Administrator privileges required for registry modification / 修改注册表需要管理员权限
- **Prerequisites** / **前置条件**: Plangothic fonts must be installed before configuration / 配置前必须先安装遍黑体字体
- **Python** (for tools): Python 3.6+ / Python 3.6+（工具使用）

---

## Quick Start / 快速开始

**Choose your approach based on your needs:**  
**根据需求选择方法：**

- 🚀 **Just want it to work?** → Use **Method 1** (Registry Files)  
- ⚙️ **Want customization?** → Use **Method 2** (Python Tools)  
- 🔍 **Need to verify setup?** → Use **Method 3** (Testing Tool)  

**只想让它工作？** → 使用**方法一**（注册表文件）  
**想要自定义？** → 使用**方法二**（Python 工具）  
**需要验证设置？** → 使用**方法三**（测试工具）

---

## ⚠️ Before You Start / 开始之前

> **Critical**: Always create a system backup before proceeding  
> **关键**：继续操作前务必创建系统备份
> 
> **Note**: This is experimental software that modifies system font settings  
> **注意**：这是修改系统字体设置的实验性软件

## Files Description / 文件说明

| File / 文件 | Description (English) | 说明（中文） |
|-------------|----------------------|-------------|
| **`LanguagePack-Install.reg`** | Installs Plangothic fallback configuration | 安装遍黑体后备字体配置 |
| **`LanguagePack-Uninstall.reg`** | Removes Plangothic fallback configuration | 移除遍黑体后备字体配置 |
| **`main.py`** | Advanced font link manager with backup, smart insertion and preview | 高级字体链接管理器，提供自动备份、智能插入、预览等功能 |
| **`main_conservative.py`** | Conservative font link manager that appends Plangothic to all fonts, preserving existing priority | 保守版字体链接管理器，所有字体均在末尾添加遍黑体，保持原有优先级不变 |
| **`font-fallback-test/`** | Contains compiled `font-fallback-test.exe` for quick verification of system FontLink configuration | 包含编译好的 `font-fallback-test.exe`，用于快速检查系统 FontLink 配置 |

---

## Registry Changes / 注册表修改

The files modify the following registry keys (both 64-bit and 32-bit views):  
以下注册表键在 64 位与 32 位（WOW6432Node）视图中均会被修改：

- `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink`
- `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\LanguagePack\SurrogateFallback`
- `HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink`
- `HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\LanguagePack\SurrogateFallback`

---

## Python Tools / Python 工具

### Advanced Manager (`main.py`) / 高级管理器

**Features / 功能：**
- **Automatic backup** - Creates a `.reg` backup of current FontLink configuration before modification
- **Smart insertion strategy**:
  - **Segoe UI family** - Appends Plangothic (preserves original priority)
  - **All other fonts** - Prepends Plangothic (higher priority)
- **Configuration preview** - Shows current FontLink data and planned changes
- **Comprehensive support** - Handles 50+ system fonts (Western, CJK, UI families)

**功能特点：**
- **自动备份** - 修改前创建当前 FontLink 配置的 `.reg` 备份文件
- **智能插入策略**：
  - **Segoe UI 系列** - 在末尾添加遍黑体（保持原有优先级）
  - **其他所有字体** - 在开头添加遍黑体（更高优先级）
- **配置预览** - 显示当前 FontLink 数据和计划的更改
- **全面支持** - 处理 50+ 个系统字体（西文、CJK、界面字体系列）

### Conservative Manager (`main_conservative.py`) / 保守管理器

**Features / 功能：**
- **Universal append strategy** - Always appends Plangothic to the end of font lists for all fonts
- **Priority preservation** - Maintains existing font priorities without reordering
- **Safer modification** - Only adds fallback entries, never removes or reorders existing ones
- **Identical usage** - Same interface as `main.py`

**功能特点：**
- **通用末尾添加策略** - 始终将遍黑体添加到所有字体列表的末尾
- **优先级保持** - 保持现有字体优先级，不重新排序
- **更安全的修改** - 只添加后备字体条目，从不删除或重新排序现有条目
- **相同用法** - 与 `main.py` 使用方式相同

Both scripts generate a new `.reg` file that can be reviewed before manual application.  
两个脚本都会生成新的 `.reg` 文件，可在手动应用前进行检查。

---

## Usage Instructions / 使用说明

### Method 1: Registry Files (Quick Setup) / 方法一：注册表文件（快速设置）

| Step / 步骤 | English | 中文 |
|-------------|---------|------|
| 1 | **Backup registry**: Create a system restore point or manually export relevant keys | **备份注册表**：创建系统还原点或手动导出相关键值 |
| 2 | **Install**: Double-click `LanguagePack-Install.reg` and confirm | **安装**：双击 `LanguagePack-Install.reg` 并确认 |
| 3 | **Restart**: Reboot the computer for changes to take effect | **重启**：重新启动计算机使更改生效 |
| 4 | **Uninstall** (if needed): Double-click `LanguagePack-Uninstall.reg` | **卸载**（如需）：双击 `LanguagePack-Uninstall.reg` |

### Method 2: Python Tools (Customizable) / 方法二：Python 工具（可自定义）

#### Advanced Mode / 高级模式
```bash
python main.py
```

#### Conservative Mode / 保守模式
```bash
python main_conservative.py
```

**Process / 流程：**
1. Read current FontLink configuration / 读取当前 FontLink 配置
2. Prompt to create backup (`backup_YYYYMMDD_HHMMSS.reg`) / 提示创建备份文件
3. Show preview of changes / 显示更改预览
4. Write new configuration to `fontlink_modified_*.reg` / 将新配置写入文件

Review the generated `.reg` file and import it (double-click) if acceptable.
检查生成的 `.reg` 文件，如果可接受则导入（双击）。

### Method 3: Testing and Verification / 方法三：测试和验证

The `font-fallback-test/` folder contains the precompiled **`font-fallback-test.exe`**.  
`font-fallback-test/` 文件夹包含预编译的 **`font-fallback-test.exe`**。

**How to use / 使用方法：**

1. **Run the tool** / **运行工具**
   ```
   font-fallback-test/font-fallback-test.exe
   ```

2. **Interface overview** / **界面概览**  
   The UI displays a table with:  
   界面显示包含以下内容的表格：
   - Font name / 字体名称
   - Preview text rendered with the font (or fallback) / 使用字体（或后备字体）渲染的预览文本
   - ✅ / ❌ indicating presence of FontLink entry / 表示是否存在 FontLink 条目
   - Raw FontLink configuration data (truncated for readability) / 原始 FontLink 配置数据（为可读性进行截断）

3. **Customization** / **自定义**
   - Edit `config.toml` to customize font lists and test text
   - 编辑 `config.toml` 自定义字体列表和测试文本
   - The tool reads the same registry locations as the `.reg` files
   - 该工具读取与 `.reg` 文件相同的注册表位置

---

## Tool Selection Guide / 工具选择指南

### When to Use Each Method / 何时使用各种方法

| Method / 方法 | Recommendation / 推荐 | Best for / 适用于 | Pros / 优点 | Cons / 缺点 |
|---------------|----------------------|-------------------|-------------|-------------|
| **Registry Files** / **注册表文件** | 🌟 **Beginner** / **初学者** | Quick installation with standard settings / 使用标准设置快速安装 | Simple double-click installation / 简单的双击安装 | No customization options / 无自定义选项 |
| **`main.py` (Advanced)** / **高级模式** | 🔧 **Advanced** / **高级用户** | Optimal font rendering performance / 最佳字体渲染性能 | Plangothic prioritized for most fonts / 大多数字体优先使用遍黑体 | May change existing font behavior / 可能改变现有字体行为 |
| **`main_conservative.py`** | 🛡️ **Safe** / **安全** | Minimal changes to existing rendering / 最小化对现有渲染的更改 | Safest modification approach / 最安全的修改方法 | Plangothic used only as last resort / 遍黑体仅作为最后选择 |
| **Testing Tool** / **测试工具** | 🔍 **Diagnostic** / **诊断** | Verification and troubleshooting / 验证和故障排除 | Real-time configuration checking / 实时配置检查 | Read-only, no modification capability / 只读，无修改功能 |

---

## Supported Plangothic Variants / 支持的遍黑体变体

- Plangothic P1 (TTF/OTF) / 遍黑体 P1（TTF/OTF）
- Plangothic P2 (TTF/OTF) / 遍黑体 P2（TTF/OTF）
- Plangothic TTC Collection / 遍黑体 TTC 字体集

---

## Target Applications / 目标应用程序

These configurations improve font rendering in:  
这些配置改善以下应用程序的字体显示：

- **System UI** - Windows Explorer, Control Panel, Settings / 系统界面 - Windows 资源管理器、控制面板、设置
- ~~**Web Browsers** - Chrome, Firefox, Edge for rare CJK characters / 网页浏览器 - Chrome、Firefox、Edge 中的罕见 CJK 字符~~
* Limited effectiveness; requires additional CSS font-family declarations for web content / 效果有限；网页内容需要额外的 CSS font-family 声明
- **Text Editors** - Notepad, WordPad, Visual Studio Code / 文本编辑器 - 记事本、写字板、Visual Studio Code
- **Office Applications** - Microsoft Office, LibreOffice for extended character sets / 办公应用 - Microsoft Office、LibreOffice 中的扩展字符集

---

## Important Notices / 重要提示

> [!WARNING]
> **Experimental Feature** / **实验性功能**  
> The global fallback feature is experimental and may affect system stability or cause unexpected rendering issues.  
> 全局后备字体功能为实验性功能，可能会影响系统稳定性或导致意外的渲染问题。

> [!IMPORTANT]
> **Always Backup** / **务必备份**  
> Create a system restore point or registry backup before applying changes.  
> 应用更改前务必创建系统还原点或注册表备份。

> [!TIP]
> **Conservative Approach** / **保守方法**  
> If you only need Plangothic as a fallback without changing existing font priorities, use `main_conservative.py`.  
> 如果您只需要遍黑体作为后备字体而不改变现有字体优先级，请使用 `main_conservative.py`。

---

## Troubleshooting / 故障排除

### Common Issues / 常见问题

| Issue / 问题 | Solution / 解决方案 |
|--------------|-------------------|
| **Font not displaying correctly** / **字体显示不正确** | 1. Ensure Plangothic fonts are installed in Windows<br>2. Use testing tool to verify FontLink configuration<br>3. Try logging out and back in<br><br>1. 确保遍黑体已安装到 Windows 中<br>2. 使用测试工具验证 FontLink 配置<br>3. 尝试注销并重新登录 |
| **System performance issues** / **系统性能问题** | 1. Use Python tool's backup to restore settings<br>2. Run `LanguagePack-Uninstall.reg`<br>3. Switch to conservative mode<br><br>1. 使用 Python 工具的备份恢复设置<br>2. 运行 `LanguagePack-Uninstall.reg`<br>3. 切换到保守模式 |
| **Configuration not taking effect** / **配置未生效** | 1. Run testing tool to check FontLink status<br>2. Restart applications or logout/login<br>3. Verify Plangothic installation<br><br>1. 运行测试工具检查 FontLink 状态<br>2. 重启应用程序或注销/登录<br>3. 验证遍黑体安装 |

### Recovery Methods / 恢复方法

- **Registry method** / **注册表方法** - Run `LanguagePack-Uninstall.reg` / 运行 `LanguagePack-Uninstall.reg`
- **Python method** / **Python 方法** - Import the backup file (`backup_*.reg`) / 导入备份文件
- **System restore** / **系统还原** - Use Windows System Restore if available / 如可用，使用 Windows 系统还原

---

## Technical Details / 技术细节

| Item / 项目 | Details / 详情 |
|-------------|----------------|
| **Font priority strategy** / **字体优先级策略** | **Advanced (`main.py`)**: Segoe UI → append, others → prepend<br>**Conservative (`main_conservative.py`)**: append for all fonts<br><br>**高级模式**：Segoe UI → 末尾添加，其他 → 开头添加<br>**保守模式**：所有字体均末尾添加 |
| **Supported fonts** / **支持的字体** | 50+ system fonts (Western, CJK, UI families) / 50+ 个系统字体（西文、CJK、界面字体系列） |
| **Default test text** / **默认测试文本** | `"包罗万象化春外，最美全年天地中"` (customizable in `config.toml`) / 可在 `config.toml` 中自定义 |
| **Testing tool configuration** / **测试工具配置** | `config.toml` supports custom font lists, test text, UI settings / 支持自定义字体列表、测试文本、界面设置 |
| **Configuration scope** / **配置范围** | System-wide (affects all users) / 系统级（影响所有用户） |
| **Registry backup location** / **注册表备份位置** | `backup_YYYYMMDD_HHMMSS.reg` in script directory / 脚本目录下的备份文件 |
| **Effective immediately** / **立即生效** | New applications only, existing may need restart / 仅新启动的应用程序，现有应用可能需重启 |
| **Web browser limitations** / **网页浏览器限制** | System FontLink only affects browser UI, not web content. Web pages need explicit CSS: `font-family: "Plangothic P1", "Plangothic P2", sans-serif;`<br><br>系统 FontLink 仅影响浏览器界面，不影响网页内容。网页需要显式 CSS：`font-family: "Plangothic P1", "Plangothic P2", sans-serif;` |

---

## Feedback / 反馈

**For bug reports or feature requests** / **错误报告或功能请求**:  
Contact the Plangothic Font project maintainers with detailed system information.

**For troubleshooting** / **故障排除**:  
Use the Python tools or `font-fallback-test.exe` for detailed diagnostics and include the output in your report.

**联系遍黑体项目维护者**，提供详细的系统信息。  
**故障排除时**，请使用 Python 工具或 `font-fallback-test.exe` 进行详细诊断，并在报告中包含输出结果。
