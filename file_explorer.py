"""
파일 탐색 및 시스템 제어 모듈
파일 시스템 탐색 및 기본적인 시스템 제어 기능을 제공합니다.
"""
import os
import subprocess
import platform
from typing import List, Dict, Optional
from pathlib import Path

class FileExplorer:
    """파일 탐색 및 시스템 제어 클래스"""
    
    def __init__(self):
        """FileExplorer 초기화"""
        self.system = platform.system()
    
    def list_directory(self, path: str = None) -> List[Dict]:
        """
        디렉토리 내용 나열
        
        Args:
            path: 디렉토리 경로 (None이면 현재 디렉토리)
            
        Returns:
            파일/디렉토리 정보 리스트
        """
        if path is None:
            path = os.getcwd()
        
        try:
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                is_dir = os.path.isdir(item_path)
                size = 0 if is_dir else os.path.getsize(item_path)
                
                items.append({
                    "name": item,
                    "path": item_path,
                    "is_directory": is_dir,
                    "size": size
                })
            
            return sorted(items, key=lambda x: (not x["is_directory"], x["name"].lower()))
        except PermissionError:
            return []
        except Exception as e:
            print(f"디렉토리 나열 오류: {e}")
            return []
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """
        파일 정보 조회
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 정보 딕셔너리 또는 None
        """
        try:
            stat = os.stat(file_path)
            return {
                "path": file_path,
                "name": os.path.basename(file_path),
                "size": stat.st_size,
                "is_directory": os.path.isdir(file_path),
                "created": stat.st_ctime,
                "modified": stat.st_mtime
            }
        except Exception as e:
            print(f"파일 정보 조회 오류: {e}")
            return None
    
    def search_files(self, directory: str, pattern: str, recursive: bool = True) -> List[str]:
        """
        파일 검색
        
        Args:
            directory: 검색할 디렉토리
            pattern: 검색 패턴 (파일명에 포함될 문자열)
            recursive: 재귀 검색 여부
            
        Returns:
            찾은 파일 경로 리스트
        """
        found_files = []
        
        try:
            if recursive:
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if pattern.lower() in file.lower():
                            found_files.append(os.path.join(root, file))
            else:
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    if os.path.isfile(item_path) and pattern.lower() in item.lower():
                        found_files.append(item_path)
        except PermissionError:
            pass
        except Exception as e:
            print(f"파일 검색 오류: {e}")
        
        return found_files
    
    def open_file(self, file_path: str) -> bool:
        """
        파일 열기 (시스템 기본 프로그램으로)
        
        Args:
            file_path: 파일 경로
            
        Returns:
            성공 여부
        """
        try:
            if self.system == "Windows":
                os.startfile(file_path)
            elif self.system == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
            return True
        except Exception as e:
            print(f"파일 열기 오류: {e}")
            return False
    
    def open_directory(self, directory_path: str) -> bool:
        """
        디렉토리 열기 (파일 탐색기/파인더)
        
        Args:
            directory_path: 디렉토리 경로
            
        Returns:
            성공 여부
        """
        try:
            if self.system == "Windows":
                os.startfile(directory_path)
            elif self.system == "Darwin":  # macOS
                subprocess.run(["open", directory_path])
            else:  # Linux
                subprocess.run(["xdg-open", directory_path])
            return True
        except Exception as e:
            print(f"디렉토리 열기 오류: {e}")
            return False
    
    def get_system_info(self) -> Dict:
        """
        시스템 정보 조회
        
        Returns:
            시스템 정보 딕셔너리
        """
        return {
            "system": self.system,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
    
    def execute_command(self, command: str, shell: bool = True) -> tuple[str, int]:
        """
        시스템 명령 실행 (주의: 보안상 제한적으로 사용)
        
        Args:
            command: 실행할 명령
            shell: 셸 사용 여부
            
        Returns:
            (출력, 반환 코드) 튜플
        """
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=10  # 10초 타임아웃
            )
            return (result.stdout + result.stderr, result.returncode)
        except subprocess.TimeoutExpired:
            return ("명령 실행 시간 초과", -1)
        except Exception as e:
            return (f"명령 실행 오류: {str(e)}", -1)

