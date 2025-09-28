import pandas as pd
from bs4 import BeautifulSoup
import json
import re
import os

def extract_product_name_from_html(soup):
    """
    Extract product name from HTML content
    """
    # Method 1: Try to extract from page title
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text(strip=True)
        # Extract product name from title (assuming format like "ProductName | 用户留存" or similar)
        if '|' in title_text:
            product_name = title_text.split('|')[0].strip()
            return product_name
        elif '_' in title_text:
            product_name = title_text.split('_')[0].strip()
            return product_name
    
    # Method 2: Try to extract from breadcrumb or navigation elements
    breadcrumb = soup.find('nav', class_='breadcrumb') or soup.find('div', class_='breadcrumb')
    if breadcrumb:
        links = breadcrumb.find_all('a')
        if len(links) > 1:
            return links[-2].get_text(strip=True)  # Usually the second to last is the app name
    
    # Method 3: Try to extract from header or h1 tags
    h1_tag = soup.find('h1')
    if h1_tag:
        h1_text = h1_tag.get_text(strip=True)
        if '用户留存' not in h1_text and '留存' not in h1_text and '使用行为' not in h1_text:
            return h1_text
    
    # Method 4: Try to extract from meta tags
    meta_title = soup.find('meta', attrs={'name': 'title'}) or soup.find('meta', attrs={'property': 'og:title'})
    if meta_title:
        content = meta_title.get('content', '')
        if '|' in content:
            return content.split('|')[0].strip()
    
    # Method 5: Try to extract from specific app info elements
    app_info = soup.find('div', class_=lambda x: x and ('app-info' in x or 'product-info' in x))
    if app_info:
        app_name = app_info.find('span') or app_info.find('div')
        if app_name:
            return app_name.get_text(strip=True)
    
    return "Unknown Product"

def extract_platform_from_html(soup):
    """
    Extract platform information from HTML content
    """
    # Method 1: Try to extract platform from meta information
    meta_tags = soup.find_all('meta')
    for meta in meta_tags:
        content = meta.get('content', '').lower()
        if 'google play' in content or 'android' in content:
            return "Google Play"
        elif 'app store' in content or 'ios' in content:
            return "App Store"
    
    # Method 2: Look for platform indicators in the HTML content
    html_text = soup.get_text().lower()
    if 'google play' in html_text or 'android' in html_text:
        return "Google Play"
    elif 'app store' in html_text or 'ios' in html_text:
        return "App Store"
    
    # Method 3: Try to extract from specific platform elements
    platform_elements = soup.find_all(['div', 'span'], class_=lambda x: x and ('platform' in x.lower() or 'store' in x.lower()))
    for element in platform_elements:
        text = element.get_text().lower()
        if 'google play' in text or 'android' in text:
            return "Google Play"
        elif 'app store' in text or 'ios' in text:
            return "App Store"
    
    return "Unknown Platform"

# Mapping for Chinese headers to English headers (will be populated based on user's request)
HEADER_MAP = {
    '国家/地区': 'Country/Region',
    '活跃用户': 'Active Users',
    '用户份额': 'User Share (%)',
    '第1天留存率': 'Day 1 Retention (%)',
    '第7天留存率': 'Day 7 Retention (%)',
    '第30天留存率': 'Day 30 Retention (%)',
    '平均时间/用户': 'Avg Time Per User',
    '会话': 'Sessions',
    '平均会话时长': 'Avg Session Duration',
    '平均活跃天数': 'Avg Active Days',
    '活跃天数百分比': 'Active Days (%)',
    '活动天数%': 'Active Days (%)',  # Direct mapping for the extracted field name
}

# Platform-specific data extraction configuration
PLATFORM_DATA_CONFIG = {
    "Android": {
        "data_points": 8,
        "metrics": [
            '活跃用户',
            '用户份额',
            '第1天留存率',
            '第7天留存率',
            '第30天留存率',
            '平均时间/用户',
            '平均活跃天数',
            '活跃天数百分比',
            '会话',
            '平均会话时长'
        ]
    },
    "iOS": {
        "data_points": 6,
        "metrics": [
            '活跃用户',
            '用户份额',
            '第1天留存率', 
            '第7天留存率',
            '第30天留存率',
            '平均时间/用户'
        ]
    }
}

