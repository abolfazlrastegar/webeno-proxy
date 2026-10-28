"""SmartProxy v0.7 visual interactive prototype. NO VPN/network modifications."""
import sys, json
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from PySide6.QtWidgets import (QApplication, QWidget, QMainWindow, QPushButton, QLabel,
    QLineEdit, QVBoxLayout, QHBoxLayout, QScrollArea, QComboBox, QCheckBox, QFrame,
    QInputDialog, QFileDialog, QMessageBox)

BASE=Path(__file__).resolve().parent
ART=BASE/'assets/smartproxy_reference.png'
STATE=Path.home()/'.config/smartproxy-ui-preview/settings.json'
W,H=1536,1024
SERVERS=[
 dict(name='Germany',city='Frankfurt',country='آلمان',proto='VLESS',transport='TCP',ping=23,source='یام‌یام'),
 dict(name='Netherlands',city='Amsterdam',country='هلند',proto='VLESS',transport='WS',ping=28,source='یام‌یام'),
 dict(name='Finland',city='Helsinki',country='فنلاند',proto='VLESS',transport='Reality',ping=32,source='یام‌یام'),
 dict(name='United States',city='New York',country='آمریکا',proto='VLESS',transport='gRPC',ping=145,source='یام‌یام'),
 dict(name='United Kingdom',city='London',country='بریتانیا',proto='VLESS',transport='WS',ping=110,source='یام‌یام'),
 dict(name='Canada',city='Toronto',country='کانادا',proto='VLESS',transport='TCP',ping=120,source='یام‌یام'),
 dict(name='France',city='Paris',country='فرانسه',proto='VLESS',transport='Reality',ping=98,source='یام‌یام'),
 dict(name='Singapore',city='Singapore',country='سنگاپور',proto='VLESS',transport='WS',ping=210,source='یام‌یام'),
 dict(name='Japan',city='Tokyo',country='ژاپن',proto='VLESS',transport='TCP',ping=180,source='یام‌یام')]
RECTS=[(309+c*302,511+r*170,289,154) for r in range(3) for c in range(3)]
STYLE='''QWidget#panel {background:#101a35;border:1px solid #33436b;border-radius:19px;color:#f1f4ff} QLabel{color:#eaf0ff} QPushButton{background:#263b8d;color:white;border:1px solid #4859a4;border-radius:10px;padding:9px;font-size:13px} QPushButton:hover{background:#3f4ec0} QLineEdit,QComboBox{background:#1c2a49;color:white;border:1px solid #53628c;border-radius:8px;padding:9px} QCheckBox{color:white;font-size:13px} QScrollArea{border:0;background:transparent}'''

def load():
 try:return json.loads(STATE.read_text())
 except Exception:return {}

class Spot(QPushButton):
 def __init__(self,parent,box,callback):
  super().__init__(parent);self.box=box;self.clicked.connect(callback)
  self.setCursor(Qt.PointingHandCursor);self.setFocusPolicy(Qt.NoFocus)
  self.setStyleSheet('QPushButton{background:transparent;border:0} QPushButton:hover{background:rgba(140,105,255,40);border:1px solid #7867cf;border-radius:10px}')

