import dash
from dash import html
from dash import dcc
from datetime import datetime as dt
import yfinance as yf
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import dash_bootstrap_components as dbc
import dash_gif_component as gif
# model
from model import prediction
from sklearn.svm import SVR


def get_stock_price_fig(df):
    fig = px.line(df,
                  x="Date",
                  y=["Close", "Open"],
                  title="Closing and Opening Price")
    return fig


def get_more(df):
    df['EWA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    fig = px.scatter(df,
                     x="Date",
                     y="EWA_20",
                     title="Exponential Moving Average (EMA)")
    fig.update_traces(mode='lines+markers')
    return fig


app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Roboto&display=swap"
    ])
app.title = 'VFS'
server = app.server

spinners = html.Div([
    dbc.Spinner(color='primary')
])

# html layout of site
app.layout = html.Div([
    html.Div([
         html.Img(
            id = 'vfs-logo',
            src='assets/VFS-logos(crop).png')
    ]
            , className='navbar'),
    html.Div([html.H1("Welcome to the Stock Dash App!", className="start")]),
    html.Div([
    html.Div(
    [
        html.Div(
            [
                # Navigation
                html.Div([
                    #html.H4("Input stock code: "),
                    html.Div([
                        dcc.Input(
                            id="dropdown_tickers",
                            type="search",
                            placeholder= "Input Stock Code",
                            debounce=False),
                        html.Button("Submit", id='submit'),
                    ],
                             className="form")
                ],
                         className="input-place"),
                html.Div([
                    dcc.DatePickerRange(id='my-date-picker-range',
                                        min_date_allowed=dt(2002, 8, 5),
                                        max_date_allowed=dt.now(),
                                        initial_visible_month=dt.now(),
                                        end_date=dt.now().date()),
                ], className="date"),
                html.Div([
                    dcc.Input(id="n_days",
                              type="text",
                              placeholder="  Number of days"),
                    html.Button(
                        "Forecast", 
                        className="nforecast",
                        id="forecast"),
                    html.Button(
                        "Stock Price", className="stock-btn", id="stock"),
                    html.Button("Indicators",
                                className="indicators-btn",
                                id="indicators")
                ], className="buttons"),
                # here
            ],
            className="nav"),

        # content
        html.Div(
            [
                html.Div(
                    [  # header
                        html.Img(id="logo"),
                        html.P(id="ticker")
                    ],
                    className="header"),
                html.Div(id="description", className="decription_ticker"),
            ],
            className="content"),
    ],
    className="container"),
    html.Div([
            html.Div([], id="graphs-content"),
            html.Div([], id="main-content"),
            html.Div([], id="forecast-content")
            ], className="graphs")
    ]),
])


# callback for company info
@app.callback([
    Output("description", "children"),
    Output("logo", "src"),
    Output("ticker", "children"),
    Output("stock", "n_clicks"),
    Output("indicators", "n_clicks"),
    Output("forecast", "n_clicks")
], [Input("submit", "n_clicks")], [State("dropdown_tickers", "value")])

def update_data(n, val):  # inpur parameter(s)
    if n == None:
        return "Hey there! Please enter a legitimate stock code to get details.", None, None, None, None, None
        # raise PreventUpdate
    else:
        if val == None:
            raise PreventUpdate
        else:
            ticker = yf.Ticker(val)
            inf = ticker.info
            df = pd.DataFrame().from_dict(inf, orient="index").T
            df[['logo_url', 'shortName', 'longBusinessSummary']]
            return df['longBusinessSummary'].values[0], df['logo_url'].values[
                0], df['shortName'].values[0], None, None, None


# callback for stocks graphs
@app.callback([
    Output("graphs-content", "children"),
], [
    Input("stock", "n_clicks"),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
], [State("dropdown_tickers", "value")])

def stock_price(n, start_date, end_date, val):
    if n == None:
        return [""]
        #raise PreventUpdate
    if val == None:
        raise PreventUpdate
    else:
        if start_date != None:
            df = yf.download(val, str(start_date), str(end_date))
        else:
            df = yf.download(val)

    df.reset_index(inplace=True)
    fig = get_stock_price_fig(df)
    return [dcc.Graph(figure=fig, 
    config={
        'scrollZoom': True,
        'doubleClick': 'autosize'
    })]


# callback for indicators
@app.callback([Output("main-content", "children")], [
    Input("indicators", "n_clicks"),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
], [State("dropdown_tickers", "value")])

def indicators(n, start_date, end_date, val):
    if n == None:
        return [""]
    if val == None:
        return [""]

    if start_date == None:
        df_more = yf.download(val)
    else:
        df_more = yf.download(val, str(start_date), str(end_date))

    df_more.reset_index(inplace=True)
    fig = get_more(df_more)
    return [dcc.Graph(figure=fig, config={
        'scrollZoom': True,
        'doubleClick': 'autosize'
    })]


# callback for forecast
@app.callback([Output("forecast-content", "children")],
              [Input("forecast", "n_clicks")],
              [State("n_days", "value"),
               State("dropdown_tickers", "value")])

def forecast(n, n_days, val):
    if n == None:
        return [""]
    if val == None:
        raise PreventUpdate
    fig = prediction(val, int(n_days) + 1)
    return [dcc.Graph(figure=fig, 
    config={
        'doubleClick': 'autosize'
    })]


if __name__ == '__main__':
    app.run_server(debug=True)
