from flask import request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_jwt
from flask_restful import Resource
from mysql_connection import get_connection
from mysql.connector import Error

class LikeResource(Resource) :
    @jwt_required()
    def post(self, postingId):

        userId = get_jwt_identity()

        try :
            connection = get_connection()
            query = '''insert into `like`
                    (likerId, postingId)
                    values
                    (%s, %s);'''
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
            return {'error' : str(e)}, 500

        return {'result' : 'success'}
    
    @jwt_required()
    def delete(self, postingId):
        userId = get_jwt_identity()

        try :
            connection = get_connection()
            query = '''delete from `like` 
                    where likerId = %s and postingId = %s;'''
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
            return {'error' : str(e)}, 500

        return {'result' : 'success'}