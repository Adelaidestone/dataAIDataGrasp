#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单数据分离器 - Simple Data Separator
==================================================

功能说明：
- 将完整数据的产品放入一个JSON
- 将不完整数据的产品放入另一个JSON
- 简单直接，无复杂逻辑

作者: AI Assistant
创建时间: 2025-09-26
版本: 1.0.0
"""

import os
import json
import glob
from datetime import datetime

class SimpleDataSeparator:
    """简单数据分离器"""
    
    def __init__(self):
        """初始化分离器"""
        self.complete_products = []
        self.incomplete_products = []
    
    def load_all_product_files(self):
        """加载所有产品文件"""
        # 从目标目录查找所有产品数据文件
        target_dir = r"D:\Users\Mussy\Desktop\result"
        product_files = glob.glob(os.path.join(target_dir, "Product_*_Data.json"))
        
        print(f"🔍 找到 {len(product_files)} 个产品文件:")
        for file in product_files:
            print(f"  📄 {os.path.basename(file)}")
        
        return product_files
    
    def is_product_complete(self, product_data):
        """检查产品数据是否完整（检查3个数据源）"""
        if not isinstance(product_data, dict):
            return False
        
        data_sources = product_data.get('Data Sources', {})
        
        # 检查3个必需的数据源（移除用户留存数据）
        required_sources = [
            'Downloads & Basic Metrics',
            'Revenue Data',
            'User Behavior Data'
        ]
        
        available_count = 0
        for source in required_sources:
            if data_sources.get(source) == 'Available':
                available_count += 1
        
        # 如果3个都有，就是完整的
        return available_count == 3
    
    def separate_products(self):
        """分离完整和不完整的产品数据"""
        product_files = self.load_all_product_files()
        
        if not product_files:
            print("❌ 没有找到产品文件")
            return False
        
        print(f"\n🔄 开始分离产品数据...")
        
        for file_path in product_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 处理数据格式（可能是列表或单个对象）
                products = data if isinstance(data, list) else [data]
                
                for product in products:
                    if not isinstance(product, dict):
                        continue
                    
                    app_name = product.get('Application', 'Unknown')
                    
                    if self.is_product_complete(product):
                        self.complete_products.append(product)
                        print(f"  ✅ 完整产品: {app_name}")
                    else:
                        self.incomplete_products.append(product)
                        print(f"  ⚠️  不完整产品: {app_name}")
                        
            except Exception as e:
                print(f"❌ 加载文件 {file_path} 失败: {e}")
                continue
        
        print(f"\n📊 分离结果:")
        print(f"  ✅ 完整产品: {len(self.complete_products)} 个")
        print(f"  ⚠️  不完整产品: {len(self.incomplete_products)} 个")
        
        return True
    
    def save_separated_data(self):
        """保存分离后的数据到两个JSON文件"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 设置输出目录
        output_dir = r"D:\Users\Mussy\Desktop\result"
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存完整产品数据
        if self.complete_products:
            complete_data = {
                "Complete_Products_Data": {
                    "generated_time": current_time,
                    "total_products": len(self.complete_products),
                    "description": "包含所有3种数据源的完整产品数据",
                    "products": self.complete_products
                }
            }
            
            complete_path = os.path.join(output_dir, "Complete_Products_Data.json")
            with open(complete_path, 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 完整产品数据已保存: {complete_path} ({len(self.complete_products)} 个产品)")
        
        # 保存不完整产品数据
        if self.incomplete_products:
            incomplete_data = {
                "Incomplete_Products_Data": {
                    "generated_time": current_time,
                    "total_products": len(self.incomplete_products),
                    "description": "缺少部分数据源的不完整产品数据",
                    "products": self.incomplete_products
                }
            }
            
            incomplete_path = os.path.join(output_dir, "Incomplete_Products_Data.json")
            with open(incomplete_path, 'w', encoding='utf-8') as f:
                json.dump(incomplete_data, f, indent=2, ensure_ascii=False)
            
            print(f"⚠️  不完整产品数据已保存: {incomplete_path} ({len(self.incomplete_products)} 个产品)")
        
        return True

def main():
    """主函数"""
    print("🔥 简单数据分离器")
    print("=" * 60)
    
    separator = SimpleDataSeparator()
    
    # 分离产品数据
    if separator.separate_products():
        # 保存分离后的数据
        separator.save_separated_data()
    
    output_dir = r"D:\Users\Mussy\Desktop\result"
    print(f"\n🎯 分离完成!")
    print(f"📁 完整产品数据: {os.path.join(output_dir, 'Complete_Products_Data.json')}")
    print(f"📁 不完整产品数据: {os.path.join(output_dir, 'Incomplete_Products_Data.json')}")

if __name__ == "__main__":
    main()
