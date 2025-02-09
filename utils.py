# scatter graph
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from typing import Union
import numpy as np
import pandas as pd


# scatter plot
def create_scatter_plot(x:Union[list,np.array,pd.Series],
                        y:Union[list,np.array,pd.Series],
                        category:Union[list,np.array,pd.Series],
                        category_color:dict = None,
                        x_axis_title:str = 'X Axis',
                        y_axis_title:str = 'Y Axis',
                        output_html:bool = False,
                        html_filename:str = "scatter_plot.html"
                        ):
    """
    散布図を作成する関数

    Parameters:
    - x: list, np.array, or pd.Series, X軸のデータ
    - y: list, np.array, or pd.Series, Y軸のデータ
    - category: list, np.array, or pd.Series, カテゴリのデータ
    - x_axis_title: str, X軸のタイトル（デフォルト: 'X Axis'）
    - y_axis_title: str, Y軸のタイトル（デフォルト: 'Y Axis'）
    - output_html: bool, HTML形式で出力する場合はTrue（デフォルト: False）
    - html_filename: str, HTMLファイル名（デフォルト: 'scatter_plot.html'）

    Returns:
    - fig: plotly.graph_objects.Figure, 作成した図
    """

    # 散布図の作成
    fig = go.Figure()

    # 各カテゴリのデータポイントを追加
    unique_categories = pd.Series(category).unique()  # カテゴリのユニークな値を取得

    # if color dict
    if category_color!=None:
        for cat in unique_categories:
            mask = pd.Series(category) == cat  # 指定カテゴリのデータをフィルタリング
            fig.add_trace(go.Scatter(
                x=np.array(x)[mask],
                y=np.array(y)[mask],
                mode='markers',
                name=str(cat),  # 凡例の名前
                marker=dict(size=5, color=category_color[cat]),  # マーカーのサイズ
            ))
    else:
        for cat in unique_categories:
            mask = pd.Series(category) == cat  # 指定カテゴリのデータをフィルタリング
            fig.add_trace(go.Scatter(
                x=np.array(x)[mask],
                y=np.array(y)[mask],
                mode='markers',
                name=str(cat),  # 凡例の名前
                marker=dict(size=5),  # マーカーのサイズ
            ))

    # 軸タイトルの設定
    fig.update_layout(
        title='Scatter Plot',
        xaxis_title=x_axis_title,
        yaxis_title=y_axis_title,
        showlegend=True,
        legend_title="Category",
        margin=dict(l=40, r=40, t=40, b=40),  # マージンの設定
        width = 700,
        height = 500,
        plot_bgcolor="rgba(255, 255, 255, 0.5)"
    )

    # 軸情報の指定
    fig.update_xaxes(range=[min(x) - 1, max(x) + 1],
                     showgrid=True, 
                     gridcolor="Black",
                     gridwidth = 0.1,
                     linecolor = "Black",
                     linewidth = 2,
                     tickcolor="LightGray",
                     title_font={"size": 18, "color": "Black"},
                     tickfont=dict(color='Black'))  # X軸目盛りの色)
    fig.update_yaxes(range=[min(y) - 1, max(y) + 1],
                     showgrid=True, 
                     gridcolor="LightGray",
                     gridwidth = 0.1,
                     linecolor = "Black",
                     linewidth = 2,
                     tickcolor="LightGray",
                     title_font={"size": 18, "color": "Black"},
                     tickfont=dict(color='Black'))  # X軸目盛りの色)

    # HTML形式で出力する場合
    if output_html:
        fig.write_html(html_filename, include_plotlyjs='cdn')  # Plotly.jsをCDNから読み込む

    return fig