class Dashboard(QWidget):
 def __init__(self):
  super().__init__();self.pix=QPixmap(str(ART));assert not self.pix.isNull()
  self.data=load();self.connected=False;self.current=int(self.data.get('selected',0))%len(SERVERS)
  self.auto_connect=self.data.get('auto_connect',True);self.auto_select=self.data.get('auto_select',True)
  self.favorites=set(self.data.get('favorites',[0]));self.personal=self.data.get('personal',[])
  self.query='';self.country='همه کشورها';self.protocol='همه پروتکل‌ها';self.tab='همه کشورها';self.page='داشبورد';self.view='grid'
  self.updated=self.data.get('updated','هرگز');self.spots=[];self.overlay=None;self.status='حالت نمایشی: اتصال واقعی غیرفعال است'
  self.make_spots();self.toast=QLabel(self);self.toast.setStyleSheet('background:#253d79;color:white;padding:10px;border:1px solid #7285c9;border-radius:9px');self.toast.setAlignment(Qt.AlignCenter);self.toast.hide()
  self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.toast.hide)
  self.resize(W,H)
 def save(self):
  STATE.parent.mkdir(parents=True,exist_ok=True)
  STATE.write_text(json.dumps(dict(selected=self.current,auto_connect=self.auto_connect,auto_select=self.auto_select,favorites=sorted(self.favorites),personal=self.personal,updated=self.updated),ensure_ascii=False,indent=2))
 def notify(self,s):
  self.status=s;self.toast.setText(s);self.toast.adjustSize();self.toast.move(max(0,(self.width()-self.toast.width())//2),max(5,self.height()-70));self.toast.raise_();self.toast.show();self.timer.start(3600);self.update()
 def spot(self,rect,cb):self.spots.append(Spot(self,rect,cb))
 def make_spots(self):
  self.spot((1000,141,146,193),self.toggle_connection);self.spot((328,269,140,60),self.choose_server)
  self.spot((948,24,255,55),self.refresh);self.spot((307,24,480,54),self.search)
  for name,rect in [('همه کشورها',(308,365,212,57)),('یام‌یام',(527,365,218,57)),('کانفیگ‌های من',(752,365,216,57)),('علاقه‌مندی‌ها',(978,365,219,57))]:self.spot(rect,lambda n=name:self.open_tab(n))
  self.spot((310,444,208,49),lambda:self.filter('protocol'));self.spot((534,444,202,49),lambda:self.filter('country'))
  self.spot((1098,443,53,49),lambda:self.change_view('grid'));self.spot((1153,443,48,49),lambda:self.change_view('list'))
  for i,r in enumerate(RECTS):
   self.spot((r[0],r[1],r[2]-50,r[3]),lambda x=i:self.select_server(x))
   self.spot((r[0]+r[2]-50,r[1]+9,40,48),lambda x=i:self.toggle_favorite(x))
  nav=['داشبورد','همه سرورها','یام‌یام','کانفیگ‌های من','تنظیمات','ابزارها','گزارش‌ها','درباره برنامه']
  for i,n in enumerate(nav):self.spot((20,118+i*60,255,59),lambda x=n:self.navigate(x))
  self.spot((1450,845,56,50),self.toggle_auto_connect);self.spot((1450,926,56,52),self.toggle_auto_select)
  self.spot((1219,755,286,52),lambda:self.navigate('قوانین مسیریابی'))
  self.spot((20,793,256,69),lambda:self.navigate('حالت نمایش'));self.spot((20,878,256,104),lambda:self.navigate('وضعیت sing-box'))
  self.spot((1462,0,74,75),lambda:self.window().close())
 def toggle_connection(self):
  self.connected=not self.connected;self.notify(('اتصال نمایشی برقرار شد' if self.connected else 'اتصال نمایشی قطع شد')+'؛ هیچ VPN واقعی فعال نیست')
 def select_server(self,i):
  if not self.allow_server(i):self.notify('این سرور با فیلتر فعلی منطبق نیست');return
  self.current=i;self.save();self.notify('سرور انتخاب شد: '+SERVERS[i]['name']+' / '+SERVERS[i]['city']+' (نمایشی)')
 def choose_server(self):self.open_tab('همه کشورها')
 def toggle_favorite(self,i):
  if i in self.favorites:self.favorites.remove(i);msg='از علاقه‌مندی‌ها حذف شد'
  else:self.favorites.add(i);msg='به علاقه‌مندی‌ها اضافه شد'
  self.save();self.notify(msg+' — '+SERVERS[i]['name'])
 def toggle_auto_connect(self):
  self.auto_connect=not self.auto_connect;self.save();self.notify('اتصال خودکار '+('روشن' if self.auto_connect else 'خاموش')+' شد (تنظیم ذخیره شد)')
 def toggle_auto_select(self):
  self.auto_select=not self.auto_select
  if self.auto_select:
   candidates=[i for i in range(len(SERVERS)) if self.allow_server(i)]
   if candidates:self.current=min(candidates,key=lambda i:SERVERS[i]['ping'])
  self.save();self.notify('انتخاب خودکار سرور '+('روشن' if self.auto_select else 'خاموش')+' شد (بر پایه پینگ نمونه)')
 def refresh(self):
  self.updated=datetime.now().strftime('%Y-%m-%d %H:%M');self.save();self.notify('به‌روزرسانی نمایشی در '+self.updated+' ثبت شد؛ هیچ منبع آنلاینی دریافت نشد')
  if self.overlay:self.render_panel()
 def search(self):
  s,ok=QInputDialog.getText(self,'جستجوی سرور','نام، کشور یا شهر:',text=self.query)
  if ok:self.query=s.strip();self.open_tab(self.tab)
 def filter(self,kind):
  if kind=='country':vals=['همه کشورها']+sorted({s['country'] for s in SERVERS});cur=self.country
  else:vals=['همه پروتکل‌ها']+sorted({s['transport'] for s in SERVERS});cur=self.protocol
  v,ok=QInputDialog.getItem(self,'فیلتر','گزینه:',vals,vals.index(cur) if cur in vals else 0,False)
  if ok:
   if kind=='country':self.country=v
   else:self.protocol=v
   self.open_tab(self.tab)
 def allow_server(self,i):
  s=SERVERS[i]
  return (not self.query or self.query.casefold() in (' '.join(map(str,s.values()))).casefold()) and (self.country=='همه کشورها' or s['country']==self.country) and (self.protocol=='همه پروتکل‌ها' or s['transport']==self.protocol) and (self.tab not in ['علاقه‌مندی‌ها','کانفیگ‌های من'] or (i in self.favorites if self.tab=='علاقه‌مندی‌ها' else False))
 def open_tab(self,name):self.tab=name;self.page='سرورها';self.render_panel()
 def navigate(self,name):
  if name=='داشبورد':self.page='داشبورد';self.remove_overlay();self.notify('داشبورد')
  elif name in ['همه سرورها','یام‌یام','کانفیگ‌های من']:
   self.open_tab({'همه سرورها':'همه کشورها'}.get(name,name))
  else:self.page=name;self.render_panel()
 def change_view(self,v):self.view=v;self.open_tab(self.tab)
 def remove_overlay(self):
  if self.overlay:self.overlay.deleteLater();self.overlay=None
 def render_panel(self):
  self.remove_overlay();p=QFrame(self);p.setObjectName('panel');p.setStyleSheet(STYLE);self.overlay=p
  lay=QVBoxLayout(p);lay.setContentsMargins(22,18,22,18);lay.setSpacing(12)
  header=QHBoxLayout();title=QLabel(self.tab if self.page=='سرورها' else self.page);title.setStyleSheet('font-size:24px;font-weight:bold');header.addWidget(title);header.addStretch()
  close=QPushButton('× بازگشت به داشبورد');close.clicked.connect(lambda:self.navigate('داشبورد'));header.addWidget(close);lay.addLayout(header)
  subtitle=QLabel('پیش‌نمایش تعاملی — هیچ عملیات VPN یا تغییر شبکه‌ای انجام نمی‌شود');subtitle.setStyleSheet('color:#adc0f4');lay.addWidget(subtitle)
  if self.page=='سرورها':
   bar=QHBoxLayout();search=QLineEdit(self.query);search.setPlaceholderText('جستجوی نام سرور، کشور یا شهر...');search.textChanged.connect(self.change_query);bar.addWidget(search)
   country=QComboBox();country.addItems(['همه کشورها']+sorted({s['country'] for s in SERVERS}));country.setCurrentText(self.country);country.currentTextChanged.connect(self.change_country);bar.addWidget(country)
   protocol=QComboBox();protocol.addItems(['همه پروتکل‌ها']+sorted({s['transport'] for s in SERVERS}));protocol.setCurrentText(self.protocol);protocol.currentTextChanged.connect(self.change_proto);bar.addWidget(protocol);lay.addLayout(bar)
   self.itemsbox=QScrollArea();self.itemsbox.setWidgetResizable(True);lay.addWidget(self.itemsbox);self.render_rows()
   lower=QHBoxLayout();add=QPushButton('افزودن کانفیگ شخصی');add.clicked.connect(self.add_personal);lower.addWidget(add)
   refresh=QPushButton('بررسی به‌روزرسانی نمایشی');refresh.clicked.connect(self.refresh);lower.addWidget(refresh);lay.addLayout(lower)
  elif self.page=='تنظیمات':
   for text,flag,handler in [('اتصال خودکار پس از قطع (ذخیره محلی)','auto_connect',self.toggle_auto_connect),('انتخاب خودکار کمترین پینگ نمونه','auto_select',self.toggle_auto_select)]:
    c=QCheckBox(text);c.setChecked(getattr(self,flag));c.toggled.connect(lambda _,h=handler:h());lay.addWidget(c)
   reset=QPushButton('پاک‌کردن فیلترها');reset.clicked.connect(self.clear_filters);lay.addWidget(reset);lay.addStretch()
  elif self.page=='ابزارها':
   for text,cb in [('انتخاب سریع بهترین سرور نمونه',self.best_server),('به‌روزرسانی وضعیت نمونه',self.refresh),('خروجی گرفتن از تنظیمات محلی',self.export_settings),('افزودن کانفیگ شخصی',self.add_personal)]:
    b=QPushButton(text);b.clicked.connect(cb);lay.addWidget(b)
   lay.addStretch()
  elif self.page=='گزارش‌ها':
   for s in [f'وضعیت اتصال: {"نمایشی متصل" if self.connected else "قطع"}',f'سرور انتخابی: {SERVERS[self.current]["name"]}',f'آخرین بررسی نمایشی: {self.updated}',f'تعداد علاقه‌مندی‌ها: {len(self.favorites)}']:
    lay.addWidget(QLabel(s))
   lay.addStretch()
  elif self.page=='قوانین مسیریابی':
   lay.addWidget(QLabel('قوانین مسیر فقط برای نمایش هستند؛ مسیریابی سیستم اجرا نمی‌شود.'))
   for s in ['وب‌سایت‌های ایرانی: مسیر مستقیم (نمونه)','سایر سایت‌ها: مسیر VPN (نمونه)']:
    lay.addWidget(QLabel(s))
   lay.addStretch()
  else:
   lay.addWidget(QLabel('SmartProxy v0.7 | رابط نمایشی قابل تعامل، بدون موتور VPN'))
   lay.addWidget(QLabel('نسخه واقعی بعداً به هسته موجود متصل خواهد شد.'));lay.addStretch()
  self.position_panel();p.show();p.raise_();self.toast.raise_()
 def change_query(self,v):self.query=v;self.render_rows()
 def change_country(self,v):self.country=v;self.render_rows()
 def change_proto(self,v):self.protocol=v;self.render_rows()
 def render_rows(self):
  if not hasattr(self,'itemsbox'):return
  body=QWidget();layout=QVBoxLayout(body);layout.setSpacing(8)
  visible=[i for i in range(len(SERVERS)) if self.allow_server(i)]
  if self.tab=='کانفیگ‌های من':
   for item in self.personal:
    row=QLabel('کانفیگ شخصی: '+item.get('name','بدون نام')+' — فقط ذخیره محلی');row.setStyleSheet('background:#243052;border-radius:10px;padding:12px');layout.addWidget(row)
  for i in visible:
   s=SERVERS[i];line=QHBoxLayout();flag=QLabel(f'{s["name"]} — {s["city"]} | {s["transport"]} | {s["ping"]} ms');line.addWidget(flag,1)
   fav=QPushButton('★' if i in self.favorites else '☆');fav.setFixedWidth(50);fav.clicked.connect(lambda _,n=i:self.favorite_from_panel(n));line.addWidget(fav)
   select=QPushButton('انتخاب شده' if self.current==i else 'انتخاب');select.clicked.connect(lambda _,n=i:self.select_from_panel(n));line.addWidget(select)
   wrap=QWidget();wrap.setLayout(line);wrap.setStyleSheet('background:#1b2947;border-radius:12px');layout.addWidget(wrap)
  if not visible and not (self.tab=='کانفیگ‌های من' and self.personal):layout.addWidget(QLabel('نتیجه‌ای با فیلترهای انتخاب‌شده پیدا نشد.'))
  layout.addStretch();self.itemsbox.setWidget(body)
 def select_from_panel(self,n):self.select_server(n);self.render_rows()
 def favorite_from_panel(self,n):self.toggle_favorite(n);self.render_rows()
 def clear_filters(self):self.query='';self.country='همه کشورها';self.protocol='همه پروتکل‌ها';self.notify('فیلترها پاک شدند')
 def best_server(self):
  self.current=min(range(len(SERVERS)),key=lambda i:SERVERS[i]['ping']);self.save();self.notify('سرور نمونه با کمترین پینگ انتخاب شد: '+SERVERS[self.current]['name'])
 def add_personal(self):
  v,ok=QInputDialog.getText(self,'افزودن کانفیگ','نام کانفیگ شخصی (بدون اتصال به موتور):')
  if ok and v.strip():self.personal.append({'name':v.strip()});self.save();self.notify('کانفیگ شخصی ذخیره شد');self.render_panel()
 def export_settings(self):
  filename,_=QFileDialog.getSaveFileName(self,'ذخیره تنظیمات','smartproxy-preview-settings.json','JSON (*.json)')
  if filename:self.save();Path(filename).write_text(STATE.read_text());self.notify('تنظیمات محلی صادر شد')
 def position_panel(self):
  if self.overlay:self.overlay.setGeometry(round(305*self.width()/W),round(367*self.height()/H),round(895*self.width()/W),round(637*self.height()/H))
 def resizeEvent(self,event):
  super().resizeEvent(event);sx=self.width()/W;sy=self.height()/H
  for sp in self.spots:
   x,y,w,h=sp.box;sp.setGeometry(QRect(round(x*sx),round(y*sy),round(w*sx),round(h*sy)))
  self.position_panel()
 def paintEvent(self,event):
  p=QPainter(self);p.setRenderHint(QPainter.SmoothPixmapTransform);p.drawPixmap(self.rect(),self.pix)
  def note(x,y,w,h,txt,color='#e9edff'):
   r=QRect(round(x*self.width()/W),round(y*self.height()/H),round(w*self.width()/W),round(h*self.height()/H));p.setBrush(QColor(15,24,50,245));p.setPen(QPen(QColor('#7887e0'),1));p.drawRoundedRect(r,10,10);p.setPen(QColor(color));p.setFont(QFont('Sans Serif',12,QFont.Bold));p.drawText(r,Qt.AlignCenter,txt)
  note(485,152,300,42,'● اتصال نمایشی' if self.connected else '● اتصال قطع است','#73e4a3' if self.connected else '#ffa7b7')
  note(468,204,325,42,SERVERS[self.current]['name']+' — '+SERVERS[self.current]['city'])
  if not self.auto_connect:note(1371,858,138,38,'خاموش','#ffacba')
  if not self.auto_select:note(1371,944,138,38,'خاموش','#ffacba')

class Main(QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle('SmartProxy v0.7 — Interactive UI Preview (No VPN)');self.setCentralWidget(Dashboard());self.resize(W,H);self.setMinimumSize(1050,700)

if __name__=='__main__':
 app=QApplication(sys.argv);app.setLayoutDirection(Qt.LeftToRight);app.setStyle('Fusion');window=Main();window.show();sys.exit(app.exec())
