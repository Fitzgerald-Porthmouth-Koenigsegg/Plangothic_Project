#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ctypes
import sys
from fontlink import FontLinkManager


def check_admin_privileges():
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("警告: 建议以管理员权限运行此脚本以确保能够读取注册表")
            print()
    except:
        pass


def get_plangothic_config():
    registry_paths = {
        "64bit": r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink",
        "32bit": r"SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink"
    }

    append_fonts = {
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
        "Microsoft JhengHei UI Light",
        "Microsoft JhengHei UI",
        "Microsoft JhengHei",
        "Microsoft Sans Serif",
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
        "Segoe UI Semibold",
        "Segoe UI Semilight",
        "Segoe UI Bold",
        "Segoe UI Light",
        "Segoe UI",
        "SimSun",
        "SimSun-ExtB",
        "SimSun-ExtG",
        "SimSun-PUA",
        "Tahoma",
        "Times New Roman",
        "微軟正黑體",
        "微軟正黑體 Bold",
        "微软雅黑",
        "微软雅黑 Bold"
    }

    target_fonts = list(append_fonts)

    plangothic_entries = [
        "PlangothicP1-Regular.ttf,Plangothic P1",
        "PlangothicP1-Regular.otf,Plangothic P1",
        "PlangothicP2-Regular.ttf,Plangothic P2",
        "PlangothicP2-Regular.otf,Plangothic P2",
        "Plangothic.ttc,Plangothic P1",
        "Plangothic.ttc,Plangothic P2"
    ]

    return registry_paths, target_fonts, append_fonts, plangothic_entries

def main():
    print("字体链接配置备份和修改工具")
    print("=" * 50)

    check_admin_privileges()

    registry_paths, target_fonts, append_fonts, plangothic_entries = get_plangothic_config()

    manager = FontLinkManager(
        registry_paths=registry_paths,
        target_fonts=target_fonts,
        append_fonts=append_fonts,
        font_entries=plangothic_entries
    )

    success = manager.run_full_process()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
