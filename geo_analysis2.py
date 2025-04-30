#pip install geopandas contextily shapely pandas matplotlib scikit-learn seaborn
import geopandas as gpd
# 사용 가능한 폰트 확인
import matplotlib.font_manager as fm

# 설치된 폰트 목록 출력
fonts = [f.name for f in fm.fontManager.ttflist]
for font in fonts:
    if any(korean in font for korean in ['맑은', '굴림', '돋움', '나눔']):
        print(font)

import seaborn as sns
import matplotlib.pyplot as plt

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# seaborn 스타일 설정
sns.set(font="Malgun Gothic",
        rc={"axes.unicode_minus": False},
        style='whitegrid')

# CSV 파일의 경우 먼저 pandas로 읽은 후 GeoDataFrame으로 변환해야 합니다
import pandas as pd

# CSV 파일을 pandas DataFrame으로 읽기
df = pd.read_csv('accident.csv', encoding='cp949')
#print(df.head())
#print(df)
# 만약 CSV 파일에 geometry 정보가 있다면 (예: 위도/경도)
# 적절한 방식으로 GeoDataFrame으로 변환해야 합니다
#df['사고다발지역시도시군구']

df['사고다발지역시도시군구'] = df['사고다발지역시도시군구'].str.rstrip('0123456789')
# 변경된 결과 확인
print(df['사고다발지역시도시군구'].head())
print('---------------------------------')


df1=df[['사고다발지역시도시군구','사고다발지역폴리곤정보']]
print(df1)

print('---------------------------------')

# df2=df['사고다발지역폴리곤정보'][0]
# print(df2)
print("폴리곤 데이터 샘플:")
print(df['사고다발지역폴리곤정보'].iloc[0])
print('---------------------------------')
import json
from shapely import wkt
from shapely.geometry import Point, Polygon
from shapely.wkt import loads

#polygon_geojson=df['사고다발지역폴리곤정보']
#print(polygon_geojson)

# 폴리곤 정보를 GeoJSON으로 변환하는 함수
def create_polygon(polygon_str):
        polygon_json = polygon_str.replace('type:', '"type":').replace('coordinates:', '"coordinates":').replace('Polygon', '"Polygon"')
        geojson = json.loads(polygon_json)
        return Polygon(geojson['coordinates'][0])


df['사고다발지역폴리곤정보'] = df['사고다발지역폴리곤정보'].apply(create_polygon)
gdf = gpd.GeoDataFrame(df[['사고다발지역시도시군구']], geometry=df['사고다발지역폴리곤정보'], crs="EPSG:4326")
print(gdf)

#시각화
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
#gdf.plot()
fig, ax = plt.subplots(figsize=(15, 10))

polygon_data=gdf['geometry'][0]

polygon_patch = plt.Polygon(list(polygon_data.exterior.coords),closed=True, edgecolor='red', facecolor='None')
ax.add_patch(polygon_patch)

plt.title('Polygon')
plt.axis('equal')
plt.show()

#저장
gdf.to_file("polygon_data.geojson", driver='GeoJSON')

#한국 좌표계로 변환하는 코드
#EPSG:5179 (Korean 1985)로 변환
gdf_transformed = gdf.to_crs("EPSG:5179")


#배경 지도 추가
import contextily as ctx

# GeoDataFrame을 Web Mercator 좌표계로 변환
#gdf_web = gdf.to_crs(epsg=3857)
#gdf_web = gdf.to_crs(epsg=5179)
gdf_web = gdf.to_crs("EPSG:5179")
# 시각화
fig, ax = plt.subplots(figsize=(15, 10))
gdf_web.plot(ax=ax, alpha=0.5)
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=19)  # 지도 스타일 선택

# 제목 추가
plt.title('사고다발지역 폴리곤')

# 축 레이블 제거 (지도에서는 불필요)
ax.set_axis_off()

plt.show()

#지역 이름 라벨 표시
for idx, row in gdf.iterrows():
        plt.annotate(text=row['사고다발지역시도시군구'],
                     xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                     ha='center')
#색상 구분
gdf.plot(column='사고다발지역시도시군구',
       legend=True,
       cmap='Set3',
       categorical=True)

