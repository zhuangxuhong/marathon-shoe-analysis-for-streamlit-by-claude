# -*- coding: utf-8 -*-
"""
马拉松跑鞋品牌数据分析平台
分析乔丹品牌及国产/国际品牌在马拉松赛场上的地位变化
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="马拉松跑鞋品牌分析",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 自定义样式 ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .insight-box {
        background-color: #F0F9FF;
        border-left: 4px solid #0EA5E9;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    .warning-box {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    .success-box {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 数据加载 ====================
@st.cache_data
def load_data():
    with open('data/marathon_shoe_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data['records'])
    df['share_pct'] = df['share'] * 100
    brands_info = data['brands']
    return df, brands_info

df, brands_info = load_data()

# ==================== 辅助函数 ====================
def get_trend_icon(change):
    """根据变化值返回趋势图标"""
    if change > 0:
        return "📈", "上升", "#10B981"
    elif change < 0:
        return "📉", "下降", "#EF4444"
    else:
        return "➡️", "持平", "#6B7280"

def generate_brand_analysis(brand_df, brand_name):
    """生成品牌智能分析"""
    analysis = []
    
    # 按人群分组分析
    for cohort in brand_df['cohort'].unique():
        cohort_df = brand_df[brand_df['cohort'] == cohort].sort_values('year')
        
        if len(cohort_df) < 2:
            continue
            
        first_year = cohort_df.iloc[0]
        last_year = cohort_df.iloc[-1]
        
        rank_change = first_year['rank'] - last_year['rank']
        share_change = last_year['share_pct'] - first_year['share_pct']
        
        # 最佳和最差表现
        best_record = cohort_df.loc[cohort_df['rank'].idxmin()]
        worst_record = cohort_df.loc[cohort_df['rank'].idxmax()]
        
        analysis.append({
            'cohort': cohort,
            'first_year': int(first_year['year']),
            'last_year': int(last_year['year']),
            'first_rank': int(first_year['rank']),
            'last_rank': int(last_year['rank']),
            'rank_change': int(rank_change),
            'first_share': first_year['share_pct'],
            'last_share': last_year['share_pct'],
            'share_change': share_change,
            'best_year': int(best_record['year']),
            'best_rank': int(best_record['rank']),
            'best_event': best_record['event'],
            'worst_year': int(worst_record['year']),
            'worst_rank': int(worst_record['rank']),
            'worst_event': worst_record['event']
        })
    
    return analysis

def generate_comparison_report(selected_brands, df, cohort_filter, event_filter):
    """生成多品牌对比分析报告"""
    report = []
    
    filtered_df = df.copy()
    if cohort_filter != "全部":
        filtered_df = filtered_df[filtered_df['cohort'] == cohort_filter]
    if event_filter != "全部":
        filtered_df = filtered_df[filtered_df['event'] == event_filter]
    
    brand_stats = []
    for brand in selected_brands:
        brand_df = filtered_df[filtered_df['brand'] == brand]
        if len(brand_df) == 0:
            continue
            
        avg_rank = brand_df['rank'].mean()
        avg_share = brand_df['share_pct'].mean()
        best_rank = brand_df['rank'].min()
        worst_rank = brand_df['rank'].max()
        
        # 计算趋势
        yearly = brand_df.groupby('year').agg({'rank': 'mean', 'share_pct': 'mean'}).reset_index()
        if len(yearly) >= 2:
            rank_trend = yearly.iloc[0]['rank'] - yearly.iloc[-1]['rank']
            share_trend = yearly.iloc[-1]['share_pct'] - yearly.iloc[0]['share_pct']
        else:
            rank_trend = 0
            share_trend = 0
        
        brand_type = brands_info.get(brand, {}).get('type', 'unknown')
        brand_type_cn = '国产' if brand_type == 'domestic' else ('国际' if brand_type == 'international' else '其他')
        
        brand_stats.append({
            'brand': brand,
            'brand_type': brand_type_cn,
            'avg_rank': avg_rank,
            'avg_share': avg_share,
            'best_rank': best_rank,
            'worst_rank': worst_rank,
            'rank_trend': rank_trend,
            'share_trend': share_trend,
            'data_points': len(brand_df)
        })
    
    return sorted(brand_stats, key=lambda x: x['avg_rank'])

# ==================== 侧边栏 ====================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/running--v1.png", width=80)
    st.markdown("## 🏃 马拉松跑鞋分析")
    st.markdown("---")
    
    # 导航
    page = st.radio(
        "选择分析模块",
        ["🏠 总览", "👟 乔丹专题", "🌏 国产vs国际", "⚖️ 品牌对比", "📊 数据浏览"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 📅 数据范围")
    st.markdown(f"- **赛事**: {df['event'].nunique()} 场")
    st.markdown(f"- **年份**: {df['year'].min()}-{df['year'].max()}")
    st.markdown(f"- **品牌**: {df['brand'].nunique()} 个")
    st.markdown(f"- **记录**: {len(df)} 条")
    
    st.markdown("---")
    st.markdown("### 📌 关于")
    st.markdown("数据来源：悦跑圈等平台统计")
    st.markdown("分析目标：乔丹品牌地位变化")

# ==================== 主页面 ====================

# ---------- 总览页面 ----------
if page == "🏠 总览":
    st.markdown('<p class="main-header">🏃 马拉松跑鞋品牌数据分析平台</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">深度分析乔丹品牌及国产/国际品牌在马拉松赛场上的地位变化</p>', unsafe_allow_html=True)
    
    # 核心指标卡片
    col1, col2, col3, col4 = st.columns(4)
    
    # 乔丹最新数据
    jordan_latest = df[(df['brand'] == '乔丹') & (df['year'] == 2025)]
    jordan_sub3 = jordan_latest[jordan_latest['cohort'] == '破3选手']
    jordan_all = jordan_latest[jordan_latest['cohort'] == '全局跑者']
    
    with col1:
        st.metric(
            label="🏅 乔丹破3选手最佳排名(2025)",
            value=f"第{int(jordan_sub3['rank'].min())}名" if len(jordan_sub3) > 0 else "无数据",
            delta=None
        )
    
    with col2:
        st.metric(
            label="👥 乔丹全局跑者最佳排名(2025)",
            value=f"第{int(jordan_all['rank'].min())}名" if len(jordan_all) > 0 else "无数据",
            delta=None
        )
    
    # 国产品牌占比
    domestic_2025 = df[(df['year'] == 2025) & (df['brand_type'] == 'domestic')]
    domestic_share = domestic_2025.groupby(['event', 'cohort'])['share'].sum().mean() * 100
    
    with col3:
        st.metric(
            label="🇨🇳 国产品牌平均占比(2025)",
            value=f"{domestic_share:.1f}%",
            delta=None
        )
    
    # 特步霸主地位
    xtep_wins = len(df[(df['brand'] == '特步') & (df['rank'] == 1)])
    total_rankings = df.groupby(['year', 'event', 'cohort']).ngroups
    
    with col4:
        st.metric(
            label="👑 特步夺冠次数",
            value=f"{xtep_wins} 次",
            delta=f"占比 {xtep_wins/total_rankings*100:.0f}%"
        )
    
    st.markdown("---")
    
    # 两列布局
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📈 乔丹品牌排名趋势")
        
        jordan_df = df[df['brand'] == '乔丹'].copy()
        jordan_trend = jordan_df.groupby(['year', 'cohort']).agg({
            'rank': 'mean',
            'share_pct': 'mean'
        }).reset_index()
        
        fig = px.line(
            jordan_trend, 
            x='year', 
            y='rank', 
            color='cohort',
            markers=True,
            color_discrete_map={'破3选手': '#EF4444', '全局跑者': '#3B82F6'}
        )
        fig.update_yaxis(autorange="reversed", title="平均排名")
        fig.update_xaxis(title="年份", dtick=1)
        fig.update_layout(
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.markdown("### 🌏 国产vs国际品牌占比趋势")
        
        type_trend = df.groupby(['year', 'cohort', 'brand_type'])['share'].sum().reset_index()
        type_trend = type_trend[type_trend['brand_type'].isin(['domestic', 'international'])]
        type_trend['share_pct'] = type_trend['share'] * 100
        type_trend['brand_type_cn'] = type_trend['brand_type'].map({'domestic': '国产品牌', 'international': '国际品牌'})
        
        # 只看破3选手
        type_trend_sub3 = type_trend[type_trend['cohort'] == '破3选手']
        
        fig = px.area(
            type_trend_sub3,
            x='year',
            y='share_pct',
            color='brand_type_cn',
            color_discrete_map={'国产品牌': '#3B82F6', '国际品牌': '#10B981'}
        )
        fig.update_xaxis(title="年份", dtick=1)
        fig.update_yaxis(title="市场份额 (%)")
        fig.update_layout(
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 关键洞察
    st.markdown("---")
    st.markdown("### 💡 关键洞察")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="warning-box">
        <strong>⚠️ 乔丹品牌警示</strong><br>
        乔丹在破3选手中的排名从2022年的第2-3名下滑至2025年的第6-8名，高端市场竞争力明显减弱。
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="success-box">
        <strong>✅ 国产品牌崛起</strong><br>
        2021年国际品牌主导市场，到2025年国产品牌在破3选手中占比超过70%，实现全面反超。
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="insight-box">
        <strong>📊 特步一枝独秀</strong><br>
        特步在多数赛事中稳居第一，2025年破3选手市场份额普遍超过25%，龙头地位稳固。
        </div>
        """, unsafe_allow_html=True)

