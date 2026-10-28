
import sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QSizePolicy, QCheckBox,
    QComboBox
)

COLORS = {
    "bg": "#0a1020",
    "panel": "#111a2e",
    "panel2": "#131e35",
    "border": "#273653",
    "muted": "#9ca8c8",
    "text": "#f6f8ff",
    "purple": "#6d4cff",
    "purple2": "#8e4fff",
    "green": "#24d18f",
    "cyan": "#17c4ff",
    "pink": "#da47d7",
    "amber": "#ffb14a",
    "red": "#ff5a78",
}

STYLE = f"""
QMainWindow, QWidget {{
    background: {COLORS["bg"]};
    color: {COLORS["text"]};
    font-family: "Vazirmatn","Noto Sans Arabic","DejaVu Sans";
}}
QFrame#sidebar, QFrame#rightPanel, QFrame#statusBox, QFrame#trafficBox, QFrame#routeBox, QFrame#autoBox {{
    background: {COLORS["panel"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 18px;
}}
QFrame#hero {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #1d4dd8, stop:.34 #4947d6, stop:.67 #884bb6, stop:1 #233c75);
    border: 1px solid #455991;
    border-radius: 24px;
}}
QFrame#serverCard {{
    background: {COLORS["panel2"]};
    border: 1px solid #30405f;
    border-radius: 17px;
}}
QFrame#serverCard[selected="true"] {{
    border: 2px solid #8d4bff;
    background: #172342;
}}
QPushButton {{
    background: #14213a;
    color: {COLORS["text"]};
    border: 1px solid #334768;
    border-radius: 12px;
    padding: 9px 14px;
}}
QPushButton:hover {{
    background: #1d2d4f;
}}
QPushButton#nav {{
    border: none;
    background: transparent;
    text-align: right;
    padding: 13px 16px;
    font-size: 14px;
}}
QPushButton#navActive {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2d3ea5, stop:1 #283181);
    border: 1px solid #3d4db5;
    text-align: right;
    padding: 13px 16px;
    font-size: 14px;
}}
QPushButton#primary {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #4947ff, stop:1 #6d4cff);
    border: 1px solid #6659ff;
    font-weight: 800;
}}
QPushButton#connect {{
    background: #12363b;
    border: 1px solid #168d88;
    min-width: 76px;
}}
QPushButton#connected {{
    background: #1bbd78;
    border: 1px solid #3ae49c;
    font-weight: 700;
}}
QLineEdit {{
    background: #11192c;
    border: 1px solid #34415f;
    border-radius: 12px;
    padding: 11px 14px;
    color: {COLORS["text"]};
}}
QComboBox {{
    background: #11192c;
    border: 1px solid #34415f;
    border-radius: 10px;
    padding: 8px 10px;
}}
QCheckBox {{
    spacing: 8px;
}}
QScrollArea {{
    border: none;
}}
"""

SERVERS = [
    dict(flag="🇩🇪", country="Germany", city="Frankfurt", proto="VLESS", transport="TCP", ping=23, fav=True, connected=True),
    dict(flag="🇳🇱", country="Netherlands", city="Amsterdam", proto="VLESS", transport="WS", ping=28),
    dict(flag="🇫🇮", country="Finland", city="Helsinki", proto="VLESS", transport="Reality", ping=32),
    dict(flag="🇺🇸", country="United States", city="New York", proto="VLESS", transport="gRPC", ping=145),
    dict(flag="🇬🇧", country="United Kingdom", city="London", proto="VLESS", transport="WS", ping=110),
    dict(flag="🇨🇦", country="Canada", city="Toronto", proto="VLESS", transport="TCP", ping=120),
    dict(flag="🇫🇷", country="France", city="Paris", proto="VLESS", transport="Reality", ping=98),
    dict(flag="🇸🇬", country="Singapore", city="Singapore", proto="VLESS", transport="WS", ping=210),
    dict(flag="🇯🇵", country="Japan", city="Tokyo", proto="VLESS", transport="TCP", ping=180),
]

def ping_color(v):
    if v < 60: return COLORS["green"]
    if v < 130: return COLORS["amber"]
    return COLORS["red"]

