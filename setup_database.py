from photo_sqlite import exec

#ユーザー生成の時にidを付ける
exec('''
/* ユーザー情報 */
CREATE TABLE users (
  login_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     TEXT,
  friend      TEXT DEFAULT('')
)

''')

exec('''
/* ユーザー情報 */

INSERT INTO users 
  (user_id)
VALUES
("taro"),("jiro"),("sabu"),("siro"),("goro");

''')



exec('''
/* ファイル情報 */
CREATE TABLE files (
  file_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     TEXT,
  filename    TEXT,
  album_id    INTEGER DEFAULT 0, /* なし */
  created_at  TIMESTAMP DEFAULT (DATETIME('now', 'localtime')),
  public      INTEGER DEFAULT 0
  
)
''')

exec('''
/* アルバム情報 */
CREATE TABLE albums (
  album_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT,
  user_id     TEXT,
  created_at  TIMESTAMP DEFAULT (DATETIME('now', 'localtime'))
  
)
''')


print('ok')

