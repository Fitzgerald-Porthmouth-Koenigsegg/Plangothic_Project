#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    collections::HashMap,
    ffi::OsStr,
    iter::once,
    os::windows::ffi::OsStrExt,
    sync::OnceLock,
};

use windows::{
    core::*,
    Win32::{
        Foundation::*,
        Graphics::Gdi::*,
        System::{
            LibraryLoader::GetModuleHandleW,
            Registry::*,
        },
        UI::{
            Controls::*,
            WindowsAndMessaging::*,
        },
    },
};

// 控件ID
const IDI_MAIN_ICON: u16 = 101;
const ID_LISTVIEW: i32 = 1001;
const ID_STATUS_BAR: i32 = 1002;
const ID_HEADER_STATIC: i32 = 1003;

// ListView 列索引
const COL_FONT_NAME: i32 = 0;
const COL_PREVIEW: i32 = 1;
const COL_FONTLINK_STATUS: i32 = 2;
const COL_FONTLINK_INFO: i32 = 3;

// Static控件样式常量
const SS_CENTER: u32 = 0x00000001;
const SS_CENTERIMAGE: u32 = 0x00000200;

// 字体缓存 - 添加预览字体专用缓存
static HEADER_FONT: OnceLock<HFONT> = OnceLock::new();
static LISTVIEW_FONT: OnceLock<HFONT> = OnceLock::new();
static PREVIEW_FONT_CACHE: OnceLock<HashMap<String, HFONT>> = OnceLock::new();
static HEADER_BRUSH: OnceLock<HBRUSH> = OnceLock::new();

// 添加列宽度缓存
static mut COL_WIDTHS: [i32; 4] = [200, 300, 80, 400];

// 数据项
#[derive(Clone)]
struct FontItem {
    name: String,
    has_fontlink: bool,
    link_text: String,
}

static FONT_ITEMS: OnceLock<Vec<FontItem>> = OnceLock::new();

// 常见系统字体
const SYSTEM_FONTS: &[&str] = &[
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
    "微软雅黑 Bold",
];

const TEST_TEXT: &str = "包罗万象化春外，最美全年天地中";

fn to_wide_string(s: &str) -> Vec<u16> {
    OsStr::new(s).encode_wide().chain(once(0)).collect()
}

fn from_wide_string(wide: &[u16]) -> String {
    let mut len = wide.len();
    if len > 0 && wide[len - 1] == 0 {
        len -= 1;
    }
    String::from_utf16_lossy(&wide[..len])
}

