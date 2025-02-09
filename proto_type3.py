import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
from flask import Flask, session, redirect
import bcrypt
import plotly.express as px
import pandas as pd
import os
import Dataloader as D
import utils as u

# -------------------------------------
# Flask
server = Flask(__name__)
server.secret_key = os.urandom(24)
server.config['SESSION_PERMANENT'] = False
server.config['SESSION_TYPE'] = 'filesystem'

# -------------------------------------
# user data
users = {
    "admin": bcrypt.hashpw("pass123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
}

# -------------------------------------
# Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True, server=server)
app.title = "Finance Dashboard, Proto"

app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    dcc.Store(id='login-status', storage_type='session', data=False),
    html.Div(id='page-content')
])

# -------------------------------------
# 1. Login
def login_layout():
    return html.Div([
        html.H2("Enter user name and password"),
        dcc.Input(id="username", type="text", placeholder="user name", style={"fontSize":"24px"}), html.Br(),
        dcc.Input(id="password", type="password", placeholder="password", style={"fontSize":"24px"}), html.Br(),
        html.Button("ログイン", id="login-button", n_clicks=0),
        html.Div(id="login-message", style={"fontSize":"24px"}),
        dcc.Location(id="redirect", refresh=True),
        html.Br(),
        html.P("認証が必要です。")
    ])

