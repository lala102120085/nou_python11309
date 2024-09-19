import requests
import zipfile
import os
import pandas as pd
import json
import ipywidgets as widgets
from IPython.display import display
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import font_manager, rcParams

# 天氣 API 設定
API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
API_KEY = "CWA-D5B056EA-33C1-4099-9FE8-C6282F14A951"

# 實價登錄資料 URL
ZIP_URL = "https://plvr.land.moi.gov.tw//Download?type=zip&fileName=lvr_landcsv.zip"
DATA_DIR = "real_estate_data"
ZIP_FILE_PATH = os.path.join(DATA_DIR, "lvr_landcsv.zip")

# 台灣各主要城市名稱
city_names = [
    '臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市',
    '基隆市', '新竹市', '嘉義市', '新竹縣', '苗栗縣', '彰化縣',
    '南投縣', '雲林縣', '嘉義縣', '屏東縣', '宜蘭縣', '花蓮縣',
    '臺東縣', '澎湖縣', '金門縣', '連江縣'
]

# 確保實價登錄資料夾存在
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 下載並解壓縮實價登錄資料
def download_and_extract_data():
    print("下載實價登錄資料中...")
    response = requests.get(ZIP_URL)
    with open(ZIP_FILE_PATH, "wb") as zip_file:
        zip_file.write(response.content)
    print("解壓縮資料...")
    with zipfile.ZipFile(ZIP_FILE_PATH, "r") as zip_ref:
        zip_ref.extractall(DATA_DIR)

# 讀取指定城市的 CSV 資料
def read_city_data(file_name):
    file_path = os.path.join(DATA_DIR, file_name)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding='utf-8')
        if df['總價元'].dtype != 'int64' and df['總價元'].dtype != 'float64':
            df['總價元'] = pd.to_numeric(df['總價元'], errors='coerce')
        return df
    else:
        print(f"找不到 {file_name} 的資料")
        return None

# 查詢指定城市的房屋交易資料
def query_real_estate(city, min_price, max_price):
    city_files = {
        '臺北市': 'a_lvr_land_a.csv',
        '新北市': 'f_lvr_land_a.csv',
        '桃園市': 'h_lvr_land_a.csv',
        '臺中市': 'b_lvr_land_a.csv',
        '臺南市': 'd_lvr_land_a.csv',
        '高雄市': 'e_lvr_land_a.csv',
        '基隆市': 'c_lvr_land_a.csv',
        '宜蘭縣': 'g_lvr_land_a.csv',
        '嘉義市': 'i_lvr_land_a.csv',
        '新竹縣': 'j_lvr_land_a.csv',
        '苗栗縣': 'k_lvr_land_a.csv',
        '南投縣': 'm_lvr_land_a.csv',
        '彰化縣': 'n_lvr_land_a.csv',
        '新竹市': 'o_lvr_land_a.csv',
        '雲林縣': 'p_lvr_land_a.csv',
        '嘉義縣': 'q_lvr_land_a.csv',
        '屏東縣': 't_lvr_land_a.csv',
        '花蓮縣': 'u_lvr_land_a.csv',
        '台東縣': 'v_lvr_land_a.csv',
        '金門縣': 'w_lvr_land_a.csv',
        '澎湖縣': 'x_lvr_land_a.csv',
    }

    if city not in city_files:
        print(f"抱歉，目前不支援 {city} 的資料查詢")
        return

    # 讀取資料
    file_name = city_files[city]
    df = read_city_data(file_name)
    if df is None:
        return

    # 篩選價格範圍
    filtered_df = df[(df['總價元'] >= min_price * 10000) & (df['總價元'] <= max_price * 10000)]

    # 返回篩選後的結果
    return filtered_df

    # 顯示篩選後的結果
    if not filtered_df.empty:
        print(f"符合條件的房屋交易資料：")
        display(filtered_df[['鄉鎮市區', '土地位置建物門牌', '總價元', '單價元平方公尺']])
    else:
        print(f"沒有符合價格範圍 {min_price} - {max_price} 萬元的交易資料。")

