from flask import request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_jwt
from flask_restful import Resource
from mysql_connection import get_connection
from mysql.connector import Error

class FollowResource(Resource) :
    @jwt_required()
    def post(self, followeeId) :
        userId = get_jwt_identity()
        try :
            connection = get_connection()
            query = '''insert into follow
                        (followerId, followeeId)
                        values
                        (%s, %s);'''
            
            record = (userId, followeeId)

            cursor = connection.cursor()
            cursor.execute(query, record)

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"fail" : str(e)}, 500
        
        return {"result" : "success"}, 200
    
    @jwt_required()
    def delete(self, followeeId) :
        followerId = get_jwt_identity()

        try :
            connection = get_connection()
            query = '''delete from follow
                    where followerId = %s and followeeId = %s;'''
            
            record = (followerId, followeeId)

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

class FolloweePostResource(Resource) :
    @jwt_required()
    def get(self) :
        userId = get_jwt_identity()
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        try :
            connection = get_connection()
            query = '''select p.id as postId, p.imageUrl, p.content, 
                                u.id as userId, u.email, p.createdAt, 
                                count(l.id) as likeCnt, if(l.id is null, 0, 1) as isLike
                        from posting as p
                        left join follow as f
                        on f.followeeId = p.userId
                        join user as u
                        on u.id = p.userId
                        left join `like` as l
                        on p.id = l.postingId
                        left join `like` as l2
                        on p.id = l2.postingId and l2.likerId = %s
                        where f.followerId = %s
                        group by p.id
                        order by p.createdAt desc
                        limit ''' + offset + ''', ''' + limit +''';'''
            
            record = (userId, userId)

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

            i = 0
            for row in result_list :
                result_list[i]['createdAt'] = row['createdAt'].isoformat()
                i = i+1

            cursor.close()
            connection.close()

        except Error as e : 
            print(e)
            cursor.close()
            connection.close()

            return {"fail" : str(e)}, 500
        
        return {"result" : "success",
                "items" : result_list,
                "count" : len(result_list)}, 200
    
class FolloweePostDetailResource(Resource) :
    @jwt_required()
    def get(self, postingId) :
        userId = get_jwt_identity()

        try :
            connection = get_connection()
            query = '''select p.id as postId, p.imageUrl, p.content,
                                u.id as userId, u.email, p.createdAt, 
                                count(l.id) as likeCnt, if(l2.id is null, 0, 1) as isLike
                        from posting as p
                        join user as u
                        on p.userId = u.id
                        left join `like` as l
                        on p.id = l.postingId
                        left join `like` as l2
                        on p.id = l2.postingId and l2.likerId = %s
                        where p.id = %s;'''
            
            record = (userId, postingId)

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

            if result_list[0]['postId'] is None :
                return {"fail" : "데이터가 없습니다."}, 400
            
            # todo : 데이터 변수 작업

            query = '''select concat('#', tn.name) as tag
                        from tag_name as tn
                        join tag as t
                        on tn.id = t.tagNameId
                        where t.postingId = %s;'''
            
            record = (postingId,)

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            tag_list = cursor.fetchall()

            tag = []
            for tag_dic in tag_list :
                tag.append(tag_dic['tag'])


            i = 0
            for row in result_list :
                result_list[i]['createdAt'] = row['createdAt'].isoformat()
                i = i+1

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"fail" : str(e)}, 500
        
        return {"result" : "success",
                "post" : result_list,
                "tag" : tag}, 200