# ---------- 乔丹专题页面 ----------
elif page == "👟 乔丹专题":
    st.markdown("## 👟 乔丹品牌深度分析")
    st.markdown("追踪乔丹跑鞋在马拉松赛场上的江湖地位变化")
    
    st.markdown("---")
    
    # 筛选器
    col1, col2 = st.columns(2)
    with col1:
        event_filter = st.selectbox("选择赛事", ["全部"] + list(df['event'].unique()), key="jordan_event")
    with col2:
        cohort_filter = st.selectbox("选择人群", ["全部", "破3选手", "全局跑者"], key="jordan_cohort")
    
    # 筛选数据
    jordan_df = df[df['brand'] == '乔丹'].copy()
    if event_filter != "全部":
        jordan_df = jordan_df[jordan_df['event'] == event_filter]
    if cohort_filter != "全部":
        jordan_df = jordan_df[jordan_df['cohort'] == cohort_filter]
    
    # 核心指标
    st.markdown("### 📊 核心指标")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        best_rank = jordan_df['rank'].min()
        best_record = jordan_df[jordan_df['rank'] == best_rank].iloc[0]
        st.metric(
            "🏆 历史最佳排名",
            f"第{int(best_rank)}名",
            f"{best_record['event']} {int(best_record['year'])}年"
        )
    
    with col2:
        worst_rank = jordan_df['rank'].max()
        worst_record = jordan_df[jordan_df['rank'] == worst_rank].iloc[0]
        st.metric(
            "📉 历史最差排名",
            f"第{int(worst_rank)}名",
            f"{worst_record['event']} {int(worst_record['year'])}年"
        )
    
    with col3:
        avg_rank = jordan_df['rank'].mean()
        st.metric("📈 平均排名", f"第{avg_rank:.1f}名")
    
    with col4:
        avg_share = jordan_df['share_pct'].mean()
        st.metric("📊 平均市场份额", f"{avg_share:.1f}%")
    
    st.markdown("---")
    
    # 图表
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📈 排名变化趋势")
        
        if cohort_filter == "全部":
            jordan_trend = jordan_df.groupby(['year', 'cohort'])['rank'].mean().reset_index()
            fig = px.line(
                jordan_trend, x='year', y='rank', color='cohort',
                markers=True,
                color_discrete_map={'破3选手': '#EF4444', '全局跑者': '#3B82F6'}
            )
        else:
            jordan_trend = jordan_df.groupby(['year', 'event'])['rank'].mean().reset_index()
            fig = px.line(jordan_trend, x='year', y='rank', color='event', markers=True)
        
        fig.update_yaxis(autorange="reversed", title="排名")
        fig.update_xaxis(title="年份", dtick=1)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.markdown("### 📊 市场份额变化")
        
        if cohort_filter == "全部":
            jordan_share = jordan_df.groupby(['year', 'cohort'])['share_pct'].mean().reset_index()
            fig = px.bar(
                jordan_share, x='year', y='share_pct', color='cohort',
                barmode='group',
                color_discrete_map={'破3选手': '#EF4444', '全局跑者': '#3B82F6'}
            )
        else:
            jordan_share = jordan_df.groupby(['year', 'event'])['share_pct'].mean().reset_index()
            fig = px.bar(jordan_share, x='year', y='share_pct', color='event', barmode='group')
        
        fig.update_yaxis(title="市场份额 (%)")
        fig.update_xaxis(title="年份", dtick=1)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # 各赛事表现热力图
    st.markdown("---")
    st.markdown("### 🗺️ 各赛事排名热力图")
    
    jordan_heatmap = jordan_df.pivot_table(
        values='rank', 
        index='event', 
        columns='year', 
        aggfunc='mean'
    )
    
    fig = px.imshow(
        jordan_heatmap,
        labels=dict(x="年份", y="赛事", color="排名"),
        color_continuous_scale='RdYlGn_r',
        aspect="auto"
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)
    
    # 智能分析
    st.markdown("---")
    st.markdown("### 🤖 智能分析报告")
    
    analysis = generate_brand_analysis(df[df['brand'] == '乔丹'], '乔丹')
    
    for item in analysis:
        trend_icon, trend_text, trend_color = get_trend_icon(item['rank_change'])
        
        if item['rank_change'] > 0:
            box_class = "success-box"
        elif item['rank_change'] < 0:
            box_class = "warning-box"
        else:
            box_class = "insight-box"
        
        st.markdown(f"""
        <div class="{box_class}">
        <strong>{item['cohort']} {trend_icon}</strong><br>
        • 排名变化：第{item['first_rank']}名 ({item['first_year']}) → 第{item['last_rank']}名 ({item['last_year']})，
        {"上升" if item['rank_change'] > 0 else "下降"}{abs(item['rank_change'])}个名次<br>
        • 份额变化：{item['first_share']:.1f}% → {item['last_share']:.1f}%，
        {"增长" if item['share_change'] > 0 else "下降"}{abs(item['share_change']):.1f}个百分点<br>
        • 最佳表现：{item['best_event']} {item['best_year']}年 第{item['best_rank']}名<br>
        • 最差表现：{item['worst_event']} {item['worst_year']}年 第{item['worst_rank']}名
        </div>
        """, unsafe_allow_html=True)

