import glob
from PIL import Image
import pandas as pd
import geopandas as gpd
from scipy import stats
import plotly.express as px
import plotly.graph_objs as go

import streamlit as st

for f in sorted(glob.glob(('./img/*.png'))):
    name = f.strip('./img/.png')
    img = Image.open(f)
    exec(f'img_{name} = img')

st.sidebar.title('CO2濃度の主要変動解析')
st.sidebar.markdown(
    """
    ### 対象期間
    2010年〜2020年の月別平均CO2濃度
    ### 前処理
    グリッド毎に線形補間を行う。※前後の欠損が多い場合は解析対象から除外
    ### 手法
    主成分分析
    """
)

'''
## GOSAT/CO2濃度を用いて、全球の卓越空間パターンを抽出してみよう
### 主成分分析（PCA; principal component analysis）

> 多変量データを統合し、新たな総合指標を作り出すための手法です。
> 多くの変数に重み（ウェイト）をつけて少数の合成変数を作るのが主成分分析です。重みのつけ方は合成変数ができるだけ多く元の変数の情報量を含むようにします。できるだけ多くの情報をもつ合成変数（主成分）を順次作っていきます。\n
> ref. https://www.macromill.com/service/data_analysis/principal-component-analysis.html

例えば図1のように、各データの(x, y)座標という2次元情報を使わなくても、各データが直線lとmの交点からlに沿ってどれくらい離れているかという1次元の情報である程度把握できる。
'''
st.image(img_01, caption='図1')
r'''
2次元のデータ(図2)を直線に射影すると、各データはその垂線と直線の交点、$(\bar{x}, \bar{y})$との距離の値に置き換わる。（1次元データ）

ただし、$(\bar{x}, \bar{y})$より右が正の値、左が負の値とする。

この直線を選ぶ基準はできるだけ「情報の損失を最小」にする必要がある。
'''
st.image(img_02, caption='図2')
r'''
情報の損失を最小化する最適化問題として定式化

求める直線の方向ベクトルを$(a, b)^{T}$とする。（ただし、$a^{2}+b^{2}=1$）

データの垂線と直線の交点座標（$(\bar{x}, \bar{y})$からの距離）を$z_{i}$とすると、すなわち$(a, b)^{T}$と$(x_{i}- \bar{x}, y_{i}- \bar{y})$という2つのベクトルの内積に等しく

$z_{i}=a(x_{i}- \bar{x})+b(y_{i}- \bar{y})$となる。

求めたいのは「情報の損失を最小」にする直線だが、それは「$z_{i}$たちの大きさをできるだけ大きく」する直線とイコールである。
'''
st.image(img_03, caption='図3')

r'''
「情報の損失の最小化」のかわりに$z_{i}$たちの大きさの総和（であると同時にバラツキ具合）

$\frac{1}{n}\sum_{i=1}^{n}z_{i}^{2}=\frac{1}{n}\sum_{i=1}^{n}\left \{ a(x_{i}- \bar{x})+b(y_{i}- \bar{y}) \right \} ^{2}=a^{2}S_{xx}+2abS_{xy}+b^{2}S_{yy}$

を最大化する。ただし、

- $S_{xx}=\frac{1}{n}\sum_{i=1}^{n}(x_{i}- \bar{x})^{2}$
- $S_{xy}=\frac{1}{n}\sum_{i=1}^{n}(x_{i}- \bar{x})(y_{i}- \bar{y})$
- $S_{yy}=\frac{1}{n}\sum_{i=1}^{n}(y_{i}- \bar{y})^{2}$

これらをラグランジュ乗数法で解く

### 分析結果
'''

pca_score = gpd.read_file('./data/shp/pca_score.shp')
pca_score = pca_score.set_index('geo_id')

pca_num = st.sidebar.radio(
    "Which PCA pattern",
    ('第一主成分', '第二主成分', '第三主成分'))
if pca_num == '第一主成分':
    color = 'pca1_score'
    title = '第一主成分(寄与率＝64%)<br>南北勾配が見られるので、すなわち北半球か南半球かの指標'
elif pca_num == '第二主成分':
    color = 'pca2_score'
    title = '第二主成分(寄与率＝14%)<br>低緯度と中高緯度で勾配が見られるので、すなわち植物活動が活発かどうかの指標'
else:
    color = 'pca3_score'
    title = '第三主成分(寄与率＝5%)<br>南米沿岸域と東アジアやオーストラリア、南アフリカとの間に勾配が見られる。エルニーニョ現象に関連した遠隔相関か？'

fig = px.choropleth_mapbox(pca_score, geojson=gpd.GeoSeries(pca_score['geometry']).__geo_interface__, locations=pca_score.index, color=color,
                           color_continuous_scale='Jet', center={"lat": pca_score['lat'].mean(), "lon": pca_score['lon'].mean()},
                           hover_data=['lat', 'lon'], mapbox_style="carto-positron", opacity=0.5,zoom=1, width=1000, height=800, title=title)
st.plotly_chart(fig, use_container_width=False)

'''
### 補足

'''