# -*- coding: utf-8 -*-
"""
马拉松跑鞋品牌数据分析平台 v2.0
结合Claude和Grok方案优点的优化版本
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# ==================== 页面配置 ====================
st.set_page_config(page_title="马拉松跑鞋品牌分析", page_icon="🏃", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1E3A8A; text-align: center; padding: 1rem 0; }
    .sub-header { font-size: 1.2rem; color: #64748B; text-align: center; margin-bottom: 2rem; }
    .insight-box { background-color: #F0F9FF; border-left: 4px solid #0EA5E9; padding: 1rem; margin: 1rem 0; border-radius: 0 8px 8px 0; color: #1E40AF; }
    .warning-box { background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 1rem; margin: 1rem 0; border-radius: 0 8px 8px 0; color: #92400E; }
    .success-box { background-color: #D1FAE5; border-left: 4px solid #10B981; padding: 1rem; margin: 1rem 0; border-radius: 0 8px 8px 0; color: #065F46; }
</style>
""", unsafe_allow_html=True)

# ==================== 数据加载 ====================
@st.cache_data
def load_data():
    with open('data/marathon_shoe_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data['records'])
    df['share_pct'] = df['share'] * 100
    df['year'] = df['year'].astype(int)
    df['rank'] = df['rank'].astype(int)
    df['type_zh'] = df['brand_type'].map({'domestic': '国产', 'international': '国际', 'other': '其他'})
    return df, data['brands']

df, brands_info = load_data()

# ==================== 辅助函数 ====================
def generate_dynamic_analysis(brand_data, brand_name):
    """动态生成品牌分析文案"""
    if len(brand_data) < 2:
        return f"**{brand_name}**：数据不足，无法生成趋势分析。"
    
    yearly = brand_data.groupby('year').agg({'share_pct': 'mean', 'rank': 'mean'}).reset_index().sort_values('year')
    start_share = yearly.iloc[0]['share_pct']
    end_share = yearly.iloc[-1]['share_pct']
    start_year = int(yearly.iloc[0]['year'])
    end_year = int(yearly.iloc[-1]['year'])
    
    share_change = end_share - start_share
    pct_change = (share_change / start_share * 100) if start_share > 0 else 0
    
    if share_change > 0:
        direction = "上升"
        icon = "📈"
    elif share_change < 0:
        direction = "下降"
        icon = "📉"
    else:
        direction = "持平"
        icon = "➡️"
    
    return f"{icon} **{brand_name}**：份额从 {start_share:.1f}%（{start_year}）→ {end_share:.1f}%（{end_year}），{direction}{abs(share_change):.1f}个百分点（{'+' if pct_change > 0 else ''}{pct_change:.1f}%）"

def calculate_yearly_rank(data, aggregate=True):
    """计算每年品牌排名"""
    if aggregate:
        yearly = data.groupby(['year', 'brand', 'type_zh'])['share'].mean().reset_index()
    else:
        yearly = data.groupby(['year', 'event', 'brand', 'type_zh'])['share'].mean().reset_index()
    
    def add_rank(group):
        group = group.copy()
        group['rank'] = group['share'].rank(ascending=False, method='min').astype(int)
        return group
    
    if aggregate:
        ranked = yearly.groupby('year').apply(add_rank).reset_index(drop=True)
    else:
        ranked = yearly.groupby(['year', 'event']).apply(add_rank).reset_index(drop=True)
    
    return ranked

# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown("## 🏃 马拉松跑鞋分析")
    st.markdown("---")
    
    # 全局筛选器
    st.markdown("### 🎯 全局筛选")
    
    all_events = sorted(df['event'].unique().tolist())
    selected_events = st.multiselect("选择赛事", all_events, default=all_events)
    
    min_year, max_year = int(df['year'].min()), int(df['year'].max())
    year_range = st.slider("年份范围", min_year, max_year, (min_year, max_year))
    
    cohort_filter = st.radio("跑者队列", ["破3选手", "全局跑者"], index=0)
    
    aggregate_mode = st.checkbox("聚合所有赛事（取平均）", value=True)
    
    st.markdown("---")
    st.markdown(f"### 📅 数据范围\n- 赛事: {len(selected_events)} 场\n- 年份: {year_range[0]}-{year_range[1]}\n- 队列: {cohort_filter}")

# 应用全局筛选
filtered_df = df[
    (df['event'].isin(selected_events)) &
    (df['year'].between(year_range[0], year_range[1])) &
    (df['cohort'] == cohort_filter)
].copy()

# ==================== 主页面 - Tab布局 ====================
st.markdown('<p class="main-header">🏃 马拉松跑鞋品牌数据分析平台</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">深度分析乔丹品牌及国产/国际品牌在马拉松赛场上的地位变化</p>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 总览排行", "👟 乔丹专题", "⚖️ 品牌对比", "🌏 国产vs国际"])

# ==================== Tab1: 总览排行 ====================
with tab1:
    st.markdown("### 📊 品牌排行榜")
    
    # 最新年份排行
    latest_year = year_range[1]
    latest_data = filtered_df[filtered_df['year'] == latest_year]
    
    if len(latest_data) == 0:
        st.warning("所选条件下暂无数据")
    else:
        if aggregate_mode:
            ranking = latest_data.groupby(['brand', 'type_zh'])['share_pct'].mean().reset_index()
        else:
            ranking = latest_data.groupby(['brand', 'type_zh'])['share_pct'].mean().reset_index()
        
        ranking = ranking.sort_values('share_pct', ascending=False).head(20).reset_index(drop=True)
        ranking['排名'] = range(1, len(ranking) + 1)
        ranking['份额(%)'] = ranking['share_pct'].round(1)
        
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.markdown(f"#### {latest_year}年 {cohort_filter} Top 20")
            display_df = ranking[['排名', 'brand', 'type_zh', '份额(%)']].copy()
            display_df.columns = ['排名', '品牌', '类型', '份额(%)']
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)
        
        with col2:
            st.markdown(f"#### {latest_year}年 份额分布")
            fig = px.bar(ranking.head(15), x='share_pct', y='brand', orientation='h',
                        color='type_zh', color_discrete_map={'国产': '#EF4444', '国际': '#3B82F6', '其他': '#9CA3AF'})
            fig.update_layout(height=500, yaxis=dict(autorange='reversed', title=''), xaxis=dict(title='份额 (%)'),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig, use_container_width=True)
        
        # 核心指标卡片
        st.markdown("---")
        st.markdown("### 💡 关键洞察")
        
        c1, c2, c3, c4 = st.columns(4)
        
        # 乔丹排名
        jordan_rank = ranking[ranking['brand'] == '乔丹']['排名'].values
        jordan_share = ranking[ranking['brand'] == '乔丹']['份额(%)'].values
        
        with c1:
            if len(jordan_rank) > 0:
                st.metric(f"🏅 乔丹排名({latest_year})", f"第{int(jordan_rank[0])}名", f"份额 {jordan_share[0]}%")
            else:
                st.metric(f"🏅 乔丹排名({latest_year})", "未进TOP20")
        
        # 特步数据
        xtep_data = ranking[ranking['brand'] == '特步']
        with c2:
            if len(xtep_data) > 0:
                st.metric("👑 特步份额", f"{xtep_data['份额(%)'].values[0]}%", "领跑市场")
        
        # 国产占比
        domestic_share = ranking[ranking['type_zh'] == '国产']['份额(%)'].sum()
        with c3:
            st.metric("🇨🇳 国产品牌占比", f"{domestic_share:.1f}%")
        
        # TOP10国产数量
        top10_domestic = len(ranking.head(10)[ranking.head(10)['type_zh'] == '国产'])
        with c4:
            st.metric("🏆 TOP10国产品牌数", f"{top10_domestic} 个")

# ==================== Tab2: 乔丹专题 ====================
with tab2:
    st.markdown("### 👟 乔丹品牌深度分析")
    
    jordan_data = filtered_df[filtered_df['brand'] == '乔丹'].copy()
    
    if len(jordan_data) == 0:
        st.warning("所选条件下暂无乔丹品牌数据")
    else:
        # 核心指标
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            best = jordan_data.loc[jordan_data['rank'].idxmin()]
            st.metric("🏆 历史最佳排名", f"第{int(best['rank'])}名", f"{best['event']} {int(best['year'])}")
        with c2:
            worst = jordan_data.loc[jordan_data['rank'].idxmax()]
            st.metric("📉 历史最差排名", f"第{int(worst['rank'])}名", f"{worst['event']} {int(worst['year'])}")
        with c3:
            st.metric("📈 平均排名", f"第{jordan_data['rank'].mean():.1f}名")
        with c4:
            st.metric("📊 平均份额", f"{jordan_data['share_pct'].mean():.1f}%")
        
        st.markdown("---")
        
        # 查看模式切换
        view_mode = st.radio("查看模式", ["份额趋势", "排名趋势"], horizontal=True)
        
        col_l, col_r = st.columns(2)
        
        with col_l:
            if view_mode == "份额趋势":
                st.markdown("#### 📈 份额变化趋势")
                if aggregate_mode:
                    trend = jordan_data.groupby('year')['share_pct'].mean().reset_index()
                else:
                    trend = jordan_data.groupby(['year', 'event'])['share_pct'].mean().reset_index()
                
                if aggregate_mode:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=trend['year'], y=trend['share_pct'], mode='lines+markers',
                                            name='乔丹', line=dict(color='#EF4444', width=3), marker=dict(size=10)))
                else:
                    fig = go.Figure()
                    for event in trend['event'].unique():
                        event_data = trend[trend['event'] == event]
                        fig.add_trace(go.Scatter(x=event_data['year'], y=event_data['share_pct'],
                                                mode='lines+markers', name=event))
                
                fig.update_layout(height=400, yaxis=dict(title='份额 (%)'), xaxis=dict(title='年份', dtick=1))
                st.plotly_chart(fig, use_container_width=True)
            
            else:  # 排名趋势
                st.markdown("#### 📊 排名变化趋势")
                ranked_data = calculate_yearly_rank(filtered_df, aggregate_mode)
                jordan_rank = ranked_data[ranked_data['brand'] == '乔丹']
                
                if aggregate_mode:
                    rank_trend = jordan_rank.groupby('year')['rank'].mean().reset_index()
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=rank_trend['year'], y=rank_trend['rank'], mode='lines+markers',
                                            name='乔丹', line=dict(color='#EF4444', width=3), marker=dict(size=10)))
                else:
                    fig = go.Figure()
                    for event in jordan_rank['event'].unique():
                        event_data = jordan_rank[jordan_rank['event'] == event]
                        fig.add_trace(go.Scatter(x=event_data['year'], y=event_data['rank'],
                                                mode='lines+markers', name=event))
                
                fig.update_layout(height=400, yaxis=dict(autorange='reversed', title='排名（越小越好）'),
                                xaxis=dict(title='年份', dtick=1))
                st.plotly_chart(fig, use_container_width=True)
        
        with col_r:
            st.markdown("#### 🗺️ 各赛事表现热力图")
            heatmap_data = jordan_data.pivot_table(values='rank', index='event', columns='year', aggfunc='mean')
            if len(heatmap_data) > 0:
                fig = px.imshow(heatmap_data, labels=dict(x="年份", y="赛事", color="排名"),
                               color_continuous_scale='RdYlGn_r', aspect="auto")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # 动态分析报告
        st.markdown("---")
        st.markdown("### 🤖 智能分析报告")
        
        analysis_text = generate_dynamic_analysis(jordan_data, '乔丹')
        
        # 计算更详细的分析
        yearly_jordan = jordan_data.groupby('year').agg({'share_pct': 'mean', 'rank': 'mean'}).reset_index().sort_values('year')
        if len(yearly_jordan) >= 2:
            start_rank = yearly_jordan.iloc[0]['rank']
            end_rank = yearly_jordan.iloc[-1]['rank']
            rank_change = end_rank - start_rank
            
            if rank_change > 0:
                box_class = "warning-box"
                trend_text = f"排名从第{start_rank:.0f}名下滑至第{end_rank:.0f}名，下降了{rank_change:.0f}个位次"
            elif rank_change < 0:
                box_class = "success-box"
                trend_text = f"排名从第{start_rank:.0f}名上升至第{end_rank:.0f}名，提升了{abs(rank_change):.0f}个位次"
            else:
                box_class = "insight-box"
                trend_text = f"排名保持在第{end_rank:.0f}名左右，相对稳定"
            
            st.markdown(f"""
            <div class="{box_class}">
            <strong>📊 乔丹品牌趋势分析</strong><br><br>
            {analysis_text}<br><br>
            <strong>排名变化：</strong>{trend_text}<br><br>
            <strong>市场定位：</strong>{"乔丹在全局跑者中保持较稳定的大众化地位，但在破3精英选手中的渗透率持续下滑，表明其在高端竞技领域的竞争力正被其他国产品牌蚕食。" if cohort_filter == "破3选手" else "乔丹在全局跑者市场中保持稳定份额，品牌认知度较高，但面临来自特步等头部国产品牌的激烈竞争。"}
            </div>
            """, unsafe_allow_html=True)

