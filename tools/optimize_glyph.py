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
import time
import argparse
import logging
from typing import List, Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

try:
    import fontforge
except ModuleNotFoundError:
    logger.error("警告：当前没有使用 `fontforge` 运行，功能无法使用")


class TimeFormatter:
    """时间格式化工具类"""
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """将秒数格式化为人类可读的时间格式"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"


class GlyphProcessor:
    """字形处理器类，处理单个字形的优化操作"""
    
    def __init__(self, simplify_value: float = 0.5):
        self.simplify_value = simplify_value
    
    @staticmethod
    def get_glyph_info(glyph) -> str:
        """获取字形的Unicode或名称信息"""
        try:
            if glyph.unicode != -1:
                return f"U+{glyph.unicode:04X}"
            else:
                return f"{glyph.glyphname}"
        except (ValueError, AttributeError):
            return f"{glyph.glyphname}"
    
    @staticmethod
    def process_compound_glyph(glyph) -> None:
        """处理复合字形，解除引用"""
        try:
            if len(glyph.references) > 0:
                try:
                    glyph.unlinkReferences()
                except (AttributeError, TypeError):
                    glyph.unlink()
        except (AttributeError, TypeError):
            pass
    
    @staticmethod
    def process_line_endpoints(glyph) -> None:
        """处理线条端点，优化接近水平或垂直的线段"""
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
    
    def process_glyph(self, glyph) -> None:
        """应用所有优化处理到单个字形"""
        # 解除复合字形引用
        self.process_compound_glyph(glyph)
        
        # 初步简化
        glyph.simplify(0.1, ('mergelines', 'choosehv'), 0.1, 0.1, 0)
        
        # 处理线段端点
        self.process_line_endpoints(glyph)
        
        # 主要简化和优化步骤
        glyph.simplify(self.simplify_value, 
                     ('mergelines', 'smoothcurves', 'removesingletonpoints'), 
                     0.3, 0, 0.5)
        glyph.addExtrema()
        glyph.canonicalContours()
        glyph.canonicalStart()
        glyph.simplify()
        glyph.removeOverlap()
        glyph.correctDirection()
        glyph.simplify(self.simplify_value, 
                     ('mergelines', 'smoothcurves'), 
                     0.3, 0, 0.5)
        glyph.round()
        glyph.autoHint()
        
        # 扩展优化
        self.optimize_glyph_extension(glyph)
    
    @staticmethod
    def optimize_glyph_extension(glyph) -> None:
        """应用扩展优化处理"""
        glyph.simplify(0.5, 
                     ('mergelines', 'smoothcurves', 'choosehv', 'removesingletonpoints'), 
                     0.3, 0, 0.5)
        glyph.addExtrema()
        glyph.width = int(round(glyph.width / 10.0) * 10)
        glyph.balance()
        glyph.autoHint()


class ProgressTracker:
    """进度跟踪器类，管理进度显示和时间估计"""
    
    def __init__(self, total: int):
        self.total = total
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.time_formatter = TimeFormatter()
        
        logger.info(f"开始处理字体，共 {total} 个字形...")
        print("进度", end="")
    
    def update(self, current: int, glyph_info: str) -> None:
        """更新并显示进度"""
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        progress = current / self.total if self.total > 0 else 0

        # 计算剩余时间估计
        if current > 0 and elapsed_time > 0:
            glyphs_per_second = current / elapsed_time
            remaining_glyphs = self.total - current
            estimated_remaining_time = remaining_glyphs / glyphs_per_second
        else:
            estimated_remaining_time = 0

        # 限制更新频率，减少屏幕刷新
        if current_time - self.last_update_time >= 0.2:
            self._display_progress(
                current, 
                progress, 
                elapsed_time, 
                estimated_remaining_time, 
                glyph_info
            )
            self.last_update_time = current_time
    
    def _display_progress(self, current: int, progress: float, 
                         elapsed_time: float, remaining_time: float, 
                         glyph_info: str) -> None:
        """显示进度条和相关信息"""
        bar_length = 30
        filled_length = int(bar_length * progress)
        bar = "#" * filled_length + "-" * (bar_length - filled_length)
        
        formatted_elapsed = self.time_formatter.format_time(elapsed_time)
        formatted_remaining = self.time_formatter.format_time(remaining_time)
        
        print(f"\r进度({current}/{self.total}): [{bar}] ({progress:.1%}) "
              f"⏱️ {formatted_elapsed} ⏳ {formatted_remaining} "
              f"⚡ 当前处理: {glyph_info}", end="", flush=True)
    
    def complete(self) -> None:
        """完成进度显示"""
        total_time = time.time() - self.start_time
        bar = "=" * 30
        print(f"\n进度({self.total}/{self.total}): [{bar}] (100%) "
              f"⏱️ 总用时: {self.time_formatter.format_time(total_time)}")


class FontOptimizer:
    """字体优化器类，管理整个字体文件的处理流程"""
    
    def __init__(self, simplify_value: float = 0.5):
        self.simplify_value = simplify_value
        self.glyph_processor = GlyphProcessor(simplify_value)
    
    def process_font(self, input_file: str) -> Optional[str]:
        """处理整个字体文件，优化所有字形"""
        try:
            font = fontforge.open(input_file)
        except OSError as e:
            logger.error(f"错误：无法打开字体文件 - {e}")
            return None
        
        glyphs = list(font.glyphs())
        total_glyphs = len(glyphs)

        if total_glyphs == 0:
            logger.warning("警告：没有找到可处理的字形")
            return None

        # 初始化进度跟踪器
        progress = ProgressTracker(total_glyphs)

        # 处理每个字形
        for index, glyph in enumerate(glyphs):
            glyph_info = self.glyph_processor.get_glyph_info(glyph)
            progress.update(index + 1, glyph_info)
            
            try:
                self.glyph_processor.process_glyph(glyph)
            except Exception as e:
                logger.warning(f"处理字形 {glyph_info} 时出错: {e}")
                continue

        # 完成进度显示
        progress.complete()
        
        # 保存新字体
        return self._save_font(font, input_file)
    
    def _save_font(self, font, input_file: str) -> str:
        """保存处理后的字体文件"""
        logger.info("新字体保存中...")
        
        file_name, file_extension = os.path.splitext(input_file)
        output_file = f"{file_name}_merge_glyphs{file_extension}"
        
        try:
            font.generate(output_file, 
                         flags=('opentype', 'round', 'dummy-dsig', 'apple'))
            logger.info(f"新字体已保存为: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"保存字体失败: {e}")
            return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='字体轮廓优化工具')
    parser.add_argument('font_file', nargs='?', help='字体文件路径')
    parser.add_argument('-s', '--simplify', type=float, default=0.5, 
                      help='simplify 参数值 (默认: 0.5)')
    
    args = parser.parse_args()

    if not args.font_file:
        logger.error("没有选择字体")
        input("按回车键退出...")
        sys.exit(1)

    try:
        logger.info(f"使用 simplify 参数值: {args.simplify}")
        optimizer = FontOptimizer(args.simplify)
        output_file = optimizer.process_font(args.font_file)
        
        if output_file:
            logger.info("处理完成！")
        else:
            logger.error("处理失败！")
    except Exception as e:
        logger.error(f"发生严重错误：{str(e)}")
        input("按回车键退出...")


if __name__ == "__main__":
    main()