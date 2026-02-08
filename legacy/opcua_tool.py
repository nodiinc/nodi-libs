import asyncio
from threading import Thread, Event
from asyncua import Server, Client, Node, ua

URL_DEFAULT = 'http://oowlilabs.com/'
PATH_DEFAULT = 'nodi/'
SERVER_DEFAULT = 'nodiOpcUaSvr'

class OpcuaServer:
    """OPC UA 서버"""
    
    def __init__(self,
                 host: str = '0.0.0.0',
                 port: int = 4840,
                 path: str = PATH_DEFAULT):
        self.server = Server()
        self.url = f'opc.tcp://{host}:{port}/{path}'
        self.server.set_endpoint(self.url)
    
    async def start_server_fore(self):
        """서버 시작 포어그라운드"""
        await self.server.init()
        await self.server.start()
        self.is_running = Event()
        self.is_running.set()
        while self.is_running.is_set():
            await asyncio.sleep(1)
    
    async def start_server_back(self):
        """서버 시작 백그라운드"""
        def _start_server_back():
            asyncio.run(self.start_server_fore())
        loop_thread = Thread(target=_start_server_back)
        loop_thread.daemon = True
        loop_thread.start()
    
    async def wait_server_active(self):
        """서버 활성화까지 대기"""
        while True:
            try:
                if await self.get_ns_ls():
                    break
            except:
                pass
            await asyncio.sleep(0.1)
    
    async def stop_server(self):
        """서버 중지"""
        await self.server.stop()
        self.is_running.clear()
        
    def set_server_name(self, name=SERVER_DEFAULT):
        """서버 이름 설정"""
        self.server.set_server_name(name)
        
    def set_secu_policy(self, policy_list):
        """보안정책 설정 (0~8)"""
        policy_md = {
            0: ua.SecurityPolicyType.NoSecurity,
            1: ua.SecurityPolicyType.Basic128Rsa15_Sign,
            2: ua.SecurityPolicyType.Basic128Rsa15_SignAndEncrypt,
            3: ua.SecurityPolicyType.Basic256_Sign,
            4: ua.SecurityPolicyType.Basic256_SignAndEncrypt,
            5: ua.SecurityPolicyType.Basic256Sha256_Sign,
            6: ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            7: ua.SecurityPolicyType.Aes128Sha256RsaOaep_Sign,
            8: ua.SecurityPolicyType.Aes128Sha256RsaOaep_SignAndEncrypt
        }
        permit_md = {
            ...
        }
        self.server.set_security_policy([policy_md[i] for i in policy_list])
        
    async def load_cert(self, certificate_path):
        """인증서 불러오기"""
        await self.server.load_certificate(certificate_path)
        
    async def load_pkey(self, publickey_path):
        """개인키 불러오기"""
        await self.server.load_private_key(publickey_path)
    
    async def add_ns(self, uri=URL_DEFAULT):
        """네임스페이스 등록"""
        namespace_index = await self.server.register_namespace(uri)
        return namespace_index
    
    async def get_ns_ls(self):
        """네임스페이스 목록 받기"""
        namespace_list = await self.server.get_namespace_array()
        return namespace_list
    
    async def get_ns_idx(self, uri=URL_DEFAULT):
        """네임스페이스 목록 받기"""
        namespace_index = await self.server.get_namespace_index(uri)
        return namespace_index
        
    def get_node_root(self):
        """루트 노드 받기 (Root)"""
        root_node = self.server.get_root_node()
        return root_node
    
    def get_node_objects(self):
        """오브젝트 노드 받기 (Root > Objects)"""
        objects_node = self.server.get_objects_node()
        return objects_node
    
    def get_node_types(self):
        """타입 노드 받기 (Root > Types)"""
        types_node = self.server.nodes.types
        return types_node

    def get_node_server(self):
        """서버 노드 받기 (Root > Objects > Server)"""
        server_node = self.server.nodes.server
        return server_node
    
    def get_node_any(self, nodeid):
        """아무 노드 받기"""
        any_node = self.server.get_node(nodeid)
        return any_node
    
    async def get_node_var(self, node_parent):
        """변수 노드 받기"""
        variable_node_list = await Node.get_variables(node_parent)
        return variable_node_list
    
    async def add_node_folder(self, nodeid, bname, node_parent=None):
        """폴더 추가"""
        if node_parent:
            folder_node = await Node.add_folder(node_parent, nodeid, bname)
        else:
            folder_node = await self.get_node_objects().add_folder(nodeid, bname)
        return folder_node
        
    async def add_node_object(self, nodeid, bname, node_parent=None):
        """오브젝트 추가"""
        if node_parent:
            object_node = await Node.add_object(node_parent, nodeid, bname)
        else:
            object_node = await self.get_node_objects().add_object(nodeid, bname)
        return object_node
        
    async def add_node_var(self, nodeid, bname, node_parent, value, writeable=None):
        """변수 추가"""
        if node_parent:
            variable_node = await Node.add_variable(node_parent, nodeid, bname, value)
        else:
            variable_node = await self.get_node_objects().add_variable(nodeid, bname, value)
        if writeable:
            await variable_node.set_writable()
        else:
            await variable_node.set_read_only()
        return variable_node
    
    async def read_node_var(self, nodeid):
        """변수 읽기"""
        value = await Node.read_value(nodeid)
        return value
        
    async def write_node_var(self, nodeid, value, variant_type=None):
        """변수 쓰기"""
        await Node.write_value(nodeid, value, variant_type)
        
    async def read_attr(self, nodeid, attribute_id):
        """속성 읽기"""
        attribute = Node.read_attribute(nodeid, attribute_id)
        return attribute
    
    async def write_attr(self, nodeid, attribute_id, value):
        """속성 쓰기"""
        Node.write_attribute(nodeid, attribute_id, value)
    
    async def add_method(self, nodeid, qname, func, input, output):
        """메서드 추가"""
        self.server.nodes.objects.add_method(nodeid, [nodeid, qname, func, input, output])
     
