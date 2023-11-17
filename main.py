from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, \
    QHBoxLayout, QVBoxLayout, QComboBox, QPlainTextEdit, QLabel, \
    QTextEdit, QPushButton, QCheckBox, QMenu, QGridLayout, QScrollArea, QSizePolicy
import sys
from selenium.common.exceptions import WebDriverException, NoSuchWindowException
from selenium.webdriver.chrome.options import Options
from PySide6.QtGui import QColor, QAction, QCloseEvent
from selenium import webdriver
from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QSvgWidget
import os
import win32clipboard as wincb
from ctypes import Structure, c_long, c_uint, c_int
from typing import List
import re

DEBUG = False

class POINT(Structure):
    _fields_ = [
        ("x", c_long),
        ("y", c_long)
    ]

class DROPFILES(Structure):
    _fields_ = [
        ("pFiles", c_uint), # 绝对路径开始的位置，单位为字节
        ("pt", POINT),      # 放手的位置点
        ("fNC", c_int),     # pt是否为客户端区域的相对坐标
        ("fWide", c_int)    # 文件是否包含Unicode字符
    ]

def createFileCopyClipboardData(filelist: List[str]) -> bytes:
    """文件复制剪贴板数据构造

    Args:
        filelist (List[str]): 要复制到剪贴板的绝对路径列表

    Returns:
        bytes: 剪贴板中的二进制数据
    """
    drop_struct = DROPFILES()
    drop_struct.pFiles = len(bytes(drop_struct))
    drop_struct.fWide = True

    # 末尾两个空字符，前一个作为最后一个路径的结尾，后一个作为整个路径列表的结尾
    filename_data = "\0".join(filelist) + "\0\0"
    # UTF16 小端序编码
    filename_data = filename_data.encode("utf-16le")

    return bytes(drop_struct) + filename_data

'''
# SvgWidget的右键菜单
        self.svg_context_menu = QMenu(self.svg_viewer)
        copy_svg = QAction("复制为svg", self.svg_context_menu)
        copy_svg.triggered.connect(self.copyAsSVG)
        self.svg_context_menu.addAction(copy_svg)
        self.svg_viewer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.svg_viewer.customContextMenuRequested.connect(self.svgContextMenuHandle)
'''

class SVGGridItem():
    def __init__(self, svg_text=None):
        self.svg_text = svg_text
        self.context_menu = QMenu()
        copy_act = QAction("复制为svg", self.context_menu)
        copy_act.triggered.connect(self.copyAsSVG)
        self.context_menu.addAction(copy_act)
        
        if svg_text is not None:
            self.svg_widget = QSvgWidget()
        else:
            self.svg_widget = None
        
    def show_context_menu(self, point):
        self.context_menu.exec(self.svg_widget.mapToGlobal(point))

    def render(self, svg_text: str) -> QSvgWidget | None:
        if svg_text is None:
            if self.svg_text is None:
                return None
        else:
            self.svg_text = svg_text
        self.svg_widget.load(self.svg_text.encode("utf-8"))
        self.svg_widget.setFixedHeight(60)
        # self.svg_widget.setMaximumHeight(80)
        self.svg_widget.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
        self.svg_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.svg_widget.customContextMenuRequested.connect(self.show_context_menu)
        return self.svg_widget

    def get_svg_src(self):
        return self.svg_text
    
    def copyAsSVG(self):
        svg_text = self.svg_text
        pattern = re.compile('^<svg.*width="[0-9]+.[0-9]+ex" height="[0-9]+.[0-9]+ex"')
        span = pattern.match(svg_text).span()
        seg = svg_text[span[0]:span[1]]
        seg = seg.replace("ex", "em")
        svg_text = seg + svg_text[span[1]:]
        svg_text = svg_text.encode("utf-8")
        wincb.OpenClipboard()
        fmt_id = wincb.RegisterClipboardFormat("image/svg+xml")
        wincb.EmptyClipboard()
        wincb.SetClipboardData(fmt_id, svg_text)
        wincb.CloseClipboard()
            


