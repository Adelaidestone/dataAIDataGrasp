# PolyBuzz 智能数据分析工具

## 概述

智能数据分析工具，能够自动检测和处理产品HTML数据文件。支持单个产品和批量产品两种模式，自动提取、转换和整合各种分析数据，生成统一的综合分析报告。

## 🗂️ 工具组件

### 🎯 **核心工具**
- `Batch_Folder_Processor.py` - **智能产品数据处理器**（唯一必需的工具）

### 🤖 **自动调用组件**
- `Data_Aggregator.py` - 数据整合器（自动调用）
- `User_Retention_Scraper.py` - 用户留存数据抓取（自动调用）
- `User_Behavior_Scraper.py` - 用户行为数据抓取（自动调用）
- `Revenue_Scraper.py` - 收入数据抓取（自动调用）
- `Grabbed_Aggregated_Analytics_Data.py` - 基础指标数据抓取（自动调用）

### 🛠️ **数据管理工具**
- `Data_Cleaner.py` - 完整数据清理工具（交互式菜单）
- `Remove_DataSources.py` - 专用Data Sources字段删除工具

## 功能特点

### 🤖 **智能模式检测**
- 📁 **单个产品模式**：输入文件夹直接包含HTML文件
- 📂 **批量产品模式**：输入文件夹包含多个产品子文件夹
- 🔍 **自动检测**：无需手动指定模式

### 🚀 **一键处理**
- 自动识别HTML文件类型
- 自动运行对应的数据抓取脚本
- 自动整合所有数据源
- 自动清理中间文件

### 📊 **完整数据流程**
- 数据提取 → 数据转换 → 数据整合 → 结果输出
- 支持Android和iOS双平台数据
- 保持数据完整性和一致性

## 🚀 快速开始

### 🔧 **配置路径**
编辑 `Batch_Folder_Processor.py` 第328行：
```python
INPUT_FOLDER = r"您的输入文件夹路径"
```

### ⚡ **一键运行**
```bash
python Batch_Folder_Processor.py
```

### 📁 **输入文件夹结构**

#### 单个产品模式
```
您的输入文件夹/
├── 产品_android_retention.html
├── 产品_ios_retention.html
├── 产品_main_allplatform.html
└── 产品_android_behaviour.html
```

#### 批量产品模式
```
您的输入文件夹/
├── 产品A/
│   ├── A_android_retention.html
│   └── A_ios_retention.html
├── 产品B/
│   ├── B_main_allplatform.html
│   └── B_android_behaviour.html
└── 产品C/
    └── ...
```

## 📋 使用场景

### 🎯 **场景1: 处理单个产品**
当您的文件夹直接包含HTML文件时：
```
设置: INPUT_FOLDER = r"D:\新建文件夹"
运行: python Batch_Folder_Processor.py
结果: 自动检测为单个产品模式
```

### 🎯 **场景2: 批量处理多个产品**
当您的文件夹包含多个产品子文件夹时：
```
设置: INPUT_FOLDER = r"D:\所有产品文件夹"
运行: python Batch_Folder_Processor.py
结果: 自动检测为批量产品模式
```

### 🛠️ **场景3: 数据清理和管理**
处理完成后，可以使用数据管理工具：
```bash
# 完整数据清理（交互式菜单）
python Data_Cleaner.py

# 快速删除Data Sources字段
python Remove_DataSources.py
```

## 🔍 **文件类型识别规则**

工具通过文件名自动识别文件类型：
- `allplatform` / `全平台` → 基础指标数据
- `retention` / `留存` → 用户留存数据
- `behavior` / `behaviour` / `行为` → 用户行为数据
- `revenue` / `收入` → 收入数据

## 📁 输出结果

### 🎯 **最终输出**
- `E:\dataAI\Comprehensive_Aggregated_Analytics_Data.json` - 完整整合数据
- `E:\dataAI\Batch_Processing_Summary.json` - 处理总结报告

### 🛠️ **数据管理**
处理完成后，您可以使用以下工具管理聚合数据：

#### **完整数据清理工具** (`Data_Cleaner.py`)
- 📱 删除指定平台数据（Android/iOS）
- 📊 删除指定数据源（downloads/revenue/behavior/retention）
- 🌍 删除指定国家/地区数据
- 📅 删除指定时间段数据
- 🔒 自动备份原始数据

