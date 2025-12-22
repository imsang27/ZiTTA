"""
ZiTTA 타입 정의 모듈
표준 Intent 계약을 정의합니다.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class Intent:
    """
    명령 의도(Intent)를 나타내는 표준 계약
    
    Attributes:
        type: Intent 타입 ("todo", "memo", "file", "chat", "plugin")
        action: 세부 액션 (Optional, 예: "create", "list", "respond")
        payload: 추가 데이터 (Optional, Dict 형태)
        source: Intent 출처 (Optional, 예: "router", "plugin:ExamplePlugin")
    """
    type: str  # "todo", "memo", "file", "chat", "plugin"
    action: Optional[str] = None  # "create", "list", "respond" 등
    payload: Optional[Dict[str, Any]] = None  # 추가 데이터
    source: Optional[str] = None  # Intent 출처

