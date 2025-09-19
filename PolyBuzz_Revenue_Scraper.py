import pandas as pd
from bs4 import BeautifulSoup
from lxml import etree
import json
import re # Import regular expression module

# Mapping for Chinese headers to English headers
HEADER_MAP = {
    '设备': 'Device',
    '平均商店收入': 'Average Store Revenue',
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
# Not used for this specific request, but kept for potential future use or context.
PLATFORM_COLOR_MAP = {
    "#41A481": "Android", # Assuming green is Google Play
    "#0099F9": "iOS"      # Assuming blue is iOS
}

html_file_path = r"D:\\Users\\Mussy\\Desktop\\新建文件夹\\PolyBuzz_ Chat with AI Friends _ data.ai收入.html"

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

    # The header for '设备' is in the first row with data-header-key="device_code"
    header_row_device = table_wrapper.find('div', class_=lambda x: x and 'TableHeader__StickyTableRow-sc-194ff62d-5' in x.split())
    if header_row_device:
        device_header_cell = header_row_device.find('div', {'data-header-key': 'device_code'})
        if device_header_cell:
            headers.append(device_header_cell.get_text(strip=True))

    # The header for '平均商店收入' is in the second row with data-header-key="est_revenue__avg"
    data_header_row = table_wrapper.find('div', class_=lambda x: x and 'TableHeader__TableRow-sc-194ff62d-4' in x.split() and 'bAcynv' in x.split())
    if data_header_row:
        avg_revenue_header_cell = data_header_row.find('div', {'data-header-key': 'est_revenue__avg'})
        if avg_revenue_header_cell:
            span_content = avg_revenue_header_cell.find('span', class_='Tooltip__ContentWrapper-sc-a710cec5-0')
            if span_content:
                headers.append(span_content.get_text(strip=True))
            else:
                headers.append(avg_revenue_header_cell.get_text(strip=True))
    
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
            # Extract device name
            device_name_div = fixed_rows[i].find('div', {'data-testid': 'text-component'})
            row_data.append(device_name_div.get_text(strip=True) if device_name_div else "")

            # Extract Average Store Revenue
            avg_revenue_str = scrollable_rows[i].find('div', {'data-key': 'est_revenue__avg'}).get_text(strip=True) if scrollable_rows[i].find('div', {'data-key': 'est_revenue__avg'}) else ""
            row_data.append(convert_to_numeric(avg_revenue_str))

            data.append(row_data)
            print(f"Row {i} data length: {len(row_data)}")

    # Adjust headers to include only the desired ones and convert to English
    final_headers = []
    if headers:
        final_headers.append(HEADER_MAP.get(headers[0], headers[0])) # '设备'
        if len(headers) > 1: # Ensure '平均商店收入' exists
            final_headers.append(HEADER_MAP.get(headers[1], headers[1]))

    print(f"Final headers (English): {final_headers}")
    print(f"Number of final headers (English): {len(final_headers)}")

    if data and final_headers:
        df = pd.DataFrame(data, columns=final_headers)
        print("✅ 成功提取表格数据：")
        
        # No grouping needed as we only have one row for "所有Android设备" and one metric
        final_json_output = df.to_dict(orient='records')

        output_json_path = "PolyBuzz_Revenue_Aggregated_Analytics_Data.json"
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(final_json_output, json_file, ensure_ascii=False, indent=4)
        print(f"整合后的数据已保存到文件：{output_json_path}")
    else:
        print("No data (table) to save.")
else:
    print("Could not find the main table wrapper in the HTML content.")
