from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QListWidget, QComboBox, QProgressBar,
                           QMessageBox, QLabel, QListWidgetItem, QApplication,
                           QSplitter, QFileDialog, QTextEdit, QGroupBox)  # 添加新的导入
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.core.usb_handler import USBHandler
import os
import shutil
import tempfile
import re
import subprocess  # 添加subprocess导入

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.usb_handler = USBHandler()
        self.setWindowTitle("U盘音乐文件排序工具")
        self.setMinimumSize(1200, 600)  # 增加窗口宽度以容纳右侧面板
        self.supported_extensions = ('.mp3', '.wav', '.flac', '.m4a', '.wma',
                                   '.mp4', '.avi', '.mkv', '.mov', '.wmv',
                                   '.3gp', '.flv', '.webm', '.rmvb', '.m4v')
        self.backup_dir = "D:\\temp"  # 默认备份目录
        self.setup_ui()

    def setup_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主分割器（左右分割）
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(main_splitter)
        
        # 左侧面板
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # U盘选择区域
        usb_layout = QHBoxLayout()
        usb_label = QLabel("选择U盘：")
        self.usb_combo = QComboBox()
        self.refresh_btn = QPushButton("刷新")
        usb_layout.addWidget(usb_label)
        usb_layout.addWidget(self.usb_combo)
        usb_layout.addWidget(self.refresh_btn)
        left_layout.addLayout(usb_layout)

        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        # 连接拖拽完成信号
        self.file_list.model().rowsMoved.connect(self.update_line_numbers)
        left_layout.addWidget(self.file_list)

        # 操作按钮区域
        button_layout = QHBoxLayout()
        self.load_btn = QPushButton("加载文件")
        self.sort_by_prefix_btn = QPushButton("按序号排序")
        self.rename_by_line_btn = QPushButton("按行号重命名")  # 新增按钮
        self.save_btn = QPushButton("保存排序")
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.sort_by_prefix_btn)
        button_layout.addWidget(self.rename_by_line_btn)  # 添加新按钮
        button_layout.addWidget(self.save_btn)
        left_layout.addLayout(button_layout)

        # 进度文本标签
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        left_layout.addWidget(self.progress_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # 右侧面板 - 备份文件列表
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 备份目录组
        backup_group = QGroupBox("备份文件目录")
        backup_layout = QVBoxLayout(backup_group)
        
        # 备份目录选择
        backup_dir_layout = QHBoxLayout()
        backup_dir_layout.addWidget(QLabel("备份目录："))
        self.backup_dir_label = QLabel(self.backup_dir)
        self.backup_dir_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
        self.choose_backup_dir_btn = QPushButton("选择目录")
        backup_dir_layout.addWidget(self.backup_dir_label)
        backup_dir_layout.addWidget(self.choose_backup_dir_btn)
        backup_layout.addLayout(backup_dir_layout)
        
        # 备份文件列表
        backup_layout.addWidget(QLabel("备份文件列表（只读）："))
        self.backup_file_list = QTextEdit()
        self.backup_file_list.setReadOnly(True)
        self.backup_file_list.setMaximumHeight(400)
        backup_layout.addWidget(self.backup_file_list)
        
        # 刷新备份列表按钮
        self.refresh_backup_btn = QPushButton("刷新备份列表")
        backup_layout.addWidget(self.refresh_backup_btn)
        
        right_layout.addWidget(backup_group)
        right_layout.addStretch()  # 添加弹性空间
        
        # 将左右面板添加到分割器
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([800, 400])  # 设置初始大小比例

        # 连接信号
        self.refresh_btn.clicked.connect(self.refresh_usb_devices)
        self.load_btn.clicked.connect(self.load_files)
        self.sort_by_prefix_btn.clicked.connect(self.sort_files_by_prefix)
        self.rename_by_line_btn.clicked.connect(self.rename_files_by_line_number)  # 连接新按钮
        self.save_btn.clicked.connect(self.save_files)
        self.choose_backup_dir_btn.clicked.connect(self.choose_backup_directory)
        self.refresh_backup_btn.clicked.connect(self.refresh_backup_file_list)
        # 连接U盘选择变化信号，实现自动加载文件列表
        self.usb_combo.currentTextChanged.connect(self.on_usb_selection_changed)
        
        # 初始化备份文件列表
        self.refresh_backup_file_list()
        
        # 初始化U盘设备列表
        self.refresh_usb_devices()

    def choose_backup_directory(self):
        """选择备份目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择备份目录", self.backup_dir)
        if directory:
            self.backup_dir = directory
            self.backup_dir_label.setText(self.backup_dir)
            self.refresh_backup_file_list()

    def refresh_backup_file_list(self):
        """刷新备份文件列表"""
        self.backup_file_list.clear()
        
        if not os.path.exists(self.backup_dir):
            self.backup_file_list.setText(f"备份目录不存在：{self.backup_dir}\n\n点击'选择目录'按钮选择或创建备份目录。")
            return
        
        try:
            files = os.listdir(self.backup_dir)
            if not files:
                self.backup_file_list.setText("备份目录为空")
                return
            
            file_info_list = []
            for file in files:
                file_path = os.path.join(self.backup_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    size_mb = size / (1024 * 1024)
                    modified_time = os.path.getmtime(file_path)
                    import time
                    modified_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modified_time))
                    file_info_list.append(f"{file} ({size_mb:.2f}MB) - {modified_str}")
            
            if file_info_list:
                self.backup_file_list.setText("\n".join(file_info_list))
            else:
                self.backup_file_list.setText("备份目录中没有文件")
                
        except Exception as e:
            self.backup_file_list.setText(f"读取备份目录失败：{str(e)}")

    def refresh_usb_devices(self):
        """刷新U盘设备列表"""
        self.usb_combo.clear()
        drives = self.usb_handler.get_usb_drives()
        
        if not drives:
            self.usb_combo.addItem("未检测到U盘")
            self.load_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            # 清空文件列表
            self.file_list.clear()
            return
        
        for drive in drives:
            self.usb_combo.addItem(f"{drive['name']} ({drive['letter']})", drive['letter'])
        
        self.load_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        # 如果有U盘，自动选择第一个并加载文件
        if drives:
            self.usb_combo.setCurrentIndex(0)
            # currentTextChanged信号会自动触发，无需手动调用load_files()

    def on_usb_selection_changed(self):
        """当U盘选择发生变化时自动加载文件列表"""
        # 检查是否有有效的U盘选择
        if (self.usb_combo.currentData() is not None and 
            self.usb_combo.currentText() != "未检测到U盘"):
            # 自动加载文件列表
            self.load_files()

    def update_line_numbers(self):
        """更新文件列表的行号显示（3位数字格式）"""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            original_text = item.data(Qt.ItemDataRole.UserRole + 1)  # 存储原始文件名
            if original_text is None:
                # 如果没有存储原始文件名，从当前文本中提取
                current_text = item.text()
                # 移除行号前缀（支持3位数字格式）
                match = re.match(r'^\d{3}\. (.+)', current_text)
                if match:
                    original_text = match.group(1)
                else:
                    original_text = current_text
                item.setData(Qt.ItemDataRole.UserRole + 1, original_text)
            
            # 更新显示文本，添加3位数字行号
            new_text = f"{i + 1:03d}. {original_text}"
            item.setText(new_text)
            
            # 检查按行号排序是否会改变当前行的位置
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                file_name = os.path.basename(file_path)
                # 提取文件名中的数字前缀
                match = re.match(r'^\s*(\d+)\s*[\.-]?\s*', file_name)
                if match:
                    try:
                        file_prefix = int(match.group(1))
                        current_line_number = i + 1
                        # 如果文件前缀与当前行号不同，标记为不同颜色
                        if file_prefix != current_line_number:
                            item.setBackground(Qt.GlobalColor.yellow)  # 黄色背景表示会改变位置
                        else:
                            item.setBackground(Qt.GlobalColor.white)   # 白色背景表示位置不变
                    except ValueError:
                        item.setBackground(Qt.GlobalColor.lightGray)  # 灰色背景表示无法解析前缀
                else:
                    item.setBackground(Qt.GlobalColor.lightGray)  # 灰色背景表示没有数字前缀
            else:
                item.setBackground(Qt.GlobalColor.white)

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
                        
                        # 存储原始文件名（不含行号）
                        original_display = f"{file} ({size_mb:.2f}MB)"
                        item.setData(Qt.ItemDataRole.UserRole + 1, original_display)
                        
                        # 存储文件完整路径
                        item.setData(Qt.ItemDataRole.UserRole, full_path)
                        
                        self.file_list.addItem(item)
            
            # 更新行号显示
            self.update_line_numbers()
            
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
            original_text = item.data(Qt.ItemDataRole.UserRole + 1)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            
            # 从原始文件名中提取文件名部分（去掉大小写信息）
            file_name = os.path.basename(file_path)
            
            # 尝试提取前缀数字
            match = re.match(r'^\s*(\d+)\s*[\.\-]?\s*', file_name)
            prefix_num = float('inf')  # 默认为无穷大，无前缀的排在最后
            if match:
                try:
                    prefix_num = int(match.group(1))
                except ValueError:
                    pass
            
            items_to_sort.append({
                'prefix': prefix_num, 
                'original_text': original_text, 
                'file_path': file_path
            })

        # 根据前缀数字排序
        items_to_sort.sort(key=lambda x: x['prefix'])

        # 清空并重新填充列表
        self.file_list.clear()
        for sorted_item_info in items_to_sort:
            new_item = QListWidgetItem()
            new_item.setData(Qt.ItemDataRole.UserRole + 1, sorted_item_info['original_text'])
            new_item.setData(Qt.ItemDataRole.UserRole, sorted_item_info['file_path'])
            self.file_list.addItem(new_item)
        
        # 更新行号显示
        self.update_line_numbers()
        
        QMessageBox.information(self, "完成", "文件已按前缀序号排序。")

    def rename_files_by_line_number(self):
        """按照行号重新命名U盘中的文件"""
        if self.usb_combo.currentData() is None:
            QMessageBox.warning(self, "警告", "请先选择U盘！")
            return
            
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "警告", "没有可重命名的文件！")
            return

        reply = QMessageBox.question(self, "确认重命名", 
                                   "此操作将直接重命名U盘中的文件，按照当前列表的行号顺序。\n\n"
                                   "• 已有序号的文件将更新序号\n"
                                   "• 没有序号的文件将添加序号\n\n"
                                   "建议在操作前备份重要文件。是否继续？",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return

        try:
            self.progress_label.setText("正在重命名文件...")
            self.progress_label.setVisible(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            renamed_count = 0
            total_files = self.file_list.count()
            
            # 收集重命名操作
            rename_operations = []
            
            for i in range(total_files):
                item = self.file_list.item(i)
                original_path = item.data(Qt.ItemDataRole.UserRole)
                original_filename = os.path.basename(original_path)
                directory = os.path.dirname(original_path)
                
                # 移除现有的数字前缀
                match = re.match(r'^\s*(\d+)\s*[\.\-]\s*(.*)', original_filename)
                if match:
                    clean_filename = match.group(2).strip()
                else:
                    clean_filename = original_filename
                
                # 如果清理后文件名为空，保留原文件名
                if not clean_filename:
                    clean_filename = original_filename
                
                # 生成新的文件名（3位数字前缀）
                new_filename = f"{i + 1:03d}. {clean_filename}"
                new_path = os.path.join(directory, new_filename)
                
                # 如果新文件名与原文件名不同，添加到重命名操作列表
                if original_path != new_path:
                    rename_operations.append((original_path, new_path, new_filename))
            
            # 执行重命名操作
            for j, (old_path, new_path, new_filename) in enumerate(rename_operations):
                try:
                    self.progress_label.setText(f"重命名文件 ({j + 1}/{len(rename_operations)}): {os.path.basename(old_path)}")
                    QApplication.processEvents()
                    
                    # 检查目标文件是否已存在
                    if os.path.exists(new_path) and old_path != new_path:
                        # 如果目标文件存在，先重命名为临时文件名
                        temp_path = new_path + ".tmp_rename"
                        os.rename(old_path, temp_path)
                        os.rename(temp_path, new_path)
                    else:
                        os.rename(old_path, new_path)
                    
                    renamed_count += 1
                    
                    # 更新列表项的路径信息
                    for k in range(self.file_list.count()):
                        list_item = self.file_list.item(k)
                        if list_item.data(Qt.ItemDataRole.UserRole) == old_path:
                            list_item.setData(Qt.ItemDataRole.UserRole, new_path)
                            # 更新显示的原始文本（包含文件大小）
                            size_mb = os.path.getsize(new_path) / (1024 * 1024)
                            original_display = f"{new_filename} ({size_mb:.2f}MB)"
                            list_item.setData(Qt.ItemDataRole.UserRole + 1, original_display)
                            break
                    
                except Exception as e:
                    QMessageBox.warning(self, "重命名警告", f"重命名文件失败：{os.path.basename(old_path)}\n错误：{str(e)}")
                
                self.progress_bar.setValue(int((j + 1) / len(rename_operations) * 100))
            
            # 更新行号显示
            self.update_line_numbers()
            
            self.progress_label.setVisible(False)
            self.progress_bar.setVisible(False)
            
            if renamed_count > 0:
                QMessageBox.information(self, "重命名完成", f"成功重命名了 {renamed_count} 个文件！")
            else:
                QMessageBox.information(self, "无需重命名", "所有文件的命名已经符合当前行号顺序。")
                
        except Exception as e:
            self.progress_label.setText(f"错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"重命名操作失败：{str(e)}")
        finally:
            self.progress_label.setVisible(False)
            self.progress_bar.setVisible(False)
            QApplication.processEvents()

    def save_files(self):
        """保存排序后的文件"""
        if self.usb_combo.currentData() is None:
            QMessageBox.warning(self, "警告", "请先选择U盘！")
            return
            
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "警告", "没有可保存的文件！")
            return

        # 检查备份目录
        if not os.path.exists(self.backup_dir):
            reply = QMessageBox.question(self, "备份目录不存在", 
                                       f"备份目录 {self.backup_dir} 不存在。\n\n是否创建该目录？",
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    os.makedirs(self.backup_dir, exist_ok=True)
                    QMessageBox.information(self, "成功", f"已创建备份目录：{self.backup_dir}")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"创建备份目录失败：{str(e)}")
                    return
            else:
                # 让用户选择备份目录
                self.choose_backup_directory()
                if not os.path.exists(self.backup_dir):
                    QMessageBox.warning(self, "警告", "必须选择有效的备份目录才能继续操作！")
                    return

        drive = self.usb_combo.currentData()
        reply = QMessageBox.question(self, "确认操作", 
                                   f"即将开始文件排序过程，目标U盘: {drive}\n"
                                   f"备份目录: {self.backup_dir}\n\n"
                                   "此操作将先备份文件，然后处理U盘。\n\n是否继续？",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return

        try:
            self.progress_label.setText("准备备份文件...")
            self.progress_label.setVisible(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            QApplication.processEvents()

            # 收集文件信息
            files_to_process = []
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                original_path = item.data(Qt.ItemDataRole.UserRole)
                filename = os.path.basename(original_path)

                # 清理文件名
                match = re.match(r"^\s*(\d+)\s*[\.\-]\s*(.*)", filename)
                cleaned_filename = filename
                if match:
                    cleaned_filename = match.group(2).strip() 
                
                if not cleaned_filename:
                    cleaned_filename = filename

                new_name = f"{i+1:03d}. {cleaned_filename}"
                backup_path = os.path.join(self.backup_dir, new_name)
                files_to_process.append({
                    'src': original_path, 
                    'backup_path': backup_path, 
                    'final_name': new_name
                })

            total_files = len(files_to_process)
            
            # 备份文件到指定目录
            self.progress_label.setText("正在备份文件...")
            QApplication.processEvents()
            
            for i, file_info in enumerate(files_to_process, 1):
                self.progress_label.setText(f"备份文件 ({i}/{total_files}): {os.path.basename(file_info['src'])}")
                QApplication.processEvents()
                shutil.copy2(file_info['src'], file_info['backup_path'])
                self.progress_bar.setValue(int(i / total_files * 50))

            # 刷新备份文件列表显示
            self.refresh_backup_file_list()
            
            self.progress_label.setText(f"备份完成！已备份 {total_files} 个文件到 {self.backup_dir}")
            QApplication.processEvents()
            
            # 询问用户选择：格式化U盘还是删除U盘文件
            choice = QMessageBox.question(self, "选择操作方式", 
                                        f"文件已成功备份到：{self.backup_dir}\n\n"
                                        "请选择下一步操作：\n\n"
                                        "• 是(Yes)：格式化U盘（推荐，会清空所有数据）\n"
                                        "• 否(No)：仅删除U盘中的音频文件",
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No |
                                        QMessageBox.StandardButton.Cancel)
            
            if choice == QMessageBox.StandardButton.Cancel:
                self.progress_label.setText("操作已取消")
                self.progress_label.setVisible(False)
                self.progress_bar.setVisible(False)
                return
            elif choice == QMessageBox.StandardButton.Yes:
                # 格式化U盘
                self.format_and_copy_files(drive, files_to_process)
            else:
                # 删除U盘文件后复制
                self.delete_and_copy_files(drive, files_to_process)
                
        except Exception as e:
            self.progress_label.setText(f"错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"操作失败：{str(e)}")
        finally:
            QApplication.processEvents()

    def format_and_copy_files(self, drive, files_to_process):
        """格式化U盘并复制文件"""
        try:
            self.progress_label.setText(f"准备格式化U盘: {drive}...")
            QApplication.processEvents()
            
            # 打开系统格式化对话框
            try:
                # 使用Windows的格式化命令
                subprocess.run(["cmd", "/c", "start", "ms-settings:storagesense"], check=False)
                # 或者直接打开资源管理器到该驱动器
                subprocess.run(["explorer", drive], check=False)
            except Exception:
                pass
            
            QMessageBox.information(self, "格式化U盘",
                                   f"请在打开的系统界面中格式化U盘 {drive}：\n\n"
                                   "1. 在资源管理器中右键点击U盘\n"
                                   "2. 选择'格式化...'\n"
                                   "3. 选择文件系统（推荐FAT32或exFAT）\n"
                                   "4. 点击'开始'进行格式化\n\n"
                                   "格式化完成后，点击'确定'继续复制文件。")
            
            self.copy_files_to_usb(drive, files_to_process, 50)
            
        except Exception as e:
            raise Exception(f"格式化操作失败：{str(e)}")

    def delete_and_copy_files(self, drive, files_to_process):
        """删除U盘文件并复制新文件"""
        try:
            self.progress_label.setText(f"正在删除U盘 {drive} 中的音频文件...")
            QApplication.processEvents()
            
            deleted_count = 0
            # 遍历U盘删除音频文件
            for root, dirs, files in os.walk(drive):
                for file in files:
                    if file.lower().endswith(self.supported_extensions):
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception as e:
                            print(f"删除文件失败 {file_path}: {e}")
            
            self.progress_label.setText(f"已删除 {deleted_count} 个音频文件")
            self.progress_bar.setValue(25)
            QApplication.processEvents()
            
            self.copy_files_to_usb(drive, files_to_process, 25)
            
        except Exception as e:
            raise Exception(f"删除文件操作失败：{str(e)}")

    def copy_files_to_usb(self, drive, files_to_process, start_progress):
        """从备份目录复制文件到U盘"""
        total_files = len(files_to_process)
        
        self.progress_label.setText("开始从备份目录复制文件到U盘...")
        QApplication.processEvents()
        
        for i, file_info in enumerate(files_to_process, 1):
            final_dst_on_usb = os.path.join(drive, file_info['final_name'])
            self.progress_label.setText(f"复制到U盘 ({i}/{total_files}): {file_info['final_name']}")
            QApplication.processEvents()
            
            # 从备份目录复制到U盘
            shutil.copy2(file_info['backup_path'], final_dst_on_usb)
            progress = start_progress + int(i / total_files * (100 - start_progress))
            self.progress_bar.setValue(progress)
        
        self.progress_label.setText("文件复制完成！")
        self.progress_bar.setValue(100)
        QApplication.processEvents()
        
        self.progress_label.setVisible(False)
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "成功", f"操作完成！\n\n已将 {total_files} 个文件按排序复制到U盘 {drive}")