# import serverless_wsgi

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api
from config import Config
from resources.follow import FollowResource, FolloweePostResource
from resources.likes import LikeResource
from resources.posting import FileDeleteResource, FileResource, FileUpdateResource, FileUploadResource
from resources.user import UserLoginResource, UserLogoutResource, UserRegisterResource

# 로그아웃 관련된 임포트문
from resources.user import jwt_blocklist

app = Flask(__name__)

# 환경변수 셋팅
app.config.from_object(Config)
# JWT 매니저 초기화
jwt=JWTManager(app)

# 로그아웃된 토큰으로 요청하는 경우 실행되지 않도록 처리하는 코드
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload) :
    jti = jwt_payload['jti']
    return jti in jwt_blocklist

api = Api(app)

# 경로와 리소스를 연결한다.
api.add_resource(UserRegisterResource,'/user/register') # 회원가입
api.add_resource(UserLoginResource,'/user/login')    # 로그인
api.add_resource(UserLogoutResource,'/user/logout')   # 로그아웃
api.add_resource(FileUploadResource,'/posting')     # 포스팅 작성
api.add_resource(FileDeleteResource,'/posting/<int:postingId>')     # 포스팅 삭제
api.add_resource(FileResource,'/posting')     # 내 포스팅 가져오기
api.add_resource(FileUpdateResource,'/posting/<int:postingId>')     # 포스팅 수정
api.add_resource(FollowResource, '/follow/<int:followeeId>')  # 친구 맺기, 끊기
api.add_resource(FolloweePostResource,'/follow/posting')     # 친구 포스팅 가져오기
api.add_resource(LikeResource, '/like/posting/<int:postingId>')     # 좋아요

# def handler(event, context) :
#     return serverless_wsgi.handle_request(app, event, context)

if __name__ == '__main__' :
    app.run()