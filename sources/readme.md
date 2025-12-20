请运行 `build.py` 以生成字体。在此之前，您需要安装 [FontForge](https://fontforge.org/)。

**安装 FontForge：**

- **macOS (Homebrew):**
  ```bash
  brew install fontforge
  ```

- **Ubuntu/Debian:**
  ```bash
  sudo apt-get install fontforge python3-fontforge
  ```

- **Windows:**
  从 [FontForge 官网](https://fontforge.org/en-US/downloads/) 下载安装包。

**运行构建脚本：**

```bash
fontforge -script build.py
```

目前，源文件采用 [UFO 3 ZIP 格式（`.ufoz`）](https://unifiedfontobject.org/versions/ufo3/)。脚本会自动解压缩 `.ufoz` 文件，使用解压后的 `.ufo` 目录生成 TTF 字体，并在完成后清理临时文件。

请注意，我们并不推荐直接使用 UFO 生成的字体进行实际应用。UFO 格式主要用于版本管理和研究用途，不是我们用于实际开发的格式。

如果在处理大型字体时遇到内存问题，可以尝试单独处理文件或减少并行进程数。

---

Please run `build.py` to generate the font. Before doing so, you need to install [FontForge](https://fontforge.org/).

**Installing FontForge:**

- **macOS (Homebrew):**
  ```bash
  brew install fontforge
  ```

- **Ubuntu/Debian:**
  ```bash
  sudo apt-get install fontforge python3-fontforge
  ```

- **Windows:**
  Download the installer from [FontForge official website](https://fontforge.org/en-US/downloads/).

**Running the build script:**

```bash
fontforge -script build.py
```

Currently, the source files are in [UFO 3 ZIP format (`.ufoz`)](https://unifiedfontobject.org/versions/ufo3/). The script will automatically unzip the `.ufoz` files, use the extracted `.ufo` directories to generate TTF fonts, and clean up temporary files after completion.

Please note that we do not recommend using fonts generated directly from UFO for actual applications. The UFO format is primarily intended for version control and research purposes, and is not our format of choice for actual development.

If you encounter memory issues when processing large fonts, try processing files individually or reducing the number of parallel processes.