// 读取FontLink注册表信息
unsafe fn read_font_link_registry() -> HashMap<String, String> {
    let mut font_links = HashMap::new();

    let key_path = to_wide_string(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink");
    let mut hkey = HKEY::default();

    if RegOpenKeyExW(
        HKEY_LOCAL_MACHINE,
        PCWSTR(key_path.as_ptr()),
        0,
        KEY_READ,
        &mut hkey,
    ).is_ok() {
        let mut index = 0;
        loop {
            let mut value_name = vec![0u16; 256];
            let mut value_name_len = value_name.len() as u32;
            let mut value_data = vec![0u8; 8192];
            let mut value_data_len = value_data.len() as u32;
            let mut value_type: u32 = 0;

            let result = RegEnumValueW(
                hkey,
                index,
                PWSTR(value_name.as_mut_ptr()),
                &mut value_name_len,
                None,
                Some(&mut value_type),
                Some(value_data.as_mut_ptr()),
                Some(&mut value_data_len),
            );

            if result.is_err() {
                break;
            }

            value_name.truncate(value_name_len as usize);
            let font_name = from_wide_string(&value_name);

            if value_type == REG_MULTI_SZ.0 {
                value_data.truncate(value_data_len as usize);
                let wide_data = value_data
                    .chunks_exact(2)
                    .map(|chunk| u16::from_le_bytes([chunk[0], chunk[1]]))
                    .collect::<Vec<_>>();
                let links = from_wide_string(&wide_data);
                font_links.insert(font_name, links);
            }

            index += 1;
        }

        let _ = RegCloseKey(hkey);
    }

    font_links
}

// 优化的字体创建函数 - 使用CreateFontIndirect以更好地支持FontLink
unsafe fn create_font_with_logfont(height: i32, face_name: &str, weight: i32) -> HFONT {
    let mut logfont = LOGFONTW::default();
    logfont.lfHeight = height;
    logfont.lfWeight = weight;
    logfont.lfCharSet = FONT_CHARSET(DEFAULT_CHARSET.0 as u8);
    logfont.lfOutPrecision = FONT_OUTPUT_PRECISION(OUT_TT_PRECIS.0 as u8); // 使用TrueType优先
    logfont.lfClipPrecision = FONT_CLIP_PRECISION(CLIP_DEFAULT_PRECIS.0 as u8);
    logfont.lfQuality = FONT_QUALITY(CLEARTYPE_QUALITY.0 as u8);
    logfont.lfPitchAndFamily = (DEFAULT_PITCH.0 | FF_DONTCARE.0) as u8;
    
    let wide_name = to_wide_string(face_name);
    let copy_len = (wide_name.len() - 1).min(31);
    for i in 0..copy_len {
        logfont.lfFaceName[i] = wide_name[i];
    }
    
    CreateFontIndirectW(&logfont)
}

// 创建字体
unsafe fn create_font_by_name(height: i32, face_name: &str, weight: i32, italic: bool) -> HFONT {
    let wide = to_wide_string(face_name);
    CreateFontW(
        height,
        0,
        0,
        0,
        weight,
        if italic { 1 } else { 0 },
        0,
        0,
        DEFAULT_CHARSET.0 as u32,
        OUT_DEFAULT_PRECIS.0 as u32,
        CLIP_DEFAULT_PRECIS.0 as u32,
        CLEARTYPE_QUALITY.0 as u32,
        (DEFAULT_PITCH.0 | FF_DONTCARE.0) as u32,
        PCWSTR(wide.as_ptr()),
    )
}

// 获取系统默认字体
unsafe fn get_system_font() -> HFONT {
    let mut ncm = NONCLIENTMETRICSW {
        cbSize: std::mem::size_of::<NONCLIENTMETRICSW>() as u32,
        ..Default::default()
    };
    
    if SystemParametersInfoW(SPI_GETNONCLIENTMETRICS, ncm.cbSize, Some(&mut ncm as *mut _ as *mut _), SYSTEM_PARAMETERS_INFO_UPDATE_FLAGS(0)).is_ok() {
        CreateFontIndirectW(&ncm.lfMessageFont)
    } else {
        create_font_by_name(-12, "Segoe UI", FW_NORMAL.0 as i32, false)
    }
}

// 获取ListView列宽度
unsafe fn get_listview_column_widths(hwnd_listview: HWND) {
    for i in 0..4 {
        COL_WIDTHS[i] = SendMessageW(hwnd_listview, LVM_GETCOLUMNWIDTH, WPARAM(i), LPARAM(0)).0 as i32;
    }
}

// 初始化ListView
unsafe fn init_listview(hwnd_listview: HWND) {
    // 设置ListView为Owner Draw模式
    let style = GetWindowLongW(hwnd_listview, GWL_STYLE) as u32;
    SetWindowLongW(hwnd_listview, GWL_STYLE, (style | LVS_OWNERDRAWFIXED as u32) as i32);

    // 设置ListView扩展样式 - 添加双缓冲
    let extended_style = LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES | LVS_EX_DOUBLEBUFFER;
    SendMessageW(hwnd_listview, LVM_SETEXTENDEDLISTVIEWSTYLE, WPARAM(0), LPARAM(extended_style as isize));

    // 设置ListView为详细视图
    SendMessageW(hwnd_listview, LVM_SETVIEW, WPARAM(LV_VIEW_DETAILS as usize), LPARAM(0));

    // 添加列
    let mut lvc = LVCOLUMNW {
        mask: LVCF_TEXT | LVCF_WIDTH | LVCF_SUBITEM,
        fmt: LVCFMT_LEFT,
        cx: 200,
        pszText: PWSTR(to_wide_string("字体名称").as_mut_ptr()),
        cchTextMax: 0,
        iSubItem: COL_FONT_NAME,
        iImage: 0,
        iOrder: 0,
        cxMin: 0,
        cxDefault: 0,
        cxIdeal: 0,
    };
    SendMessageW(hwnd_listview, LVM_INSERTCOLUMNW, WPARAM(COL_FONT_NAME as usize), LPARAM(&lvc as *const _ as isize));

    lvc.cx = 300;
    lvc.pszText = PWSTR(to_wide_string("预览").as_mut_ptr());
    lvc.iSubItem = COL_PREVIEW;
    SendMessageW(hwnd_listview, LVM_INSERTCOLUMNW, WPARAM(COL_PREVIEW as usize), LPARAM(&lvc as *const _ as isize));

    lvc.cx = 80;
    lvc.pszText = PWSTR(to_wide_string("FontLink").as_mut_ptr());
    lvc.iSubItem = COL_FONTLINK_STATUS;
    SendMessageW(hwnd_listview, LVM_INSERTCOLUMNW, WPARAM(COL_FONTLINK_STATUS as usize), LPARAM(&lvc as *const _ as isize));

    lvc.cx = 400;
    lvc.pszText = PWSTR(to_wide_string("FontLink配置").as_mut_ptr());
    lvc.iSubItem = COL_FONTLINK_INFO;
    SendMessageW(hwnd_listview, LVM_INSERTCOLUMNW, WPARAM(COL_FONTLINK_INFO as usize), LPARAM(&lvc as *const _ as isize));

    // 设置字体
    if let Some(font) = LISTVIEW_FONT.get() {
        SendMessageW(hwnd_listview, WM_SETFONT, WPARAM(font.0 as usize), LPARAM(1));
    }

    // 设置项目高度以提供更好的显示效果
    SendMessageW(hwnd_listview, LVM_SETITEMCOUNT, WPARAM(0), LPARAM(24));

    // 填充数据
    if let Some(items) = FONT_ITEMS.get() {
        for (i, _item) in items.iter().enumerate() {
            let lvi = LVITEMW {
                mask: LVIF_TEXT | LVIF_PARAM,
                iItem: i as i32,
                iSubItem: 0,
                state: LIST_VIEW_ITEM_STATE_FLAGS(0),
                stateMask: LIST_VIEW_ITEM_STATE_FLAGS(0),
                pszText: PWSTR::null(), // Owner draw模式下不需要设置文本
                cchTextMax: 0,
                iImage: 0,
                lParam: LPARAM(i as isize),
                iIndent: 0,
                iGroupId: 0,
                cColumns: 0,
                puColumns: std::ptr::null_mut(),
                piColFmt: std::ptr::null_mut(),
                iGroup: 0,
            };
            
            SendMessageW(hwnd_listview, LVM_INSERTITEMW, WPARAM(0), LPARAM(&lvi as *const _ as isize));
        }
    }

    // 更新列宽度缓存
    get_listview_column_widths(hwnd_listview);
}

// 初始化状态栏
unsafe fn init_status_bar(hwnd_parent: HWND) -> HWND {
    let hwnd_status = CreateWindowExW(
        WINDOW_EX_STYLE(0),
        STATUSCLASSNAMEW,
        PCWSTR::null(),
        WS_CHILD | WS_VISIBLE | WINDOW_STYLE(SBARS_SIZEGRIP),
        0, 0, 0, 0,
        hwnd_parent,
        HMENU(ID_STATUS_BAR as isize),
        GetModuleHandleW(None).unwrap(),
        None,
    );

    if hwnd_status.0 != 0 {
        let parts = [200, 400, -1i32];
        SendMessageW(hwnd_status, SB_SETPARTS, WPARAM(parts.len()), LPARAM(parts.as_ptr() as isize));
        
        let text1 = to_wide_string("字体回退测试工具");
        let text2 = to_wide_string("检查系统FontLink配置");
        let text3 = to_wide_string("✅=有配置 ❌=无配置");
        
        SendMessageW(hwnd_status, SB_SETTEXTW, WPARAM(0), LPARAM(text1.as_ptr() as isize));
        SendMessageW(hwnd_status, SB_SETTEXTW, WPARAM(1), LPARAM(text2.as_ptr() as isize));
        SendMessageW(hwnd_status, SB_SETTEXTW, WPARAM(2), LPARAM(text3.as_ptr() as isize));
    }

    hwnd_status
}

// 简化的视觉样式设置
unsafe fn enable_visual_styles(_hwnd: HWND) {
    // 移除可能导致透明背景的DWM设置
    // 只保留基本的DPI感知
}

// 优化的Owner Draw处理函数
unsafe fn handle_owner_draw_listview(draw_item: &DRAWITEMSTRUCT) -> LRESULT {
    if let Some(items) = FONT_ITEMS.get() {
        let item_index = draw_item.itemID as usize;
        if item_index < items.len() {
            let item = &items[item_index];
            let rect = draw_item.rcItem;
            
            // 创建内存DC进行双缓冲绘制
            let mem_dc = CreateCompatibleDC(draw_item.hDC);
            let width = rect.right - rect.left;
            let height = rect.bottom - rect.top;
            let bitmap = CreateCompatibleBitmap(draw_item.hDC, width, height);
            let old_bitmap = SelectObject(mem_dc, HGDIOBJ(bitmap.0 as isize));
            
            // 设置背景
            let bg_color = if (draw_item.itemState.0 & ODS_SELECTED.0) != 0 {
                GetSysColor(COLOR_HIGHLIGHT)
            } else {
                0x00FFFFFF
            };
            
            let bg_brush = CreateSolidBrush(COLORREF(bg_color));
            let mem_rect = RECT { left: 0, top: 0, right: width, bottom: height };
            FillRect(mem_dc, &mem_rect, bg_brush);
            DeleteObject(bg_brush);
            
            // 设置文本背景为透明
            SetBkMode(mem_dc, TRANSPARENT);
            
            let mut col_left = 0i32;
            
            // 绘制每一列
            for col_index in 0..4 {
                let col_width = COL_WIDTHS[col_index];
                let mut col_rect = RECT {
                    left: col_left,
                    top: 0,
                    right: col_left + col_width - 1, // 减1避免重叠
                    bottom: height,
                };
                
                // 添加内边距
                col_rect.left += 4;
                col_rect.right -= 4;
                col_rect.top += 2;
                col_rect.bottom -= 2;
                
                match col_index {
                    0 => {
                        // 字体名称列
                        if let Some(font) = LISTVIEW_FONT.get() {
                            SelectObject(mem_dc, HGDIOBJ(font.0 as isize));
                        }
                        
                        let text_color = if (draw_item.itemState.0 & ODS_SELECTED.0) != 0 {
                            GetSysColor(COLOR_HIGHLIGHTTEXT)
                        } else {
                            0x00000000
                        };
                        SetTextColor(mem_dc, COLORREF(text_color));
                        
                        let mut font_name = to_wide_string(&item.name);
                        DrawTextW(
                            mem_dc,
                            &mut font_name,
                            &mut col_rect,
                            DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS,
                        );
                    }
                    1 => {
                        // 预览列 - 使用缓存的字体以启用FontLink
                        if let Some(font_cache) = PREVIEW_FONT_CACHE.get() {
                            if let Some(preview_font) = font_cache.get(&item.name) {
                                SelectObject(mem_dc, HGDIOBJ(preview_font.0 as isize));
                            } else if let Some(default_font) = LISTVIEW_FONT.get() {
                                SelectObject(mem_dc, HGDIOBJ(default_font.0 as isize));
                            }
                        }
                        
                        let text_color = if (draw_item.itemState.0 & ODS_SELECTED.0) != 0 {
                            GetSysColor(COLOR_HIGHLIGHTTEXT)
                        } else {
                            0x00AA6600 // 深橙色
                        };
                        SetTextColor(mem_dc, COLORREF(text_color));
                        
                        let mut preview_text = to_wide_string(TEST_TEXT);
                        DrawTextW(
                            mem_dc,
                            &mut preview_text,
                            &mut col_rect,
                            DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS,
                        );
                    }
                    2 => {
                        // FontLink状态列
                        if let Some(font) = LISTVIEW_FONT.get() {
                            SelectObject(mem_dc, HGDIOBJ(font.0 as isize));
                        }
                        
                        let color = if (draw_item.itemState.0 & ODS_SELECTED.0) != 0 {
                            GetSysColor(COLOR_HIGHLIGHTTEXT)
                        } else if item.has_fontlink {
                            0x00008000 // 绿色
                        } else {
                            0x000000AA // 红色
                        };
                        SetTextColor(mem_dc, COLORREF(color));
                        
                        let status = if item.has_fontlink { "✅" } else { "❌" };
                        let mut status_text = to_wide_string(status);
                        DrawTextW(
                            mem_dc,
                            &mut status_text,
                            &mut col_rect,
                            DT_CENTER | DT_VCENTER | DT_SINGLELINE,
                        );
                    }
                    3 => {
                        // FontLink信息列
                        if let Some(font) = LISTVIEW_FONT.get() {
                            SelectObject(mem_dc, HGDIOBJ(font.0 as isize));
                        }
                        
                        let text_color = if (draw_item.itemState.0 & ODS_SELECTED.0) != 0 {
                            GetSysColor(COLOR_HIGHLIGHTTEXT)
                        } else {
                            0x00666666
                        };
                        SetTextColor(mem_dc, COLORREF(text_color));
                        
                        let mut link_text = to_wide_string(&item.link_text);
                        DrawTextW(
                            mem_dc,
                            &mut link_text,
                            &mut col_rect,
                            DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS,
                        );
                    }
                    _ => {}
                }
                
                col_left += col_width;
            }
            
            // 复制到实际DC
            let _ = BitBlt(
                draw_item.hDC,
                rect.left,
                rect.top,
                width,
                height,
                mem_dc,
                0,
                0,
                SRCCOPY,
            );
            
            // 清理资源
            SelectObject(mem_dc, old_bitmap);
            DeleteObject(bitmap);
            DeleteDC(mem_dc);
        }
    }
    LRESULT(1)
}

// 主窗口过程
unsafe extern "system" fn window_proc(
    hwnd: HWND,
    msg: u32,
    wparam: WPARAM,
    lparam: LPARAM,
) -> LRESULT {
    match msg {
        WM_CREATE => {
            // 启用基本视觉样式
            enable_visual_styles(hwnd);

            // 创建字体
            let header_font = create_font_by_name(-16, "Segoe UI", FW_SEMIBOLD.0 as i32, false);
            let listview_font = get_system_font();
            let _ = HEADER_FONT.set(header_font);
            let _ = LISTVIEW_FONT.set(listview_font);

            // 创建标题背景画刷
            let header_brush = CreateSolidBrush(COLORREF(0x00AA6600)); // 深橙色背景
            let _ = HEADER_BRUSH.set(header_brush);

            // 创建预览字体缓存 - 使用支持FontLink的方式
            let mut font_cache = HashMap::new();
            for font_name in SYSTEM_FONTS {
                let preview_font = create_font_with_logfont(-16, font_name, FW_NORMAL.0 as i32);
                if !preview_font.is_invalid() {
                    font_cache.insert(font_name.to_string(), preview_font);
                }
            }
            let _ = PREVIEW_FONT_CACHE.set(font_cache);

            // 读取FontLink数据
            let font_links = read_font_link_registry();
            let mut items = Vec::new();
            
            for font_name in SYSTEM_FONTS {
                let has_fontlink = font_links.contains_key(*font_name);
                let link_text = if let Some(links) = font_links.get(*font_name) {
                    let clean = links.replace('\0', " | ");
                    if clean.len() > 100 {
                        format!("{}...", &clean[..100])
                    } else {
                        clean
                    }
                } else {
                    "(无配置)".to_string()
                };

                items.push(FontItem {
                    name: font_name.to_string(),
                    has_fontlink,
                    link_text,
                });
            }
            let _ = FONT_ITEMS.set(items);

            // 获取客户区尺寸
            let mut client_rect = RECT::default();
            let _ = GetClientRect(hwnd, &mut client_rect);
            let client_width = client_rect.right - client_rect.left;
            let client_height = client_rect.bottom - client_rect.top;

            // 创建标题静态控件
            let header_height = 40;
            let hwnd_header = CreateWindowExW(
                WINDOW_EX_STYLE(0),
                w!("STATIC"),
                w!("🔤 字体回退测试工具 - SystemLink 配置检查器"),
                WS_CHILD | WS_VISIBLE | WINDOW_STYLE(SS_CENTER | SS_CENTERIMAGE),
                0, 0,
                client_width, header_height,
                hwnd,
                HMENU(ID_HEADER_STATIC as isize),
                GetModuleHandleW(None).unwrap(),
                None,
            );

            if let Some(font) = HEADER_FONT.get() {
                SendMessageW(hwnd_header, WM_SETFONT, WPARAM(font.0 as usize), LPARAM(1));
            }

            // 创建状态栏
            let hwnd_status = init_status_bar(hwnd);
            
            // 获取状态栏高度
            let mut status_rect = RECT::default();
            let _ = GetClientRect(hwnd_status, &mut status_rect);
            let status_height = status_rect.bottom - status_rect.top;

            // 创建ListView
            let listview_y = header_height + 5;
            let listview_height = client_height - header_height - status_height - 10;
            
            let hwnd_listview = CreateWindowExW(
                WS_EX_CLIENTEDGE,
                WC_LISTVIEWW,
                PCWSTR::null(),
                WS_CHILD | WS_VISIBLE | WS_TABSTOP | WINDOW_STYLE(LVS_REPORT | LVS_SINGLESEL),
                5, listview_y,
                client_width - 10, listview_height,
                hwnd,
                HMENU(ID_LISTVIEW as isize),
                GetModuleHandleW(None).unwrap(),
                None,
            );

            init_listview(hwnd_listview);

            return LRESULT(0);
        }
        WM_SIZE => {
            let width = (lparam.0 & 0xFFFF) as i32;
            let height = ((lparam.0 >> 16) & 0xFFFF) as i32;

            // 调整状态栏大小
            let hwnd_status = HWND(GetDlgItem(hwnd, ID_STATUS_BAR).0);
            if hwnd_status.0 != 0 {
                SendMessageW(hwnd_status, WM_SIZE, wparam, lparam);
            }

            // 调整标题控件大小
            let hwnd_header = HWND(GetDlgItem(hwnd, ID_HEADER_STATIC).0);
            if hwnd_header.0 != 0 {
                let _ = SetWindowPos(hwnd_header, HWND(0), 0, 0, width, 40, SWP_NOZORDER | SWP_NOACTIVATE);
            }

            // 调整ListView大小
            let hwnd_listview = HWND(GetDlgItem(hwnd, ID_LISTVIEW).0);
            if hwnd_listview.0 != 0 {
                let mut status_rect = RECT::default();
                let _ = GetClientRect(hwnd_status, &mut status_rect);
                let status_height = status_rect.bottom - status_rect.top;
                
                let listview_height = height - 40 - status_height - 10;
                let _ = SetWindowPos(hwnd_listview, HWND(0), 5, 45, width - 10, listview_height, SWP_NOZORDER | SWP_NOACTIVATE);
                
                // 更新列宽度缓存
                get_listview_column_widths(hwnd_listview);
            }

            return LRESULT(0);
        }
        WM_CTLCOLORSTATIC => {
            let hdc = HDC(wparam.0 as isize);
            let hwnd_static = HWND(lparam.0 as isize);
            let id = GetDlgCtrlID(hwnd_static);
            
            if id == ID_HEADER_STATIC {
                // 设置标题背景和文字颜色
                SetTextColor(hdc, COLORREF(0x00FFFFFF)); // 白色文字
                SetBkColor(hdc, COLORREF(0x00AA6600)); // 深橙色背景
                if let Some(brush) = HEADER_BRUSH.get() {
                    return LRESULT(brush.0 as isize);
                }
            }
            return LRESULT(0);
        }
        WM_ERASEBKGND => {
            // 使用系统默认窗口背景色绘制
            let hdc = HDC(wparam.0 as isize);
            let mut rect = RECT::default();
            let _ = GetClientRect(hwnd, &mut rect);
            let brush = GetSysColorBrush(COLOR_WINDOW);
            FillRect(hdc, &rect, brush);
            return LRESULT(1);
        }
        WM_DRAWITEM => {
            let draw_item = &*(lparam.0 as *const DRAWITEMSTRUCT);
            if draw_item.CtlID as i32 == ID_LISTVIEW {
                return handle_owner_draw_listview(draw_item);
            }
            return LRESULT(0);
        }
        WM_DESTROY => {
            // 清理字体资源
            if let Some(font) = HEADER_FONT.get() {
                if !font.is_invalid() {
                    DeleteObject(*font);
                }
            }
            if let Some(font) = LISTVIEW_FONT.get() {
                if !font.is_invalid() {
                    DeleteObject(*font);
                }
            }
            if let Some(cache) = PREVIEW_FONT_CACHE.get() {
                for font in cache.values() {
                    if !font.is_invalid() {
                        DeleteObject(*font);
                    }
                }
            }
            if let Some(brush) = HEADER_BRUSH.get() {
                DeleteObject(*brush);
            }
            
            PostQuitMessage(0);
            return LRESULT(0);
        }
        _ => {}
    }
    DefWindowProcW(hwnd, msg, wparam, lparam)
}

fn main() -> Result<()> {
    unsafe {
        // 启用视觉样式和DPI感知
        SetProcessDPIAware();
        
        let hinstance = GetModuleHandleW(None)?;

        let class_name = to_wide_string("FontFallbackTestWindow");
        let window_title = to_wide_string("字体回退测试工具 v3");

        let hicon = LoadIconW(hinstance, PCWSTR(IDI_MAIN_ICON as usize as *const u16));
        let _icon = if hicon.is_ok() { hicon.unwrap() } else { LoadIconW(HINSTANCE(0), IDI_APPLICATION)? };

        let wc = WNDCLASSW {
            style: CS_HREDRAW | CS_VREDRAW,
            lpfnWndProc: Some(window_proc),
            cbClsExtra: 0,
            cbWndExtra: 0,
            hInstance: hinstance.into(),
            hIcon: LoadIconW(HINSTANCE(0), IDI_APPLICATION)?,
            hCursor: LoadCursorW(HINSTANCE(0), IDC_ARROW)?,
            hbrBackground: HBRUSH((COLOR_WINDOW.0 + 1) as isize),
            lpszMenuName: PCWSTR::null(),
            lpszClassName: PCWSTR(class_name.as_ptr()),
        };

        RegisterClassW(&wc);

        let hwnd = CreateWindowExW(
            WINDOW_EX_STYLE(0),
            PCWSTR(class_name.as_ptr()),
            PCWSTR(window_title.as_ptr()),
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            CW_USEDEFAULT, CW_USEDEFAULT,
            1200, 800,
            HWND(0),
            HMENU(0),
            hinstance,
            None,
        );

        if hwnd.0 == 0 {
            return Err(Error::from_win32());
        }

        let small_icon = LoadImageW(hinstance, PCWSTR(IDI_MAIN_ICON as usize as *const u16), IMAGE_ICON, 
                                   GetSystemMetrics(SM_CXSMICON), GetSystemMetrics(SM_CYSMICON), IMAGE_FLAGS(0));
        let large_icon = LoadImageW(hinstance, PCWSTR(IDI_MAIN_ICON as usize as *const u16), IMAGE_ICON,
                                   GetSystemMetrics(SM_CXICON), GetSystemMetrics(SM_CYICON), IMAGE_FLAGS(0));

        if small_icon.is_ok() {
            SendMessageW(hwnd, WM_SETICON, WPARAM(ICON_SMALL as usize), LPARAM(small_icon.unwrap().0));
        }
        if large_icon.is_ok() {
            SendMessageW(hwnd, WM_SETICON, WPARAM(ICON_BIG as usize), LPARAM(large_icon.unwrap().0));
        }

        ShowWindow(hwnd, SW_SHOW);
        UpdateWindow(hwnd);

        let mut msg = MSG::default();
        while GetMessageW(&mut msg, HWND(0), 0, 0).into() {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }

        Ok(())
    }
}
