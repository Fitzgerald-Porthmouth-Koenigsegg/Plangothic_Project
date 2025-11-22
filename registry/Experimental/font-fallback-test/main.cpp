#include <windows.h>
#include <windowsx.h>
#include <commctrl.h>
#include <vector>
#include <string>
#include <map>

#ifdef __MINGW32__
extern "C"
int WINAPI WinMain(HINSTANCE hInst, HINSTANCE, LPSTR, int nCmdShow) {
    return wWinMain(hInst, nullptr, GetCommandLineW(), nCmdShow);
}
#endif

#define IDI_MAIN_ICON 101
#define ID_LISTVIEW   1001
#define ID_STATUSBAR  1002
#define ID_HEADER_STATIC 1003

#pragma comment(lib, "comctl32.lib")
#pragma execution_character_set("utf-8")

// 常量定义
static const int HEADER_HEIGHT = 40;
static const int STATUS_HEIGHT = 25;
static const int MARGIN = 5;
static const int COLUMN_COUNT = 4;

// UTF-8 → UTF-16
std::wstring utf8_to_w(const std::string& s) {
    int len = MultiByteToWideChar(CP_UTF8, 0, s.c_str(), -1, nullptr, 0);
    if (len <= 1) return L"";

    std::wstring ws(len, L'\0');
    MultiByteToWideChar(CP_UTF8, 0, s.c_str(), -1, &ws[0], len);
    ws.pop_back();
    return ws;
}

// INI 读取
std::string ini_get(const char* sec, const char* key, const char* def, const char* path) {
    char buf[512] = {};
    GetPrivateProfileStringA(sec, key, def, buf, sizeof(buf), path);
    return buf;
}

int ini_get_int(const char* sec, const char* key, int def, const char* path) {
    return GetPrivateProfileIntA(sec, key, def, path);
}

// 配置结构
struct UIConfig {
    std::wstring window_title;
    std::wstring header_text;

    COLORREF header_bg_color;
    COLORREF header_text_color;
    COLORREF preview_text_color;
    COLORREF success_color;
    COLORREF error_color;
    COLORREF info_color;

    std::wstring header_font_name;
    int header_font_size;
    int header_font_weight;

    int listview_font_size;
    int preview_font_size;

    std::wstring status_text[3];
    std::wstring column_header[COLUMN_COUNT];
    int column_width[COLUMN_COUNT];

    std::wstring test_text;
    std::wstring registry_key;
    std::vector<std::wstring> fonts;
};

UIConfig g_cfg;

// 全局资源
HFONT g_hHeaderFont = NULL;
HFONT g_hListFont = NULL;
std::map<std::wstring, HFONT> g_previewFonts;

HBRUSH g_headerBrush = NULL;

std::vector<bool> g_hasFontlink;
std::vector<std::wstring> g_fontlinkText;

// 读取 INI 配置
void load_config() {
    char exe[MAX_PATH]; GetModuleFileNameA(NULL, exe, MAX_PATH);
    std::string exePath(exe);
    exePath = exePath.substr(0, exePath.find_last_of("\\/"));
    std::string ini = exePath + "\\config.ini";

    g_cfg.window_title = utf8_to_w(ini_get("UI", "window_title", "窗口", ini.c_str()));
    g_cfg.header_text  = utf8_to_w(ini_get("UI", "header_text", "标题", ini.c_str()));

    g_cfg.header_bg_color   = strtoul(ini_get("UI","header_bg_color","0x00AA6600",ini.c_str()).c_str(),0,16);
    g_cfg.header_text_color = strtoul(ini_get("UI","header_text_color","0xFFFFFF",ini.c_str()).c_str(),0,16);
    g_cfg.preview_text_color= strtoul(ini_get("UI","preview_text_color","0x00AA6600",ini.c_str()).c_str(),0,16);

    g_cfg.success_color = strtoul(ini_get("UI","success_color","0x00008000",ini.c_str()).c_str(),0,16);
    g_cfg.error_color   = strtoul(ini_get("UI","error_color","0x000000AA",ini.c_str()).c_str(),0,16);
    g_cfg.info_color    = strtoul(ini_get("UI","info_color","0x00666666",ini.c_str()).c_str(),0,16);

    g_cfg.header_font_name   = utf8_to_w(ini_get("UI","header_font_name","Segoe UI", ini.c_str()));
    g_cfg.header_font_size   = ini_get_int("UI","header_font_size",-16, ini.c_str());
    g_cfg.header_font_weight = ini_get_int("UI","header_font_weight",600, ini.c_str());
    g_cfg.listview_font_size = ini_get_int("UI","listview_font_size",-12, ini.c_str());
    g_cfg.preview_font_size  = ini_get_int("UI","preview_font_size",-16, ini.c_str());

    g_cfg.status_text[0] = utf8_to_w(ini_get("UI","status_text_0","", ini.c_str()));
    g_cfg.status_text[1] = utf8_to_w(ini_get("UI","status_text_1","", ini.c_str()));
    g_cfg.status_text[2] = utf8_to_w(ini_get("UI","status_text_2","", ini.c_str()));

    for (int i=0;i<COLUMN_COUNT;i++){
        char keyH[32], keyW[32];
        sprintf(keyH,"column_header_%d",i);
        sprintf(keyW,"column_width_%d",i);
        g_cfg.column_header[i] = utf8_to_w(ini_get("UI",keyH,"",ini.c_str()));
        g_cfg.column_width[i]  = ini_get_int("UI",keyW,100,ini.c_str());
    }

    g_cfg.test_text = utf8_to_w(ini_get("Test","test_text","Test",ini.c_str()));

    g_cfg.registry_key = utf8_to_w(ini_get("Registry","key_path",
        "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\FontLink\\SystemLink",
        ini.c_str()));

    int n = ini_get_int("Fonts","count",0,ini.c_str());
    for (int i=0;i<n;i++){
        char key[32]; sprintf(key,"font_%d",i);
        g_cfg.fonts.push_back(utf8_to_w(ini_get("Fonts",key,"",ini.c_str())));
    }
}