# 查詢天氣
def get_weather(city):
    params = {
        "Authorization": API_KEY,
        "locationName": city
    }
    response = requests.get(API_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        if 'records' in data and 'location' in data['records']:
            location_data = data['records']['location']

            for location in location_data:
                if location['locationName'] == city:
                    weather_elements = location['weatherElement']
                    weather_description = weather_elements[0]['time'][0]['parameter']['parameterName']
                    max_temp = weather_elements[4]['time'][0]['parameter']['parameterName']
                    min_temp = weather_elements[2]['time'][0]['parameter']['parameterName']

                    return f"{city} 的天氣狀況：{weather_description}\n最高溫度：{max_temp}°C\n最低溫度：{min_temp}°C"
        else:
            return f"無法取得 {city} 的天氣資料。"
    else:
        return "API 請求失敗，請檢查您的 API 金鑰和請求參數。"

# 天氣介面按鈕事件
def on_weather_button_click(b):
    city = city_selector.value
    result = get_weather(city)
    weather_output.value = result

# 繪製泡泡圖的函數
def plot_bubble_chart(df, city):
    # 清理數據：移除缺失或無效的數據
    df = df.dropna(subset=['總價元', '建物移轉總面積平方公尺', '鄉鎮市區'])
    
    # 按區域分組，計算每個區域的交易總數
    area_count = df['鄉鎮市區'].value_counts()
    
    # 將每個房屋的區域交易總數作為泡泡大小
    df['泡泡大小'] = df['鄉鎮市區'].apply(lambda x: area_count.get(x, 0))
    
    # 繪製泡泡圖
    plt.figure(figsize=(12, 8))
    
    # 使用不同顏色繪製每個區域的泡泡
    unique_areas = df['鄉鎮市區'].unique()
    colors = plt.cm.get_cmap('tab20', len(unique_areas))  # 使用 'tab20' 顏色映射
    color_map = {area: colors(i) for i, area in enumerate(unique_areas)}
    
    for area in unique_areas:
        area_data = df[df['鄉鎮市區'] == area]
        plt.scatter(
            area_data['建物移轉總面積平方公尺'],  # x軸：建物面積
            area_data['總價元'],          # y軸：總價
            s=area_data['泡泡大小'] * 10,     # 泡泡大小：區域交易總數
            alpha=0.5,
            color=color_map[area],         #區域多寡
            label=area
        )
    
    # 設定圖表標題與軸標籤
    plt.title(f"{city} 各區域房屋交易數據")
    plt.xlabel('建物移轉總面積 (平方公尺)')
    plt.ylabel('總價 (元)')
    
    # 添加圖例
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1), title="區域")
    
    # 顯示圖表
    plt.tight_layout()
    plt.show()

    # 繪製顏色比照圖
    plot_color_legend(color_map)

# 繪製顏色比照圖
def plot_color_legend(color_map):
    """
    繪製顏色比照圖
    """
    fig, ax = plt.subplots(figsize=(12, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    for i, (area, color) in enumerate(color_map.items()):
        rect = patches.Rectangle((0.1 * i, 0.5), 0.1, 0.4, linewidth=1, edgecolor='black', facecolor=color)
        ax.add_patch(rect)
        plt.text(0.1 * i + 0.05, 0.5, area, va='center', ha='center', fontsize=10)
    
    plt.show()

# 房屋查詢按鈕事件
def on_real_estate_button_click(b):
    city = city_selector.value
    min_price = min_price_slider.value
    max_price = max_price_slider.value
    
    # 查詢房屋資料
    filtered_df = query_real_estate(city, min_price, max_price)
    
    # 確認 df 不為空
    if filtered_df is not None and not filtered_df.empty:
        # 顯示篩選後的表格資料
        display(filtered_df[['鄉鎮市區', '土地位置建物門牌', '總價元', '單價元平方公尺']])
        
        # 繪製泡泡圖
        plot_bubble_chart(filtered_df, city)
    else:
        print(f"沒有符合價格範圍 {min_price} - {max_price} 萬元的交易資料。")


# 天氣查詢介面
city_selector = widgets.Dropdown(
    options=city_names,
    value='臺北市',
    description='選擇城市: ',
)

weather_output = widgets.Textarea(
    value='',
    placeholder='天氣資訊將顯示在這裡',
    description='天氣狀況: ',
    layout=widgets.Layout(width='30%', height='80px')
)

weather_button = widgets.Button(description="查詢天氣")
weather_button.on_click(on_weather_button_click)

# 房屋查詢介面
min_price_slider = widgets.IntSlider(
    value=1000,
    min=0,
    max=5000,
    step=50,
    description='最低價格(萬): '
)

max_price_slider = widgets.IntSlider(
    value=2000,
    min=0,
    max=5000,
    step=50,
    description='最高價格(萬): '
)

real_estate_button = widgets.Button(description="查詢房屋交易")
real_estate_button.on_click(on_real_estate_button_click)

# 顯示天氣查詢與房屋查詢的 UI
display(city_selector, weather_button, weather_output)
display(min_price_slider, max_price_slider, real_estate_button)

# 主程式下載房屋實價登錄資料
download_and_extract_data()
