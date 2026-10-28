"""SmartProxy v0.8 integration beta, visual reference + real source handling."""
import sys, json, subprocess
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QFrame, QLabel, QPushButton, QLineEdit, QInputDialog, QMessageBox, QScrollArea
from main_v07 import Dashboard as PreviewDashboard, W, H, STYLE
from smartproxy.sources import load, save, add_source, add_manual, collect
from smartproxy.cli import SOURCES, CONFIG, USER_DATA
from smartproxy.core import make_config

class Dashboard(PreviewDashboard):
    def __init__(self):
        super().__init__()
        self.connected=False
        self.nodes=[]
        self.problems=[]
        self.load_existing()
        self.status='نسخه آزمایشی یکپارچه — عملکرد شبکه فقط پس از نصب موتور فعال است'

    def load_existing(self):
        cfg = CONFIG
        if cfg.exists():
            try:
                data=json.loads(cfg.read_text())
                self.nodes=[o for o in data.get('outbounds',[]) if o.get('tag','').startswith('node-')]
            except Exception as ex:self.problems=[str(ex)]

    def source_dialog(self):
        v,ok=QInputDialog.getText(self,'افزودن منبع','لینک HTTPS اشتراک یا کانفیگ VLESS / VMess / Trojan / SS:')
        if not ok or not v.strip():return
        v=v.strip()
        try:
            data=load(SOURCES)
            if v.startswith('https://'):add_source(data,v)
            elif v.startswith(('vless://','vmess://','trojan://','ss://')):add_manual(data,v)
            else:raise ValueError('لینک HTTPS یا URI کانفیگ معتبر وارد کنید')
            save(SOURCES,data)
            self.notify('منبع ذخیره شد؛ برای دریافت، به‌روزرسانی را بزنید')
            self.render_panel()
        except Exception as ex:QMessageBox.warning(self,'خطای افزودن',str(ex))

    def add_personal(self):self.source_dialog()

    def refresh(self):
        try:
            nodes,problems=collect(load(SOURCES))
            self.nodes=nodes;self.problems=problems
            if nodes:
                USER_DATA.mkdir(parents=True,exist_ok=True);USER_DATA.chmod(0o700)
                CONFIG.write_text(json.dumps(make_config(nodes,'tun'),ensure_ascii=False,indent=2))
                CONFIG.chmod(0o600)
            self.notify(f'{len(nodes)} سرور دریافت شد؛ {len(problems)} خطای منبع')
            self.render_panel()
        except Exception as ex:QMessageBox.warning(self,'خطای دریافت کانفیگ',str(ex))

    def toggle_connection(self):
        action='stop' if self.connected else 'start'
        if action=='start' and not self.nodes:
            self.notify('هنوز کانفیگ واقعی دریافت نشده؛ ابتدا منبع را اضافه و به‌روزرسانی کنید')
            return
        ans=QMessageBox.question(self,'تغییر وضعیت VPN',f'اجرای فرمان واقعی smartproxy {action} ؟\nاین کار ممکن است مسیر شبکه را تغییر دهد.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if ans!=QMessageBox.Yes:return
        try:
            p=subprocess.run([sys.executable,'-m','smartproxy.cli',action],text=True,capture_output=True,timeout=45)
            if p.returncode != 0:raise RuntimeError((p.stderr or p.stdout or 'خطای نامشخص')[:1200])
            self.connected=(action=='start')
            self.notify(f'فرمان {action} با موفقیت اجرا شد')
        except Exception as ex:QMessageBox.warning(self,'اتصال ناموفق',str(ex))

    def select_server(self,i):
        self.notify('برای انتخاب سرور واقعی از فهرست کانفیگ‌های دریافتی استفاده کنید؛ انتخاب تصویر نمایشی اعمال نمی‌شود')

    def render_panel(self):
        self.remove_overlay()
        p=QFrame(self);p.setObjectName('panel');p.setStyleSheet(STYLE);self.overlay=p
        layout=QVBoxLayout(p);layout.setContentsMargins(18,14,18,14)
        line=QHBoxLayout()
        label=QLabel('سرورهای واقعی و مدیریت منابع');label.setStyleSheet('font-size:20px;font-weight:bold')
        back=QPushButton('× بستن');back.clicked.connect(self.remove_overlay)
        line.addWidget(label);line.addStretch();line.addWidget(back);layout.addLayout(line)
        row=QHBoxLayout()
        a=QPushButton('افزودن URL یا کانفیگ');a.clicked.connect(self.source_dialog)
        b=QPushButton('دریافت و به‌روزرسانی');b.clicked.connect(self.refresh)
        c=QPushButton('بررسی sing-box');c.clicked.connect(self.check_config)
        row.addWidget(a);row.addWidget(b);row.addWidget(c);layout.addLayout(row)
        src=load(SOURCES)
        layout.addWidget(QLabel(f'اشتراک‌ها: {len(src.get("sources",[]))} | کانفیگ‌های دستی: {len(src.get("manual",[]))} | سرورهای دریافت‌شده: {len(self.nodes)}'))
        scroll=QScrollArea();scroll.setWidgetResizable(True);host=QWidget();vl=QVBoxLayout(host)
        query=self.query.casefold()
        if self.page=='تنظیمات':
            vl.addWidget(QLabel('تنظیمات انتخاب خودکار در این نسخه فقط محلی است؛ به موتور Failover متصل نیست.'))
        for i,node in enumerate(self.nodes):
            title=node.get('server','بدون آدرس')
            protocol=node.get('type','?')
            tag=node.get('tag',f'node-{i+1}')
            label=f'{tag}   |   {protocol}   |   {title} : {node.get("server_port",node.get("port","?"))}'
            if query and query not in label.casefold():continue
            item=QLabel(label);item.setStyleSheet('background:#1a294c;border-radius:8px;padding:11px;')
            vl.addWidget(item)
        if not self.nodes:vl.addWidget(QLabel('هنوز سروری دریافت نشده؛ آدرس مستقیم Subscription یا کانفیگ شخصی وارد کنید.'))
        for problem in self.problems[:6]:vl.addWidget(QLabel('خطای منبع: '+str(problem)[:170]))
        vl.addStretch();scroll.setWidget(host);layout.addWidget(scroll)
        self.position_panel();p.show();p.raise_();self.toast.raise_()

    def check_config(self):
        try:
            p=subprocess.run([sys.executable,'-m','smartproxy.cli','check'],capture_output=True,text=True,timeout=30)
            QMessageBox.information(self,'بررسی کانفیگ',f'کد خروج: {p.returncode}\n'+(p.stdout+p.stderr)[:1800])
        except Exception as ex:QMessageBox.warning(self,'خطا',str(ex))

    def open_tab(self,name):self.tab=name;self.page='سرورها';self.render_panel()
    def navigate(self,name):
        if name=='داشبورد':self.page=name;self.remove_overlay();self.notify('داشبورد')
        else:self.page=name;self.render_panel()
    def best_server(self):self.notify('انتخاب خودکار واقعی هنوز به موتور Failover متصل نیست')

class Main(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('SmartProxy v0.8 — Integration Beta');self.setCentralWidget(Dashboard());self.resize(W,H);self.setMinimumSize(1050,700)

if __name__=='__main__':
    app=QApplication(sys.argv);app.setLayoutDirection(Qt.LeftToRight);app.setStyle('Fusion');w=Main();w.show();sys.exit(app.exec())