#지역별 통계 정보
# 지역별 사고 건수
stats = gdf.groupby('사고다발지역시도시군구').size()
print("지역별 사고다발구역 수:")
print(stats)

#면적 계산
# 먼저 한국 좌표계로 변환
gdf_korean = gdf.to_crs("EPSG:5179")

# 면적 계산 (제곱미터 단위)
gdf_korean['면적'] = gdf_korean.geometry.area
print("지역별 사고다발구역 면적:")
print(gdf_korean[['사고다발지역시도시군구', '면적']])

# 1.면적이 넓은 사고다발구역 분석
# 한국 좌표계로 변환 후 면적 계산
gdf_korean = gdf.to_crs("EPSG:5179")
gdf_korean['면적'] = gdf_korean.geometry.area

# 지역별 총 면적과 평균 면적 계산
area_stats = gdf_korean.groupby('사고다발지역시도시군구').agg({
    '면적': ['sum', 'mean', 'count']
}).round(2)

# 결과 정렬 (총 면적 기준)
area_stats = area_stats.sort_values(('면적', 'sum'), ascending=False)
print("\n== 지역별 사고다발구역 면적 분석 ==")
print(area_stats)

# 시각화
plt.figure(figsize=(12, 6))
area_stats[('면적', 'sum')].plot(kind='bar')
plt.title('지역별 총 사고다발구역 면적')
plt.xlabel('지역')
plt.ylabel('총 면적 (m²)')
plt.xticks(rotation=45)
plt.show()

'''
- 각 지역의 총 사고다발구역 면적 계산
- 평균 면적과 구역 수도 함께 분석
- 면적이 넓은 지역은 잠재적 위험이 더 클 수 있음
'''

#2.지역별 패턴 분석
# 패턴 분석을 위한 지표 계산
pattern_analysis = pd.DataFrame({
    '구역_수': gdf_korean.groupby('사고다발지역시도시군구').size(),
    '평균_면적': gdf_korean.groupby('사고다발지역시도시군구')['면적'].mean(),
    '밀집도': gdf_korean.groupby('사고다발지역시도시군구').apply(
        lambda x: len(x) / x.geometry.unary_union.area
    )
})

# 클러스터링을 통한 패턴 그룹화
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# 데이터 정규화
scaler = StandardScaler()
scaled_data = scaler.fit_transform(pattern_analysis)

# K-means 클러스터링
kmeans = KMeans(n_clusters=3, random_state=42)
pattern_analysis['패턴_그룹'] = kmeans.fit_predict(scaled_data)

print("\n== 지역별 패턴 분석 ==")
print(pattern_analysis)

# 시각화
plt.figure(figsize=(10, 6))
plt.scatter(pattern_analysis['평균_면적'], pattern_analysis['밀집도'],
           c=pattern_analysis['패턴_그룹'], cmap='viridis')
plt.xlabel('평균 면적')
plt.ylabel('밀집도')
plt.title('사고다발구역 패턴 분석')
plt.show()
'''
- 구역 수, 평균 면적, 밀집도 등 다양한 지표 분석
- 클러스터링을 통한 유사한 패턴을 가진 지역 그룹화
- 시각화를 통한 패턴 이해 도움
'''

#1. **대규모 사고다발구역 분석**:
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 한국 좌표계로 변환 및 면적 계산
gdf_korean = gdf.to_crs("EPSG:5179")
gdf_korean['면적'] = gdf_korean.geometry.area


# 면적 기준 상위 지역 분석
def analyze_large_areas(gdf):
    # 지역별 통계 계산
    area_stats = gdf.groupby('사고다발지역시도시군구').agg({
        '면적': ['sum', 'mean', 'count']
    }).round(2)

    area_stats.columns = ['총면적', '평균면적', '구역수']
    area_stats = area_stats.sort_values('총면적', ascending=False)

    # 상위 10개 지역 출력
    print("\n=== 대규모 사고다발구역 분석 (상위 10개 지역) ===")
    print(area_stats.head(10))

    # 시각화
    plt.figure(figsize=(15, 6))
    plt.subplot(1, 2, 1)
    area_stats['총면적'].head(10).plot(kind='bar')
    plt.title('지역별 총 사고다발구역 면적')
    plt.xticks(rotation=45)

    plt.subplot(1, 2, 2)
    area_stats.plot.scatter(x='구역수', y='총면적')
    plt.title('구역수 vs 총면적')

    plt.tight_layout()
    plt.show()

    return area_stats


