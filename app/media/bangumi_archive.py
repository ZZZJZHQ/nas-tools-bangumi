import os
import json
import struct
from typing import Optional, TypeVar, Generic
from pathlib import Path
import time

T = TypeVar('T')


class ArchiveStore(Generic[T]):
    """
    Bangumi Archive数据存储类
    用于处理jsonlines格式数据文件，支持索引快速查找
    """

    def __init__(self, base_path: str, file_name: str):
        """
        初始化ArchiveStore
        
        :param base_path: 基础路径
        :param file_name: 数据文件名
        """
        self.base_path = base_path
        self.file_name = file_name
        self.file_path = os.path.join(base_path, file_name)
        self.index_path = os.path.splitext(self.file_path)[0] + ".idx"
        # 缓存索引信息以提高查询效率
        self._index_cache = None
        self._index_cache_time = 0
        
    def exists(self) -> bool:
        """
        检查数据文件是否存在
        
        :return: 文件是否存在
        """
        return os.path.exists(self.file_path) and os.path.exists(self.index_path)
        
    def find_by_id(self, item_id: int) -> Optional[T]:
        """
        根据ID查找条目
        
        :param item_id: 条目ID
        :return: 条目数据或None
        """
        if not self.exists():
            return None

        try:
            # 加载索引缓存
            self._load_index_cache()
            
            if not self._index_cache:
                return None
                
            index_size = self._index_cache['index_size']
            index_data = self._index_cache['index_data']
            
            # 计算索引位置
            index_position = item_id * index_size
            
            # 检查索引位置是否有效
            if index_position + index_size > len(index_data):
                return None
                
            # 读取偏移量
            offset_data = index_data[index_position:index_position + index_size]
            
            # 解析偏移量
            if index_size == 1:
                offset = struct.unpack('B', offset_data)[0]
            elif index_size == 2:
                offset = struct.unpack('<H', offset_data)[0]
            else:  # index_size == 4
                offset = struct.unpack('<I', offset_data)[0]
            
            # 根据偏移量读取数据
            with open(self.file_path, 'r', encoding='utf-8') as data_file:
                data_file.seek(offset)
                line = data_file.readline().strip()
                if line:
                    return json.loads(line)
        except (FileNotFoundError, ValueError, json.JSONDecodeError, struct.error, IndexError):
            pass
            
        return None
        
    def _load_index_cache(self):
        """
        加载索引缓存
        """
        try:
            # 检查索引文件是否已更新
            index_mtime = os.path.getmtime(self.index_path)
            if self._index_cache_time < index_mtime:
                # 重新加载索引
                with open(self.index_path, 'rb') as idx_file:
                    # 读取索引大小（第一个字节）
                    index_size = struct.unpack('B', idx_file.read(1))[0]
                    # 读取索引数据
                    index_data = idx_file.read()
                    
                self._index_cache = {
                    'index_size': index_size,
                    'index_data': index_data
                }
                self._index_cache_time = index_mtime
        except (FileNotFoundError, struct.error):
            self._index_cache = None


class BangumiArchive:
    """
    Bangumi Archive管理类
    管理subject、person、character、episode等数据存储
    """
    
    def __init__(self, base_path: str = None):
        """
        初始化BangumiArchive
        
        :param base_path: 基础路径
        """
        if not base_path:
            # 默认存储在config目录下
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "bangumi_archive")
            
        self.base_path = base_path
        self.subject = ArchiveStore[dict](base_path, "subject.jsonl")
        self.person = ArchiveStore[dict](base_path, "person.jsonl")
        self.character = ArchiveStore[dict](base_path, "character.jsonl")
        self.episode = ArchiveStore[dict](base_path, "episode.jsonl")
        
    def exists(self) -> bool:
        """
        检查Archive是否可用
        
        :return: Archive是否可用
        """
        return all([
            self.subject.exists(),
            self.person.exists(),
            self.character.exists(),
            self.episode.exists()
        ])
        
    def get_subject(self, subject_id: int) -> Optional[dict]:
        """
        获取番剧信息
        
        :param subject_id: 番剧ID
        :return: 番剧信息
        """
        return self.subject.find_by_id(subject_id)
        
    def get_person(self, person_id: int) -> Optional[dict]:
        """
        获取人物信息
        
        :param person_id: 人物ID
        :return: 人物信息
        """
        return self.person.find_by_id(person_id)
        
    def get_character(self, character_id: int) -> Optional[dict]:
        """
        获取角色信息
        
        :param character_id: 角色ID
        :return: 角色信息
        """
        return self.character.find_by_id(character_id)
        
    def get_episode(self, episode_id: int) -> Optional[dict]:
        """
        获取剧集信息
        
        :param episode_id: 剧集ID
        :return: 剧集信息
        """
        return self.episode.find_by_id(episode_id)