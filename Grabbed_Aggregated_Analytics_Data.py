import pandas as pd
from bs4 import BeautifulSoup
from lxml import etree
import json
import re # Import regular expression module

# Mapping for Chinese headers to English headers
HEADER_MAP = {
    '应用': 'Application',
    '平台': 'Platform',
    '下载': 'Downloads',
    '下载变化': 'Downloads Change',
    '累积下载量': 'Cumulative Downloads',
    '累积下载量变化': 'Cumulative Downloads Change',
    '商店收入': 'Store Revenue',
    '商店收入变化': 'Store Revenue Change',
    '活跃用户': 'Active Users',
    '活跃用户变化': 'Active Users Change',
}

def convert_to_numeric(value_str):
    if not isinstance(value_str, str) or not value_str.strip():
        return value_str # Return as is if not a string or empty

    cleaned_str = value_str.replace('$', '').strip()

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
    
    # Remove any remaining non-numeric characters that might cause conversion errors
    cleaned_str = ''.join(filter(lambda x: x.isdigit() or x == '.', cleaned_str))

    try:
        if not cleaned_str: # Handle cases where after cleaning, string is empty
            return value_str
        numeric_value = float(cleaned_str) * multiplier
        if is_negative:
            numeric_value = -numeric_value
        return int(numeric_value) if numeric_value == int(numeric_value) else numeric_value
    except ValueError:
        return value_str # Return original if conversion fails

# Map Highcharts series colors to platforms based on the legend in the image
PLATFORM_COLOR_MAP = {
    "#41A481": "Android", # Assuming green is Google Play
    "#0099F9": "iOS"      # Assuming blue is iOS
}

html_file_path = r"D:\Users\Mussy\Desktop\新建文件夹\Poly.AI - Create AI Chat Bot _ data.ai首页下载量全平台.html"

try:
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
except FileNotFoundError:
    print(f"Error: The file '{html_file_path}' was not found.")
    exit()
except Exception as e:
    print(f"An error occurred while reading the file: {e}")
    exit()

soup = BeautifulSoup(html_content, 'html.parser')

# Initialize grouped_output globally so both table and chart data can add to it
grouped_output = {}

# --- Table Data Extraction ---
table_wrapper = soup.find('div', class_='Table__TableWrapper-sc-5979c7d8-0')

