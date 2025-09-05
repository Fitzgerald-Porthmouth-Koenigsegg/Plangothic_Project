#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Registry REG_MULTI_SZ Encoder/Decoder
用于编码和解码 Windows 注册表中的 REG_MULTI_SZ 数据格式

可以作为库导入使用，也可以直接运行作为命令行工具。

Example:
    作为库使用:
        from reg_multi_sz_converter import RegMultiSzConverter

        converter = RegMultiSzConverter()

        # 解码
        strings = converter.decode_hex_string(hex_data)

        # 编码
        hex_data = converter.encode_to_hex_string(strings)

    作为命令行工具使用:
        python reg_multi_sz_converter.py
"""

import re
import sys
from typing import List, Union


class RegMultiSzConverter:
    """Windows 注册表 REG_MULTI_SZ 数据转换器"""

    def decode_hex_string(self, hex_string: str) -> List[str]:
        """
        解码注册表中的 hex(7): 格式字符串为可读的字符串列表

        Args:
            hex_string: 形如 "hex(7):50,00,6c,00,61,00,6e,00,67,00,..." 的字符串

        Returns:
            解码后的字符串列表

        Raises:
            ValueError: 当输入数据格式无效时
        """
        hex_data = re.sub(r'^hex\(7\):\s*', '', hex_string, flags=re.IGNORECASE)

        hex_data = re.sub(r'\\\s*\n\s*', '', hex_data)
        hex_data = re.sub(r'\\\s*$', '', hex_data, flags=re.MULTILINE)

        hex_data = re.sub(r'\s', '', hex_data)

        hex_bytes = [b.strip() for b in hex_data.split(',') if b.strip()]

        try:
            byte_array = bytearray()
            for hex_byte in hex_bytes:
                if hex_byte:
                    byte_array.append(int(hex_byte, 16))
        except ValueError as e:
            raise ValueError(f"无效的十六进制数据: '{hex_byte}' - {e}")

        try:
            decoded_string = byte_array.decode('utf-16le')
        except UnicodeDecodeError as e:
            raise ValueError(f"UTF-16LE 解码失败: {e}")

        strings = decoded_string.rstrip('\x00').split('\x00')

        return [s for s in strings if s]

    def encode_to_hex_string(self, strings: Union[List[str], str], format_style: str = "regedit") -> str:
        """
        将字符串列表编码为注册表 hex(7): 格式

        Args:
            strings: 要编码的字符串列表，或单个字符串
            format_style: 格式化样式，"regedit" 或 "compact"

        Returns:
            编码后的 hex(7): 格式字符串

        Raises:
            ValueError: 当输入参数无效时
        """
        if isinstance(strings, str):
            strings = [strings]

        if not strings:
            raise ValueError("字符串列表不能为空")

        combined_string = '\x00'.join(strings) + '\x00\x00'

        byte_data = combined_string.encode('utf-16le')

        hex_bytes = [f"{b:02x}" for b in byte_data]

        if format_style == "compact":
            return "hex(7):" + ",".join(hex_bytes)
        elif format_style == "regedit":
            result = "hex(7):"
            line_length = 7
            max_line_length = 75

            for i, hex_byte in enumerate(hex_bytes):
                if i == 0:
                    result += hex_byte
                    line_length += len(hex_byte)
                else:
                    addition = "," + hex_byte
                    if line_length + len(addition) > max_line_length:
                        result += ",\\\n  " + hex_byte
                        line_length = 2 + len(hex_byte)
                    else:
                        result += addition
                        line_length += len(addition)

            return result
        else:
            raise ValueError(f"不支持的格式样式: {format_style}")

    @staticmethod
    def is_hex_data(text: str) -> bool:
        """
        判断输入是否为 hex(7): 格式的数据

        Args:
            text: 要检查的文本

        Returns:
            如果是 hex(7): 格式返回 True，否则返回 False
        """
        return bool(re.search(r'hex\(7\):', text, re.IGNORECASE))


def decode_registry_hex(hex_string: str) -> List[str]:
    """
    便捷函数：解码注册表 hex(7): 数据

    Args:
        hex_string: hex(7): 格式的字符串

    Returns:
        解码后的字符串列表
    """
    converter = RegMultiSzConverter()
    return converter.decode_hex_string(hex_string)


def encode_to_registry_hex(strings: Union[List[str], str], format_style: str = "regedit") -> str:
    """
    便捷函数：编码字符串列表为注册表 hex(7): 格式

    Args:
        strings: 要编码的字符串列表或单个字符串
        format_style: 格式化样式，"regedit" 或 "compact"

    Returns:
        编码后的 hex(7): 格式字符串
    """
    converter = RegMultiSzConverter()
    return converter.encode_to_hex_string(strings, format_style)


def main():
    """命令行工具主函数"""
    converter = RegMultiSzConverter()

    print("Windows 注册表 REG_MULTI_SZ 编码/解码工具")
    print("请输入数据 (以空行结束):")
    print("- 如果以 hex(7): 开头，将自动解码")
    print("- 否则将作为字符串列表进行编码")
    print("-" * 50)

    lines = []
    try:
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line)
    except KeyboardInterrupt:
        print("\n\n程序已退出")
        sys.exit(0)

    if not lines:
        print("没有输入任何数据!")
        return

    input_text = "\n".join(lines)

    if converter.is_hex_data(input_text):
        print("\n检测到 hex(7): 格式数据，正在解码...")
        try:
            decoded_strings = converter.decode_hex_string(input_text)
            print("\n解码结果:")
            for i, s in enumerate(decoded_strings, 1):
                print(f"  {i}. {s}")
        except Exception as e:
            print(f"\n解码失败: {e}")
            print("请检查输入的十六进制数据格式是否正确")
    else:
        print("\n检测到普通文本，正在编码为 hex(7): 格式...")
        strings = [line.strip() for line in lines if line.strip()]

        if not strings:
            print("没有有效的字符串!")
            return

        try:
            encoded_hex = converter.encode_to_hex_string(strings, "regedit")
            print("\n编码结果:")
            print(encoded_hex)
        except Exception as e:
            print(f"\n编码失败: {e}")


if __name__ == "__main__":
    main()