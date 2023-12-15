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
    
class FolloweePostResource(Resource) :
    @jwt_required()
    def get(self) :
        userId = get_jwt_identity()

        try :
            connection = get_connection()
            query = '''select p.userId, p.imageUrl, p.content, p.createdAt, p.updatedAt
                        from follow as f
                        join posting as p
                        on f.followeeId = p.userId and followerid = %s
                        order by p.updatedAt desc;'''
            
            record = (userId, )

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

            i = 0
            for row in result_list :
                result_list[i]['createdAt'] = row['createdAt'].isoformat()
                result_list[i]['updatedAt'] = row['updatedAt'].isoformat()
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