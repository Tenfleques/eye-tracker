# %%
import hashlib
import sqlite3


def establish_database(database, force=False):
    import sqlite3
    import os.path
    if force or not os.path.exists(database):
        create_Stimulus = f'''
                                create table Stimulus
                                    (ID_v integer PRIMARY KEY AUTOINCREMENT,
                                    name text,
                                    trajectory blob,
                                    Video blob,
                                    meta_v blob,
                                    hash integer
                                    )                                   


                    '''
        drop_Stimulus = f'''
                        drop table if exists Stimulus
                        '''

        create_users = '''
                                        create table Users
                                            (id integer primary key autoincrement,
                                            surname text,
                                            name text,
                                            patronymic text,
                                            age integer,
                                            sex text
                                            )
                        '''
        drop_users = '''drop table if exists users'''

        drop_Video_user = '''drop table if exists Video_user'''
        create_Video_user = '''

                                        create table Video_user
                                            ( video_ID integer,
                                             [user_ID] integer,
                                             user_data text
                                            )
                                            '''
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute(drop_Stimulus)
        cursor.execute(drop_users)
        cursor.execute(drop_Video_user)
        cursor.execute(create_Stimulus)
        cursor.execute(create_users)
        cursor.execute(create_Video_user)
        conn.commit()
        conn.close()


# %%
class Video_loader:
    def __init__(self, database='Video_loader.db', force = False):

        self.database = database
        establish_database(database, force)

    # videos is a list of list with videos and its paths
    # example : videos = [[video1_path, meta1_path], [video2_path, meta_2path]]
    def upload_video(self, video, table='Stimulus', force=False):
        import sqlite3
        import hashlib
        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()
        import time
        name = video[0]
        video_path = video[1]
        trajectory_path = video[2]
        meta_path = video[3]

        # compute hash
        with open(video_path, 'br') as fin:
            video_file = fin.read()
            h = hashlib.sha3_256()
            h.update(video_file)
            hash_video = h.hexdigest()
        with open(meta_path, 'r') as fin:
            meta_file = fin.read()

        # find if this video already exists
        SQLCommand = f'''
                        select id_v, name, hash from {table}
                            where hash = '{hash_video}'
                        '''
        cursor.execute(SQLCommand)
        data = cursor.fetchone()
        if not data or force:
            SQLCommand = f'''
                            INSERT INTO {table} ( name, trajectory, Video, meta_v, hash)
                                Values (?, ?, ?, ?, ?)
                          '''
            with open(trajectory_path, 'r') as fin:
                trajectory_file = fin.read()
            # technical part, need for insertion is executed properly

            retry_flag = True
            retry_count = 0
            while retry_flag and retry_count < 5:
                try:
                    cursor.execute(SQLCommand, (name, trajectory_file, video_file, meta_file, hash_video))
                    retry_flag = False
                except Exception as e:
                    print(e)
                    print("Retry after 1 sec")
                    retry_count = retry_count + 1
                    time.sleep(1)
            if retry_flag == True:
                return -1
            # print(f"sample {video_path} have been inserted")
            connection.commit()
            connection.close()
            return 0
        # if yes

        connection.close()
        return -2

    def download_video(self, name, path_where_download):
        import sqlite3

        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()
        SQLCommand = (f"SELECT Video FROM Stimulus where name = '{name}'")
        cursor.execute(SQLCommand)
        data = cursor.fetchone()[0]
        data = bytes(data)

        with open(path_where_download, 'wb') as video:
            video.write(data)
        connection.close()


# %%

# %%
class User:

    def __init__(self, surname, name, patronymic, age, sex):
        self.name = name
        self.surname = surname
        self.patronymic = patronymic
        self.age = age
        self.sex = sex

    def upload_to_database(self, database, table='Users'):
        establish_database(database)
        import sqlite3
        connection = sqlite3.connect(f"{database}.db")
        cursor = connection.cursor()
        SQLCommand = \
            f'''
                        Select id from {table}
                            where 
                                surname = '{self.surname}' and 
                                name = '{self.name}' and
                                patronymic ='{self.patronymic}' and
                                age = {self.age} and
                                sex = '{self.sex}'
                    '''
        cursor.execute(SQLCommand)
        data = cursor.fetchone()
        if data:
            return data[0]
        SQLCommand = \
            f'''
                    insert into {table} (surname,
                                            name,
                                            patronymic,
                                            age ,
                                            sex ) values (?, ?, ?, ?, ?)
                '''
        cursor.execute(SQLCommand, (self.surname, self.name, self.patronymic, self.age, self.sex))
        connection.commit()
        connection.close()
        return -1


# loader = Video_loader(force=False)
# for i in range(1,4):
#     video = [f'sample{i}', rf"C:\Users\Admin\Documents\kivy\Resources\Videos\sample{i}.mp4",r'C:\Users\Admin\Documents\job\trajectory.txt', rf'C:\Users\Admin\Documents\job\test{i}.ini']
#     print(loader.upload_video(video))

connection = sqlite3.connect('Video_loader.db')
cursor = connection.cursor()
cursor.execute("select name from Stimulus where name like '%1%'")
print(cursor.fetchall())
connection.close()