# ---------- 国产vs国际页面 ----------
elif page == "🌏 国产vs国际":
    st.markdown("## 🌏 国产品牌 vs 国际品牌")
    st.markdown("分析国产品牌在马拉松赛场上的崛起之路")
    
    st.markdown("---")
    
    # 筛选器
    col1, col2 = st.columns(2)
    with col1:
        cohort_filter = st.selectbox("选择人群", ["破3选手", "全局跑者", "全部"], key="type_cohort")
    with col2:
        event_filter = st.selectbox("选择赛事", ["全部"] + list(df['event'].unique()), key="type_event")
    
    # 筛选数据
    filtered_df = df.copy()
    if cohort_filter != "全部":
        filtered_df = filtered_df[filtered_df['cohort'] == cohort_filter]
    if event_filter != "全部":
        filtered_df = filtered_df[filtered_df['event'] == event_filter]
    
    # 计算国产/国际占比
    type_summary = filtered_df.groupby(['year', 'brand_type'])['share'].sum().reset_index()
    type_summary = type_summary[type_summary['brand_type'].isin(['domestic', 'international'])]
    type_summary['share_pct'] = type_summary['share'] * 100
    type_summary['brand_type_cn'] = type_summary['brand_type'].map({
        'domestic': '国产品牌', 
        'international': '国际品牌'
    })
    
    # 核心指标
    col1, col2, col3, col4 = st.columns(4)
    
    domestic_2021 = type_summary[(type_summary['year'] == type_summary['year'].min()) & (type_summary['brand_type'] == 'domestic')]['share_pct'].values
    domestic_2025 = type_summary[(type_summary['year'] == type_summary['year'].max()) & (type_summary['brand_type'] == 'domestic')]['share_pct'].values
    
    with col1:
        val = domestic_2021[0] if len(domestic_2021) > 0 else 0
        st.metric("🇨🇳 国产品牌占比(起始年)", f"{val:.1f}%")
    
    with col2:
        val = domestic_2025[0] if len(domestic_2025) > 0 else 0
        st.metric("🇨🇳 国产品牌占比(最新)", f"{val:.1f}%")
    
    with col3:
        if len(domestic_2021) > 0 and len(domestic_2025) > 0:
            change = domestic_2025[0] - domestic_2021[0]
            st.metric("📈 国产品牌增长", f"+{change:.1f}%")
        else:
            st.metric("📈 国产品牌增长", "N/A")
    
    with col4:
        # 国产品牌TOP10数量
        top10_domestic = filtered_df[(filtered_df['rank'] <= 10) & (filtered_df['brand_type'] == 'domestic')]
        top10_count = top10_domestic.groupby('year').size().mean()
        st.metric("🏅 TOP10中国产品牌数(均)", f"{top10_count:.1f}个")
    
    st.markdown("---")
    
    # 图表
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📊 市场份额变化趋势")
        
        fig = px.area(
            type_summary,
            x='year',
            y='share_pct',
            color='brand_type_cn',
            color_discrete_map={'国产品牌': '#EF4444', '国际品牌': '#3B82F6'}
        )
        fig.update_xaxis(title="年份", dtick=1)
        fig.update_yaxis(title="市场份额 (%)")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.markdown("### 📈 TOP10品牌数量变化")
        
        top10_by_type = filtered_df[filtered_df['rank'] <= 10].groupby(['year', 'brand_type']).size().reset_index(name='count')
        top10_by_type = top10_by_type[top10_by_type['brand_type'].isin(['domestic', 'international'])]
        top10_by_type['brand_type_cn'] = top10_by_type['brand_type'].map({
            'domestic': '国产品牌', 
            'international': '国际品牌'
        })
        
        fig = px.bar(
            top10_by_type,
            x='year',
            y='count',
            color='brand_type_cn',
            barmode='group',
            color_discrete_map={'国产品牌': '#EF4444', '国际品牌': '#3B82F6'}
        )
        fig.update_xaxis(title="年份", dtick=1)
        fig.update_yaxis(title="品牌数量")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # 代表品牌趋势
    st.markdown("---")
    st.markdown("### 🏃 代表品牌排名变化")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 国产品牌TOP5")
        domestic_brands = ['特步', '李宁', '安踏', '鸿星尔克', '乔丹']
        domestic_trend = filtered_df[filtered_df['brand'].isin(domestic_brands)]
        domestic_trend = domestic_trend.groupby(['year', 'brand'])['rank'].mean().reset_index()
        
        fig = px.line(domestic_trend, x='year', y='rank', color='brand', markers=True)
        fig.update_yaxis(autorange="reversed", title="平均排名")
        fig.update_xaxis(title="年份", dtick=1)
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 国际品牌TOP5")
        international_brands = ['Nike', 'Adidas', 'ASICS', 'Saucony', 'HOKA']
        international_trend = filtered_df[filtered_df['brand'].isin(international_brands)]
        international_trend = international_trend.groupby(['year', 'brand'])['rank'].mean().reset_index()
        
        fig = px.line(international_trend, x='year', y='rank', color='brand', markers=True)
        fig.update_yaxis(autorange="reversed", title="平均排名")
        fig.update_xaxis(title="年份", dtick=1)
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    # 智能分析
    st.markdown("---")
    st.markdown("### 🤖 智能分析报告")
    
    st.markdown("""
    <div class="success-box">
    <strong>📊 国产品牌崛起分析</strong><br><br>
    
    <strong>1. 整体趋势</strong><br>
    从数据可以看出，国产品牌在马拉松赛场上实现了从"追赶者"到"主导者"的华丽转身。
    以破3选手为例，国产品牌的市场份额从2021年的不足50%增长到2025年的超过70%。<br><br>
    
    <strong>2. 关键转折点</strong><br>
    2022-2023年是关键转折期。特步、鸿星尔克等品牌凭借碳板跑鞋技术的突破，
    在专业跑者群体中迅速获得认可，打破了Nike等国际品牌的垄断地位。<br><br>
    
    <strong>3. 分化趋势</strong><br>
    国产品牌内部出现明显分化：特步一骑绝尘稳居榜首，鸿星尔克、必迈等品牌快速上升，
    而乔丹则呈现下滑趋势，从第一梯队滑落至第二梯队。
    </div>
    """, unsafe_allow_html=True)