class OpcuaClient:
    """OPC UA 클라이언트"""
           
    def __init__(self, host='0.0.0.0', port=4840, path=PATH_DEFAULT, timeout=5.0):
        self.url = f'opc.tcp://{host}:{port}/{path}'
        self.timeout = float(timeout)
        self.client = Client(self.url, self.timeout)
        
    async def connect_client(self):
        """클라이언트 연결"""
        await self.client.connect()
        
    async def disconnect_client(self):
        """클라이언트 해제"""
        await self.client.disconnect()
    
    def set_auth_user(self, username, password):
        """사용자 인증 설정"""
        self.client.set_user(username)
        self.client.set_password(password)
    
    async def set_auth_cert(self, cert_path, pkey_path):
        """인증서 인증 설정"""
        await self.client.load_client_certificate(cert_path)
        await self.client.load_private_key(pkey_path)
    
    async def read_ns_ls(self):
        """네임스페이스 목록 읽기"""
        ns_ls = await self.client.get_namespace_array()
        return ns_ls
        
    async def read_ns_idx(self, uri=URL_DEFAULT):
        """네임스페이스 인덱스 읽기"""
        ns_idx = await self.client.get_namespace_index(uri)
        return ns_idx
    
    async def get_node_any(self, nodeid):
        """아무 노드 받기"""
        node = self.client.get_node(nodeid)
        return node

    async def read_node_var_one(self, node):
        """변수 한 개 읽기"""
        value = await node.read_value()
        return value

    async def read_node_var_many(self, node_list):
        """변수 여러 개 읽기"""
        value_list = await self.client.read_values(node_list)
        return value_list

    async def write_node_var_one(self, node, value):
        """변수 쓰기"""
        await node.write_value(value)

    async def write_node_var_many(self, node_list, value_list):
        """변수 쓰기"""
        await self.client.write_values(node_list, value_list)
    
    async def sub_node_many(self, nodeid_list, interval,
                            datachg_call=None, event_call=None, statchg_call=None):
        """노드 구독"""  # TODO: This is incomplete
        
        class SubHandler:
            
            def datachange_notification(self, node, value, data):
                if datachg_call: datachg_call()
                
            def event_notification(self, event):
                if event_call: event_call()

            def status_change_notification(self, status):
                if statchg_call: statchg_call()
        
        handler = SubHandler()
        subscription = await self.client.create_subscription(interval, handler)
        handler_list = [await subscription.subscribe_data_change(nodeid) for nodeid in nodeid_list]
    
    async def browse_node_all(self, node: Node):
        """재귀적 노드 탐색"""
        node_class = await node.read_node_class()
        child_l = []
        for child_i in await node.get_children():
            child_class = await Node.read_node_class(child_i)
            if child_class in [ua.NodeClass.Object, ua.NodeClass.Variable]:
                child_l.append(await self.browse_node_all(child_i))
        if node_class == ua.NodeClass.Variable:
            try:
                variable_type = (await Node.read_data_type_as_variant_type(node)).value
            except ua.UaError:
                variable_type = None
        else:
            variable_type = None
        node_d = {
            'nodeid' : node.nodeid.to_string(),
            'bname'  : (await Node.read_display_name(node)).Text,
            'class'  : node_class.value,
            'child'  : child_l,
            'type'   : variable_type,
        }
        return node_d
    
    
    
###################
##### TESTING #####
###################
    
