import json
import os
import subprocess
import sys
import argparse
from datetime import datetime

def run_scraper_script(script_name):
    """
    Run a scraper script and return success status
    """
    try:
        print(f"🚀 运行脚本: {script_name}")
        
        # 使用最简单的方法 - 不捕获输出，让脚本直接输出到控制台
        result = subprocess.run([sys.executable, script_name])
        
        if result.returncode == 0:
            print(f"✅ {script_name} 运行成功")
            return True
        else:
            print(f"❌ {script_name} 运行失败 (退出代码: {result.returncode})")
            return False
    except Exception as e:
        print(f"❌ 运行 {script_name} 时出错: {e}")
        return False

def load_json_file(file_path):
    """
    Load JSON data from file if it exists
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
    else:
        print(f"File not found: {file_path}")
        return None

def run_all_scrapers():
    """
    Run all scraper scripts to get fresh data
    """
    scrapers = {
        'Grabbed_Aggregated_Analytics_Data.py': 'Aggregated_Analytics_Data.json',
        'Revenue_Scraper.py': 'PolyBuzz_Revenue_Aggregated_Analytics_Data.json',
        'User_Behavior_Scraper.py': 'User_Behavior_Combined_Analytics_Data.json',
        'User_Retention_Scraper.py': 'PolyBuzz_User_Retention_Combined_Analytics_Data.json'
    }
    
    print("=" * 60)
    print("🔄 开始运行所有数据抓取脚本...")
    print("=" * 60)
    
    results = {}
    for script, expected_output in scrapers.items():
        if os.path.exists(script):
            success = run_scraper_script(script)
            results[script] = {
                'success': success,
                'output_file': expected_output,
                'output_exists': os.path.exists(expected_output) if success else False
            }
        else:
            print(f"⚠️  脚本文件不存在: {script}")
            results[script] = {
                'success': False,
                'output_file': expected_output,
                'output_exists': False
            }
    
    print("\n" + "=" * 60)
    print("📊 脚本运行结果汇总:")
    print("=" * 60)
    
    for script, result in results.items():
        status = "✅ 成功" if result['success'] else "❌ 失败"
        output_status = "✅ 已生成" if result['output_exists'] else "❌ 未生成"
        print(f"{script:<35} | {status:<8} | 输出文件: {output_status}")
    
    successful_runs = sum(1 for r in results.values() if r['success'])
    total_runs = len(results)
    
    print(f"\n📈 总计: {successful_runs}/{total_runs} 个脚本成功运行")
    print("=" * 60)
    
    return results

def aggregate_all_data():
    """
    Aggregate data from all scraper outputs into a unified structure
    """
    # Define file paths
    files = {
        'grabbed': 'Aggregated_Analytics_Data.json',
        'revenue': 'PolyBuzz_Revenue_Aggregated_Analytics_Data.json',
        'user_behavior': 'User_Behavior_Combined_Analytics_Data.json',
        'user_retention': 'PolyBuzz_User_Retention_Combined_Analytics_Data.json'
    }
    
    # Load all data files
    data = {}
    for key, file_path in files.items():
        data[key] = load_json_file(file_path)
    
    # Initialize the aggregated structure
    aggregated_data = []
    
    # Get application info from any available source
    app_name = "Unknown Application"
    platforms = {}
    
    # Extract application name and platform info
    for source_data in data.values():
        if source_data and isinstance(source_data, dict):
            if 'Application' in source_data:
                app_name = source_data['Application']
                break
        elif source_data and isinstance(source_data, list) and len(source_data) > 0:
            if 'Application' in source_data[0]:
                app_name = source_data[0]['Application']
                break
    
    # Build platform-specific data structure
    # Start with existing grabbed data structure if available
    if data['grabbed'] and isinstance(data['grabbed'], list) and len(data['grabbed']) > 0:
        base_app_data = data['grabbed'][0]
        platforms = base_app_data.get('Platforms', {})
    else:
        # Create basic platform structure
        platforms = {
            "Android": {},
            "iOS": {}
        }
    
    # Add revenue data
    if data['revenue']:
        revenue_info = data['revenue']
        platform_key = "Android" if revenue_info.get('Platform') == "Google Play" else "iOS"
        
        if platform_key not in platforms:
            platforms[platform_key] = {}
            
        # Add revenue data to the appropriate platform
        if 'Revenue Data' in revenue_info and revenue_info['Revenue Data']:
            platforms[platform_key]['Average Store Revenue'] = revenue_info['Revenue Data'][0].get('Average Store Revenue', 0)
            platforms[platform_key]['Device Info'] = revenue_info['Revenue Data'][0].get('Device', 'Unknown Device')
    
    # Add user behavior data (now handles combined data)
    if data['user_behavior']:
        behavior_info = data['user_behavior']
        
        # Check if it's combined data format
        if 'Platforms' in behavior_info:
            # New combined format
            for platform_name, platform_data in behavior_info['Platforms'].items():
                platform_key = platform_name  # Use the key directly (Android/iOS)
                
                if platform_key not in platforms:
                    platforms[platform_key] = {}
                
                if 'User Behavior Data' in platform_data and platform_data['User Behavior Data']:
                    behavior_data = platform_data['User Behavior Data']
                    
                    # Find global data (全球)
                    global_data = next((item for item in behavior_data if item.get('Country/Region') == '全球'), None)
                    if global_data:
                        if 'Active Users' in global_data:
                            platforms[platform_key]['Active Users from Behavior'] = global_data['Active Users']
                        if 'User Share' in global_data:
                            platforms[platform_key]['User Share'] = global_data['User Share']
                        if 'Avg Time Per User' in global_data:
                            platforms[platform_key]['Avg Time Per User'] = global_data['Avg Time Per User']
                    
                    # Add country breakdown
                    platforms[platform_key]['User Behavior by Country'] = behavior_data
        else:
            # Old single platform format (for backward compatibility)
            platform_key = "Android" if behavior_info.get('Platform') == "Google Play" else "iOS"
            
            if platform_key not in platforms:
                platforms[platform_key] = {}
                
            # Add user behavior summary
            if 'User Behavior Data' in behavior_info and behavior_info['User Behavior Data']:
                behavior_data = behavior_info['User Behavior Data']
                
                # Find global data (全球)
                global_data = next((item for item in behavior_data if item.get('Country/Region') == '全球'), None)
                if global_data:
                    if 'Active Users' in global_data:
                        platforms[platform_key]['Active Users from Behavior'] = global_data['Active Users']
                    if 'User Share' in global_data:
                        platforms[platform_key]['User Share'] = global_data['User Share']
                    if 'Avg Time Per User' in global_data:
                        platforms[platform_key]['Avg Time Per User'] = global_data['Avg Time Per User']
                
                # Add country breakdown
                platforms[platform_key]['User Behavior by Country'] = behavior_data
    
    # Add user retention data (now handles combined data)
    if data['user_retention']:
        retention_info = data['user_retention']
        
        # Check if it's combined data format
        if 'Platforms' in retention_info:
            # New combined format
            for platform_name, platform_data in retention_info['Platforms'].items():
                platform_key = platform_name  # Use the key directly (Android/iOS)
                
                if platform_key not in platforms:
                    platforms[platform_key] = {}
                
                # Add retention data
                if 'Monthly App Retention' in platform_data:
                    platforms[platform_key]['Monthly Retention'] = platform_data['Monthly App Retention']
                if 'Publisher Apps User Retention (Overall)' in platform_data:
                    platforms[platform_key]['Overall Retention'] = platform_data['Publisher Apps User Retention (Overall)']
        else:
            # Old single platform format (for backward compatibility)
            platform_key = "Android" if retention_info.get('Platform') == "Google Play" else "iOS"
            
            if platform_key not in platforms:
                platforms[platform_key] = {}
                
            # Add retention data
            if 'Monthly App Retention' in retention_info:
                platforms[platform_key]['Monthly Retention'] = retention_info['Monthly App Retention']
            if 'Publisher Apps User Retention (Overall)' in retention_info:
                platforms[platform_key]['Overall Retention'] = retention_info['Publisher Apps User Retention (Overall)']
    
    # Create the final aggregated structure
    aggregated_app_data = {
        "Application": app_name,
        "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Data Sources": {
            "Downloads & Basic Metrics": "Available" if data['grabbed'] else "Not Available",
            "Revenue Data": "Available" if data['revenue'] else "Not Available", 
            "User Behavior Data": "Available" if data['user_behavior'] else "Not Available",
            "User Retention Data": "Available" if data['user_retention'] else "Not Available"
        },
        "Platforms": platforms
    }
    
    aggregated_data.append(aggregated_app_data)
    
    return aggregated_data

def main():
    """
    Main function to run the data aggregation
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='数据整合工具 - PolyBuzz Analytics Data Aggregator')
    parser.add_argument('--run-scrapers', '-r', action='store_true', 
                       help='先运行所有抓取脚本，然后整合数据')
    parser.add_argument('--skip-scrapers', '-s', action='store_true', 
                       help='跳过运行抓取脚本，仅整合现有数据文件')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🔥 数据整合工具 - PolyBuzz Analytics Data Aggregator")
    print("=" * 80)
    
    # Determine run mode
    if args.run_scrapers:
        choice = '2'
        print("📋 命令行参数：运行抓取脚本模式")
    elif args.skip_scrapers:
        choice = '1'
        print("📋 命令行参数：跳过抓取脚本模式")
    else:
        # Interactive mode
        print("\n选择运行模式:")
        print("1. 仅整合现有数据文件")
        print("2. 先运行所有抓取脚本，然后整合数据 (推荐)")
        print("\n💡 提示：也可以使用命令行参数:")
        print("   python Data_Aggregator.py --run-scrapers     (运行抓取脚本)")
        print("   python Data_Aggregator.py --skip-scrapers    (跳过抓取脚本)")
        
        while True:
            try:
                choice = input("\n请选择 (1 或 2): ").strip()
                if choice in ['1', '2']:
                    break
                else:
                    print("请输入 1 或 2")
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                return
    
    if choice == '2':
        print("\n🔄 将先运行所有数据抓取脚本...")
        scraper_results = run_all_scrapers()
        
        # Check if any scrapers failed
        failed_scrapers = [script for script, result in scraper_results.items() if not result['success']]
        if failed_scrapers:
            print(f"\n⚠️  以下脚本运行失败: {', '.join(failed_scrapers)}")
            print("将使用现有的数据文件进行整合...")
    else:
        print("\n📁 使用现有数据文件进行整合...")
    
    print("\n" + "=" * 60)
    print("📊 开始数据整合...")
    print("=" * 60)
    
    # Aggregate all data
    aggregated_data = aggregate_all_data()
    
    # Save to output file
    output_file = "Comprehensive_Aggregated_Analytics_Data.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(aggregated_data, f, ensure_ascii=False, indent=4)
        
        print(f"\n✅ 数据整合完成！")
        print("=" * 60)
        print(f"📁 输出文件：{output_file}")
        print(f"📊 整合的应用数量：{len(aggregated_data)}")
        
        # Print summary
        if aggregated_data:
            app_data = aggregated_data[0]
            print(f"📱 应用名称：{app_data['Application']}")
            print(f"🕒 更新时间：{app_data['Last Updated']}")
            print("\n📈 数据源状态：")
            for source, status in app_data['Data Sources'].items():
                status_icon = "✅" if status == "Available" else "❌"
                print(f"   {status_icon} {source}: {status}")
            print(f"\n🔧 平台数量：{len(app_data['Platforms'])}")
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ 保存文件时出错：{e}")

if __name__ == "__main__":
    main()
