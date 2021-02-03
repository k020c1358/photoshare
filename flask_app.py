from flask import Flask, redirect, request
from flask import render_template, send_file
import photo_db, sns_user as user # 自作モジュールを取り込む
import math #ページング機能のために追加

#1ページに表示するデータ数
limit=5

#from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'dpwvgAxaY2iWHMb2'

#キャシューを５秒と更新 ctrl+F5:強制的に更新
#app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=5)

# ログイン処理を実現する --- (*1)
@app.route('/login')
def login():
    return render_template('login_form.html')

@app.route('/login/try', methods=['POST'])
def login_try():
    ok = user.try_login(request.form)
    if not ok: return msg('ログイン失敗')
    return redirect('/')

@app.route('/logout')
def logout():
    user.try_logout()
    return msg('ログアウトしました')


# メイン画面 - メンバーの最新写真を全部表示する --- (*2)
#ページング機能を追加
@app.route('/')
@user.login_required
def index():
    now_user= user.get_id()
    list_friend= photo_db.get_friend_list()
    id=user.get_id()
    
    ok_list=[] #表示許可がある非公開写真の所有者のidをここに追加
    for i in list_friend:
      if now_user in i["friend"]:
        ok_list.append(i["user_id"])

    #ここからはページング機能
    #ページの番号を得る
    page_s = request.args.get('page','0')
    page = int(page_s)
    #表示するデータの先頭を計算
    index = page*limit
    
    photos=photo_db.get_files(index)
    count = 0 #写真の番号
    count_list = [] #表示許可のない写真の番号を追加する
    
    for i in photos:
      if i["public"] and i["user_id"] != id and i["user_id"] not in ok_list:
        count_list.append(count)
      count += 1
    
    # 表示できるすべてのファイルの数を得る
    amount=photo_db.get_amount() - len(count_list)
    #表示許可のない写真の情報を削除
    for v in count_list: del photos[v]


    #ページャーを作る
    s=''
    s += make_pager(page, amount, limit)
    
    return render_template('index.html', 
                id=id,photos=photos,s=s)



# アルバムに入っている画像一覧を表示 --- (*3)
@app.route('/album/<album_id>')
@user.login_required
def album_show(album_id):
    album = photo_db.get_album(album_id)
    return render_template('album.html',
            album=album,
            photos=photo_db.get_album_files(album_id))

# ユーザーがアップした画像の一覧を表示 --- (*4)
@app.route('/user/<user_id>')
@user.login_required
def user_page(user_id):
    return render_template('user.html', id=user_id,
            photos=photo_db.get_user_files(user_id))

# ユーザーのhomepageを表示 
@app.route('/myhomepage')
@user.login_required
def myhomepage():
    albums = photo_db.get_albums(user.get_id())
    user_msg = photo_db.get_user(user.get_id())
    

    return render_template('myhomepage.html', albums=albums,user_name=user.get_id(),user_msg=user_msg)

#友達追加
@app.route('/myhomepage/add',methods=['POST'])
@user.login_required
def add():
    user_msg = photo_db.get_user(user.get_id())
    if user_msg[0]["friend"] == "":
      photo_db.friend_add(user.get_id(), request.form.get("add_friend"))
      
    else:
      photo_db.friend_add(user.get_id(), ","+ request.form.get("add_friend"))
      
    return redirect('/myhomepage')

#友達削除
@app.route('/myhomepage/delete',methods=['POST'])
@user.login_required
def delete():
    user_msg = photo_db.get_user(user.get_id())
    friend = user_msg[0]["friend"]
    friend = friend.split(",")
    del_f = request.form.get("delete_friend")
    
    if friend == [] :
      return msg('友達がない')
    if friend.count(del_f) == 0:
      return msg(f'友達{del_f}さんがいない')
      
    else:
      friend.remove(del_f)
      friend = ",".join(friend)

      photo_db.friend_delete(user.get_id(),friend)

    return redirect('/myhomepage')

    
