from collections import deque
import paho.mqtt.client as mqtt

class MosquittoClient:
    """Mosquitto MQTT Client"""

    def __init__(self, id, host, port=1883, timeout=10,
                 username=None, password=None,
                 inflight_qt=20, message_qt=20, debug=False):
        
        # Create client
        self.client = mqtt.Client(client_id=id)
        
        # Get arguments
        self.host = host
        self.port = port
        self.timeout = timeout
        self.username = username
        self.password = password
        self.inflight_qt = inflight_qt
        self.message_qt = message_qt
        self.debug = debug
        
        # Set authentication
        if (self.username is not None) and (self.password is not None):
            self.client.username_pw_set(username=self.username,
                                        password=self.password)
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_connect_fail = self._on_connect_fail
        self.client.on_disconnect = self._on_disconnect
        self.client.on_log = self._on_log
        
        # Set other options
        self.client.max_queued_messages_set(queue_size=self.message_qt)
        self.client.max_inflight_messages_set(inflight=self.inflight_qt)
        
        """
        ["max_queued_messages_set" Method]
            * Description
                - MQTT에서 "queued_messages"는 전송을 기다리는 메시지의 수를 의미
                - 클라이언트 객체의 메시지 대기열 크기를 설정하는 데 사용
            * "queue_size" Argument
                - 대기열에 유지할 수 있는 메시지 수의 최대 한도
                - 높게 설정하면 메시지가 대기열에 머무는 시간이 줄어들지만
                    메모리 사용량이 증가
                - 기본값 0 (무제한)
                
        ["max_inflight_messages_set" Method]
            * Description
                - MQTT에서 in-flight 메시지는 이미 브로커에 전송되었지만
                아직 브로커에서 확인을 받지 않은 메시지를 의미
                - 클라이언트 객체의 동시 진행 중 메시지 수를 설정하는 데 사용
                - QoS 1 또는 2에서 사용할 수 있음
            * "inflight" Argument
                - 동시에 전송할 수 있는 최대 in-flight 메시지 수
                - 높게 설정하면 클라이언트가 동시에 더 많은 메시지를 처리하지만
                  메모리 및 대역폭 요구 사항이 증가
                - 기본값 20
        """
    
    def connect(self):
        """Connect client"""
        self.client.connect(host=self.host,
                            port=int(self.port),
                            keepalive=int(self.timeout))

    def disconnect(self):
        """Disconnect client"""
        self.client.disconnect()
    
    def check_connection(self):
        """Check connection status"""
        res = self.client.is_connected()
        return res
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback on connect success"""
        if self.debug:
            print(f'on_connect | '
                  f'client: {client} | '
                  f'userdata: {userdata} | '
                  f'flags: {flags} | '
                  f'rc: {rc}')
    
    def _on_connect_fail(self, client, userdata, flags, rc):
        """Callback on connect failure"""
        if self.debug:
            print(f'on_connect_fail | '
                  f'client: {client} | '
                  f'userdata: {userdata} | '
                  f'flags: {flags} | '
                  f'rc: {rc}')

    def _on_disconnect(self, client, userdata, rc):
        """Callback on disconnect"""
        if self.debug:
            print(f'on_disconnect | '
                  f'client: {client} | '
                  f'userdata: {userdata} | '
                  f'rc: {rc}')
        
    def _on_log(self, client, userdata, level, buf):
        """Callback on log"""
        if self.debug:
            print(f'on_log | '
                  f'client: {client} | '
                  f'userdata: {userdata} | '
                  f'level: {level} | '
                  f'buf: {buf}')

class MosquittoPublisher(MosquittoClient):
    """Mosquitto MQTT Publisher"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set callbacks
        self.client.on_publish = self._on_publish
    
    def publish(self, topic: str, payload: bin, qos=0, retain=False, properties=None):
        """Publish to topic"""
        """
        * Cannot publish multiple messages coincidentally.
        * Should do publish() multiple times.
        """
        (rc, mid) = self.client.publish(topic=topic,
                                        payload=payload,
                                        qos=int(qos),
                                        retain=bool(retain),
                                        properties=properties)
        if self.debug:
            print(f'publish | '
                  f'return: rc {rc} | '
                  f'mid: {mid}')
        return (rc, mid)

    def _on_publish(self, client, userdata, mid):
        """Callback on publish"""
        if self.debug:
            print(f'on_publish | '
                  f'client: {client} | '
                  f'userdata: {userdata} | '
                  f'mid: {mid}')