// 创建字体
HFONT make_font(const std::wstring& name, int size, int weight) {
    LOGFONTW lf{};
    lf.lfHeight = size;
    lf.lfWeight = weight;
    lstrcpyW(lf.lfFaceName, name.c_str());
    return CreateFontIndirectW(&lf);
}

// 初始化 GDI 资源（字体、画刷）
void create_fonts() {
    g_hHeaderFont = make_font(g_cfg.header_font_name, g_cfg.header_font_size, g_cfg.header_font_weight);
    g_hListFont   = make_font(L"Segoe UI", g_cfg.listview_font_size, 400);

    for (auto &f : g_cfg.fonts) {
        HFONT h = make_font(f, g_cfg.preview_font_size, 400);
        if (h) g_previewFonts[f] = h;
    }

    g_headerBrush = CreateSolidBrush(g_cfg.header_bg_color);
}

// 读取 FontLink 注册表
void load_fontlink() {
    HKEY hKey;
    if (RegOpenKeyExW(HKEY_LOCAL_MACHINE, g_cfg.registry_key.c_str(), 0, KEY_READ, &hKey)!=ERROR_SUCCESS)
        return;

    WCHAR name[256];
    BYTE data[4096];
    DWORD name_len, type, data_len;

    for (DWORD idx=0;;idx++) {
        name_len = 256; data_len = sizeof(data);
        if (RegEnumValueW(hKey, idx, name, &name_len, NULL, &type, data, &data_len)!=ERROR_SUCCESS)
            break;

        if (type != REG_MULTI_SZ) continue;

        std::wstring fn(name);
        std::wstring links((WCHAR*)data, data_len/2);
        std::wstring fixed;
        for (size_t i=0;i<links.size();i++){
            if (links[i] != 0) fixed += links[i];
            else if (i+1 < links.size() && links[i+1] != 0) fixed += L'|';
        }

        for (size_t i=0;i<g_cfg.fonts.size();i++){
            if (g_cfg.fonts[i] == fn){
                g_hasFontlink[i] = true;
                g_fontlinkText[i] = fixed;
            }
        }
    }
    RegCloseKey(hKey);
}

// ListView 初始化
void init_listview(HWND hList) {
    ListView_SetExtendedListViewStyle(hList,
        LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES | LVS_EX_DOUBLEBUFFER);

    LVCOLUMNW col{};
    col.mask = LVCF_TEXT | LVCF_WIDTH | LVCF_SUBITEM;

    for (int i=0;i<COLUMN_COUNT;i++){
        col.pszText = (LPWSTR)g_cfg.column_header[i].c_str();
        col.cx = g_cfg.column_width[i];
        ListView_InsertColumn(hList, i, &col);
    }

    // 行
    for (int i=0; i<(int)g_cfg.fonts.size(); i++){
        LVITEMW it{};
        it.iItem = i;
        it.mask = LVIF_TEXT;
        ListView_InsertItem(hList, &it);
    }

    SendMessageW(hList, WM_SETFONT, (WPARAM)g_hListFont, TRUE);
}