#ユーザーのalbumを表示 
@app.route('/myhomepage/albums/<album_id>')
@user.login_required
def my_album(album_id):
    album = photo_db.get_album(album_id)
    albums = photo_db.get_albums(user.get_id())

    return render_template('myalbum.html', album=album,photos=photo_db.get_album_files(album_id),albums=albums)

#写真公開かどうかをチェンジ
@app.route('/myhomepage/albums/public_change/<album_id>/<file_id>')
@user.login_required
def public_change(album_id,file_id):
    
    photo_db.public_c(file_id)

    return redirect('/myhomepage/albums/'+ album_id)


#写真を削除する
@app.route('/myhomepage/albums/photo_delete/<album_id>/<file_id>')
@user.login_required
def photo_delete(album_id,file_id):
    
    photo_db.delete_photo(file_id)

    return redirect('/myhomepage/albums/'+ album_id)


#アルバムを変更する
@app.route('/myhomepage/albums/album_change/<file_id>',methods=['GET','POST'])
@user.login_required
def album_change(file_id):
    album_id = request.form.get("album")
    photo_db.change_album(album_id,file_id)

    return redirect('/myhomepage/albums/'+ album_id)


# 画像ファイルのアップロードに関する機能を実現する --- (*5)
@app.route('/upload')
@user.login_required
def upload():
    return render_template('upload_form.html',
            albums=photo_db.get_albums(user.get_id()))

@app.route('/upload/try', methods=['POST'])
@user.login_required
def upload_try():
    # アップロードされたファイルを確認 --- (*6)
    upfile = request.files.get('upfile', None)
    if upfile is None: return msg('アップロード失敗')
    if upfile.filename == '': return msg('アップロード失敗')
    # どのアルバムに所属させるかをフォームから値を得る --- (*7)
    album_id = int(request.form.get('album', '0'))
    # ファイルの保存とデータベースへの登録を行う --- (*8)
    photo_id = photo_db.save_file(user.get_id(), upfile, album_id)
    if photo_id == 0: return msg('データベースのエラー')
    return redirect('/user/' + str(user.get_id()))

# アルバムの作成機能 ---  (*9)
@app.route('/album/new')
@user.login_required
def album_new():
    return render_template('album_new_form.html')

@app.route('/album/new/try')
@user.login_required
def album_new_try():
    id = photo_db.album_new(user.get_id(), request.args)
    if id == 0: return msg('新規アルバム作成に失敗')
    return redirect('/upload')


# 画像ファイルを送信する機能 --- (*10)
@app.route('/photo/<file_id>')
@user.login_required
def photo(file_id):
 
    ptype = request.args.get('t', '')
    photo = photo_db.get_file(file_id, ptype)
    if photo is None: return msg('ファイルがありません')
    
    return send_file(photo['path'])
    


def msg(s):
    return render_template('msg.html', msg=s)

# CSSなど静的ファイルの後ろにバージョンを自動追記
@app.context_processor
def add_staticfile():
    return dict(staticfile=staticfile_cp)
def staticfile_cp(fname):
    import os
    path = os.path.join(app.root_path, 'static', fname)
    mtime =  str(int(os.stat(path).st_mtime))
    return '/static/' + fname + '?v=' + str(mtime)



#ページング機能に使う関数

def make_pager(page, total, per_page):
  #ページ数を計算
  page_count = math.ceil(total / per_page)
  s = '<div style="">'#
  #前へボタン
  prev_link = '?page=' + str(page - 1)
  if page <= 0 :prev_link = '#'
  s += make_button(prev_link, '←前へ')
  #ページ番号
  s += '{0}/{1}'.format(page+1, page_count)
  #次へボタン
  next_link = '?page=' + str(page + 1)
  if page >= page_count - 1: next_link ='#'
  s += make_button(next_link, '次へ→')
  s += '</div>'
  
  return s



def make_button(href, label):
  klass = 'pure-button'
  if href == '#': klass += ' pure-button-disabled'
  return '''
  <a href="{0}" class="{1}">{2}</a>
  '''.format(href, klass, label)






if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

