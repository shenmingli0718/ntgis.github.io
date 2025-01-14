import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import folium
from folium import Marker
import os
import base64
import io
import dash_bootstrap_components as dbc
from geopy.geocoders import Nominatim
import geopandas as gpd
import pandas as pd
from userdefinefun import get_unique_zip_area_df
from userdefinefun import create_map1, create_map2
from userdefinefun import style_function
from userdefinefun import create_vp_dropdown_options
from dash import no_update
from flask import request
from flask_cors import CORS
from flask import jsonify

# 移除重複的郵遞區號及區域名稱組合，並進行排序
unique_zip_area = get_unique_zip_area_df()

# 將資料轉換為 Dash 下拉選單格式
dropdown_options = [
    {'label': f"{row['郵遞區號']} {row['區域名稱']}", 'value': row['郵遞區號']}
    for _, row in unique_zip_area.iterrows()
]

# 將景點名稱資料轉換為 Dash 下拉選單格式
# 讀取 "新北市觀光旅遊景點(中文).csv" 檔案
global selected_df
#selected_df = pd.read_csv('newtpe_tourist_att.csv', encoding='utf-8')

#vp_dropdown_options = [
#    {'label': f"{idx+1} {row['Name']}", 'value': row['Name']}
#    for idx, row in selected_df.iterrows()
#]

# 建立 Dash 應用
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# C#app = dash.Dash(__name__, suppress_callback_exceptions=True)
###
import socket

def get_host_ip():
    """
    使用 socket 獲取主機的本地 IP 地址
    """
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print("hostname = ", hostname)
    print("local_ip = ", local_ip)
    return local_ip

# 獲取主機 IP 地址
server_ip = get_host_ip()
###
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script>
            // 定義伺服器的 IP 地址，供 JavaScript 使用
            const server_ip = "{server_ip}";
            // 父窗口監聽子窗口的 postMessage 消息
            window.addEventListener('message', function(event) {
                // 確保消息格式正確，並檢查 action
                if (event.data && event.data.action === 'updateMap') {
                    console.log('收到來自子窗口的更新地圖請求，ID: ', event.data.id);
                    // 通知 Dash 的後端邏輯
                    DashRenderer.dispatchEvent({
                        type: 'updateMap',
                        payload: event.data.id
                    });
                }
            });
        </script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""
# 初始化地圖函數
##
# 自定義樣式函數
def create_map(name):
    
    # 讀取大台北鄉鎮市區界圖shpe file(含台北市、新北市)
    Big_Taipei_data = gpd.read_file('./Taipei.shp', encoding='utf-8')
    Ｎew_Taipei_data = Big_Taipei_data[(Big_Taipei_data['COUNTYNAME']=='新北市')]
    ##
    # 設定地圖中心點和縮放級別，這裡以新北市的經緯度為例
    map_center = [24.989868, 121.656173]  # 新北市中心位置約在石碇區石碇里

    #mymap = folium.Map(location=map_center, zoom_start=12)

    # 將 Shapefile 轉為 GeoJSON 並添加到地圖
    #folium.GeoJson(New_Taipei_data, style_function=style_function).add_to(mymap)
    ##
    # calling the Nominatim tool
    loc = Nominatim(user_agent="Get NewTaipei", timeout=5)
    # entering the location name
    getLoc = loc.geocode(name, country_codes = "TW")
    #getLoc = loc.geocode(name)
    #getLoc = loc.geocode(name)
    #popup=getLoc.address + '\n' + str(getLoc.latitude) + '\n' + str(getLoc.longitude) 
    #
    if getLoc is not None:
        if name != "石碇區石碇里":
            popup=getLoc.address + "<br>" + str(getLoc.latitude) + "<br>" + str(getLoc.longitude)
        else:
            popup="新北市中心位置：" + "<br>" + getLoc.address + "<br>" + str(getLoc.latitude) + "<br>" + str(getLoc.longitude)

        mymap = folium.Map(location=[getLoc.latitude, getLoc.longitude], zoom_start=12)
        Marker([getLoc.latitude, getLoc.longitude], popup=popup).add_to(mymap)
        # 將 Shapefile 轉為 GeoJSON 並添加到地圖
        folium.GeoJson(New_Taipei_data, style_function=style_function).add_to(mymap)
        error_msg=""
    else:
        getLoc = loc.geocode(name)
        if getLoc is not None:
            popup=getLoc.address + "<br>" + str(getLoc.latitude) + "<br>" + str(getLoc.longitude)
            mymap = folium.Map(location=[getLoc.latitude, getLoc.longitude], zoom_start=12)
            Marker([getLoc.latitude, getLoc.longitude], popup=popup).add_to(mymap)
            # 將 Shapefile 轉為 GeoJSON 並添加到地圖
            folium.GeoJson(New_Taipei_data, style_function=style_function).add_to(mymap)
            error_msg=""
        else:
            mymap = folium.Map(location=map_center, zoom_start=12)
            error_msg="名稱:" + name + " 地理編碼錯誤致搜尋失敗"

    # 將 Shapefile 轉為 GeoJSON 並添加到地圖
    #folium.GeoJson(New_Taipei_data, style_function=style_function).add_to(mymap)
    ##   
    # 創建 Folium 地圖
    #folium_map = folium.Map(location=[lat, lon], zoom_start=12)

    #folium.Marker([getLoc.latitude, getLoc.longitude], popup=popup).add_to(mymap)

    mymap.save("mymap.html")
    #
    # 將地圖保存為 HTML 字串
    map_io = io.BytesIO()
    mymap.save(map_io, close_file=False)
    map_html = map_io.getvalue().decode()

    return map_html, error_msg, [] 