// 绘制 ListView 行（OwnerDraw）
void draw_listview_row(DRAWITEMSTRUCT* dis) {
    int row = dis->itemID;
    HDC hdc = dis->hDC;
    RECT rc = dis->rcItem;

    bool selected = (dis->itemState & ODS_SELECTED);

    // 双缓冲
    HDC mem = CreateCompatibleDC(hdc);
    HBITMAP bmp = CreateCompatibleBitmap(hdc, rc.right-rc.left, rc.bottom-rc.top);
    HGDIOBJ oldBmp = SelectObject(mem, bmp);

    RECT rectMem = {0,0, rc.right-rc.left, rc.bottom-rc.top};

    HBRUSH bg = CreateSolidBrush(selected ? GetSysColor(COLOR_HIGHLIGHT) : RGB(255,255,255));
    FillRect(mem, &rectMem, bg);
    DeleteObject(bg);

    SetBkMode(mem, TRANSPARENT);

    int x = 0;

    HWND hList = dis->hwndItem;
    for (int col=0; col<COLUMN_COUNT; col++){
        int colWidth = ListView_GetColumnWidth(hList, col);
        RECT cr = { x+4, 2, x + colWidth - 4, rectMem.bottom - 2 };

        switch(col){

        case 0: // Font Name
            SelectObject(mem, g_hListFont);
            SetTextColor(mem, selected ? GetSysColor(COLOR_HIGHLIGHTTEXT) : RGB(0,0,0));
            DrawTextW(mem, (LPWSTR)g_cfg.fonts[row].c_str(), -1, &cr,
                      DT_LEFT|DT_VCENTER|DT_SINGLELINE|DT_END_ELLIPSIS);
            break;

        case 1: // Preview
        {
            HFONT pf = g_previewFonts[g_cfg.fonts[row]];
            SelectObject(mem, pf ? pf : g_hListFont);

            SetTextColor(mem, selected ?
                GetSysColor(COLOR_HIGHLIGHTTEXT) :
                g_cfg.preview_text_color);

            DrawTextW(mem, (LPWSTR)g_cfg.test_text.c_str(), -1, &cr,
                      DT_LEFT|DT_VCENTER|DT_SINGLELINE|DT_END_ELLIPSIS);
        }
        break;

        case 2: // Status
        {
            SelectObject(mem, g_hListFont);

            COLORREF colr = selected ? GetSysColor(COLOR_HIGHLIGHTTEXT) :
                (g_hasFontlink[row] ? g_cfg.success_color : g_cfg.error_color);

            SetTextColor(mem, colr);

            const wchar_t* s = g_hasFontlink[row] ? L"✅" : L"❌";
            DrawTextW(mem, (LPWSTR)s, -1, &cr, DT_CENTER|DT_VCENTER|DT_SINGLELINE);
        }
        break;

        case 3: // Link Text
            SelectObject(mem, g_hListFont);
            SetTextColor(mem, selected ? GetSysColor(COLOR_HIGHLIGHTTEXT) : g_cfg.info_color);
            DrawTextW(mem, (LPWSTR)g_fontlinkText[row].c_str(), -1, &cr,
                      DT_LEFT|DT_VCENTER|DT_SINGLELINE|DT_END_ELLIPSIS);
            break;
        }
        x += colWidth;
    }

    BitBlt(hdc, rc.left, rc.top, rc.right-rc.left, rc.bottom-rc.top, mem, 0,0, SRCCOPY);

    SelectObject(mem, oldBmp);
    DeleteObject(bmp);
    DeleteDC(mem);
}

// 处理 STATIC 背景（Header）
HBRUSH handle_ctlcolor_static(HDC hdc, HWND hwndCtl) {
    if (GetDlgCtrlID(hwndCtl) == ID_HEADER_STATIC) {
        SetTextColor(hdc, g_cfg.header_text_color);
        SetBkColor(hdc, g_cfg.header_bg_color);
        return g_headerBrush;
    }
    return NULL;
}

// 更新布局
void update_layout(HWND hwnd, HWND hHeader, HWND hStatus, HWND hList, int w, int h) {
    MoveWindow(hHeader, 0, 0, w, HEADER_HEIGHT, FALSE);
    MoveWindow(hStatus, 0, h-STATUS_HEIGHT, w, STATUS_HEIGHT, FALSE);
    MoveWindow(hList,
        MARGIN,
        HEADER_HEIGHT + MARGIN,
        w - MARGIN*2,
        h - HEADER_HEIGHT - STATUS_HEIGHT - MARGIN*2,
        FALSE);

    if (hList) {
        RECT rcList;
        GetClientRect(hList, &rcList);
        int listWidth = rcList.right - rcList.left;

        int used = 0;
        for (int i = 0; i < COLUMN_COUNT - 1; i++) {
            used += ListView_GetColumnWidth(hList, i);
        }

        int lastWidth = listWidth - used;
        if (lastWidth < 50) lastWidth = 50;  // 最小宽度保护

        ListView_SetColumnWidth(hList, COLUMN_COUNT - 1, lastWidth);

        HWND hHdr = ListView_GetHeader(hList);
        if (hHdr) {
            InvalidateRect(hHdr, NULL, TRUE);
        }
    }

    InvalidateRect(hList, NULL, TRUE);
}

