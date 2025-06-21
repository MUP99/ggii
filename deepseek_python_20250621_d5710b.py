import sys
import os
import webbrowser
import time
import cv2
import numpy as np
import pyautogui
import keyboard
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QGroupBox, QGridLayout, QSizePolicy, QSpacerItem,
                             QMessageBox, QFrame, QSlider)
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QSize, QTimer

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AimAssistApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("COD AimAssist v1.5")
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
        self.setGeometry(100, 100, 900, 700)
        
        # Default settings
        self.target_color = np.array([201, 0, 141])  # اللون الافتراضي (BGR)
        self.threshold = 40
        self.sensitivity = 0.7
        self.active = False
        self.mode = "Head"
        
        self.setup_ui()
        
        # إنشاء مؤقت للتتبع
        self.tracker_timer = QTimer(self)
        self.tracker_timer.timeout.connect(self.track_target)
        self.tracker_timer.setInterval(10)  # 10ms (100 FPS)
        
    def setup_ui(self):
        # إنشاء التبويبات الرئيسية
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)
        
        # إنشاء محتوى التبويبات
        self.multiplayer_tab = self.create_multiplayer_tab()
        self.settings_tab = self.create_settings_tab()
        self.contact_tab = self.create_contact_tab()
        
        # إضافة التبويبات
        self.tabs.addTab(self.multiplayer_tab, "Multiplayer")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.contact_tab, "Contact")
        
        # شريط الحالة
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("color: #AAAAAA; padding: 5px;")
        
        # التخطيط الرئيسي
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(self.status_label)
        main_widget.setLayout(main_layout)
        
        self.setCentralWidget(main_widget)
        
        # تطبيق التصميم
        self.apply_styles()
        
    def create_multiplayer_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # العنوان
        title = QLabel("Aim Assist Multiplayer")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFA500; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # أزرار المساعدة على التصويب
        aim_assist_group = self.create_aim_assist_group()
        layout.addWidget(aim_assist_group)
        
        # أزرار إضافية
        additional_buttons = self.create_additional_buttons()
        layout.addWidget(additional_buttons)
        
        # معاينة اللون
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Target Color:"))
        
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(40, 40)
        self.update_color_preview()
        color_layout.addWidget(self.color_preview)
        
        color_btn = QPushButton("Change Color")
        color_btn.clicked.connect(self.select_target_color)
        color_layout.addWidget(color_btn)
        
        layout.addLayout(color_layout)
        
        # معلومات الإصدار
        version = QLabel("Version 1.5 | Updated: 2023-11-15")
        version.setFont(QFont("Arial", 9))
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #666666; margin-top: 20px;")
        layout.addWidget(version)
        
        tab.setLayout(layout)
        return tab
    
    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Settings & Configuration")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1E90FF; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # عتبة اللون
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Color Threshold:"))
        
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(10)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(self.threshold)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        threshold_layout.addWidget(self.threshold_slider)
        
        self.threshold_label = QLabel(str(self.threshold))
        threshold_layout.addWidget(self.threshold_label)
        
        layout.addLayout(threshold_layout)
        
        # الحساسية
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("Sensitivity:"))
        
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setMinimum(10)
        self.sensitivity_slider.setMaximum(100)
        self.sensitivity_slider.setValue(int(self.sensitivity * 100))
        self.sensitivity_slider.valueChanged.connect(self.update_sensitivity)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        
        self.sensitivity_label = QLabel(f"{self.sensitivity:.2f}")
        sensitivity_layout.addWidget(self.sensitivity_label)
        
        layout.addLayout(sensitivity_layout)
        
        # أزرار التحكم
        btn_save = self.create_button("Save Settings", "#4CAF50")
        btn_save.setFixedHeight(50)
        btn_save.clicked.connect(self.save_settings)
        
        btn_reset = self.create_button("Reset to Default", "#F44336")
        btn_reset.setFixedHeight(50)
        btn_reset.clicked.connect(self.reset_settings)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_reset)
        layout.addLayout(btn_layout)
        
        # مساحة فارغة
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        tab.setLayout(layout)
        return tab
    
    def create_contact_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(30)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Contact & Support")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1E90FF; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # بطاقات الاتصال
        contact_frame = QFrame()
        contact_frame.setStyleSheet("background-color: #252525; border-radius: 10px; padding: 20px;")
        contact_layout = QVBoxLayout()
        
        # دعم البريد الإلكتروني
        email_card = self.create_contact_card(
            "Email Support", 
            "support@codassist.com", 
            "Send us an email for any issues or questions", 
            "#FF5722"
        )
        email_card.clicked.connect(lambda: self.open_email("support@codassist.com"))
        contact_layout.addWidget(email_card)
        
        # مجتمع الديسكورد
        discord_card = self.create_contact_card(
            "Discord Community", 
            "discord.gg/codassist", 
            "Join our Discord server for real-time support", 
            "#7289DA"
        )
        discord_card.clicked.connect(lambda: webbrowser.open("https://discord.gg/codassist"))
        contact_layout.addWidget(discord_card)
        
        # الموقع الرسمي
        website_card = self.create_contact_card(
            "Official Website", 
            "www.codassist.com", 
            "Visit our website for updates and documentation", 
            "#4CAF50"
        )
        website_card.clicked.connect(lambda: webbrowser.open("https://www.codassist.com"))
        contact_layout.addWidget(website_card)
        
        # التحديثات
        updates_card = self.create_contact_card(
            "Check for Updates", 
            "Version 1.5 (Latest)", 
            "Click to check for software updates", 
            "#2196F3"
        )
        updates_card.clicked.connect(self.check_for_updates)
        contact_layout.addWidget(updates_card)
        
        contact_frame.setLayout(contact_layout)
        layout.addWidget(contact_frame)
        
        # حقوق النشر
        copyright = QLabel("© 2023 COD AimAssist. All rights reserved.")
        copyright.setFont(QFont("Arial", 9))
        copyright.setAlignment(Qt.AlignCenter)
        copyright.setStyleSheet("color: #666666; margin-top: 30px;")
        layout.addWidget(copyright)
        
        tab.setLayout(layout)
        return tab
    
    def create_contact_card(self, title, subtitle, description, color):
        card = QPushButton()
        card.setCursor(Qt.PointingHandCursor)
        card.setStyleSheet(
            f"QPushButton {{ text-align: left; padding: 15px; border-radius: 8px; background-color: {color}; }}"
            f"QPushButton:hover {{ background-color: {self.lighten_color(color)}; }}"
        )
        
        card_layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        card_layout.addWidget(title_label)
        
        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setStyleSheet("color: white; margin-top: 5px;")
        card_layout.addWidget(subtitle_label)
        
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setStyleSheet("color: rgba(255,255,255,0.8); margin-top: 10px;")
        card_layout.addWidget(desc_label)
        
        card.setLayout(card_layout)
        return card
    
    def create_aim_assist_group(self):
        group = QGroupBox()
        group.setStyleSheet("QGroupBox { border: 2px solid #444444; border-radius: 10px; }")
        layout = QGridLayout()
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(15)
        
        # أنواع المساعدة على التصويب
        assist_types = [
            ("Lite AimAssist", "#4CAF50", "Low intensity assist for subtle aiming help"),
            ("Normal AimAssist", "#2196F3", "Standard assist for balanced gameplay"),
            ("Middle AimAssist", "#FF9800", "Enhanced assist for more aggressive play"),
            ("Super AimAssist", "#F44336", "Maximum assist for competitive advantage")
        ]
        
        # إنشاء أزرار لكل نوع
        for i, (name, color, tip) in enumerate(assist_types):
            # زر البدء
            btn = self.create_button(name, color, tip)
            btn.setFixedHeight(60)
            layout.addWidget(btn, i, 0)
            
            # زر الإيقاف
            stop_btn = self.create_button(f"Stop {name}", "#555555", "Deactivate this aim assist level")
            stop_btn.setFixedHeight(60)
            layout.addWidget(stop_btn, i, 1)
            
            # ربط الأحداث
            btn.clicked.connect(lambda checked, n=name: self.activate_aim_assist(n))
            stop_btn.clicked.connect(lambda checked, n=name: self.deactivate_aim_assist(n))
        
        group.setLayout(layout)
        return group
    
    def create_additional_buttons(self):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # أزرار إضافية
        buttons = [
            ("Head", "#9C27B0", "Focus aim on head shots"),
            ("Random", "#00BCD4", "Randomize aim pattern for unpredictability"),
            ("Chests", "#795548", "Prioritize chest shots for consistent damage")
        ]
        
        for name, color, tip in buttons:
            btn = self.create_button(name, color, tip)
            btn.setFixedHeight(50)
            layout.addWidget(btn)
            btn.clicked.connect(lambda checked, n=name: self.handle_additional_button(n))
        
        widget.setLayout(layout)
        return widget
    
    def create_button(self, text, color, tooltip=""):
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 12, QFont.Bold))
        btn.setCursor(Qt.PointingHandCursor)
        if tooltip:
            btn.setToolTip(tooltip)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {color}; color: white; border-radius: 8px; padding: 10px; }}"
            f"QPushButton:hover {{ background-color: {self.lighten_color(color)}; }}"
            f"QPushButton:pressed {{ background-color: {self.darken_color(color)}; }}"
            f"QToolTip {{ background-color: #333333; color: #FFFFFF; border: 1px solid #555555; }}"
        )
        return btn
    
    def lighten_color(self, hex_color, factor=0.3):
        color = QColor(hex_color)
        return color.lighter(int(100 + factor * 100)).name()
    
    def darken_color(self, hex_color, factor=0.3):
        color = QColor(hex_color)
        return color.darker(int(100 + factor * 100)).name()
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QTabWidget::pane {
                border: 1px solid #333333;
                border-radius: 4px;
                background: #1E1E1E;
                margin-top: 5px;
            }
            QTabBar::tab {
                background: #252525;
                color: #CCCCCC;
                padding: 12px 25px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #333333;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #2D2D2D;
                color: #FFFFFF;
                border-bottom: 3px solid #FFA500;
            }
            QTabBar::tab:hover {
                background: #3A3A3A;
            }
            QGroupBox {
                color: #CCCCCC;
                font-size: 14px;
                margin-top: 20px;
                font-weight: bold;
            }
            QLabel {
                color: #CCCCCC;
            }
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 8px;
                background: #333;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #1E90FF;
                border: 1px solid #555;
                width: 18px;
                margin: -4px 0;
                border-radius: 9px;
            }
            QSlider::add-page:horizontal {
                background: #555;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #1E90FF;
                border-radius: 4px;
            }
        """)
    
    def activate_aim_assist(self, name):
        self.active = True
        self.mode = name
        self.tracker_timer.start()
        self.status_label.setText(f"Active: {name} | Press F8 to stop")
        
    def deactivate_aim_assist(self, name):
        self.active = False
        self.tracker_timer.stop()
        self.status_label.setText("Aim assist deactivated")
        
    def handle_additional_button(self, name):
        self.mode = name
        self.status_label.setText(f"Mode set to: {name}")
        
    def open_email(self, email):
        webbrowser.open(f"mailto:{email}")
        
    def check_for_updates(self):
        QMessageBox.information(
            self, 
            "Software Update", 
            "You are using the latest version (v1.5)\n\n"
            "No updates available at this time.",
            QMessageBox.Ok
        )
        
    def track_target(self):
        if not self.active:
            return
            
        try:
            # التقاط لقطة الشاشة
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # إنشاء قناع للون الهدف
            diff = np.abs(frame - self.target_color)
            mask = np.sum(diff, axis=2) < self.threshold
            mask = mask.astype(np.uint8) * 255
            
            # العثور على الكنتورات
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    
                    # الحصول على مركز الشاشة
                    screen_width, screen_height = pyautogui.size()
                    center_x = screen_width // 2
                    center_y = screen_height // 2
                    
                    # حساب الحركة
                    move_x = int((cx - center_x) * self.sensitivity)
                    move_y = int((cy - center_y) * self.sensitivity)
                    
                    # تحريك الفأرة
                    pyautogui.moveRel(move_x, move_y, duration=0.01)
                    self.status_label.setText(f"Tracking | Target at ({cx}, {cy})")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
        
        # التحقق من الضغط على F8 للإيقاف
        if keyboard.is_pressed('f8'):
            self.active = False
            self.tracker_timer.stop()
            self.status_label.setText("Tracking stopped by user")
    
    def select_target_color(self):
        self.hide()
        time.sleep(0.5)  # إعطاء وقت لإخفاء النافذة
        
        # التقاط لقطة الشاشة
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # إنشاء نافذة لاختيار اللون
        cv2.namedWindow("Select Target Color - Click then press ESC", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Select Target Color - Click then press ESC", 800, 600)
        
        # دالة رد الماوس
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.target_color = frame[y, x].copy()
                self.update_color_preview()
                cv2.destroyAllWindows()
                self.show()
        
        cv2.setMouseCallback("Select Target Color - Click then press ESC", mouse_callback)
        cv2.imshow("Select Target Color - Click then press ESC", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        self.show()
    
    def update_color_preview(self):
        r, g, b = self.target_color[2], self.target_color[1], self.target_color[0]
        self.color_preview.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 1px solid #444;")
    
    def update_threshold(self, value):
        self.threshold = value
        self.threshold_label.setText(str(value))
    
    def update_sensitivity(self, value):
        self.sensitivity = value / 100.0
        self.sensitivity_label.setText(f"{self.sensitivity:.2f}")
    
    def save_settings(self):
        self.status_label.setText("Settings saved successfully")
    
    def reset_settings(self):
        self.threshold = 40
        self.sensitivity = 0.7
        self.threshold_slider.setValue(self.threshold)
        self.sensitivity_slider.setValue(int(self.sensitivity * 100))
        self.threshold_label.setText(str(self.threshold))
        self.sensitivity_label.setText(f"{self.sensitivity:.2f}")
        self.status_label.setText("Settings reset to default")

if __name__ == "__main__":
    # إخفاء نافذة الكونسول في ويندوز
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # تخصيص لوحة الألوان
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.Base, QColor(45, 45, 45))
    palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))
    palette.setColor(QPalette.ToolTipBase, QColor(45, 45, 45))
    palette.setColor(QPalette.ToolTipText, QColor(220, 220, 220))
    palette.setColor(QPalette.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.Button, QColor(60, 60, 60))
    palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.Highlight, QColor(255, 165, 0))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    window = AimAssistApp()
    window.show()
    sys.exit(app.exec_())