# App Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
            dcc.Location(id='url', refresh=False),
            html.Div(id='page-content')
            ]),
            #
            html.H4("互動式 GIS 系統", className='text-center mb-4'),
            dbc.Label("請輸入世界各地任一地點名稱:"),
            dcc.Input(id='name-input', type='text', value=""),            
            html.Br(),
            dbc.Button("繪製地圖(世界範圍)", id="generate-map-btn1", color="primary", className="mt-2"),
            dbc.Label("-----------------------------------"),
            html.Br(),
            html.Div([
            html.Label("新北市觀光旅遊景點位置查詢"),
            html.Label("點選新北市郵遞區號及區域名稱"),
            html.Br(),
            dcc.Dropdown(
                id='zip-area-dropdown',
                options=dropdown_options,
                placeholder="選擇新北市郵遞區號及區域名稱",
                ),
            ]),
            #
            dbc.Button("繪製地圖(新北市範圍)", id="generate-map-btn2", color="primary", className="mt-2"),
            #dbc.Button("區景點瀏覽", id="viewpoint-qry-btn", color="primary", className="mt-2"),
            html.Br(),
            html.Br(),
            dcc.Dropdown(
                id='viewpoint-dropdown',
            #   options=vp_dropdown_options,
                placeholder="選擇區內景點名稱",
                ),
            html.Br(),
            #html.Div(id='error-message', style={'color': 'red', 'margin-top': '10px'}),
            html.Div(id='error-message', style={'color': 'red', 'marginTop': '10px'}),
        ], width=3),
        dbc.Col([
            html.Iframe(id='map', width='100%', height='600'),
        ], width=9),
        dcc.Store(id='selected-location'),  # 儲存選擇的景點資訊
        dcc.Store(id='map-update-data')  # 用于触发地图更新的存储组件
        
    ])
], fluid=True)

# Callback 更新地圖
@app.callback(
    [Output('map', 'srcDoc'), Output('error-message', 'children'),
     Output('viewpoint-dropdown', 'options')],  # 更新地圖和錯誤訊息
    #[Input('generate-map-btn', 'n_clicks')],
    #[Input('latitude-input', 'value'), Input('longitude-input', 'value')]
    Input('generate-map-btn1', 'n_clicks'),  # 按鈕點擊事件觸發
                                             # 使用 Input 監聽按鈕點擊事件：按鈕的點擊事件觸發地圖更新。
    Input('generate-map-btn2', 'n_clicks'), 
    Input('zip-area-dropdown', 'value'),
    State('name-input', 'value'),   # 名稱或地址 # 使用 State 來儲存緯度和經度數值：避免在按鈕點擊之前緯度和經度變化時觸發回調。
    State('viewpoint-dropdown', 'value')
    #state('viewpoint-dropdown', 'value')
)
##
def update_map_and_dropdown(map_clicks1, map_clicks2, zipcode, name, viewpoint):
    # ***** Initialize default values
    #map_html = "<p>No map data available.</p>"  # Default or empty map HTML
    #error_msg = ""  # No error initially
    #viewpoint_options = []  # Default empty options
    #
    ctx = dash.callback_context  # 用於判斷哪個輸入觸發了回調
    triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]
    # 如果是 zip-area-dropdown 觸發的回調，更新 viewpoint-dropdown 的選項
    if triggered_input == 'zip-area-dropdown':
        return create_vp_dropdown_options(zipcode) 
    elif triggered_input in ['generate-map-btn1', 'generate-map-btn2']:
    # 當按鈕點擊後，根據 name 和 zipcode 判斷要生成哪種地圖
        if name:
            if map_clicks1 is not None:
                return create_map(name)  # 優先使用 name
        elif zipcode:
            if map_clicks2 is not None:
                if not viewpoint: 
                    return create_map1(zipcode,server_ip)
                    print("trace 1 on create_map1")
                else:
                    return create_map2(zipcode,viewpoint,server_ip)
        else:
            return no_update, no_update, no_update   # 必須
    else:
        # 初始狀態，當 n_clicks 為 None 時顯示默認地圖
        name = name if name else "石碇區石碇里"  # 預設地點
        return create_map(name)
            
                
    #    else:
    #        if qry_clicks is not None:
    #            return create_qry(zipcode)
    #else:
        # 如果都沒有提供，顯示一個默認的地圖或錯誤訊息
        #return None, "Please provide either a name or a zipcode."
        #return None, "請輸入地點名稱或點選郵遞區號及區域名稱", [ ]
