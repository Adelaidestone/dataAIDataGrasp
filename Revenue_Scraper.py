import pandas as pd
from bs4 import BeautifulSoup
from lxml import etree
import json
import re # Import regular expression module

def extract_product_name_from_html(soup):
    """
    Extract product name from HTML content
    """
    # Method 1: Try to extract from page title
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text(strip=True)
        # Extract product name from title (assuming format like "ProductName | 收入" or similar)
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
        if '收入' not in h1_text and '用户留存' not in h1_text and '留存' not in h1_text and '使用行为' not in h1_text:
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

# Mapping for Chinese headers to English headers
HEADER_MAP = {
    '设备': 'Device',
    '平均商店收入': 'Average Store Revenue',
}

def convert_to_numeric(value_str):
    if not isinstance(value_str, str) or not value_str.strip():
        return value_str # Return as is if not a string or empty

    # Keep original string for later reference
    original_str = value_str.strip()
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
            return original_str
        
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
        return original_str # Return original if conversion fails

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

# Extract product name from HTML
product_name = extract_product_name_from_html(soup)
print(f"提取到的产品名: {product_name}")

# Extract platform from HTML
platform = extract_platform_from_html(soup)
print(f"提取到的平台: {platform}")

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
        
        # Include product name and platform in the final output
        final_json_output = {
            "Application": product_name,
            "Platform": platform,
            "Revenue Data": df.to_dict(orient='records')
        }

        output_json_path = "PolyBuzz_Revenue_Aggregated_Analytics_Data.json"
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(final_json_output, json_file, ensure_ascii=False, indent=4)
        print(f"整合后的数据已保存到文件：{output_json_path}")
    else:
        print("No data (table) to save.")
else:
    print("Could not find the main table wrapper in the HTML content.")
