import psycopg2
import settings

conn = psycopg2.connect(database = settings.db, user = settings.user, password = settings.password)

def create_tables(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS client_info
    (id SERIAL PRIMARY KEY,
    name VARCHAR(60) NOT NULL,
    surname VARCHAR(60) NOT NULL,
    email VARCHAR(60) NOT NULL);

    CREATE TABLE IF NOT EXISTS client_phone
    (id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES client_info(id),
    phone_number VARCHAR(11));
    """

    with conn.cursor() as cur:
        cur.execute(sql)

    conn.commit()

def client_info_add(conn, client_name, client_surname, client_email, phones):
    id = client_find_by_data(conn, client_name, client_surname, client_email)
    if not id:
        sql = """
        INSERT INTO client_info (name,surname,email)
        VALUES (%s,%s,%s) RETURNING id;
        """
        with conn.cursor() as cur:
            cur.execute(sql, (client_name, client_surname, client_email))
            id = cur.fetchone()[0]
    else:
        print('Клиент уже есть в базе')
    if phones:
        for phone in phones:
            client_phone_add(conn, id, phone)
    print('Добавление клиента - ok')
    conn.commit()

def client_phone_add(conn, client_id, client_phone):
    sql = """
    INSERT INTO client_phone (client_id,phone_number)
    VALUES (%s,%s);
    """
    with conn.cursor() as cur:
        cur.execute(sql, (client_id, client_phone))
    print(f'Номер {client_phone} - ok')
    conn.commit()

def client_phone_delete(conn, client_id, client_phone):
    sql = """
    DELETE FROM client_phone WHERE client_id = %s and phone_number = %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (client_id, client_phone))
    print(f'Номер {client_phone} - deleted')
    conn.commit()

def client_delete(conn, client_id):
    sql = "DELETE FROM client_phone WHERE client_id = %s;"
    
    with conn.cursor() as cur:
        cur.execute(sql, (client_id))
    conn.commit()

    sql = "DELETE FROM client_info WHERE id = %s;"
    with conn.cursor() as cur:
        cur.execute(sql, (client_id))
    print("Клиент удалён")
    conn.commit()

def client_find_by_data(conn, client_name, client_surname, client_email):
    sql = """
    SELECT id
    FROM client_info
    WHERE (name = %s
    AND surname = %s)
    OR email = %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (client_name, client_surname, client_email))
        id = cur.fetchone()
        if id:
            id = id[0]

    return id

def client_find(conn, client_name, client_surname, client_email, phones):
    sql = """
    SELECT *
    FROM client_info as ci """
    if phones:
        sql += """
        LEFT JOIN client_phone as cp ON cp.client_id = ci.id
        """
    sql += " WHERE "
    
    if client_name:
        sql += f"ci.name = '{client_name}'"
    if client_surname:
        if client_name:
            sql += " AND "
        sql += f"ci.surname = '{client_surname}'"
    if client_email:
        if client_name or client_surname:
            sql += " AND "
        sql += f"ci.email = '{client_email}'"
    if phones:
        if client_name or client_surname or client_email:
            sql += " AND "
        sql += f"""cp.phone_number IN ('{"','".join(phones)}')"""

    with conn.cursor() as cur:
        cur.execute(sql)
        res = cur.fetchall()
    print(res)
    
def client_find_by_id(conn, client_id):
    sql = """
    SELECT *
    FROM client_info
    WHERE id = %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (client_id))
        res = cur.fetchone()

    return res

def client_info_update(conn, client_name, client_surname, client_email, client_id):
    sql = """
    UPDATE client_info
    SET """

    if client_name:
        sql += f"name = '{client_name}'"
    if client_surname:
        if client_name:
            sql += ","
        sql += f"surname = '{client_surname}'"
    if client_email:
        if client_name or client_surname:
            sql += ","
        sql += f"email = '{client_email}'"

    sql += f" WHERE id = {client_id}" 
    print(sql)
    with conn.cursor() as cur:
        cur.execute(sql)
    print("UPDATE - OK")
    conn.commit()

