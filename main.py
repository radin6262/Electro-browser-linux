import sys
import os
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar, QLineEdit,
    QMenu, QToolButton, QDialog, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QHBoxLayout, QWidget, QLabel
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

# -------------------------------
# COOKIE MONITORING DIALOG
# -------------------------------
class CookieManager(QDialog):
    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cookie Manager")
        self.resize(600, 400)
        self.layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Domain", "Path"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        # Connect to the store and load existing cookies
        self.store = profile.cookieStore()
        self.store.cookieAdded.connect(self.add_cookie_to_table)
        self.store.loadAllCookies()

    def add_cookie_to_table(self, cookie):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(cookie.name().data().decode()))
        self.table.setItem(row, 1, QTableWidgetItem(cookie.domain()))
        self.table.setItem(row, 2, QTableWidgetItem(cookie.path()))

# -------------------------------
# RESOURCE HANDLER
# -------------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- COLORS ---
BG_DARK = "#0b0b10"
SURFACE = "#11111b"
OVERLAY = "#1e1e2e"
ACCENT = "#cba6f7"
TEXT = "#cdd6f4"

# -------------------------------
# BROWSER MAIN WINDOW
# -------------------------------
class ElectroBrowser(QMainWindow):
    def __init__(self, profile: QWebEngineProfile):
        super().__init__()
        self.profile = profile

        # --- CENTRAL WIDGET & MAIN LAYOUT ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- TOP HEADER ROW (Tabs + Plus Button + Nav Cluster) ---
        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(50)
        self.header_widget.setStyleSheet(f"background-color: {SURFACE};")
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(1)


        # 1. Tabs (Left Side)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabBar().setDrawBase(False)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        # 2. Plus Button (Right next to Tabs)
        self.plus_button = QToolButton()
        self.plus_button.setText("+")
        self.plus_button.clicked.connect(self.add_new_tab)
        # After creating plus_button
        self.plus_button.setAutoFillBackground(True)
        self.plus_button.setStyleSheet(f"""
            QToolButton {{
            background-color: {OVERLAY};
                color: skyblue;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 18px;
            }}
            QToolButton:hover {{
                background-color: {ACCENT};
                color: {BG_DARK};
            }}
            QToolButton:pressed {{
                background-color: {TEXT};
                color: {BG_DARK};
            }}
        """)


        # 3. Nav Cluster (Far Right: Refresh, Back, Forward, Menu)
        self.nav_cluster = QWidget()
        self.nav_cluster_layout = QHBoxLayout(self.nav_cluster)
        self.nav_cluster_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_cluster_layout.setSpacing(10)

        self.btn_refresh = self.create_nav_btn("↻", lambda: self.tabs.currentWidget().reload())
        self.btn_back = self.create_nav_btn("←", lambda: self.tabs.currentWidget().back())
        self.btn_forward = self.create_nav_btn("→", lambda: self.tabs.currentWidget().forward())
        
        self.menu_button = QToolButton()
        self.menu_button.setText("≡")
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.menu_button.setAutoFillBackground(True)
        self.menu_button.setStyleSheet(f"""
            QToolButton {{
                background-color: {OVERLAY};
                color: skyblue;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 18px;
                min-width: 36px;
                min-height: 36px;
            }}
            QToolButton:hover {{
                background-color: {ACCENT};
                color: {BG_DARK};
            }}
                QToolButton:pressed {{
                background-color: {TEXT};
                color: {BG_DARK};
            }}
        """)
        self.setup_menu()

        self.nav_cluster_layout.addWidget(self.btn_refresh)
        self.nav_cluster_layout.addWidget(self.btn_back)
        self.nav_cluster_layout.addWidget(self.btn_forward)
        self.nav_cluster_layout.addWidget(self.menu_button)

        self.header_layout.addWidget(self.tabs)
        self.header_layout.addWidget(self.plus_button)
        self.header_layout.addStretch() # This pushes the nav buttons to the right
        self.header_layout.addWidget(self.nav_cluster)
        for btn in [self.btn_refresh, self.btn_back, self.btn_forward, self.menu_button, self.plus_button]:
            btn.setFixedHeight(36)  # or 40
            btn.setFixedWidth(36)   # optional

        # --- ADDRESS BAR ROW (The "Frame" in your sketch) ---
        self.address_widget = QWidget()
        self.address_widget.setFixedHeight(50)
        self.address_widget.setStyleSheet(f"background-color: {SURFACE}; border-bottom: 1px solid {OVERLAY};")
        self.address_layout = QHBoxLayout(self.address_widget)

        self.web_icon = QLabel("") # Representing the "web box" icon in your sketch
        self.web_icon.setStyleSheet(f"color: {ACCENT}; font-size: 18px; padding-left: 10px;")

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or enter address")
        self.url_bar.returnPressed.connect(self.navigate_to_url)

        self.address_layout.addWidget(self.web_icon)
        self.address_layout.addWidget(self.url_bar)

        # --- CONTENT AREA (Web Box) ---
        # The QTabWidget also acts as the container for the browsers
        # We add the header and address bar above it.
        self.main_layout.addWidget(self.header_widget)
        self.main_layout.addWidget(self.address_widget)
        self.main_layout.addWidget(self.tabs)
        self.header_widget.setMinimumHeight(50)

        

        # Add the first tab
        self.add_new_tab()

        self.apply_styles()
        self.setWindowTitle("Electro Browser / Linux edition")
        self.resize(1280, 750)

    def create_nav_btn(self, text, slot):
        btn = QToolButton()
        btn.setText(text)
        btn.clicked.connect(slot)
        btn.setAutoFillBackground(True)
        btn.setStyleSheet(f"""
            QToolButton {{
                background-color: {OVERLAY};
                color: skyblue;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 18px;
                min-width: 36px;
                min-height: 36px;
            }}
            QToolButton:hover {{
                background-color: {ACCENT};
                color: {BG_DARK};
            }}
            QToolButton:pressed {{
                background-color: {TEXT};
                color: {BG_DARK};
            }}
        """)
        return btn

    def setup_menu(self):
        self.main_menu = QMenu(self)
        
        # cookie_manager_action = QAction("Manage Cookies", self)
        # cookie_manager_action.triggered.connect(self.show_cookie_manager)

        clear_cookies_action = QAction("Clear All Cookies", self)
        clear_cookies_action.triggered.connect(self.clear_all_cookies)

        # self.main_menu.addAction(cookie_manager_action)
        self.main_menu.addAction(clear_cookies_action)
        self.main_menu.addSeparator()
        self.main_menu.addAction("Exit", self.close)
        self.menu_button.setMenu(self.main_menu)

    def show_cookie_manager(self):
        self.manager = CookieManager(self.profile, self)
        self.manager.show()

    def clear_all_cookies(self):
        self.profile.cookieStore().deleteAllCookies()
        print("All cookies cleared.")

    def inject_anti_bot_js(self, page):
        page.runJavaScript("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

            window.chrome = {
                runtime: {},
            };

            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = (parameters) =>
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters);
        """)

    def add_new_tab(self, qurl=None):
        browser = QWebEngineView()
        page = QWebEnginePage(self.profile, browser)
        browser.setPage(page)
        page.loadFinished.connect(lambda _: self.inject_anti_bot_js(page))

        if not isinstance(qurl, QUrl):
            if isinstance(qurl, str):
                qurl = QUrl(qurl)
            else:
                path = resource_path("landing.html")
                if os.path.exists(path):
                    qurl = QUrl.fromLocalFile(path)
                else:
                    qurl = QUrl("https://www.google.com")

        browser.setUrl(qurl)

        index = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(index)
        browser.show()
        browser.setFocus()

        browser.urlChanged.connect(lambda q: self.update_url_bar(q, browser))
        browser.titleChanged.connect(
            lambda t: self.tabs.setTabText(self.tabs.indexOf(browser), t[:18])
        )

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if text.startswith(("http://", "https://")):
            url = QUrl(text)
        elif "." in text and " " not in text:
            url = QUrl("https://" + text)
        else:
            url = QUrl(f"https://www.google.com/search?q={text}")
        self.tabs.currentWidget().setUrl(url)

    def update_url_bar(self, q, browser):
        if browser == self.tabs.currentWidget():
            if q.isLocalFile():
                self.url_bar.clear()
            else:
                self.url_bar.setText(q.toString())

    def close_tab(self, index):
        # GET THE WIDGET FIRST
        widget = self.tabs.widget(index)
        
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
            # ACTUALLY DESTROY THE WIDGET
            if widget:
                widget.deleteLater()
        else:
            self.tabs.removeTab(index)
            # ACTUALLY DESTROY THE WIDGET
            if widget:
                widget.deleteLater()
            self.add_new_tab()

    def apply_styles(self):
        self.setStyleSheet(f"""
        QMainWindow {{ background-color: {BG_DARK}; }}

        /* Remove the border / white line from QTabWidget */
        QTabWidget::pane {{
            border: none;
            background: {BG_DARK};
            padding: 0px;
        }}

        /* Tabs style */
        QTabBar::tab {{
            background: #2F2F2F;
            color: {TEXT};
            padding: 10px 20px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 2px;
            border-bottom: 0px solid transparent; /* remove bottom line */
        }}

        QTabBar::tab:selected {{
            background: #454545;
            border-bottom: 0px solid transparent; /* remove bottom line */
        }}
        QTabBar::tab:hover {{
            background: #686868;
            border-bottom: 0px solid transparent; /* remove bottom line */
        }}

        QToolButton {{
            background-color: {OVERLAY};
            color: skyblue;
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 18px;
            min-width: 36px;
            min-height: 36px;
            max-height: 50px;
        }}

        QToolButton:hover {{
            background-color: {ACCENT};
            color: {BG_DARK};
        }}

        QToolButton:pressed {{
            background-color: {TEXT};
            color: {BG_DARK};
        }}

        QLineEdit {{
            background: {BG_DARK};
            color: {TEXT};
            border-radius: 12px;
            padding: 8px 18px;
            border: 1px solid {OVERLAY};
        }}

        QMenu {{
            background-color: {SURFACE};
            color: {TEXT};
            border: 1px solid {OVERLAY};
        }}
        QMenu::item:selected {{
            background-color: {ACCENT};
            color: {BG_DARK};
        }}
    """)



# -------------------------------
# APP ENTRY
# -------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    data = os.path.join(os.path.expanduser("~"), ".electro_browser_data")
    os.makedirs(data, exist_ok=True)

    profile = QWebEngineProfile("ElectroProfile", app)
    profile.setPersistentStoragePath(data)
    profile.setCachePath(os.path.join(data, "cache"))
    profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
    profile.settings().setAttribute(profile.settings().WebAttribute.LocalStorageEnabled, True)
    profile.setHttpUserAgent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )

    ElectroBrowser(profile).show()
    sys.exit(app.exec())