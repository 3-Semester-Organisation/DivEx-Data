import os

import yfinance as yf
import time, sched
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
cnx = mysql.connector.connect(
    host="",
    port=13306,
    user="root",
    password=os.getenv("DB_PASS"),
    database="jpa_test")

# Get a cursor
cur = cnx.cursor()

dk_tickers = [
    "MAERSK-A.CO",
    "MAERSK-B.CO",
    "NOVO-B.CO",
    "AMBU-B.CO",
    "BAVA.CO",
    "CARL-A.CO",
    "CARL-B.CO",
    "COLO-B.CO",
    "DANSKE.CO",
    "DEMANT.CO",
    "DSV.CO",
    "GMAB.CO",
    "GN.CO",
    "ISS.CO",
    "JYSK.CO",
    "NKT.CO",
    "NDA-DK.CO",
    "NSIS-B.CO",
    "PNDORA.CO",
    "ROCK-B.CO",
    "RBREW.CO",
    "TRMD-A.CO",
    "VWS.CO",
    "ORSTED.CO",
    "ZEAL.CO"
]

nor_tickers = [
    "MPCC.OL", "BWLPG.OL", "HAUTO.OL", "OET.OL", "AGAS.OL",
    "KCC.OL", "RANA.OL", "HAFNI.OL", "EQNR.OL", "BELCO.OL",
    "FRO.OL", "VAR.OL", "ODFB.OL", "FLNG.OL", "WAWI.OL",
    "AKRBP.OL", "DNO.OL", "BWO.OL", "TIETO.OL", "B2I.OL",
    "2020.OL", "GSF.OL", "TEL.OL", "DNB.OL"
]

swe_tickers = [
    "SHB-A.ST", "SSAB-B.ST", "COOR.ST", "TIETOS.ST", "NDA-SE.ST",
    "NPAPER.ST", "CORE-D.ST", "SEB-A.ST", "SWED-A.ST", "FPAR-D.ST",
    "BIOG-B.ST", "VOLV-B.ST", "TELIA.ST", "SAGA-D.ST", "ORES.ST",
    "TEL2-A.ST", "ARP.ST", "AKEL-D.ST", "DUNI.ST", "HPOL-B.ST",
    "CIBUS.ST", "BILI-A.ST", "EWRK.ST", "BETS-B.ST", "8TRA.ST"
]

def get_data(ticker):
    dat = yf.Ticker(ticker)
    info = dat.info
    time.sleep(2)
    dividends = dat.dividends

    opening_date = int(datetime.now().timestamp())
    closing_date = int((datetime.now() - timedelta(days=1)).timestamp())
    open = info.get('open')
    previous_close = info.get('previousClose')

    name = info.get("shortName")
    country = info.get("country")
    exchange = info.get("exchange")
    currency = info.get("currency")
    industry = info.get("industry")
    sector = info.get("sector")

    print(name, ticker, country, exchange, currency, industry, sector)

    dividend_rate = info.get("dividendRate",0)
    payout_ratio = info.get("payoutRatio",0)
    dividend_yield = info.get("dividendYield",0)
    ex_dividend_date = info.get("exDividendDate",0)
    five_year_avg_dividend_yield = info.get("fiveYearAvgDividendYield",0)

    print(dividend_rate,payout_ratio,dividend_yield,ex_dividend_date,five_year_avg_dividend_yield)
    data = (ticker,)
    cur.execute("SELECT id,dividend_id FROM stock WHERE ticker = %s", data)
    data = cur.fetchall()
    row_count = cur.rowcount

    if row_count > 0:
        print("EXISTS: ", ticker)
        stock_id = data[0][0]
        dividend_id = data[0][1]

        div_update_query = "UPDATE dividend SET dividend_rate = %s, dividend_ratio = %s, dividend_yield = %s, ex_dividend_date = %s, five_year_avg_dividend_yield = %s WHERE id = %s"
        data_update = (dividend_rate, payout_ratio, dividend_yield, ex_dividend_date, five_year_avg_dividend_yield,dividend_id)
        cur.execute(div_update_query, data_update)
        cnx.commit()


        hist_div_update_query = "SELECT ex_dividend_date FROM historical_dividend WHERE stock_id = %s ORDER BY ex_dividend_date DESC LIMIT 1"
        cur.execute(hist_div_update_query,(stock_id,))
        old_hist_div_date = cur.fetchone()[0]

        print(old_hist_div_date)

        last_dividend_date = dividends.index[-1]
        dividend_date = datetime.fromisoformat(str(last_dividend_date))
        offset = dividend_date.utcoffset()
        dividend_date_with_offset = dividend_date + offset
        last_dividend_unix = dividend_date_with_offset.timestamp()

        last_dividend_value = dividends.iloc[-1]  # The value of the last dividend

        if last_dividend_unix > old_hist_div_date:
            print("new hist div entry")
            hist_div_query = "INSERT INTO historical_dividend (ex_dividend_date,stock_id, dividend) VALUES(%s,%s,%s)"
            hist_div_data = (last_dividend_unix, stock_id, last_dividend_value)
            cur.execute(hist_div_query, hist_div_data)
            cnx.commit()

        hist_price_query = "INSERT INTO historical_pricing (closing_date, opening_date, opening_price, previous_daily_closing_price, stock_id) VALUES(%s,%s,%s,%s,%s)"
        hist_price_data = (closing_date, opening_date, open, previous_close, stock_id)
        cur.execute(hist_price_query, hist_price_data)
        cnx.commit()
        print("Updated ticker: ", ticker)
    else:
        print("DOESNT EXIST: ", ticker)
        div_query = "INSERT INTO dividend (dividend_rate,dividend_ratio,dividend_yield,ex_dividend_date,five_year_avg_dividend_yield) VALUES(%s,%s,%s,%s,%s)"
        data = (dividend_rate,payout_ratio,dividend_yield,ex_dividend_date,five_year_avg_dividend_yield)
        cur.execute(div_query, data)
        div_auto_id = cur.lastrowid
        cnx.commit()

        stock_query = "INSERT INTO stock (country, currency, exchange, industry, name, sector, ticker ,dividend_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
        data = (country, currency, exchange, industry, name, sector,ticker, div_auto_id)
        cur.execute(stock_query, data)
        stock_auto_id = cur.lastrowid
        cnx.commit()

        hist_price_query = "INSERT INTO historical_pricing (closing_date, opening_date, opening_price, previous_daily_closing_price, stock_id) VALUES(%s,%s,%s,%s,%s)"
        hist_price_data = (closing_date,opening_date,open,previous_close,stock_auto_id)
        cur.execute(hist_price_query, hist_price_data)
        cnx.commit()

        hist_div_query = "INSERT INTO historical_dividend (ex_dividend_date,stock_id, dividend) VALUES(%s,%s,%s)"
        for date, dividend in dividends.items():

            dividend_date = datetime.fromisoformat(str(date))
            offset = dividend_date.utcoffset()
            dividend_date_with_offset = dividend_date + offset
            unix_timestamp = dividend_date_with_offset.timestamp()

            hist_div_data = (unix_timestamp,stock_auto_id,dividend)
            cur.execute(hist_div_query, hist_div_data)
            cnx.commit()
        print("Inserted ticker: ", ticker)


all_tickers = dk_tickers + nor_tickers + swe_tickers

for ticker in dk_tickers:
    get_data(ticker)
    time.sleep(15)
