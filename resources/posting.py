from flask import request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_jwt
from flask_restful import Resource
from config import Config
from mysql_connection import get_connection
from mysql.connector import Error

from datetime import datetime

import boto3

class FileUploadResource(Resource) :
    @jwt_required()
    def post(self) :
        file = request.files.get('photo')
        userId = get_jwt_identity()
        content = request.form.get('content')

        if file is None :
            return {"error" : '파일을 업로드 하세요'}, 400
        
        # 파일명을 회사의 파일명 정책에 맞게 변경한다.
        # 파일명은 유니크 해야 한다.
        current_time = datetime.now()
        new_file_name = current_time.isoformat().replace(':', '_') + '.jpg' 

        # 유저가 올린 파일의 이름을 새로운 파일 이름으로 변경한다.
        file.filename = new_file_name

        # S3에 업로드 하면 된다.
        # S3에 업로드 하기 위해서는 
        # AWS에서 제공하는 파이썬 라이브러리인 boto3 라이브러리를 이용해야 한다.
        # boto3 라이브러리는 AWS의 모든 서비스를 파이썬 코드로 작성할 수 있는 라이브러리다.
        # pip install boto3 로 설치!

        s3 = boto3.client('s3', 
                     aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                     aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)
        

        try :
            s3.upload_fileobj(file, 
                              Config.S3_BUCKET,
                              file.filename,
                              ExtraArgs = {'ACL' : 'public-read',
                                           'ContentType' : 'image/jpeg'})
        except Exception as e :
            print(e)

            return {'error' : str(e)}, 500
        
        label_list, label_confidence_list = self.detect_labels(new_file_name, Config.S3_BUCKET)


        try :
            connection = get_connection()
            query = '''insert into posting
                        (userId, imageUrl, content)
                        values
                        (%s, %s, %s);'''
            
            imgUrl = Config.S3_LOCATION + file.filename

            record = (userId, imgUrl, content)

            cursor = connection.cursor()
            cursor.execute(query, record)

            # 2. tag_name 테이블 처리를 해준다.
            # 리코그니션을 이용해서 받아온 label이 tag_name 테이블에 이미 존재하면 아이디만 가져오고
            # 그렇지 않으면 테이블에 인서트 한후에 그 아이디를 가져온다.

            postingId = cursor.lastrowid

            for tag in label_list :
                tag = tag.lower()
                query = '''select *
                            from tag_name
                            where name = %s;'''
                
                record = (tag, )

                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, record)
                result_list = cursor.fetchall()

                if len(result_list) != 0 :
                    tag_name_id = result_list[0]['id']

                else :
                    query = '''insert into tag_name
                                (name)
                                values
                                (%s);'''
                    
                    record = (tag,)
                    cursor = connection.cursor()
                    cursor.execute(query, record)

                    tag_name_id = cursor.lastrowid

                    
                    # 3. 위의 태그네임 아이디와 포스팅 아이디를 이용해서 tag 테이블에 데이터를 넣어준다.

                    # 트랜잭션 처리를 위해서 commit은 테이블 처리를 다 하고나서 마지막에 한번 해준다.
                    # 이렇게 해주면 중간에 다른 테이블에서 문제가 발생하면 모든 테이블이 롤백(원상복구)된다.
                    # 이 기능을 트랜잭션이라고 한다.
                query = '''insert into tag
                            (postingId, tagNameId)
                            values
                            (%s, %s);'''
                
                record = (postingId, tag_name_id)

                cursor = connection.cursor()
                cursor.execute(query, record)
                
            connection.commit()
            cursor.close()
            connection.close()

        
        except Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"fail" : str(e)}
        
        return {'result' : 'success',
                'imgeUrl' : Config.S3_LOCATION + file.filename,
                'labels' : label_list,
                'confidence' : label_confidence_list,
                'labelsCnt' : len(label_list)}, 200
    
    def detect_labels(self, photo, bucket):

        client = boto3.client('rekognition',
                              'ap-northeast-2',
                              aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)

        response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
        MaxLabels=5,
        # Uncomment to use image properties and filtration settings
        #Features=["GENERAL_LABELS", "IMAGE_PROPERTIES"],
        #Settings={"GeneralLabels": {"LabelInclusionFilters":["Cat"]},
        # "ImageProperties": {"MaxDominantColors":10}}
        )

        print('Detected labels for ' + photo)
        print()
        label_list = []
        label_confidence_list = []
        for label in response['Labels']:
            print("Label: " + label['Name'])
            print("Confidence: " + str(label['Confidence']))
            
            if label['Confidence'] >= 80 :
                label_list.append(label['Name'])
                label_confidence_list.append(label['Confidence'])

        return label_list, label_confidence_list
    
class FileDeleteResource(Resource) :
    @jwt_required()
    def delete(self, postingId) :
        userId = get_jwt_identity()

        try :
            connection = get_connection()
            query = '''delete from posting
                    where userId = %s and id = %s;'''
            
            record = (userId, postingId)

            cursor = connection.cursor()
            cursor.execute(query, record)

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"fail", str(e)}, 500
        
        return {"result" : "success"}, 200
    
class FileResource(Resource) :
    @jwt_required()
    def get(self) :
        userId = get_jwt_identity()

        try :
            connection = get_connection()
            query = '''select *
                    from posting
                    where userId = %s
                    order by createdAt desc;;'''
            
            record = (userId,)

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()

            print(result_list)

            i = 0
            for row in result_list :
                result_list[i]['createdAt'] = row['createdAt'].isoformat()
                result_list[i]['updatedAt'] = row['updatedAt'].isoformat()
                i = i+1

            print(result_list)

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"fail": str(e)}, 500
        
        return {"result" : "success",
                "items" : result_list}, 200
    
class FileUpdateResource(Resource) :
    @jwt_required()
    def put(self, postingId) :
        file = request.files.get('photo')
        content = request.form.get('content')
        userId = get_jwt_identity()

        if file is None :
            return {"error" : '파일을 업로드 하세요'}, 400
        
        # 파일명을 회사의 파일명 정책에 맞게 변경한다.
        # 파일명은 유니크 해야 한다.
        current_time = datetime.now()
        new_file_name = current_time.isoformat().replace(':', '_') + str(userId) +'.jpg'

        # 유저가 올린 파일의 이름을 새로운 파일 이름으로 변경한다.
        file.filename = new_file_name

        # S3에 업로드 하면 된다.
        # S3에 업로드 하기 위해서는 
        # AWS에서 제공하는 파이썬 라이브러리인 boto3 라이브러리를 이용해야 한다.
        # boto3 라이브러리는 AWS의 모든 서비스를 파이썬 코드로 작성할 수 있는 라이브러리다.
        # pip install boto3 로 설치!

        s3 = boto3.client('s3', 
                     aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                     aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)
        

        try :
            s3.upload_fileobj(file, 
                              Config.S3_BUCKET,
                              file.filename,
                              ExtraArgs = {'ACL' : 'public-read',
                                           'ContentType' : 'image/jpeg'})
        except Exception as e :
            print(e)

            return {'error' : str(e)}, 500
        
        try :
            connection = get_connection()
            query = '''update posting
                    set imageUrl= %s, content= %s
                    where userId= %s and id = %s;'''
            
            imgUrl = Config.S3_LOCATION + file.filename
            
            record = (imgUrl, content, userId, postingId)

            cursor = connection.cursor()
            cursor.execute(query, record)

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"fail": str(e)}, 500
        
        return {"result": "success"}, 200