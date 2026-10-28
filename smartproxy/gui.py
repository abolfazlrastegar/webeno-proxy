"""Desktop shell for SmartProxy. Displays locally saved data; no fake live stats."""
import json
import subprocess
import sys
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QSystemTrayIcon, QMenu, QMessageBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from .cli import CONFIG, SOURCES
from .sources import load
from .core import parse_uri

class Worker(QThread):
    done = Signal(int, str)
    def __init__(self, *args):
        super().__init__()
        self.args = args
    def run(self):
        try:
            p = subprocess.run([sys.executable, '-m', 'smartproxy.cli', *self.args],
                               capture_output=True, text=True, timeout=120)
            self.done.emit(p.returncode, (p.stdout + '\n' + p.stderr).strip())
        except Exception as exc:
            self.done.emit(1, str(exc))

class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SmartProxy Linux · Preview 0.3')
        self.resize(760, 550)
        self.setStyleSheet('QWidget { font-size: 13px; } QPushButton { padding: 7px 12px; }'
                           'QTabWidget::pane { border: 1px solid palette(mid); }')
        root = QVBoxLayout(self)
        heading = QLabel('SmartProxy Linux')
        heading.setStyleSheet('font-size: 23px; font-weight: 700; margin: 5px 0;')
        root.addWidget(heading)
        self.status = QLabel('VPN status unknown')
        root.addWidget(self.status)
        buttons = QHBoxLayout()
        for label, cmd in [('▶ Start VPN','start'),('■ Stop VPN','stop'),('↻ Refresh sources','refresh'),('✓ Check config','check')]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, c=cmd: self.action(c))
            buttons.addWidget(btn)
        root.addLayout(buttons)
        source_row = QHBoxLayout()
        self.source = QLineEdit()
        self.source.setPlaceholderText('Paste personal HTTPS subscription or VLESS/VMess/Trojan/SS URI')
        source_row.addWidget(self.source)
        add = QPushButton('+ Add my config')
        add.clicked.connect(lambda: self.action('add'))
        source_row.addWidget(add)
        root.addLayout(source_row)
        self.tabs = QTabWidget()
        self.tables = []
        for name in ('All imported','Yamyam','My configs'):
            table = QTableWidget(0, 4)
            table.setHorizontalHeaderLabels(['Server','Protocol','Endpoint','Source / status'])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.tabs.addTab(table, name)
            self.tables.append(table)
        root.addWidget(self.tabs)
        self.note = QLabel('Yamyam website is a reference only until a working subscription URL is configured. '
                           'Ping and traffic counters are not implemented; no live values are shown.')
        self.note.setWordWrap(True)
        self.note.setStyleSheet('color: #888;')
        root.addWidget(self.note)
        icon_pix = QPixmap(32, 32)
        icon_pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(icon_pix)
        painter.setBrush(QColor('#3386ef'))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        painter.end()
        self.tray = QSystemTrayIcon(QIcon(icon_pix), self)
        menu = QMenu()
        menu.addAction('Open', self.showNormal)
        menu.addAction('Start', lambda: self.action('start'))
        menu.addAction('Stop', lambda: self.action('stop'))
        menu.addSeparator()
        menu.addAction('Quit', QApplication.instance().quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda r: self.showNormal() if r == QSystemTrayIcon.ActivationReason.Trigger else None)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        self.worker = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(5000)
        self.refresh_status()
        self.reload_tables()

    def reload_tables(self):
        for table in self.tables:
            table.setRowCount(0)
        try:
            sources = load(SOURCES)
            manual = [parse_uri(uri) for uri in sources.get('manual', [])]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            manual = []
            self.note.setText(f'Cannot read personal sources: {exc}')
        try:
            data = json.loads(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else {}
            imported = [x for x in data.get('outbounds', []) if x.get('type') in
                        ('vless','vmess','trojan','shadowsocks')]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            imported = []
            self.note.setText(f'Cannot read generated config: {exc}')
        for node in imported:
            self.append(0, node, 'Imported · origin not recorded')
        for node in manual:
            self.append(2, node, 'Personal · saved')
        # Source provenance is not stored for downloaded subscriptions. Never mislabel nodes as Yamyam.
        self.tabs.setTabText(0, f'All imported ({len(imported)})')
        self.tabs.setTabText(1, 'Yamyam (not configured)')
        self.tabs.setTabText(2, f'My configs ({len(manual)})')

    def append(self, idx, node, source):
        table = self.tables[idx]
        row = table.rowCount()
        table.insertRow(row)
        values = [node.get('tag','—'), node.get('type','—'),
                  f"{node.get('server','—')}:{node.get('server_port','—')}", source]
        for col, value in enumerate(values):
            table.setItem(row, col, QTableWidgetItem(str(value)))

    def refresh_status(self):
        try:
            p = subprocess.run(['systemctl','is-active','smartproxy.service'],
                               capture_output=True, text=True, timeout=3)
            self.status.setText('VPN: Service active (tunnel not independently verified)' if p.returncode == 0
                                else 'VPN: Disconnected / service inactive')
        except (OSError, subprocess.TimeoutExpired):
            self.status.setText('VPN: Cannot determine service state')

    def action(self, command):
        if self.worker and self.worker.isRunning():
            return
        if command == 'add':
            value = self.source.text().strip()
            if not value:
                QMessageBox.warning(self, 'Missing config', 'Paste a subscription URL or URI.')
                return
            args = ('add-uri' if value.startswith(('vless://','vmess://','trojan://','ss://')) else 'add', value)
        else:
            args = (command,)
        self.status.setText('Running ' + command + '…')
        self.worker = Worker(*args)
        self.worker.done.connect(self.completed)
        self.worker.start()

    def completed(self, code, output):
        self.refresh_status()
        self.reload_tables()
        if code or output:
            (QMessageBox.warning if code else QMessageBox.information)(self, 'SmartProxy', output or f'Exit code: {code}')

    def closeEvent(self, event):
        if self.tray.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = Main()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
