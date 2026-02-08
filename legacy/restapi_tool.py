from flask import Flask
from flask_restx import Api, Resource
import requests
from requests.structures import CaseInsensitiveDict

class RestApiServer:
    """REST API 서버"""
    
    def __init__(self, host='0.0.0.0', port=80, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        
        # Flask 객체 선언 및 파라미터 어플리케이션 패키지의 이름 입력
        self.app = Flask(__name__)
        
        # Flask 객체에 Api 객체 등록
        self.api = Api(self.app)

    def start(self):
        self.app.run(host = self.host,
                     port = self.port,
                     debug = self.debug)
    
    class Test(Resource):
        def get(self):
            return('hello: world')
        
    def add_route(self, path):
        self.app.add_url_rule(path, 'test', self.Test)
    
class RestApiClient:
    """REST API 클라이언트"""

    def __init__(self, url, proxy=None):
        self.url = url
        self.header = CaseInsensitiveDict()
        self.proxy  = proxy

    def restApi(self, method, params=None, headers=None, data=None):
        response = requests.request(
            method = method,
            url = self.url,
            proxies = self.proxy,
            params = params,
            headers = headers,
            data = data
        )
        return response


if __name__ == '__main__':
    
    ras_o = RestApiServer(port=8123)
    ras_o.add_route('/hi')
    ras_o.start()
    

    # url = "https://reqbin.com/echo"
    # headers = {}
    # headers["Content-Type"] = "application/json"
    # data = '{"data":"Hello Beeceptor"}'

    # api = RestApiClient(url)
    # resp = api.restApi("GET")
    # # GET R / POST C / PUT U / DELETE D

    # print(resp)
    # print(type(resp))