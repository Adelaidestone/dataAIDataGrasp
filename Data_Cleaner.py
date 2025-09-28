"""
数据清理工具 - Data Cleaner
功能：自由删除聚合数据中的指定内容
支持删除特定平台、数据源、国家/地区、时间段等
"""

import json
import os
from datetime import datetime
import copy

class DataCleaner:
    def __init__(self, data_file="Comprehensive_Aggregated_Analytics_Data.json"):
        self.data_file = data_file
        self.backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{data_file}"
        self.data = None
        
    def load_data(self):
        """加载数据文件"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ 已加载数据文件: {self.data_file}")
            return True
        except Exception as e:
            print(f"❌ 加载数据文件失败: {e}")
            return False
    
    def backup_data(self):
        """备份原始数据"""
        try:
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            print(f"✅ 数据已备份到: {self.backup_file}")
        except Exception as e:
            print(f"❌ 备份失败: {e}")
    
    def save_data(self):
        """保存修改后的数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            print(f"✅ 数据已保存到: {self.data_file}")
        except Exception as e:
            print(f"❌ 保存失败: {e}")
    
    def show_data_structure(self):
        """显示数据结构"""
        if not self.data:
            print("❌ 请先加载数据")
            return
        
        print("\n📊 当前数据结构:")
        print("=" * 60)
        
        for i, app in enumerate(self.data):
            print(f"应用 {i+1}: {app.get('Application', 'Unknown')}")
            print(f"  更新时间: {app.get('Last Updated', 'Unknown')}")
            
            # 显示数据源
            data_sources = app.get('Data Sources', {})
            print("  数据源:")
            for source, status in data_sources.items():
                status_icon = "✅" if status == "Available" else "❌"
                print(f"    {status_icon} {source}")
            
            # 显示平台
            platforms = app.get('Platforms', {})
            print("  平台:")
            for platform in platforms.keys():
                print(f"    📱 {platform}")
                
                # 显示该平台的数据类型
                platform_data = platforms[platform]
                if 'User Behavior by Country' in platform_data:
                    countries = len(platform_data['User Behavior by Country'])
                    print(f"      - 用户行为数据: {countries} 个国家/地区")
                
                if 'Monthly App Retention' in platform_data:
                    months = len(platform_data['Monthly App Retention'])
                    print(f"      - 用户留存数据: {months} 个月份")
                
                if 'Recent Three Month Downloads' in platform_data:
                    downloads = len(platform_data['Recent Three Month Downloads'])
                    print(f"      - 下载趋势数据: {downloads} 个月份")
            
            print()
    
    def delete_platform(self, platform_name):
        """删除指定平台的所有数据"""
        if not self.data:
            print("❌ 请先加载数据")
            return
        
        deleted_count = 0
        for app in self.data:
            platforms = app.get('Platforms', {})
            if platform_name in platforms:
                del platforms[platform_name]
                deleted_count += 1
                print(f"✅ 已删除应用 '{app.get('Application')}' 的 {platform_name} 平台数据")
        
        if deleted_count == 0:
            print(f"⚠️ 未找到平台: {platform_name}")
        else:
            print(f"🎯 总共删除了 {deleted_count} 个应用的 {platform_name} 平台数据")
    
    def delete_data_source(self, source_name):
        """删除指定数据源"""
        if not self.data:
            print("❌ 请先加载数据")
            return
        
        source_mapping = {
            'downloads': ['Downloads', 'Downloads Change', 'Cumulative Downloads', 'Cumulative Downloads Change', 
                         'Active Users', 'Active Users Change', 'Recent Three Month Downloads'],
            'revenue': ['Store Revenue', 'Store Revenue Change', 'Average Store Revenue', 'Device Info'],
            'behavior': ['Active Users from Behavior', 'User Share', 'Avg Time Per User', 'User Behavior by Country'],
            'retention': ['Monthly App Retention', 'Overall Retention']
        }
        
        if source_name.lower() not in source_mapping:
            print(f"❌ 未知数据源: {source_name}")
            print(f"💡 可用数据源: {list(source_mapping.keys())}")
            return
        
        fields_to_delete = source_mapping[source_name.lower()]
        deleted_count = 0
        
        for app in self.data:
            # 更新数据源状态
            data_sources = app.get('Data Sources', {})
            for ds_name, status in data_sources.items():
                if source_name.lower() in ds_name.lower():
                    data_sources[ds_name] = "Not Available"
            
            # 删除平台数据中的相关字段
            platforms = app.get('Platforms', {})
            for platform_name, platform_data in platforms.items():
                for field in fields_to_delete:
                    if field in platform_data:
                        del platform_data[field]
                        deleted_count += 1
        
        print(f"✅ 已删除 {source_name} 数据源，共删除 {deleted_count} 个字段")
    
    def delete_countries(self, countries_to_delete, platform=None):
        """删除指定国家/地区的数据"""
        if not self.data:
            print("❌ 请先加载数据")
            return
        
        if isinstance(countries_to_delete, str):
            countries_to_delete = [countries_to_delete]
        
        deleted_count = 0
        for app in self.data:
            platforms = app.get('Platforms', {})
            
            for platform_name, platform_data in platforms.items():
                if platform and platform_name != platform:
                    continue
                
                if 'User Behavior by Country' in platform_data:
                    behavior_data = platform_data['User Behavior by Country']
                    original_length = len(behavior_data)
                    
                    # 过滤掉指定的国家/地区
                    platform_data['User Behavior by Country'] = [
                        country_data for country_data in behavior_data
                        if country_data.get('Country/Region') not in countries_to_delete
                    ]
                    
                    new_length = len(platform_data['User Behavior by Country'])
                    deleted_count += (original_length - new_length)
        
        print(f"✅ 已删除国家/地区: {', '.join(countries_to_delete)}")
        print(f"🎯 总共删除了 {deleted_count} 条国家数据")
    
    def delete_time_period(self, start_month=None, end_month=None, year=None):
        """删除指定时间段的数据"""
        if not self.data:
            print("❌ 请先加载数据")
            return
        
        deleted_count = 0
        for app in self.data:
            platforms = app.get('Platforms', {})
            
            for platform_name, platform_data in platforms.items():
                # 删除下载趋势数据
                if 'Recent Three Month Downloads' in platform_data:
                    downloads = platform_data['Recent Three Month Downloads']
                    original_length = len(downloads)
                    
                    filtered_downloads = []
                    for download in downloads:
                        keep = True
                        if year and download.get('Year') == year:
                            if start_month and download.get('Month') == start_month:
                                keep = False
                            elif end_month and download.get('Month') == end_month:
                                keep = False
                        
                        if keep:
                            filtered_downloads.append(download)
                    
                    platform_data['Recent Three Month Downloads'] = filtered_downloads
                    deleted_count += (original_length - len(filtered_downloads))
                
                # 删除留存数据
                if 'Monthly App Retention' in platform_data:
                    retention = platform_data['Monthly App Retention']
                    original_length = len(retention)
                    
                    if year:
                        platform_data['Monthly App Retention'] = [
                            month_data for month_data in retention
                            if f"{year}年" not in month_data.get('Month', '')
                        ]
                    
                    deleted_count += (original_length - len(platform_data['Monthly App Retention']))
        
        print(f"✅ 已删除时间段数据，总共删除了 {deleted_count} 条记录")
    
    def interactive_menu(self):
        """交互式菜单"""
        while True:
            print("\n" + "="*60)
            print("🛠️  数据清理工具 - 交互式菜单")
            print("="*60)
            print("1. 📊 查看数据结构")
            print("2. 📱 删除指定平台数据")
            print("3. 📋 删除指定数据源")
            print("4. 🌍 删除指定国家/地区数据")
            print("5. 📅 删除指定时间段数据")
            print("6. 💾 保存修改")
            print("7. 🔄 重新加载数据")
            print("8. 🚪 退出")
            print("="*60)
            
            choice = input("请选择操作 (1-8): ").strip()
            
            if choice == '1':
                self.show_data_structure()
            
            elif choice == '2':
                platform = input("请输入要删除的平台名称 (Android/iOS): ").strip()
                if platform:
                    self.delete_platform(platform)
            
            elif choice == '3':
                print("可用数据源: downloads, revenue, behavior, retention")
                source = input("请输入要删除的数据源: ").strip()
                if source:
                    self.delete_data_source(source)
            
            elif choice == '4':
                countries = input("请输入要删除的国家/地区 (用逗号分隔): ").strip()
                platform = input("指定平台 (Android/iOS，留空则删除所有平台): ").strip()
                if countries:
                    country_list = [c.strip() for c in countries.split(',')]
                    self.delete_countries(country_list, platform if platform else None)
            
            elif choice == '5':
                year = input("请输入年份 (如: 2025): ").strip()
                month = input("请输入月份 (如: June): ").strip()
                if year or month:
                    self.delete_time_period(
                        start_month=month if month else None,
                        year=int(year) if year.isdigit() else None
                    )
            
            elif choice == '6':
                self.save_data()
            
            elif choice == '7':
                self.load_data()
            
            elif choice == '8':
                print("👋 再见！")
                break
            
            else:
                print("❌ 无效选择，请重试")

def main():
    print("🛠️  数据清理工具启动")
    print("="*60)
    
    cleaner = DataCleaner()
    
    if not cleaner.load_data():
        return
    
    # 自动备份
    cleaner.backup_data()
    
    # 显示使用方法
    print("\n💡 使用方法:")
    print("1. 查看数据结构了解当前内容")
    print("2. 选择要删除的内容类型")
    print("3. 保存修改")
    print("4. 原始数据已自动备份")
    
    # 启动交互式菜单
    cleaner.interactive_menu()

if __name__ == "__main__":
    main()
