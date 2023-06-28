import sqlite3


def start_db():
    global cursor, conn
    conn = sqlite3.connect('todo_app.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            todo_text TEXT,
            done BOOLEAN,
            chat_id INTEGER,
            todo_number INTEGER
        )
    ''')
    conn.commit()

    # Триггер для автоматического увеличения todo_number при удалении
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_todo_number
        AFTER INSERT ON job
        FOR EACH ROW
        BEGIN
            UPDATE job
            SET todo_number = (
                SELECT IFNULL(MAX(todo_number), 0) + 1
                FROM job
                WHERE chat_id = NEW.chat_id
            )
            WHERE id = NEW.id;
        END;
    ''')
    conn.commit()

    # Триггер для автоматического уменьшения todo_number при удалении
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS decrement_todo_number
        BEFORE DELETE ON job
        FOR EACH ROW
        BEGIN
            UPDATE job
            SET todo_number = todo_number - 1
            WHERE chat_id = OLD.chat_id
              AND todo_number > (SELECT todo_number FROM job WHERE id = OLD.id);
        END;
    ''')
    conn.commit()


def check_todo(chat_id, **kwargs):
    """
    Получает на входе chat_id и некоторые именованные парамаетры,
    и проверяет наличие записи в таблице job по заданным параметрам.
    В зависимости какой именованный параметр передан будет определяться
    алгоритм поиска записи в таблице job.
    Если в словаре kwargs присутствует todo_text, то проверка будет выполняться
    по параметрам todo_text и chat_id.
    Если в словаре kwargs  не присутствует todo_text, то проверка будет выполняться
    по параметрам todo_number и chat_id.
    :param chat_id: ID чата в телеграм
    :param kwargs: todo_text или todo_number
    :return: Запись существует - True, запись не существует - False
    """
    if kwargs.get('todo_text'):
        sql_query = '''SELECT * FROM job WHERE chat_id = ? AND todo_text = ?'''
        cursor.execute(sql_query, (chat_id, kwargs['todo_text']))
    else:
        sql_query = '''SELECT * FROM job WHERE chat_id = ? AND todo_number = ?'''
        cursor.execute(sql_query, (chat_id, kwargs['todo_number']))
    if cursor.fetchone():
        return True
    else:
        return False


def get_todos(chat_id):
    """
    Получает на входе chat_id и возвращает все записи с таблицы job
    :param chat_id: ID чата в телеграм
    :return: Возвращает список задач из базы данных по данноу chat_id
    """
    sql_query = '''SELECT * FROM job WHERE chat_id = ?'''
    cursor.execute(sql_query, (chat_id,))
    todos = cursor.fetchall()
    return todos


async def create_todo(todo, chat_id):
    """
    Создает в таблице job задачу
    :param todo: Описание задачи
    :param chat_id: ID чата в телеграм
    """
    sql_query = '''INSERT INTO job (todo_text, done, chat_id) VALUES (?, ?, ?)'''
    cursor.execute(sql_query, (todo, False, chat_id))
    conn.commit()


def done_todo(todo_number, chat_id):
    """
    Отмечает в таблице значение done=True записи под номером todo_number
    :param todo_number: Номер задачи
    :param chat_id: ID чата в телеграм
    """
    sql_query = '''UPDATE job SET done = ? WHERE chat_id = ? AND todo_number = ?'''
    cursor.execute(sql_query, (True, chat_id, todo_number))
    conn.commit()


def delete_todo(todo_number, chat_id):
    """
    Удаляет в таблице job запись где chat_id и todo_number равен к заданным параметрам
    :param todo_number: Номер задачи
    :param chat_id: ID чата в телеграм
    """
    sql_query = '''DELETE FROM job WHERE chat_id = ? AND todo_number = ?'''
    cursor.execute(sql_query, (chat_id, todo_number))
    conn.commit()



