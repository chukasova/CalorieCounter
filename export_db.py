import pandas as pd

from data_base import products, engine

df = pd.read_csv('products.csv', sep=';', encoding='windows-1251')

with engine.connect() as conn:
    for row in df.itertuples():
        ins = products.insert().values(
            name_product=row.name_product,
            prot=row.prot,
            fat=row.fat,
            carb=row.carb,
            ccal=row.ccal)
        result = conn.execute(ins)
