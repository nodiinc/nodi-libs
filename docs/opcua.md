# OPC UA Server

1. Address Space

    - OPC UA Server가 제공하는 데이터/기능을 계층적으로 구성한 구조
    - Address Space는 트리구조로 표현
    - Node라는 개별 항목들로 구성

1. Namespace

    - Address Space 내 Node를 고유하게 식별하는 데 사용
    - Namespace는 Namespace Index로 식별
    - 동일한 Node Identifier를 갖지만 다른 Namespace에 속하는 Node를 구별
    ```
    > 특히 여러 공급업체가 OPC UA Server를 제공하는 경우 유용
    > Node Identifier가 충돌하지 않도록 보장
    ```
    
1. Namespace Index

    - Namespace Index는 Unsigned Integer
    - 기본 Namespace Index는 0이고, 이 경우 Node Identifier의 'ns=0'은 생략
    - Namespace Index별 Node 숫자 부여 방식
    ```
    > ns=0인 경우 i=20001부터 순차적 부여
    > ns=1인 경우 ns=1;i=2001부터 순차적 부여
    > ns>2인 경우 ns=n;i=1부터 순차적 부여
    ```

1. View

    - Address Space 일부를 나타내는 창구 역할
    - Client가 뷰를 사용하면 Address Space의 일부만 조회/접근할 수 있음

1. Node

    - Address Space 내 Node를 고유하게 식별하는데 사용
    - Variables, Methods, Objects, Folders 등 다양한 구성요소를 포함
    - Node는 NodeId로 식별
    - Node는 NodeId 외에도 Browse Name을 가지고 있음

1. NodeId

    - NodeId는 Namespace Index와 Node Identifier 두 부분으로 구성

1. Node Identifier

    - 각 Namespace Index 내 Node Identifier는 고유해야 함
    - Node는 기본적으로 Unsigned Integer
    - Node Identifier로 사용 가능한 타입
    ```
    > Numeric
        - 구성요소  : 숫자
        - 주 사용처 : 정적 Node 식별
        - Id 예시   : 1001
        - Node 예시 : ns=1;i=1001

    > String
        - 구성요소  : 문자열
        - 주 사용처 : 동적으로 생성되는 Node 식별
        - Id 예시   : 'MyVariable'
        - Node 예시 : ns=2;s=MyVariable

    > GUID
        - 구성요소  : GUID(Global Unique Identifier)로 구성
        - 주 사용처 : Global로 고유한 식별에 사용
        - Id 예시   : {a4f9b010-3128-11ec-9ed1-6d8e7b8b6d2d}
        - Node 예시 : ns=3;g=a4f9b010-3128-11ec-9ed1-6d8e7b8b6d2d
        
    > Opaque
        - 구성요소  : 바이너리 데이터로 구성
        - 주 사용처 : 하드웨어 장치나 다른 시스템과 통신할 때 사용
        - Id 예시   : (hexadecimal bytes) 0x12 0x34 0x56 0x78
        - Node 예시 : ns=4;b=12345678
    ```

1. Browse Name

    - Node를 식별하는데 사용되는 문자열 식별자
    - 사람이 이해하기 쉽고 의미 있는 이름으로 구성
    - Client가 Server의 Address Space를 탐색하고 원하는 Node에 접근하기 위해 사용
    
1. Notes for Development

    - Server의 set_value 또는 get_value를 for문으로 반복하는 속도가 Client의 write_many 또는 read_many보다 빠름
    - nodeid 변수로는 ns_index만 넣어도 되고 또는 'ns=2;s=TestVar'와 같이 직접 NodeId를 넣어도 됨

1. Attribute

    - attr_id 입력 옵션 opcua > ua > attribute_ids.py 참고
    - attr_data 입력 옵션 opcua > ua > uatypes.py > class DataValue 참고        