# ---------- 品牌对比页面 ----------
elif page == "⚖️ 品牌对比":
    st.markdown("## ⚖️ 自由品牌对比分析")
    st.markdown("选择任意品牌进行深度对比，系统将自动生成分析报告")
    
    st.markdown("---")
    
    # 品牌选择器
    all_brands = sorted(df['brand'].unique().tolist())
    # 预设一些常见品牌在前面
    popular_brands = ['乔丹', '特步', 'Nike', 'Adidas', '李宁', '鸿星尔克', '安踏', 'ASICS', 'Saucony', 'HOKA']
    default_brands = ['乔丹', '特步', 'Nike']
    
    selected_brands = st.multiselect(
        "选择要对比的品牌（最多5个）",
        options=all_brands,
        default=default_brands,
        max_selections=5
    )
    
    col1, col2 = st.columns(2)
    with col1:
        cohort_filter = st.selectbox("选择人群", ["全部", "破3选手", "全局跑者"], key="compare_cohort")
    with col2:
        event_filter = st.selectbox("选择赛事", ["全部"] + list(df['event'].unique()), key="compare_event")
    
    if len(selected_brands) < 2:
        st.warning("⚠️ 请至少选择2个品牌进行对比")
    else:
        # 筛选数据
        filtered_df = df[df['brand'].isin(selected_brands)].copy()
        if cohort_filter != "全部":
            filtered_df = filtered_df[filtered_df['cohort'] == cohort_filter]
        if event_filter != "全部":
            filtered_df = filtered_df[filtered_df['event'] == event_filter]
        
        st.markdown("---")
        
        # 对比图表
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("### 📈 排名对比趋势")
            
            trend_data = filtered_df.groupby(['year', 'brand'])['rank'].mean().reset_index()
            
            fig = px.line(
                trend_data, 
                x='year', 
                y='rank', 
                color='brand',
                markers=True
            )
            fig.update_yaxis(autorange="reversed", title="平均排名")
            fig.update_xaxis(title="年份", dtick=1)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            st.markdown("### 📊 市场份额对比")
            
            share_data = filtered_df.groupby(['year', 'brand'])['share_pct'].mean().reset_index()
            
            fig = px.bar(
                share_data,
                x='year',
                y='share_pct',
                color='brand',
                barmode='group'
            )
            fig.update_yaxis(title="市场份额 (%)")
            fig.update_xaxis(title="年份", dtick=1)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # 雷达图对比
        st.markdown("---")
        st.markdown("### 🎯 综合实力雷达图")
        
        # 计算各品牌指标
        radar_data = []
        for brand in selected_brands:
            brand_df = filtered_df[filtered_df['brand'] == brand]
            if len(brand_df) == 0:
                continue
            
            # 各项指标（归一化到0-100）
            avg_rank = brand_df['rank'].mean()
            avg_share = brand_df['share_pct'].mean()
            best_rank = brand_df['rank'].min()
            stability = 100 - brand_df['rank'].std() * 5  # 稳定性
            coverage = brand_df['event'].nunique() / df['event'].nunique() * 100  # 赛事覆盖率
            
            radar_data.append({
                'brand': brand,
                '平均排名': max(0, 100 - avg_rank * 5),
                '市场份额': min(100, avg_share * 5),
                '最佳表现': max(0, 100 - best_rank * 8),
                '稳定性': max(0, stability),
                '赛事覆盖': coverage
            })
        
        if radar_data:
            categories = ['平均排名', '市场份额', '最佳表现', '稳定性', '赛事覆盖']
            
            fig = go.Figure()
            
            for item in radar_data:
                fig.add_trace(go.Scatterpolar(
                    r=[item[cat] for cat in categories],
                    theta=categories,
                    fill='toself',
                    name=item['brand']
                ))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                height=450
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 智能分析报告
        st.markdown("---")
        st.markdown("### 🤖 智能分析报告")
        
        report = generate_comparison_report(selected_brands, df, cohort_filter, event_filter)
        
        if report:
            # 排名表格
            st.markdown("#### 📋 品牌综合排名")
            
            report_df = pd.DataFrame(report)
            report_df['排名趋势'] = report_df['rank_trend'].apply(
                lambda x: "📈 上升" if x > 0 else ("📉 下降" if x < 0 else "➡️ 持平")
            )
            report_df['份额趋势'] = report_df['share_trend'].apply(
                lambda x: f"+{x:.1f}%" if x > 0 else f"{x:.1f}%"
            )
            
            display_df = report_df[['brand', 'brand_type', 'avg_rank', 'avg_share', 'best_rank', '排名趋势', '份额趋势']].copy()
            display_df.columns = ['品牌', '类型', '平均排名', '平均份额(%)', '最佳排名', '排名趋势', '份额变化']
            display_df['平均排名'] = display_df['平均排名'].round(1)
            display_df['平均份额(%)'] = display_df['平均份额(%)'].round(1)
            display_df['最佳排名'] = display_df['最佳排名'].astype(int)
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # 文字分析
            st.markdown("#### 💡 对比分析结论")
            
            # 找出表现最好和最差的品牌
            best_brand = report[0]
            worst_brand = report[-1]
            
            # 生成分析文字
            analysis_text = f"""
            <div class="insight-box">
            <strong>📊 综合对比分析</strong><br><br>
            
            <strong>1. 整体排名</strong><br>
            在所选品牌中，<strong>{best_brand['brand']}</strong>表现最佳，平均排名第{best_brand['avg_rank']:.1f}名，
            平均市场份额{best_brand['avg_share']:.1f}%。
            <strong>{worst_brand['brand']}</strong>相对较弱，平均排名第{worst_brand['avg_rank']:.1f}名。<br><br>
            
            <strong>2. 发展趋势</strong><br>
            """
            
            for item in report:
                trend_icon, trend_text, _ = get_trend_icon(item['rank_trend'])
                analysis_text += f"• {item['brand']}：排名{trend_text}{abs(item['rank_trend']):.0f}个名次，份额{'增长' if item['share_trend'] > 0 else '下降'}{abs(item['share_trend']):.1f}%<br>"
            
            analysis_text += """<br>
            <strong>3. 竞争格局</strong><br>
            """
            
            domestic_count = sum(1 for item in report if item['brand_type'] == '国产')
            international_count = len(report) - domestic_count
            
            if domestic_count > international_count:
                analysis_text += f"所选品牌中国产品牌占多数（{domestic_count}个），反映了国产品牌在马拉松市场的主导地位。"
            else:
                analysis_text += f"所选品牌中国际品牌占多数（{international_count}个），但整体市场趋势显示国产品牌正在快速崛起。"
            
            analysis_text += "</div>"
            
            st.markdown(analysis_text, unsafe_allow_html=True)

