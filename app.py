import streamlit as st
from streamlit_option_menu import option_menu
import sqlite3
import hashlib
import os

data_base = "./users.db"

# Функция для создания таблиц в базе данных
def init_db():
    conn = sqlite3.connect(data_base)
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
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            video_path TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            user_id INTEGER,
            content TEXT NOT NULL,
            FOREIGN KEY(video_id) REFERENCES videos(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY(video_id) REFERENCES videos(id),
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
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, is_admin) VALUES (?,?,?)', 
                  (username, hash_password(password), int(is_admin)))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Пользователь с таким именем уже существует.")
    conn.close()

# Функция для проверки учетных данных пользователя
def login_user(username, password):
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', 
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

# Функция для создания видеоролика
def create_video(user_id, title, description, video_path):
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('INSERT INTO videos (user_id, title, description, video_path) VALUES (?,?,?,?)', 
              (user_id, title, description, video_path))
    conn.commit()
    conn.close()

# Функция для удаления видеоролика
def delete_video(video_id):
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('DELETE FROM videos WHERE id=?', (video_id,))
    conn.commit()
    conn.close()

# Функция для получения всех видеороликов
def get_all_videos():
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('SELECT videos.id, users.username, videos.title, videos.description, videos.video_path FROM videos JOIN users ON videos.user_id = users.id')
    videos = c.fetchall()
    conn.close()
    return videos

# Функция для получения видеороликов пользователя
def get_user_videos(user_id):
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('SELECT id, title, description, video_path FROM videos WHERE user_id=?', (user_id,))
    videos = c.fetchall()
    conn.close()
    return videos

# Функция для добавления комментария
def add_comment(video_id, user_id, content):
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('INSERT INTO comments (video_id, user_id, content) VALUES (?,?,?)', 
              (video_id, user_id, content))
    conn.commit()
    conn.close()

# Функция для получения комментариев к видеоролику
def get_video_comments(video_id):
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('SELECT comments.id, users.username, comments.content FROM comments JOIN users ON comments.user_id = users.id WHERE video_id=?', (video_id,))
    comments = c.fetchall()
    conn.close()
    return comments

# Функция для добавления лайка
def add_like(video_id, user_id):
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('INSERT INTO likes (video_id, user_id) VALUES (?,?)', 
              (video_id, user_id))
    conn.commit()
    conn.close()

# Функция для получения количества лайков видеоролика
def get_video_likes(video_id):
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM likes WHERE video_id=?', (video_id,))
    likes = c.fetchone()[0]
    conn.close()
    return likes

# Функция для отображения видеоролика
def show_video(video_id):
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('SELECT videos.id, users.username, videos.title, videos.description, videos.video_path FROM videos JOIN users ON videos.user_id = users.id WHERE videos.id=?', (video_id,))
    video = c.fetchone()
    conn.close()
    st.title(video[2])
    st.text(video[3])
    st.video(video[4])
    likes = get_video_likes(video_id)
    st.write(f"Лайков: {likes}")
    if st.button("Лайк"):
        add_like(video_id, st.session_state['user_id'])
        st.rerun()
    comments = get_video_comments(video_id)
    for comment in comments:
        st.write(f"{comment[1]}: {comment[2]}")
    comment_content = st.text_input("Добавить комментарий")
    if st.button("Отправить комментарий"):
        add_comment(video_id, st.session_state['user_id'], comment_content)
        st.rerun()
    user_videos = get_user_videos(video[1])
    st.write("Другие видеоролики автора:")
    for user_video in user_videos:
        if user_video[0]!= video_id:
            st.write(f"{user_video[1]}")
            st.video(user_video[3])

# Главная страница
def main_page():
    st.title("Все видеоролики")
    videos = get_all_videos()
    for video in videos:
        st.write(f"{video[2]}")
        st.video(video[4])
        if st.button(f"Открыть видеоролик {video[2]}"):
            show_video(video[0])

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
            st.success("Вход выполнен успешно!")
            st.rerun()
        else:
            st.error("Неправильный логин или пароль")

# Функция для назначения пользователя администратором по имени
def assign_admin_by_username(username):
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('UPDATE users SET is_admin=1 WHERE username=?', (username,))
    conn.commit()
    conn.close()

def unassign_admin_by_username(username):
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('UPDATE users SET is_admin=0 WHERE username=?', (username,))
    conn.commit()
    conn.close()

def show_all_accounts():
    conn = sqlite3.connect(data_base)
    c = conn.cursor()
    c.execute('SELECT username, password FROM users')
    accounts = c.fetchall()
    conn.close()

    for account in accounts:
        st.markdown("---")
        st.write(f"**Username:** {account[0]}")
        st.write(f"**Password:** {account[1]}")

# Главная функция
def main():
    init_db()

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        with st.sidebar:
            selected = option_menu("Меню", ["Все видеоролики", "Мои видеоролики", "Загрузить видеоролик", "Удалить аккаунт", "Выйти"],
                                   icons=["house", "file-earmark", "pencil-square", "trash", "box-arrow-right"])
        if selected == "Все видеоролики":
            main_page()
        elif selected == "Мои видеоролики":
            user_videos = get_user_videos(st.session_state['user_id'])
            for video in user_videos:
                st.write(f"{video[1]}")
                st.video(video[3])
        elif selected == "Загрузить видеоролик":
            st.title("Загрузить видеоролик")
            title = st.text_input("Название видеоролика")
            description = st.text_area("Описание видеоролика")
            video_file = st.file_uploader("Выбрать видеофайл")
            if st.button("Загрузить"):
                create_video(st.session_state['user_id'], title, description, video_file.name)
                st.success("Видеоролик загружен!")
        elif selected == "Удалить аккаунт":
            if st.button("Удалить мой аккаунт"):
                conn = sqlite3.connect(data_base)
                c = conn.cursor()
                c.execute('DELETE FROM users WHERE id=?', (st.session_state['user_id'],))
                conn.commit()
                conn.close()
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
                    icons=["person-dash", "person-plus-fill", "person-dash-fill", "key-fill"])
                if admin_selected == "Удалить пользователя":
                    username_to_delete = st.text_input("Имя пользователя для удаления")
                    if st.button("Удалить пользователя"):
                        conn = sqlite3.connect(data_base)
                        c = conn.cursor()
                        c.execute('SELECT id FROM users WHERE username=?', (username_to_delete,))
                        user = c.fetchone()
                        if user:
                            c.execute('DELETE FROM users WHERE id=?', (user[0],))
                            conn.commit()
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
