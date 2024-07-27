

import streamlit as st
from streamlit_option_menu import option_menu
import sqlite3
import hashlib

# Функция для создания таблиц в базе данных
def init_db():
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            user_id INTEGER,
            content TEXT NOT NULL,
            parent_comment_id INTEGER,
            FOREIGN KEY(article_id) REFERENCES articles(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Хеширование паролей
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Функция для регистрации пользователя
def register_user(username, password, is_admin=False):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)', 
                  (username, hash_password(password), int(is_admin)))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Пользователь с таким именем уже существует.")
    conn.close()

# Функция для проверки учетных данных пользователя
def login_user(username, password):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', 
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

# Функция для создания статьи
def create_article(user_id, title, content):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('INSERT INTO articles (user_id, title, content) VALUES (?, ?, ?)', 
              (user_id, title, content))
    conn.commit()
    conn.close()

# Функция для удаления статьи (для администраторов)
def delete_article(article_id):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('DELETE FROM articles WHERE id=?', (article_id,))
    c.execute('DELETE FROM comments WHERE article_id=?', (article_id,))
    conn.commit()
    conn.close()

# Функция для удаления статьи пользователя
def delete_user_article(article_id, user_id):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('DELETE FROM articles WHERE id=? AND user_id=?', (article_id, user_id))
    c.execute('DELETE FROM comments WHERE article_id=?', (article_id,))
    conn.commit()
    conn.close()

# Функция для удаления пользователя (для администраторов)
def delete_user(user_id):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    
    # Удаление всех статей пользователя
    c.execute('DELETE FROM articles WHERE user_id=?', (user_id,))
    
    # Удаление всех комментариев пользователя
    c.execute('DELETE FROM comments WHERE user_id=?', (user_id,))
    
    # Удаление самого пользователя
    c.execute('DELETE FROM users WHERE id=?', (user_id,))
    
    conn.commit()
    conn.close()

# Функция для удаления комментария (для администраторов)
def delete_comment(comment_id):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('DELETE FROM comments WHERE id=?', (comment_id,))
    conn.commit()
    conn.close()

# Функция для получения всех статей
def get_all_articles():
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('SELECT articles.id, users.username, articles.title, articles.content FROM articles JOIN users ON articles.user_id = users.id')
    articles = c.fetchall()
    conn.close()
    return articles

# Функция для получения статей пользователя
def get_user_articles(user_id):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('SELECT id, title, content FROM articles WHERE user_id=?', (user_id,))
    articles = c.fetchall()
    conn.close()
    return articles

# Функция для добавления комментария
def add_comment(article_id, user_id, content, parent_comment_id=None):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('INSERT INTO comments (article_id, user_id, content, parent_comment_id) VALUES (?, ?, ?, ?)', 
              (article_id, user_id, content, parent_comment_id))
    conn.commit()
    conn.close()

# Функция для получения комментариев к статье
def get_article_comments(article_id):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('SELECT comments.id, users.username, comments.content FROM comments JOIN users ON comments.user_id = users.id WHERE article_id=? AND parent_comment_id IS NULL', (article_id,))
    comments = c.fetchall()
    conn.close()
    return comments

# Функция для получения ответов на комментарии
def get_comment_replies(comment_id):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('SELECT comments.id, users.username, comments.content FROM comments JOIN users ON comments.user_id = users.id WHERE parent_comment_id=?', (comment_id,))
    replies = c.fetchall()
    conn.close()
    return replies

# Функция для отображения других статей автора в диалоговом окне
@st.experimental_dialog("Другие статьи автора")
def show_other_articles_by_author(author_name):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('SELECT id, title, content FROM articles WHERE user_id=(SELECT id FROM users WHERE username=?)', (author_name,))
    articles = c.fetchall()
    conn.close()

    if articles:
        selected_article = st.selectbox(f"Другие статьи автора {author_name}", [f"{article[1]} (ID: {article[0]})" for article in articles])
        if selected_article:
            article_id = int(selected_article.split('(ID: ')[1].split(')')[0])
            full_content = [article[2] for article in articles if article[0] == article_id][0]
            st.write(full_content)
    else:
        st.info(f"Нет других статей от автора {author_name}")

# Функция для отображения статьи
@st.experimental_dialog("Полная версия статьи")
def show_article_content(content):
    st.write(content)

def show_article(article_id, title, content):
    st.subheader(title)
    if len(content) > 100:
        st.text(content[:100] + '...')
        if st.button("Читать полностью", key=f"full_{article_id}"):
            show_article_content(content)
    else:
        st.text(content)

# Главная страница
def main_page():
    st.title("Все статьи")
    articles = get_all_articles()
    for article in articles:
        show_article(article[0], article[2], article[3])
        st.subheader("Комментарии")
        comments = get_article_comments(article[0])
        for comment in comments:
            st.write(f"{comment[1]}: {comment[2]}")
            replies = get_comment_replies(comment[0])
            for reply in replies:
                st.write(f"--- {reply[1]}: {reply[2]}")
            if 'logged_in' in st.session_state:
                reply_content = st.text_input(f"Ответить на комментарий от {comment[1]}", key=f"reply_{comment[0]}")
                if st.button(f"Ответить на комментарий {comment[1]}", key=f"submit_reply_{comment[0]}"):
                    if reply_content:
                        add_comment(article[0], st.session_state['user_id'], reply_content, comment[0])
                        st.rerun()
            if 'logged_in' in st.session_state and st.session_state['is_admin']:
                if st.button(f"Удалить комментарий {comment[2]}", key=f"delete_comment_{comment[0]}"):
                    delete_comment(comment[0])
                    st.rerun()
        if 'logged_in' in st.session_state:
            comment_content = st.text_input(f"Добавить комментарий к статье {article[2]}", key=f"comment_{article[0]}")
            if st.button(f"Отправить комментарий к статье {article[2]}", key=f"submit_comment_{article[0]}"):
                if comment_content:
                    add_comment(article[0], st.session_state['user_id'], comment_content)
                    st.rerun()
        if st.button(f"Показать другие статьи автора {article[1]}", key=f"show_other_articles_{article[1]}_{article[0]}"):
            show_other_articles_by_author(article[1])
        st.markdown("---")

