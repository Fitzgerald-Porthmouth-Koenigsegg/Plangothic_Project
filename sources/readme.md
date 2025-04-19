请运行 `build.py` 以生成字体。在此之前，您需要安装 [`fontmake`](https://github.com/googlefonts/fontmake) 和 [`fontTools`](https://github.com/fonttools/fonttools)。您可以通过以下命令进行安装：

```bash
pip3 install fonttools fontmake
```

目前，源文件采用 [UFO 3 ZIP 格式（`.ufoz`）](https://unifiedfontobject.org/versions/ufo3/)。由于 `fontmake` 暂不支持 `.ufoz` 格式，所以脚本会自动解压缩并使用解压后的 `.ufo` 文件夹来生成字体。

请注意，我们并不推荐直接使用 UFO 生成的字体进行实际应用。UFO 格式主要用于版本管理和研究用途，不是我们用于实际开发的格式。

如果遇到 `fontmake: Error: In '*': Compiling UFO failed: 27585` 错误，这可能是由于字形复杂度或内存不足等其他原因造成的，我们无法提供解决方案。

---

Please run `build.py` to generate the font. Before doing so, you need to install [`fontmake`](https://github.com/googlefonts/fontmake) and [`fontTools`](https://github.com/fonttools/fonttools). You can install them using the following commands:

```bash
pip3 install fonttools fontmake
```

Currently, the source files are in [UFO 3 ZIP format (`.ufoz`)](https://unifiedfontobject.org/versions/ufo3/). Since `fontmake` does not yet support `.ufoz` format, the script will automatically unzip the files and use the extracted `.ufo` folder to build the font.

Please note that we do not recommend using fonts generated directly from UFO for actual applications. The UFO format is primarily intended for version control and research purposes, and is not our format of choice for actual development.

If you encounter the error `fontmake: Error: In '*': Compiling UFO failed: 27585`, it may be due to glyph complexity or insufficient memory, among other reasons. Unfortunately, we cannot provide a solution for this issue.

