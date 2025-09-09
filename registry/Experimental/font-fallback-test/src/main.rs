#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::ffi::OsStr;
use std::iter::once;
use std::os::windows::ffi::OsStrExt;
use std::collections::HashMap;
use std::sync::OnceLock;
use windows::core::*;
use windows::Win32::Foundation::*;
use windows::Win32::Graphics::Gdi::*;
use windows::Win32::System::LibraryLoader::GetModuleHandleW;
use windows::Win32::System::Registry::*;
use windows::Win32::UI::WindowsAndMessaging::*;

// 常量
const ID_CANVAS: i32 = 5000;
const ID_SCROLLBAR: i32 = 5001;
const ID_TITLE: i32 = 1000;
const ID_SEPARATOR: i32 = 1001;
const ID_FOOTER: i32 = 3000;

// 滚动条样式常量
const SBS_VERT: u32 = 0x0001;

// 滚动条命令常量
const SB_TOP: u32 = 6;
const SB_BOTTOM: u32 = 7;
const SB_LINEUP: u32 = 0;
const SB_LINEDOWN: u32 = 1;
const SB_PAGEUP: u32 = 2;
const SB_PAGEDOWN: u32 = 3;
const SB_THUMBPOSITION: u32 = 4;
const SB_THUMBTRACK: u32 = 5;

static mut SCROLL_POS: i32 = 0;
static mut TOTAL_HEIGHT: i32 = 0;
static mut CLIENT_HEIGHT: i32 = 0;

// Font handles cache
static HEADER_FONT: OnceLock<HFONT> = OnceLock::new();
static LABEL_FONT: OnceLock<HFONT> = OnceLock::new();
static INFO_FONT: OnceLock<HFONT> = OnceLock::new();

// 数据项
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

// 测试文本
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

fn get_wheel_delta_wparam(wparam: WPARAM) -> i16 {
    ((wparam.0 >> 16) & 0xffff) as i16
}

// Helper to create HFONT by name & size (height in logical units)
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

// Update scrollbar and scroll content
unsafe fn update_scrollbar(hwnd: HWND) {
    let scrollbar = HWND(GetDlgItem(hwnd, ID_SCROLLBAR).0);
    if scrollbar.0 != 0 {
        let max_scroll = (TOTAL_HEIGHT - CLIENT_HEIGHT).max(0);
        
        let si = SCROLLINFO {
            cbSize: std::mem::size_of::<SCROLLINFO>() as u32,
            fMask: SIF_RANGE | SIF_PAGE | SIF_POS,
            nMin: 0,
            nMax: TOTAL_HEIGHT,
            nPage: CLIENT_HEIGHT as u32,
            nPos: SCROLL_POS,
            nTrackPos: 0,
        };
        
        // 使用 SendMessage 代替 SetScrollInfo
        let _ = SendMessageW(
            scrollbar,
            SBM_SETSCROLLINFO,
            WPARAM(TRUE.0 as usize),
            LPARAM(&si as *const SCROLLINFO as isize),
        );
        
        // 使用 SendMessage 代替 EnableWindow
        let _ = SendMessageW(
            scrollbar,
            WM_ENABLE,
            WPARAM(if max_scroll > 0 { 1 } else { 0 }),
            LPARAM(0),
        );
    }
}

// Scroll content by invalidating canvas
unsafe fn scroll_to(hwnd: HWND, new_pos: i32) {
    let max_scroll = (TOTAL_HEIGHT - CLIENT_HEIGHT).max(0);
    let new_pos = new_pos.max(0).min(max_scroll);

    if new_pos != SCROLL_POS {
        SCROLL_POS = new_pos;
        update_scrollbar(hwnd);
        
        let canvas = HWND(GetDlgItem(hwnd, ID_CANVAS).0);
        if canvas.0 != 0 {
            InvalidateRect(canvas, None, FALSE);
        } else {
            InvalidateRect(hwnd, None, FALSE);
        }
    }
}

