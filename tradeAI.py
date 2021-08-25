import time
import pyupbit
import datetime
import schedule
import requests
from fbprophet import Prophet

access = "dCHhpFD2wGux5pvzE"
secret = "xWgUlKSbWz2nF"
myToken = "xoxb-Cm"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

predicted_close_price = 0
def predict_price(ticker):
    """Prophet으로 당일 종가 가격 예측"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute60")
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    if len(closeDf) == 0:
        closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price = closeValue
predict_price("KRW-DOGE")
schedule.every().hour.do(lambda: predict_price("KRW-DOGE"))

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("Autotrade start DOGE")
post_message(myToken,"#coin", "Autotrade start DOGE")

# 총 매수 할 원화, 분할 매수 비율
total = 500000


# 시간 간격
interval = "day"

# ticker, k, currency
ticker = "KRW-DOGE"
currency = "DOGE"
k = 0.12

# 자동매매 시작
while True:

    # 시간 설정
    start_time = get_start_time(ticker)
    now = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(days=1) - datetime.timedelta(seconds=5)
       
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-DOGE")
        end_time = start_time + datetime.timedelta(days=1)
        schedule.run_pending()

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-DOGE", k)
            current_price = get_current_price("KRW-DOGE")
            
            if target_price < current_price and current_price < predicted_close_price:
                upbit.buy_market_order(ticker, total)
                time.sleep(1)
                buy_average = get_buy_average(currency)
        else:
            btc = get_balance("DOGE")
            if btc > 0.00008:
                upbit.sell_market_order("KRW-DOGE", btc*0.9995)
        time.sleep(1)
        
    except Exception as e:
        print(e)
        post_message(myToken,"#coin", e)
        time.sleep(1)
