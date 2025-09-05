#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体链接配置备份和修改工具库
用于备份和修改 Windows 注册表中的字体链接配置
"""

import winreg
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
from .reg_multi_sz_converter import RegMultiSzConverter


class FontLinkManager:
    """字体链接管理器"""

    def __init__(self, registry_paths: Dict[str, str], target_fonts: List[str], 
                 append_fonts: Set[str], font_entries: List[str]):
        """
        初始化字体链接管理器

        Args:
            registry_paths: 注册表路径字典，格式: {"架构名": "注册表路径"}
            target_fonts: 目标字体列表
            append_fonts: 需要在末尾添加字体条目的字体集合
            font_entries: 要添加的字体条目列表
        """
        self.converter = RegMultiSzConverter()
        self.registry_paths = registry_paths
        self.target_fonts = target_fonts
        self.append_fonts = append_fonts
        self.font_entries = font_entries

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

                # 计算不存在的字体数量
                total_delete_count = sum(
                    1 for arch in self.registry_paths 
                    for font in self.target_fonts 
                    if self.read_registry_value(winreg.HKEY_LOCAL_MACHINE, self.registry_paths[arch], font) is None
                )

                print(f"\n备份完成！共处理 {backup_count + total_delete_count} 个字体配置到: {output_file}")
                return True

        except Exception as e:
            print(f"备份失败: {e}")
            return False

    def create_modified_reg(self, backup_file: str, output_file: str) -> bool:
        """
        创建修改后的 .reg 文件，对不同字体使用不同的插入策略

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
                f.write(f'; 说明: \n')
                f.write(f';   - 特定字体: 在末尾添加字体条目\n')
                f.write(f';   - 其他字体: 在开头添加字体条目\n\n')

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

                        # 判断是在末尾添加还是在开头添加
                        append_to_end = font_name in self.append_fonts

                        if font_links is not None:
                            # 已存在的字体：根据字体类型决定插入位置
                            if append_to_end:
                                # 在末尾添加
                                new_font_links = font_links.copy()
                                new_font_links.extend(self.font_entries)
                                insertion_info = "末尾"
                            else:
                                # 在开头添加
                                new_font_links = self.font_entries.copy()
                                new_font_links.extend(font_links)
                                insertion_info = "开头"

                            hex_data = self.converter.encode_to_hex_string(new_font_links, "regedit")
                            f.write(f'"{font_name}"={hex_data}\n')
                            path_modify_count += 1
                            modify_count += 1

                            print(f"已修改: [{arch}] {font_name} (在{insertion_info}添加)")
                            print(f"  原有条目: {len(font_links)} 个")
                            print(f"  新增条目: {len(self.font_entries)} 个")
                            print(f"  总计条目: {len(new_font_links)} 个")
                        else:
                            # 不存在的字体：创建新配置（统一在开头）
                            hex_data = self.converter.encode_to_hex_string(self.font_entries, "regedit")
                            f.write(f'"{font_name}"={hex_data}\n')
                            path_modify_count += 1
                            modify_count += 1
                            print(f"已创建: [{arch}] {font_name} (新配置，{len(self.font_entries)} 个条目)")

                    f.write('\n')
                    print(f"{arch} 路径修改完成: {path_modify_count} 个字体")

                print(f"\n修改版文件创建完成！共处理 {modify_count} 个字体配置")
                print(f"输出文件: {output_file}")
                print(f"\n插入策略:")
                print(f"  末尾添加: {', '.join(sorted(self.append_fonts))}")
                print(f"  开头添加: 其他所有字体")
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
                    insertion_strategy = "末尾添加" if font_name in self.append_fonts else "开头添加"
                    print(f"  {font_name} [{insertion_strategy}]:")
                    for i, link in enumerate(font_links, 1):
                        print(f"    {i}. {link}")
                    found_count += 1
                else:
                    print(f"  {font_name}: [未找到]")
                    not_found_count += 1
                print()
            
            print(f"  统计: {found_count} 个存在, {not_found_count} 个不存在")
            print()

    def run_full_process(self, backup_filename: Optional[str] = None, 
                        modified_filename: Optional[str] = None) -> bool:
        """
        运行完整的备份和修改流程

        Args:
            backup_filename: 备份文件名，如果为None则自动生成
            modified_filename: 修改文件名，如果为None则自动生成

        Returns:
            流程是否成功完成
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_filename or f"fontlink_backup_{timestamp}.reg"
        modified_file = modified_filename or f"fontlink_modified_{timestamp}.reg"

        try:
            print("1. 预览当前配置...")
            self.preview_current_config()

            print("2. 备份原始配置...")
            if not self.backup_font_links(backup_file):
                print("✗ 备份失败")
                return False
            print(f"✓ 备份成功: {backup_file}")
            print()

            print("3. 创建修改版配置...")
            if not self.create_modified_reg(backup_file, modified_file):
                print("✗ 修改版创建失败")
                return False
            print(f"✓ 修改版创建成功: {modified_file}")
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
            
            return True

        except KeyboardInterrupt:
            print("\n操作已取消")
            return False
        except Exception as e:
            print(f"发生错误: {e}")
            return False
