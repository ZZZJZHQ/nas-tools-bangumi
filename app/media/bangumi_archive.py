import json
import os
import struct
import time
from pathlib import Path
from typing import TypeVar, List, Optional, Dict, Any, Generic
from app.helper.bangumi_archive_helper import BangumiArchiveHelper

T = TypeVar('T', Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any])


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
        self.base_path = Path(base_path)
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
            print(f"[BangumiArchive] 数据文件不存在: {self.file_path}")
            return None

        try:
            # 加载索引缓存
            self._load_index_cache()
            
            if not self._index_cache:
                print(f"[BangumiArchive] 无法加载索引缓存: {self.index_path}")
                return None
                
            index_size = self._index_cache['index_size']
            index_data = self._index_cache['index_data']
            
            # 计算索引位置
            index_position = item_id * index_size
            
            # 检查索引位置是否有效
            if index_position + index_size > len(index_data):
                print(f"[BangumiArchive] 索引位置超出范围，ID: {item_id}")
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
                    result = json.loads(line)
                    print(f"[BangumiArchive] 成功查询到ID为 {item_id} 的数据")
                    return result
                else:
                    print(f"[BangumiArchive] 未找到ID为 {item_id} 的数据")
        except (FileNotFoundError, ValueError, json.JSONDecodeError, struct.error, IndexError) as e:
            print(f"[BangumiArchive] 查询ID {item_id} 时发生错误: {e}")
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
        except (FileNotFoundError, struct.error) as e:
            print(f"[BangumiArchive] 加载索引文件失败: {e}")
            self._index_cache = None

    def get_all_items(self) -> List[T]:
        """
        获取所有条目
        
        :return: 所有条目列表
        """
        if not self.exists():
            print(f"[BangumiArchive] 数据文件不存在: {self.file_path}")
            return []
            
        items = []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        items.append(json.loads(line))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[BangumiArchive] 读取所有项目时发生错误: {e}")
            pass
            
        return items


class BangumiArchive:
    """
    Bangumi Archive管理类
    管理subject、person、character、episode等数据存储
    """
    
    def __init__(self):
        """
        初始化BangumiArchive
        
        :param base_path: 基础路径
        """
        base_path = BangumiArchiveHelper()._base_path
            
        self.base_path = base_path
        self.subject = ArchiveStore[dict](base_path, "subject.jsonlines")
        self.character = ArchiveStore[dict](base_path, "character.jsonlines")
        self.episode = ArchiveStore[dict](base_path, "episode.jsonlines")
        # subject-episode映射文件路径
        self.subject_episode_map_path = os.path.join(base_path, "subject_episode.map")
        # 缓存映射数据
        self._subject_episode_map = None
        self._subject_episode_map_time = 0
        
    def exists(self) -> bool:
        """
        检查Archive是否可用
        
        :return: Archive是否可用
        """
        return all([
            self.subject.exists(),
            self.character.exists(),
            self.episode.exists()
        ])
        
    def get_subject(self, subject_id: int) -> Optional[dict]:
        """
        获取番剧信息
        
        :param subject_id: 番剧ID
        :return: 番剧信息
        """
        result = self.subject.find_by_id(subject_id)
        if result:
            print(f"[BangumiArchive] 成功从离线数据库查询到subject_id为 {subject_id} 的番剧信息")
        else:
            print(f"[BangumiArchive] 离线数据库中未找到subject_id为 {subject_id} 的番剧信息")
        return result
        
    def get_character(self, character_id: int) -> Optional[dict]:
        """
        获取角色信息
        
        :param character_id: 角色ID
        :return: 角色信息
        """
        result = self.character.find_by_id(character_id)
        if result:
            print(f"[BangumiArchive] 成功从离线数据库查询到character_id为 {character_id} 的角色信息")
        else:
            print(f"[BangumiArchive] 离线数据库中未找到character_id为 {character_id} 的角色信息")
        return result
        
    def get_episode(self, episode_id: int) -> Optional[dict]:
        """
        获取剧集信息
        
        :param episode_id: 剧集ID
        :return: 剧集信息
        """
        result = self.episode.find_by_id(episode_id)
        if result:
            print(f"[BangumiArchive] 成功从离线数据库查询到episode_id为 {episode_id} 的剧集信息")
        else:
            print(f"[BangumiArchive] 离线数据库中未找到episode_id为 {episode_id} 的剧集信息")
        return result
        
    def _load_subject_episode_map(self):
        """
        加载subject-episode映射缓存
        """
        try:
            # 检查映射文件是否已更新
            if os.path.exists(self.subject_episode_map_path):
                map_mtime = os.path.getmtime(self.subject_episode_map_path)
                if self._subject_episode_map_time < map_mtime:
                    # 重新加载映射
                    with open(self.subject_episode_map_path, 'rb') as map_file:
                        self._subject_episode_map = {}
                        while map_file.tell() < os.path.getsize(self.subject_episode_map_path):
                            subject_id = struct.unpack('<I', map_file.read(4))[0]  # 4字节
                            episode_count = struct.unpack('<H', map_file.read(2))[0]  # 2字节
                            episode_ids = []
                            for _ in range(episode_count):
                                episode_id = struct.unpack('<I', map_file.read(4))[0]  # 4字节
                                episode_ids.append(episode_id)
                            self._subject_episode_map[subject_id] = episode_ids
                    self._subject_episode_map_time = map_mtime
                    print(f"[BangumiArchive] 成功加载subject-episode映射，共 {len(self._subject_episode_map)} 个番剧")
        except (FileNotFoundError, struct.error) as e:
            print(f"[BangumiArchive] 加载subject-episode映射文件失败: {e}")
            self._subject_episode_map = None

    def get_subject_episodes(self, subject_id: int) -> List[dict]:
        """
        获取指定番剧的所有剧集信息
        
        :param subject_id: 番剧ID
        :return: 番剧的所有剧集列表
        """
        if not self.exists():
            print(f"[BangumiArchive] 离线数据库不存在，无法查询subject_id为 {subject_id} 的剧集信息")
            return []
            
        # 尝试使用索引映射文件进行快速查询
        self._load_subject_episode_map()
        if self._subject_episode_map and subject_id in self._subject_episode_map:
            episode_ids = self._subject_episode_map[subject_id]
            print(f"[BangumiArchive] 使用索引映射查询到subject_id为 {subject_id} 的 {len(episode_ids)} 个剧集ID")
            # 根据episode_id获取详细信息
            episodes = []
            for episode_id in episode_ids:
                episode = self.get_episode(episode_id)
                if episode:
                    episodes.append(episode)
            print(f"[BangumiArchive] 成功从离线数据库查询到subject_id为 {subject_id} 的 {len(episodes)} 个剧集信息")
            return episodes
            
        # 如果没有映射文件或映射中没有该subject_id，回退到全表扫描方式
        print(f"[BangumiArchive] 未找到subject_id为 {subject_id} 的索引映射，使用全表扫描方式查询")
        all_episodes = self.episode.get_all_items()
        subject_episodes = [ep for ep in all_episodes if ep.get("subject_id") == subject_id]
        print(f"[BangumiArchive] 全表扫描查询到subject_id为 {subject_id} 的 {len(subject_episodes)} 个剧集信息")
        return subject_episodes
        