# box plot
def create_box_plot(data:Union[list,np.array,pd.Series],
                    category:Union[list,np.array,pd.Series],
                    x_axis_title:str = 'X Axis',
                    y_axis_title:str = 'Y Axis',
                    output_html:bool = False,
                    html_filename:str = "scatter_plot.html"
                    ):
    """
    散布図を作成する関数

    Parameters:
    - data : list, np.array, or pd.Series, Y軸のデータ
    - category: list, np.array, or pd.Series, カテゴリのデータ
    - x_axis_title: str, X軸のタイトル（デフォルト: 'X Axis'）
    - y_axis_title: str, Y軸のタイトル（デフォルト: 'Y Axis'）
    - output_html: bool, HTML形式で出力する場合はTrue（デフォルト: False）
    - html_filename: str, HTMLファイル名（デフォルト: 'scatter_plot.html'）

    Returns:
    - fig: plotly.graph_objects.Figure, 作成した図
    """

    # 散布図の作成
    fig = go.Figure()

    # 各カテゴリのデータポイントを追加
    unique_categories = pd.Series(category).unique()  # カテゴリのユニークな値を取得

    # each category
    if category is not None:
        categories = pd.Series(category).unique()  # カテゴリのユニークな値を取得
        for cat in categories:
            mask = pd.Series(category) == cat
            cat_data = np.array(data)[mask]
            fig.add_trace(go.Box(
                y=cat_data,             # 指定カテゴリのデータのみ使用
                name=str(cat),          # 凡例に表示されるカテゴリ名
                boxmean=True            # 平均値を表示
            ))
            # データ数を注釈として追加
            fig.add_annotation(
                x=str(cat),
                y=max(cat_data) * 1.03,  # 注釈位置を調整
                text=f"N={len(cat_data)}",
                showarrow=False,
                font=dict(size=12, color="black")
            )
    else:
        # カテゴリがない場合は全データで1つの箱ひげ図を作成
        fig.add_trace(go.Box(
            y=data,
            boxmean=True  # 平均値を表示
        ))

        # データ数を注釈として追加
        fig.add_annotation(
            x = 0,
            y= max(data) * 1.05,
            text=f"N={len(data)}",
            showarrow=False,
            font=dict(size=12, color="black")
        )

    # 軸タイトルの設定
    fig.update_layout(
        title='Box Plot',
        xaxis_title=x_axis_title,
        yaxis_title=y_axis_title,
        showlegend=True,
        legend_title="Category",
        margin=dict(l=40, r=40, t=40, b=40),  # マージンの設定
        width = 1200, # size
        height = 500, # size
        plot_bgcolor="rgba(255, 255, 255, 0.5)"
    )

    # 軸情報の指定
    fig.update_xaxes(tickangle=90,
                     showgrid=False,
                     gridcolor="Black",
                     gridwidth = 0.1,
                     linecolor = "Black",
                     linewidth = 2,
                     tickcolor="LightGray",
                     title_font={"size": 18, "color": "Black"},
                     tickfont=dict(color='Black'))  # X軸目盛りの色)
    
    fig.update_yaxes(range=[min(data) - min(data)*0.1, max(data) + max(data)*0.1],
                     showgrid=True,
                     gridcolor="LightGray",
                     gridwidth = 0.1,
                     linecolor = "Black",
                     linewidth = 2,
                     tickcolor="LightGray",
                     title_font={"size": 18, "color": "Black"},
                     tickfont=dict(color='Black'))  # X軸目盛りの色)

    # HTML形式で出力する場合
    if output_html:
        fig.write_html(html_filename, include_plotlyjs='cdn')  # Plotly.jsをCDNから読み込む

    return fig