# Dash login
@app.callback(
    [Output("login-message", "children"),
     Output("login-status", "data"),
     Output("redirect", "pathname")],
    Input("login-button", "n_clicks"),
    State("username", "value"),
    State("password", "value"),
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    if username in users and bcrypt.checkpw(password.encode('utf-8'), users[username].encode('utf-8')):
        session['user'] = username
        return "Success", True, "/"
    return "Failed login", False, "/login"

# 2. logout
@app.callback(
    Output("url", "pathname"),
    Input("logout-button", "n_clicks"),
    prevent_initial_call=True
)
def logout(n_clicks):
    session.pop('user', None)
    return "/login"

# -------------------------------------
# Home page
# -------------------------------------
# Dataset
Data = D.DataExe()
exedata = Data.exe_tble

def home_layout():
    return html.Div(
        children= [
            html.H1("Finance dashboard page, proto"),
            #html.Button("logout", id="logout-button", n_clicks=0),
            html.Div(
                style = {"display":"flex", "height":"100vh"},
                children = [
                    html.Div(
                        style = {"width":"30%", "padding":"25px"},
                        children = [
                            html.H2("各リンク"),
                            html.Li(html.A("日経東証1部株価",
                                           style={"fontSize":"24px", "lineHeight": "48px","marginBottom": "20px"})),
                            html.A("Link", style={"fontSize":"24px","marginBottom": "20px","marginLeft": "10px"},
                                           href="/kabu/A"),
                            html.Li(html.A("仮想通貨",
                                           style={"fontSize":"24px", "lineHeight": "48px","marginBottom": "20px"})),
                            html.A("Link", style={"fontSize":"24px","marginBottom": "20px","marginLeft": "10px"},
                                           href="/cript/A"),
                        ]
                    ),
                    html.Div(
                        style={"width": "50%", "padding": "20px", "overflowY": "auto", "overflowX": "hidden"},
                        children=[
                            html.H2("更新日"),
                            dash_table.DataTable(
                                id="exetble",
                                columns = [{"name":col, "id":col} for col in exedata.columns],
                                data = exedata.to_dict("records"),
                                fixed_rows = {"headers":True},
                                style_table = {"width":"100%"},
                                style_cell = {"backgroundColor":"#F8F8FF", "color": "#000000","border": "1px solid #444","textAlign":"left", "paddingLeft":"10px","fontSize":"20px"},
                                style_header = {"backgroundColor": "#191970","color": "#ffffff", "border": "1px solid #666","fontweight":"bold","fontSize":"20px"},
                                style_data_conditional=[
                                    {"if": {"row_index": "odd"}, "backgroundColor": "#E0FFF"},
                                    {"if": {"row_index": "even"}, "backgroundColor": "#FFFFF"}
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

# -------------------------------------
# Table page
# -------------------------------------
# parmaeter
ROOT = r"C:\Users\yktkk\Desktop\DS_practice\programing\WebPage"
nikkei_list_file_path = os.path.join(ROOT, "datadash/dataset/nikkei.csv")
translation_dict_path = os.path.join(ROOT, "datadash/dataset/financials_translation_dict.json")
Dataset = D.Data(nikkei_list_file_path=nikkei_list_file_path,
                translation_dict_path=translation_dict_path)
def table_layout1():
    # base data
    df = Dataset.nikkei
    return html.Div(
                children = [
                    html.H2("Japan finance dashboard"),
                    html.A("ホームに戻る", href="/"),
                    html.Div(
                        style = {"display":"flex", "height":"100vh"},
                        children=[
                            html.Div(
                                style = {"width":"40%", "padding":"25px", "overflowY": "auto", "overflowX": "hidden"},
                                children = [html.H3("Finance table"),
                                            dash_table.DataTable(
                                                id="basetable",
                                                columns = [{"name":col, "id":col} for col in df.columns],
                                                data = df.to_dict("records"),
                                                fixed_rows = {"headers":True},
                                                style_table = {"width":"100%"},
                                                style_cell = {"backgroundColor":"#F8F8FF", "color": "#000000","border": "1px solid #444","textAlign":"left", "paddingLeft":"10px","fontSize":"12px"},
                                                style_header = {"backgroundColor": "#191970","color": "#ffffff", "border": "1px solid #666","fontweight":"bold","fontSize":"12px"},
                                                style_data_conditional=[
                                                    {"if": {"row_index": "odd"}, "backgroundColor": "#F0FFFF"},
                                                    {"if": {"row_index": "even"}, "backgroundColor": "#FFFFFF"}
                                                ]
                                            )
                                ]
                            ),
                            html.Div(
                                style={"width": "60%", "padding": "20px"},
                                children=[
                                    html.H3("Plots"),
                                    html.Div(
                                        style = {"display":"flex", "alignItems":"center", "gap":"10px"},
                                        children = [
                                            dcc.Dropdown(
                                            id = "name",
                                            options = [{"label":item, "value":item} for item in df["銘柄名"].values],
                                            value = df["銘柄名"].values[0],
                                            clearable=False,
                                            style={"width":"60%","backgroundColor": "#FFFFFF"}
                                            ),
                                            html.Label("day_period", style={"fontSize":"16px", "marginLeft":"0px"}),
                                            dcc.Input(
                                                id = "period",
                                                type="number",
                                                value = 28,
                                                min = 7, max=168,
                                                step=1,
                                                style={"width":"20%", "marginLeft":"10px"}
                                            )
                                        ]
                                    ),
                                    dcc.Graph(id="trendgraph")
                                ]
                            )
                        ]
                    ),
                ]
            )

# graph,
@app.callback(
    Output("trendgraph", "figure"),
    Input("name", "value"),
    Input("period", "value")
)
def update_graph(name:str, period:int):
    # set company
    code = str(Dataset.nikkei_items[name]["コード"]).zfill(4)
    print("Selected name / code : {} / {}".format(name, code))
    Dataset.set_company(code=code)
    # get trend
    trend = Dataset.gethistory(period=period).reset_index()
    if trend is None or trend.empty:
        print("Error, Dataset.gethisotry() returned None or empty data")
    # graph
    # fig = px.line(
    #     trend,
    #     x = "Date",
    #     y = "Open",
    #     labels = {"x":"date", "y":"open price"},
    #     title = "history"
    # )
    # fig.update_layout(
    #     margin = dict(l=5, r=5, t=40, b=5),
    #     title_x = 0.05, title_y=0.96
    # )
    # plotly
    fig = u.create_trend_plot(
        dates = trend["Date"].values,
        values = trend["Open"].values,
        title = "Trend plot",
        x_axis_title = "Date",
        y_axis_title = "Price"
    )

    return fig

# -------------------------------------
# page transition
# -------------------------------------
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('login-status', 'data')
)
def display_page(pathname, login_status):
    # not login status
    if not login_status:
        return login_layout()
    # url
    if pathname in ["/", ""]:
        return home_layout()
    elif pathname == "/login":
        return login_layout()
    elif pathname.startswith('/kabu/'):
        category = pathname.split('/')[-1]
        return table_layout1()
    else:
        return html.H2("404: ページが見つかりません")

if __name__ == '__main__':
    app.run_server(debug=True)
