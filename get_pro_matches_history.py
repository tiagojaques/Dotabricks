# Databricks notebook source
# Databricks notebook source
import datetime
import requests
from pyspark.sql import functions as F

def get_data(**kwargs):    
    url = "https://api.opendota.com/api/proMatches"
    
    params = "&".join([f"{k}={v}" for k,v in kwargs.items()])
    if params != "":
        url += "?" + params

    response = requests.get(url)
    return response.json()

def read_matches_s3():
    df = spark.read.parquet("/mnt/datalake/raw/pro_matches_history")
    return df

def get_min_match_id(df):
    min_match_id = df.groupBy().agg(F.min("match_id")).collect()[0][0]
    return min_match_id

def get_max_date(df):
    max_date = df.withColumn("match_date", F.from_unixtime("start_time")).groupBy().agg( F.date_add(F.max(F.col("match_date")),-1)).collect()[0][0]
    return max_date

def get_min_date(df):
    min_date = df.withColumn("match_date", F.from_unixtime("start_time")).groupBy().agg( F.date_add(F.min(F.col("match_date")),-1)).collect()[0][0]
    return min_date

def save_match_list(df):
    df.coalesce(1).write.mode("append").parquet("/mnt/datalake/raw/pro_matches_history")
    
def get_and_save(**kwargs):
    data = get_data(**kwargs) # obtem partidas novas a partir da partida mais antiga
    df = spark.createDataFrame(data) # transforma em df spark
    save_match_list(df) # salva os dados em modo append
    return df

def get_history_pro_matches(**kwargs):
    df = read_matches_s3() # lê os dados do datalake
    #df_new = get_min_match_id(df) Pega partida mais antiga do nosso datalake
    min_match_id = get_min_match_id(df)
    while min_match_id is not None:
        print(min_match_id)
        try:
            df_new = get_and_save(less_than_match_id=min_match_id)
            min_match_id = get_min_match_id(df_new)
        
        except AnalysisException as err:
            print(err)
            break
            
def get_new_pro_matches(**kwargs):
    df = read_matches_s3() # lê os dados do datalake
    max_date = get_max_date(df)
    df_new = get_and_save(**kwargs)
    date_process = get_min_date(df_new)
    min_match_id = get_min_match_id(df_new)

    print(min_match_id)
    while max_date <= date_process:
        df_new = get_and_save(less_than_match_id=min_match_id)
        min_match_id = get_min_match_id(df_new)


mode = dbutils.widgets.get("mode")

if mode == "new":
    get_new_pro_matches()

elif mode == "history":
    get_history_pro_matches()

# COMMAND ----------

df = read_matches_s3()
min_match_id = df.groupBy().agg(F.min("match_id")).collect()[0][0]
print(min_match_id)

# COMMAND ----------

get_history_pro_matches()