// Canvas window proc - does double-buffered painting of font items
unsafe extern "system" fn canvas_wndproc(hwnd: HWND, msg: u32, wparam: WPARAM, lparam: LPARAM) -> LRESULT {
    match msg {
        WM_ERASEBKGND => {
            return LRESULT(1);
        }
        WM_PAINT => {
            let mut ps = PAINTSTRUCT::default();
            let hdc = BeginPaint(hwnd, &mut ps);

            let mut client = RECT::default();
            let _ = GetClientRect(hwnd, &mut client);
            let width = (client.right - client.left).max(1);
            let height = (client.bottom - client.top).max(1);

            let mem_dc = CreateCompatibleDC(hdc);
            let bmp = CreateCompatibleBitmap(hdc, width, height);
            let old_bmp = SelectObject(mem_dc, bmp);

            // Fill background white
            let brush = CreateSolidBrush(COLORREF(0x00FFFFFF));
            FillRect(mem_dc, &client, HBRUSH(brush.0));
            DeleteObject(brush);

            // Prepare fonts
            let label_font = LABEL_FONT.get().expect("label font");
            let info_font = INFO_FONT.get().expect("info font");

            let line_height: i32 = 100;
            let margin_left = 10;
            let mut y = -SCROLL_POS;

            let items = FONT_ITEMS.get().expect("font items");
            let visible_top = -50;  // Allow some overdraw
            let visible_bottom = height + 50;

            for item in items.iter() {
                if y + line_height < visible_top {
                    y += line_height;
                    continue;
                }
                if y > visible_bottom {
                    break;
                }

                // Draw font name
                SelectObject(mem_dc, HGDIOBJ(label_font.0 as isize));
                SetTextColor(mem_dc, COLORREF(0x00000000));
                let name_text = format!("📝 {} {}", item.name, if item.has_fontlink { "✅" } else { "❌" });
                let mut name_w = to_wide_string(&name_text);
                let name_rc = RECT { left: margin_left, top: y, right: width - margin_left, bottom: y + 24 };
                DrawTextW(mem_dc, &mut name_w, &name_rc as *const RECT as *mut RECT, DT_LEFT | DT_VCENTER | DT_SINGLELINE);

                // Create preview font
                let hpreview = create_font_by_name(-36, &item.name, FW_NORMAL.0 as i32, false);
                let preview_font = if !hpreview.is_invalid() {
                    hpreview
                } else {
                    create_font_by_name(-36, "Consolas", FW_NORMAL.0 as i32, false)
                };

                if !preview_font.is_invalid() {
                    SelectObject(mem_dc, HGDIOBJ(preview_font.0 as isize));
                }

                // Draw preview block border
                let preview_rc = RECT { left: margin_left + 10, top: y + 26, right: width - margin_left - 10, bottom: y + 26 + 48 };
                let border_brush = CreateSolidBrush(COLORREF(0x00E0E0E0));
                FrameRect(mem_dc, &preview_rc, HBRUSH(border_brush.0));
                DeleteObject(border_brush);

                // Draw preview text
                SetTextColor(mem_dc, COLORREF(0x00000080));
                let mut preview_w = to_wide_string(TEST_TEXT);
                DrawTextW(mem_dc, &mut preview_w, &preview_rc as *const RECT as *mut RECT, DT_CENTER | DT_VCENTER | DT_SINGLELINE);

                // Draw FontLink info
                SelectObject(mem_dc, HGDIOBJ(info_font.0 as isize));
                SetTextColor(mem_dc, COLORREF(0x00666666));
                let mut info_w = to_wide_string(&item.link_text);
                let info_rc = RECT { left: margin_left + 10, top: y + 76, right: width - margin_left - 10, bottom: y + line_height - 6 };
                DrawTextW(mem_dc, &mut info_w, &info_rc as *const RECT as *mut RECT, DT_LEFT | DT_TOP | DT_WORDBREAK);

                // Clean up preview font
                if !preview_font.is_invalid() {
                    DeleteObject(preview_font);
                }

                y += line_height;
            }

            let _ = BitBlt(hdc, 0, 0, width, height, mem_dc, 0, 0, SRCCOPY);

            SelectObject(mem_dc, old_bmp);
            DeleteObject(bmp);
            DeleteDC(mem_dc);

            EndPaint(hwnd, &ps);
            return LRESULT(0);
        }
        WM_SIZE => {
            InvalidateRect(hwnd, None, FALSE);
            return LRESULT(0);
        }
        _ => {}
    }
    DefWindowProcW(hwnd, msg, wparam, lparam)
}

