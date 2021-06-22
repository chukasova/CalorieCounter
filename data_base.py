from sqlalchemy import create_engine, Table, DateTime, select
from sqlalchemy import Column, Integer, String, Float, Table, ForeignKey
from sqlalchemy import MetaData
from sqlalchemy.engine import LegacyCursorResult
from sqlalchemy.sql import func
from sqlalchemy.sql import text

from sqlalchemy.ext.declarative import declarative_base

meta = MetaData()

# engine = create_engine('sqlite:///user.db', echo=True)
engine = create_engine("mysql+pymysql://chuka:Azsxdcf123*@localhost:3306/kaloriescounter", echo=True)

users: Table = Table(
    'users', meta,
    Column('id', Integer, primary_key=True),
    Column('gender', String(100)),
    Column('weight', Float),
    Column('height', Float),
    Column('calories', Float),
    Column('age', Integer),
)

products: Table = Table(
    'products', meta,
    Column('id', Integer, primary_key=True),
    Column('name_product', String(100)),
    Column('prot', Float),
    Column('fat', Float),
    Column('carb', Float),
    Column('ccal', Float),
)

users_product: Table = Table(
    'users_product', meta,
    Column('id', Integer, primary_key=True),
    Column('users_id', Integer, ForeignKey('users.id')),
    Column('products_id', Integer, ForeignKey('products.id')),
    Column('mass', Float),
    Column('total_ccal', Float),
    Column('time', DateTime(timezone=True), server_default=func.now())
)


def create_user_table():
    meta.drop_all(engine)
    meta.create_all(engine)


def add_user(user_id, gender, weight, height, calories, age):
    ins = users.insert().values(id=user_id,
                                gender=gender,
                                weight=weight,
                                height=height,
                                calories=calories,
                                age=age)
    conn = engine.connect()
    result = conn.execute(ins)


def get_user(user_id):
    sel = users.select().where(users.c.id == user_id)
    conn = engine.connect()
    result = conn.execute(sel)
    return result.fetchone()


def get_user_kkal(user_id):
    statement = '''SELECT calories FROM kaloriescounter.users
where id = %s'''

    with engine.connect() as con:
        res: LegacyCursorResult = con.execute(statement, (user_id,))
    return res.fetchone()


def eat_today(user_id):
    statement = '''SELECT products.name_product, users_product.mass, users_product.total_ccal FROM kaloriescounter.users_product
INNER JOIN products ON users_product.products_id = products.id
where time > current_date()
and users_id = %s'''

    with engine.connect() as con:
        res: LegacyCursorResult = con.execute(statement, (user_id,))
    return res.fetchall()


def user_update_weight(user_id, weight_new):
    conn = engine.connect()
    stmt = users.update().where(users.c.id == user_id).values(weight=weight_new)
    conn.execute(stmt)


def user_update_age(user_id, age_new):
    conn = engine.connect()
    stmt = users.update().where(users.c.id == user_id).values(age=age_new)
    conn.execute(stmt)


def user_update_height(user_id, height_new):
    conn = engine.connect()
    stmt = users.update().where(users.c.id == user_id).values(height=height_new)
    conn.execute(stmt)


def user_update_calories(user_id, calories_new):
    conn = engine.connect()
    stmt = users.update().where(users.c.id == user_id).values(calories=calories_new)
    conn.execute(stmt)


def add_new_prod(name_product, fat, prot, carb, ccal):
    ins = products.insert().values(name_product=name_product,
                                   prot=prot,
                                   fat=fat,
                                   carb=carb,
                                   ccal=ccal
                                   )
    with engine.connect() as conn:
        result = conn.execute(ins)


def add_eaten_product(user_id, products_id, mass, total_ccal):
    ins = users_product.insert().values(users_id=user_id,
                                        products_id=products_id,
                                        mass=mass,
                                        total_ccal=total_ccal,
                                        )
    with engine.connect() as conn:
        result = conn.execute(ins)


def get_search_prod(string):
    conn = engine.connect()
    stmt = select(products).where(products.c.name_product == string)
    result = conn.execute(stmt)
    return result.all()


def get_like(string):
    conn = engine.connect()
    stmt = select(products).where(products.c.name_product.startswith(string))
    result = conn.execute(stmt)
    return result.all()


def get_last_data(user_id):
    statement = ''' 
    select users_id, SUM(total_ccal), DATE(time) FROM users_product 
    WHERE time >= DATE_ADD(CURDATE(), INTERVAL -6 DAY) and users_id = %s
    GROUP BY DATE(time)
    '''
    with engine.connect() as con:
        res: LegacyCursorResult = con.execute(statement, (user_id,))
    return res.fetchall()


if __name__ == '__main__':
    create_user_table()