# Функция для страницы регистрации
def register_page():
    st.title("Регистрация")
    username = st.text_input("Имя пользователя")
    password = st.text_input("Пароль", type="password")
    if st.button("Зарегистрироваться"):
        register_user(username, password)
        st.success("Регистрация прошла успешно!")

# Функция для страницы входа
def login_page():
    st.title("Вход")
    username = st.text_input("Имя пользователя")
    password = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        user = login_user(username, password)
        if user:
            st.session_state['logged_in'] = True
            st.session_state['username'] = user[1]
            st.session_state['user_id'] = user[0]
            st.session_state['is_admin'] = user[3]
            st.success("Вход выполнен успешно!")
            st.rerun()
        else:
            st.error("Неверное имя пользователя или пароль")

# Функция для назначения пользователя администратором по имени
def assign_admin_by_username(username):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET is_admin=1 WHERE username=?', (username,))
    conn.commit()
    conn.close()

def unassign_admin_by_username(username):
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET is_admin=0 WHERE username=?', (username,))
    conn.commit()
    conn.close()

def show_all_accounts():
    conn = sqlite3.connect('./users.db')
    c = conn.cursor()
    c.execute('SELECT username, password FROM users')
    accounts = c.fetchall()
    conn.close()

    for account in accounts:
        st.markdown("---")
        st.write(f"**Username:** {account[0]}")
        st.write(f"**Password:** {account[1]}")
        #st.write(f"**Comments:** {account[2]}")

# Главная функция
def main():
    init_db()

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        with st.sidebar:
            selected = option_menu("Меню", ["Все статьи", "Мои статьи", "Создать статью", "Удалить аккаунт", "Выйти"],
                                   icons=["house", "file-earmark", "pencil-square", "trash", "box-arrow-right"])
        if selected == "Все статьи":
            main_page()
        elif selected == "Мои статьи":
            user_articles = get_user_articles(st.session_state['user_id'])
            for article in user_articles:
                st.subheader(article[1])
                st.text(article[2])
                if st.button(f"Удалить статью {article[1]}", key=f"delete_article_{article[0]}"):
                    delete_user_article(article[0], st.session_state['user_id'])
                    st.rerun()
                st.markdown("---")
        elif selected == "Создать статью":
            st.title("Создать статью")
            title = st.text_input("Заголовок")
            content = st.text_area("Содержание")
            if st.button("Опубликовать"):
                create_article(st.session_state['user_id'], title, content)
                st.success("Статья опубликована!")
        elif selected == "Удалить аккаунт":
            if st.button("Удалить мой аккаунт"):
                delete_user(st.session_state['user_id'])
                st.session_state['logged_in'] = False
                st.rerun()
        elif selected == "Выйти":
            st.session_state['logged_in'] = False
            st.rerun()
        if st.session_state['is_admin']:
            with st.sidebar:
                st.sidebar.subheader("Администратор")
                admin_selected = option_menu("Админ-меню", 
                    ["Удалить пользователя", "Назначить администратора", "Снять с админов", "Докс"], 
                    icons=["person-dash", "person-plus-fill", "person-dash-fill", "key-fill", "Очистить статьи пользователя"])
                if admin_selected == "Удалить пользователя":
                    username_to_delete = st.text_input("Имя пользователя для удаления")
                    if st.button("Удалить пользователя"):
                        conn = sqlite3.connect('./users.db')
                        c = conn.cursor()
                        c.execute('SELECT id FROM users WHERE username=?', (username_to_delete,))
                        user = c.fetchone()
                        if user:
                            delete_user(user[0])
                            st.success("Пользователь удалён!")
                        else:
                            st.error("Пользователь не найден.")
                        conn.close()
                elif admin_selected == "Назначить администратора":
                    username_to_delete = st.text_input("Имя пользователя для назначения")
                    if username_to_delete:
                        assign_admin_by_username(username_to_delete)
                        st.success(f"Пользователь {username_to_delete} назначен администратором.")
                    else:
                        st.warning("Пожалуйста, введите имя пользователя.")

                elif admin_selected == "Снять с админов":
                    username_to_delete = st.text_input("Имя пользователя для снятия")
                    if username_to_delete:
                        unassign_admin_by_username(username_to_delete)
                        st.success(f"Пользователь {username_to_delete} был снят с админинов.")
                    else:
                        st.warning("Пожалуйста, введите имя пользователя.")

                elif admin_selected == "Докс":
                    show_all_accounts()

    else:
        with st.sidebar:
            page = option_menu("Меню", ["Войти", "Зарегистрироваться"], icons=["box-arrow-in-right", "person-plus"])
        if page == "Войти":
            login_page()
        elif page == "Зарегистрироваться":
            register_page()

if __name__ == "__main__":
    main()