area_analysis = analyze_large_areas(gdf_korean)

#2. **지역 패턴 분석**:
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

def analyze_patterns(gdf):
    # 패턴 분석을 위한 특성 계산
    pattern_data = pd.DataFrame({
        '구역수': gdf.groupby('사고다발지역시도시군구').size(),
        '평균면적': gdf.groupby('사고다발지역시도시군구')['면적'].mean(),
        '총면적': gdf.groupby('사고다발지역시도시군구')['면적'].sum()
    })

    # 데이터 정규화
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(pattern_data)

    # K-means 클러스터링
    kmeans = KMeans(n_clusters=3, random_state=42)
    pattern_data['클러스터'] = kmeans.fit_predict(scaled_features)

    # 클러스터별 특성 분석
    cluster_stats = pattern_data.groupby('클러스터').mean()
    print("\n=== 클러스터별 특성 ===")
    print(cluster_stats)

    # 시각화
    plt.figure(figsize=(12, 6))
    plt.scatter(pattern_data['평균면적'], pattern_data['구역수'],
                c=pattern_data['클러스터'], cmap='viridis')
    plt.xlabel('평균 면적')
    plt.ylabel('구역 수')
    plt.title('지역 패턴 클러스터링')

    # 클러스터 중심점 표시
    centers = kmeans.cluster_centers_
    plt.scatter(centers[:, 1], centers[:, 0], c='red', marker='x', s=200, linewidths=3)

    plt.show()

    return pattern_data


pattern_analysis = analyze_patterns(gdf_korean)

'''
**종합 분석 결과**:
1. **대규모 사고다발구역**:
    - 면적이 가장 큰 지역들을 파악하여 우선 관리 대상 선정
    - 구역 수와 면적의 관계를 통해 밀집도 높은 지역 식별

2. **패턴 분석**:
    - 클러스터 0: 소규모 다발구역 (작은 면적, 적은 구역 수)
    - 클러스터 1: 중규모 다발구역 (중간 면적, 중간 구역 수)
    - 클러스터 2: 대규모 다발구역 (큰 면적, 많은 구역 수)
'''

# 1. **밀집도 높은 지역 분석**:
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_density(gdf):
    # 지역별 기본 통계 계산
    density_stats = pd.DataFrame({
        '구역수': gdf.groupby('사고다발지역시도시군구').size(),
        '총면적': gdf.groupby('사고다발지역시도시군구')['면적'].sum(),
        '평균면적': gdf.groupby('사고다발지역시도시군구')['면적'].mean()
    })

    # 밀집도 계산 (구역수 / 총면적)
    density_stats['밀집도'] = (density_stats['구역수'] / density_stats['총면적']) * 1000000  # 제곱킬로미터당 구역수

    # 결과 정렬
    density_sorted = density_stats.sort_values('밀집도', ascending=False)

    print("\n=== 밀집도 분석 결과 (상위 10개 지역) ===")
    print("\n밀집도 = 구역수/총면적 (높을수록 조밀)")
    print(density_sorted.head(10))

    # 시각화
    plt.figure(figsize=(15, 10))

    # 1. 밀집도 분포
    plt.subplot(2, 2, 1)
    density_sorted['밀집도'].head(10).plot(kind='bar')
    plt.title('상위 10개 지역 밀집도')
    plt.xticks(rotation=45)

    # 2. 구역수 vs 총면적 산점도
    plt.subplot(2, 2, 2)
    plt.scatter(density_stats['총면적'], density_stats['구역수'], alpha=0.6)
    for idx, row in density_sorted.head(5).iterrows():
        plt.annotate(idx, (row['총면적'], row['구역수']))
    plt.xlabel('총면적')
    plt.ylabel('구역수')
    plt.title('구역수 vs 총면적 관계')

    # 3. 밀집도 히트맵
    if '좌표_X' in gdf.columns and '좌표_Y' in gdf.columns:
        plt.subplot(2, 2, 3)
        sns.kdeplot(data=gdf, x='좌표_X', y='좌표_Y', cmap='Reds')
        plt.title('사고다발구역 밀집도 히트맵')

    plt.tight_layout()
    plt.show()

    return density_stats


