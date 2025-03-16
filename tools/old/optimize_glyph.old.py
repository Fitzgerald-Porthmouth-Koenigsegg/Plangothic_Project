#!/usr/bin/env python3
"""
Font Glyph Optimizer - 字体轮廓优化工具

Usage 使用方法:
    fontforge -script optimize_glyph.py "PlangothicTest-Regular.ttf" -s 0.5

Output 输出:
    Creates a new optimized font file with "_merge_glyphs" suffix
"""

import sys
import os
import io
import time
import contextlib

try:
    import fontforge
except ModuleNotFoundError:
    print("\n警告：当前没有使用 `fontforge` 运行，功能无法使用")
    pass

def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"

def get_glyph_info(glyph):
    try:
        if glyph.unicode != -1:
            char = chr(glyph.unicode)
            return f"U+{glyph.unicode:04X}"
        else:
            return f"{glyph.glyphname}"
    except (ValueError, AttributeError):
        return f"{glyph.glyphname}"

def process_compound_glyph(glyph):
    try:
        if len(glyph.references) > 0:
            try:
                glyph.unlinkReferences()
            except (AttributeError, TypeError):
                glyph.unlink()
    except (AttributeError, TypeError):
        pass

def process_line_endpoints(glyph):
    contours = glyph.foreground
    for contour in contours:
        prev_point = None
        for point in contour:
            if prev_point is not None:
                if (abs(point.x - prev_point.x) < 0.1 or 
                    abs(point.y - prev_point.y) < 0.1):
                    point.type = fontforge.splineCorner
                    prev_point.type = fontforge.splineCorner
            prev_point = point

def processing_optimization_glyph_extension(glyph):
    glyph.simplify(0.5, ('mergelines', 'smoothcurves', 'choosehv', 'removesingletonpoints' ), 0.3, 0, 0.5)
    glyph.addExtrema()
    glyph.width = int(round(glyph.width / 10.0) * 10)
    glyph.balance()
    glyph.autoHint()

def process_font(input_file, simplify_value=0.5):
    try:
        font = fontforge.open(input_file)
    except OSError as e:
        print(f"错误：无法打开字体文件 - {e}")
        return
    glyphs = list(font.glyphs())
    total_glyphs = len(glyphs)

    if total_glyphs == 0:
        print("警告：没有找到可处理的字形")
        return

    start_time = time.time()
    last_update_time = start_time

    print(f"开始处理字体，共 {total_glyphs} 个字形...")
    print("进度", end="")

    for index, glyph in enumerate(glyphs):
        current_time = time.time()
        elapsed_time = current_time - start_time
        progress = (index + 1) / total_glyphs if total_glyphs > 0 else 0

        if index > 0 and elapsed_time > 0:
            glyphs_per_second = (index + 1) / elapsed_time
            remaining_glyphs = total_glyphs - (index + 1)
            estimated_remaining_time = remaining_glyphs / glyphs_per_second
        else:
            estimated_remaining_time = 0

        glyph_info = get_glyph_info(glyph)

        if current_time - last_update_time >= 0.2:
            bar_length = 30
            filled_length = int(bar_length * progress)
            bar = "#" * filled_length + "-" * (bar_length - filled_length)
            print(f"\r进度({index + 1}/{total_glyphs}): [{bar}] ({progress:.1%}) ⏱️ {format_time(elapsed_time)} ⏳ {format_time(estimated_remaining_time)} ⚡ 当前处理: {glyph_info}", end="", flush=True)
            last_update_time = current_time

        process_compound_glyph(glyph)
        glyph.simplify(0.1, ('mergelines', 'choosehv'), 0.1, 0.1, 0)
        process_line_endpoints(glyph)
        glyph.simplify(simplify_value, ('mergelines', 'smoothcurves', 'removesingletonpoints'), 0.3, 0, 0.5)
        glyph.addExtrema()
        glyph.canonicalContours()
        glyph.canonicalStart()
        glyph.simplify()
        glyph.removeOverlap()
        glyph.correctDirection()
        glyph.simplify(simplify_value, ('mergelines', 'smoothcurves'), 0.3, 0, 0.5)
        glyph.round()
        glyph.autoHint()
        processing_optimization_glyph_extension(glyph)

    total_time = time.time() - start_time
    bar = "=" * 30
    print(f"\n进度({total_glyphs}/{total_glyphs}): [{bar}] (100%) ⏱️ 总用时: {format_time(total_time)}")
    print(f"\n新字体保存中...")

    file_name, file_extension = os.path.splitext(input_file)
    output_file = f"{file_name}_merge_glyphs{file_extension}"
    font.generate(output_file, flags=('opentype', 'round', 'dummy-dsig', 'apple'))
    print(f"\n新字体已保存为: {output_file}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='字体轮廓优化工具')
    parser.add_argument('font_file', nargs='?', help='字体文件路径')
    parser.add_argument('-s', '--simplify', type=float, default=0.5, help='simplify 参数值 (默认: 0.5)')

    args = parser.parse_args()

    if not args.font_file:
        print("\n 没有选择字体")
        input("按回车键退出...")
        sys.exit(1)

    try:
        print(f"\n使用 simplify 参数值: {args.simplify}")
        process_font(args.font_file, args.simplify)
        print("处理完成！")
    except Exception as e:
        print(f"\n发生严重错误：{str(e)}")
        input("按回车键退出...")
