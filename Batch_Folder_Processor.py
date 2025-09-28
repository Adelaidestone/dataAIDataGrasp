"""
智能产品数据处理器 - Smart Product Data Processor
功能：智能处理产品HTML数据文件
- 单个产品模式：输入文件夹直接包含HTML文件
- 批量产品模式：输入文件夹包含多个产品子文件夹
自动检测模式并处理，生成最终聚合数据
"""

import os
import json
import shutil
import subprocess
import sys
from datetime import datetime
import re
from pathlib import Path

import glob

class SmartProductProcessor:
    def __init__(self, base_input_path, base_output_path="E:\\dataAI\\batch_results"):
        self.base_input_path = base_input_path
        self.base_output_path = base_output_path
        self.script_mappings = {
            'main_allplatform': 'Grabbed_Aggregated_Analytics_Data.py',
            'user_behavior': 'User_Behavior_Scraper.py',
            'revenue': 'Revenue_Scraper.py'
        }
    
    def get_folders_to_process(self):
        """获取需要处理的文件夹列表"""
        folders = []
        try:
            for item in os.listdir(self.base_input_path):
                item_path = os.path.join(self.base_input_path, item)
                if os.path.isdir(item_path):
                    folders.append(item_path)
        except Exception as e:
            print(f"❌ 读取文件夹时出错: {e}")
        
        return folders
    
    def identify_file_type(self, filename):
        """识别HTML文件类型"""
        filename_lower = filename.lower()
        if '行为' in filename or 'behavior' in filename_lower or 'behaviour' in filename_lower or 'userbehavior' in filename_lower or 'userbehaivor' in filename_lower:
            return 'user_behavior'
        elif '收入' in filename or 'revenue' in filename_lower:
            return 'revenue'
        elif 'allplatform' in filename_lower or '全平台' in filename or '下载量' in filename:
            return 'main_allplatform'
        else:
            return 'unknown'
    
    def extract_product_name(self, filename):
        """从文件名提取产品名称"""
        # 简单的产品名提取，可以根据需要优化
        name_parts = filename.replace('.html', '').split('_')
        if name_parts:
            return name_parts[0]
        return "Unknown Product"
    
    def analyze_folder_files(self, folder_path):
        """分析文件夹中的HTML文件"""
        html_files = []
        
        for file in os.listdir(folder_path):
            if file.endswith('.html'):
                file_type = self.identify_file_type(file)
                product_name = self.extract_product_name(file)
                
                html_files.append({
                    'filename': file,
                    'filepath': os.path.join(folder_path, file),
                    'file_type': file_type,
                    'product_name': product_name,
                    'script': self.script_mappings.get(file_type, 'unknown')
                })
                
                print(f"  📄 {file} → {self.script_mappings.get(file_type, '未知脚本')}")
        
        return html_files
    
    def update_script_path(self, script_name, files):
        """更新脚本中的HTML文件路径"""
        try:
            script_path = os.path.join("E:\\dataAI", script_name)
            backup_path = script_path + ".backup"
            
            # 备份原文件
            shutil.copy2(script_path, backup_path)
            
            # 读取脚本内容
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if script_name in ['User_Behavior_Scraper.py']:
                # 多平台脚本 - 更新html_files字典
                android_file = None
                ios_file = None
                
                for file_info in files:
                    if 'android' in file_info['filename'].lower() or '安卓' in file_info['filename']:
                        android_file = file_info['filepath'].replace('\\', '\\\\')
                    elif 'ios' in file_info['filename'].lower() or '苹果' in file_info['filename']:
                        ios_file = file_info['filepath'].replace('\\', '\\\\')
                    else:
                        # 如果没有明确的平台标识，默认为Android
                        if not android_file:
                            android_file = file_info['filepath'].replace('\\', '\\\\')
                
                if android_file or ios_file:
                    # 构建新的html_files字典
                    new_html_files = "html_files = {\n"
                    if android_file:
                        new_html_files += f'    "Android": r"{android_file}",\n'
                    if ios_file:
                        new_html_files += f'    "iOS": r"{ios_file}"\n'
                    new_html_files += "}"
                    
                    # 替换html_files字典
                    pattern = r'html_files\s*=\s*\{[^}]*\}'
                    content = re.sub(pattern, new_html_files, content, flags=re.DOTALL)
            
            else:
                # 单平台脚本 - 更新html_file_path变量
                if files:
                    file_path = files[0]['filepath'].replace('\\', '\\\\')
                    pattern = r'html_file_path\s*=\s*r?"[^"]*"'
                    replacement = f'html_file_path = r"{file_path}"'
                    content = re.sub(pattern, replacement, content)
            
            # 写回文件
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 更新脚本路径: {script_name}")
            return True
            
        except Exception as e:
            print(f"❌ 更新脚本路径失败 {script_name}: {e}")
            return False
    
    def restore_script_backup(self, script_name):
        """恢复脚本备份"""
        try:
            script_path = os.path.join("E:\\dataAI", script_name)
            backup_path = script_path + ".backup"
            
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, script_path)
                os.remove(backup_path)
                print(f"🔄 恢复脚本: {script_name}")
            
        except Exception as e:
            print(f"❌ 恢复脚本失败 {script_name}: {e}")
    
    def run_script(self, script_name):
        """运行脚本"""
        try:
            script_path = os.path.join("E:\\dataAI", script_name)
            print(f"🚀 运行: {script_name}")
            
            result = subprocess.run([sys.executable, script_path], 
                                  cwd="E:\\dataAI")
            
            if result.returncode == 0:
                print(f"✅ {script_name} 运行成功")
                return True
            else:
                print(f"❌ {script_name} 运行失败")
                return False
                
        except Exception as e:
            print(f"❌ 运行脚本失败 {script_name}: {e}")
            return False
    
    def process_revenue_files_separately(self, files):
        """单独处理Revenue文件"""
        for file_info in files:
            print(f"🚀 处理Revenue文件: {file_info['filename']}")
            if self.update_script_path('Revenue_Scraper.py', [file_info]):
                self.run_script('Revenue_Scraper.py')
                self.restore_script_backup('Revenue_Scraper.py')
    
    def process_product_folder(self, product_folder_path):
        """处理单个产品文件夹"""
        try:
            folder_name = os.path.basename(product_folder_path)
            print(f"🔍 分析产品文件夹: {folder_name}")
            
            # 分析文件夹中的HTML文件
            html_files = self.analyze_folder_files(product_folder_path)
            
            if not html_files:
                print(f"⚠️ 文件夹中没有HTML文件: {folder_name}")
                return False
            
            # 按脚本分组处理
            script_groups = {}
            for file_info in html_files:
                script = file_info['script']
                if script != 'unknown':
                    if script not in script_groups:
                        script_groups[script] = []
                    script_groups[script].append(file_info)
            
            print(f"🔧 需要运行 {len(script_groups)} 个脚本")
            
            # 处理每个脚本组
            for script, files in script_groups.items():
                print(f"🚀 处理脚本: {script}")
                
                if script == 'Revenue_Scraper.py':
                    # Revenue脚本需要单独处理每个平台
                    self.process_revenue_files_separately(files)
                else:
                    # 其他脚本支持双平台
                    if self.update_script_path(script, files):
                        self.run_script(script)
                        self.restore_script_backup(script)
            
            # 直接保存产品数据并清理原始文件
            self.save_product_data_from_aggregator()
            self.cleanup_raw_data()
            
            return True
            
        except Exception as e:
            print(f"❌ 处理产品文件夹时出错: {e}")
            return False
    
    def save_product_data_from_aggregator(self):
        """直接从各个脚本输出生成产品数据文件"""
        print("🔄 生成最终聚合数据...")
        
        try:
            # 直接从各个脚本的输出文件整合数据
            files = {
                'grabbed': 'Aggregated_Analytics_Data.json',
                'revenue': 'PolyBuzz_Revenue_Aggregated_Analytics_Data.json',
                'user_behavior': 'User_Behavior_Combined_Analytics_Data.json'
            }
            
            # 加载数据文件
            data = {}
            for key, file_path in files.items():
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data[key] = json.load(f)
                    except:
                        data[key] = None
                else:
                    data[key] = None
            
            # 获取应用名称
            app_name = "Unknown_Application"
            for source_data in data.values():
                if source_data and isinstance(source_data, dict):
                    if 'Application' in source_data:
                        app_name = source_data['Application']
                        break
                elif source_data and isinstance(source_data, list) and len(source_data) > 0:
                    if 'Application' in source_data[0]:
                        app_name = source_data[0]['Application']
                        break
            
            # 创建聚合数据结构
            aggregated_data = [{
                "Application": app_name,
                "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Data Sources": {
                    "Downloads & Basic Metrics": "Available" if data['grabbed'] else "Not Available",
                    "Revenue Data": "Available" if data['revenue'] else "Not Available", 
                    "User Behavior Data": "Available" if data['user_behavior'] else "Not Available"
                },
                "Platforms": self.build_platform_data(data)
            }]
            
            # 清理产品名称，用于文件名
            import re
            clean_name = re.sub(r'[^\w\s-]', '', app_name).strip()
            clean_name = re.sub(r'[-\s]+', '_', clean_name)
            
            # 直接保存到最终输出目录
            final_output_dir = r"D:\Users\Mussy\Desktop\result"
            os.makedirs(final_output_dir, exist_ok=True)
            
            product_file = f"Product_{clean_name}_Data.json"
            product_path = os.path.join(final_output_dir, product_file)
            
            with open(product_path, 'w', encoding='utf-8') as f:
                json.dump(aggregated_data, f, ensure_ascii=False, indent=4)
            
            print(f"✅ 最终聚合数据生成成功")
            print(f"💾 产品数据已保存到: {product_path}")
                
        except Exception as e:
            print(f"❌ 生成最终聚合数据时出错: {e}")
    
    def build_platform_data(self, data):
        """构建平台数据结构"""
        platforms = {}
        
        # 从grabbed数据获取基础平台结构
        if data['grabbed'] and isinstance(data['grabbed'], list) and len(data['grabbed']) > 0:
            base_app_data = data['grabbed'][0]
            platforms = base_app_data.get('Platforms', {})
        
        # 添加用户行为数据
        if data['user_behavior'] and 'Platforms' in data['user_behavior']:
            for platform_name, behavior_data in data['user_behavior']['Platforms'].items():
                if platform_name not in platforms:
                    platforms[platform_name] = {}
                
                # 添加用户行为数据
                if 'User Behavior Data' in behavior_data:
                    platforms[platform_name]['User Behavior by Country'] = behavior_data['User Behavior Data']
        
        return platforms
    
    def run_simple_data_separator(self):
        """运行简单数据分离器"""
        try:
            separator_path = os.path.join("E:\\dataAI", "Simple_Data_Separator.py")
            if os.path.exists(separator_path):
                result = subprocess.run([sys.executable, separator_path], cwd="E:\\dataAI")
                if result.returncode == 0:
                    print("✅ 数据分离成功")
                else:
                    print("❌ 数据分离失败")
            else:
                print("❌ 简单数据分离器不存在")
        except Exception as e:
            print(f"❌ 运行数据分离器失败: {e}")
    
    def cleanup_raw_data(self):
        """清理原始数据文件"""
        print("🧹 清理原始数据文件...")
        
        try:
            main_dir = "E:\\dataAI"
            
            # 删除原始JSON文件
            json_patterns = [
                'Aggregated_Analytics_Data.json',
                'User_Behavior_*.json',
                'PolyBuzz_*.json'
            ]
            
            cleaned_files = 0
            for pattern in json_patterns:
                for file_path in glob.glob(os.path.join(main_dir, pattern)):
                    os.remove(file_path)
                    cleaned_files += 1
                    print(f"🗑️ 删除: {os.path.basename(file_path)}")
            
            print(f"✅ 清理完成，删除了 {cleaned_files} 个原始文件")
            
        except Exception as e:
            print(f"❌ 清理过程中出错: {e}")
    

    def process_all_folders(self):
        """智能处理输入文件夹 - 自动判断单个产品还是多个产品"""
        
        
        # 先检查输入文件夹是否直接包含HTML文件
        html_files_in_root = [f for f in os.listdir(self.base_input_path) 
                             if f.endswith('.html') and os.path.isfile(os.path.join(self.base_input_path, f))]
        
        if html_files_in_root:
            # 如果根目录直接包含HTML文件，说明这是单个产品文件夹
            print("🎯 检测到单个产品模式 - 输入文件夹直接包含HTML文件")
            print("=" * 80)
            success = self.process_product_folder(self.base_input_path)
            
            if success:
                successful_products = [os.path.basename(self.base_input_path)]
                print(f"✅ 产品处理成功")
            else:
                successful_products = []
                print(f"❌ 产品处理失败")
        else:
            # 如果根目录不包含HTML文件，说明是多个产品文件夹的批量模式
            folders = self.get_folders_to_process()
            
            if not folders:
                print(f"❌ 输入文件夹中既没有HTML文件，也没有子文件夹: {self.base_input_path}")
                return
            
            print(f"🎯 检测到批量产品模式 - 找到 {len(folders)} 个产品文件夹")
            print("=" * 80)
            
            successful_products = []
            
            for i, folder_path in enumerate(folders, 1):
                folder_name = os.path.basename(folder_path)
                print(f"\n🚀 [{i}/{len(folders)}] 开始处理产品: {folder_name}")
                print("=" * 80)
                
                try:
                    success = self.process_product_folder(folder_path)
                    if success:
                        successful_products.append(folder_name)
                        print(f"✅ 产品 '{folder_name}' 处理成功")
                    else:
                        print(f"❌ 产品 '{folder_name}' 处理失败")
                except Exception as e:
                    print(f"❌ 处理产品文件夹 '{folder_name}' 时出错: {e}")
                    continue
        
        # 处理完所有产品后，使用简单数据分离器
        if successful_products:
            print(f"\n🔄 使用简单数据分离器处理 {len(successful_products)} 个产品数据...")
            self.run_simple_data_separator()
        
        # 生成总体报告
        self.generate_batch_summary(successful_products)
    
    def generate_batch_summary(self, successful_products):
        """生成批量处理的总结报告"""
        summary = {
            "Batch_Processing_Summary": {
                "Processing_Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Base_Input_Path": self.base_input_path,
                "Base_Output_Path": "E:\\dataAI",  # 最终聚合数据的位置
                "Successful_Products": successful_products,
                "Total_Products_Processed": len(successful_products),
                "Final_Output_Files": []
            }
        }
        
        # 收集最终聚合数据文件
        final_files = [
            "Complete_Products_Data.json",
            "Incomplete_Products_Data.json"
        ]
        
        summary["Batch_Processing_Summary"]["Final_Output_Files"] = final_files
        
        # 保存总结报告到目标目录
        final_output_dir = r"D:\Users\Mussy\Desktop\result"
        os.makedirs(final_output_dir, exist_ok=True)
        summary_path = os.path.join(final_output_dir, 'Batch_Processing_Summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)
        
        print(f"\n🎉 处理完成!")
        print(f"📊 成功处理了 {len(successful_products)} 个产品:")
        for product in successful_products:
            print(f"   ✅ {product}")
        print(f"📊 总结报告: {summary_path}")
        print(f"📁 最终聚合数据: D:\\Users\\Mussy\\Desktop\\result")
        
        # 所有数据已直接输出到目标目录，无需复制
    

def main():
    """主函数"""
    
    # ========================================
    # 🔧 在这里设置您的输入文件夹路径
    # ========================================
    INPUT_FOLDER = r"D:\Users\Mussy\Desktop\input"  # 📂 修改为您的输入文件夹路径
    
    # 可选：设置临时输出路径（最终聚合数据始终保存到 E:\dataAI\）
    TEMP_OUTPUT = r"D:\Users\Mussy\Desktop\result"
    
    # ========================================
    
    if not os.path.exists(INPUT_FOLDER):
        print(f"❌ 输入路径不存在: {INPUT_FOLDER}")
        print("💡 请在脚本中修改 INPUT_FOLDER 变量为正确的路径")
        return
    
    print("🎯 智能产品数据处理器")
    print("=" * 60)
    print(f"📂 输入目录: {INPUT_FOLDER}")
    print(f"📊 最终聚合数据位置: E:\\dataAI\\")
    print(f"📁 临时处理目录: {TEMP_OUTPUT}")
    print("🤖 自动检测: 单个产品 或 批量产品")
    print("=" * 60)
    
    processor = SmartProductProcessor(INPUT_FOLDER, TEMP_OUTPUT)
    processor.process_all_folders()

if __name__ == "__main__":
    main()