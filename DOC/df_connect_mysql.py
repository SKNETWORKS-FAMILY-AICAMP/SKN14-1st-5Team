import pandas as pd
from sqlalchemy import create_engine
import pymysql

df = pd.read_csv('car_accident_cleaned.csv')

engine = create_engine('mysql+pymysql://skn14:skn14@localhost:3306/accidentdb', echo=True)

df.to_sql(name='car_accident', con=engine, if_exists='replace', index=False)