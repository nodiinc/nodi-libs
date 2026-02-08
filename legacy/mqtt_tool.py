import paho.mqtt.client as mqtt
import time

def match_mqtt_pattern(topic, pattern):
    """Check if check topic is matched with sub pattern"""
    
    # Split inputs
    topic_parts = topic.split('/')
    pattern_parts = pattern.split('/')    
    
    i = 0
    while i < len(pattern_parts):

        # '#' matches all remaining levels
        if pattern_parts[i] == '#':
            return True
        
        # Pattern is longer than topic
        if i >= len(topic_parts):
            return False
        
        # Not matching and not a wildcard
        if pattern_parts[i] != '+' and pattern_parts[i] != topic_parts[i]:
            return False
        i += 1
    
    # All parts matched
    if i == len(topic_parts):
        return True

    # Not all parts matched
    else:
        return False

BROKER_HOST = "localhost"
BROKER_PORT = 19183
CLIENT_ID = f"mqtt-clear-retain-{int(time.time())}"
BROKER_USR = "nodi-edge"
BROKER_PWD = "n@Di-eD6e"

# 수집된 retain 토픽 목록
retain_topics = set()
finished = False

def on_connect(client, userdata, flags, rc):
    print("[CONNECTED]", rc)
    client.subscribe("#")  # 루트부터 전체 구독

def on_message(client, userdata, msg):
    # retain 플래그가 True인 메시지만 처리
    if msg.retain:
        print(f"[RETAIN] {msg.topic}")
        retain_topics.add(msg.topic)

def on_disconnect(client, userdata, rc):
    print("[DISCONNECTED]", rc)

def collect_retained_topics(timeout=3):
    global finished
    client = mqtt.Client(client_id=CLIENT_ID, clean_session=True)
    client.username_pw_set(BROKER_USR, BROKER_PWD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()
    time.sleep(timeout)  # 수집 시간 확보
    client.loop_stop()
    client.disconnect()
    finished = True

def clear_retained_topics():
    client = mqtt.Client(client_id=f"{CLIENT_ID}-clear", clean_session=True)
    client.username_pw_set(BROKER_USR, BROKER_PWD)
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()
    for topic in retain_topics:
        print(f"[CLEAR] {topic}")
        client.publish(topic, payload=None, qos=0, retain=True)
        time.sleep(0.01)  # 브로커 과부하 방지용
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    print("== RETAINED TOPIC COLLECTION START ==")
    collect_retained_topics()
    print("== RETAINED TOPIC CLEARING START ==")
    clear_retained_topics()
    print("== DONE ==")
