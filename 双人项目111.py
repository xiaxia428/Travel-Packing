import streamlit as st
import requests
import os
import pandas as pd
from datetime import datetime, timedelta

def load_env_vars():
    # 优先从 Streamlit Cloud Secrets 读取（部署时安全）
    try:
        for key in ['DEEPSEEK_API_KEY', 'LLM_BASE_URL', 'LLM_MODEL', 'OPENWEATHER_API_KEY', 'AMAP_API_KEY']:
            if key in st.secrets:
                os.environ[key] = st.secrets[key]
    except Exception:
        pass
    
    # 本地开发时从 .env 文件读取
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    # 只在环境变量不存在时才从 .env 加载（优先使用 Secrets）
                    if key not in os.environ:
                        os.environ[key] = value.strip()

load_env_vars()

# 页面配置
st.set_page_config(
    page_title="🎒 智能旅行打包助手 Pro",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 美化的CSS样式
st.markdown("""
<style>
    /* 全局样式 */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 主标题样式 */
    .main-header {
        background: linear-gradient(90deg, #11998e, #38ef7d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        padding: 1rem 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 卡片样式 */
    .card {
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: none;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.15);
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(90deg, #11998e, #38ef7d);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.4);
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(17, 153, 142, 0.6);
    }
    
    /* 进度条样式 */
    .stProgress > div > div {
        background: linear-gradient(90deg, #11998e, #38ef7d);
        border-radius: 10px;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .metric-number {
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    /* 提示卡片 */
    .tip-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    /* 天气卡片 */
    .weather-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
    }
    
    /* 分类标签 */
    .category-tag {
        display: inline-block;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        margin: 0.3rem;
        font-size: 0.9rem;
    }
    
    .tag-必需品 { background: #ff6b6b; color: white; }
    .tag-衣物 { background: #4ecdc4; color: white; }
    .tag-电子设备 { background: #45b7d1; color: white; }
    .tag-洗漱用品 { background: #96ceb4; color: white; }
    .tag-药品 { background: #dda0dd; color: white; }
    .tag-其他 { background: #95a5a6; color: white; }
    
    /* 动画效果 */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fadeIn {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* 成功提示 */
    .success-banner {
        background: linear-gradient(90deg, #00b09b, #96c93d);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ------------------------------
# 天气API功能
# ------------------------------
def get_coordinates(city, api_key):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data:
                return data[0]["lat"], data[0]["lon"], data[0].get("country", "")
    except:
        pass
    return None, None, None


def get_weather(city):
    # 仅读取侧边栏用户输入密钥，不再读取环境变量
    api_key = st.session_state.get("weather_api_key", "")
    
    if not api_key:
        return None, None, None, "请在侧边栏填写OpenWeather天气API密钥"

    lat, lon, country = get_coordinates(city, api_key)
    
    if lat is None:
        return None, None, None, f"无法找到城市：{city}"

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&lang=zh_cn&units=metric"
    
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        
        if res.status_code == 200:
            temp = data["main"]["temp"]
            weather = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            icon = data["weather"][0]["icon"]
            return temp, weather, humidity, wind_speed, data
        elif res.status_code == 401:
            return None, None, None, "你输入的API Key 无效或未激活"
        else:
            return None, None, None, f"错误：{res.status_code}"
    except Exception as e:
        return None, None, None, f"网络错误：{str(e)}"


# ------------------------------
# 智能打包清单生成
# ------------------------------
def generate_packing_list(days, season, activity, has_rain, is_hot, is_cold, budget):
    categories = {
        "证件": ["身份证 / 护照", "学生证 / 老年证", "签证", "机票/火车票", "酒店预订确认单", "保险单"],
        "电子产品": ["手机", "充电器", "充电宝", "耳机", "相机", "平板电脑"],
        "衣物": [],
        "洗漱用品": ["牙刷", "牙膏", "洗发水", "沐浴露", "洗面奶", "护肤品", "化妆品"],
        "药品": ["创可贴", "感冒药", "肠胃药", "退烧药", "晕车药", "个人处方药"],
        "日用品": ["纸巾", "湿巾", "口罩", "墨镜", "雨伞/雨衣", "水杯", "零食"]
    }
    
    # 基础衣物
    if days <= 2:
        clothes = ["内衣裤×2", "袜子×2", "上衣×2", "裤子×1"]
    elif days <= 5:
        clothes = ["内衣裤×3", "袜子×3", "上衣×3", "裤子×2", "外套×1"]
    else:
        clothes = ["内衣裤×5", "袜子×5", "上衣×5", "裤子×3", "外套×1", "睡衣×1"]
        if days >= 7:
            clothes += ["洗衣液", "衣架"]
    
    # 季节衣物
    if season == "春季":
        clothes += ["薄外套", "长袖衬衫", "针织衫", "轻薄羽绒服"]
    elif season == "夏季":
        clothes += ["短袖T恤", "短裤", "防晒衣", "凉鞋", "泳衣"]
        if is_hot:
            clothes += ["防晒霜 SPF50+", "冰袖", "遮阳帽", "小风扇"]
    elif season == "秋季":
        clothes += ["长袖上衣", "牛仔裤", "轻薄外套", "围巾", "帽子"]
    elif season == "冬季":
        clothes += ["厚羽绒服", "保暖内衣", "毛衣", "保暖裤", "围巾", "手套", "帽子", "保暖袜"]
        if is_cold:
            clothes += ["暖宝宝", "保温杯", "润唇膏", "护手霜"]
    
    # 活动衣物
    if activity == "海滩":
        clothes += ["泳衣", "沙滩裤", "拖鞋", "防晒衣", "大檐帽"]
    elif activity == "徒步登山":
        clothes += ["登山鞋", "速干衣", "登山袜", "背包", "冲锋衣"]
    elif activity == "商务出差":
        clothes += ["正装", "领带/领结", "商务衬衫", "皮鞋", "公文包"]
    elif activity == "城市观光":
        clothes += ["舒适的运动鞋", "休闲装", "双肩包"]
    elif activity == "露营":
        clothes += ["帐篷", "睡袋", "防潮垫", "头灯", "野外餐具"]
    
    # 下雨添加
    if has_rain:
        clothes += ["雨衣", "防水鞋套"]
    
    categories["衣物"] = clothes
    
    # 活动特定物品
    if activity == "海滩":
        categories["日用品"] += ["防晒霜", "晒后修复", "防水手机袋", "沙滩垫"]
    elif activity == "徒步登山":
        categories["日用品"] += ["登山杖", "指南针", "地图", "头灯", "瑞士军刀"]
    elif activity == "商务出差":
        categories["日用品"] += ["名片", "笔记本", "签字笔", "U盘", "笔记本电脑"]
        categories["药品"] += ["口气清新剂", "领带夹"]
    
    # 预算相关
    if budget == "穷游":
        categories["日用品"] += ["泡面", "压缩饼干", "水壶"]
    elif budget == "舒适":
        categories["日用品"] += ["零食", "书籍", "眼罩"]
    elif budget == "豪华":
        categories["日用品"] += ["品牌护肤品", "香薰", "高档零食", "纪念品袋"]
    
    return categories


# ------------------------------
# 辅助函数：获取分类图标
# ------------------------------
def get_category_icon(category):
    icons = {
        "证件": "🪪",
        "电子产品": "📱",
        "衣物": "👕",
        "洗漱用品": "🧴",
        "药品": "💊",
        "日用品": "🎒",
    }
    return icons.get(category, "📦")


# ------------------------------
# 旅行小贴士
# ------------------------------
def get_tips(season, activity, has_rain, is_hot, is_cold, days):
    tips = []
    
    # 季节建议
    if season == "夏季":
        tips.append("☀️ 夏季炎热，多喝水，避免中暑")
        tips.append("🧴 记得携带防晒霜，每2小时补涂一次")
        tips.append("🌡️ 选择透气轻薄的衣服")
    elif season == "冬季":
        tips.append("❄️ 冬季寒冷，注意保暖，特别是手脚")
        tips.append("🧣 携带润肤霜，防止皮肤干裂")
        tips.append("🚶 穿防滑鞋，注意路面结冰")
    elif season == "春季":
        tips.append("🌸 春季易过敏，随身带抗过敏药")
        tips.append("🧥 早晚温差大，带件外套")
    elif season == "秋季":
        tips.append("🍂 秋季干燥，多喝水和吃水果")
        tips.append("🧣 带上围巾，早晚温差大")
    
    # 活动建议
    if activity == "海滩":
        tips.append("🏖️ 最佳游玩时间是早上或傍晚，避免正午")
        tips.append("🐚 注意海边的礁石和海洋生物")
        tips.append("📸 带好防水套保护电子设备")
    elif activity == "徒步登山":
        tips.append("🥾 选择合适的登山鞋和袜子")
        tips.append("💧 徒步中要多喝水，每20分钟补充一次")
        tips.append("🗺️ 提前下载离线地图")
        tips.append("📱 告诉家人朋友你的行程")
    elif activity == "商务出差":
        tips.append("💼 提前整理好正装，避免褶皱")
        tips.append("📋 检查所有文件是否准备齐全")
        tips.append("🕐 提前规划路线，留出缓冲时间")
    elif activity == "城市观光":
        tips.append("🚶 穿舒适的鞋子，每天可能走很多路")
        tips.append("🗺️ 提前了解当地交通，使用交通APP")
        tips.append("📸 热门景点提前预约门票")
    
    # 天气建议
    if has_rain:
        tips.append("🌧️ 雨天路滑，小心摔倒")
        tips.append("☂️ 随身带伞，最好准备雨衣")
    if is_hot:
        tips.append("🥵 高温天气，避免剧烈运动")
        tips.append("🚰 多喝含电解质的饮料")
    if is_cold:
        tips.append("🥶 注意保暖，防止冻伤")
        tips.append("🍵 喝热茶或姜汤暖身")
    
    # 通用建议
    tips.append("📱 提前下载必要的APP和离线地图")
    tips.append("💳 确认银行卡可以在国外使用")
    tips.append("🔌 准备转换插头（如果去国外）")
    tips.append("📦 液体物品要符合航空公司规定")
    
    if days >= 7:
        tips.append("🧺 超过7天建议准备洗衣液和衣架")
        tips.append("💊 可以考虑带些常用药品以防万一")
    
    return tips


# ------------------------------
# 紧急联系人模板
# ------------------------------
def get_emergency_contacts():
    return {
        "国内": [
            ("急救电话", "120"),
            ("报警电话", "110"),
            ("火警电话", "119"),
            ("旅游投诉", "12301"),
        ],
        "常用": [
            ("家人电话", "____________"),
            ("酒店电话", "____________"),
            ("航空公司", "____________"),
            ("保险公司", "____________"),
        ]
    }


# ------------------------------
# 地图和景点推荐功能
# ------------------------------
def get_amap_iframe(city_name, width="100%", height=400):
    """生成高德地图iframe嵌入代码"""
    amap_key = os.environ.get('AMAP_API_KEY', 'e7504e0b778d4f34bd5b3741d0557793')
    
    coords = {"lat": 39.9042, "lng": 116.4074}
    try:
        geocode_url = f"https://restapi.amap.com/v3/geocode/geo?address={city_name}&key={amap_key}"
        response = requests.get(geocode_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1' and data.get('geocodes'):
                location = data['geocodes'][0]['location']
                lng, lat = map(float, location.split(','))
                coords = {"lat": lat, "lng": lng}
    except Exception as e:
        pass
    
    iframe_url = f"https://amap.com/embed?zoom=11&lat={coords['lat']}&lng={coords['lng']}&markers=pos:{coords['lng']},{coords['lat']},name:{city_name}&key={amap_key}"
    
    return f"""
    <iframe 
        src="{iframe_url}" 
        width="{width}" 
        height="{height}" 
        frameborder="0" 
        style="border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);"
    ></iframe>
    """


def search_hot_spots(city_name, limit=10):
    """搜索城市热门景点"""
    amap_key = os.environ.get('AMAP_API_KEY', 'e7504e0b778d4f34bd5b3741d0557793')
    spots = []
    
    try:
        search_url = f"https://restapi.amap.com/v3/place/text?keywords={city_name}热门景点&city={city_name}&types=110000&key={amap_key}&offset={limit}&page=1"
        response = requests.get(search_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1' and data.get('pois'):
                for poi in data['pois'][:limit]:
                    spot_detail = get_spot_detail(poi.get('id', ''))
                    
                    spots.append({
                        "name": poi.get('name', ''),
                        "type": poi.get('type', '').split(';')[1] if ';' in poi.get('type', '') else poi.get('type', '景点'),
                        "rating": spot_detail.get('rating', 4.5),
                        "tags": spot_detail.get('tags', ['推荐']),
                        "address": poi.get('address', ''),
                        "location": poi.get('location', ''),
                        "photos": spot_detail.get('photos', []),
                        "summary": spot_detail.get('summary', ''),
                    })
    except Exception as e:
        pass
    
    return spots


def get_spot_detail(spot_id):
    """获取景点详细信息"""
    amap_key = os.environ.get('AMAP_API_KEY', 'e7504e0b778d4f34bd5b3741d0557793')
    detail = {"rating": 4.5, "tags": [], "photos": [], "summary": ""}
    
    try:
        detail_url = f"https://restapi.amap.com/v3/place/detail?id={spot_id}&key={amap_key}"
        response = requests.get(detail_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1' and data.get('pois'):
                poi = data['pois'][0]
                detail['rating'] = float(poi.get('rating', '4.5'))
                detail['tags'] = poi.get('tag', '').split('|') if poi.get('tag') else ['推荐']
                detail['summary'] = poi.get('introduction', '')
                
                if poi.get('photos'):
                    detail['photos'] = [photo.get('url', '') for photo in poi['photos'][:3]]
    except Exception as e:
        pass
    
    return detail


# ------------------------------
# 主界面
# ------------------------------
st.markdown('<h1 class="main-header">🎒 智能旅行打包助手 Pro</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: white; font-size: 1.2rem; margin-bottom: 2rem;">✈️ 让每一次旅行都轻松愉快 🌟</p>', unsafe_allow_html=True)

# 侧边栏配置
with st.sidebar:
    st.markdown("## 🔑 天气API密钥")
    weather_user_key = st.text_input(
        "OpenWeather API Key",
        value="",
        type="password",
        help="请输入你自己的OpenWeather密钥，必填才能查询天气",
        key="input_weather_key"
    )
    # 将用户输入密钥存入session
    st.session_state["weather_api_key"] = weather_user_key.strip()
    
    st.markdown("---")
    st.markdown("## 📝 行程信息")
    
    dest = st.text_input("🏙️ 目的地城市", placeholder="如：上海、三亚、伦敦")
    col1, col2 = st.columns(2)
    with col1:
        days = st.number_input("📅 天数", min_value=1, max_value=30, value=3)
    with col2:
        people = st.number_input("👥 人数", min_value=1, max_value=10, value=1)
    
    season = st.selectbox("🌡️ 季节", ["春季", "夏季", "秋季", "冬季"])
    activity = st.selectbox("🎯 主要活动", ["城市观光", "海滩", "徒步登山", "商务出差", "露营", "走亲访友"])
    
    # 初始预算（结合人数）
    col3, col4 = st.columns(2)
    with col3:
        initial_budget = st.number_input(
            "💵 初始预算（元/人）",
            min_value=0,
            value=1000,
            step=100,
            help="输入每人计划的初始预算"
        )
    with col4:
        total_budget_display = people * initial_budget
        st.metric("💼 总预算", f"¥{total_budget_display:,.0f}")
    
    # 预算等级
    budget = st.select_slider("💰 预算等级", options=["穷游", "经济", "舒适", "豪华"], value="舒适")
    
    weather_tips = st.checkbox("📡 获取实时天气", value=True)
    gen = st.button("✨ 智能生成清单", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📊 统计信息")
    if "items" in st.session_state:
        total = len(st.session_state.get("all_items", []))
        packed = st.session_state.get("packed_count", 0)
        st.info(f"📦 总物品：{total}\n✅ 已打包：{packed}\n📈 进度：{int(packed/total*100) if total > 0 else 0}%")


# 主内容区域
if gen or "categories" in st.session_state:
    if gen:
        # 获取天气信息
        weather_info = None
        humidity = None
        wind_speed = None
        
        if weather_tips and dest:
            result = get_weather(dest)
            if result[0] is not None:
                temp, weather_info, humidity, wind_speed, data = result
            else:
                weather_msg = result[3]
                st.warning(f"⚠️ {weather_msg}")
                temp = None
            has_rain = weather_info and ("雨" in str(weather_info) or "雪" in str(weather_info))
            is_hot = temp and temp >= 30
            is_cold = temp and temp <= 5
        else:
            has_rain = False
            is_hot = season == "夏季"
            is_cold = season == "冬季"
            temp = None
            weather_info = None
        
        # 生成清单
        categories = generate_packing_list(days, season, activity, has_rain, is_hot, is_cold, budget)
        
        # 保存到session
        st.session_state.categories = categories
        st.session_state.dest = dest
        st.session_state.temp = temp
        st.session_state.weather = weather_info
        st.session_state.humidity = humidity
        st.session_state.wind_speed = wind_speed
        st.session_state.all_items = []
        st.session_state.packed_count = 0
    
    # 显示天气信息卡片
    if weather_tips and st.session_state.get("temp"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="weather-card">
                <h3>🌡️ 温度</h3>
                <div class="metric-number">{st.session_state.temp}°C</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="weather-card">
                <h3>🌤️ 天气</h3>
                <div style="font-size: 1.5rem;">{st.session_state.weather}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            if st.session_state.humidity:
                st.markdown(f"""
                <div class="weather-card">
                    <h3>💧 湿度</h3>
                    <div class="metric-number">{st.session_state.humidity}%</div>
                </div>
                """, unsafe_allow_html=True)
        with col4:
            if st.session_state.wind_speed:
                st.markdown(f"""
                <div class="weather-card">
                    <h3>🌬️ 风速</h3>
                    <div class="metric-number">{st.session_state.wind_speed} m/s</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    # 目的地和行程信息
    st.markdown(f"""
    <div class="card animate-fadeIn">
        <h2>🧳 {st.session_state.dest} 之旅</h2>
        <p style="color: #666; font-size: 1.1rem;">
            📅 {days} 天 | 👥 {people} 人 | 🎯 {activity} | 💰 {budget}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tab界面
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 物品清单", "💡 旅行贴士", "📞 紧急联系人", "🗺️ 旅游路线", "📤 导出分享"])
    
    # Tab 1: 物品清单
    with tab1:
        st.markdown("### 📦 分类物品清单（可编辑）")
        
        all_items = []
        item_keys = {}  # 用于跟踪物品键的映射
        
        for category, items in st.session_state.categories.items():
            st.markdown(f"#### {get_category_icon(category)} {category}")
            
            df_items = pd.DataFrame({"物品": items})
            edited_df = st.data_editor(
                df_items,
                num_rows="dynamic",
                use_container_width=True,
                key=f"editor_{category}"
            )
            edited_items = edited_df["物品"].dropna().tolist()
            
            # 分类统计
            col1, col2 = st.columns([3, 1])
            with col1:
                for idx, item in enumerate(edited_items):
                    # 使用索引确保每个键唯一
                    item_key = f"item_{category}_{idx}"
                    st.checkbox(f"  {item}", key=item_key)
                    item_keys[f"{item}_{idx}"] = item_key
            with col2:
                packed_count = sum(1 for idx, item in enumerate(edited_items) if st.session_state.get(f"item_{category}_{idx}", False))
                total_count = len(edited_items)
                progress = packed_count / total_count if total_count > 0 else 0
                st.progress(progress)
                st.caption(f"{packed_count}/{total_count}")
            
            all_items.extend(edited_items)
            st.markdown("---")
        
        st.session_state.all_items = all_items
        
        # 添加自定义物品
        st.markdown("### ➕ 添加自定义物品")
        
        # 获取所有已添加的物品（用于提示）
        all_existing_items = []
        for category, items in st.session_state.categories.items():
            all_existing_items.extend(items)
        
        # 显示已添加物品的提示
        if all_existing_items:
            with st.expander("📋 查看已添加的物品", expanded=False):
                # 按分类显示
                for category, items in st.session_state.categories.items():
                    if items:
                        items_str = "、".join(items)
                        st.markdown(f"**{get_category_icon(category)} {category}：**{items_str}")
        
        # 简化界面：输入框 + 选择分类
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # 主要输入框（不使用key，让Streamlit自动管理）
            custom_item = st.text_input(
                "✨ 输入物品名称",
                placeholder="输入物品名称...",
                label_visibility="collapsed"
            )
            
            # 已有物品下拉列表
            if all_existing_items:
                st.markdown("💡 **快速选择已有物品：**")
                selected = st.selectbox(
                    "📂 从已有物品选择",
                    options=["（请选择）"] + all_existing_items,
                    label_visibility="collapsed",
                    index=0
                )
                if selected != "（请选择）":
                    st.info(f"已选择：{selected}，点击「添加」即可")
                    # 使用 selected 作为要添加的物品
                    custom_item = selected
        
        with col2:
            custom_category = st.selectbox("📁 分类", list(st.session_state.categories.keys()))
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ 添加", use_container_width=True):
                if custom_item and custom_item.strip():
                    # 检查是否重复
                    existing_items = st.session_state.categories.get(custom_category, [])
                    if custom_item in existing_items:
                        st.warning(f"⚠️ '{custom_item}' 已存在于【{custom_category}】！")
                    else:
                        st.session_state.categories[custom_category].append(custom_item)
                        st.success(f"✅ 已添加：{custom_item}")
                        st.rerun()
                else:
                    st.warning("⚠️ 请输入或选择物品名称！")
    
    # Tab 2: 旅行贴士
    with tab2:
        st.markdown("### 💡 根据你的行程生成的贴心建议")
        
        tips = get_tips(season, activity, st.session_state.categories.get("雨伞/雨衣", []), 
                       st.session_state.temp and st.session_state.temp >= 30,
                       st.session_state.temp and st.session_state.temp <= 5, days)
        
        for i, tip in enumerate(tips):
            st.markdown(f"""
            <div class="tip-card">
                {tip}
            </div>
            """, unsafe_allow_html=True)
        
        # 季节特别提醒
        st.markdown("### 🌟 特别提醒")
        if season == "夏季":
            st.warning("🔥 夏季高温，注意防暑降温！")
        elif season == "冬季":
            st.warning("❄️ 冬季寒冷，注意防寒保暖！")
        
        if st.session_state.get("weather") and ("雨" in str(st.session_state.weather) or "雪" in str(st.session_state.weather)):
            st.warning("🌧️ 天气有雨/雪，请带好雨具！")
    
    # Tab 3: 紧急联系人
    with tab3:
        st.markdown("### 📞 紧急联系人卡片")
        
        contacts = get_emergency_contacts()
        
        st.markdown("#### 🆘 国内紧急电话")
        for name, phone in contacts["国内"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{name}**: {phone}")
            with col2:
                if st.button(f"📱 拨打", key=f"call_{name}"):
                    st.info(f"正在拨打 {phone}...")
        
        st.markdown("#### 👨‍👩‍👧 个人紧急联系人")
        st.info("请提前填写好以下联系信息，方便紧急情况下使用")
        
        with st.form("emergency_form"):
            col1, col2 = st.columns(2)
            with col1:
                family_name = st.text_input("家人姓名")
                family_phone = st.text_input("家人电话")
            with col2:
                hotel_name = st.text_input("酒店名称")
                hotel_phone = st.text_input("酒店电话")
            
            submitted = st.form_submit_button("保存联系人", use_container_width=True)
            if submitted:
                st.success("✅ 紧急联系人已保存！")
        
        # 保险信息
        st.markdown("#### 🛡️ 旅行保险")
        st.markdown("""
        建议购买旅行保险，覆盖：
        - 意外伤害
        - 医疗费用
        - 航班延误/取消
        - 行李丢失
        - 紧急救援
        """)
    
    # Tab 4: 旅游路线
    with tab4:
        st.markdown("### 🗺️ 推荐旅游路线")
        
        # 基于目的地和活动生成路线
        if dest:
            # 计算每日预算
            daily_budget = initial_budget / days if days > 0 else initial_budget
            budget_per_person = initial_budget
            
            st.markdown(f"""
            #### {dest} {days}日{activity}路线规划
            """)
            
            # 预算分配
            st.markdown("#### 💰 预算分配建议")
            
            budget_breakdown = {
                "🏨 住宿": int(budget_per_person * 0.35),
                "🍜 餐饮": int(budget_per_person * 0.25),
                "🎫 门票/活动": int(budget_per_person * 0.20),
                "🚌 交通": int(budget_per_person * 0.12),
                "🎁 购物/纪念品": int(budget_per_person * 0.08),
            }
            
            for item, amount in budget_breakdown.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{item}**")
                with col2:
                    st.progress(amount / budget_per_person, text=f"¥{amount}")
            
            # 热门打卡地点数据
            popular_spots = {
                "北京": [
                    {"name": "故宫博物院", "type": "历史", "rating": 4.9, "tags": ["必打卡", "世界文化遗产"]},
                    {"name": "天安门广场", "type": "地标", "rating": 4.8, "tags": ["必打卡", "爱国主义"]},
                    {"name": "八达岭长城", "type": "自然风光", "rating": 4.9, "tags": ["必打卡", "世界文化遗产"]},
                    {"name": "颐和园", "type": "园林", "rating": 4.8, "tags": ["皇家园林"]},
                    {"name": "南锣鼓巷", "type": "特色街区", "rating": 4.6, "tags": ["美食", "文艺"]},
                    {"name": "鸟巢/水立方", "type": "现代建筑", "rating": 4.7, "tags": ["地标"]},
                    {"name": "什刹海", "type": "休闲", "rating": 4.7, "tags": ["夜景", "美食"]},
                    {"name": "三里屯", "type": "购物", "rating": 4.5, "tags": ["时尚", "夜生活"]},
                ],
                "上海": [
                    {"name": "外滩", "type": "地标", "rating": 4.9, "tags": ["必打卡", "夜景"]},
                    {"name": "东方明珠", "type": "现代建筑", "rating": 4.7, "tags": ["地标", "观景"]},
                    {"name": "豫园", "type": "园林", "rating": 4.7, "tags": ["历史", "美食"]},
                    {"name": "上海迪士尼", "type": "主题乐园", "rating": 4.8, "tags": ["亲子", "必打卡"]},
                    {"name": "田子坊", "type": "特色街区", "rating": 4.5, "tags": ["文艺", "美食"]},
                    {"name": "南京路", "type": "购物", "rating": 4.6, "tags": ["步行街"]},
                    {"name": "陆家嘴", "type": "现代建筑", "rating": 4.8, "tags": ["金融中心", "夜景"]},
                    {"name": "武康路", "type": "休闲", "rating": 4.6, "tags": ["历史建筑", "文艺"]},
                ],
                "广州": [
                    {"name": "广州塔", "type": "地标", "rating": 4.8, "tags": ["必打卡", "夜景"]},
                    {"name": "长隆旅游度假区", "type": "主题乐园", "rating": 4.9, "tags": ["亲子", "必打卡"]},
                    {"name": "沙面岛", "type": "历史", "rating": 4.6, "tags": ["欧式建筑"]},
                    {"name": "白云山", "type": "自然风光", "rating": 4.5, "tags": ["登山", "休闲"]},
                    {"name": "上下九步行街", "type": "购物", "rating": 4.4, "tags": ["美食", "老字号"]},
                    {"name": "陈家祠", "type": "历史", "rating": 4.7, "tags": ["岭南建筑"]},
                    {"name": "北京路", "type": "购物", "rating": 4.5, "tags": ["步行街"]},
                    {"name": "夜游珠江", "type": "休闲", "rating": 4.7, "tags": ["夜景"]},
                ],
                "深圳": [
                    {"name": "深圳欢乐谷", "type": "主题乐园", "rating": 4.6, "tags": ["亲子"]},
                    {"name": "世界之窗", "type": "主题乐园", "rating": 4.5, "tags": ["亲子", "拍照"]},
                    {"name": "东部华侨城", "type": "主题乐园", "rating": 4.6, "tags": ["度假"]},
                    {"name": "大鹏古城", "type": "历史", "rating": 4.4, "tags": ["古镇"]},
                    {"name": "海岸城", "type": "购物", "rating": 4.5, "tags": ["商圈"]},
                    {"name": "莲花山公园", "type": "自然风光", "rating": 4.5, "tags": ["休闲"]},
                    {"name": "海上世界", "type": "休闲", "rating": 4.4, "tags": ["夜景"]},
                    {"name": "观澜湖新城", "type": "购物", "rating": 4.3, "tags": ["休闲"]},
                ],
                "杭州": [
                    {"name": "西湖", "type": "自然风光", "rating": 4.9, "tags": ["必打卡", "世界文化遗产"]},
                    {"name": "灵隐寺", "type": "历史", "rating": 4.8, "tags": ["祈福", "必打卡"]},
                    {"name": "西溪湿地", "type": "自然风光", "rating": 4.6, "tags": ["生态"]},
                    {"name": "河坊街", "type": "特色街区", "rating": 4.5, "tags": ["美食", "老字号"]},
                    {"name": "雷峰塔", "type": "历史", "rating": 4.6, "tags": ["白娘子传说"]},
                    {"name": "宋城", "type": "主题乐园", "rating": 4.7, "tags": ["亲子", "演出"]},
                    {"name": "断桥残雪", "type": "自然风光", "rating": 4.7, "tags": ["西湖十景"]},
                    {"name": "龙井村", "type": "休闲", "rating": 4.6, "tags": ["茶文化"]},
                ],
                "成都": [
                    {"name": "宽窄巷子", "type": "特色街区", "rating": 4.7, "tags": ["必打卡", "美食"]},
                    {"name": "锦里", "type": "特色街区", "rating": 4.6, "tags": ["美食", "夜景"]},
                    {"name": "大熊猫基地", "type": "主题乐园", "rating": 4.9, "tags": ["必打卡", "亲子"]},
                    {"name": "武侯祠", "type": "历史", "rating": 4.7, "tags": ["三国文化"]},
                    {"name": "杜甫草堂", "type": "历史", "rating": 4.6, "tags": ["文化"]},
                    {"name": "春熙路", "type": "购物", "rating": 4.5, "tags": ["商圈"]},
                    {"name": "都江堰", "type": "自然风光", "rating": 4.8, "tags": ["世界文化遗产"]},
                    {"name": "青城山", "type": "自然风光", "rating": 4.6, "tags": ["道教"]},
                ],
                "重庆": [
                    {"name": "洪崖洞", "type": "特色街区", "rating": 4.9, "tags": ["必打卡", "夜景"]},
                    {"name": "解放碑", "type": "地标", "rating": 4.7, "tags": ["商圈"]},
                    {"name": "长江索道", "type": "休闲", "rating": 4.6, "tags": ["必打卡"]},
                    {"name": "磁器口古镇", "type": "特色街区", "rating": 4.5, "tags": ["美食", "古镇"]},
                    {"name": "李子坝轻轨站", "type": "地标", "rating": 4.6, "tags": ["网红"]},
                    {"name": "南山一棵树", "type": "自然风光", "rating": 4.7, "tags": ["夜景"]},
                    {"name": "武隆天生三桥", "type": "自然风光", "rating": 4.8, "tags": ["世界自然遗产"]},
                    {"name": "渣滓洞", "type": "历史", "rating": 4.5, "tags": ["红色旅游"]},
                ],
                "西安": [
                    {"name": "兵马俑", "type": "历史", "rating": 4.9, "tags": ["必打卡", "世界文化遗产"]},
                    {"name": "大雁塔", "type": "历史", "rating": 4.7, "tags": ["必打卡"]},
                    {"name": "城墙", "type": "历史", "rating": 4.8, "tags": ["必打卡"]},
                    {"name": "回民街", "type": "特色街区", "rating": 4.6, "tags": ["美食"]},
                    {"name": "华清宫", "type": "历史", "rating": 4.7, "tags": ["温泉"]},
                    {"name": "陕西历史博物馆", "type": "历史", "rating": 4.8, "tags": ["必打卡"]},
                    {"name": "大唐不夜城", "type": "休闲", "rating": 4.7, "tags": ["夜景", "演出"]},
                    {"name": "碑林博物馆", "type": "历史", "rating": 4.6, "tags": ["书法"]},
                ],
                "三亚": [
                    {"name": "亚龙湾", "type": "自然风光", "rating": 4.8, "tags": ["必打卡", "海滩"]},
                    {"name": "蜈支洲岛", "type": "自然风光", "rating": 4.9, "tags": ["必打卡", "海岛"]},
                    {"name": "天涯海角", "type": "自然风光", "rating": 4.6, "tags": ["必打卡", "地标"]},
                    {"name": "南山文化旅游区", "type": "历史", "rating": 4.7, "tags": ["祈福", "108米观音"]},
                    {"name": "海棠湾", "type": "自然风光", "rating": 4.7, "tags": ["海滩", "奢华"]},
                    {"name": "呀诺达雨林", "type": "自然风光", "rating": 4.5, "tags": ["雨林"]},
                    {"name": "第一市场", "type": "购物", "rating": 4.4, "tags": ["海鲜"]},
                    {"name": "三亚千古情", "type": "主题乐园", "rating": 4.6, "tags": ["演出"]},
                ],
                "丽江": [
                    {"name": "丽江古城", "type": "特色街区", "rating": 4.8, "tags": ["必打卡", "世界文化遗产"]},
                    {"name": "玉龙雪山", "type": "自然风光", "rating": 4.9, "tags": ["必打卡"]},
                    {"name": "束河古镇", "type": "特色街区", "rating": 4.5, "tags": ["古镇"]},
                    {"name": "拉市海", "type": "自然风光", "rating": 4.4, "tags": ["湿地"]},
                    {"name": "木府", "type": "历史", "rating": 4.5, "tags": ["土司府"]},
                    {"name": "黑龙潭", "type": "自然风光", "rating": 4.4, "tags": ["公园"]},
                    {"name": "白沙古镇", "type": "特色街区", "rating": 4.3, "tags": ["原生态"]},
                    {"name": "四方街", "type": "休闲", "rating": 4.6, "tags": ["夜景"]},
                ],
                "惠州": [
                    {"name": "西湖", "type": "自然风光", "rating": 4.6, "tags": ["必打卡", "国家AAAA级景区"]},
                    {"name": "双月湾", "type": "自然风光", "rating": 4.7, "tags": ["必打卡", "海滩"]},
                    {"name": "巽寮湾", "type": "自然风光", "rating": 4.5, "tags": ["海滩", "度假"]},
                    {"name": "罗浮山", "type": "自然风光", "rating": 4.5, "tags": ["道教名山", "国家AAAAA级景区"]},
                    {"name": "惠州科技馆", "type": "休闲", "rating": 4.3, "tags": ["亲子", "科普"]},
                    {"name": "大亚湾", "type": "自然风光", "rating": 4.4, "tags": ["海岛", "海鲜"]},
                    {"name": "南昆山", "type": "自然风光", "rating": 4.4, "tags": ["避暑", "温泉"]},
                    {"name": "永记生态园", "type": "休闲", "rating": 4.2, "tags": ["亲子", "采摘"]},
                ],
                "湛江": [
                    {"name": "湖光岩", "type": "自然风光", "rating": 4.7, "tags": ["必打卡", "世界地质公园"], "location": "110.3044,21.1575",
                     "description": "世界地质公园、国家AAAA级景区，是玛珥湖的典型代表。湖水清澈，周围绿树成荫，环境清幽，是了解地质知识的绝佳场所。",
                     "suitable_for": "适合各年龄段游客，尤其推荐地质爱好者、自然风光爱好者。建议2-6人结伴游览，游览时间约2-3小时。"},
                    {"name": "东海岛", "type": "自然风光", "rating": 4.6, "tags": ["海滩", "必打卡"], "location": "110.4876,21.0378",
                     "description": "中国第一长滩，全长28公里，海水清澈，沙滩细腻。可以在海边漫步、骑沙滩摩托车、品尝海鲜。",
                     "suitable_for": "适合各年龄段游客，尤其推荐海滩爱好者。适合2-10人结伴，建议游玩半天到一天。"},
                    {"name": "硇洲岛", "type": "自然风光", "rating": 4.5, "tags": ["海岛", "火山"], "location": "110.5836,20.9234",
                     "description": "中国最大的火山岛，岛上有灯塔、火山岩等独特景观。可以体验海岛风光和火山地质奇观。",
                     "suitable_for": "适合各年龄段游客，建议穿舒适运动鞋。适合2-6人，建议游玩一整天。"},
                    {"name": "金沙湾", "type": "自然风光", "rating": 4.5, "tags": ["海滩", "夜景"], "location": "110.4036,21.1945",
                     "description": "湛江市区的海滨公园，沙滩平缓，海水清澈。夜晚灯光璀璨，是观赏湛江海湾夜景的好去处。",
                     "suitable_for": "适合各年龄段游客，尤其推荐夜游和摄影爱好者。适合2-6人，游览时间约1-2小时。"},
                    {"name": "赤坎老街", "type": "特色街区", "rating": 4.6, "tags": ["历史", "美食"], "location": "110.3586,21.1965",
                     "description": "湛江最古老的商业街区，保留了大量南洋风格的骑楼建筑。可以感受老湛江的风情，品尝地道的小吃。",
                     "suitable_for": "适合各年龄段游客，尤其推荐历史文化爱好者。适合2-4人，游览时间约1-2小时。"},
                                        {"name": "广州湾法国公使署", "type": "历史", "rating": 4.4, "tags": ["历史建筑"], "location": "110.3596,21.1965",
                     "description": "法式建筑风格的旧政府办公楼，见证了湛江的殖民历史。建筑风格独特，是了解湛江近代史的好去处。",
                     "suitable_for": "适合各年龄段游客，尤其推荐历史爱好者。适合2-4人，游览时间约1小时。"},
                    {"name": "特呈岛", "type": "自然风光", "rating": 4.4, "tags": ["海岛", "休闲"], "location": "110.4366,21.1235",
                     "description": "距离市区最近的海岛，岛上有红树林、白沙滩。可以乘坐渡船前往，体验海岛渔村风情。",
                     "suitable_for": "适合各年龄段游客，尤其推荐休闲度假的朋友。适合2-8人，建议游玩半天。"},
                    {"name": "南三岛", "type": "自然风光", "rating": 4.3, "tags": ["海滩", "原生态"], "location": "110.6236,21.1675",
                     "description": "保持着较为原生态的海岛风光，沙滩干净，海水清澈。是远离喧嚣、享受宁静的好去处。",
                     "suitable_for": "适合喜欢原生态海岛风光的游客。适合2-6人，建议游玩半天到一天。"},
                ],
            }
            
            # 获取当前城市的打卡地点
            city_spots = popular_spots.get(dest, [])
            
            # 获取高德地图 API Key
            amap_key = os.environ.get('AMAP_API_KEY', 'e7504e0b778d4f34bd5b3741d0557793')
            
            # 使用高德地图地理编码 API 获取城市坐标
            coords = {"lat": 39.9042, "lng": 116.4074}
            try:
                geocode_url = f"https://restapi.amap.com/v3/geocode/geo?address={dest}&key={amap_key}"
                response = requests.get(geocode_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1' and data.get('geocodes'):
                        location = data['geocodes'][0]['location']
                        lng, lat = map(float, location.split(','))
                        coords = {"lat": lat, "lng": lng}
            except Exception as e:
                pass
            
            # 使用高德地图搜索 API 获取热门景点
            amap_spots = []
            try:
                search_url = f"https://restapi.amap.com/v3/place/text?keywords={dest}景点&city={dest}&types=110000&key={amap_key}&offset=10"
                response = requests.get(search_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1' and data.get('pois'):
                        for poi in data['pois'][:8]:
                            amap_spots.append({
                                "name": poi.get('name', ''),
                                "type": poi.get('type', '').split(';')[0] if poi.get('type') else '景点',
                                "rating": 4.5,  # 高德API不返回评分，默认4.5
                                "tags": ["推荐"],
                                "address": poi.get('address', ''),
                                "location": poi.get('location', ''),
                            })
            except Exception as e:
                pass
            
            # ===== 电子地图展示 =====
            st.markdown("#### 🗺️ 目的地电子地图")
            try:
                # 使用交互式iframe地图
                map_iframe = get_amap_iframe(dest, height=450)
                st.markdown(map_iframe, unsafe_allow_html=True)
            except Exception as e:
                # 备用方案：静态地图
                map_url = f"https://webapi.amap.com/staticmapservice?center={coords['lng']},{coords['lat']}&zoom=11&size=800*450&markers=mid,ff0000,1:{coords['lng']},{coords['lat']}&key={amap_key}"
                st.image(map_url, caption=f"{dest} 地图概览", use_column_width=True)
            
            # ===== 热门景点推荐 =====
            st.markdown("#### ⭐ 当地热门景点推荐")
            
            # 使用API搜索景点
            api_spots = search_hot_spots(dest, limit=8)
            
            # 如果API获取失败，使用预设数据
            if api_spots:
                city_spots = api_spots
            elif amap_spots:
                city_spots = amap_spots
            elif not city_spots:
                st.info("正在获取景点数据...")
            
            if city_spots:
                # 按评分排序
                sorted_spots = sorted(city_spots, key=lambda x: x['rating'], reverse=True)
                
                # 以卡片形式展示景点（每行2个）
                cols = st.columns(2)
                for idx, spot in enumerate(sorted_spots[:6]):
                    with cols[idx % 2]:
                        tags_str = " ".join([f"#{tag}" for tag in spot['tags'][:3]])
                        address_info = spot['address'][:60] + '...' if len(spot.get('address', '')) > 60 else spot.get('address', '')
                        description = spot.get('description', '暂无详细介绍')
                        suitable_for = spot.get('suitable_for', '适合各类游客参观')
                        
                        # 用白色卡片显示景点信息
                        card_html = f"""
                        <div style="background: white; border-radius: 15px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 20px; border: 1px solid #e8e8e8;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                                <h4 style="margin: 0; color: #333; font-size: 20px;">🌟 {spot['name']}</h4>
                                <span style="background: linear-gradient(90deg, #FFD700, #FFA500); color: white; padding: 8px 16px; border-radius: 15px; font-size: 14px; font-weight: bold;">
                                    {spot['rating']}分
                                </span>
                            </div>
                            <p style="color: #666; font-size: 15px; margin: 0 0 12px 0;">📍 {spot['type']}</p>
                            <p style="color: #444; font-size: 14px; line-height: 1.6; margin: 0 0 12px 0;"><strong style="color: #1f77b4;">✨ 推荐理由：</strong>{description}</p>
                            <p style="color: #555; font-size: 13px; line-height: 1.5; margin: 0 0 12px 0;"><strong style="color: #ff9800;">👥 适合人群：</strong>{suitable_for}</p>
                            <p style="color: #888; font-size: 13px; margin: 0 0 8px 0;">🏠 {address_info}</p>
                            <p style="color: #1f77b4; font-size: 13px; margin: 0;">🏷️ {tags_str}</p>
                        </div>
                        """
                        st.write(card_html, unsafe_allow_html=True)
            else:
                st.info(f"暂未获取到{dest}的景点数据，我们正在努力扩展城市覆盖范围！")
            
            # 🎯 自定义旅游路线功能
            st.markdown("#### ✏️ 自定义旅游路线")
            
            # 初始化自定义路线列表
            if 'custom_routes' not in st.session_state:
                st.session_state.custom_routes = []
            
            # 添加自定义打卡地点
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                new_spot = st.text_input("📍 添加打卡地点名称", key="custom_spot_name")
            with col2:
                spot_time = st.selectbox("⏰ 预计游玩时间", ["1小时", "2小时", "半天", "全天"])
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ 添加", key="add_custom_spot"):
                    if new_spot.strip():
                        st.session_state.custom_routes.append({
                            "name": new_spot.strip(),
                            "time": spot_time,
                            "day": 0
                        })
                        st.success(f"✅ 已添加：{new_spot}")
            
            # 显示自定义路线列表
            if st.session_state.custom_routes:
                st.markdown("**已添加的打卡地点：**")
                for i, spot in enumerate(st.session_state.custom_routes):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.markdown(f"📍 {spot['name']}")
                    with col2:
                        st.markdown(f"⏰ {spot['time']}")
                    with col3:
                        if st.button("🗑️", key=f"del_spot_{i}"):
                            del st.session_state.custom_routes[i]
                            st.rerun()
            
            # 根据活动类型和打卡地点生成路线
            st.markdown(f"#### 📅 结合打卡地点的每日行程建议")
            
            # 根据活动类型选择打卡地点
            if activity == "城市观光" and city_spots:
                # 选择历史、地标类景点
                sightseeing_spots = [s for s in city_spots if s['type'] in ['历史', '地标', '园林']]
                shopping_spots = [s for s in city_spots if s['type'] in ['购物', '特色街区']]
                
                day1_spots = sightseeing_spots[:2] if len(sightseeing_spots) >= 2 else []
                day2_spots = sightseeing_spots[2:4] if len(sightseeing_spots) >= 4 else sightseeing_spots[2:]
                day3_spots = shopping_spots[:2] if len(shopping_spots) >= 2 else []
                
                routes = [
                    ("第1天", f"✈️ 抵达入住 → 🛕 {day1_spots[0]['name'] if day1_spots else '历史景点'} → 🌆 夜游{dest}"),
                    ("第2天", f"🏛️ {day2_spots[0]['name'] if day2_spots else '文化景点'} → 🛍️ 商业街区 → 🎭 特色演出"),
                    ("第3天", f"🌳 公园休闲 →  购买特产 → 👋 返程"),
                ]
            elif activity == "海滩" and city_spots:
                beach_spots = [s for s in city_spots if s['type'] in ['自然风光']]
                routes = [
                    ("第1天", f"🏨 抵达入住 → 🏖️ {beach_spots[0]['name'] if beach_spots else '沙滩'}休息 → 🌅 日落观赏"),
                    ("第2天", f"🤿 海上活动 → {beach_spots[1]['name'] if len(beach_spots)>=2 else '海岛'}探秘 → 🦐 海鲜大餐"),
                    ("第3天", f"🛒 当地市集 → 🎁 购买特产 → 👋 退房返程"),
                ]
            elif activity == "徒步登山" and city_spots:
                nature_spots = [s for s in city_spots if s['type'] in ['自然风光']]
                routes = [
                    ("第1天", "🏕️ 抵达出发点 → ⛺ 搭建营地 → 🌌 星空观赏"),
                    ("第2天", f"🥾 登山徒步 → 🏞️ {nature_spots[0]['name'] if nature_spots else '观景点'}打卡 → ⛺ 营地休息"),
                    ("第3天", "🌅 山顶日出 → 🥾 下山返程 → 🍜 庆功宴"),
                ]
            elif activity == "商务出差":
                routes = [
                    ("第1天", "✈️ 抵达 → 🏨 入住酒店 → 📋 准备会议资料"),
                    ("第2天", "💼 商务会议/活动 → 🍽️ 商务餐叙 → 📝 总结汇报"),
                    ("第3天", f"🏛️ {city_spots[0]['name'] if city_spots else '景点'}快速游览 → 🎁 购买礼品 → 返回"),
                ]
            elif activity == "露营":
                routes = [
                    ("第1天", "🚗 抵达营地 → ⛺ 搭建帐篷 → 🔥 篝火晚会"),
                    ("第2天", f"🥾 周边探索 → 🏞️ {city_spots[0]['name'] if city_spots else '自然风光'} → 🍖 户外烧烤"),
                    ("第3天", "🌅 早晨瑜伽 → 🎣 钓鱼活动 → 收拾返程"),
                ]
            else:  # 走亲访友
                routes = [
                    ("第1天", "✈️/🚄 抵达 → 🏠 亲友家入住 → 🍽️ 团圆聚餐"),
                    ("第2天", f"👨‍👩‍👧‍👦 家庭活动 → 🏛️ {city_spots[0]['name'] if city_spots else '当地景点'}游览 → 🎁 送礼拜访"),
                    ("第3天", "🛒 购买特产 → 👋 告别亲友 → 返程"),
                ]
            
            # 只显示实际天数的路线
            for i, (day, route) in enumerate(routes):
                if i < days:
                    with st.expander(f"{day} {route.split(' → ')[0]}", expanded=i==0):
                        st.markdown(f"**行程安排：**")
                        steps = route.split(" → ")
                        for step in steps:
                            st.markdown(f"  • {step}")
                        
                        # 当日预算
                        daily_amount = int(budget_per_person / days)
                        st.markdown(f"**当日预算：** ¥{daily_amount:,}")
            
            # 打卡地点表格
            if city_spots:
                st.markdown("#### 📊 打卡地点详情")
                spot_data = []
                for spot in city_spots:
                    spot_data.append({
                        "景点名称": spot['name'],
                        "类型": spot['type'],
                        "评分": spot['rating'],
                        "标签": ", ".join(spot['tags']),
                    })
                st.dataframe(pd.DataFrame(spot_data), use_container_width=True)
            
            # 实用信息
            st.markdown("#### 💡 实用旅行信息")
            
            info_tips = {
                "🏨 住宿建议": f"根据{people}人，建议选择家庭房或相邻房间，方便照顾" if people > 1 else "建议选择市中心交通便利的酒店",
                "🍜 餐饮推荐": "尝试当地特色美食，但注意卫生情况，建议提前查询口碑好的餐厅",
                "🚌 交通出行": "建议购买当地的交通卡或使用正规打车软件，避免被宰",
                "⚠️ 安全提示": "保管好个人财物，尤其是证件和现金，遇到问题及时报警",
            }
            
            for title, content in info_tips.items():
                with st.expander(title, expanded=False):
                    st.markdown(content)
            
            # 总预算汇总
            st.markdown("#### 💵 旅行预算总览")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👥 出行人数", f"{people}人")
            with col2:
                st.metric("💰 人均预算", f"¥{budget_per_person:,}")
            with col3:
                st.metric("💼 总预算", f"¥{budget_per_person * people:,}")
            
            # 节省预算建议
            with st.expander("💡 如何节省旅行预算", expanded=False):
                st.markdown("""
                1. **提前预订** - 机票、酒店提前1-2个月预订通常更便宜
                2. **灵活出行** - 避开节假日和周末，机票价格差异大
                3. **当地交通** - 使用公共交通代替出租车，可以省不少钱
                4. **餐饮选择** - 多尝试当地小吃和市场，比餐厅便宜又正宗
                5. **免费景点** - 许多城市的博物馆、公园是免费的
                6. **购物技巧** - 在当地人去的市场购物，避免旅游区的溢价
                7. **住宿优惠** - 关注酒店官网或使用比价网站
                """)
        else:
            st.info("👆 请先在顶部填写目的地城市，然后点击「智能生成清单」来获取推荐路线")
        
        st.markdown("#### ✅ 出发前检查清单")
        checks = [
            "证件（身份证/护照）是否有效",
            "机票/酒店预订确认",
            "手机充满电，充电宝带好",
            "现金和银行卡",
            "药品和处方",
            "换洗衣物充足",
            "天气对应的装备",
            "充电器和转换插头",
            "保险单打印或电子版",
        ]
        
        for i, check in enumerate(checks):
            st.checkbox(check, key=f"pre_check_{i}")
    
    # Tab 5: 导出分享
    with tab5:
        st.markdown("### 📤 导出和分享")
        
        # 生成 PDF 友好的 HTML
        if st.button("📄 导出精美 PDF 清单", use_container_width=True):
            # 构建天气信息
            weather_html = ""
            if st.session_state.get("temp"):
                weather_html = f"""
                <div class="weather-info">
                    <h3>🌤️ 天气信息</h3>
                    <p><strong>温度：</strong>{st.session_state.temp}°C</p>
                    <p><strong>天气：</strong>{st.session_state.weather}</p>
                    {f'<p><strong>湿度：</strong>{st.session_state.humidity}%</p>' if st.session_state.humidity else ''}
                    {f'<p><strong>风速：</strong>{st.session_state.wind_speed} m/s</p>' if st.session_state.wind_speed else ''}
                </div>
                """
            
            # 构建物品清单 HTML
            items_html = ""
            for category, items in st.session_state.categories.items():
                icon = get_category_icon(category)
                items_html += f"""
                <div class="category-section">
                    <h3>{icon} {category}</h3>
                    <ul class="item-list">
                        {''.join(f'<li><span class="checkbox"></span>{item}</li>' for item in items)}
                    </ul>
                </div>
                """
            
            # 构建旅行贴士
            tips = get_tips(season, activity, False, 
                           st.session_state.temp and st.session_state.temp >= 30,
                           st.session_state.temp and st.session_state.temp <= 5, days)
            tips_html = '<ul class="tips-list">' + ''.join(f'<li>{tip}</li>' for tip in tips) + '</ul>'
            
            # 完整的 HTML 文档
            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>旅行打包清单 - {st.session_state.dest}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 40px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        .trip-info {{
            padding: 30px 40px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        .trip-info h2 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5rem;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .info-item {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .info-item strong {{
            color: #667eea;
            display: block;
            margin-bottom: 5px;
        }}
        .weather-info {{
            margin-top: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            border-radius: 15px;
            color: white;
        }}
        .weather-info h3 {{
            margin-bottom: 10px;
            font-size: 1.3rem;
        }}
        .weather-info p {{
            margin: 5px 0;
            font-size: 1.1rem;
        }}
        .content {{
            padding: 40px;
        }}
        .category-section {{
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }}
        .category-section h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .item-list {{
            list-style: none;
        }}
        .item-list li {{
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            align-items: center;
        }}
        .item-list li:last-child {{
            border-bottom: none;
        }}
        .checkbox {{
            width: 20px;
            height: 20px;
            border: 2px solid #667eea;
            border-radius: 5px;
            margin-right: 15px;
            display: inline-block;
        }}
        .tips-section {{
            margin-top: 40px;
            padding: 25px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 15px;
            color: white;
        }}
        .tips-section h3 {{
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}
        .tips-list {{
            list-style: none;
        }}
        .tips-list li {{
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }}
        .tips-list li:last-child {{
            border-bottom: none;
        }}
        .footer {{
            padding: 30px 40px;
            background: #f8f9fa;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }}
        .footer .app-name {{
            font-weight: bold;
            color: #667eea;
        }}
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                border-radius: 0;
            }}
            .checkbox {{
                border: 2px solid #333;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎒 旅行打包清单</h1>
            <div class="subtitle">✈️ {st.session_state.dest} 之旅</div>
        </div>
        
        <div class="trip-info">
            <h2>📋 行程信息</h2>
            <div class="info-grid">
                <div class="info-item">
                    <strong>🏙️ 目的地</strong>
                    {st.session_state.dest}
                </div>
                <div class="info-item">
                    <strong>📅 行程天数</strong>
                    {days} 天
                </div>
                <div class="info-item">
                    <strong>👥 出行人数</strong>
                    {people} 人
                </div>
                <div class="info-item">
                    <strong>🎯 活动类型</strong>
                    {activity}
                </div>
                <div class="info-item">
                    <strong>💰 预算等级</strong>
                    {budget}
                </div>
                <div class="info-item">
                    <strong>💵 人均预算</strong>
                    ¥{initial_budget:,}/人
                </div>
                <div class="info-item">
                    <strong>💼 总预算</strong>
                    ¥{initial_budget * people:,}
                </div>
                <div class="info-item">
                    <strong>🌡️ 出行季节</strong>
                    {season}
                </div>
            </div>
            {weather_html}
        </div>
        
        <div class="content">
            <h2 style="color: #667eea; margin-bottom: 20px; font-size: 1.5rem;">📦 物品清单</h2>
            {items_html}
            
            <div class="tips-section">
                <h3>💡 旅行小贴士</h3>
                {tips_html}
            </div>
        </div>
        
        <div class="footer">
            <p>由 <span class="app-name">智能旅行打包助手 Pro</span> 生成</p>
            <p style="margin-top: 5px;">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
    </div>
</body>
</html>"""
            
            st.download_button(
                "⬇️ 下载精美 PDF 清单 (HTML格式)",
                html_content.encode("utf-8"),
                file_name=f"旅行清单_{st.session_state.dest}_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True
            )
            
            st.success("✅ 已生成精美清单！点击上方按钮下载 HTML 文件")
            st.info("💡 提示：在浏览器中打开 HTML 文件，按 Ctrl+P 可打印为 PDF")

        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 分享功能
        st.markdown("#### 📱 分享到社交媒体")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.button("💬 微信", use_container_width=True)
        with col2:
            st.button("📱 朋友圈", use_container_width=True)
        with col3:
            st.button("微博", use_container_width=True)
        with col4:
            st.button("📧 邮件", use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 统计信息
        st.markdown("#### 📊 打包统计")
        total_items = sum(len(items) for items in st.session_state.categories.values())
        st.metric("总物品数", total_items)
        
        # 行李箱建议
        st.markdown("#### 🧳 推荐行李箱尺寸")
        if days <= 3:
            st.info("🎒 建议：20寸登机箱 | 重量：<7kg")
        elif days <= 7:
            st.info("🧳 建议：24寸托运行李箱 + 20寸登机箱")
        else:
            st.info("🧳 建议：28寸托运行李箱 + 20寸登机箱 | 重量：<23kg")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # PDF 打印教程
        st.markdown("""
        ### 📖 如何将清单打印为 PDF
        
        1. **点击上方「下载精美 PDF 清单」按钮**
        2. **在浏览器中打开下载的 HTML 文件**
        3. **按 `Ctrl + P` (Windows) 或 `Cmd + P` (Mac) 打开打印窗口**
        4. **选择「另存为 PDF」或「Save as PDF」**
        5. **点击保存即可获得精美的 PDF 文件！**
        
        💡 **小贴士**：在打印设置中可以选择纸张大小和方向，推荐使用 A4 竖向
        """)

else:
    # 初始界面
    st.markdown("""
    <div class="card" style="text-align: center; padding: 3rem;">
        <h2>🌟 欢迎使用智能旅行打包助手</h2>
        <p style="font-size: 1.2rem; color: #666;">
            填写左侧的行程信息，点击"智能生成清单"开始您的旅行准备！
        </p>
        <br>
        <h4>✨ 功能特色</h4>
        <p>
            🎯 智能推荐物品 | 📡 实时天气 | 💡 旅行贴士<br>
            📋 分类整理 | ✅ 进度追踪 | 📤 一键导出
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 展示预览
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📦</h3>
            <div class="metric-number">500+</div>
            <p>智能物品推荐</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>💡</h3>
            <div class="metric-number">50+</div>
            <p>实用旅行技巧</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🌍</h3>
            <div class="metric-number">10000+</div>
            <p>用户信赖选择</p>
        </div>
        """, unsafe_allow_html=True)

# 页脚
st.markdown("""
<div style="text-align: center; padding: 2rem; color: white;">
    <p>Made with ❤️ by 智能旅行打包助手 Pro</p>
    <p style="font-size: 0.9rem;">让每一次旅行都成为美好回忆 ✈️</p>
</div>
""", unsafe_allow_html=True)