# box plot gray
def create_box_plot_with_count(data: Union[list, np.ndarray, pd.Series], 
                               category: Union[list, np.ndarray, pd.Series] = None, 
                               title: str = "Box Plot with Counts"):
    """
    データ数を注釈として表示する箱ひげ図を作成する関数

    Parameters:
    - data: リスト、NumPy配列、またはPandasシリーズのいずれかで指定可能なデータ
    - category: リスト、NumPy配列、またはPandasシリーズのいずれかで指定可能なカテゴリ情報（デフォルトはNone）
    - title: str, グラフのタイトル

    Returns:
    - fig: plotly.graph_objects.Figure, 作成した箱ひげ図
    """
    
    fig = go.Figure()

    # カテゴリごとにデータを分割して追加し、データ数を注釈として表示
    if category is not None:
        categories = pd.Series(category).unique()  # カテゴリのユニークな値を取得
        for cat in categories:
            mask = pd.Series(category) == cat
            cat_data = np.array(data)[mask]
            fig.add_trace(go.Box(
                y=cat_data,             # 指定カテゴリのデータのみ使用
                name=str(cat),          # 凡例に表示されるカテゴリ名
                boxmean=True,            # 平均値を表示
                marker_color="red",             # 中を白で塗りつぶし
                line_color="black"                # 枠線を黒で表示
            ))
            # データ数を注釈として追加
            fig.add_annotation(
                x=str(cat),
                y=max(cat_data) * 1.03,  # 注釈位置を調整
                text=f"N={len(cat_data)}",
                showarrow=False,
                font=dict(size=12, color="black")
            )
    else:
        # カテゴリがない場合は全データで1つの箱ひげ図を作成
        fig.add_trace(go.Box(
            y=data,
            boxmean=True,  # 平均値を表示
            marker_color="blue",             # 中を白で塗りつぶし
            line_color="black"                # 枠線を黒で表示
        ))

        # データ数を注釈として追加
        fig.add_annotation(
            x = 0,
            y= max(data) * 1.03,
            text=f"N={len(data)}",
            showarrow=False,
            font=dict(size=12, color="black")
        )

    # グラフのレイアウト設定
    fig.update_layout(
        title=title,
        xaxis_title="Category" if category is not None else "",
        yaxis_title="Values",
        showlegend=True,
        legend_title="Category",
        margin=dict(l=40, r=40, t=40, b=40),  # マージンの設定
        width = 700, # size
        height = 500, # size
        plot_bgcolor="rgba(255, 255, 255, 0.5)"
    )

    fig.update_xaxes(tickangle=90,
                     showgrid=False,
                     gridcolor="Black",
                     gridwidth = 0.1,
                     linecolor = "Black",
                     linewidth = 2,
                     tickcolor="LightGray",
                     title_font={"size": 18, "color": "Black"},
                     tickfont=dict(color='Black'))  # X軸目盛りの色)
    
    fig.update_yaxes(range=[min(data) - min(data)*0.1, max(data) + max(data)*0.1],
                     showgrid=True,
                     gridcolor="LightGray",
                     gridwidth = 0.1,
                     linecolor = "Black",
                     linewidth = 2,
                     tickcolor="LightGray",
                     title_font={"size": 18, "color": "Black"},
                     tickfont=dict(color='Black'))  # X軸目盛りの色)

    return fig

# plot
def create_trend_plot(dates: Union[pd.Series, list[pd.Timestamp]], 
                      values: Union[pd.Series, list[float]], 
                      title: str = "Trend Plot", 
                      x_axis_title: str = "Date", 
                      y_axis_title: str = "Value"):
    """
    日付をX軸としたトレンドグラフを作成する関数

    Parameters:
    - dates: pd.Seriesまたはリストで指定するdatetime型の日付データ
    - values: pd.Seriesまたはリストで指定するY軸の数値データ
    - title: str, グラフのタイトル
    - x_axis_title: str, X軸のタイトル
    - y_axis_title: str, Y軸のタイトル

    Returns:
    - fig: plotly.graph_objects.Figure, 作成したトレンドグラフ
    """

    fig = go.Figure()

    # トレンドラインを追加
    fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name="Trend",
        line=dict(color="blue"),       # 線の色を設定
        marker=dict(size=6, color="red")  # マーカーのサイズと色を設定
    ))

    # レイアウトの設定
    fig.update_layout(
        title=title,
        xaxis_title=x_axis_title,
        yaxis_title=y_axis_title,
        xaxis=dict(type="date"),       # X軸を日付型に設定
        showlegend=True,
        paper_bgcolor="rgba(255, 255, 255, 1)",
        plot_bgcolor="rgba(230, 230, 250, 0.3)",
        margin = dict(l=5, r=5, t=45, b=5),
        title_x = 0.05, title_y=0.96
    )

    return fig