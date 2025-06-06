# U盘音乐文件排序工具

一个基于PyQt6开发的Windows桌面应用程序，用于对U盘中的音频视频文件进行排序和重命名。

## 功能特性

- 🔍 **自动检测U盘设备** - 程序启动时自动扫描并列出可用的U盘
- 📁 **多格式支持** - 支持常见的音频视频格式（MP3、WAV、FLAC、MP4、AVI等）
- 🎯 **拖拽排序** - 直观的拖拽界面，轻松调整文件顺序
- 🔢 **智能排序** - 按文件名中的数字前缀自动排序
- ✏️ **批量重命名** - 按行号批量重命名文件，支持3位数字格式（001、002、003...）
- 💾 **文件备份** - 操作前自动备份文件到指定目录（默认D:\temp）
- 🎨 **颜色标记** - 用不同颜色标记排序时会发生变化的文件
- 🔄 **实时更新** - 行号在拖拽排序时实时刷新

## 系统要求

- Windows 10/11
- Python 3.8+ （开发环境）
- PyQt6 （开发环境）

## 安装使用

### 方式一：下载可执行文件（推荐）

1. 前往 [Releases](../../releases) 页面
2. 下载最新版本的 `UdiskMusicReOrder-vX.X.X.zip`
3. 解压到任意目录
4. 运行 `UdiskMusicReOrder.exe`

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/your-username/UdiskMusicReOrder.git
cd UdiskMusicReOrder

# 安装依赖
pip install -r requirements.txt

# 运行程序
python src/main.py
```

## 使用说明

1. **插入U盘** - 将包含音频文件的U盘插入电脑
2. **启动程序** - 运行 UdiskMusicReOrder.exe
3. **选择U盘** - 程序会自动检测U盘，选择目标U盘
4. **加载文件** - 程序会自动加载U盘中的音频视频文件
5. **排序文件** - 使用以下方式之一排序：
   - 拖拽文件到目标位置
   - 点击"按序号排序"按钮自动排序
6. **重命名文件** - 点击"按行号重命名"按钮批量重命名
7. **保存排序** - 点击"保存排序"按钮将排序结果写入U盘

## GitHub Actions 自动构建

本项目配置了GitHub Actions自动构建和发布流程：

### 触发条件
- 推送标签时自动触发（如 `v1.0.0`）
- 支持手动触发

### 构建流程
1. 设置Python 3.11环境
2. 安装项目依赖
3. 使用PyInstaller打包成单文件可执行程序
4. 创建发布包（包含exe文件和使用说明）
5. 自动创建GitHub Release
6. 上传构建产物

### 发布新版本

```bash
# 创建并推送标签
git tag v1.0.0
git push origin v1.0.0
```

推送标签后，GitHub Actions会自动：
- 构建Windows可执行文件
- 创建Release页面
- 上传打包好的zip文件

### 手动触发构建

1. 进入GitHub仓库的Actions页面
2. 选择"Build and Release"工作流
3. 点击"Run workflow"按钮
4. 选择分支并运行

## 技术栈

- **界面框架**: PyQt6
- **打包工具**: PyInstaller
- **CI/CD**: GitHub Actions
- **开发语言**: Python 3.11

## 项目结构

```
UdiskMusicReOrder/
├── src/
│   ├── main.py              # 程序入口
│   ├── ui/
│   │   └── main_window.py   # 主窗口界面
│   ├── core/
│   │   ├── file_manager.py  # 文件管理
│   │   └── usb_handler.py   # U盘操作
│   └── utils/               # 工具函数
├── resources/               # 资源文件
├── .github/
│   └── workflows/
│       └── build-and-release.yml  # GitHub Actions配置
├── requirements.txt         # Python依赖
└── README.md               # 项目说明
```

## 注意事项

- 操作前程序会自动备份文件到D:\temp目录
- 格式化操作不可逆，请谨慎操作
- 确保U盘有足够的存储空间
- 支持的文件格式：MP3、WAV、FLAC、M4A、WMA、MP4、AVI、MKV、MOV、WMV等