if __name__ == '__main__':
    
    async def ous_main():

        ous = OpcuaServer()
        ous.set_server_name()
        print('set_server_name:', ous.server.name)
    
        ous.set_secu_policy([i for i in range(0,9)])
        await ous.load_cert('/home/user/edge/conf/nodi_cert.der')
        await ous.load_pkey('/home/user/edge/conf/nodi_pkey.pem')
        print('load_cert:', ous.server.certificate)
     
        await ous.start_server_back()
        print('start_server:', ous)
        await ous.wait_server_active()
        
        uri = 'urn:freeopcua:python:server'
        
        ns_add = await ous.add_ns(uri)
        print('ns_add:', ns_add)
        
        ns_ls = await ous.get_ns_ls()
        print('ns_ls:', ns_ls)
        
        ns_idx = await ous.get_ns_idx(uri)
        print('ns_idx:', ns_idx)
        
        root_nd = ous.get_node_root()
        print('get_node_root:', root_nd)
        
        obj_nd = ous.get_node_objects()
        print('get_node_objects:', obj_nd)
        
        type_nd = ous.get_node_types()
        print('get_node_types:', type_nd)
        
        svr_nd = ous.get_node_server()
        print('get_node_server:', svr_nd)
            
        any_nd = ous.get_node_any(type_nd)
        print('get_node_any:', any_nd)
        
        fldr_nd1 = await ous.add_node_folder(0, 'fldr_nd1')
        print('add_node_folder1:', fldr_nd1)
        
        fldr_nd2 = await ous.add_node_folder('ns=2;s=hello', 'fldr_nd2', fldr_nd1)
        print('add_node_folder2:', fldr_nd2)
        
        obj_nd = await ous.add_node_object(f'ns={ns_idx};s=hi', 'obj_nd', fldr_nd1)
        print('add_node_object:', obj_nd)
        
        var_nd1 = await ous.add_node_var('ns=1;s=/ifac/ous/i/rw00000', 'var_nd1', fldr_nd2, 'good', True)
        print('add_node_var1:', var_nd1)
        
        var_nd2 = await ous.add_node_var('ns=1;s=/ifac/ous/i/rw00001', 'var_nd2', fldr_nd2, 'good', True)
        print('add_node_var2:', var_nd2)
        
        var_nd3 = await ous.add_node_var(f'ns={ns_idx};s=/ifac/ous/i/rw00002', 'var_nd3', fldr_nd2, 'good', True)
        print('add_node_var3:', var_nd3)
        
        var_nd4 = await ous.add_node_var(ns_idx, 'var_nd4', fldr_nd2, 'good', True)
        print('add_node_var2:', var_nd4)
        
        get_nd = await ous.get_node_var(fldr_nd2)
        print('get_node_var:', get_nd)
        
        any_nd = ous.get_node_any(var_nd1)
        print('get_node_any:', any_nd, type(any_nd))
        
        read_val1 = await ous.read_node_var(var_nd1)
        print('read_node_var1:', read_val1)
        
        read_val2 = await ous.read_node_var(var_nd2)
        print('read_node_var2:', read_val2)
        
        await ous.write_node_var(var_nd2, 'guys')
        print('write_node_var')
        
        read_val1 = await ous.read_node_var(var_nd1)
        print('read_node_var1:', read_val1)
        
        read_val2 = await ous.read_node_var(var_nd2)
        print('read_node_var2:', read_val2)
 
    async def ouc_main():
    
        await asyncio.sleep(15)
        ouc = OpcuaClient(host='192.168.10.67',
                          port='49320',
                          path='')
        await ouc.connect_client()
        print('connect_client:', ouc)
        
        ns_ls = await ouc.read_ns_ls()
        print('ns_ls_read:', ns_ls)
        
        # ns_idx = await ouc.read_ns_idx('urn:freeopcua:python:server')
        # print('ns_read:', ns_idx)
   
        # tagmp_ls = ['ns=1;s=/ifac/ous/i/rw00000', 'ns=1;s=/ifac/ous/i/rw00001', 'ns=1;s=/ifac/ous/i/rw00002']
        
        # nd_ls = [await ouc.get_node_any(i) for i in tagmp_ls]
        # print("nd_ls:", nd_ls)
        
        # var_read = await ouc.read_node_var_many(nd_ls)
        # print('read_node_var_many:', var_read)
        
        # await ouc.write_node_var_one(any_nd1, 'bad')
        # print('write_node_var_one')
        
        # var_read = await ouc.read_node_var_one(any_nd1)
        # print('read_node_var_one:', var_read)
        
        # var_read = await ouc.read_node_var_many([any_nd1, any_nd2, any_nd3])
        # print('read_node_var_many:', var_read)
        
        # await ouc.write_node_var_many([any_nd1, any_nd2], ['hello', 'world'])
        # print('write_node_var_many')
        
        # var_read = await ouc.read_node_var_many([any_nd1, any_nd2, any_nd3])
        # print('read_node_var_many:', var_read)
         
    async def ou_main():
        await asyncio.gather(
            # ous_main(),
            ouc_main()
        )
    
    asyncio.run(ou_main())
    
    import time
    while True:
        print('Looping main!')
        time.sleep(1)