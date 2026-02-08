# OTA (Over-The-Air) 업데이트 시스템 설계

## 개요

nodi-edge 디바이스의 원격 소프트웨어 업데이트를 위한 OTA 시스템 설계 문서.

## 전체 흐름

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              OTA 전체 흐름                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [개발 PC]                        [클라우드]                    [엣지 머신]   │
│                                                                             │
│  1. 개발/빌드                                                               │
│     ├─ git tag v1.2.3                                                       │
│     ├─ 빌드 & 패키징                                                         │
│     └─ 업로드 ──────────────────→ 2. 패키지 저장소                            │
│                                     ├─ S3/MinIO                             │
│                                     └─ 버전 메타데이터 DB                     │
│                                                                             │
│                                  3. 디바이스 관리                             │
│                                     ├─ 연결 상태 모니터링 ←──── Heartbeat ───┤
│                                     ├─ 현재 버전 추적 ←──────── 버전 리포트 ──┤
│                                     └─ 업데이트 대상 선정                     │
│                                                                             │
│                                  4. 업데이트 배포                             │
│                                     ├─ 승인 프로세스                          │
│                                     └─ 커맨드 전송 ─────────→ 5. 업데이트 수신 │
│                                                                 ├─ 다운로드   │
│                                                                 ├─ 검증       │
│                                                                 ├─ 백업       │
│                                                                 ├─ 설치       │
│                                                                 ├─ 재시작     │
│                                                                 └─ 롤백 (실패시)│
│                                                                             │
│                                  6. 결과 수집 ←─────────────── 결과 리포트 ──┤
│                                     └─ 성공/실패 기록                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 기존 구현 (참고)

### Rpt (Report) - 로컬 → 클라우드

- 파일: `/root/edge/rpt/core.py`
- 역할: 로컬 데이터를 MQTT로 클라우드에 publish
- 토픽: `RPT_REPORT_TOPIC_FORMAT.format(sn=serial_number)`

### Rmt (Remote) - 클라우드 → 로컬

- 파일: `/root/edge/rmt/core.py`
- 역할: 클라우드에서 커맨드를 subscribe하고 실행
- 토픽: `RMT_REQUEST_TOPIC_FORMAT.format(sn=serial_number)`
- 응답: `RMT_RESPONSE_TOPIC_FORMAT.format(sn=serial_number)`

---

## 1. 버전 관리 (개발 PC)

### 패키지 구조

```
nodi-edge/
├── pyproject.toml             # version = "1.2.3"
├── src/nodi_edge/__init__.py  # __version__ = "1.2.3"
└── CHANGELOG.md
```

### 배포 패키지 구조

```
nodi-edge-1.2.3.tar.gz
├── nodi_edge/              # 소스 코드
├── requirements.txt        # 의존성
├── install.sh              # 설치 스크립트
├── manifest.json           # 메타데이터
│   {
│     "version": "1.2.3",
│     "checksum": "sha256:abc123...",
│     "min_python": "3.9",
│     "requires_restart": true,
│     "rollback_supported": true
│   }
└── migrations/             # DB 마이그레이션 (필요시)
```

---

## 2. 클라우드 측 구성

### DB 스키마 (예시)

```python
# 패키지 저장소
packages:
  - package_id: "nodi-edge"
    version: "1.2.3"
    url: "s3://packages/nodi-edge-1.2.3.tar.gz"
    checksum: "sha256:abc123..."
    release_date: "2026-01-19"
    release_notes: "버그 수정"
    status: "stable"  # stable, beta, deprecated

# 디바이스 등록
devices:
  - serial_number: "EDGE001"
    site_id: "factory-a"
    current_version: "1.2.0"
    target_version: "1.2.3"  # null이면 업데이트 없음
    last_heartbeat: "2026-01-19T10:00:00Z"
    status: "online"  # online, offline, updating
    update_policy: "auto"  # auto, manual, scheduled

# 업데이트 이력
update_history:
  - device_sn: "EDGE001"
    from_version: "1.2.0"
    to_version: "1.2.3"
    status: "success"  # pending, downloading, installing, success, failed, rolled_back
    started_at: "2026-01-19T10:05:00Z"
    completed_at: "2026-01-19T10:07:00Z"
    error_message: null
```

---

## 3. 엣지 측 OTA Agent

### 처리 흐름

