import streamlit as st
import requests
from bs4 import BeautifulSoup
import jieba
from collections import Counter
import plotly.express as px
import matplotlib.pyplot as plt
from pyecharts.charts import WordCloud, Bar, Line, Scatter, Radar, Funnel
from pyecharts import options as opts
from streamlit.components.v1 import html
import re  # 导入正则表达式模块

import matplotlib

# 设置中文字体，解决乱码问题
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']  # 或者使用 'SimHei'
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# Streamlit界面设置
st.title('文章词频分析与词云展示')

# 用户输入文章URL
url = st.text_input('请输入文章URL')


# 抓取文本内容
def fetch_text_content(url):
    response = requests.get(url)
    response.encoding = 'utf-8'  # 设置编码为utf-8，避免乱码
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text()
    return text


# 过滤掉标点符号、空格和换行符
def remove_punctuation_and_spaces(text):
    # 去除所有标点符号
    text_without_punctuation = re.sub(r'[^\w\s]', '', text)  # 保留字母、数字和空格

    # 去掉换行符，合并多个空格为一个空格
    text_cleaned = re.sub(r'\s+', ' ', text_without_punctuation).strip()  # \s+ 处理多个空格为一个
    text_cleaned = re.sub(r'\n+', ' ', text_cleaned)  # 去除换行符

    # 移除合并后的空格
    text_cleaned = text_cleaned.replace(' ', '')  # 删除所有空格

    return text_cleaned


# 分词并统计词频
def word_frequency(text):
    text = remove_punctuation_and_spaces(text)  # 先去除标点符号、空格和换行符
    words = jieba.cut(text)
    freq = Counter(words)
    return freq  # 返回Counter对象


# 绘制词云
def draw_wordcloud(freq):
    if not freq:  # 检查freq是否为空
        return None
    wordcloud = WordCloud(init_opts=opts.InitOpts(width="1000px", height="600px"))
    wordcloud.add("", list(freq.items()), word_size_range=[20, 100])
    return wordcloud


# 绘制图形
def draw_chart(chart_type, freq_dict):
    if not freq_dict:
        return None  # 如果freq_dict为空，不绘制图表

    if chart_type == '条形图':
        bar = Bar()
        bar.add_xaxis(list(freq_dict.keys()))
        bar.add_yaxis("词频", list(freq_dict.values()))
        bar.set_global_opts(title_opts=opts.TitleOpts(title=f"{chart_type}"))
        return bar

    elif chart_type == '饼图':
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(list(freq_dict.values()), labels=list(freq_dict.keys()), autopct='%1.1f%%')
        ax.set_title(chart_type)
        return fig

    elif chart_type == '折线图':
        line = Line()
        line.add_xaxis(list(freq_dict.keys()))
        line.add_yaxis("词频", list(freq_dict.values()))
        line.set_global_opts(title_opts=opts.TitleOpts(title=f"{chart_type}"))
        return line

    elif chart_type == '散点图':
        scatter = Scatter()
        scatter.add_xaxis(list(freq_dict.keys()))
        scatter.add_yaxis("词频", list(freq_dict.values()))
        scatter.set_global_opts(title_opts=opts.TitleOpts(title=f"{chart_type}"))
        return scatter

    elif chart_type == '雷达图':
        radar = Radar()
        radar.add_schema(
            schema=[opts.RadarIndicatorItem(name=list(freq_dict.keys())[i], max_=list(freq_dict.values())[i]) for i in
                    range(len(list(freq_dict.keys())))])
        radar.add("", [list(freq_dict.values())])
        radar.set_global_opts(title_opts=opts.TitleOpts(title=f"{chart_type}"))
        return radar

    elif chart_type == '漏斗图':
        top_words = sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)[:10]  # 排序并取前10
        funnel = Funnel()
        funnel.add(
            "词频漏斗",
            [opts.FunnelItem(name=word, value=freq) for word, freq in top_words]
        )
        funnel.set_global_opts(title_opts=opts.TitleOpts(title=f"{chart_type}"))
        return funnel

    elif chart_type == '热力图':
        fig = px.imshow([[freq_dict.get(i, 0) for i in range(len(freq_dict) + 1)] for j in range(len(freq_dict) + 1)],
                        title=f"{chart_type}")
        return fig

    else:
        return None


# Streamlit侧边栏筛选图型
def sidebar_chart_selection():
    chart_type = st.sidebar.selectbox(
        '选择图型',
        ('条形图', '饼图', '折线图', '散点图', '雷达图', '漏斗图', '热力图')
    )
    return chart_type


# 主函数
def main():
    if url:
        text_content = fetch_text_content(url)
        freq = word_frequency(text_content)

        # 展示词云
        st.subheader('词云展示')
        wordcloud = draw_wordcloud(freq)
        if wordcloud:
            wordcloud_html = wordcloud.render_embed()  # 这里直接生成HTML
            html(wordcloud_html, height=600, width=1000)

        # 展示词频排名前20的词汇
        st.subheader('词频排名前20的词汇')
        top_20_words = freq.most_common(20)  # 使用Counter的most_common方法
        for word, freq in top_20_words:
            st.write(f'{word}: {freq}')

        # 侧边栏图型筛选
        chart_type = sidebar_chart_selection()
        st.sidebar.write(f'您选择的图型是：{chart_type}')

        # 绘制并展示图形
        chart_fig = draw_chart(chart_type, dict(top_20_words))  # 使用词频的前20个词数据
        if chart_fig:
            st.subheader(f'{chart_type}展示')
            if chart_type == '饼图':
                st.pyplot(chart_fig)  # 显示matplotlib饼图
            elif chart_type == '热力图':
                st.plotly_chart(chart_fig)  # 显示plotly热力图
            else:
                # pyecharts图表需要调用render_embed方法来展示
                if isinstance(chart_fig, (Bar, Line, Scatter, Radar, Funnel)):
                    chart_html = chart_fig.render_embed()
                    html(chart_html, height=600, width=1000)


if __name__ == '__main__':
    main()