###
from dash import no_update

@app.callback(
    Output('map-update-data', 'data'),
    Input('map-update-data', 'data'),
    prevent_initial_call=True
)
def update_map_trigger(data):
    print('(update_map_trigger) 被觸發，data: ', data)
    if data:
        return data
    return no_update


@app.callback(
    Output('map', 'srcDoc', allow_duplicate=True),
    Input('map-update-data', 'data'),  # 监听 Store 数据的变化
    prevent_initial_call=True
)
def refresh_map(data):
    print('(refresh_map) 被觸發，data: ', data)
    if data:
        # 解析传递的 zip 和 id，这里假设 zip 是固定值
        zip_code = '999'  # 示例值
        location_id = data
        print('(rfresh_map) data = ', data)
        return create_map2(zip_code, location_id)[0]
    return no_update

##@app.server.route('/message', methods=['POST'])
##def receive_message():
##    message = request.json
##    if message.get('action') == 'updateMap':
##        location_id = message.get('id')
##        print('(receive_message) message.get("id") = ', location_id)
##        # 模擬觸發回調的行為
##        app.layout.children.append(html.Div(id='map-update-data', data=location_id))
##        # 更新地图触发数据
##        return jsonify({"status": "success", "data": location_id}), 200
##    return jsonify({"status": "ignored"}), 200
###
@app.server.route('/message', methods=['POST'])
def receive_message():
    try:
        message = request.json
        if message.get('action') == 'updateMap':
            location_id = message.get('id')
            print('(receive_message) message.get("id") = ', location_id)
            
             # 手動觸發 `map-update-data` 的變更
            with app.server.app_context():
                data_store = {'data': location_id}  # 包裝成符合 Dash Store 的格式

            # 模擬觸發回調的行為
            return jsonify({"status": "success", "data": location_id}), 200
        else:
            return jsonify({"status": "failed", "error": "Invalid action"}), 400
    except Exception as e:
        print("Error in /message:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

###
@app.server.route('/get_host', methods=['GET'])
def get_host():
    return request.host.split(':')[0]  # 返回伺服器的 IP 地址
###
#
# 頁面佈局1：主頁面包含Folium地圖和Marker按鈕操作
def layout_main():
    return html.Div([
        html.H1("景點地圖管理系統"),
        #html.Iframe(id="map", srcDoc=open("mymap.html", "r").read(), width="100%", height="600"),
    ])

# 頁面佈局2：編輯資料頁面
def layout_edit():
    return html.Div([
        html.H1("景點編輯資料"),
        dcc.Input(id='edit-location-id', type='text', placeholder='景點ID', readOnly=True),
        dcc.Input(id='transport-info', type='text', placeholder='交通資訊'),
        dcc.Input(id='opening-hours', type='text', placeholder='開放時間'),
        dcc.Input(id='ticket-info', type='text', placeholder='門票資訊'),
        html.Button('儲存資料', id='save-button'),
        html.Div(id='save-status')
    ])

# 頁面佈局3：照片上傳頁面
def layout_upload():
    return html.Div([
        html.H1("景點照片上傳"),
        dcc.Input(id='upload-location-id', type='text', placeholder='景點ID', readOnly=True),
        dcc.Upload(id='upload-photo', children=html.Button('上傳照片')),
        html.Div(id='upload-photo-status')
    ])

# 頁面佈局4：照片下載頁面
def layout_download():
    return html.Div([
        html.H1("景點照片下載"),
        dcc.Input(id='download-location-id', type='text', placeholder='景點ID', readOnly=True),
        html.Button('下載照片', id='download-button'),
        dcc.Download(id='download-photo')
    ])
#
##
## 路由到不同頁面
##
##@app.callback(
##    Output('page-content', 'children'),
##    Input('url', 'pathname')
##)
##def display_page(pathname):
##    print("(display_page) pathname= ", pathname) 
##    if pathname.startswith('/upload'):
##        location_id = pathname.split('/')[-1]
##        return html.Div([html.H3(f"上傳照片 for 景點 {location_id}"), html.Button("關閉視窗", id='close-window')])
##    elif pathname.startswith('/download'):
##        location_id = pathname.split('/')[-1]
##        return html.Div([html.H3(f"下載照片 for 景點 {location_id}"), html.Button("關閉視窗", id='close-window')])
##    elif pathname.startswith('/edit'):
##        location_id = pathname.split('/')[-1]
##        return html.Div([html.H3(f"填寫相關訊息 for 景點 {location_id}"), html.Button("關閉視窗", id='close-window')])
##    #return "404 Page Not Found"
##    return ""

###

#start
# 運行應用
if __name__ == '__main__':
    #app.run_server(debug=True)
    app.run_server(host='0.0.0.0', debug=True, port=8799, use_reloader=False)
    #app.run_server(mode="inline", port=8799, use_reloader=False)
    
# 將應用靜態導出為 HTML 文件
app.run_server(export=True, directory='exported')