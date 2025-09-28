"""
删除 Data Sources 字段脚本
专门用于删除产品数据中的 "Data Sources" 部分
现在处理新的 Product_*.json 文件格式
"""

import json
import os
import glob
from datetime import datetime

def remove_data_sources(target_dir=r"D:\Users\Mussy\Desktop\result"):
    """删除所有产品文件中的 Data Sources 字段"""
    
    # 创建备份目录
    backup_dir = os.path.join(target_dir, "backup_" + datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        # 查找所有产品文件
        product_files = glob.glob(os.path.join(target_dir, "Product_*.json"))
        
        if not product_files:
            print("❌ 未找到任何产品文件")
            return
        
        print(f"✅ 找到 {len(product_files)} 个产品文件")
        
        removed_count = 0
        processed_files = 0
        
        for file_path in product_files:
            filename = os.path.basename(file_path)
            print(f"\n🔄 处理文件: {filename}")
            
            # 备份文件
            backup_path = os.path.join(backup_dir, filename)
            
            # 读取数据
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 备份
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # 删除 Data Sources 字段
            file_removed_count = 0
            for app in data:
                if 'Data Sources' in app:
                    del app['Data Sources']
                    file_removed_count += 1
                    print(f"  🗑️ 已删除应用 '{app.get('Application', 'Unknown')}' 的 Data Sources")
            
            # 保存修改后的数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            removed_count += file_removed_count
            processed_files += 1
            print(f"  ✅ 文件处理完成，删除了 {file_removed_count} 个 Data Sources")
        
        print(f"\n🎉 全部完成!")
        print(f"📊 处理了 {processed_files} 个文件")
        print(f"📊 总共删除了 {removed_count} 个 Data Sources 字段")
        print(f"💾 修改后的数据已保存到各产品文件")
        print(f"🔒 所有原始数据备份在: {backup_dir}")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")

def main():
    print("🗑️ 产品数据 Data Sources 删除工具")
    print("="*60)
    print("这个脚本将删除所有产品JSON文件中的 'Data Sources' 字段")
    print("处理目录: D:\\Users\\Mussy\\Desktop\\result")
    print("原始数据会自动备份")
    print("="*60)
    
    # 直接执行删除操作
    remove_data_sources()

if __name__ == "__main__":
    main()