# ==================== Tab3: 品牌对比 ====================
with tab3:
    st.markdown("### ⚖️ 自由品牌对比分析")
    
    # 获取TOP品牌作为默认选项
    top_brands = filtered_df.groupby('brand')['share_pct'].mean().sort_values(ascending=False).head(10).index.tolist()
    default_brands = ['乔丹'] + [b for b in top_brands if b != '乔丹'][:4]
    
    all_brands = sorted(filtered_df['brand'].unique().tolist())
    selected_brands = st.multiselect("选择要对比的品牌（可多选）", all_brands, default=default_brands)
    
    if len(selected_brands) < 2:
        st.warning("请至少选择2个品牌进行对比")
    else:
        compare_df = filtered_df[filtered_df['brand'].isin(selected_brands)]
        
        col_l, col_r = st.columns(2)
        
        with col_l:
            st.markdown("#### 📈 份额趋势对比")
            if aggregate_mode:
                trend = compare_df.groupby(['year', 'brand'])['share_pct'].mean().reset_index()
            else:
                trend = compare_df.groupby(['year', 'brand'])['share_pct'].mean().reset_index()
            
            fig = go.Figure()
            for brand in selected_brands:
                brand_trend = trend[trend['brand'] == brand]
                if len(brand_trend) > 0:
                    fig.add_trace(go.Scatter(x=brand_trend['year'], y=brand_trend['share_pct'],
                                            mode='lines+markers', name=brand))
            fig.update_layout(height=400, yaxis=dict(title='份额 (%)'), xaxis=dict(title='年份', dtick=1))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_r:
            st.markdown("#### 📊 排名趋势对比")
            ranked = calculate_yearly_rank(filtered_df, aggregate_mode)
            ranked_compare = ranked[ranked['brand'].isin(selected_brands)]
            
            if aggregate_mode:
                rank_trend = ranked_compare.groupby(['year', 'brand'])['rank'].mean().reset_index()
            else:
                rank_trend = ranked_compare.groupby(['year', 'brand'])['rank'].mean().reset_index()
            
            fig = go.Figure()
            for brand in selected_brands:
                brand_rank = rank_trend[rank_trend['brand'] == brand]
                if len(brand_rank) > 0:
                    fig.add_trace(go.Scatter(x=brand_rank['year'], y=brand_rank['rank'],
                                            mode='lines+markers', name=brand))
            fig.update_layout(height=400, yaxis=dict(autorange='reversed', title='排名（越小越好）'),
                            xaxis=dict(title='年份', dtick=1))
            st.plotly_chart(fig, use_container_width=True)
        
        # 雷达图
        st.markdown("---")
        st.markdown("#### 🎯 综合实力雷达图")
        
        with st.expander("📖 点击查看雷达图各维度含义"):
            st.markdown("""
            | 维度 | 计算方式 | 含义说明 |
            |------|----------|----------|
            | **排名得分** | 100 - 平均排名×5 | 平均排名越靠前，得分越高 |
            | **份额得分** | 平均市场份额×5 | 市场份额越高，得分越高 |
            | **最佳表现** | 100 - 最佳排名×8 | 历史最佳排名越靠前，得分越高 |
            | **稳定性** | 100 - 排名标准差×5 | 排名波动越小，得分越高 |
            | **赛事覆盖** | 参与赛事数/总赛事数×100 | 参与的赛事越多，得分越高 |
            """)
        
        radar_data = []
        for brand in selected_brands:
            bd = compare_df[compare_df['brand'] == brand]
            if len(bd) == 0:
                continue
            radar_data.append({
                'brand': brand,
                '排名得分': max(0, min(100, 100 - bd['rank'].mean() * 5)),
                '份额得分': min(100, bd['share_pct'].mean() * 5),
                '最佳表现': max(0, min(100, 100 - bd['rank'].min() * 8)),
                '稳定性': max(0, min(100, 100 - bd['rank'].std() * 5)),
                '赛事覆盖': bd['event'].nunique() / df['event'].nunique() * 100
            })
        
        if radar_data:
            cats = ['排名得分', '份额得分', '最佳表现', '稳定性', '赛事覆盖']
            fig = go.Figure()
            for r in radar_data:
                fig.add_trace(go.Scatterpolar(r=[r[c] for c in cats], theta=cats, fill='toself', name=r['brand']))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=450)
            st.plotly_chart(fig, use_container_width=True)
        
        # 动态分析报告
        st.markdown("---")
        st.markdown("#### 🤖 自动分析总结")
        
        analysis_lines = []
        for brand in selected_brands:
            brand_data = compare_df[compare_df['brand'] == brand]
            analysis_lines.append(generate_dynamic_analysis(brand_data, brand))
        
        st.markdown("\n\n".join(analysis_lines))
        
        # 对比结论
        if len(radar_data) >= 2:
            sorted_by_rank = sorted(radar_data, key=lambda x: x['排名得分'], reverse=True)
            best = sorted_by_rank[0]
            worst = sorted_by_rank[-1]
            
            st.markdown(f"""
            <div class="insight-box">
            <strong>📊 对比结论</strong><br>
            • 综合表现最佳：<strong>{best['brand']}</strong>（排名得分 {best['排名得分']:.0f}）<br>
            • 相对较弱：<strong>{worst['brand']}</strong>（排名得分 {worst['排名得分']:.0f}）
            </div>
            """, unsafe_allow_html=True)