class ServerCard(QFrame):
    def __init__(self, s):
        super().__init__()
        self.setObjectName("serverCard")
        self.setProperty("selected", "true" if s.get("connected") else "false")
        self.setMinimumHeight(142)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16,14,16,14)
        lay.setSpacing(8)

        top = QHBoxLayout()
        flag = QLabel(s["flag"]); flag.setStyleSheet("font-size:34px;")
        names = QVBoxLayout()
        country = QLabel(s["country"]); country.setStyleSheet("font-size:15px;font-weight:900;")
        city = QLabel(s["city"]); city.setStyleSheet(f"color:{COLORS['muted']};font-size:13px;")
        names.addWidget(country); names.addWidget(city)
        star = QLabel("★" if s.get("fav") else "☆")
        star.setStyleSheet(f"font-size:22px;color:{COLORS['green'] if s.get('fav') else '#8ea0ca'};")
        top.addWidget(flag); top.addLayout(names,1); top.addWidget(star)
        lay.addLayout(top)

        proto = QLabel(f'{s["proto"]}  ·  {s["transport"]}')
        proto.setStyleSheet(f"color:{COLORS['muted']};")
        lay.addWidget(proto)

        bottom = QHBoxLayout()
        ping = QLabel(f'{s["ping"]} ms   ▂▅▇')
        ping.setStyleSheet(f"color:{ping_color(s['ping'])};font-weight:900;")
        btn = QPushButton("✓ متصل" if s.get("connected") else "اتصال")
        btn.setObjectName("connected" if s.get("connected") else "connect")
        bottom.addWidget(ping); bottom.addStretch(); bottom.addWidget(btn)
        lay.addLayout(bottom)