density_analysis = analyze_density(gdf_korean)

'''
**분석 결과 해석**:
1. **밀집도 분석**:
    - 단위 면적당 사고다발구역이 가장 많은 지역 식별
    - 좁은 면적에 많은 사고다발구역이 몰려있는 위험지역 파악
    - 지역별 관리 우선순위 설정 가능
'''
'''
#1. **시간대별 중첩 패턴 분석**:
def analyze_temporal_patterns(gdf):
    if '발생시간' in gdf.columns:  # 발생시간 컬럼이 있다고 가정
        # 시간대별 사고 분포
        gdf['시간대'] = pd.to_datetime(gdf['발생시간']).dt.hour
        temporal_stats = pd.DataFrame({
            '발생건수': gdf.groupby('시간대').size(),
            '평균_중첩수': gdf.groupby('시간대')['중첩횟수'].mean()
        })

        plt.figure(figsize=(12, 6))
        temporal_stats.plot(kind='bar')
        plt.title('시간대별 사고 발생 및 중첩 패턴')
        plt.show()

        return temporal_stats

# temporal_analysis = analyze_temporal_patterns(gdf_korean)

#2. **지형적 특성과 사고다발구역 관계 분석**:
def analyze_geographical_features(gdf):
    # 경사도나 고도 데이터가 있다고 가정
    geographical_stats = pd.DataFrame({
        '평균_경사도': gdf.groupby('사고다발지역시도시군구')['경사도'].mean(),
        '사고_건수': gdf.groupby('사고다발지역시도시군구').size()
    })

    # 상관관계 분석
    correlation = geographical_stats['평균_경사도'].corr(geographical_stats['사고_건수'])
    print(f"\n경사도와 사고 건수의 상관계수: {correlation:.2f}")

    return geographical_stats


#3. **클러스터 간 거리 분석**:
from scipy.spatial.distance import pdist, squareform


def analyze_cluster_distances(gdf):
    # 사고다발구역 중심점 간의 거리 계산
    centroids = gdf.geometry.centroid
    coords = np.column_stack((centroids.x, centroids.y))
    distances = pdist(coords)
    distance_matrix = squareform(distances)

    # 평균 거리 계산
    mean_distances = pd.Series(distance_matrix.mean(axis=1), index=gdf.index)

    print("\n=== 클러스터 간 거리 분석 ===")
    print(f"평균 클러스터 간 거리: {mean_distances.mean():.2f}m")
    print(f"최소 클러스터 간 거리: {mean_distances.min():.2f}m")

    return mean_distances

#4. **도로 유형별 분석**:
def analyze_road_types(gdf):
    if '도로유형' in gdf.columns:  # 도로유형 컬럼이 있다고 가정
        road_stats = pd.DataFrame({
            '사고건수': gdf.groupby('도로유형').size(),
            '평균면적': gdf.groupby('도로유형')['면적'].mean(),
            '중첩비율': gdf.groupby('도로유형')['중첩횟수'].mean()
        })

        print("\n=== 도로 유형별 분석 ===")
        print(road_stats)

        return road_stats

#5. **공간적 자기상관성 분석**:
from pysal.lib import weights
from pysal.explore import esda


def analyze_spatial_autocorrelation(gdf):
    # 공간 가중치 행렬 생성
    w = weights.distance.DistanceBand.from_dataframe(gdf, threshold=1000)

    # Moran's I 통계량 계산
    moran = esda.moran.Moran(gdf['중첩횟수'], w)

    print("\n=== 공간적 자기상관성 분석 ===")
    print(f"Moran's I: {moran.I:.3f}")
    print(f"p-value: {moran.p_sim:.3f}")
'''
'''
**새로운 인사이트**:
1. **시간적 패턴**:
    - 특정 시간대의 중첩 위험도 증가
    - 시간대별 맞춤형 교통관리 전략 수립 가능

2. **지형적 특성**:
    - 경사도와 사고 발생의 상관관계
    - 지형에 따른 위험도 예측 가능

3. **공간적 군집성**:
    - 사고다발구역 간의 거리 패턴
    - 위험지역의 공간적 확산 예측

4. **도로 특성**:
    - 도로 유형별 위험도 차이
    - 도로 설계 개선점 도출
'''