class MosquittoSubscriber(MosquittoClient):
    """Mosquitto MQTT Subscriber"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_queue = deque()
        
        # Set callbacks
        self.client.on_subscribe = self._on_subscribe
        self.client.on_unsubscribe = self._on_unsubscribe
        self.client.on_message = self._on_message
    
    def subscribe(self, topic, qos=0, options=None, properties=None):
        """Subscribe topic"""
        """
        * Can publish multiple messages coincidentally.
        * Should delivery list [(topic, qos), ...] as argument.
        """
        (rc, mid) = self.client.subscribe(topic=topic,
                                          qos=int(qos),
                                          options=options,
                                          properties=properties)
        if self.debug:
            print(f'subscribe | '
                  f'return: rc {rc} | '
                  f'mid: {mid}')
        return (rc, mid)
    
    def unsubscribe(self, topic, properties=None):
        """Unsubscribe topic"""
        (rc, mid) = self.client.unsubscribe(topic=topic,
                                            properties=properties)
        self.message_queue.clear()
        if self.debug:
            print(f'unsubscribe | '
                  f'return: rc {self.rc} | '
                  f'mid: {self.mid}')
        return (rc, mid)
    
    def disconnect(self):
        """Disconnect client"""
        super().disconnect()
        
        # Clear message queue
        self.message_queue.clear()
    
    def start_loop_front(self):
        """Start looping on foreground"""
        self.client.loop_forever()
    
    def start_loop_back(self):
        """Start looping on background"""
        self.client.loop_start()
    
    def stop_loop_back(self):
        """Stop looping on background"""
        self.client.loop_stop()
    
    def check_loop_back(self):
        """Check looping status on background"""
        if self.client._thread is None:
            return False
        elif not self.client._thread.is_alive():
            return False
        else:
            return True
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback on subscribe"""
        if self.debug:
            print(f'on_subscribe | '
                  f'client: {client} | '
                  f'userdata: {userdata} | '
                  f'mid: {mid} | '
                  f'granted_qos: {granted_qos}')
        
    def _on_unsubscribe(self, client, userdata, mid):
        """Callback on unsubscribe"""
        if self.debug:
            print(f'on_unsubscribe | '
                  f'client: {client} | '
                  f'userdata: {userdata} | '
                  f'mid: {mid}')
        
    def _on_message(self, client, userdata, message):
        """Callback on message reception"""
        self.message_queue.append(message)
        if self.debug:
            print(f'on_message | '
                  f'client: {client} | '
                  f'userdata: {userdata} | '
                  f'message: {message} | '
                  f'topic: {message.topic} | '
                  f'payload: {message.payload} | '
                  f'qos: {message.qos} | '
                  f'retain: {message.retain}')

if __name__ == '__main__':
    
    import time
    from multiprocessing import Process

    def mqp_func():
        mqp = MosquittoPublisher(id = 'mqp',
                                 host = '43.202.161.226',
                                 port = 1883,
                                 username = 'nodi',
                                 password = 'PASS00371')
        cnt = 0
        while True:
            try:
                mqp.connect()
                while True:
                    mqp.publish(topic = 'derms/rtu1/test1',
                                payload = f'hello, world!!! {cnt}',
                                qos = 0,
                                retain = False)
                    mqp.publish(topic = 'derms/rtu2/test1',
                                payload = f'hello, world!!! {cnt}',
                                qos = 0,
                                retain = False)
                    mqp.publish(topic = 'derms/rtu2/test2',
                                payload = f'hello, world!!! {cnt}',
                                qos = 0,
                                retain = False)
                    cnt += 1
                    print("OTHER MQP LOGIC IS RUNNING!")
                    time.sleep(2)
            except Exception as exc:
                print(exc)
                mqp.disconnect()
                print(f"OTHER MQP LOGIC IS RESETTING!")
                time.sleep(4)

    def mqs_func():
        mqs = MosquittoSubscriber(id = 'mqs',
                                  host = '43.202.161.226',
                                  port = 1883,
                                  username = 'nodi',
                                  password = 'PASS00371')
        while True:
            try:
                mqs.connect()
                # mqs.subscribe([['derms/rtu1/test1', 0],
                #                ['derms/rtu2/test1', 0],
                #                ['derms/rtu2/test2', 0]])
                mqs.subscribe('/edge/NE-D5A70/creq')
                print('STARTING!!!')
                mqs.start_loop_back()
                cnt = 0
                while True:
                    print('CHECK!!!!', mqs.check_loop_back())
                    msg_ls = []
                    if len(mqs.message_queue) > 0:
                        msg_qu_cp = mqs.message_queue.copy()
                        mqs.message_queue.clear()
                        for msg_it in msg_qu_cp:
                            msg_ls.append([msg_it.topic,
                                           msg_it.payload.decode()])
                    print(msg_ls)
                    cnt += 1
                    print(f"MQS IS RUNNING! {cnt}")
                    if cnt > 6:
                        mqs.stop_loop_back()
                        print('CHECK!!!!', mqs.check_loop_back())
                        raise
                    time.sleep(2)
            except Exception as exc:
                print(exc)
                # mqs.loop_back_stop()
                mqs.disconnect()
                print(f"MQS IS RESETTING!")
                time.sleep(2)
                

    mqc = input('INPUT: ')
    if mqc == 'p':
        mqp_proc = Process(target=mqp_func)
        mqp_proc.start()
        mqp_proc.join()
    elif mqc == 's':
        mqs_proc = Process(target=mqs_func)
        mqs_proc.start()
        mqs_proc.join()
    
    # HOST = '223.130.131.186'
    # PORT = 1883
    # USER = 'by39w69c0iecy1tr'
    # PWD  = 'ac807757ae735dcfac7f97fbb0c19c24'