# ---------- 数据浏览页面 ----------
elif page == "📊 数据浏览":
    st.markdown("## 📊 完整数据浏览")
    st.markdown("查看和筛选所有马拉松跑鞋品牌数据")
    
    st.markdown("---")
    
    # 筛选器
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        year_filter = st.multiselect("年份", sorted(df['year'].unique()), default=sorted(df['year'].unique()))
    with col2:
        event_filter = st.multiselect("赛事", df['event'].unique(), default=list(df['event'].unique()))
    with col3:
        cohort_filter = st.multiselect("人群", df['cohort'].unique(), default=list(df['cohort'].unique()))
    with col4:
        brand_type_filter = st.multiselect("品牌类型", ['domestic', 'international', 'other'], default=['domestic', 'international'])
    
    # 筛选数据
    filtered_df = df[
        (df['year'].isin(year_filter)) &
        (df['event'].isin(event_filter)) &
        (df['cohort'].isin(cohort_filter)) &
        (df['brand_type'].isin(brand_type_filter))
    ].copy()
    
    # 品牌搜索
    brand_search = st.text_input("🔍 搜索品牌", "")
    if brand_search:
        filtered_df = filtered_df[filtered_df['brand'].str.contains(brand_search, case=False)]
    
    st.markdown(f"**共 {len(filtered_df)} 条记录**")
    
    # 数据表格
    display_df = filtered_df[['year', 'event', 'cohort', 'rank', 'brand', 'brand_type', 'share_pct']].copy()
    display_df.columns = ['年份', '赛事', '人群', '排名', '品牌', '品牌类型', '份额(%)']
    display_df['品牌类型'] = display_df['品牌类型'].map({
        'domestic': '国产',
        'international': '国际',
        'other': '其他'
    })
    display_df['份额(%)'] = display_df['份额(%)'].round(1)
    display_df['排名'] = display_df['排名'].astype(int)
    
    st.dataframe(
        display_df.sort_values(['年份', '赛事', '人群', '排名'], ascending=[False, True, True, True]),
        use_container_width=True,
        height=500,
        hide_index=True
    )
    
    # 下载按钮
    csv = display_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下载CSV文件",
        data=csv,
        file_name="marathon_shoe_data.csv",
        mime="text/csv"
    )

# ==================== 页脚 ====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; padding: 1rem;">
    <p>📊 马拉松跑鞋品牌数据分析平台 | 数据来源：悦跑圈等平台统计</p>
    <p>🏃 专注于乔丹品牌及国产/国际品牌地位变化分析</p>
</div>
""", unsafe_allow_html=True)
