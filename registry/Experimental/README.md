# Windows Registry Files for Plangothic Font
# Windows 遍黑体注册表安装文件

## Overview / 概述
These registry files (.reg) are designed to enhance the installation of Plangothic Font on Windows and enable global fallback functionality. This ensures that the Plangothic Font is used as a fallback font across the system, improving text rendering for unsupported characters, especially CJK Extension characters.

此文件夹下的注册表文件用于增强遍黑体在 Windows 平台的安装效果，并启用全局后备字体功能。该功能确保遍黑体在系统中作为后备字体使用，从而改善不支持字符的文本显示效果，特别是 CJK 扩展区字符。

## Files Description / 文件说明

### Registry Files / 注册表文件
- **`LanguagePack-Install.reg`** - Installs Plangothic font fallback configuration
  - **安装配置** - 安装遍黑体后备字体配置
- **`LanguagePack-Uninstall.reg`** - Removes Plangothic font fallback configuration  
  - **卸载配置** - 移除遍黑体后备字体配置

### Python Tool / Python 工具
- **`font_link_manager.py`** - Advanced font link configuration backup and modification tool
  - **字体链接管理器** - 高级字体链接配置备份和修改工具

## What These Files Do / 文件功能说明

### Registry Files / 注册表文件功能
The registry files modify the following Windows font systems:
注册表文件修改以下 Windows 字体系统：

1. **SystemLink Configuration** - Registers Plangothic fonts in the font linking system
   - **SystemLink 配置** - 在字体链接系统中注册遍黑体字体

2. **SurrogateFallback Configuration** - Modifies fallback settings for specific fonts:
   - **SurrogateFallback 配置** - 修改特定字体的后备设置：
   - `MingLiU` (細明體)
   - `MingLiU_HKSCS` (細明體_HKSCS)
   - `PMingLiU` (新細明體)
   - `SimSun` (宋体)

### Python Tool Features / Python 工具功能
The `font_link_manager.py` script provides:
`font_link_manager.py` 脚本提供：

- **Automatic Backup** - Creates backup of current font link configuration
  - **自动备份** - 创建当前字体链接配置的备份
- **Smart Insertion** - Uses different insertion strategies for different fonts:
  - **智能插入** - 对不同字体使用不同的插入策略：
  - Segoe UI family: Appends Plangothic fonts to the end (preserves priority)
    - Segoe UI 系列：将遍黑体添加到末尾（保持优先级）
  - Other fonts: Prepends Plangothic fonts to the beginning (higher priority)
    - 其他字体：将遍黑体添加到开头（更高优先级）
- **Configuration Preview** - Shows current font link settings before modification
  - **配置预览** - 修改前显示当前字体链接设置
- **Comprehensive Coverage** - Supports 50+ system fonts including:
  - **全面覆盖** - 支持 50+ 个系统字体，包括：
  - Western fonts (Arial, Times New Roman, Tahoma, etc.)
    - 西文字体（Arial、Times New Roman、Tahoma 等）
  - CJK fonts (Microsoft YaHei, SimSun, Meiryo, etc.)
    - CJK 字体（微软雅黑、宋体、Meiryo 等）
  - UI fonts (Segoe UI, Malgun Gothic, etc.)
    - 界面字体（Segoe UI、Malgun Gothic 等）

## ⚠️ Important Notice / 重要提示
> [!WARNING]
>
> **For Registry Files / 注册表文件：**  
> The global fallback feature is experimental and should be used with caution. It may affect system stability or font rendering in unexpected ways.  
> 全局后备字体功能为实验性功能，请谨慎使用。此功能可能会影响系统稳定性或导致字体显示异常。
>
> **For Python Tool / Python 工具：**  
> The Python tool is recommended for advanced users. It provides more control and safety features, including automatic backup and restoration capabilities.  
> Python 工具推荐给高级用户使用。它提供更多控制和安全功能，包括自动备份和恢复能力。

## Usage Instructions / 使用说明

