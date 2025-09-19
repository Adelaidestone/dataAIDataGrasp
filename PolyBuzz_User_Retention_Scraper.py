import pandas as pd
from bs4 import BeautifulSoup
from lxml import etree
import json
import re # Import regular expression module

# Define the application name explicitly as it's part of the filename, not in table data directly
# APPLICATION_NAME = "PolyBuzz: Chat with AI Friends"

# Mapping for Chinese headers to English headers
HEADER_MAP = {
    '月': 'Month',
    '应用': 'Application',
    '第0天': 'Day 0 Retention',
    '第1天': 'Day 1 Retention',
    '第2天': 'Day 2 Retention',
    '第3天': 'Day 3 Retention',
    '第4天': 'Day 4 Retention',
    '第5天': 'Day 5 Retention',
    '第6天': 'Day 6 Retention',
    '第7天': 'Day 7 Retention',
    '第14天': 'Day 14 Retention',
    '第30天': 'Day 30 Retention',
}

def convert_to_numeric(value_str):
    if not isinstance(value_str, str) or not value_str.strip():
        return value_str # Return as is if not a string or empty

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
    
    # Remove any remaining non-numeric characters that might cause conversion errors
    cleaned_str = ''.join(filter(lambda x: x.isdigit() or x == '.', cleaned_str))

    try:
        if not cleaned_str: # Handle cases where after cleaning, string is empty
            return value_str
        numeric_value = float(cleaned_str) * multiplier
        if is_negative:
            numeric_value = -numeric_value
        return numeric_value # Return as float for percentages
    except ValueError:
        return value_str # Return original if conversion fails

# PLATFORM_COLOR_MAP is not needed for this retention table as it doesn't have line charts
PLATFORM_COLOR_MAP = {}

