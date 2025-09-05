#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ctypes
from fontlink import FontLinkManager


def main():
    print("Custom font link configuration example")
    print("=" * 50)

    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("Warning: It is recommended to run this script with administrator privileges")
            print()
    except:
        pass

    registry_paths = {
        "64bit": r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink",
        "32bit": r"SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink"
    }

    target_fonts = [
        "Arial",
        "Segoe UI",
        "Times New Roman",
        "Tahoma",
    ]

    # All fonts are prefixed at the beginning (an empty set indicates no fonts were suffixed)
    append_fonts = set()

    custom_font_entries = [
        "SourceHanSansSC-Regular.otf,Source Han Sans SC",
        "SourceHanSansSC-Bold.otf,Source Han Sans SC Bold",
        "NotoSansCJK-Regular.ttc,Noto Sans CJK SC",
    ]

    manager = FontLinkManager(
        registry_paths=registry_paths,
        target_fonts=target_fonts,
        append_fonts=append_fonts,
        font_entries=custom_font_entries
    )

    manager.run_full_process(
        backup_filename="custom_font_backup.reg",
        modified_filename="custom_font_modified.reg"
    )


if __name__ == "__main__":
    main()
