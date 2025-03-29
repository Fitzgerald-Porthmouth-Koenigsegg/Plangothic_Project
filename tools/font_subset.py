#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
font_subset.py - 字体子集化工具
使用 fonttools 中的 pyftsubset 功能创建字体子集

Usage 使用方法:
    python font_subset.py 原字体.ttf -u 4E00-9FFF,3000-303F -f woff2
    python font_subset.py 原字体.ttf -t "这是要包含的中文文本" -f woff2
    python font_subset.py 原字体.ttf --text-file 文本内容.txt -f woff2
"""

import argparse
import os
import subprocess
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(description='字体子集化工具')
    parser.add_argument('font_file', help='原始字体文件路径')
    parser.add_argument('--output', '-o', help='输出文件路径，默认为原文件名加上"_subset"后缀', default=None)
    parser.add_argument('--flavor', '-f', help='输出格式 (woff, woff2)', default=None)
    parser.add_argument('--unicodes', '-u', help='Unicode范围，例如：U+4E00-U+9FFF,U+3000-U+303F')
    parser.add_argument('--text', '-t', help='要包含的文本')
    parser.add_argument('--text-file', help='包含要子集化文本的文件路径')
    parser.add_argument('--layout-features', help='要保留的OpenType特性，例如：kern,liga')
    
    return parser.parse_args()

def create_font_subset(args):
    # 检查字体文件是否存在
    if not os.path.exists(args.font_file):
        print(f"错误: 字体文件 '{args.font_file}' 不存在")
        return False
    
    # 构建输出文件路径
    if args.output is None:
        font_path = Path(args.font_file)
        output_dir = font_path.parent
        output_name = f"{font_path.stem}_subset{font_path.suffix}"
        if args.flavor:
            output_name = f"{font_path.stem}_subset.{args.flavor}"
        output_path = output_dir / output_name
        args.output = str(output_path)
    
    # 构建命令
    cmd = ['pyftsubset', args.font_file, f'--output-file={args.output}']
    
    # 添加Unicode范围参数
    if args.unicodes:
        cleaned_unicodes = args.unicodes.replace("U+", "")
        cmd.append(f'--unicodes={cleaned_unicodes}')
    
    # 添加文本参数
    if args.text:
        cmd.append(f'--text={args.text}')
    
    # 添加文本文件参数
    if args.text_file:
        if not os.path.exists(args.text_file):
            print(f"错误: 文本文件 '{args.text_file}' 不存在")
            return False
        cmd.append(f'--text-file={args.text_file}')
    
    # 添加输出格式参数
    if args.flavor:
        cmd.append(f'--flavor={args.flavor}')
    
    # 添加布局特性参数
    if args.layout_features:
        cmd.append(f'--layout-features={args.layout_features}')

    cmd.append('--notdef-outline')
    cmd.append('--notdef-glyph')

    # 检查是否至少指定了一种子集化方法
    if not (args.unicodes or args.text or args.text_file):
        print("错误: 请至少指定一种子集化方法 (--unicodes, --text 或 --text-file)")
        return False
    
    # 执行命令
    try:
        print(f"执行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print(f"子集化完成! 输出文件: {args.output}")
        original_size = os.path.getsize(args.font_file) / 1024
        subset_size = os.path.getsize(args.output) / 1024
        print(f"原始大小: {original_size:.2f} KB")
        print(f"子集大小: {subset_size:.2f} KB")
        print(f"压缩率: {(1 - subset_size/original_size) * 100:.2f}%")
        return True
    except subprocess.CalledProcessError as e:
        print(f"子集化过程中出现错误: {e}")
        return False
    except Exception as e:
        print(f"发生未知错误: {e}")
        return False

def main():
    args = parse_arguments()
    create_font_subset(args)

if __name__ == "__main__":
    main()