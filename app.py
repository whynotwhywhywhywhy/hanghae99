from pymongo import MongoClient
import jwt
import datetime
import hashlib
import certifi
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'


ca = certifi.where()
client = MongoClient('mongodb+srv://test:sparta@cluster0.l0pgj.mongodb.net/?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.dbsparta

# first page 진입
@app.route('/')
def intro():
    return render_template('firstpage.html')
# -----------------------------------------------------------------------------------------
# /main
# 토큰이 남아있는지 확인하여 토큰이 있으면 메인페이지로 아닐경우 로그인페이지로 보내준다.
@app.route('/main')
def main():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        words = list(db.mini.find({}, {"_id": False}))
        return render_template('main.html', user_info=user_info, words=words)
        # return render_template('main.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    # 위의 함수를 통해 rediret(url_for("(함수 명)") 함수명에 해당되는 파라미터로 보냄
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
    # 위의 함수를 통해 rediret(url_for("(함수 명)") 함수명에 해당되는 파라미터로 보냄

@app.route("/mini", methods=["POST"])
def mini_post():
    gu_receive = request.form['gu_give']
    dong_receive = request.form['dong_give']
    chung_receive = request.form['chung_give']
    ann_receive = request.form['ann_give']
    gyo_receive = request.form['gyo_give']
    pyun_receive = request.form['pyun_give']

    doc = {
        'gu': gu_receive,
        'dong': dong_receive,
        'chung': chung_receive,
        'ann': ann_receive,
        'gyo': gyo_receive,
        'pyun': pyun_receive,
    }
    db.mini.insert_one(doc)

    return jsonify({'msg': '저장 완료!'})

@app.route("/check", methods=["POST"])
def check_post():
    id_receive = request.form['id_give']
    user = db.users.find_one({'id': id_receive})
    if user is not None:
        return jsonify({'msg': 0})
    else:
        return jsonify({'msg': 1})


@app.route("/boxcheck", methods=["POST"])
def boxcheck():
    checkval_receive = request.form['check_val']
    result = list(db.mini.find({'gu': {"$regex": checkval_receive}}, {'_id': False}))
    if checkval_receive == "all":
        mini_list = list(db.mini.find({}, {'_id': False}))
        return jsonify({'msg': mini_list})
    else:
        return jsonify({'msg': result})


@app.route("/mini", methods=["GET"])
def mini_get():
    mini_list = list(db.mini.find({}, {'_id': False}))
    return jsonify({'mini': mini_list})



# # 닉네임 데이터 얻기
# @app.route('/main')
# def comment():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         user_info = db.user.find_one({"username": payload["id"]})
#         return render_template('main.html', user_info=user_info)
#     except jwt.ExpiredSignatureError:
#         return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
#     except jwt.exceptions.DecodeError:
#         return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

# -----------------------------------------------------------------------------------------
# /login 으로 이동
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

# @app.route('/user')
# def user():
#     # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False
#         # user_info = db.users.find_one({"username": username}, {"_id": False})
#         return render_template('user.html', user_info=user_info, status=status)
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))

@app.route('/user')
def user():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('user.html', user_info=user_info)
        # return render_template('main.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    # 위의 함수를 통해 rediret(url_for("(함수 명)") 함수명에 해당되는 파라미터로 보냄
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
    # 위의 함수를 통해 rediret(url_for("(함수 명)") 함수명에 해당되는 파라미터로 보냄


# 로그인 api이며 입력한 아이디와 암호화된 비밀번호를 통해
# find하여 none이 아니면 유저아이디와 로그인 시간을 가지고 있는 토큰을 쿠키에 넣는다
# /login  데이터 저장
@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 1)  # 로그인 1시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        # hashlib.sha256(명.encode('utf-8')).hexdigest() 암호화 시킨다. exp는 지속 시간을 나타낸다

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# 로그인 비밀번호 닉네임을 확인하여 데이터 베이스 추가
@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "nickname": nickname_receive                                # 닉네임
        # "profile_pic": "",                                          # 프로필 사진 파일 이름
        # "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        # "profile_info": ""                                          # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

