import sys
import os # 新增导入 os 模块

# 将项目根目录添加到 sys.path
# __file__ 指向当前文件 (d:\小项目app\音乐排序\UdiskMusicReOrder\src\main.py)
# os.path.dirname(__file__) 是 src 目录
# os.path.dirname(os.path.dirname(__file__)) 是项目根目录 UdiskMusicReOrder
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtWidgets import QApplication
# from ui.main_window import MainWindow # 旧的导入方式
from src.ui.main_window import MainWindow # 新的导入方式

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()