def convert_to_numeric(value_str):
    if not isinstance(value_str, str) or not value_str.strip():
        return value_str

    # Keep original string for later reference
    original_str = value_str.strip()
    cleaned_str = value_str.replace('$', '').replace('%', '').strip()

    is_negative = False
    if cleaned_str.startswith('-'):
        is_negative = True
        cleaned_str = cleaned_str[1:]

    multiplier = 1
    if '亿' in cleaned_str:
        multiplier = 100_000_000
        cleaned_str = cleaned_str.replace('亿', '')
    elif '万' in cleaned_str:
        multiplier = 10_000
        cleaned_str = cleaned_str.replace('万', '')
    elif '千' in cleaned_str:
        multiplier = 1_000
        cleaned_str = cleaned_str.replace('千', '')
    
    # Handle time durations like '1h 30m 15s' or '30m'
    if re.match(r'^(?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s)?$', cleaned_str):
        total_seconds = 0
        hours_match = re.search(r'(\d+)h', cleaned_str)
        minutes_match = re.search(r'(\d+)m', cleaned_str)
        seconds_match = re.search(r'(\d+)s', cleaned_str)

        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60
        if seconds_match:
            total_seconds += int(seconds_match.group(1))
        return total_seconds

    # Extract only digits and decimal point
    cleaned_str = ''.join(filter(lambda x: x.isdigit() or x == '.', cleaned_str))

    try:
        if not cleaned_str:
            return original_str  # Return original string if cannot be converted
        
        # Convert to float first
        numeric_value = float(cleaned_str) * multiplier
        if is_negative:
            numeric_value = -numeric_value
        
        # Preserve original decimal precision
        # If original has no decimal point and result is whole number, return int
        if '.' not in original_str and numeric_value.is_integer():
            return int(numeric_value)
        else:
            # For decimals, preserve the original precision
            return numeric_value
            
    except ValueError:
        return original_str  # Return original string if conversion fails

# HTML file paths for both platforms
html_files = {
    "Android": r"D:\\Users\\Mussy\\Desktop\\新建文件夹\\PolyBuzz_ Chat with AI Friends _ data.ai使用行为8幻神.html",
    "iOS": r"D:\\Users\\Mussy\\Desktop\\新建文件夹\\PolyBuzz_ Chat with AI Friends _ data.ai苹果用户行为.html"
}

