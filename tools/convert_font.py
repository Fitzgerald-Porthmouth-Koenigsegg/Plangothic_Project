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
import sys
import argparse
import time
import logging
from typing import Dict, Optional, Tuple, Any, List
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# 常量定义
SUPPORTED_FORMATS = {
    'ttf': 'TrueType 字体 (.ttf)',
    'otf': 'OpenType 字体 (.otf)',
    'woff': 'Web Open Font Format (.woff)',
    'woff2': 'Web Open Font Format 2 (.woff2)',
    'eot': 'Embedded OpenType (.eot)',
    'svg': 'SVG 字体 (.svg)'
}

# 格式特定的转换标志
FORMAT_FLAGS = {
    'otf': ('opentype', 'round', 'dummy-dsig', 'apple'),
    'ttf': ('opentype', 'round', 'dummy-dsig', 'apple', 'short-post', 'old-kern'),
    'woff2': ('opentype', 'round', 'dummy-dsig', 'no-flex', 'no-hints', 'short-post', 'omit-instructions'),
    # 其他格式使用默认设置
}

try:
    import fontforge
except ModuleNotFoundError:
    logger.warning("当前没有使用 `fontforge` 运行，功能无法使用")
    fontforge = None


class FontConverter:
    """字体转换器类，封装所有字体处理逻辑"""
    
    def __init__(self, input_path: str, output_path: Optional[str] = None, 
                 format_type: str = 'woff2', family_name: Optional[str] = None, 
                 version: Optional[str] = None):
        """
        初始化字体转换器
        
        Args:
            input_path: 输入字体文件路径
            output_path: 输出字体文件路径（可选）
            format_type: 输出格式类型
            family_name: 字体族名称（可选）
            version: 字体版本号（可选）
        """
        self.input_path = input_path
        self.format_type = format_type
        self.family_name = family_name
        self.version = version
        
        # 如果未指定输出路径，根据输入文件名生成
        if not output_path:
            base_name = Path(input_path).stem
            self.output_path = f"{base_name}.{format_type}"
        else:
            self.output_path = output_path
            
        self.font = None
    
    def setup_font_properties(self) -> None:
        """设置字体属性"""
        if not self.font:
            return
            
        try:
            # 设置字体名称
            if self.family_name:
                self.font.familyname = self.family_name
                self.font.fontname = self.family_name.replace(' ', '')
                self.font.fullname = self.family_name
            
            # 设置版本号
            if self.version:
                self.font.version = self.version
            
            # 优化设置
            self._apply_optimization_settings()
                
        except Exception as e:
            logger.warning(f"设置字体属性时出现问题：{str(e)}")
    
    def _apply_optimization_settings(self) -> None:
        """应用字体优化设置"""
        try:
            # ClearType 优化
            self.font.head_optimized_for_cleartype = True
        except Exception:
            pass
            
        try:
            # 垂直度量设置
            self.font.os2_typoascent = self.font.ascent
            self.font.os2_typodescent = -self.font.descent
            self.font.os2_typolinegap = 0
            self.font.hhea_ascent = self.font.ascent
            self.font.hhea_descent = -self.font.descent
            self.font.hhea_linegap = 0
        except Exception:
            pass
            
        try:
            # 栅格化平滑设置
            self.font.gasp = {
                8: ('gridfit', 'antialias', 'symmetric-smoothing'),
                16: ('gridfit', 'antialias', 'symmetric-smoothing'),
                65535: ('gridfit', 'antialias', 'symmetric-smoothing')
            }
        except Exception:
            pass
    
    def convert(self) -> bool:
        """
        执行字体转换
        
        Returns:
            bool: 转换是否成功
        """
        if fontforge is None:
            logger.error("FontForge 模块未加载，无法进行转换")
            return False
            
        try:
            start_time = time.time()
    
            # 检查输入文件是否存在
            if not os.path.exists(self.input_path):
                raise FileNotFoundError(f"未找到字体文件：{self.input_path}")
    
            logger.info(f"正在加载字体：{self.input_path}")
            self.font = fontforge.open(self.input_path)
            
            # 设置字体属性
            self.setup_font_properties()
    
            logger.info(f"正在转换字体到 {self.format_type} 格式...")
            
            # 获取特定格式的标志，如果未定义则使用默认值
            flags = FORMAT_FLAGS.get(self.format_type, ())
            self.font.generate(self.output_path, flags=flags)
    
            # 计算并显示统计信息
            self._show_conversion_stats(start_time)
            
            return True
            
        except Exception as e:
            logger.error(f"转换过程中出现问题：{str(e)}")
            return False
        finally:
            # 确保关闭字体文件
            if self.font:
                try:
                    self.font.close()
                except Exception:
                    pass
    
    def _show_conversion_stats(self, start_time: float) -> None:
        """显示转换统计信息"""
        end_time = time.time()
        
        if not os.path.exists(self.output_path):
            logger.warning("无法找到输出文件，无法显示统计信息")
            return
            
        input_size = os.path.getsize(self.input_path) / 1024  # KB
        output_size = os.path.getsize(self.output_path) / 1024  # KB
        
        logger.info("\n转换完成：")
        logger.info(f"处理时间：{end_time - start_time:.2f} 秒")
        logger.info(f"源文件：{input_size:.2f} KB")
        logger.info(f"转换后：{output_size:.2f} KB")
        logger.info(f"大小变化：{((output_size/input_size)-1)*100:+.1f}%")
        
        logger.info(f"✓ 字体已保存为 {self.output_path}")


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='字体格式转换工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='\n'.join([
            "支持的格式：",
            *[f"  {fmt:<6} - {desc}" for fmt, desc in SUPPORTED_FORMATS.items()],
            "\n使用示例：",
            f"  fontforge -script {Path(__file__).name} input.ttf -o output.woff2 -f woff2"
        ])
    )
    
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

    return parser.parse_args()


def main() -> int:
    """主函数"""
    args = parse_arguments()
    
    if not args.input_font:
        return 1
        
    converter = FontConverter(
        args.input_font,
        args.output,
        args.format,
        args.family_name,
        args.version
    )
    
    success = converter.convert()
    
    # 交互模式下等待用户按键
    if sys.stdin.isatty():
        input("\n按回车键退出...")
        
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())