// 主窗口过程
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    static HWND hHeader = NULL, hStatus = NULL, hList = NULL;

    switch(msg) {

    case WM_CREATE:
    {
        create_fonts();

        g_hasFontlink.assign(g_cfg.fonts.size(), false);
        g_fontlinkText.assign(g_cfg.fonts.size(), L"(无配置)");

        load_fontlink();

        RECT rc; GetClientRect(hwnd, &rc);

        hHeader = CreateWindowW(L"STATIC", g_cfg.header_text.c_str(),
            WS_CHILD|WS_VISIBLE|SS_CENTER|SS_CENTERIMAGE,
            0, 0, rc.right, HEADER_HEIGHT,
            hwnd, (HMENU)ID_HEADER_STATIC, NULL, NULL);
        SendMessageW(hHeader, WM_SETFONT, (WPARAM)g_hHeaderFont, TRUE);

        hStatus = CreateWindowExW(0, STATUSCLASSNAMEW, L"",
            WS_CHILD|WS_VISIBLE|SBARS_SIZEGRIP,
            0,0,0,0, hwnd, (HMENU)ID_STATUSBAR, NULL, NULL);

        {
            RECT rcClient; GetClientRect(hwnd, &rcClient);
            int parts[3] = { rcClient.right/3, rcClient.right*2/3, -1 };
            SendMessageW(hStatus, SB_SETPARTS, 3, (LPARAM)parts);
        }

        for (int i=0;i<3;i++)
            SendMessageW(hStatus, SB_SETTEXTW, i, (LPARAM)g_cfg.status_text[i].c_str());

        hList = CreateWindowExW(WS_EX_CLIENTEDGE, WC_LISTVIEWW, L"",
            WS_CHILD|WS_VISIBLE|LVS_REPORT|LVS_SINGLESEL|LVS_OWNERDRAWFIXED,
            MARGIN, HEADER_HEIGHT+MARGIN,
            rc.right-MARGIN*2, rc.bottom-HEADER_HEIGHT-STATUS_HEIGHT-MARGIN*2,
            hwnd, (HMENU)ID_LISTVIEW, NULL, NULL);

        init_listview(hList);
    }
    return 0;

    case WM_SIZE:
        update_layout(hwnd, hHeader, hStatus, hList, LOWORD(lParam), HIWORD(lParam));
        if (hHeader) {
            InvalidateRect(hHeader, NULL, TRUE);
            UpdateWindow(hHeader);
        }
        return 0;

    case WM_NOTIFY:
    {
        LPNMHDR pnmh = (LPNMHDR)lParam;
        if (pnmh->hwndFrom == hList && pnmh->code == HDN_ENDTRACK) {
        PostMessage(hwnd, WM_SIZE, 0, MAKELPARAM(0, 0));
        }
    }
    return 0;

    case WM_CTLCOLORSTATIC:
        return (LRESULT)handle_ctlcolor_static((HDC)wParam, (HWND)lParam);

    case WM_DRAWITEM:
        if (((DRAWITEMSTRUCT*)lParam)->CtlID == ID_LISTVIEW)
            draw_listview_row((DRAWITEMSTRUCT*)lParam);
        return TRUE;

    case WM_DESTROY:
        DeleteObject(g_hHeaderFont);
        DeleteObject(g_hListFont);
        for (auto &kv : g_previewFonts) DeleteObject(kv.second);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

// WinMain
int WINAPI wWinMain(HINSTANCE hInst, HINSTANCE, PWSTR, int nCmdShow) {
    SetProcessDPIAware();
    load_config();

    WNDCLASSW wc{};
    wc.lpfnWndProc = WndProc;
    wc.hInstance   = hInst;
    wc.hIcon       = LoadIconW(hInst, MAKEINTRESOURCE(IDI_MAIN_ICON));
    wc.hCursor     = LoadCursor(NULL, IDC_ARROW);
    wc.lpszClassName = L"FontFallbackWindow";
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW+1);

    RegisterClassW(&wc);

    HWND hwnd = CreateWindowW(
        wc.lpszClassName, g_cfg.window_title.c_str(),
        WS_OVERLAPPEDWINDOW|WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT, 1200, 800,
        NULL, NULL, hInst, NULL
    );

    // 设置任务栏图标
    HICON hIcon = (HICON)LoadImageW(hInst, MAKEINTRESOURCE(IDI_MAIN_ICON),
                    IMAGE_ICON, 0, 0, LR_DEFAULTSIZE);

    SendMessageW(hwnd, WM_SETICON, ICON_SMALL, (LPARAM)hIcon);
    SendMessageW(hwnd, WM_SETICON, ICON_BIG,   (LPARAM)hIcon);

    ShowWindow(hwnd, nCmdShow);
    UpdateWindow(hwnd);

    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return 0;
}