class BackgroudProcess():
    def __init__(self):
        """初始化后台的浏览器进程
        """
        
        self.back_driver = None

        self.options = {
            "Edge": webdriver.EdgeOptions(),
            "Chrome": webdriver.ChromeOptions(),
            "Firefox": webdriver.FirefoxOptions()
        }

        
        if not DEBUG:
            for opt in self.options.values():
                opt.add_argument("--headless")

    
    def is_alive(self) -> bool:
        """检查进程是否正常活动

        Returns:
            bool: 正常能使用返回True，无法使用则返回False
        """
        if self.back_driver is None or self.type is None:
            return False
        
        try:
            win_handles = self.back_driver.window_handles
            return True
        except WebDriverException:
            del self.back_driver
            self.back_driver = None
            return False
    
    def open(self, type: str):
        """打开后台broswer进程

        Raises:
            ValueError: type中为不支持的类型，type和back_driver都重置为None
        """
        self.type = type
        if self.type == "Edge":
            self.back_driver = webdriver.Edge(options=self.options['Edge'])
        elif self.type == "Chrome":
            self.back_driver = webdriver.Chrome(options=self.options['Chrome'])
        elif self.type == "Firefox":
            self.back_driver = webdriver.Firefox(options=self.options['Firefox'])
        else:
            self.type = None
            self.back_driver = None
            raise ValueError("Unsupported type argument.")
        self.back_driver.get(os.path.join(os.getcwd(), "test.html"))
    
    def close(self):
        """关闭后台浏览器进程
        """
        if self.is_alive():
            try:
                self.back_driver.quit()
            except Exception:
                del self.back_driver
            finally:
                self.back_driver = None
                self.type = None
        else:
            self.back_driver = None
            self.type = None
    
    def setTex(self, tex):
        input_area = self.back_driver.find_element("id", "inpt")
        self.back_driver.execute_script("document.getElementById('inpt').value=''")
        tex = tex.replace("\t", " ")
        input_area.send_keys(tex)

        self.back_driver.execute_script("convertLatex()")
    
    def getSvg(self):
        """返回当前的svg

        Returns:
            str: svg元素的outerHTML
        """
        svg_output = self.back_driver.find_element("tag name", "svg")
        defs_output = svg_output.find_element("tag name", "defs")
        # 判断LaTex渲染是否报错（点击确定是已确保LaTex不为空白）
        if len(defs_output.get_attribute("innerHTML")) == 0:
            return tuple([svg_output.text])
        
        return svg_output.get_attribute("outerHTML")



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tex Converter")
        self.back_driver = BackgroudProcess()

        # 总体为左右布局
        widget = QWidget()
        self.mainLayout = QHBoxLayout()
        self.leftLayout = QVBoxLayout()
        self.mainLayout.addLayout(self.leftLayout)
        widget.setLayout(self.mainLayout)
        self.setCentralWidget(widget)

        # 浏览器类型选择
        self.webdriver_type = QHBoxLayout()
        self.webdriver_type.addWidget(QLabel("选择浏览器"))
        self.leftLayout.addLayout(self.webdriver_type)
        browser_type = QComboBox()
        browser_type.addItems(['Chrome', 'Edge'])
        self.webdriver_type.addWidget(browser_type)

        # 操作按钮
        self.tool_bt_line = QHBoxLayout()
        self.leftLayout.addLayout(self.tool_bt_line)
        invoke_browser = QCheckBox("启动后台进程")
        invoke_browser.setCheckState(Qt.CheckState.Unchecked)
        check_browser = QPushButton("检查后台进程")
        check_browser.clicked.connect(self.checkBrowserHandle)
        self.tool_bt_line.addWidget(invoke_browser)
        self.tool_bt_line.addWidget(check_browser)
        invoke_browser.stateChanged.connect(self.toggleBrowserHandle)

        # “仅渲染当前LaTeX”复选框
        self.show_current_tex_only = QCheckBox("仅渲染当前LaTeX")
        self.show_current_tex_only.setCheckState(Qt.CheckState.Unchecked)
        self.leftLayout.addWidget(self.show_current_tex_only)

        # Latex输入区域
        self.input_field = QVBoxLayout()
        self.leftLayout.addLayout(self.input_field)
        self.input_field.addWidget(QLabel("Latex公式："))
        self.input_field.addWidget(QPlainTextEdit())
        
        confirm_button = QPushButton("确认")
        confirm_button.clicked.connect(self.convertButtonHandle)
        self.input_field.addWidget(confirm_button)

        # 日志显示
        self.console_field = QVBoxLayout()
        self.leftLayout.addLayout(self.console_field)
        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        self.console_field.addWidget(self.console_log)
        
        # 右侧界面为SVG的结果展示
        self.svg_container = QWidget()
        # self.svg_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.display_area = QScrollArea()
        self.display_area.setFixedWidth(300)
        self.display_area.setWidget(self.svg_container)
        self.display_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.display_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.display_area.setWidgetResizable(True)
        self.mainLayout.addWidget(self.display_area)

        # 存放svgitem
        self.svgitem_list = []
        
        # 一列纵向布局svg
        self.svg_vbox = QVBoxLayout()
        self.svg_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.svg_container.setLayout(self.svg_vbox)


        # self.svg_viewer.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.svg_viewer.customContextMenuRequested.connect(self.svgContextMenuHandle)
        # self.console_field.addWidget(self.svg_viewer)
    
    def closeEvent(self, event: QCloseEvent) -> None:
        self.back_driver.close()
        return super().closeEvent(event)
    
    def svgContextMenuHandle(self, point):
        self.svg_context_menu.exec(self.svg_viewer.mapToGlobal(point))
    
    def copyAsSVG(self):
        svg_text = self.back_driver.getSvg()
        pattern = re.compile('^<svg.*width="[0-9]+.[0-9]+ex" height="[0-9]+.[0-9]+ex"')
        span = pattern.match(svg_text).span()
        seg = svg_text[span[0]:span[1]]
        seg = seg.replace("ex", "em")
        svg_text = seg + svg_text[span[1]:]
        svg_text = svg_text.encode("utf-8")
        wincb.OpenClipboard()
        fmt_id = wincb.RegisterClipboardFormat("image/svg+xml")
        wincb.EmptyClipboard()
        wincb.SetClipboardData(fmt_id, svg_text)
        wincb.CloseClipboard()
    
    
    def convertButtonHandle(self):
        if not self.back_driver.is_alive():
            self.console_log.append("\n后台进程还未开启，请先开启！")
            return

        latex_text = self.input_field.itemAt(1).widget().toPlainText().strip()
        if len(latex_text) == 0:
            self.console_log.append("\n输入的LaTex不能为空白")
            return

        self.back_driver.setTex(latex_text)
        
        # LaTex错误，提示错误信息
        data = self.back_driver.getSvg()
        if isinstance(data, tuple):
            self.console_log.append("\nLaTex输入错误：{}".format(data[0]))
            return

        svg_img = SVGGridItem(data)
        self.svgitem_list.append(svg_img)

        if self.show_current_tex_only.checkState() == Qt.CheckState.Checked:  # 检查是否勾选“仅渲染当前LaTex”
            for i in reversed(range(self.svg_vbox.count())):  # 清除已有的Svg
                widget = self.svg_vbox.itemAt(i).widget()
                widget.setParent(None)
                widget.deleteLater()
        self.svg_vbox.addWidget(svg_img.render(None))


    def checkBrowserHandle(self):
        if self.back_driver.is_alive():
            self.console_log.append("\n后台进程正常")
        else:
            self.console_log.append("\n后台进程异常，需要重启")

    def toggleBrowserHandle(self, cur_state):
        """启动或关闭浏览器进程
        """
        select_browser = self.webdriver_type.itemAt(1).widget().currentText()
        if cur_state == 0:
            if self.back_driver.is_alive():
                self.back_driver.close()
        elif cur_state == 2:
            if not self.back_driver.is_alive():
                self.back_driver.open(select_browser)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()