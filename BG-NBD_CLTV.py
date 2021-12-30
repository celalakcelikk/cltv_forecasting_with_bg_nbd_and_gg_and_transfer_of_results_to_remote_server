import datetime as dt

import pandas as pd
from lifetimes import BetaGeoFitter, GammaGammaFitter
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import create_engine

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 500)
pd.set_option('display.float_format', lambda x: '%.4f' % x)

##################################################
# Verinin Veri Tabanından ya da Dosyadan Okunması
##################################################

creds = {'user': 'user',
         'passwd': '****',
         'host': '0.0.0.0',
         'port': 3306,
         'db': 'db'}

# MySQL conection string.
connstr = 'mysql+mysqlconnector://{user}:{passwd}@{host}:{port}/{db}'

# sqlalchemy engine for MySQL connection.
conn = create_engine(connstr.format(**creds))

retail_mysql_df = pd.read_sql_query("select * from online_retail_2010_2011", conn)
df = retail_mysql_df.copy()

#: OR
retail_excel_df = pd.read_excel("datasets/online_retail_II.xlsx", sheet_name="Year 2010-2011")
df = retail_excel_df.copy()


#########################
# Veri Ön İşleme
#########################

def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit


def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit


df.dropna(inplace=True)
df = df[~df["Invoice"].str.contains("C", na=False)]
df = df[df["Quantity"] > 0]
df = df[df["Price"] > 0]
replace_with_thresholds(df, "Quantity")
replace_with_thresholds(df, "Price")
df["TotalPrice"] = df["Quantity"] * df["Price"]

#######################################
# Lifetime Veri Yapısının Hazırlanması
#######################################
# recency: Son satın alma üzerinden geçen zaman. Haftalık. (daha önce analiz gününe göre, burada kullanıcı özelinde)
# T: Analiz tarihinden ne kadar süre önce ilk satın alma yapılmış. Haftalık.
# frequency: tekrar eden toplam satın alma sayısı (frequency>1)
# monetary_value: satın alma başına ortalama kazanç

today_date = df["InvoiceDate"].max() + dt.timedelta(days=2)
today_date = today_date.replace(hour=0, minute=0, second=0)
df = df[df["Country"] == "United Kingdom"]
cltv_df = df.groupby('CustomerID').agg(
    {'InvoiceDate': [lambda InvoiceDate: (InvoiceDate.max() - InvoiceDate.min()).days,
                     lambda InvoiceDate: (today_date - InvoiceDate.min()).days],
     'Invoice': lambda Invoice: Invoice.nunique(),
     'TotalPrice': lambda TotalPrice: TotalPrice.sum()})

cltv_df.columns = cltv_df.columns.droplevel(0)
cltv_df.columns = ['recency', 'T', 'frequency', 'monetary']
cltv_df["monetary"] = cltv_df["monetary"] / cltv_df["frequency"]
cltv_df = cltv_df[(cltv_df['frequency'] > 1)]
cltv_df["recency"] = cltv_df["recency"] / 7
cltv_df["T"] = cltv_df["T"] / 7

#############################
# BG-NBD Modelinin Kurulması
#############################

bgf = BetaGeoFitter(penalizer_coef=0.001)

bgf.fit(cltv_df['frequency'],
        cltv_df['recency'],
        cltv_df['T'])

cltv_df["expected_purc_1_week"] = bgf.predict(1,
                                              cltv_df['frequency'],
                                              cltv_df['recency'],
                                              cltv_df['T'])

cltv_df["expected_purc_1_month"] = bgf.predict(4,
                                               cltv_df['frequency'],
                                               cltv_df['recency'],
                                               cltv_df['T'])

#################################
# GAMMA-GAMMA Modelinin Kurulması
#################################

ggf = GammaGammaFitter(penalizer_coef=0.01)
ggf.fit(cltv_df['frequency'], cltv_df['monetary'])
cltv_df["expected_average_profit"] = ggf.conditional_expected_average_profit(cltv_df['frequency'],
                                                                             cltv_df['monetary'])

