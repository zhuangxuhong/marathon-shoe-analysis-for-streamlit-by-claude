# -*- coding: utf-8 -*-
"""
马拉松跑鞋品牌数据分析平台
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

st.set_page_config(page_title="马拉松跑鞋品牌分析", page_icon="🏃", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1E3A8A; text-align: center; padding: 1rem 0; }
    .sub-header { font-size: 1.2rem; color: #64748B; text-align: center; margin-bottom: 2rem; }
    .insight-box { background-color: #F0F9FF; border-left: 4px solid #0EA5E9; padding: 1rem; margin: 1rem 0; border-radius: 0 8px 8px 0; }
    .warning-box { background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 1rem; margin: 1rem 0; border-radius: 0 8px 8px 0; }
    .success-box { background-color: #D1FAE5; border-left: 4px solid #10B981; padding: 1rem; margin: 1rem 0; border-radius: 0 8px 8px 0; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    with open('data/marathon_shoe_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data['records'])
    df['share_pct'] = df['share'] * 100
    df['year'] = df['year'].astype(int)
    df['rank'] = df['rank'].astype(int)
    return df, data['brands']

df, brands_info = load_data()

def get_trend_icon(change):
    if change > 0: return "📈", "上升", "#10B981"
    elif change < 0: return "📉", "下降", "#EF4444"
    else: return "➡️", "持平", "#6B7280"

def generate_brand_analysis(brand_df):
    analysis = []
    for cohort in brand_df['cohort'].unique():
        cohort_df = brand_df[brand_df['cohort'] == cohort].sort_values('year')
        if len(cohort_df) < 2: continue
        first, last = cohort_df.iloc[0], cohort_df.iloc[-1]
        best = cohort_df.loc[cohort_df['rank'].idxmin()]
        worst = cohort_df.loc[cohort_df['rank'].idxmax()]
        analysis.append({
            'cohort': cohort, 'first_year': int(first['year']), 'last_year': int(last['year']),
            'first_rank': int(first['rank']), 'last_rank': int(last['rank']),
            'rank_change': int(first['rank']) - int(last['rank']),
            'first_share': first['share_pct'], 'last_share': last['share_pct'],
            'share_change': last['share_pct'] - first['share_pct'],
            'best_year': int(best['year']), 'best_rank': int(best['rank']), 'best_event': best['event'],
            'worst_year': int(worst['year']), 'worst_rank': int(worst['rank']), 'worst_event': worst['event']
        })
    return analysis

def generate_comparison_report(selected_brands, df, cohort_filter, event_filter):
    filtered_df = df.copy()
    if cohort_filter != "全部": filtered_df = filtered_df[filtered_df['cohort'] == cohort_filter]
    if event_filter != "全部": filtered_df = filtered_df[filtered_df['event'] == event_filter]
    brand_stats = []
    for brand in selected_brands:
        brand_df = filtered_df[filtered_df['brand'] == brand]
        if len(brand_df) == 0: continue
        yearly = brand_df.groupby('year').agg({'rank': 'mean', 'share_pct': 'mean'}).reset_index()
        rank_trend = yearly.iloc[0]['rank'] - yearly.iloc[-1]['rank'] if len(yearly) >= 2 else 0
        share_trend = yearly.iloc[-1]['share_pct'] - yearly.iloc[0]['share_pct'] if len(yearly) >= 2 else 0
        brand_type = brands_info.get(brand, {}).get('type', 'unknown')
        brand_type_cn = '国产' if brand_type == 'domestic' else ('国际' if brand_type == 'international' else '其他')
        brand_stats.append({
            'brand': brand, 'brand_type': brand_type_cn, 'avg_rank': brand_df['rank'].mean(),
            'avg_share': brand_df['share_pct'].mean(), 'best_rank': int(brand_df['rank'].min()),
            'worst_rank': int(brand_df['rank'].max()), 'rank_trend': rank_trend, 'share_trend': share_trend
        })
    return sorted(brand_stats, key=lambda x: x['avg_rank'])

with st.sidebar:
    st.markdown("## 🏃 马拉松跑鞋分析")
    st.markdown("---")
    page = st.radio("选择分析模块", ["🏠 总览", "👟 乔丹专题", "🌏 国产vs国际", "⚖️ 品牌对比", "📊 数据浏览"])
    st.markdown("---")
    st.markdown(f"### 📅 数据范围\n- 赛事: {df['event'].nunique()} 场\n- 年份: {df['year'].min()}-{df['year'].max()}\n- 品牌: {df['brand'].nunique()} 个\n- 记录: {len(df)} 条")

if page == "🏠 总览":
    st.markdown('<p class="main-header">🏃 马拉松跑鞋品牌数据分析平台</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">深度分析乔丹品牌及国产/国际品牌在马拉松赛场上的地位变化</p>', unsafe_allow_html=True)
    
    max_year = df['year'].max()
    jordan_latest = df[(df['brand'] == '乔丹') & (df['year'] == max_year)]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        jordan_sub3 = jordan_latest[jordan_latest['cohort'] == '破3选手']
        st.metric(f"🏅 乔丹破3排名({max_year})", f"第{int(jordan_sub3['rank'].min())}名" if len(jordan_sub3)>0 else "无数据")
    with col2:
        jordan_all = jordan_latest[jordan_latest['cohort'] == '全局跑者']
        st.metric(f"👥 乔丹全局排名({max_year})", f"第{int(jordan_all['rank'].min())}名" if len(jordan_all)>0 else "无数据")
    with col3:
        domestic_latest = df[(df['year'] == max_year) & (df['brand_type'] == 'domestic')]
        domestic_share = domestic_latest.groupby(['event', 'cohort'])['share'].sum().mean() * 100 if len(domestic_latest)>0 else 0
        st.metric(f"🇨🇳 国产品牌占比({max_year})", f"{domestic_share:.1f}%")
    with col4:
        st.metric("👑 特步夺冠次数", f"{len(df[(df['brand'] == '特步') & (df['rank'] == 1)])} 次")
    
    st.markdown("---")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📈 乔丹品牌排名趋势")
        jordan_df = df[df['brand'] == '乔丹']
        if len(jordan_df) > 0:
            jordan_trend = jordan_df.groupby(['year', 'cohort'])['rank'].mean().reset_index()
            fig = go.Figure()
            for cohort in jordan_trend['cohort'].unique():
                cdata = jordan_trend[jordan_trend['cohort'] == cohort]
                fig.add_trace(go.Scatter(x=cdata['year'], y=cdata['rank'], mode='lines+markers', name=cohort,
                    line=dict(color='#EF4444' if cohort=='破3选手' else '#3B82F6')))
            fig.update_layout(height=350, yaxis=dict(autorange='reversed', title='平均排名'), xaxis=dict(title='年份', dtick=1),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.markdown("### 🌏 国产vs国际占比趋势（破3选手）")
        type_trend = df.groupby(['year', 'cohort', 'brand_type'])['share'].sum().reset_index()
        type_trend = type_trend[type_trend['brand_type'].isin(['domestic', 'international'])]
        type_trend['share_pct'] = type_trend['share'] * 100
        type_trend_sub3 = type_trend[type_trend['cohort'] == '破3选手']
        if len(type_trend_sub3) > 0:
            fig = go.Figure()
            for bt in ['domestic', 'international']:
                tdata = type_trend_sub3[type_trend_sub3['brand_type'] == bt]
                fig.add_trace(go.Scatter(x=tdata['year'], y=tdata['share_pct'], mode='lines', fill='tozeroy',
                    name='国产品牌' if bt=='domestic' else '国际品牌', line=dict(color='#3B82F6' if bt=='domestic' else '#10B981')))
            fig.update_layout(height=350, yaxis=dict(title='市场份额 (%)'), xaxis=dict(title='年份', dtick=1),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 💡 关键洞察")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div class="warning-box"><strong>⚠️ 乔丹品牌警示</strong><br>乔丹在破3选手中排名呈下滑趋势，高端市场竞争力减弱。</div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="success-box"><strong>✅ 国产品牌崛起</strong><br>国产品牌从追赶者成为主导者，市场份额持续提升。</div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="insight-box"><strong>📊 特步一枝独秀</strong><br>特步稳居第一，破3选手份额持续领先。</div>', unsafe_allow_html=True)

elif page == "👟 乔丹专题":
    st.markdown("## 👟 乔丹品牌深度分析")
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1: event_filter = st.selectbox("选择赛事", ["全部"] + sorted(df['event'].unique().tolist()), key="j_event")
    with c2: cohort_filter = st.selectbox("选择人群", ["全部", "破3选手", "全局跑者"], key="j_cohort")
    
    jordan_df = df[df['brand'] == '乔丹'].copy()
    if event_filter != "全部": jordan_df = jordan_df[jordan_df['event'] == event_filter]
    if cohort_filter != "全部": jordan_df = jordan_df[jordan_df['cohort'] == cohort_filter]
    
    if len(jordan_df) == 0:
        st.warning("所选条件下暂无数据")
    else:
        st.markdown("### 📊 核心指标")
        c1, c2, c3, c4 = st.columns(4)
        best = jordan_df.loc[jordan_df['rank'].idxmin()]
        worst = jordan_df.loc[jordan_df['rank'].idxmax()]
        with c1: st.metric("🏆 最佳排名", f"第{int(best['rank'])}名", f"{best['event']} {int(best['year'])}")
        with c2: st.metric("📉 最差排名", f"第{int(worst['rank'])}名", f"{worst['event']} {int(worst['year'])}")
        with c3: st.metric("📈 平均排名", f"第{jordan_df['rank'].mean():.1f}名")
        with c4: st.metric("📊 平均份额", f"{jordan_df['share_pct'].mean():.1f}%")
        
        st.markdown("---")
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### 📈 排名变化趋势")
            if cohort_filter == "全部":
                trend = jordan_df.groupby(['year', 'cohort'])['rank'].mean().reset_index()
                fig = go.Figure()
                for c in trend['cohort'].unique():
                    cd = trend[trend['cohort'] == c]
                    fig.add_trace(go.Scatter(x=cd['year'], y=cd['rank'], mode='lines+markers', name=c, line=dict(color='#EF4444' if c=='破3选手' else '#3B82F6')))
            else:
                trend = jordan_df.groupby(['year', 'event'])['rank'].mean().reset_index()
                fig = go.Figure()
                for e in trend['event'].unique():
                    ed = trend[trend['event'] == e]
                    fig.add_trace(go.Scatter(x=ed['year'], y=ed['rank'], mode='lines+markers', name=e))
            fig.update_layout(height=400, yaxis=dict(autorange='reversed', title='排名'), xaxis=dict(title='年份', dtick=1))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_r:
            st.markdown("### 📊 市场份额变化")
            if cohort_filter == "全部":
                share = jordan_df.groupby(['year', 'cohort'])['share_pct'].mean().reset_index()
                fig = go.Figure()
                for c in share['cohort'].unique():
                    cd = share[share['cohort'] == c]
                    fig.add_trace(go.Bar(x=cd['year'], y=cd['share_pct'], name=c, marker_color='#EF4444' if c=='破3选手' else '#3B82F6'))
            else:
                share = jordan_df.groupby(['year', 'event'])['share_pct'].mean().reset_index()
                fig = go.Figure()
                for e in share['event'].unique():
                    ed = share[share['event'] == e]
                    fig.add_trace(go.Bar(x=ed['year'], y=ed['share_pct'], name=e))
            fig.update_layout(height=400, barmode='group', yaxis=dict(title='份额 (%)'), xaxis=dict(title='年份', dtick=1))
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🗺️ 各赛事排名热力图")
        heatmap = jordan_df.pivot_table(values='rank', index='event', columns='year', aggfunc='mean')
        if len(heatmap) > 0:
            fig = px.imshow(heatmap, labels=dict(x="年份", y="赛事", color="排名"), color_continuous_scale='RdYlGn_r', aspect="auto")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🤖 智能分析报告")
        for item in generate_brand_analysis(df[df['brand'] == '乔丹']):
            box = "success-box" if item['rank_change'] > 0 else ("warning-box" if item['rank_change'] < 0 else "insight-box")
            trend_word = "上升" if item['rank_change'] > 0 else ("下降" if item['rank_change'] < 0 else "持平")
            share_word = "增长" if item['share_change'] > 0 else "下降"
            st.markdown(f'<div class="{box}"><strong>{item["cohort"]}</strong><br>• 排名：第{item["first_rank"]}名({item["first_year"]})→第{item["last_rank"]}名({item["last_year"]})，{trend_word}{abs(item["rank_change"])}名<br>• 份额：{item["first_share"]:.1f}%→{item["last_share"]:.1f}%，{share_word}{abs(item["share_change"]):.1f}%<br>• 最佳：{item["best_event"]} {item["best_year"]}年 第{item["best_rank"]}名<br>• 最差：{item["worst_event"]} {item["worst_year"]}年 第{item["worst_rank"]}名</div>', unsafe_allow_html=True)

elif page == "🌏 国产vs国际":
    st.markdown("## 🌏 国产品牌 vs 国际品牌")
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1: cohort_filter = st.selectbox("选择人群", ["破3选手", "全局跑者", "全部"], key="t_cohort")
    with c2: event_filter = st.selectbox("选择赛事", ["全部"] + sorted(df['event'].unique().tolist()), key="t_event")
    
    filtered_df = df.copy()
    if cohort_filter != "全部": filtered_df = filtered_df[filtered_df['cohort'] == cohort_filter]
    if event_filter != "全部": filtered_df = filtered_df[filtered_df['event'] == event_filter]
    
    type_sum = filtered_df.groupby(['year', 'brand_type'])['share'].sum().reset_index()
    type_sum = type_sum[type_sum['brand_type'].isin(['domestic', 'international'])]
    type_sum['share_pct'] = type_sum['share'] * 100
    
    if len(type_sum) > 0:
        min_yr, max_yr = type_sum['year'].min(), type_sum['year'].max()
        dom_first = type_sum[(type_sum['year']==min_yr) & (type_sum['brand_type']=='domestic')]['share_pct'].values
        dom_last = type_sum[(type_sum['year']==max_yr) & (type_sum['brand_type']=='domestic')]['share_pct'].values
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric(f"🇨🇳 国产占比({min_yr})", f"{dom_first[0]:.1f}%" if len(dom_first)>0 else "N/A")
        with c2: st.metric(f"🇨🇳 国产占比({max_yr})", f"{dom_last[0]:.1f}%" if len(dom_last)>0 else "N/A")
        with c3:
            if len(dom_first)>0 and len(dom_last)>0:
                st.metric("📈 国产增长", f"{dom_last[0]-dom_first[0]:+.1f}%")
        with c4:
            top10_dom = filtered_df[(filtered_df['rank']<=10) & (filtered_df['brand_type']=='domestic')]
            if len(top10_dom)>0: st.metric("🏅 TOP10国产数(均)", f"{top10_dom.groupby('year').size().mean():.1f}个")
        
        st.markdown("---")
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### 📊 市场份额趋势")
            fig = go.Figure()
            for bt in ['domestic', 'international']:
                td = type_sum[type_sum['brand_type'] == bt]
                fig.add_trace(go.Scatter(x=td['year'], y=td['share_pct'], mode='lines', fill='tozeroy',
                    name='国产' if bt=='domestic' else '国际', line=dict(color='#EF4444' if bt=='domestic' else '#3B82F6')))
            fig.update_layout(height=400, yaxis=dict(title='份额 (%)'), xaxis=dict(title='年份', dtick=1))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_r:
            st.markdown("### 📈 TOP10品牌数量")
            top10 = filtered_df[filtered_df['rank']<=10].groupby(['year', 'brand_type']).size().reset_index(name='count')
            top10 = top10[top10['brand_type'].isin(['domestic', 'international'])]
            if len(top10) > 0:
                fig = go.Figure()
                for bt in ['domestic', 'international']:
                    td = top10[top10['brand_type'] == bt]
                    fig.add_trace(go.Bar(x=td['year'], y=td['count'], name='国产' if bt=='domestic' else '国际',
                        marker_color='#EF4444' if bt=='domestic' else '#3B82F6'))
                fig.update_layout(height=400, barmode='group', yaxis=dict(title='数量'), xaxis=dict(title='年份', dtick=1))
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🏃 代表品牌排名变化")
        cl, cr = st.columns(2)
        with cl:
            st.markdown("#### 国产品牌TOP5")
            dom_brands = ['特步', '李宁', '安踏', '鸿星尔克', '乔丹']
            dom_trend = filtered_df[filtered_df['brand'].isin(dom_brands)].groupby(['year', 'brand'])['rank'].mean().reset_index()
            if len(dom_trend) > 0:
                fig = go.Figure()
                for b in dom_brands:
                    bd = dom_trend[dom_trend['brand'] == b]
                    if len(bd) > 0: fig.add_trace(go.Scatter(x=bd['year'], y=bd['rank'], mode='lines+markers', name=b))
                fig.update_layout(height=350, yaxis=dict(autorange='reversed', title='排名'), xaxis=dict(title='年份', dtick=1))
                st.plotly_chart(fig, use_container_width=True)
        with cr:
            st.markdown("#### 国际品牌TOP5")
            int_brands = ['Nike', 'Adidas', 'ASICS', 'Saucony', 'HOKA']
            int_trend = filtered_df[filtered_df['brand'].isin(int_brands)].groupby(['year', 'brand'])['rank'].mean().reset_index()
            if len(int_trend) > 0:
                fig = go.Figure()
                for b in int_brands:
                    bd = int_trend[int_trend['brand'] == b]
                    if len(bd) > 0: fig.add_trace(go.Scatter(x=bd['year'], y=bd['rank'], mode='lines+markers', name=b))
                fig.update_layout(height=350, yaxis=dict(autorange='reversed', title='排名'), xaxis=dict(title='年份', dtick=1))
                st.plotly_chart(fig, use_container_width=True)

elif page == "⚖️ 品牌对比":
    st.markdown("## ⚖️ 自由品牌对比分析")
    st.markdown("---")
    all_brands = sorted(df['brand'].unique().tolist())
    selected = st.multiselect("选择品牌（最多5个）", all_brands, default=['乔丹', '特步', 'Nike'], max_selections=5)
    c1, c2 = st.columns(2)
    with c1: cohort_f = st.selectbox("人群", ["全部", "破3选手", "全局跑者"], key="cmp_c")
    with c2: event_f = st.selectbox("赛事", ["全部"] + sorted(df['event'].unique().tolist()), key="cmp_e")
    
    if len(selected) < 2:
        st.warning("请至少选择2个品牌")
    else:
        fdf = df[df['brand'].isin(selected)].copy()
        if cohort_f != "全部": fdf = fdf[fdf['cohort'] == cohort_f]
        if event_f != "全部": fdf = fdf[fdf['event'] == event_f]
        
        if len(fdf) == 0:
            st.warning("暂无数据")
        else:
            st.markdown("---")
            cl, cr = st.columns(2)
            with cl:
                st.markdown("### 📈 排名对比")
                trend = fdf.groupby(['year', 'brand'])['rank'].mean().reset_index()
                fig = go.Figure()
                for b in selected:
                    bd = trend[trend['brand'] == b]
                    if len(bd) > 0: fig.add_trace(go.Scatter(x=bd['year'], y=bd['rank'], mode='lines+markers', name=b))
                fig.update_layout(height=400, yaxis=dict(autorange='reversed', title='排名'), xaxis=dict(title='年份', dtick=1))
                st.plotly_chart(fig, use_container_width=True)
            with cr:
                st.markdown("### 📊 份额对比")
                share = fdf.groupby(['year', 'brand'])['share_pct'].mean().reset_index()
                fig = go.Figure()
                for b in selected:
                    bd = share[share['brand'] == b]
                    if len(bd) > 0: fig.add_trace(go.Bar(x=bd['year'], y=bd['share_pct'], name=b))
                fig.update_layout(height=400, barmode='group', yaxis=dict(title='份额 (%)'), xaxis=dict(title='年份', dtick=1))
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 🎯 综合实力雷达图")
            radar_data = []
            for b in selected:
                bd = fdf[fdf['brand'] == b]
                if len(bd) == 0: continue
                radar_data.append({'brand': b, '排名': max(0, 100 - bd['rank'].mean()*5), '份额': min(100, bd['share_pct'].mean()*5),
                    '最佳': max(0, 100 - bd['rank'].min()*8), '稳定': max(0, 100 - bd['rank'].std()*5),
                    '覆盖': bd['event'].nunique() / df['event'].nunique() * 100})
            if radar_data:
                cats = ['排名', '份额', '最佳', '稳定', '覆盖']
                fig = go.Figure()
                for r in radar_data:
                    fig.add_trace(go.Scatterpolar(r=[r[c] for c in cats], theta=cats, fill='toself', name=r['brand']))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=450)
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 🤖 智能分析报告")
            report = generate_comparison_report(selected, df, cohort_f, event_f)
            if report:
                rdf = pd.DataFrame(report)
                rdf['趋势'] = rdf['rank_trend'].apply(lambda x: "📈上升" if x>0 else ("📉下降" if x<0 else "➡️持平"))
                rdf['份额变化'] = rdf['share_trend'].apply(lambda x: f"+{x:.1f}%" if x>0 else f"{x:.1f}%")
                disp = rdf[['brand', 'brand_type', 'avg_rank', 'avg_share', 'best_rank', '趋势', '份额变化']].copy()
                disp.columns = ['品牌', '类型', '平均排名', '平均份额(%)', '最佳排名', '趋势', '份额变化']
                disp['平均排名'] = disp['平均排名'].round(1)
                disp['平均份额(%)'] = disp['平均份额(%)'].round(1)
                st.dataframe(disp, use_container_width=True, hide_index=True)
                
                best, worst = report[0], report[-1]
                st.markdown(f'<div class="insight-box"><strong>📊 对比结论</strong><br>• <strong>{best["brand"]}</strong>表现最佳，平均第{best["avg_rank"]:.1f}名，份额{best["avg_share"]:.1f}%<br>• <strong>{worst["brand"]}</strong>相对较弱，平均第{worst["avg_rank"]:.1f}名</div>', unsafe_allow_html=True)

elif page == "📊 数据浏览":
    st.markdown("## 📊 完整数据浏览")
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1: year_f = st.multiselect("年份", sorted(df['year'].unique()), default=sorted(df['year'].unique()))
    with c2: event_f = st.multiselect("赛事", df['event'].unique(), default=list(df['event'].unique()))
    with c3: cohort_f = st.multiselect("人群", df['cohort'].unique(), default=list(df['cohort'].unique()))
    with c4: type_f = st.multiselect("类型", ['domestic', 'international', 'other'], default=['domestic', 'international'])
    
    fdf = df[(df['year'].isin(year_f)) & (df['event'].isin(event_f)) & (df['cohort'].isin(cohort_f)) & (df['brand_type'].isin(type_f))].copy()
    search = st.text_input("🔍 搜索品牌")
    if search: fdf = fdf[fdf['brand'].str.contains(search, case=False, na=False)]
    
    st.markdown(f"**共 {len(fdf)} 条记录**")
    disp = fdf[['year', 'event', 'cohort', 'rank', 'brand', 'brand_type', 'share_pct']].copy()
    disp.columns = ['年份', '赛事', '人群', '排名', '品牌', '类型', '份额(%)']
    disp['类型'] = disp['类型'].map({'domestic': '国产', 'international': '国际', 'other': '其他'})
    disp['份额(%)'] = disp['份额(%)'].round(1)
    st.dataframe(disp.sort_values(['年份', '赛事', '人群', '排名'], ascending=[False, True, True, True]), use_container_width=True, height=500, hide_index=True)
    
    csv = disp.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 下载CSV", csv, "marathon_shoe_data.csv", "text/csv")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#64748B;padding:1rem;">📊 马拉松跑鞋品牌分析平台 | 数据来源：悦跑圈等平台</div>', unsafe_allow_html=True)
