import win32api
import win32file
import string

class USBHandler:
    @staticmethod
    def format_drive(drive_letter: str) -> bool:
        """格式化指定的驱动器"""
        try:
            # 这里需要调用Windows API进行格式化
            # 注意：实际实现时需要添加更多的错误处理和用户确认
            return True
        except Exception as e:
            print(f"格式化失败: {str(e)}")
            return False

    @staticmethod
    def get_drive_info(drive_letter: str) -> dict:
        """获取驱动器信息"""
        try:
            sectors_per_cluster, bytes_per_sector, _, _, _ = win32api.GetDiskFreeSpace(drive_letter)
            total_bytes = win32file.GetDiskFreeSpaceEx(drive_letter)[1]
            return {
                "total_space": total_bytes,
                "sector_size": bytes_per_sector,
                "cluster_size": sectors_per_cluster * bytes_per_sector
            }
        except Exception as e:
            print(f"获取驱动器信息失败: {str(e)}")
            return {}

    @staticmethod
    def get_usb_drives():
        """获取所有可用的U盘驱动器"""
        drives = []
        # 获取所有驱动器字母
        drive_letters = list(string.ascii_uppercase)
        for letter in drive_letters:
            drive = f"{letter}:\\"
            try:
                drive_type = win32file.GetDriveType(drive)
                # 检查是否是可移动设备
                if drive_type == win32file.DRIVE_REMOVABLE:
                    # 获取驱动器卷标
                    try:
                        volume_name = win32api.GetVolumeInformation(drive)[0]
                        drives.append({
                            'letter': drive,
                            'name': volume_name if volume_name else '可移动磁盘'
                        })
                    except:
                        continue
            except:
                continue
        return drives