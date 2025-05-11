from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QListWidget, QComboBox, QProgressBar,
                           QMessageBox, QLabel, QListWidgetItem, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
# from core.usb_handler import USBHandler # 旧的导入方式 (这是导致错误的行)
from src.core.usb_handler import USBHandler # 新的导入方式
import os
import shutil
import tempfile
import re # <-- 添加导入 re 模块

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.usb_handler = USBHandler()
        self.setWindowTitle("U盘音乐文件排序工具")
        self.setMinimumSize(800, 600)
        self.supported_extensions = ('.mp3', '.wav', '.flac', '.m4a', '.wma',
                                   '.mp4', '.avi', '.mkv', '.mov', '.wmv',
                                   '.3gp', '.flv', '.webm', '.rmvb', '.m4v')
        # self.temp_dir = os.path.join(os.path.expanduser("~"), "UdiskMusicReOrder_temp") # <-- 移除这一行
        self.setup_ui()

    def setup_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # U盘选择区域
        usb_layout = QHBoxLayout()
        usb_label = QLabel("选择U盘：")
        self.usb_combo = QComboBox()
        self.refresh_btn = QPushButton("刷新")
        usb_layout.addWidget(usb_label)
        usb_layout.addWidget(self.usb_combo)
        usb_layout.addWidget(self.refresh_btn)
        layout.addLayout(usb_layout)

        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        layout.addWidget(self.file_list)

        # 操作按钮区域
        button_layout = QHBoxLayout()
        self.load_btn = QPushButton("加载文件")
        self.sort_by_prefix_btn = QPushButton("按序号排序") # <-- 新增按钮
        self.save_btn = QPushButton("保存排序")
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.sort_by_prefix_btn) # <-- 添加按钮到布局
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

        # 进度文本标签 (确保这个标签在您的 setup_ui 中，根据您之前的请求添加)
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 连接信号
        self.refresh_btn.clicked.connect(self.refresh_usb_devices)
        self.load_btn.clicked.connect(self.load_files)
        self.sort_by_prefix_btn.clicked.connect(self.sort_files_by_prefix) # <-- 连接新按钮的信号
        self.save_btn.clicked.connect(self.save_files)

    def refresh_usb_devices(self):
        """刷新U盘设备列表"""
        self.usb_combo.clear()
        drives = self.usb_handler.get_usb_drives()
        
        if not drives:
            self.usb_combo.addItem("未检测到U盘")
            self.load_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            return
        
        for drive in drives:
            self.usb_combo.addItem(f"{drive['name']} ({drive['letter']})", drive['letter'])
        
        self.load_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

    def load_files(self):
        """加载U盘中的文件"""
        if self.usb_combo.currentData() is None:
            QMessageBox.warning(self, "警告", "请先选择U盘！")
            return
            
        drive_path = self.usb_combo.currentData()
        self.file_list.clear()
        
        try:
            # 遍历U盘中的所有文件
            for root, _, files in os.walk(drive_path):
                for file in files:
                    if file.lower().endswith(self.supported_extensions):
                        full_path = os.path.join(root, file)
                        # 获取文件大小（以MB为单位）
                        size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        # 创建列表项
                        item = QListWidgetItem()
                        item.setText(f"{file} ({size_mb:.2f}MB)") # Corrected this line
                        item.setData(Qt.ItemDataRole.UserRole, full_path)
                        self.file_list.addItem(item)
            
            if self.file_list.count() == 0:
                QMessageBox.information(self, "提示", "未找到支持的音频文件！")
            else:
                QMessageBox.information(self, "成功", f"已加载 {self.file_list.count()} 个音频文件")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载文件失败：{str(e)}")

    def sort_files_by_prefix(self):
        """根据文件名前缀的数字对列表中的文件进行排序"""
        if self.file_list.count() == 0:
            QMessageBox.information(self, "提示", "列表中没有文件可排序。")
            return

        items_to_sort = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            text = item.text()
            data = item.data(Qt.ItemDataRole.UserRole) # 保存原始数据

            # 尝试提取前缀数字
            # 正则表达式匹配开头的数字，后面可能跟有点、空格、短横线等
            match = re.match(r"^\s*(\d+)\s*[\.\-]?\s*", text)
            prefix_num = float('inf') # 默认为无穷大，无前缀的排在最后
            if match:
                try:
                    prefix_num = int(match.group(1))
                except ValueError:
                    pass # 如果转换失败，保持为无穷大
            
            items_to_sort.append({'prefix': prefix_num, 'text': text, 'data': data, 'original_item': item})

        # 根据前缀数字排序
        items_to_sort.sort(key=lambda x: x['prefix'])

        # 清空并重新填充列表
        self.file_list.clear()
        for sorted_item_info in items_to_sort:
            new_item = QListWidgetItem()
            new_item.setText(sorted_item_info['text'])
            new_item.setData(Qt.ItemDataRole.UserRole, sorted_item_info['data'])
            self.file_list.addItem(new_item)
        
        QMessageBox.information(self, "完成", "文件已按前缀序号排序。")

    def save_files(self):
        """保存排序后的文件"""
        if self.usb_combo.currentData() is None:
            QMessageBox.warning(self, "警告", "请先选择U盘！")
            return
            
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "警告", "没有可保存的文件！")
            return

        drive = self.usb_combo.currentData()
        reply = QMessageBox.question(self, "确认操作", 
                                   f"即将开始文件排序过程，目标U盘: {drive}\n"
                                   "此操作包含格式化U盘步骤，请确保已备份重要数据。\n\n是否继续？",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return

        current_temp_dir = None # 初始化变量
        try:
            # 动态创建临时文件夹
            current_temp_dir = tempfile.mkdtemp(prefix="UdiskMusicReOrder_")
            
            self.progress_label.setText(f"准备临时目录: {current_temp_dir}")
            self.progress_label.setVisible(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            # 注意：这里不需要手动创建 current_temp_dir，mkdtemp 已经创建了
            # if os.path.exists(current_temp_dir): # mkdtemp 保证了它不存在或已创建
            #     shutil.rmtree(current_temp_dir)
            # os.makedirs(current_temp_dir) # mkdtemp 已经创建

            self.progress_label.setText("正在收集文件信息...")
            QApplication.processEvents()

            files_to_copy = []
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                original_path = item.data(Qt.ItemDataRole.UserRole)
                filename = os.path.basename(original_path)

                # 尝试移除旧的数字前缀
                # 正则表达式匹配开头的数字，后面跟着点、短横线等，然后是实际的文件名部分
                match = re.match(r"^\s*(\d+)\s*[\.\-]\s*(.*)", filename)
                cleaned_filename = filename
                if match:
                    # 如果匹配成功，group(2) 包含的是数字前缀之后的部分
                    cleaned_filename = match.group(2).strip() 
                
                # 如果移除前缀后文件名变为空（例如，文件名就是 "123. "），则保留原始文件名以避免错误
                if not cleaned_filename:
                    cleaned_filename = filename

                new_name = f"{i+1:03d}. {cleaned_filename}"
                temp_path = os.path.join(current_temp_dir, new_name) # 使用 current_temp_dir
                files_to_copy.append({'src': original_path, 'tmp_dst': temp_path, 'final_name': new_name})

            total_files = len(files_to_copy)
            if total_files == 0:
                QMessageBox.information(self, "提示", "没有有效文件被选中进行处理。")
                self.progress_label.setVisible(False)
                self.progress_bar.setVisible(False)
                if current_temp_dir and os.path.exists(current_temp_dir): # 清理已创建的临时目录
                    shutil.rmtree(current_temp_dir)
                return

            self.progress_label.setText("开始复制文件到临时区域...")
            QApplication.processEvents()
            for i, file_info in enumerate(files_to_copy, 1):
                self.progress_label.setText(f"复制到临时目录 ({i}/{total_files}): {os.path.basename(file_info['src'])}")
                QApplication.processEvents()
                shutil.copy2(file_info['src'], file_info['tmp_dst'])
                self.progress_bar.setValue(int(i / total_files * 40))

            self.progress_label.setText("正在验证临时文件...")
            QApplication.processEvents()
            self.progress_bar.setValue(45)

            # First, update the progress label's text
            self.progress_label.setText(f"已成功将 {total_files} 个文件备份到临时区域。等待确认格式化...")
            QApplication.processEvents() # Ensure UI updates

            # Then, show the confirmation dialog
            reply_format = QMessageBox.question(self, "确认格式化", 
                                       f"已成功将 {total_files} 个文件备份到临时区域 ({current_temp_dir})。\n\n即将格式化U盘: {drive}\n\n此操作将删除U盘上所有现有数据且不可恢复，是否继续？",
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No)
            
            if reply_format == QMessageBox.StandardButton.No:
                self.progress_label.setText("操作已取消。正在清理临时文件...")
                QApplication.processEvents()
                # current_temp_dir 在这里肯定有值且存在
                shutil.rmtree(current_temp_dir)
                current_temp_dir = None # 标记为已清理
                self.progress_label.setVisible(False)
                self.progress_bar.setVisible(False)
                QMessageBox.information(self, "取消", "操作已取消，临时文件已清理。")
                return

            self.progress_label.setText(f"准备格式化U盘: {drive}...")
            QApplication.processEvents()

            # 尝试引导用户进行系统格式化
            # 假设 self.usb_handler.format_drive(drive) 会尝试打开相关系统界面
            # 并返回 True 如果尝试成功, False 如果尝试失败 (例如无法执行命令)
            format_action_initiated = self.usb_handler.format_drive(drive)

            if format_action_initiated:
                QMessageBox.information(self, "格式化U盘",
                                       f"已尝试为U盘 {drive} 打开系统格式化相关界面。\n\n"
                                       "请在该界面中手动完成U盘的格式化操作。\n"
                                       "(通常是右键点击U盘 -> 选择 '格式化...' -> 设置选项 -> 开始格式化)。\n\n"
                                       "格式化完成后，请点击本对话框的“确定”按钮以继续复制文件。",
                                       QMessageBox.StandardButton.Ok)
            else:
                QMessageBox.warning(self, "格式化U盘",
                                     f"无法自动打开U盘 {drive} 的系统格式化相关界面。\n\n"
                                     "请手动打开 '此电脑' (或 '我的电脑')，找到U盘驱动器 ({drive})，"
                                     "然后右键点击并选择 '格式化...'。\n"
                                     "请在系统界面中完成格式化操作。\n\n"
                                     "格式化完成后，请点击本对话框的“确定”按钮以继续复制文件。",
                                     QMessageBox.StandardButton.Ok)
            
            # 用户点击“确定”后，我们假定格式化已完成
            self.progress_label.setText(f"U盘 {drive} 格式化操作已由用户确认。")
            QApplication.processEvents()
            self.progress_bar.setValue(50) # 更新进度条，表示格式化阶段（用户确认）完成

            self.progress_label.setText("开始从临时区域复制文件到U盘...")
            QApplication.processEvents()
            for i, file_info in enumerate(files_to_copy, 1):
                final_dst_on_usb = os.path.join(drive, file_info['final_name'])
                self.progress_label.setText(f"复制到U盘 ({i}/{total_files}): {file_info['final_name']}")
                QApplication.processEvents()
                shutil.copy2(file_info['tmp_dst'], final_dst_on_usb)
                self.progress_bar.setValue(50 + int(i / total_files * 40))
            
            self.progress_label.setText("正在验证U盘上的文件...")
            QApplication.processEvents()
            self.progress_bar.setValue(95)

            self.progress_label.setText("正在清理临时文件...")
            QApplication.processEvents()
            shutil.rmtree(current_temp_dir) # 清理临时目录
            current_temp_dir = None # 标记为已清理
            self.progress_bar.setValue(100)
            
            self.progress_label.setVisible(False)
            self.progress_bar.setVisible(False)
            QMessageBox.information(self, "成功", "文件排序并复制到U盘完成！")

        except Exception as e:
            self.progress_label.setText(f"错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存文件失败：{str(e)}")
            if current_temp_dir and os.path.exists(current_temp_dir): # 确保在异常时也尝试清理
                try:
                    shutil.rmtree(current_temp_dir)
                    self.progress_label.setText(f"错误: {str(e)}. 临时文件已清理。")
                    current_temp_dir = None
                except Exception as cleanup_e:
                    self.progress_label.setText(f"错误: {str(e)}. 清理临时文件失败: {cleanup_e}")
        finally:
            # 再次确保，如果 current_temp_dir 仍然存在（例如在 except 块中清理失败）
            if current_temp_dir and os.path.exists(current_temp_dir):
                 try:
                     shutil.rmtree(current_temp_dir)
                 except Exception:
                     # 在 finally 块中最好不要再抛出新异常
                     print(f"Failed to cleanup temp directory in finally block: {current_temp_dir}")
            QApplication.processEvents()