#########################
# 6 aylık CLTV Prediction
#########################
#: 2010-2011 UK müşterileri için 6 aylık CLTV prediction yapınız.
#: Elde ettiğiniz sonuçları yorumlayıp üzerinde değerlendirme yapınız.
#: Dikkat!
##: 6 aylık expected sales değil cltv prediction yapılmasını bekliyoruz.
##: Yani direkt BGNBD & GAMMA modellerini kurarak devam ediniz ve cltv prediction için ay bölümüne 6 giriniz.

#: BG-NBD ve GG modeli ile CLTV'nin hesaplanması.
cltv = ggf.customer_lifetime_value(bgf,
                                   cltv_df['frequency'],
                                   cltv_df['recency'],
                                   cltv_df['T'],
                                   cltv_df['monetary'],
                                   time=6,  # 6 aylık
                                   freq="W",  # T'nin frekans bilgisi.
                                   discount_rate=0.01)
cltv = cltv.reset_index()
cltv_final = cltv_df.merge(cltv, on="CustomerID", how="left")

scaler = MinMaxScaler(feature_range=(0, 1))
scaler.fit(cltv_final[["clv"]])
cltv_final["scaled_clv"] = scaler.transform(cltv_final[["clv"]])

##################################################
# Farklı zaman periyotlarından oluşan CLTV analizi
##################################################
#: 2010-2011 UK müşterileri için 1 aylık ve 12 aylık CLTV hesaplayınız.
#: 1 aylık CLTV'de en yüksek olan 10 kişi ile 12 aylık'taki en yüksek 10 kişiyi analiz ediniz.
#: Fark var mı? Varsa sizce neden olabilir?
#: Dikkat!
##: Sıfırdan model kurulmasına gerek yoktur.
##: Önceki adımda oluşturulan model üzerinden ilerlenebilir.

#: 1 aylık
cltv = ggf.customer_lifetime_value(bgf,
                                   cltv_df['frequency'],
                                   cltv_df['recency'],
                                   cltv_df['T'],
                                   cltv_df['monetary'],
                                   time=1,  # 1 aylık
                                   freq="W",  # T'nin frekans bilgisi.
                                   discount_rate=0.01)
cltv = cltv.reset_index()
cltv_final_1_month = cltv_df.merge(cltv, on="CustomerID", how="left")

scaler = MinMaxScaler(feature_range=(0, 1))
scaler.fit(cltv_final_1_month[["clv"]])
cltv_final_1_month["scaled_clv"] = scaler.transform(cltv_final_1_month[["clv"]])

#: 12 aylık
cltv = ggf.customer_lifetime_value(bgf,
                                   cltv_df['frequency'],
                                   cltv_df['recency'],
                                   cltv_df['T'],
                                   cltv_df['monetary'],
                                   time=12,  # 12 aylık
                                   freq="W",  # T'nin frekans bilgisi.
                                   discount_rate=0.01)
cltv = cltv.reset_index()
cltv_final_12_month = cltv_df.merge(cltv, on="CustomerID", how="left")

scaler = MinMaxScaler(feature_range=(0, 1))
scaler.fit(cltv_final_1_month[["clv"]])
cltv_final_12_month["scaled_clv"] = scaler.transform(cltv_final_12_month[["clv"]])

####################################
# Segmentasyon ve Aksiyon Önerileri
####################################
#: 2010-2011 UK müşterileri için 6 aylık CLTV'ye göre tüm müşterilerinizi 4 gruba (segmente) ayırınız ve grup isimlerini veri setine ekleyiniz.
#: 4 grup içerisinden seçeceğiniz 2 grup için yönetime kısa kısa 6 aylık aksiyon önerilerinde bulununuz

cltv_final["segment"] = pd.qcut(cltv_final["scaled_clv"], 4, labels=["D", "C", "B", "A"])
cltv_final.head()

###############################
# Veri tabanına kayıt gönderme
###############################
#: Aşağıdaki değişkenlerden oluşacak final tablosunu veri tabanına gönderiniz.
#: Tablonun adını isim_soyisim şeklinde oluşturunuz.
#: Tablo ismi ilgili fonksiyonda "name" bölümüne girilmelidir.

cltv_final["CustomerID"] = cltv_final["CustomerID"].astype(int)
cltv_final.to_sql(name='celal_akcelik', con=conn, if_exists='replace', index=False)