def start_mes():
    print("""
Выберите требуемое действие, отправив соответствующую цифру:

1 - Создать таблицы для БД
2 - Добавить клиента
3 - Добавить клиенту номер телефона
4 - Изменить данные о клиенте
5 - Удалить телефон у клиента
6 - Удалить клиента
7 - Найти клиента
0 - Выход""")
    
    act_id = input("Введите необходимую цифру: ")

    return act_id

def phones_get():
    phone = input("Телефонный номер (если нету - просто нажмите enter), формат ввода 79181234567: ")
    phones = []
    while phone:
        if len(phone) != 11 or phone[0] != '7':
            phone = input("Неверный формат телефона, введите в формате 79181234567 или нажмите enter, чтобы пропустить: ")
        else:
            try:
                int(phone)
                phones.append(phone)
            except:
                phone = input("Неверный формат телефона, введите в формате 79181234567 или нажмите enter, чтобы пропустить: ")
        phone = input("Ещё телефонный номер (если нету - просто нажмите enter), формат ввода 79181234567: ")
    return phones

act_id = start_mes()
while act_id != '0':
    if act_id == '1':
        create_tables(conn)
        print("Таблицы созданы.")
    elif act_id == '2':
        name = input("Введите имя клиента: ")
        surname = input("Введите фамилию клиента: ")
        email = input("Введите email клиента: ")
        check_email = False
        while not check_email:
            if "@" in email and "." in email:
                check_email = True
            else:
                print("Неверный формат email! \nПример: name@mail.ru")
                email = input("Введите email клиента: ")

        phones = phones_get()

        client_info_add(conn, name, surname, email, phones)
    elif act_id == '3':
        client_id = input("Введите ID клиента: ")
        try:
            client_find_by_id(conn, client_id)
            if client_find_by_id(conn, client_id):
                phones = phones_get()
                if phones:
                    for phone in phones:
                        client_phone_add(conn, client_id, phone)
                else:
                    print("Номер телефона не был указан")
            else:
                print("Нет такого клиента")
        except:
            print("Неверный ввод")
    elif act_id == '4':
        client_id = input("Введите ID клиента: ")
        try:
            client_find_by_id(conn, client_id)
            if client_find_by_id(conn, client_id):
                name = input("Введите имя клиента или нажмите enter, чтобы пропустить: ")
                surname = input("Введите фамилию клиента или нажмите enter, чтобы пропустить: ")
                email = input("Введите email клиента или нажмите enter, чтобы пропустить: ")
                if email:
                    check_email = False
                    while not check_email:
                        if "@" in email and "." in email:
                            check_email = True
                        else:
                            print("Неверный формат email! \nПример: name@mail.ru")
                            email = input("Введите email клиента: ")
                client_info_update(conn, name, surname, email, client_id)
            else:
                print("Нет такого клиента")
        except:
            print("Неверный ввод")
    elif act_id == '5':
        client_id = input("Введите ID клиента: ")
        try:
            client_find_by_id(conn, client_id)
            if client_find_by_id(conn, client_id):
                phones = phones_get()
                if phones:
                    for phone in phones:
                        client_phone_delete(conn, client_id, phone)
                else:
                    print("Номер телефона не был указан")
            else:
                print("Нет такого клиента")
        except:
            print("Неверный ввод")
    elif act_id == '6':
        client_id = input("Введите ID клиента: ")
        try:
            client_find_by_id(conn, client_id)
            if client_find_by_id(conn, client_id):
                client_delete(conn, client_id)
            else:
                print("Нет такого клиента")
        except:
            print("Неверный ввод")
    elif act_id == '7':
        name = input("Введите имя клиента или нажмите enter, чтобы пропустить: ")
        surname = input("Введите фамилию клиента или нажмите enter, чтобы пропустить: ")
        email = input("Введите email клиента или нажмите enter, чтобы пропустить: ")
        phones = phones_get()
        res = client_find(conn, name, surname, email, phones)

    else:
        print("Неверный выбор!")
    act_id = start_mes()

conn.close()