def extract_retention_table_data(table_wrapper, table_name):
    if not table_wrapper:
        print(f"Could not find the table wrapper for {table_name}.")
        return []

    # Initialize output for this specific table
    table_output_records = []

    # Extract headers
    headers = []

    # Check if it's the app_user_retention_table (monthly data) or publisher_apps_user_retention_table (overall app data)
    is_monthly_table = (table_wrapper.get('data-table-type') == 'app_user_retention_table')

    if is_monthly_table:
        # '月' header for monthly table
        month_header_cell = table_wrapper.find('div', {'data-header-key': 'date'})
        if month_header_cell:
            span_content = month_header_cell.find('span', class_='Tooltip__ContentWrapper-sc-a710cec5-0')
            if span_content:
                headers.append(span_content.get_text(strip=True))
            else:
                headers.append(month_header_cell.get_text(strip=True))
    else:
        # '应用' header for publisher apps table
        app_header_cell = table_wrapper.find('div', {'data-header-key': 'product_id'})
        if app_header_cell:
            headers.append(app_header_cell.get_text(strip=True))

    # Day retention headers (第0天, 第1天, etc.)
    # Find the row containing day retention headers. This might be in a nested div.
    day_retention_headers_row = table_wrapper.find('div', class_=lambda x: x and 'TableHeader__CellRow-sc-194ff62d-2' in x.split() and 'hoHRDw' in x.split())
    if day_retention_headers_row:
        for cell in day_retention_headers_row.find_all('div', class_='TableHeader__CellContent-sc-194ff62d-3'):
            headers.append(cell.get_text(strip=True))

    print(f"Extracted headers (Chinese) for {table_name}: {headers}")
    print(f"Number of extracted headers (Chinese) for {table_name}: {len(headers)}")

    # Data extraction
    fixed_table_grid = table_wrapper.find('div', class_=lambda x: x and 'ReactVirtualized__Table' in x.split() and 'FixedStyledTable' in x.split())
    scrollable_table_grid = table_wrapper.find('div', class_=lambda x: x and 'ReactVirtualized__Table' in x.split() and 'StyledTable' in x.split() and 'FixedStyledTable' not in x.split())

    if fixed_table_grid and scrollable_table_grid:
        fixed_rows = fixed_table_grid.find_all('div', class_='ReactVirtualized__Table__row', attrs={'aria-rowindex': True})
        scrollable_rows = scrollable_table_grid.find_all('div', class_='ReactVirtualized__Table__row', attrs={'aria-rowindex': True})

        print(f"Fixed rows found for {table_name}: {len(fixed_rows)}")
        print(f"Scrollable rows found for {table_name}: {len(scrollable_rows)}")

        min_rows = min(len(fixed_rows), len(scrollable_rows))

        for i in range(min_rows):
            row_data = []
            
            # Extract app name or month based on table type
            if is_monthly_table:
                month_div = fixed_rows[i].find('div', {'data-testid': 'table-cell#date'})
                row_data.append(month_div.get_text(strip=True) if month_div else "")
            else:
                app_name_div = fixed_rows[i].find('div', {'data-testid': 'text-component'})
                row_data.append(app_name_div.get_text(strip=True) if app_name_div else "")

            # Extract day retention percentages
            scroll_row = scrollable_rows[i]
            for retention_day_key in [f'est_retention_day__aggr-{j}' for j in range(8)] + ['est_retention_day__aggr-14', 'est_retention_day__aggr-30']:
                retention_cell = scroll_row.find('div', {'data-key': retention_day_key})
                retention_value_str = "N/A"
                if retention_cell:
                    span_value = retention_cell.find('span', class_='DataMetric__DisplayValue-sc-a50818d6-1')
                    if span_value:
                        retention_value_str = span_value.get_text(strip=True)
                    else:
                        na_span = retention_cell.find('span', class_=lambda x: x and 'NA__Wrapper-sc-7d3243c2-0' in x.split())
                        if na_span:
                            retention_value_str = na_span.get_text(strip=True)
                
                row_data.append(convert_to_numeric(retention_value_str))
            
            table_output_records.append(row_data)
            print(f"Row {i} data length for {table_name}: {len(row_data)}")

    # Adjust headers to include only the desired ones and convert to English
    final_headers = []
    if headers:
        for h in headers:
            final_headers.append(HEADER_MAP.get(h, h))

    print(f"Final headers (English) for {table_name}: {final_headers}")
    print(f"Number of final headers (English) for {table_name}: {len(final_headers)}")

    if table_output_records and final_headers:
        df = pd.DataFrame(table_output_records, columns=final_headers)
        print(f"✅ 成功提取 {table_name} 的表格数据：")
        return df.to_dict(orient='records')
    else:
        print(f"No data to save for {table_name}.")
        return []

html_file_path = r"D:\\Users\\Mussy\\Desktop\\新建文件夹\\PolyBuzz_ Chat with AI Friends _ 用户留存.html"

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

# --- Extract data from the first table (Monthly App Retention) ---
table_wrapper_monthly = soup.find('div', {'data-table-type': 'app_user_retention_table'})
monthly_retention_data = extract_retention_table_data(table_wrapper_monthly, "Monthly App Retention")

# --- Extract data from the second table (Publisher Apps User Retention) ---
table_wrapper_publisher = soup.find('div', {'data-table-type': 'publisher_apps_user_retention_table'})
publisher_retention_data = extract_retention_table_data(table_wrapper_publisher, "Publisher Apps User Retention (Overall)")

# Combine all extracted data into a single JSON object
final_json_output = {
    "Monthly App Retention": monthly_retention_data,
    "Publisher Apps User Retention (Overall)": publisher_retention_data
}

output_json_path = "PolyBuzz_User_Retention_Aggregated_Analytics_Data.json"
with open(output_json_path, 'w', encoding='utf-8') as json_file:
    json.dump(final_json_output, json_file, ensure_ascii=False, indent=4)
print(f"整合后的数据已保存到文件：{output_json_path}")
