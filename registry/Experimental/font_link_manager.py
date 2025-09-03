#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体链接配置备份和修改工具
用于备份和修改 Windows 注册表中的字体链接配置

需要配合 reg_multi_sz_converter 库使用
"""

import winreg
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from reg_multi_sz_converter import RegMultiSzConverter


class FontLinkManager:
    """字体链接管理器"""

    def __init__(self):
        self.converter = RegMultiSzConverter()

        self.registry_paths = {
            "64bit": r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink",
            "32bit": r"SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink"
        }

        self.target_fonts = [
            "Arial",
            "Batang",
            "BatangChe",
            "Dotum",
            "DotumChe",
            "Gulim",
            "GulimChe",
            "Gungsuh",
            "GungsuhChe",
            "Lucida Sans Unicode",
            "Malgun Gothic Bold",
            "Malgun Gothic",
            "Meiryo Bold",
            "Meiryo UI Bold",
            "Meiryo UI",
            "Meiryo",
            "Microsoft JhengHei Bold",
            "Microsoft JhengHei UI Bold",
            "Microsoft JhengHei UI",
            "Microsoft JhengHei",
            "Microsoft YaHei Bold",
            "Microsoft YaHei UI Bold",
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "MingLiU",
            "MingLiU_HKSCS",
            "MingLiU_HKSCS-ExtB",
            "MingLiU-ExtB",
            "MS Gothic",
            "MS Mincho",
            "MS PGothic",
            "MS PMincho",
            "MS UI Gothic",
            "NSimSun",
            "PMingLiU",
            "PMingLiU-ExtB",
            "SimSun",
            "SimSun-ExtB",
            "SimSun-PUA",
            "Tahoma",
            "Times New Roman",
            "微軟正黑體",
            "微軟正黑體 Bold",
            "微软雅黑",
            "微软雅黑 Bold",
        ]

        self.plangothic_entries = [
            "PlangothicP1-Regular.ttf,Plangothic P1",
            "PlangothicP1-Regular.otf,Plangothic P1",
            "PlangothicP2-Regular.ttf,Plangothic P2",
            "PlangothicP2-Regular.otf,Plangothic P2",
            "Plangothic.ttc,Plangothic P1",
            "Plangothic.ttc,Plangothic P2"
        ]

    def read_registry_value(self, hkey: int, path: str, value_name: str) -> Optional[List[str]]:
        """
        读取注册表中的 REG_MULTI_SZ 值

        Args:
            hkey: 注册表根键（如 winreg.HKEY_LOCAL_MACHINE）
            path: 注册表路径
            value_name: 值名称

        Returns:
            字符串列表，如果读取失败返回 None
        """
        try:
            with winreg.OpenKey(hkey, path, 0, winreg.KEY_READ) as key:
                value, reg_type = winreg.QueryValueEx(key, value_name)
                if reg_type == winreg.REG_MULTI_SZ:
                    return value
                else:
                    print(f"警告: {value_name} 不是 REG_MULTI_SZ 类型")
                    return None
        except FileNotFoundError:
            return None
        except PermissionError:
            print(f"权限不足，无法读取: {path}\\{value_name}")
            return None
        except Exception as e:
            print(f"读取注册表失败: {path}\\{value_name} - {e}")
            return None

    def backup_font_links(self, output_file: str) -> bool:
        """
        备份字体链接配置到 .reg 文件

        Args:
            output_file: 输出的 .reg 文件路径

        Returns:
            备份是否成功
        """
        try:
            with open(output_file, 'w', encoding='utf-16le') as f:
                f.write('\ufeff')
                f.write('Windows Registry Editor Version 5.00\n\n')
                f.write(f'; 字体链接配置备份\n')
                f.write(f'; 备份时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')

                backup_count = 0

                for arch, reg_path in self.registry_paths.items():
                    f.write(f'; {arch} 配置\n')
                    f.write(f'[HKEY_LOCAL_MACHINE\\{reg_path}]\n')

                    path_backup_count = 0
                    path_delete_count = 0

                    for font_name in self.target_fonts:
                        font_links = self.read_registry_value(
                            winreg.HKEY_LOCAL_MACHINE,
                            reg_path,
                            font_name
                        )

                        if font_links is not None:
                            # 存在的值：正常备份
                            hex_data = self.converter.encode_to_hex_string(font_links, "regedit")
                            f.write(f'"{font_name}"={hex_data}\n')
                            path_backup_count += 1
                            backup_count += 1
                            print(f"已备份: [{arch}] {font_name} ({len(font_links)} 个条目)")
                        else:
                            # 不存在的值：添加删除条目
                            f.write(f'"{font_name}"=-\n')
                            path_delete_count += 1
                            print(f"已标记删除: [{arch}] {font_name} (原本不存在)")

                    f.write('\n')
                    print(f"{arch} 路径处理完成: {path_backup_count} 个备份, {path_delete_count} 个删除标记")

                print(f"\n备份完成！共处理 {backup_count + sum(1 for arch in self.registry_paths for font in self.target_fonts if self.read_registry_value(winreg.HKEY_LOCAL_MACHINE, self.registry_paths[arch], font) is None)} 个字体配置到: {output_file}")
                return True

        except Exception as e:
            print(f"备份失败: {e}")
            return False

    def create_modified_reg(self, backup_file: str, output_file: str) -> bool:
        """
        创建修改后的 .reg 文件，在每个字体的条目开头添加 Plangothic 字体

        Args:
            backup_file: 备份文件路径
            output_file: 输出文件路径

        Returns:
            创建是否成功
        """
        try:
            with open(output_file, 'w', encoding='utf-16le') as f:
                f.write('\ufeff')
                f.write('Windows Registry Editor Version 5.00\n\n')
                f.write(f'; 修改后的字体链接配置\n')
                f.write(f'; 基于备份文件: {os.path.basename(backup_file)}\n')
                f.write(f'; 修改时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'; 说明: 在每个字体的链接列表开头添加了 Plangothic 字体\n\n')

                modify_count = 0

                for arch, reg_path in self.registry_paths.items():
                    f.write(f'; {arch} 配置 - 修改版\n')
                    f.write(f'[HKEY_LOCAL_MACHINE\\{reg_path}]\n')

                    path_modify_count = 0

                    for font_name in self.target_fonts:
                        font_links = self.read_registry_value(
                            winreg.HKEY_LOCAL_MACHINE,
                            reg_path,
                            font_name
                        )

                        if font_links is not None:
                            # 已存在的字体：在开头添加 Plangothic 字体
                            new_font_links = self.plangothic_entries.copy()
                            new_font_links.extend(font_links)

                            hex_data = self.converter.encode_to_hex_string(new_font_links, "regedit")
                            f.write(f'"{font_name}"={hex_data}\n')
                            path_modify_count += 1
                            modify_count += 1

                            print(f"已修改: [{arch}] {font_name}")
                            print(f"  原有条目: {len(font_links)} 个")
                            print(f"  新增条目: {len(self.plangothic_entries)} 个")
                            print(f"  总计条目: {len(new_font_links)} 个")
                        else:
                            # 不存在的字体：创建新配置
                            hex_data = self.converter.encode_to_hex_string(self.plangothic_entries, "regedit")
                            f.write(f'"{font_name}"={hex_data}\n')
                            path_modify_count += 1
                            modify_count += 1
                            print(f"已创建: [{arch}] {font_name} (新配置，{len(self.plangothic_entries)} 个条目)")

                    f.write('\n')
                    print(f"{arch} 路径修改完成: {path_modify_count} 个字体")

                print(f"\n修改版文件创建完成！共处理 {modify_count} 个字体配置")
                print(f"输出文件: {output_file}")
                return True

        except Exception as e:
            print(f"创建修改版文件失败: {e}")
            return False

    def preview_current_config(self):
        """预览当前的字体链接配置"""
        print("=== 当前字体链接配置 ===\n")

        for arch, reg_path in self.registry_paths.items():
            print(f"[{arch.upper()}] {reg_path}")
            print("-" * 60)

            found_count = 0
            not_found_count = 0

            for font_name in self.target_fonts:
                font_links = self.read_registry_value(
                    winreg.HKEY_LOCAL_MACHINE,
                    reg_path,
                    font_name
                )

                if font_links is not None:
                    print(f"  {font_name}:")
                    for i, link in enumerate(font_links, 1):
                        print(f"    {i}. {link}")
                    found_count += 1
                else:
                    print(f"  {font_name}: [未找到]")
                    not_found_count += 1
                print()
            
            print(f"  统计: {found_count} 个存在, {not_found_count} 个不存在")
            print()


def main():
    """主函数"""
    print("字体链接配置备份和修改工具")
    print("=" * 50)

    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("警告: 建议以管理员权限运行此脚本以确保能够读取注册表")
            print()
    except:
        pass

    manager = FontLinkManager()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"fontlink_backup_{timestamp}.reg"
    modified_file = f"fontlink_modified_{timestamp}.reg"

    try:
        print("1. 预览当前配置...")
        manager.preview_current_config()

        print("2. 备份原始配置...")
        if manager.backup_font_links(backup_file):
            print(f"✓ 备份成功: {backup_file}")
        else:
            print("✗ 备份失败")
            return

        print()

        print("3. 创建修改版配置...")
        if manager.create_modified_reg(backup_file, modified_file):
            print(f"✓ 修改版创建成功: {modified_file}")
        else:
            print("✗ 修改版创建失败")
            return

        print()
        print("=" * 50)
        print("操作完成！")
        print(f"备份文件: {backup_file}")
        print(f"修改文件: {modified_file}")
        print()
        print("使用说明:")
        print("1. 双击 .reg 文件可以导入到注册表")
        print("2. 建议先备份当前配置，然后再导入修改版")
        print("3. 如需恢复，可以导入备份文件")
        print("4. 修改注册表后可能需要重启或重新登录才能生效")
        print("5. 备份文件中 '字体名'=- 表示删除该注册表项")

    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    main()