```python
class OtaAgent:

    def handle_update_command(self, cmd: dict) -> dict:
        """
        cmd = {
            "action": "update",
            "package": "nodi-edge",
            "version": "1.2.3",
            "url": "https://...",
            "checksum": "sha256:abc123..."
        }
        """
        try:
            # 1. 다운로드
            self._download_package(cmd["url"], cmd["checksum"])

            # 2. 검증
            self._verify_package(cmd["checksum"])

            # 3. 백업 (롤백용)
            self._backup_current_version()

            # 4. 설치
            self._install_package()

            # 5. 서비스 재시작
            self._restart_services()

            # 6. 헬스체크
            if not self._health_check():
                raise Exception("Health check failed")

            return {"status": "success", "version": cmd["version"]}

        except Exception as exc:
            # 롤백
            self._rollback()
            return {"status": "failed", "error": str(exc)}
```

### 상태 전이

```
IDLE → DOWNLOADING → VERIFYING → BACKING_UP → INSTALLING → RESTARTING → HEALTH_CHECK → IDLE
                                                                              ↓ (실패시)
                                                                         ROLLING_BACK → IDLE
```

---

## 4. 버전 리포트 (Rpt 확장)

기존 Rpt에 버전 정보 추가:

```python
rpt_pl = {
    'tm_rpt': get_current_timestamp(),
    # ... 기존 데이터 ...

    # 버전 정보 추가
    'ota/current_version': "1.2.0",
    'ota/update_status': "idle",  # idle, downloading, installing
    'ota/last_update_time': "2026-01-15T...",
    'ota/disk_free_gb': 5.2,  # 업데이트 가능 여부 판단용
}
```

---

## 5. 업데이트 커맨드 (Rmt 확장)

`func/core.py`에 OTA 함수 추가:

```python
class Func:
    def run(self, req_pl: dict) -> Any:
        action = req_pl.get("action")

        if action == "ota_update":
            return self._handle_ota_update(req_pl)
        elif action == "ota_rollback":
            return self._handle_ota_rollback(req_pl)
        elif action == "ota_status":
            return self._get_ota_status()
        # ... 기존 함수들 ...
```

### MQTT 메시지 포맷

**업데이트 요청 (클라우드 → 엣지):**
```json
{
    "action": "ota_update",
    "package": "nodi-edge",
    "version": "1.2.3",
    "url": "https://s3.example.com/packages/nodi-edge-1.2.3.tar.gz",
    "checksum": "sha256:abc123def456...",
    "force": false
}
```

**업데이트 응답 (엣지 → 클라우드):**
```json
{
    "action": "ota_update",
    "status": "success",
    "version": "1.2.3",
    "previous_version": "1.2.0",
    "timestamp": "2026-01-19T10:07:00Z"
}
```

**실패 응답:**
```json
{
    "action": "ota_update",
    "status": "failed",
    "error": "Checksum mismatch",
    "rolled_back": true,
    "current_version": "1.2.0",
    "timestamp": "2026-01-19T10:06:30Z"
}
```

---

## 6. 구현 우선순위

| 순서 | 구성요소 | 위치 | 설명 |
|------|---------|------|------|
| 1 | 버전 리포트 | 엣지 (Rpt 확장) | 현재 버전을 클라우드로 전송 |
| 2 | 패키지 다운로더 | 엣지 (신규) | URL에서 패키지 다운로드 + 검증 |
| 3 | 설치/롤백 로직 | 엣지 (신규) | pip install + systemd restart + rollback |
| 4 | OTA 커맨드 핸들러 | 엣지 (Rmt/Func 확장) | 업데이트 커맨드 처리 |
| 5 | 패키지 저장소 | 클라우드 | S3 + 메타데이터 API |
| 6 | 디바이스 관리 UI | 클라우드 | 버전 현황 + 업데이트 승인 |

---

## 7. 보안 고려사항

### 패키지 검증
- SHA256 체크섬 검증 필수
- 선택적: GPG 서명 검증

### 통신 보안
- HTTPS로 패키지 다운로드
- MQTT TLS 사용

### 롤백 안전성
- 업데이트 전 현재 버전 백업 필수
- 헬스체크 실패 시 자동 롤백
- 롤백 실패 시 알림

---

## 8. 디렉토리 구조 (엣지)

```
/home/nodi/nodi-edge-data/
├── backup/
│   └── ota/
│       ├── nodi-edge-1.2.0.backup.tar.gz  # 롤백용 백업
│       └── nodi-edge-1.1.0.backup.tar.gz
├── config/
│   └── ota.yaml                           # OTA 설정
├── data/
│   └── ota/
│       └── downloads/                     # 다운로드 임시 저장
└── log/
    └── ota.log                            # OTA 전용 로그
```

### OTA 설정 파일 (ota.yaml)

```yaml
ota:
  enabled: true
  auto_update: false
  check_interval_hours: 24
  max_backup_count: 3
  download_timeout_sec: 300
  install_timeout_sec: 600
  health_check_retries: 3
  health_check_interval_sec: 10
```