if table_wrapper:
    # Extract headers
    headers = []

    # First header row (for '应用')
    header_row_app = table_wrapper.find('div', class_=lambda x: x and 'TableHeader__StickyTableRow-sc-194ff62d-5' in x.split())
    if header_row_app:
        app_header_cell = header_row_app.find('div', {'data-header-key': 'product_id'})
        if app_header_cell:
            headers.append(app_header_cell.get_text(strip=True))

    # Second header row (for '下载', '累积下载量', '商店收入', '活跃用户')
    data_header_row = table_wrapper.find('div', class_=lambda x: x and 'TableHeader__TableRow-sc-194ff62d-4' in x.split() and 'bAcynv' in x.split())
    if data_header_row:
        for cell in data_header_row.find_all('div', class_='TableHeader__CellContent-sc-194ff62d-3'):
            span_content = cell.find('span', class_='Tooltip__ContentWrapper-sc-a710cec5-0')
            if span_content:
                headers.append(span_content.get_text(strip=True))
            else:
                headers.append(cell.get_text(strip=True))
    
    print(f"Extracted headers (Chinese): {headers}")
    print(f"Number of extracted headers (Chinese): {len(headers)}")

    # Data extraction
    data = []

    # Directly find the fixed and scrollable tables using their distinguishing classes
    fixed_table_grid = table_wrapper.find('div', class_=lambda x: x and 'ReactVirtualized__Table' in x.split() and 'FixedStyledTable' in x.split())
    scrollable_table_grid = table_wrapper.find('div', class_=lambda x: x and 'ReactVirtualized__Table' in x.split() and 'StyledTable' in x.split() and 'FixedStyledTable' not in x.split())

    if fixed_table_grid and scrollable_table_grid:
        fixed_rows = fixed_table_grid.find_all('div', class_='ReactVirtualized__Table__row', attrs={'aria-rowindex': True})
        scrollable_rows = scrollable_table_grid.find_all('div', class_='ReactVirtualized__Table__row', attrs={'aria-rowindex': True})

        print(f"Fixed rows found: {len(fixed_rows)}")
        print(f"Scrollable rows found: {len(scrollable_rows)}")

        min_rows = min(len(fixed_rows), len(scrollable_rows))

        for i in range(min_rows):
            row_data = []
            # Extract application name
            app_name_div = fixed_rows[i].find('div', {'data-testid': 'text-component'})
            row_data.append(app_name_div.get_text(strip=True) if app_name_div else "")

            # Extract platform information (Android/iOS)
            platform_span = fixed_rows[i].find('span', {'data-testid': 'store-image'})
            if platform_span:
                platform_type = platform_span.get('type')
                if platform_type == 'gp':
                    row_data.append("Android")
                elif platform_type == 'ios':
                    row_data.append("iOS")
                else:
                    row_data.append("") # Unknown platform
            else:
                row_data.append("") # Platform information not found

            # Extract metrics from the scrollable table
            scroll_row = scrollable_rows[i]
            
            # Downloads and download change
            download_sum_str = scroll_row.find('div', {'data-key': 'est_download__sum'}).get_text(strip=True) if scroll_row.find('div', {'data-key': 'est_download__sum'}) else ""
            row_data.append(convert_to_numeric(download_sum_str))
            
            download_change_div = scroll_row.find('div', {'data-key': 'value_change(est_download__sum)__aggr'})
            if download_change_div:
                change_value_span = download_change_div.find('span', class_='DataMetric__DisplayValue-sc-a50818d6-1')
                if change_value_span:
                    change_text = change_value_span.get_text(strip=True)
                    if download_change_div.find('div', class_=lambda x: x and 'down' in x.split()):
                        row_data.append(convert_to_numeric("-" + change_text))
                    else:
                        row_data.append(convert_to_numeric(change_text))
                else:
                    row_data.append("")
            else:
                row_data.append("")

            # Cumulative downloads and change
            cumulative_download_aggr_str = scroll_row.find('div', {'data-key': 'est_cumulative_download__aggr'}).get_text(strip=True) if scroll_row.find('div', {'data-key': 'est_cumulative_download__aggr'}) else ""
            row_data.append(convert_to_numeric(cumulative_download_aggr_str))

            cumulative_download_change_div = scroll_row.find('div', {'data-key': 'value_change(est_cumulative_download__aggr)__aggr'})
            if cumulative_download_change_div:
                change_value_span = cumulative_download_change_div.find('span', class_='DataMetric__DisplayValue-sc-a50818d6-1')
                if change_value_span:
                    change_text = change_value_span.get_text(strip=True)
                    if cumulative_download_change_div.find('div', class_=lambda x: x and 'down' in x.split()):
                        row_data.append(convert_to_numeric("-" + change_text))
                    else:
                        row_data.append(convert_to_numeric(change_text))
                else:
                    row_data.append("")
            else:
                row_data.append("")

            # Revenue and revenue change
            revenue_sum_str = scroll_row.find('div', {'data-key': 'est_revenue__sum'}).get_text(strip=True) if scroll_row.find('div', {'data-key': 'est_revenue__sum'}) else ""
            row_data.append(convert_to_numeric(revenue_sum_str))

            revenue_change_div = scroll_row.find('div', {'data-key': 'value_change(est_revenue__sum)__aggr'})
            if revenue_change_div:
                change_value_span = revenue_change_div.find('span', class_='DataMetric__DisplayValue-sc-a50818d6-1')
                if change_value_span:
                    change_text = change_value_span.get_text(strip=True)
                    if revenue_change_div.find('div', class_=lambda x: x and 'down' in x.split()):
                        row_data.append(convert_to_numeric("-" + change_text))
                    else:
                        row_data.append(convert_to_numeric(change_text))
                else:
                    row_data.append("")
            else:
                row_data.append("")

            # Active users and change
            active_users_aggr_str = scroll_row.find('div', {'data-key': 'est_average_active_users__aggr'}).get_text(strip=True) if scroll_row.find('div', {'data-key': 'est_average_active_users__aggr'}) else ""
            row_data.append(convert_to_numeric(active_users_aggr_str))

            active_users_change_div = scroll_row.find('div', {'data-key': 'value_change(est_average_active_users__aggr)__aggr'})
            if active_users_change_div:
                change_value_span = active_users_change_div.find('span', class_='DataMetric__DisplayValue-sc-a50818d6-1')
                if change_value_span:
                    change_text = change_value_span.get_text(strip=True)
                    if active_users_change_div.find('div', class_=lambda x: x and 'down' in x.split()):
                        row_data.append(convert_to_numeric("-" + change_text))
                    else:
                        row_data.append(convert_to_numeric(change_text))
                else:
                    row_data.append("")
            else:
                row_data.append("")

            data.append(row_data)
            print(f"Row {i} data length: {len(row_data)}")

    # Adjust headers to include change values and platform, and convert to English
    final_headers = []
    if headers: # Ensure headers list is not empty before proceeding
        final_headers.append(HEADER_MAP.get(headers[0], headers[0])) # '应用'
        final_headers.append(HEADER_MAP.get("平台", "平台")) # Add Platform header in English
        for h in headers[1:]:
            final_headers.append(HEADER_MAP.get(h, h))
            final_headers.append(HEADER_MAP.get(f"{h}变化", f"{h}变化"))

    print(f"Final headers (English): {final_headers}")
    print(f"Number of final headers (English): {len(final_headers)}")

    if data and final_headers:
        df = pd.DataFrame(data, columns=final_headers)
        print("✅ 成功提取表格数据：")
        
        # Group data by application
        # This grouped_output will be used for both table and chart data
        for record in df.to_dict(orient='records'):
            app_name = record['Application']
            platform = record['Platform']
            
            if app_name not in grouped_output:
                grouped_output[app_name] = {"Application": app_name, "Platforms": {}}
            
            # Create platform-specific data, excluding 'Application' and 'Platform' keys
            platform_specific_data = {k: v for k, v in record.items() if k not in ['Application', 'Platform']}
            grouped_output[app_name]["Platforms"][platform] = platform_specific_data
    else: 
        print("No table data or headers extracted to create DataFrame.")