class SmartProxy(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartProxy v0.5 — UI Preview")
        self.resize(1540, 1000)
        self.setMinimumSize(1320, 820)

        rootw = QWidget()
        self.setCentralWidget(rootw)
        root = QHBoxLayout(rootw)
        root.setContentsMargins(18,18,18,18)
        root.setSpacing(16)

        # Sidebar
        side = QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(260)
        sl = QVBoxLayout(side); sl.setContentsMargins(18,18,18,18); sl.setSpacing(8)

        logoRow = QHBoxLayout()
        shield = QLabel("⚡"); shield.setAlignment(Qt.AlignCenter); shield.setFixedSize(54,54)
        shield.setStyleSheet("background:#5c45ff;border-radius:18px;font-size:26px;font-weight:900;")
        bt = QVBoxLayout()
        brand = QLabel("SmartProxy"); brand.setStyleSheet("font-size:24px;font-weight:900;")
        version = QLabel("v0.4"); version.setStyleSheet(f"color:{COLORS['muted']};")
        bt.addWidget(brand); bt.addWidget(version)
        logoRow.addWidget(shield); logoRow.addLayout(bt); logoRow.addStretch()
        sl.addLayout(logoRow)
        sl.addSpacing(18)

        navs = [
            ("⌂","داشبورد"),("◎","همه سرورها"),("☁","یام‌یام"),("☆","کانفیگ‌های من"),
            ("⚙","تنظیمات"),("🛠","ابزارها"),("▥","گزارش‌ها"),("ⓘ","درباره برنامه")
        ]
        for i,(ic,tx) in enumerate(navs):
            b = QPushButton(f"{ic}    {tx}")
            b.setObjectName("navActive" if i==0 else "nav")
            sl.addWidget(b)

        sl.addStretch()

        theme = QFrame(); theme.setObjectName("statusBox")
        tl = QHBoxLayout(theme); tl.setContentsMargins(14,10,14,10)
        t = QLabel("☀   ◉"); t.setStyleSheet("font-size:18px;")
        tx = QLabel("حالت تاریک"); tx.setStyleSheet("font-weight:700;")
        tl.addWidget(t); tl.addStretch(); tl.addWidget(tx)
        sl.addWidget(theme)

        engine = QFrame(); engine.setObjectName("statusBox")
        el = QVBoxLayout(engine); el.setContentsMargins(14,12,14,12)
        er = QHBoxLayout()
        dot = QLabel("●"); dot.setStyleSheet(f"color:{COLORS['green']};")
        en = QLabel("sing-box"); en.setStyleSheet("font-weight:800;")
        arrow = QLabel("›"); arrow.setStyleSheet("font-size:22px;color:#b8c1df;")
        er.addWidget(dot); er.addWidget(en); er.addStretch(); er.addWidget(arrow)
        sub = QLabel("در حال اجرا"); sub.setStyleSheet(f"color:{COLORS['muted']};")
        el.addLayout(er); el.addWidget(sub)
        sl.addWidget(engine)
        root.addWidget(side)

        # Center
        center = QVBoxLayout(); center.setSpacing(14)

        topbar = QHBoxLayout()
        search = QLineEdit(); search.setPlaceholderText("جستجوی کشور، شهر یا نام سرور...")
        search.setFixedHeight(48)
        refresh = QPushButton("↻  به‌روزرسانی کانفیگ‌ها  ⌄"); refresh.setObjectName("primary"); refresh.setFixedHeight(48)
        topbar.addWidget(search,1); topbar.addWidget(refresh)
        center.addLayout(topbar)

        hero = QFrame(); hero.setObjectName("hero"); hero.setMinimumHeight(245)
        hl = QHBoxLayout(hero); hl.setContentsMargins(24,22,24,22)

        left = QVBoxLayout(); left.setSpacing(8)
        first = QHBoxLayout()
        flag = QLabel("🇩🇪"); flag.setStyleSheet("font-size:58px;")
        cinfo = QVBoxLayout()
        st = QLabel("●  متصل هستید"); st.setStyleSheet("font-size:19px;font-weight:900;color:#9ef45d;")
        loc = QLabel("Germany – Frankfurt"); loc.setStyleSheet("font-size:23px;font-weight:900;")
        meta = QLabel("VLESS   ·   203.0.113.10"); meta.setStyleSheet("font-size:15px;color:#eef3ff;")
        cinfo.addWidget(st); cinfo.addWidget(loc); cinfo.addWidget(meta)
        first.addWidget(flag); first.addLayout(cinfo); first.addStretch()
        left.addLayout(first)
        left.addStretch()
        change = QPushButton("⇄  تغییر سرور"); change.setMaximumWidth(150)
        left.addWidget(change)
        hl.addLayout(left,1)

        p = QVBoxLayout(); p.setAlignment(Qt.AlignCenter)
        power = QPushButton("⏻"); power.setFixedSize(118,118)
        power.setStyleSheet("font-size:48px;background:#149c62;border:4px solid white;border-radius:59px;font-weight:900;")
        off = QPushButton("قطع اتصال"); off.setStyleSheet("background:#9d3e86;border:1px solid #c15ca6;")
        p.addWidget(power, alignment=Qt.AlignCenter); p.addWidget(off)
        hl.addLayout(p)
        center.addWidget(hero)

        # tabs
        tabrow = QHBoxLayout()
        for i,(ic,tx) in enumerate([("◎","همه کشورها"),("☁","یام‌یام"),("★","کانفیگ‌های من"),("♡","علاقه‌مندی‌ها")]):
            b=QPushButton(f"{ic}   {tx}")
            if i==0: b.setObjectName("primary")
            b.setFixedHeight(54)
            tabrow.addWidget(b,1)
        center.addLayout(tabrow)

        filterrow = QHBoxLayout()
        proto = QComboBox(); proto.addItems(["همه پروتکل‌ها","VLESS","VMess","Trojan","Shadowsocks"])
        country = QComboBox(); country.addItems(["همه کشورها","Germany","Netherlands","Finland","United States","United Kingdom","Canada","France","Singapore","Japan"])
        gridBtn = QPushButton("▦"); gridBtn.setObjectName("primary"); gridBtn.setFixedWidth(52)
        listBtn = QPushButton("☷"); listBtn.setFixedWidth(52)
        filterrow.addWidget(proto); filterrow.addWidget(country); filterrow.addStretch(); filterrow.addWidget(gridBtn); filterrow.addWidget(listBtn)
        center.addLayout(filterrow)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        host = QWidget(); grid = QGridLayout(host); grid.setSpacing(14)
        for i,s in enumerate(SERVERS):
            grid.addWidget(ServerCard(s), i//3, i%3)
        for c in range(3): grid.setColumnStretch(c,1)
        scroll.setWidget(host)
        center.addWidget(scroll,1)
        root.addLayout(center,1)

        # Right panel
        right = QVBoxLayout(); right.setSpacing(14)
        rightWrap = QWidget(); rightWrap.setFixedWidth(300)
        rightWrap.setLayout(right)

        status = QFrame(); status.setObjectName("statusBox")
        q = QVBoxLayout(status); q.setContentsMargins(16,15,16,15)
        h = QHBoxLayout()
        title = QLabel("وضعیت اتصال"); title.setStyleSheet("font-size:18px;font-weight:900;")
        connected = QLabel("●  متصل"); connected.setStyleSheet(f"color:{COLORS['green']};font-weight:900;")
        h.addWidget(title); h.addStretch(); h.addWidget(connected); q.addLayout(h)
        q.addWidget(QLabel("────────────────────────"))
        for k,v in [("کشور فعلی","🇩🇪 آلمان"),("IP خارجی","203.0.113.10"),("مدت اتصال","00:12:36")]:
            row = QHBoxLayout(); a=QLabel(k); a.setStyleSheet(f"color:{COLORS['muted']};"); b=QLabel(v); b.setStyleSheet("font-weight:800;")
            row.addWidget(a); row.addStretch(); row.addWidget(b); q.addLayout(row)
        right.addWidget(status)

        traffic = QFrame(); traffic.setObjectName("trafficBox")
        tq = QVBoxLayout(traffic); tq.setContentsMargins(16,15,16,15)
        ttitle = QLabel("ترافیک لحظه‌ای"); ttitle.setStyleSheet("font-size:17px;font-weight:900;")
        tq.addWidget(ttitle)
        tr = QHBoxLayout()
        dl = QLabel("↓  دانلود\n12.4 Mbps"); dl.setStyleSheet("font-size:14px;font-weight:800;")
        ul = QLabel("↑  آپلود\n3.6 Mbps"); ul.setStyleSheet("font-size:14px;font-weight:800;")
        tr.addWidget(dl); tr.addStretch(); tr.addWidget(ul)
        tq.addLayout(tr)
        graph = QLabel("╲╱╲╱╲╱╲╱\n  ╲╱╲╱╲╱"); graph.setAlignment(Qt.AlignCenter)
        graph.setStyleSheet(f"font-size:24px;color:{COLORS['cyan']};padding:8px;")
        tq.addWidget(graph)
        right.addWidget(traffic)

        route = QFrame(); route.setObjectName("routeBox")
        rq = QVBoxLayout(route); rq.setContentsMargins(16,15,16,15)
        rt = QLabel("مسیر ترافیک"); rt.setStyleSheet("font-size:17px;font-weight:900;"); rq.addWidget(rt)
        for lefttxt,righttxt,color in [
            ("◎  سایت‌های ایرانی","عبور مستقیم",COLORS["green"]),
            ("◎  سایر سایت‌ها","از طریق VPN","#b55cff"),
            ("⚙  قوانین مسیریابی","›","#c7d0ea"),
        ]:
            row=QHBoxLayout(); a=QLabel(lefttxt); b=QLabel(righttxt); b.setStyleSheet(f"color:{color};font-weight:800;")
            row.addWidget(a); row.addStretch(); row.addWidget(b); rq.addLayout(row)
        right.addWidget(route)

        auto = QFrame(); auto.setObjectName("autoBox")
        aq = QVBoxLayout(auto); aq.setContentsMargins(16,15,16,15)
        for title,sub in [("اتصال خودکار","در صورت قطع، خودکار وصل شود"),("انتخاب خودکار سرور","بهترین سرور را انتخاب کند")]:
            row=QHBoxLayout()
            texts=QVBoxLayout()
            a=QLabel(title); a.setStyleSheet("font-size:15px;font-weight:800;")
            b=QLabel(sub); b.setStyleSheet(f"color:{COLORS['muted']};font-size:12px;")
            texts.addWidget(a); texts.addWidget(b)
            tog=QCheckBox(); tog.setChecked(True)
            row.addLayout(texts,1); row.addWidget(tog)
            aq.addLayout(row)
        right.addWidget(auto)
        right.addStretch()

        root.addWidget(rightWrap)

def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LeftToRight)
    app.setStyleSheet(STYLE)
    font=QFont(); font.setPointSize(10); app.setFont(font)
    w=SmartProxy(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