# ==================== Tab4: 国产vs国际 ====================
with tab4:
    st.markdown("### 🌏 国产品牌 vs 国际品牌")
    
    # 核心指标
    if aggregate_mode:
        type_trend = filtered_df.groupby(['year', 'brand_type', 'type_zh'])['share'].sum().reset_index()
    else:
        type_trend = filtered_df.groupby(['year', 'brand_type', 'type_zh'])['share'].sum().reset_index()
    
    type_trend['share_pct'] = type_trend['share'] * 100
    type_trend = type_trend[type_trend['brand_type'].isin(['domestic', 'international'])]
    
    if len(type_trend) > 0:
        min_yr = type_trend['year'].min()
        max_yr = type_trend['year'].max()
        
        dom_first = type_trend[(type_trend['year'] == min_yr) & (type_trend['brand_type'] == 'domestic')]['share_pct'].sum()
        dom_last = type_trend[(type_trend['year'] == max_yr) & (type_trend['brand_type'] == 'domestic')]['share_pct'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(f"🇨🇳 国产占比({min_yr})", f"{dom_first:.1f}%")
        with c2:
            st.metric(f"🇨🇳 国产占比({max_yr})", f"{dom_last:.1f}%")
        with c3:
            change = dom_last - dom_first
            st.metric("📈 国产增长", f"{change:+.1f}%")
        with c4:
            top10_dom = filtered_df[(filtered_df['rank'] <= 10) & (filtered_df['brand_type'] == 'domestic')]
            if len(top10_dom) > 0:
                st.metric("🏅 TOP10国产数(均)", f"{top10_dom.groupby('year').size().mean():.1f}个")
        
        st.markdown("---")
        col_l, col_r = st.columns(2)
        
        with col_l:
            st.markdown("#### 📊 市场份额趋势")
            yearly_type = type_trend.groupby(['year', 'type_zh'])['share_pct'].sum().reset_index()
            
            fig = go.Figure()
            for type_zh in ['国产', '国际']:
                td = yearly_type[yearly_type['type_zh'] == type_zh]
                color = '#EF4444' if type_zh == '国产' else '#3B82F6'
                fig.add_trace(go.Scatter(x=td['year'], y=td['share_pct'], mode='lines', fill='tozeroy',
                                        name=type_zh, line=dict(color=color)))
            fig.update_layout(height=400, yaxis=dict(title='份额 (%)'), xaxis=dict(title='年份', dtick=1))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_r:
            st.markdown("#### 📈 TOP10品牌数量变化")
            top10_by_type = filtered_df[filtered_df['rank'] <= 10].groupby(['year', 'type_zh']).size().reset_index(name='count')
            top10_by_type = top10_by_type[top10_by_type['type_zh'].isin(['国产', '国际'])]
            
            if len(top10_by_type) > 0:
                fig = go.Figure()
                for type_zh in ['国产', '国际']:
                    td = top10_by_type[top10_by_type['type_zh'] == type_zh]
                    color = '#EF4444' if type_zh == '国产' else '#3B82F6'
                    fig.add_trace(go.Bar(x=td['year'], y=td['count'], name=type_zh, marker_color=color))
                fig.update_layout(height=400, barmode='group', yaxis=dict(title='品牌数量'), xaxis=dict(title='年份', dtick=1))
                st.plotly_chart(fig, use_container_width=True)
        
        # 代表品牌趋势
        st.markdown("---")
        st.markdown("#### 🏃 代表品牌排名变化")
        
        cl, cr = st.columns(2)
        with cl:
            st.markdown("##### 国产品牌TOP5")
            dom_brands = ['特步', '李宁', '安踏', '鸿星尔克', '乔丹']
            dom_trend = filtered_df[filtered_df['brand'].isin(dom_brands)].groupby(['year', 'brand'])['rank'].mean().reset_index()
            
            if len(dom_trend) > 0:
                fig = go.Figure()
                for b in dom_brands:
                    bd = dom_trend[dom_trend['brand'] == b]
                    if len(bd) > 0:
                        fig.add_trace(go.Scatter(x=bd['year'], y=bd['rank'], mode='lines+markers', name=b))
                fig.update_layout(height=350, yaxis=dict(autorange='reversed', title='排名'), xaxis=dict(title='年份', dtick=1))
                st.plotly_chart(fig, use_container_width=True)
        
        with cr:
            st.markdown("##### 国际品牌TOP5")
            int_brands = ['Nike', 'Adidas', 'ASICS', 'Saucony', 'HOKA']
            int_trend = filtered_df[filtered_df['brand'].isin(int_brands)].groupby(['year', 'brand'])['rank'].mean().reset_index()
            
            if len(int_trend) > 0:
                fig = go.Figure()
                for b in int_brands:
                    bd = int_trend[int_trend['brand'] == b]
                    if len(bd) > 0:
                        fig.add_trace(go.Scatter(x=bd['year'], y=bd['rank'], mode='lines+markers', name=b))
                fig.update_layout(height=350, yaxis=dict(autorange='reversed', title='排名'), xaxis=dict(title='年份', dtick=1))
                st.plotly_chart(fig, use_container_width=True)
        
        # 智能分析
        st.markdown("---")
        st.markdown("#### 🤖 智能分析报告")
        
        growth_rate = (dom_last - dom_first) / dom_first * 100 if dom_first > 0 else 0
        
        st.markdown(f"""
        <div class="success-box">
        <strong>📊 国产品牌崛起分析</strong><br><br>
        <strong>1. 整体格局</strong><br>
        {max_yr}年国产品牌总份额达 <strong>{dom_last:.1f}%</strong>，较{min_yr}年的{dom_first:.1f}%增长了<strong>{change:.1f}个百分点</strong>（增幅{growth_rate:.1f}%）。<br><br>
        <strong>2. 竞争态势</strong><br>
        国产品牌在{"破3精英选手" if cohort_filter == "破3选手" else "全局跑者"}群体中{"占据绝对主导地位" if dom_last > 70 else "正在快速崛起"}，
        特步、必迈等品牌凭借碳板跑鞋技术突破，{"已打破" if dom_last > 60 else "正在挑战"}国际品牌的市场垄断。<br><br>
        <strong>3. 趋势预判</strong><br>
        按当前增长趋势，国产品牌有望在高端竞技跑鞋领域进一步扩大优势，但需持续关注产品创新和品质提升。
        </div>
        """, unsafe_allow_html=True)

# ==================== 页脚 ====================
st.markdown("---")
st.markdown('<div style="text-align:center;color:#64748B;padding:1rem;">📊 马拉松跑鞋品牌分析平台 v2.0 | 数据来源：悦跑圈等平台</div>', unsafe_allow_html=True)