def process_behavior_html_file(file_path, platform_name):
    """
    Process a single HTML file and return the extracted user behavior data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"⚠️ 文件未找到: {file_path}")
        return None
    except Exception as e:
        print(f"❌ 读取文件时出错 {file_path}: {e}")
        return None

    soup = BeautifulSoup(html_content, 'html.parser')
    
    print(f"\n🔍 处理 {platform_name} 平台用户行为数据...")

    # Extract product name from HTML
    product_name = extract_product_name_from_html(soup)
    print(f"提取到的产品名: {product_name}")

    # Extract platform from HTML
    platform = extract_platform_from_html(soup)
    print(f"提取到的平台: {platform}")
    
    # Show platform-specific configuration
    platform_config = PLATFORM_DATA_CONFIG.get(platform_name, PLATFORM_DATA_CONFIG["iOS"])
    print(f"📊 {platform_name} 平台配置: 提取 {platform_config['data_points']} 个数据点")
    print(f"📋 数据指标: {', '.join(platform_config['metrics'])}")

    # --- Data Extraction Logic Goes Here ---
    table_wrapper = soup.find('div', {'data-table-type': 'table_change(__table__$app_usage_country)'})
    extracted_data = []

    if table_wrapper:
        headers = []
        data_keys_map = {}
        header_cells = table_wrapper.select('div.TableHeader__CellWrapper-sc-194ff62d-1[data-header-key]')
        for cell in header_cells:
            header_text = cell.find('div', class_='TableHeader__CellContent-sc-194ff62d-3').get_text(strip=True)
            data_key = cell['data-header-key']
            headers.append(header_text)
            data_keys_map[header_text] = data_key
        
        # If no headers found via TableHeader, create a manual mapping based on observed data-key attributes
        if not data_keys_map:
            print("DEBUG: No headers found via TableHeader, using manual mapping")
            # Manual mapping based on observed data-key attributes in the HTML
            manual_data_keys = {
                '活跃用户': 'est_average_active_users__aggr',
                '用户份额': 'est_average_active_users_country_share__aggr', 
                '第1天留存率': 'est_retention_d1__aggr',
                '第7天留存率': 'est_retention_d7__aggr',
                '第30天留存率': 'est_retention_d30__aggr',
                '平均时间/用户': 'est_average_time_per_user__aggr',
                '平均活跃天数': 'est_average_active_days__aggr',
                '活跃天数百分比': 'est_percentage_active_days__aggr'
            }
            
            # Debug: Try to find any missing data-key attributes from the scrollable table
            print("DEBUG: Checking for additional data-key attributes...")
            if scrollable_table_grid:
                first_row = scrollable_table_grid.find('div', class_='ReactVirtualized__Table__row', attrs={'aria-rowindex': True})
                if first_row:
                    all_cells = first_row.find_all('div', {'data-key': True})
                    found_keys = [cell.get('data-key') for cell in all_cells if cell.get('data-key')]
                    print(f"DEBUG: All data-key attributes found: {found_keys}")
                    
                    # Add any missing keys to manual mapping
                    missing_keys = set(found_keys) - set(manual_data_keys.values())
                    for missing_key in missing_keys:
                        print(f"DEBUG: Found unmapped data-key: {missing_key}")
                        # Try to guess the Chinese name based on the key
                        if 'session' in missing_key.lower():
                            manual_data_keys['会话'] = missing_key
                        elif 'duration' in missing_key.lower():
                            manual_data_keys['会话时长'] = missing_key
                        elif 'time' in missing_key.lower() and 'session' in missing_key.lower():
                            manual_data_keys['平均会话时长'] = missing_key
            data_keys_map = manual_data_keys
        
        # Filter out empty headers and map to English
        english_headers = [HEADER_MAP.get(h, h) for h in headers if h.strip()]

        fixed_table_grid = table_wrapper.find('div', class_=lambda x: x and 'ReactVirtualized__Table' in x.split() and 'FixedStyledTable' in x.split())
        scrollable_table_grid = table_wrapper.find('div', class_=lambda x: x and 'ReactVirtualized__Table' in x.split() and 'StyledTable' in x.split() and 'FixedStyledTable' not in x.split())

        if fixed_table_grid and scrollable_table_grid:
            fixed_rows = fixed_table_grid.find_all('div', class_='ReactVirtualized__Table__row', attrs={'aria-rowindex': True})
            scrollable_rows = scrollable_table_grid.find_all('div', class_='ReactVirtualized__Table__row', attrs={'aria-rowindex': True})

            print(f"DEBUG: Found {len(fixed_rows)} fixed rows and {len(scrollable_rows)} scrollable rows.")

            min_rows = min(len(fixed_rows), len(scrollable_rows))

            for i in range(min_rows):
                row_data = {}
                
                # Extract country/region from fixed_rows
                country_name = "N/A"
                # Looking for the div that contains the country name, which has data-testid="text-component"
                try:
                    country_div = fixed_rows[i].find('div', {'data-testid': 'table-cell#country_code'}).find('div', {'data-testid': 'text-component'})
                    if country_div:
                        country_name = country_div.get_text(strip=True)
                except:
                    print(f"DEBUG: Could not find country_div for row {i}")
                
                row_data[HEADER_MAP.get('国家/地区', '国家/地区')] = country_name
                print(f"DEBUG: Extracted Country/Region for row {i}: '{country_name}'")
                
                # Extract data from scrollable_rows
                scroll_row = scrollable_rows[i]
                
                # Get platform-specific metrics to extract
                platform_config = PLATFORM_DATA_CONFIG.get(platform_name, PLATFORM_DATA_CONFIG["iOS"])  # Default to iOS config
                target_data_points = platform_config["data_points"]
                
                # For Android, use the first 8 meaningful data keys found
                if platform_name == "Android":
                    # Get all available data keys and filter out non-data keys
                    exclude_keys = ['selectableRow', 'country_code', 'value_change']
                    all_available_keys = []
                    for v in data_keys_map.values():
                        if v and not any(exclude in v for exclude in exclude_keys):
                            # Only include keys that contain '__aggr' (actual data keys)
                            if '__aggr' in v:
                                all_available_keys.append(v)
                    
                    data_keys_to_extract = all_available_keys[:target_data_points]
                    # Update metrics list to match found keys
                    extracted_metrics = [k for k, v in data_keys_map.items() if v in data_keys_to_extract]
                else:
                    # For iOS, use the original logic
                    metrics_to_extract = platform_config["metrics"]
                    data_keys_to_extract = [
                        data_keys_map.get(metric) for metric in metrics_to_extract
                    ]
                    data_keys_to_extract = [key for key in data_keys_to_extract if key is not None]
                    extracted_metrics = [k for k, v in data_keys_map.items() if v in data_keys_to_extract]
                
                if i == 0:  # Only print debug info for first row
                    print(f"DEBUG: Platform {platform_name} - Looking for {target_data_points} data points")
                    print(f"DEBUG: Extracted metrics: {extracted_metrics}")
                    print(f"DEBUG: Found {len(data_keys_to_extract)} data keys: {data_keys_to_extract}")

                for original_data_key in data_keys_to_extract:
                    if original_data_key:
                        cell_wrapper = scroll_row.find('div', {'data-key': original_data_key})
                        cell_value = "N/A"
                        if cell_wrapper:
                            # Search for any span or div with actual data recursively within the cell wrapper
                            found_value = False
                            for child in cell_wrapper.find_all(['span', 'div'], recursive=True):
                                text = child.get_text(strip=True)
                                # Capture any meaningful text, including N/A (since N/A is valid data indicating unavailable)
                                if text and text != '-' and not text.strip().startswith('NaN'):
                                    cell_value = text
                                    found_value = True
                                    break
                            
                            # If no specific span/div found, try to get text directly from the cell wrapper
                            if not found_value:
                                cell_value = cell_wrapper.get_text(strip=True)
                        
                        # Convert the original_data_key back to its English header name for the row_data dict
                        chinese_header = next((k for k, v in data_keys_map.items() if v == original_data_key), original_data_key)
                        
                        # Handle special case for percentage active days field
                        if chinese_header == original_data_key and original_data_key == 'est_percentage_active_days__aggr':
                            chinese_header = '活跃天数百分比'
                        elif chinese_header == '活动天数%':
                            chinese_header = '活跃天数百分比'
                        
                        english_header = HEADER_MAP.get(chinese_header, chinese_header)
                        
                        row_data[english_header] = convert_to_numeric(cell_value)
                
                if row_data:
                    extracted_data.append(row_data)

        else:
            print("DEBUG: Could not find fixed_table_grid or scrollable_table_grid.")

    else:
        print("Could not find the target table wrapper.")

    return {
        "Application": product_name,
        "Platform": platform,
        "User Behavior Data": extracted_data
    }

# Process all HTML files
all_platform_data = {}
for platform, file_path in html_files.items():
    print(f"\n{'='*60}")
    print(f"🚀 开始处理 {platform} 平台用户行为数据...")
    print(f"{'='*60}")
    
    platform_data = process_behavior_html_file(file_path, platform)
    if platform_data:
        all_platform_data[platform] = platform_data
        print(f"✅ {platform} 平台数据处理完成")
    else:
        print(f"❌ {platform} 平台数据处理失败")

# Save data for each platform separately and create a combined file
print(f"\n{'='*60}")
print("💾 保存数据文件...")
print(f"{'='*60}")

for platform, data in all_platform_data.items():
    if platform == "Android":
        output_path = "User_Behavior_Aggregated_Analytics_Data.json"
    else:
        output_path = f"User_Behavior_{platform}_Aggregated_Analytics_Data.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print(f"✅ {platform} 数据已保存到: {output_path}")
    except Exception as e:
        print(f"❌ 保存 {platform} 数据时出错: {e}")

# Create a combined summary file that Data_Aggregator.py can find
if all_platform_data:
    combined_data = {
        "Application": next(iter(all_platform_data.values()))["Application"],
        "Platforms": all_platform_data
    }
    
    combined_output_path = "User_Behavior_Combined_Analytics_Data.json"
    try:
        with open(combined_output_path, 'w', encoding='utf-8') as json_file:
            json.dump(combined_data, json_file, ensure_ascii=False, indent=4)
        print(f"✅ 合并数据已保存到: {combined_output_path}")
    except Exception as e:
        print(f"❌ 保存合并数据时出错: {e}")

# Also save to unified file for user convenience
output_dir = r"D:\Users\Mussy\Desktop\result"
os.makedirs(output_dir, exist_ok=True)

if all_platform_data:
    # Create unified data structure
    unified_data = {
        "Application": next(iter(all_platform_data.values()))["Application"],
        "Data_Type": "User Behavior Analytics",
        "Generated_Time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Total_Platforms": len(all_platform_data),
        "Platforms": {}
    }
    
    # Add platform data with detailed information
    for platform_name, platform_data in all_platform_data.items():
        platform_config = PLATFORM_DATA_CONFIG.get(platform_name, PLATFORM_DATA_CONFIG["iOS"])
        
        unified_data["Platforms"][platform_name] = {
            "Platform": platform_data["Platform"],
            "Data_Points_Count": platform_config["data_points"],
            "Metrics_Extracted": platform_config["metrics"],
            "Data": platform_data["User Behavior Data"]
        }
    
    # Save to unified file
    unified_output_path = os.path.join(output_dir, "User_Behavior_Unified_Analytics_Data.json")
    try:
        with open(unified_output_path, 'w', encoding='utf-8') as json_file:
            json.dump(unified_data, json_file, ensure_ascii=False, indent=2)
        print(f"✅ 统一数据也已保存到: {unified_output_path}")
        print(f"📊 包含 {len(all_platform_data)} 个平台的数据")
        for platform, data in all_platform_data.items():
            config = PLATFORM_DATA_CONFIG.get(platform, PLATFORM_DATA_CONFIG["iOS"])
            print(f"   - {platform}: {config['data_points']} 个数据点")
    except Exception as e:
        print(f"❌ 保存统一数据时出错: {e}")
else:
    print("⚠️ 没有数据需要保存")

print(f"\n🎉 所有处理完成！成功处理了 {len(all_platform_data)} 个平台的数据")