### Method 1: Using Registry Files (Simple) / 方法一：使用注册表文件（简单）

1. **Backup Your Registry** / **备份注册表**
   - Create a system restore point or backup registry manually
   - 创建系统还原点或手动备份注册表

2. **Install Configuration** / **安装配置**
   - Double-click `LanguagePack-Install.reg` to apply the configuration
   - 双击 `LanguagePack-Install.reg` 应用配置

3. **Restart System** / **重启系统**
   - Restart your computer for changes to take effect
   - 重启计算机使更改生效

4. **Uninstall (if needed)** / **卸载（如需要）**
   - Double-click `LanguagePack-Uninstall.reg` to remove the configuration
   - 双击 `LanguagePack-Uninstall.reg` 移除配置

### Method 2: Using Python Tool (Advanced) / 方法二：使用 Python 工具（高级）

1. **Run** / **运行**
   ```bash
   python font_link_manager.py
   ```

2. **Follow the Interactive Process** / **按照交互流程操作**
   - The tool will automatically backup current settings
   - 工具将自动备份当前设置
   - Generate modified registry files for review
   - 生成修改后的注册表文件供检查

## Supported Plangothic Variants / 支持的遍黑体变体
- Plangothic P1 (TTF/OTF)
- Plangothic P2 (TTF/OTF)  
- Plangothic TTC Collection
- 遍黑体 P1（TTF/OTF）
- 遍黑体 P2（TTF/OTF）
- 遍黑体 TTC 字体集

## Target Applications / 目标应用程序
These configurations help improve font rendering in:
这些配置有助于改善以下应用程序的字体显示：

- **System UI** - Windows Explorer, Control Panel, etc.
  - **系统界面** - Windows 资源管理器、控制面板等
- **Web Browsers** - Improved rendering of rare CJK characters
  - **网页浏览器** - 改善罕见 CJK 字符的显示
- **Text Editors** - Notepad, WordPad, and other editors
  - **文本编辑器** - 记事本、写字板等编辑器
- **Office Applications** - Better support for extended character sets
  - **办公应用** - 更好地支持扩展字符集

## Troubleshooting / 故障排除

### Common Issues / 常见问题
- **Font not displaying correctly** / **字体显示不正确**
  - Ensure Plangothic fonts are properly installed in Windows
  - 确保遍黑体已正确安装到 Windows 中
  - Try logging out and logging back in
  - 尝试注销并重新登录

- **System performance issues** / **系统性能问题**
  - Use the Python tool's backup to restore original settings
  - 使用 Python 工具的备份恢复原始设置
  - Or run `LanguagePack-Uninstall.reg`
  - 或运行 `LanguagePack-Uninstall.reg`

### Recovery / 恢复方法
- **Registry Method** / **注册表方法**
  - Run `LanguagePack-Uninstall.reg` to remove configurations
  - 运行 `LanguagePack-Uninstall.reg` 移除配置

- **Python Tool Method** / **Python 工具方法**
  - Import the automatically generated backup `.reg` file
  - 导入自动生成的备份 `.reg` 文件

## Technical Details / 技术细节
- **Registry Paths Modified** / **修改的注册表路径**
  - `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink`
  - `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\LanguagePack\SurrogateFallback`
  - `HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink`
  - `HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\LanguagePack\SurrogateFallback`

- **Font Priority Strategy** / **字体优先级策略**
  - Segoe UI: Maintains original priority (append)
    - Segoe UI：保持原有优先级（末尾添加）
  - Other fonts: Plangothic gets higher priority (prepend)
    - 其他字体：遍黑体获得更高优先级（开头添加）

## Feedback / 反馈
If you encounter any issues or have suggestions for improvement:
如果您遇到任何问题或有改进建议：

- Report issues to the Plangothic Font project maintainers
- 向遍黑体项目维护者报告问题
- Consider using the Python tool for more control and diagnostics
- 考虑使用 Python 工具获得更多控制和诊断功能
