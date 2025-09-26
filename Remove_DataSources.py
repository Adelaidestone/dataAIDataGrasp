"""
删除 Data Sources 字段脚本
专门用于删除聚合数据中的 "Data Sources" 部分
"""

import json
import os
from datetime import datetime

def remove_data_sources(data_file="Comprehensive_Aggregated_Analytics_Data.json"):
    """删除 Data Sources 字段"""
    
    # 备份原文件
    backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{data_file}"
    
    try:
        # 读取数据
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 已加载数据文件: {data_file}")
        
        # 备份
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ 数据已备份到: {backup_file}")
        
        # 删除 Data Sources 字段
        removed_count = 0
        for app in data:
            if 'Data Sources' in app:
                del app['Data Sources']
                removed_count += 1
                print(f"🗑️ 已删除应用 '{app.get('Application', 'Unknown')}' 的 Data Sources")
        
        # 保存修改后的数据
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"\n🎉 完成!")
        print(f"📊 总共删除了 {removed_count} 个 Data Sources 字段")
        print(f"💾 修改后的数据已保存到: {data_file}")
        print(f"🔒 原始数据备份在: {backup_file}")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")

def main():
    print("🗑️ Data Sources 删除工具")
    print("="*50)
    print("这个脚本将删除聚合数据中的 'Data Sources' 字段")
    print("原始数据会自动备份")
    print("="*50)
    
    # 确认操作
    confirm = input("确认删除 Data Sources 字段? (y/N): ").strip().lower()
    
    if confirm in ['y', 'yes']:
        remove_data_sources()
    else:
        print("❌ 操作已取消")

if __name__ == "__main__":
    main()
