import os
import shutil
from typing import List, Tuple

class FileManager:
    def __init__(self):
        self.temp_dir = os.path.join(os.path.expanduser("~"), "UdiskMusicReOrder_temp")

    def get_usb_drives(self) -> List[str]:
        """获取系统中的U盘设备列表"""
        # TODO: 实现U盘检测逻辑
        return []

    def load_files(self, drive_path: str) -> List[str]:
        """加载指定驱动器中的媒体文件"""
        media_files = []
        for root, _, files in os.walk(drive_path):
            for file in files:
                if file.lower().endswith(('.mp3', '.wav', '.flac', '.m4a')):
                    media_files.append(os.path.join(root, file))
        return media_files

    def prepare_temp_directory(self):
        """准备临时目录"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir)

    def copy_files_with_order(self, files: List[Tuple[str, str]], target_drive: str, 
                            progress_callback=None):
        """按顺序复制文件到目标驱动器"""
        total_files = len(files)
        for index, (src, filename) in enumerate(files, 1):
            new_name = f"{index}. {filename}"
            dst = os.path.join(target_drive, new_name)
            shutil.copy2(src, dst)
            if progress_callback:
                progress_callback(index / total_files * 100)