import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import folium
from folium import Icon
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# --------------------------
# 1. 데이터 로딩 및 전처리
# --------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Hospital Data Status.csv", encoding='utf-8')
    columns_to_use = ["요양기관명", "종별코드명", "시도코드명", "주소", "좌표(X)", "좌표(Y)"]
    df = df[columns_to_use]
    df = df.rename(columns={
        "좌표(X)": "경도",
        "좌표(Y)": "위도"
    })
    df = df.dropna(subset=["경도", "위도"])
    return df

df = load_data()

# --------------------------
# 2. Streamlit 앱 구성
# --------------------------

# 제목 및 설명
st.title("🏥 병원 정보 시각화 대시보드")
st.markdown("""
이 대시보드는 한국의 병원 데이터를 시각화합니다.  
왼쪽의 필터를 사용하여 특정 지역 또는 병원 종류를 선택하세요.
""")

# --------------------------
# 3. 사이드바 필터
# --------------------------
st.sidebar.header("🔎 필터 옵션")

# 시도 필터
selected_region = st.sidebar.selectbox("시도 선택", ["전체"] + sorted(df["시도코드명"].unique()))

# 종별코드명 필터
selected_type = st.sidebar.selectbox("병원 종류 선택", ["전체"] + sorted(df["종별코드명"].unique()))

# --------------------------
# 4. 데이터 필터링
# --------------------------
filtered_df = df.copy()

if selected_region != "전체":
    filtered_df = filtered_df[filtered_df["시도코드명"] == selected_region]

# if selected_type != "전체":
#     filtered_df = filtered_df[filtered_df["종별코드명"] == selected_type]

# --------------------------
# 5. 데이터 출력
# --------------------------
st.metric(label="병원 수", value=len(filtered_df))
st.dataframe(filtered_df)

# --------------------------
# 6. 병원 분포 시각화 (선택 시도만)
# --------------------------
st.subheader("📊 선택 지역 내 병원 종류 분포")

# 선택된 시도가 '전체'가 아니라면
if selected_region != "전체":
    # 선택된 시도에 해당하는 데이터만 필터링
    region_data = filtered_df[filtered_df["시도코드명"] == selected_region]
    
    # 병원 종류별 수 집계 (병원 종류 필터는 무시하고 시도에 따른 병원 종류만 집계)
    type_counts = region_data["종별코드명"].value_counts().reset_index()
    type_counts.columns = ["병원종류", "병원수"]

    # 병원 종류별 막대 그래프 그리기
    fig_bar = px.bar(
        type_counts,
        x="병원종류",
        y="병원수",
        color="병원종류",
        title=f"{selected_region} 내 병원 종류별 수"
    )
    fig_bar.update_layout(
        legend_itemclick=False,
        legend_itemdoubleclick=False
    )
    st.plotly_chart(fig_bar)

else:
    # 전체 데이터 기준으로 시도별 병원 종류별 수 집계
    region_counts = df.groupby(["시도코드명", "종별코드명"])["요양기관명"].count().reset_index(name="병원수")
    region_counts.columns = ["시도", "병원종류", "병원수"]

    # 시도별 병원 종류 분포 막대 그래프 그리기
    fig_bar = px.bar(
        region_counts,
        x="시도",
        y="병원수",
        color="병원종류",
        title="시도별 병원 종류별 수 (전체 기준)"
    )
    fig_bar.update_layout(
        legend_itemclick=False,
        legend_itemdoubleclick=False
    )
    st.plotly_chart(fig_bar)




# --------------------------
# 7. 지도 시각화 (folium)
# --------------------------
# 시도별 중심 좌표 설정
region_centers = {
    "서울특별시": [37.5665, 126.9780],
    "부산광역시": [35.1796, 129.0756],
    "대구광역시": [35.8714, 128.6014],
    "인천광역시": [37.4563, 126.7052],
    "광주광역시": [35.1595, 126.8526],
    "대전광역시": [36.3504, 127.3845],
    "울산광역시": [35.5384, 129.3114],
    "세종특별자치시": [36.4801, 127.2891],
    "경기도": [37.4138, 127.5183],
    "강원특별자치도": [37.8228, 128.1555],
    "충청북도": [36.6358, 127.4913],
    "충청남도": [36.5184, 126.8000],
    "전라북도": [35.7175, 127.1530],
    "전라남도": [34.8161, 126.4629],
    "경상북도": [36.4919, 128.8889],
    "경상남도": [35.4606, 128.2132],
    "제주특별자치도": [33.4996, 126.5312]
}

# 지도 생성 및 마커 추가
st.subheader("🗺️ 병원 위치 지도")

# 시도 선택에 따른 지도 중심 좌표 설정
if selected_region != "전체" and selected_region in region_centers:
    map_center = region_centers[selected_region]
    zoom_level = 10
else:
    map_center = [37.5665, 126.9780]  # 서울 중심
    zoom_level = 7

# folium 지도 생성
m = folium.Map(location=map_center, zoom_start=zoom_level)
marker_cluster = MarkerCluster().add_to(m)

# 병원 종류별 색상 지정
for _, row in filtered_df.iterrows():
    color = "blue"  # 기본 색상
    if row["종별코드명"] == "종합병원":
        color = "red"
    elif row["종별코드명"] == "한방병원":
        color = "green"
    
    folium.Marker(
        location=[row["위도"], row["경도"]],
        popup=f"<b>{row['요양기관명']}</b><br>{row['주소']}",
        icon=Icon(color=color)  # 아이콘 색상 지정
    ).add_to(marker_cluster)

# Streamlit에 folium 지도 출력
st_folium(m, width=700, height=500)
