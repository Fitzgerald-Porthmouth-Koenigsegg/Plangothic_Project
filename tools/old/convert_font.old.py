#!/usr/bin/env python3
"""
convert_font.py - Font Format Converter
字体格式转换工具

Supported formats 支持的格式:
- TTF  (TrueType Font)
- OTF  (OpenType Font)
- WOFF (Web Open Font Format)
- WOFF2 (Web Open Font Format 2)
- EOT  (Embedded OpenType)
- SVG  (Scalable Vector Graphics Font)

Usage 使用方法:
    fontforge -script convert_font.py "PlangothicTest-Regular.ttf" -f woff2
    
Arguments 参数:
    input_font      Input font file path 输入字体文件路径
    -o, --output    Output font file path (optional) 输出字体文件路径（可选）
    -f, --format    Output format (default: woff2) 输出格式（默认：woff2）
    --family-name   Set font family name 设置字体族名称
    --version       Set font version number 设置字体版本号
"""

import os
import argparse
import time
from datetime import datetime

try:
    import fontforge
except ModuleNotFoundError:
    print("\n警告：当前没有使用 `fontforge` 运行，功能无法使用")
    pass

def setup_font_properties(font, family_name=None, version=None):
    """设置字体属性"""
    try:
        if family_name:
            try:
                font.familyname = family_name
                font.fontname = family_name.replace(' ', '')
                font.fullname = family_name
            except Exception as e:
                print(f"警告：设置字体名称失败：{str(e)}")
        
        if version:
            try:
                font.version = version
            except Exception as e:
                print(f"警告：设置版本号失败：{str(e)}")
        
        try:
            font.head_optimized_for_cleartype = True
        except:
            pass
            
        try:
            font.os2_typoascent = font.ascent
            font.os2_typodescent = -font.descent
            font.os2_typolinegap = 0
            font.hhea_ascent = font.ascent
            font.hhea_descent = -font.descent
            font.hhea_linegap = 0
        except:
            pass
            
        try:
            font.gasp = {8: ('gridfit', 'antialias', 'symmetric-smoothing'),
                        16: ('gridfit', 'antialias', 'symmetric-smoothing'),
                        65535: ('gridfit', 'antialias', 'symmetric-smoothing')}
        except:
            pass
            
    except Exception as e:
        print(f"警告：设置字体属性时出现问题：{str(e)}")

def convert_font(input_path, output_path, format_type, optimization='default', family_name=None, version=None):
    try:
        start_time = time.time()

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"错误：未找到字体文件：{input_path}")

        print(f"\n正在加载字体：{input_path}")
        font = fontforge.open(input_path)
        
        if not output_path:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}.{format_type}"
            
        setup_font_properties(font, family_name, version)

        print(f"\n正在使用 {optimization} 模式转换字体...")

        if format_type == 'otf':
            font.generate(output_path, flags=('opentype', 'round', 'dummy-dsig', 'apple'))
        elif format_type == 'ttf':
            font.generate(output_path, flags=('opentype', 'round', 'dummy-dsig', 'apple', 'short-post', 'old-kern'))
        elif format_type == 'woff2':
            font.generate(output_path, flags=('opentype', 'round', 'dummy-dsig', 'no-flex', 'no-hints', 'short-post', 'omit-instructions'))
        else:
            font.generate(output_path)

        end_time = time.time()
        input_size = os.path.getsize(input_path) / 1024  # KB
        output_size = os.path.getsize(output_path) / 1024  # KB
        
        print(f"\n转换完成：")
        print(f"处理时间：{end_time - start_time:.2f} 秒")
        print(f"源文件：{input_size:.2f} KB")
        print(f"转换后：{output_size:.2f} KB")
        print(f"大小变化：{((output_size/input_size)-1)*100:+.1f}%")
        
        print(f"✓ 字体已保存为 {output_path}")
        return True
        
    except Exception as e:
        print(f"错误：转换过程中出现问题：{str(e)}")
        return False

if __name__ == "__main__":
    SUPPORTED_FORMATS = {
        'ttf': 'TrueType 字体 (.ttf)',
        'otf': 'OpenType 字体 (.otf)',
        'woff': 'Web Open Font Format (.woff)',
        'woff2': 'Web Open Font Format 2 (.woff2)',
        'eot': 'Embedded OpenType (.eot)',
        'svg': 'SVG 字体 (.svg)'
    }

    parser = argparse.ArgumentParser(description='字体格式转换工具')
    parser.add_argument('input_font', help='输入字体文件路径')
    parser.add_argument('-o', '--output', help='输出字体文件路径（可选）')
    parser.add_argument(
        '-f', '--format',
        choices=list(SUPPORTED_FORMATS.keys()),
        default='woff2',
        help='输出字体格式（默认：woff2）'
    )
    parser.add_argument('--family-name', help='设置字体族名称')
    parser.add_argument('--version', help='设置字体版本号')

    args = parser.parse_args()

    if not args.input_font:
        print("使用示例：")
        print(f"python {os.path.basename(__file__)} input.ttf -o output.woff2 -f woff2")
        print("\n支持的格式：")
        for fmt, desc in SUPPORTED_FORMATS.items():
            print(f"  {fmt:<6} - {desc}")
    else:
        convert_font(
            args.input_font,
            args.output,
            args.format,
            args.family_name,
            args.version
        )
    input("按回车键退出...")