// 计算合适的 footer 高度
unsafe fn calculate_footer_height(footer_hwnd: HWND, width: i32) -> i32 {
    let hdc = GetDC(footer_hwnd);
    if hdc.0 == 0 {
        return 60; // 默认高度
    }
    
    // 选择正确的字体
    if let Some(lf) = LABEL_FONT.get() {
        if !lf.is_invalid() {
            SelectObject(hdc, HGDIOBJ(lf.0 as isize));
        }
    }
    
    let footer_text = "📖 使用说明：观察每个字体的显示效果，✅表示有FontLink配置，❌表示无配置。使用鼠标滚轮或滚动条浏览所有字体。\n异常显示通常与FontLink配置相关。";
    let mut footer_w = to_wide_string(footer_text);
    
    let mut rect = RECT {
        left: 0,
        top: 0,
        right: width - 40, // 减去边距
        bottom: 0,
    };
    
    // 计算文本所需的高度
    let height = DrawTextW(
        hdc,
        &mut footer_w,
        &mut rect,
        DT_CALCRECT | DT_LEFT | DT_TOP | DT_WORDBREAK,
    );
    
    ReleaseDC(footer_hwnd, hdc);
    
    // 返回计算出的高度加上一些边距
    (height + 20).max(60)
}

// Main window proc
unsafe extern "system" fn window_proc(
    hwnd: HWND,
    msg: u32,
    wparam: WPARAM,
    lparam: LPARAM,
) -> LRESULT {
    match msg {
        WM_CREATE => {
            let header = create_font_by_name(-24, "Microsoft YaHei UI", FW_BOLD.0 as i32, false);
            let label = create_font_by_name(-16, "Microsoft YaHei UI", FW_NORMAL.0 as i32, false);
            let info = create_font_by_name(-14, "Consolas", FW_NORMAL.0 as i32, false);

            let _ = HEADER_FONT.set(header);
            let _ = LABEL_FONT.set(label);
            let _ = INFO_FONT.set(info);

            let font_links = read_font_link_registry();
            let mut items = Vec::new();
            for f in SYSTEM_FONTS.iter() {
                let has = font_links.contains_key(*f);
                let link_text = if let Some(v) = font_links.get(*f) {
                    let clean = v.replace('\0', " | ");
                    if clean.len() > 200 {
                        format!("💡 FontLink: {}...", &clean[..200])
                    } else {
                        format!("💡 FontLink: {}", clean)
                    }
                } else {
                    "💡 FontLink: (无配置)".to_string()
                };
                items.push(FontItem {
                    name: f.to_string(),
                    has_fontlink: has,
                    link_text,
                });
            }
            let _ = FONT_ITEMS.set(items);

            let mut client_rect = RECT::default();
            let _ = GetClientRect(hwnd, &mut client_rect);
            let client_width = client_rect.right - client_rect.left;
            let margin_left = 20;
            let mut y_pos = 20;

            // Title
            const SS_CENTERIMAGE: u32 = 0x00000200;
            let title_text = to_wide_string("🔤 字体回退测试工具 - SystemLink 配置检查器");
            let title_hwnd = CreateWindowExW(
                WINDOW_EX_STYLE(0),
                w!("STATIC"),
                PCWSTR(title_text.as_ptr()),
                WINDOW_STYLE(WS_VISIBLE.0 | WS_CHILD.0 | SS_CENTERIMAGE),
                margin_left,
                y_pos,
                client_width - margin_left * 2,
                36,
                hwnd,
                HMENU(ID_TITLE as isize),
                GetModuleHandleW(None).unwrap(),
                None,
            );
            if let Some(hf) = HEADER_FONT.get() {
                if !hf.is_invalid() {
                    let _ = SendMessageW(title_hwnd, WM_SETFONT, WPARAM(hf.0 as usize), LPARAM(1));
                }
            }
            y_pos += 46;

            // Separator
            let _sep = CreateWindowExW(
                WS_EX_STATICEDGE,
                w!("STATIC"),
                PCWSTR::null(),
                WS_VISIBLE | WS_CHILD,
                margin_left,
                y_pos,
                client_width - margin_left * 2,
                2,
                hwnd,
                HMENU(ID_SEPARATOR as isize),
                GetModuleHandleW(None).unwrap(),
                None,
            );
            y_pos += 16;

            let items_len = FONT_ITEMS.get().map(|v| v.len()).unwrap_or(0) as i32;
            let line_height = 100;
            TOTAL_HEIGHT = items_len * line_height + 100;

            let hinstance = GetModuleHandleW(None).unwrap();
            
            // Register canvas class
            let canvas_class = to_wide_string("FontCanvasClass");
            let wc = WNDCLASSW {
                style: CS_HREDRAW | CS_VREDRAW,
                lpfnWndProc: Some(canvas_wndproc),
                cbClsExtra: 0,
                cbWndExtra: 0,
                hInstance: hinstance.into(),
                hIcon: HICON(0),
                hCursor: LoadCursorW(HINSTANCE(0), IDC_ARROW).unwrap(),
                hbrBackground: HBRUSH(0),
                lpszMenuName: PCWSTR::null(),
                lpszClassName: PCWSTR(canvas_class.as_ptr()),
            };
            let _ = RegisterClassW(&wc);

            // 先创建 footer 来计算其高度
            let footer_text = to_wide_string("📖 使用说明：观察每个字体的显示效果，✅表示有FontLink配置，❌表示无配置。\n使用鼠标滚轮或滚动条浏览所有字体。异常显示通常与FontLink配置相关。");
            let footer_hwnd = CreateWindowExW(
                WINDOW_EX_STYLE(0),
                w!("STATIC"),
                PCWSTR(footer_text.as_ptr()),
                WS_VISIBLE | WS_CHILD,
                margin_left,
                0, // 稍后设置正确位置
                client_width - margin_left * 2,
                60, // 临时高度
                hwnd,
                HMENU(ID_FOOTER as isize),
                GetModuleHandleW(None).unwrap(),
                None,
            );
            if let Some(lf) = LABEL_FONT.get() {
                if !lf.is_invalid() {
                    let _ = SendMessageW(footer_hwnd, WM_SETFONT, WPARAM(lf.0 as usize), LPARAM(1));
                }
            }

            // 计算 footer 的实际高度
            let footer_height = calculate_footer_height(footer_hwnd, client_width);
            let canvas_height = client_rect.bottom - y_pos - footer_height - 10; // 10px 间距
            CLIENT_HEIGHT = canvas_height;
            
            let scrollbar_width = GetSystemMetrics(SM_CXVSCROLL);
            let canvas_width = client_width - margin_left * 2 - scrollbar_width;
            
            // Create canvas
            let _canvas = CreateWindowExW(
                WINDOW_EX_STYLE(0),
                PCWSTR(canvas_class.as_ptr()),
                PCWSTR::null(),
                WS_VISIBLE | WS_CHILD,
                margin_left,
                y_pos,
                canvas_width,
                canvas_height,
                hwnd,
                HMENU(ID_CANVAS as isize),
                hinstance,
                None,
            );

            // Create vertical scrollbar
            let _scrollbar = CreateWindowExW(
                WINDOW_EX_STYLE(0),
                w!("SCROLLBAR"),
                PCWSTR::null(),
                WINDOW_STYLE(WS_VISIBLE.0 | WS_CHILD.0 | SBS_VERT),
                margin_left + canvas_width,
                y_pos,
                scrollbar_width,
                canvas_height,
                hwnd,
                HMENU(ID_SCROLLBAR as isize),
                hinstance,
                None,
            );

            // 设置 footer 的正确位置和大小
            let _ = SetWindowPos(
                footer_hwnd, 
                HWND(0), 
                margin_left, 
                y_pos + canvas_height + 10, 
                client_width - margin_left * 2, 
                footer_height, 
                SWP_NOZORDER | SWP_NOACTIVATE
            );

            // Initialize scrollbar
            update_scrollbar(hwnd);

            return LRESULT(0);
        }
        WM_SIZE => {
            let scrollbar = HWND(GetDlgItem(hwnd, ID_SCROLLBAR).0);
            let canvas = HWND(GetDlgItem(hwnd, ID_CANVAS).0);
            let title = HWND(GetDlgItem(hwnd, ID_TITLE).0);
            let separator = HWND(GetDlgItem(hwnd, ID_SEPARATOR).0);
            let footer = HWND(GetDlgItem(hwnd, ID_FOOTER).0);
            
            if canvas.0 != 0 && scrollbar.0 != 0 && footer.0 != 0 {
                let mut client = RECT::default();
                let _ = GetClientRect(hwnd, &mut client);
                let margin_left = 20;
                let client_width = client.right - client.left;
                
                // 重新计算布局
                let title_height = 36;
                let sep_height = 2;
                let gap1 = 46 - title_height;
                let gap2 = 16 - sep_height;
                let gap3 = 10; // canvas 和 footer 之间的间距
                
                let mut y_pos = 20;
                
                // 调整 title 位置
                if title.0 != 0 {
                    let _ = SetWindowPos(title, HWND(0), margin_left, y_pos, client_width - margin_left * 2, title_height, SWP_NOZORDER | SWP_NOACTIVATE);
                }
                y_pos += title_height + gap1;
                
                // 调整 separator 位置
                if separator.0 != 0 {
                    let _ = SetWindowPos(separator, HWND(0), margin_left, y_pos, client_width - margin_left * 2, sep_height, SWP_NOZORDER | SWP_NOACTIVATE);
                }
                y_pos += sep_height + gap2;
                
                // 计算 footer 高度
                let footer_height = calculate_footer_height(footer, client_width);
                
                // 计算 canvas 高度（总高度 - 已用高度 - footer 高度 - 间距）
                let canvas_height = (client.bottom - y_pos - footer_height - gap3 - 20).max(100); // 至少100px高度，底部留20px边距
                
                CLIENT_HEIGHT = canvas_height;
                
                let scrollbar_width = GetSystemMetrics(SM_CXVSCROLL);
                let canvas_width = client_width - margin_left * 2 - scrollbar_width;
                
                // 调整 canvas 和 scrollbar 位置
                let _ = SetWindowPos(canvas, HWND(0), margin_left, y_pos, canvas_width, canvas_height, SWP_NOZORDER | SWP_NOACTIVATE);
                let _ = SetWindowPos(scrollbar, HWND(0), margin_left + canvas_width, y_pos, scrollbar_width, canvas_height, SWP_NOZORDER | SWP_NOACTIVATE);
                
                // 调整 footer 位置
                let _ = SetWindowPos(footer, HWND(0), margin_left, y_pos + canvas_height + gap3, client_width - margin_left * 2, footer_height, SWP_NOZORDER | SWP_NOACTIVATE);
                
                update_scrollbar(hwnd);
                InvalidateRect(canvas, None, FALSE);
            }
            return LRESULT(0);
        }
        WM_VSCROLL => {
            let scrollbar = HWND(GetDlgItem(hwnd, ID_SCROLLBAR).0);
            if HWND(lparam.0 as isize) == scrollbar {
                let mut si = SCROLLINFO {
                    cbSize: std::mem::size_of::<SCROLLINFO>() as u32,
                    fMask: SIF_ALL,
                    nMin: 0,
                    nMax: 0,
                    nPage: 0,
                    nPos: 0,
                    nTrackPos: 0,
                };
                let _ = GetScrollInfo(scrollbar, SB_CTL, &mut si);
                
                let mut new_pos = SCROLL_POS;
                match (wparam.0 & 0xFFFF) as u32 {
                    SB_TOP => new_pos = si.nMin,
                    SB_BOTTOM => new_pos = si.nMax,
                    SB_LINEUP => new_pos -= 30,
                    SB_LINEDOWN => new_pos += 30,
                    SB_PAGEUP => new_pos -= si.nPage as i32,
                    SB_PAGEDOWN => new_pos += si.nPage as i32,
                    SB_THUMBTRACK | SB_THUMBPOSITION => new_pos = si.nTrackPos,
                    _ => {}
                }
                
                scroll_to(hwnd, new_pos);
            }
            return LRESULT(0);
        }
        WM_MOUSEWHEEL => {
            let delta = get_wheel_delta_wparam(wparam) as i32;
            let step = (delta * -30) / 120;
            scroll_to(hwnd, SCROLL_POS + step);
            return LRESULT(0);
        }
        WM_KEYDOWN => {
            match wparam.0 as i32 {
                0x26 /*VK_UP*/ => { scroll_to(hwnd, SCROLL_POS - 30); return LRESULT(0); }
                0x28 /*VK_DOWN*/ => { scroll_to(hwnd, SCROLL_POS + 30); return LRESULT(0); }
                0x21 /*VK_PRIOR*/ => { 
                    scroll_to(hwnd, SCROLL_POS - CLIENT_HEIGHT); 
                    return LRESULT(0); 
                }
                0x22 /*VK_NEXT*/ => { 
                    scroll_to(hwnd, SCROLL_POS + CLIENT_HEIGHT); 
                    return LRESULT(0); 
                }
                _ => {}
            }
        }
        WM_CTLCOLORSTATIC => {
            let hdc = HDC(wparam.0 as isize);
            let hwnd_static = HWND(lparam.0 as isize);
            let id = GetDlgCtrlID(hwnd_static);
            if id == ID_TITLE {
                let _ = SetTextColor(hdc, COLORREF(0x00FFFFFF));
                let _ = SetBkColor(hdc, COLORREF(0x0080A0C0));
                return LRESULT(GetStockObject(LTGRAY_BRUSH).0 as isize);
            } else if id == ID_FOOTER {
                let _ = SetTextColor(hdc, COLORREF(0x00006400));
                let _ = SetBkColor(hdc, COLORREF(0x00F0FFF0));
                return LRESULT(GetStockObject(WHITE_BRUSH).0 as isize);
            }
            let _ = SetBkMode(hdc, TRANSPARENT);
            return LRESULT(GetStockObject(NULL_BRUSH).0 as isize);
        }
        WM_DESTROY => {
            if let Some(hf) = HEADER_FONT.get() {
                if !hf.is_invalid() { let _ = DeleteObject(*hf); }
            }
            if let Some(hf) = LABEL_FONT.get() {
                if !hf.is_invalid() { let _ = DeleteObject(*hf); }
            }
            if let Some(hf) = INFO_FONT.get() {
                if !hf.is_invalid() { let _ = DeleteObject(*hf); }
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
        let hinstance = GetModuleHandleW(None)?;

        let class_name = to_wide_string("FontFallbackTestWindow");
        let window_title = to_wide_string("字体回退测试工具 v3 - Canvas 自绘版 (带滚动条)");

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
            100,
            50,
            1000,
            750,
            HWND(0),
            HMENU(0),
            hinstance,
            None,
        );

        if hwnd.0 == 0 {
            return Err(Error::from_win32());
        }

        ShowWindow(hwnd, SW_SHOW);
        let _ = UpdateWindow(hwnd);

        let mut msg = MSG::default();
        while GetMessageW(&mut msg, HWND(0), 0, 0).into() {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }

        Ok(())
    }
}