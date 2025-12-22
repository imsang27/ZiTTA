"""
플러그인 관리 모듈 (core 패키지)
플러그인 기반 확장 구조를 제공합니다.
"""
import os
import importlib
import importlib.util
import inspect
from typing import Dict, List, Optional, Any, Union
from .config import Config
from .types import Intent


class PluginBase:
    """플러그인 기본 클래스"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """
        플러그인 초기화
        
        Args:
            name: 플러그인 이름
            version: 플러그인 버전
        """
        self.name = name
        self.version = version
        self.enabled = True
    
    def on_load(self):
        """플러그인 로드 시 호출"""
        pass
    
    def on_unload(self):
        """플러그인 언로드 시 호출"""
        pass
    
    def handle_command(self, command: str, context: Dict = None) -> Optional[Dict]:
        """
        명령 처리
        
        Args:
            command: 사용자 명령
            context: 컨텍스트 정보
            
        Returns:
            처리 결과 또는 None (처리하지 않음)
        """
        return None
    
    def get_commands(self) -> List[str]:
        """
        지원하는 명령 목록 반환
        
        Returns:
            명령 키워드 리스트
        """
        return []


class PluginManager:
    """플러그인 관리자"""
    
    def __init__(self):
        """플러그인 관리자 초기화"""
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_dir = Config.PLUGIN_DIR
        self._ensure_plugin_dir()
    
    def _ensure_plugin_dir(self):
        """플러그인 디렉토리 생성"""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            # __init__.py 파일 생성
            init_file = os.path.join(self.plugin_dir, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write("# ZiTTA 플러그인 디렉토리\n")
    
    def load_plugins(self):
        """모든 플러그인 로드"""
        if not os.path.exists(self.plugin_dir):
            return
        
        # 플러그인 디렉토리의 모든 Python 파일 검색
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                plugin_name = filename[:-3]  # .py 제거
                try:
                    self.load_plugin(plugin_name)
                except Exception as e:
                    print(f"플러그인 '{plugin_name}' 로드 실패: {e}")
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        플러그인 로드
        
        Args:
            plugin_name: 플러그인 이름 (파일명에서 .py 제외)
            
        Returns:
            성공 여부
        """
        try:
            # 플러그인 모듈 import
            spec = importlib.util.spec_from_file_location(
                plugin_name,
                os.path.join(self.plugin_dir, f"{plugin_name}.py")
            )
            
            if spec is None or spec.loader is None:
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # PluginBase를 상속한 클래스 찾기
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, PluginBase)
                    and obj is not PluginBase
                ):
                    plugin_instance = obj()
                    self.plugins[plugin_name] = plugin_instance
                    plugin_instance.on_load()
                    print(f"플러그인 '{plugin_name}' 로드 완료")
                    return True
            
            return False
        except Exception as e:
            print(f"플러그인 '{plugin_name}' 로드 오류: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        플러그인 언로드
        
        Args:
            plugin_name: 플러그인 이름
            
        Returns:
            성공 여부
        """
        if plugin_name in self.plugins:
            try:
                self.plugins[plugin_name].on_unload()
                del self.plugins[plugin_name]
                print(f"플러그인 '{plugin_name}' 언로드 완료")
                return True
            except Exception as e:
                print(f"플러그인 '{plugin_name}' 언로드 오류: {e}")
                return False
        return False
    
    def handle_command(self, command: str, context: Dict = None) -> Optional[Intent]:
        """
        명령을 플러그인에 전달하여 처리
        
        Args:
            command: 사용자 명령
            context: 컨텍스트 정보
            
        Returns:
            Intent 객체 또는 None (처리하지 않음)
        """
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    result = plugin.handle_command(command, context)
                    if result is not None:
                        # Intent로 변환
                        return self._convert_to_intent(result, plugin.name)
                except Exception as e:
                    print(f"플러그인 '{plugin.name}' 명령 처리 오류: {e}")
        return None
    
    def _convert_to_intent(self, result: Union[Dict, Intent], plugin_name: str) -> Intent:
        """
        플러그인 결과를 Intent로 변환 (구버전 dict 호환 지원)
        
        Args:
            result: 플러그인 반환값 (Dict 또는 Intent)
            plugin_name: 플러그인 이름
            
        Returns:
            Intent 객체
        """
        # 이미 Intent인 경우 그대로 반환
        if isinstance(result, Intent):
            return result
        
        # dict인 경우 Intent로 변환
        if isinstance(result, dict):
            # 구버전 형식: {"type":"plugin_response","plugin":"X","response":"..."}
            if result.get("type") == "plugin_response":
                return Intent(
                    type="plugin",
                    action="respond",
                    payload={
                        "plugin": result.get("plugin", plugin_name),
                        "response": result.get("response", "")
                    },
                    source=f"plugin:{plugin_name}"
                )
            # 기타 dict 형식도 Intent로 변환 시도
            return Intent(
                type=result.get("type", "plugin"),
                action=result.get("action"),
                payload=result.get("payload") or result,  # payload가 없으면 전체 dict를 payload로
                source=f"plugin:{plugin_name}"
            )
        
        # 예상치 못한 타입인 경우 기본 Intent 반환
        return Intent(
            type="plugin",
            action="respond",
            payload={"result": result},
            source=f"plugin:{plugin_name}"
        )
    
    def get_plugin_list(self) -> List[Dict[str, Any]]:
        """
        로드된 플러그인 목록 반환
        
        Returns:
            플러그인 정보 리스트
        """
        return [
            {
                "name": plugin.name,
                "version": plugin.version,
                "enabled": plugin.enabled,
            }
            for plugin in self.plugins.values()
        ]


