# Producer 설정 파라미터

## 필수/핵심 설정

- bootstrap.servers: 브로커 목록 (예: 'localhost:9092')
- client.id: 클라이언트 식별자
- acks: 메시지 전송 신뢰성 수준
    ```
    0: 응답 대기 없음
    1: 리더 응답 대기 (기본값)
    all/-1: 모든 복제본 응답 대기
    ```

## 성능 설정

- batch.size: 배치 크기 (기본값: 16384)
- linger.ms: 배치 전송 대기 시간 (기본값: 0)
- compression.type: 압축 방식 (none, gzip, snappy, lz4, zstd)
- buffer.memory: 전송 대기 버퍼 크기 (기본값: 32MB)
- max.request.size: 최대 요청 크기 (기본값: 1MB)

## 재시도/타임아웃 설정

- retries: 재시도 횟수 (기본값: 2147483647)
- retry.backoff.ms: 재시도 간격 (기본값: 100)
- request.timeout.ms: 요청 타임아웃 (기본값: 30000)
- delivery.timeout.ms: 전송 완료 타임아웃 (기본값: 120000)

## 추가 설정

- enable.idempotence: 멱등성 프로듀서 활성화 (기본값: false) (정확히 한 번 전송 보장)
- transaction.timeout.ms: 트랜잭션 타임아웃 (기본값: 60000)
- message.timeout.ms: 메시지 전송 타임아웃 (기본값: 300000)
- queue.buffering.max.messages: 내부 큐의 최대 메시지 수 (기본값: 100000)
- queue.buffering.max.kbytes: 내부 큐의 최대 크기 (KB) (기본값: 1048576)


# Consumer 설정 파라미터

## 필수/핵심 설정

- bootstrap.servers: 브로커 목록
- group.id: 컨슈머 그룹 ID
- auto.offset.reset: 초기 오프셋 설정
    ```
    earliest: 가장 초기부터
    latest: 최신부터 (기본값)
    none: 저장된 오프셋 없으면 에러
    ```
    
## 성능 설정

- fetch.min.bytes: 최소 페치 크기 (기본값: 1)
- fetch.max.bytes: 최대 페치 크기 (기본값: 52428800)
- fetch.max.wait.ms: 최대 페치 대기 시간 (기본값: 500)
- max.partition.fetch.bytes: 파티션당 최대 페치 크기 (기본값: 1MB)
- max.poll.records: poll() 당 최대 레코드 수 (기본값: 500)

## 세션/커밋 설정

- session.timeout.ms: 세션 타임아웃 (기본값: 45000)
- heartbeat.interval.ms: 하트비트 간격 (기본값: 3000)
- enable.auto.commit: 자동 커밋 여부 (기본값: true)
- enable.auto.offset.store: 자동 오프셋 저장 여부 (기본값: true)
- auto.commit.interval.ms: 자동 커밋 간격 (기본값: 5000)
- max.poll.interval.ms: poll() 호출 간격 제한 (기본값: 300000)

## 추가 설정

- fetch.error.backoff.ms: 페치 에러 시 재시도 간격 (기본값: 500)
- queued.min.messages: 내부 큐의 최소 메시지 수 (기본값: 100000)
- queued.max.messages.kbytes: 내부 큐의 최대 크기 (KB) (기본값: 1048576)
- fetch.queue.backoff.ms: 큐 백오프 시간 (기본값: 1000)


# 공통 설정 파라미터

## 보안 설정

- security.protocol: 보안 프로토콜 (PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL)
- ssl.key.location: SSL 키 파일 경로
- ssl.certificate.location: SSL 인증서 경로
- ssl.ca.location: CA 인증서 경로
- sasl.mechanism: SASL 인증 방식 (PLAIN, GSSAPI, SCRAM-SHA-256, SCRAM-SHA-512)
- sasl.username: SASL 사용자명
- sasl.password: SASL 비밀번호

## 모니터링 설정

- statistics.interval.ms: 통계 수집 간격 (기본값: 0, 비활성화) (예시: 매 30초마다 통계 수집 -> 30000 설정)
- metrics.recording.level: 메트릭 수집 레벨 (INFO, DEBUG) (성능 모니터링에 필요한 메트릭 수준 설정)
- metrics.sample.window.ms: 메트릭 샘플링 윈도우 (기본값: 30000)

# 네트워크 설정

- receive.buffer.bytes: 소켓 수신 버퍼 크기 (기본값: 32768) (대역폭이 높은 네트워크에서는 증가 필요)
- send.buffer.bytes: 소켓 송신 버퍼 크기 (기본값: 131072)
- socket.timeout.ms: 소켓 연결 타임아웃 (기본값: 60000)
- socket.keepalive.enable: TCP keepalive 활성화 여부 (기본값: false)
- connections.max.idle.ms: 유휴 연결 유지 시간 (기본값: 540000)

# 디버깅 설정

- debug: 디버그 출력 설정 (all, broker, topic, msg 등 동시 선택 가능)
- log.connection.close: 연결 종료 로깅 (기본값: true)