#### **快速字段删除工具** (`Remove_DataSources.py`)
- 🗑️ 专门删除 `Data Sources` 字段
- ⚡ 一键快速操作
- 🔒 自动备份保护

### 📊 **数据结构**
```json
[
    {
        "Application": "应用名称",
        "Last Updated": "更新时间",
        "Data Sources": {
            "Downloads & Basic Metrics": "Available/Not Available",
            "Revenue Data": "Available/Not Available", 
            "User Behavior Data": "Available/Not Available",
            "User Retention Data": "Available/Not Available"
        },
        "Platforms": {
            "Android": {
                // Android平台的所有数据
            },
            "iOS": {
                // iOS平台的所有数据
            }
        }
    }
]
```

## 🔄 **处理流程**

### 自动执行步骤：
1. **🔍 分析输入** - 检测模式和文件类型
2. **🚀 运行脚本** - 自动调用对应的数据抓取脚本
3. **📊 整合数据** - 使用Data_Aggregator整合所有数据
4. **🧹 清理文件** - 删除中间文件，只保留最终结果
5. **📋 生成报告** - 创建处理总结报告

## 运行示例

### 成功运行示例
```
🎯 智能产品数据处理器
============================================================
📂 输入目录: D:\Users\Mussy\Desktop
📊 最终聚合数据位置: E:\dataAI\
🤖 自动检测: 单个产品 或 批量产品
============================================================
🎯 检测到批量产品模式 - 找到 4 个产品文件夹
================================================================================

🚀 [1/4] 开始处理产品: 新建文件夹
================================================================================
🔍 分析产品文件夹: 新建文件夹
  📄 产品_main_allplatform.html → Grabbed_Aggregated_Analytics_Data.py
🔧 需要运行 1 个脚本
🚀 处理脚本: Grabbed_Aggregated_Analytics_Data.py
✅ 更新脚本路径: Grabbed_Aggregated_Analytics_Data.py
🚀 运行: Grabbed_Aggregated_Analytics_Data.py
✅ Grabbed_Aggregated_Analytics_Data.py 运行成功
🔄 生成最终聚合数据...
✅ 最终聚合数据生成成功
🧹 清理原始数据文件...
✅ 清理完成，删除了 1 个原始文件
📊 只保留: Comprehensive_Aggregated_Analytics_Data.json
✅ 产品 '新建文件夹' 处理成功

🎉 处理完成!
📊 成功处理了 1 个产品:
   ✅ 新建文件夹
📊 总结报告: E:\dataAI\Batch_Processing_Summary.json
📁 最终聚合数据: E:\dataAI
```

## 🔧 依赖要求

### Python包依赖
```bash
pip install beautifulsoup4 lxml pandas
```

### 系统要求
- Python 3.6+
- Windows 10/11 (已测试)
- 足够的磁盘空间存储数据文件

## 🛠️ 故障排除

### 常见问题

#### 1. 文件夹为空
```
⚠️ 文件夹中没有HTML文件: 产品名
```
**解决方案**: 确保输入文件夹包含HTML文件

#### 2. 路径不存在
```
❌ 输入路径不存在: D:\不存在的路径
```
**解决方案**: 检查并修正 INPUT_FOLDER 路径

#### 3. 脚本运行失败
```
❌ Revenue_Scraper.py 运行失败
```
**解决方案**: 检查HTML文件格式和内容完整性

### 🔍 调试技巧
1. 检查HTML文件是否完整下载
2. 确认文件名符合识别规则
3. 查看生成的总结报告了解详细状态

## 📞 支持

### 🔧 数据管理工具使用
1. **完整清理**：`python Data_Cleaner.py` - 交互式菜单选择删除内容
2. **快速删除**：`python Remove_DataSources.py` - 一键删除Data Sources字段

### 快速检查清单
- ✅ Python环境正确安装
- ✅ 依赖包已安装
- ✅ 输入路径配置正确
- ✅ HTML文件格式完整

---
*最后更新: 2025-09-26*
*工具版本: v2.1 - 智能简化版 + 数据管理*