else: 
    print("Could not find the main table wrapper in the HTML content.")

# --- Line Chart Data Extraction (integrating into grouped_output) ---
# Find the highcharts-series-group which contains all series
highcharts_group = soup.find('g', class_='highcharts-series-group')

if highcharts_group:
    # Find all individual series, but skip the first one if it's a base line (stroke-width 0)
    # The series we are interested in in the HTML are 'highcharts-series-1', 'highcharts-series-2', etc.
    series_elements = highcharts_group.find_all('g', class_=re.compile(r'highcharts-series highcharts-series-\d+ highcharts-line-series'))

    line_chart_extracted_count = 0
    for series_g in series_elements:
        # Get the stroke color from the 'highcharts-graph' path within this series
        graph_path = series_g.find('path', class_='highcharts-graph')
        if graph_path and graph_path.get('stroke') and float(graph_path.get('stroke-width', 1)) > 0: # Ensure it's an actual visible line
            series_color = graph_path['stroke']
            platform_for_series = PLATFORM_COLOR_MAP.get(series_color, "Unknown")
            
            # Find the corresponding markers group for this series
            series_id_match = re.search(r'highcharts-series-(\d+)', series_g['class'][1])
            if series_id_match:
                series_number = series_id_match.group(1)
                markers_class = f'highcharts-markers highcharts-series-{series_number} highcharts-line-series highcharts-tracker'
                markers_g = highcharts_group.find('g', class_=markers_class)

                if markers_g:
                    chart_points = markers_g.find_all('path', class_='highcharts-point', attrs={'aria-label': True})

                    for point in chart_points:
                        aria_label = point['aria-label']
                        match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December) (\d{4}), ([\d,]+)\. (.*)', aria_label)
                        if match:
                            month_str, year, downloads_str, app_info_from_label = match.groups()
                            
                            downloads = int(downloads_str.replace(',', ''))

                            print(f"  Chart: Original aria_label: {aria_label}")
                            print(f"  Chart: Extracted app_info_from_label: '{app_info_from_label}'")
                            
                            # Clean app name from label (remove platform suffix if present and any trailing dot)
                            app_name_raw = app_info_from_label.strip()
                            if app_name_raw.endswith('.'):
                                app_name_raw = app_name_raw[:-1] # Remove trailing dot
                            
                            app_platform_match = re.search(r'(.*?)( \((Google Play|iOS)\))?', app_name_raw)
                            
                            # Ensure app_name is correctly extracted for grouping. If it's empty, default to the known app name.
                            temp_app_name = app_platform_match.group(1).strip() if app_platform_match else app_name_raw.strip()
                            if not temp_app_name: # If it's still empty or not found, assume it's the known app
                                app_name = "PolyBuzz: Chat with AI Friends"
                            else:
                                app_name = temp_app_name
                            
                            print(f"  Chart: Cleaned app_name for grouping: '{app_name}'")
                            print(f"  Chart: Platform for series: '{platform_for_series}'")

                            # Ensure the application structure exists in grouped_output
                            if app_name not in grouped_output:
                                grouped_output[app_name] = {"Application": app_name, "Platforms": {}}
                            if platform_for_series not in grouped_output[app_name]["Platforms"]:
                                grouped_output[app_name]["Platforms"][platform_for_series] = {}

                            # Initialize 'Recent Three Month Downloads' at the platform level if it doesn't exist
                            if "Recent Three Month Downloads" not in grouped_output[app_name]["Platforms"][platform_for_series]:
                                grouped_output[app_name]["Platforms"][platform_for_series]["Recent Three Month Downloads"] = []
                            
                            grouped_output[app_name]["Platforms"][platform_for_series]["Recent Three Month Downloads"].append({
                                "Month": month_str,
                                "Year": int(year),
                                # "Platform": platform_for_series, # Platform is implied by parent key
                                "Downloads": downloads
                            })
                            line_chart_extracted_count += 1
    
    if line_chart_extracted_count > 0:
        print(f"✅ 成功提取并整合折线图数据 ({line_chart_extracted_count} 个数据点)。")
    else:
        print("No line chart data extracted or integrated.")
else:
    print("Could not find the highcharts-series-group for line chart data.")

# --- Final JSON Output ---
if grouped_output:
    final_json_output = list(grouped_output.values())

    output_json_path = "Aggregated_Analytics_Data.json"
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(final_json_output, json_file, ensure_ascii=False, indent=4)
    print(f"整合后的数据已保存到文件：{output_json_path}")
else:
    print("No data (table or line chart) to save.")