# 아이디를 확인하여 데이터베이스 추가
# bool()은 true/false로 변환한다
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

# 닉네임을 확인하여 데이터베이스 추가
# bool()은 true/false로 변환한다
@app.route('/sign_up/check_nickname_dup', methods=['POST'])
def check_nickname_dup():
    nickname_receive = request.form['nickname_give']
    exists = bool(db.users.find_one({"nickname": nickname_receive}))
    return jsonify({'result': 'success', 'exists': exists})
#-----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------

# # mian.html로 이동
# @app.route('/main')
# def info():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         hotel_list = list(db.hotel.find({}, {'_id': False}))
#         reviewer = payload["user_id"]
#         return render_template('main.html', rows=hotel_list, user_id=reviewer)
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("login"))

# 동네정보 데이터베이스로 전송


# posting 으로 이동
@app.route('/posting')
def posting():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('posting.html', user_info=user_info)

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    # 위의 함수를 통해 rediret(url_for("(함수 명)") 함수명에 해당되는 파라미터로 보냄
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
    # 위의 함수를 통해 rediret(url_for("(함수 명)") 함수명에 해당되는 파라미터로 보냄


# posting 데이터 저장
@app.route("/posting", methods=["POST"])
def web_mars_post():
    gu_receive = request.form['gu_give']
    dong_receive = request.form['dong_give']
    clean_receive = request.form['clean_give']
    safe_receive = request.form['safe_give']
    trans_receive = request.form['trans_give']
    store_receive = request.form['store_give']

    doc = {
        'gu': gu_receive,
        'dong': dong_receive,
        'clean': clean_receive,
        'safe': safe_receive,
        'trans': trans_receive,
        'store': store_receive,
    }

    db.database.insert_one(doc)

    return jsonify({'msg': '입력 완료!'})
#-----------------------------------------------------------------------------------------

# # user 로 이동
# @app.route('/user')
# def user1():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         user_info = db.users.find_one({"username": payload["id"]})
#         return render_template('user.html', user_info=user_info)
#         # return render_template('main.html')
#     except jwt.ExpiredSignatureError:
#         return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
#     # 위의 함수를 통해 rediret(url_for("(함수 명)") 함수명에 해당되는 파라미터로 보냄
#     except jwt.exceptions.DecodeError:
#         return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
#     # 위의 함수를 통해 rediret(url_for("(함수 명)") 함수명에 해당되는 파라미터로 보냄

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
#
@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username = payload["id"]
        name_receive = request.form["name_give"]
        about_receive = request.form["about_give"]
        new_doc = {
            "profile_name": name_receive,
            "profile_info": about_receive
        }
        if 'file_give' in request.files:
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/{username}.{extension}"
            file.save("./static/"+file_path)
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path
        db.users.update_one({'username': payload['id']}, {'$set':new_doc})
        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))
#
# @app.route('/posting', methods=['POST'])
# def posting():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         user_info = db.users.find_one({"username": payload["id"]})
#         comment_receive = request.form["comment_give"]
#         date_receive = request.form["date_give"]
#         doc = {
#             "username": user_info["username"],
#             "profile_name": user_info["profile_name"],
#             "profile_pic_real": user_info["profile_pic_real"],
#             "comment": comment_receive,
#             "date": date_receive
#         }
#         db.posts.insert_one(doc)
#         return jsonify({"result": "success", 'msg': '포스팅 성공'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))
#
#
# @app.route("/get_posts", methods=['GET'])
# def get_posts():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 포스팅 목록 받아오기
#         return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다."})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))
#
#
# @app.route('/update_like', methods=['POST'])
# def update_like():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 좋아요 수 변경
#         return jsonify({"result": "success", 'msg': 'updated'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)