import json
import zipfile
import struct
import requests
import shutil
from pathlib import Path
from typing import Dict, Any, Callable
from app.media.bangumi_archive import BangumiArchive
from app.helper.bangumi_archive_helper import BangumiArchiveHelper


class BangumiArchiveUpdater:
    """
    Bangumi Archive数据更新类
    用于从GitHub下载最新数据并更新本地Archive
    """
    
    ARCHIVE_RELEASE_URL = "https://raw.githubusercontent.com/bangumi/Archive/master/aux/latest.json"
    CACHE_FILE = "archive_cache.zip"
    CACHE_INFO_FILE = "cache_info.json"
    
    def __init__(self, archive_path: str = None):
        """
        初始化Archive更新器
        
        :param archive_path: Archive数据存储路径
        """
        if archive_path is None:
            # 默认存储在与media.db相同的目录下
            archive_path = BangumiArchiveHelper()._base_path
        
        self.archive_path = Path(archive_path)
        self.temp_path = self.archive_path / "temp"
        self.cache_file_path = self.archive_path / self.CACHE_FILE
        self.cache_info_path = self.archive_path / self.CACHE_INFO_FILE
        self.archive = BangumiArchive()
        
        # 确保目录存在
        self.archive_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
    def get_latest_archive_meta(self) -> Dict[str, Any]:
        """
        获取最新的Archive元数据
        
        :return: Archive元数据
        :raises: Exception 当无法获取元数据时抛出异常
        """
        try:
            response = requests.get(self.ARCHIVE_RELEASE_URL, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"无法获取Archive元数据: {str(e)}")
            
    def download_and_update(self, progress_callback: Callable[[int], None] = None):
        """
        下载并更新Archive数据
        
        :param progress_callback: 进度回调函数，接收一个0-100的整数参数
        """
        try:
            # 获取最新Archive信息
            if progress_callback:
                progress_callback(5)
                
            archive_meta = self.get_latest_archive_meta()
            download_url = archive_meta.get("browser_download_url")
            file_name = archive_meta.get("name", "")
            
            if not download_url:
                raise Exception("无法获取下载链接")
            
            # 清理临时zip路径
            temp_zip_path = self.temp_path / "archive.zip"
            if temp_zip_path.exists():
                temp_zip_path.unlink()
            
            # 检查缓存文件是否存在且版本匹配
            use_cache = False
            if self.cache_file_path.exists() and self.cache_info_path.exists():
                cached_info = self._get_cached_info()
                if cached_info.get("name") == file_name:
                    print(f"使用缓存文件，文件名: {file_name}")
                    try:
                        shutil.copy2(self.cache_file_path, temp_zip_path)
                        if progress_callback:
                            progress_callback(50)
                        use_cache = True
                    except Exception as e:
                        print(f"使用缓存失败: {e}，重新下载")
                        # 清理损坏的缓存
                        self.cache_file_path.unlink(missing_ok=True)
                        self.cache_info_path.unlink(missing_ok=True)
            
            # 如果不能使用缓存，则下载新文件
            if not use_cache:
                print(f"开始下载新版本: {file_name}")
                self._download_file(download_url, temp_zip_path, progress_callback)
                # 下载成功后更新缓存
                try:
                    shutil.copy2(temp_zip_path, self.cache_file_path)
                except Exception as e:
                    print(f"保存缓存失败: {e}")
            
            # 更新缓存信息
            self._save_cached_info(archive_meta)
            
            # 解压文件
            if progress_callback:
                progress_callback(50)
                
            print("正在解压Archive数据...")
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_path)
            
            # 删除临时zip文件
            temp_zip_path.unlink(missing_ok=True)
            
            # 为每个数据文件生成索引
            if progress_callback:
                progress_callback(60)
                
            data_files = ["subject.jsonlines", "person.jsonlines", "character.jsonlines", "episode.jsonlines"]
            for i, filename in enumerate(data_files):
                file_path = self.temp_path / filename
                if file_path.exists():
                    self._generate_index(file_path)
                    
                if progress_callback:
                    progress = 60 + int(30 * (i + 1) / len(data_files))
                    progress_callback(progress)
            
            # 生成subject-episode映射文件
            self._generate_subject_episode_map()
            
            # 替换现有文件
            if progress_callback:
                progress_callback(90)
                
            print("正在替换现有数据文件...")
            for filename in data_files:
                temp_file_path = self.temp_path / filename
                temp_index_path = self.temp_path / f"{filename.split('.')[0]}.idx"
                target_file_path = self.archive_path / filename
                target_index_path = self.archive_path / f"{filename.split('.')[0]}.idx"
                
                # 替换数据文件
                if temp_file_path.exists():
                    if target_file_path.exists():
                        target_file_path.unlink()
                    shutil.move(str(temp_file_path), str(target_file_path))
                
                # 替换索引文件
                if temp_index_path.exists():
                    if target_index_path.exists():
                        target_index_path.unlink()
                    shutil.move(str(temp_index_path), str(target_index_path))
                
            # 替换subject-episode映射文件
            temp_map_path = self.temp_path / "subject_episode.map"
            target_map_path = self.archive_path / "subject_episode.map"
            if temp_map_path.exists():
                if target_map_path.exists():
                    target_map_path.unlink()
                shutil.move(str(temp_map_path), str(target_map_path))
            
            # 清理临时目录
            self._clean_temp_dir()
            
            if progress_callback:
                progress_callback(100)
                
            print("Archive数据更新完成")
            return True
            
        except Exception as e:
            # 清理临时文件
            self._clean_temp_dir()
            raise Exception(f"Archive数据更新失败: {str(e)}")
            
    def _download_file(self, download_url: str, temp_zip_path: Path, progress_callback: Callable[[int], None] = None):
        """
        下载文件
        
        :param download_url: 下载链接
        :param temp_zip_path: 临时文件路径
        :param progress_callback: 进度回调函数
        """
        print(f"正在下载Archive数据: {download_url}")
        response = requests.get(download_url, timeout=300, stream=True)
        response.raise_for_status()
        
        with open(temp_zip_path, 'wb') as f:
            total_length = response.headers.get('content-length')
            
            if total_length is None:  # 没有Content-Length header
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    if progress_callback and total_length > 0:
                        progress = 10 + int(40 * dl / total_length)
                        progress_callback(progress)
                        
    def _get_cached_info(self) -> Dict[str, Any]:
        """
        获取缓存文件的信息
        
        :return: 缓存信息字典
        """
        if self.cache_info_path.exists():
            try:
                with open(self.cache_info_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
        
    def _save_cached_info(self, archive_meta: Dict[str, Any]):
        """
        保存缓存文件的信息
        
        :param archive_meta: Archive元数据
        """
        try:
            with open(self.cache_info_path, 'w', encoding='utf-8') as f:
                json.dump(archive_meta, f, ensure_ascii=False, indent=2)
        except:
            pass
            
    def _generate_index(self, file_path: Path):
        """
        为数据文件生成索引文件
        
        :param file_path: 数据文件路径
        """
        print(f"正在为 {file_path.name} 生成索引...")
        
        if not file_path.exists():
            return
            
        # 获取最后一行的ID以确定索引大小
        last_id = 0
        # 修复编码错误问题：使用二进制模式读取文件，然后正确解码
        try:
            with open(file_path, 'rb') as f:
                # 读取最后几行以找到最后一个ID
                f.seek(0, 2)  # 移动到文件末尾
                file_size = f.tell()
                # 从末尾读取64KB来查找最后一个ID
                start_pos = max(0, file_size - 64 * 1024)
                f.seek(start_pos)
                raw_data = f.read()
                # 使用errors='ignore'处理解码错误
                data = raw_data.decode('utf-8', errors='ignore')
                
                # 查找最后的ID
                lines = data.split('\n')
                for line in reversed(lines):
                    if '"id"' in line:
                        try:
                            obj = json.loads(line)
                            if 'id' in obj:
                                last_id = max(last_id, obj['id'])
                        except:
                            continue
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return
            
        # 确定索引大小
        index_size = 1
        if last_id >= 256:
            index_size = 2
        if last_id >= 65536:
            index_size = 4
            
        # 创建索引文件
        index_file_path = file_path.with_suffix('.idx')
        # 使用二进制模式写入索引文件
        index_file = open(index_file_path, 'wb')
        
        # 写入索引大小
        index_file.write(struct.pack('B', index_size))
        
        # 为每个记录生成索引
        try:
            with open(file_path, 'rb') as f:  # 使用二进制模式读取
                position = 0
                raw_line = f.readline()
                while raw_line:
                    try:
                        # 使用errors='ignore'处理可能的解码错误
                        line = raw_line.decode('utf-8', errors='ignore').strip()
                        if line:  # 确保行不为空
                            # 查找ID
                            obj = json.loads(line)
                            if 'id' in obj:
                                record_id = obj['id']
                                # 定位到索引位置
                                index_file.seek(1 + record_id * index_size)
                                # 写入偏移量
                                if index_size == 1:
                                    index_file.write(struct.pack('B', position))
                                elif index_size == 2:
                                    index_file.write(struct.pack('<H', position))
                                else:
                                    index_file.write(struct.pack('<I', position))
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        # 忽略无法解析的行
                        pass
                    except Exception as e:
                        # 忽略其他异常
                        pass
                    
                    # 更新位置
                    position += len(raw_line)
                    raw_line = f.readline()
        except Exception as e:
            print(f"生成索引时出错: {e}")
            raise
        finally:
            if 'index_file' in locals():
                index_file.close()
            
        print(f"{file_path.name} 索引生成完成")

    def _generate_subject_episode_map(self):
        """
        生成subject-episode映射文件，用于提高根据subject_id查询剧集的性能
        """
        print("正在生成subject-episode映射文件...")
        
        try:
            # 创建映射字典
            subject_episode_map = {}
            
            # 读取episode数据文件
            episode_file_path = self.temp_path / "episode.jsonlines"
            if not episode_file_path.exists():
                print("episode.jsonlines文件不存在，无法生成映射文件")
                return False
                
            # 遍历所有剧集
            with open(episode_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        episode = json.loads(line)
                        subject_id = episode.get("subject_id")
                        episode_id = episode.get("id")
                        
                        # 确保subject_id和episode_id都存在
                        if subject_id is not None and episode_id is not None:
                            # 确保subject_id和episode_id都是整数类型
                            subject_id = int(subject_id)
                            episode_id = int(episode_id)
                            
                            if subject_id not in subject_episode_map:
                                subject_episode_map[subject_id] = []
                            subject_episode_map[subject_id].append(episode_id)
                    except (json.JSONDecodeError, ValueError, TypeError) as e:
                        print(f"解析第{line_num}行时出错: {e}")
                        continue
            
            # 写入映射文件到临时目录
            map_file_path = self.temp_path / "subject_episode.map"
            print(f"正在写入映射文件，共 {len(subject_episode_map)} 个番剧")
            
            with open(map_file_path, 'wb') as map_file:
                for subject_id, episode_ids in subject_episode_map.items():
                    # 写入subject_id (4字节，小端序)
                    map_file.write(struct.pack('<I', subject_id))
                    # 写入episode数量 (2字节，小端序)
                    map_file.write(struct.pack('<H', len(episode_ids)))
                    # 写入episode_id列表 (每个4字节，小端序)
                    for episode_id in episode_ids:
                        map_file.write(struct.pack('<I', episode_id))
            
            print("subject-episode映射文件生成完成")
            return True
            
        except Exception as e:
            print(f"生成subject-episode映射文件失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _clean_temp_dir(self):
        """
        清理临时目录
        """
        try:
            if self.temp_path.exists():
                shutil.rmtree(self.temp_path)
                self.temp_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"清理临时目录失败: {e}")
    def update_archive(self):
        """
        更新Bangumi Archive数据
        
        :return: 更新结果，成功返回True，失败返回False
        """
        try:
            self.download_and_update()
            return True
        except Exception as e:
            print(f"更新Bangumi Archive数据失败: {str(e)}")
            return False