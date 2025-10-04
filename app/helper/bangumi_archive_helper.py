import os
import json
from app.utils.commons import SingletonMeta
from app.utils import RequestUtils, PathUtils
from app.helper import DbHelper
from config import Config
import log
import threading
import time
import datetime


class BangumiArchiveHelper(metaclass=SingletonMeta):
    
    def __init__(self):
        self._dbhelper = DbHelper()
        self._config = Config()
        self._update_progress = {}  # 存储更新进度，支持多任务跟踪
        self._last_status_update = 0  # 上次状态更新时间
        self._cached_status = None  # 缓存的状态信息
        self._log_file = None  # 日志文件路径
        self._max_log_entries = 10  # 最大日志条目数
    
    def get_config(self):
        """
        获取Bangumi Archive配置
        """
        config = self._config.get_config('bangumi_archive') or {}
        # 同时也从bangumi配置中获取access_token
        bangumi_config = self._config.get_config('bangumi') or {}
        if 'access_token' not in config and 'access_token' in bangumi_config:
            config['access_token'] = bangumi_config['access_token']
        
        return config
    
    def save_config(self, data):
        """
        保存Bangumi Archive配置
        """
        try:
            # 获取现有的bangumi配置
            bangumi_config = self._config.get_config('bangumi') or {}
            
            # 准备要更新的配置
            archive_config = self._config.get_config('bangumi_archive') or {}
            
            # 更新Archive配置
            if data:
                archive_config.update({
                    "enabled": data.get("enabled"),
                    "cron": data.get("cron")
                })
                
                # 如果提供了access_token，则更新到bangumi配置中
                if "access_token" in data and data["access_token"] is not None:
                    bangumi_config["access_token"] = data["access_token"]
            
            # 保存配置
            config_data = self._config.get_config()
            config_data.update({
                "bangumi_archive": archive_config,
                "bangumi": bangumi_config
            })
            self._config.save_config(config_data)
            return True
        except Exception as e:
            log.error(f"保存Bangumi Archive配置出错：{e}")
            return False
    
    def _get_log_file_path(self):
        """
        获取日志文件路径
        """
        from config import Config as AppConfig
        config_path = AppConfig().get_config_path()
        return os.path.join(config_path, "bangumi_archive", "update.log")
    
    def _manage_log_file(self, log_file_path):
        """
        管理日志文件，确保只保留最近的条目
        """
        try:
            if not os.path.exists(log_file_path):
                return
            
            # 读取所有日志行
            with open(log_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # 如果行数超过了最大限制，则只保留最近的条目
            if len(lines) > self._max_log_entries:
                # 保留最后_max_log_entries行
                lines_to_keep = lines[-self._max_log_entries:]
                
                # 写回文件
                with open(log_file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines_to_keep)
        except Exception as e:
            log.error(f"管理Bangumi Archive日志文件出错：{e}")
    
    def _write_log(self, operation, status, message=""):
        """
        写入操作日志
        """
        try:
            log_file_path = self._get_log_file_path()
            log_dir = os.path.dirname(log_file_path)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {operation} - {status}"
            if message:
                log_entry += f" - {message}"
            log_entry += "\n"
            
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
            
            # 管理日志文件大小
            self._manage_log_file(log_file_path)
        except Exception as e:
            log.error(f"写入Bangumi Archive日志出错：{e}")
    
    def _read_logs(self, limit=10):
        """
        读取最新的操作日志
        """
        try:
            log_file_path = self._get_log_file_path()
            if not os.path.exists(log_file_path):
                return []
            
            logs = []
            with open(log_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # 取最新的limit条日志
                for line in lines[-limit:]:
                    logs.append(line.strip())
            
            # 倒序返回，最新的在前面
            return logs[::-1]
        except Exception as e:
            log.error(f"读取Bangumi Archive日志出错：{e}")
            return []
    
    def get_status(self):
        """
        获取Archive状态信息
        
        :return: 状态信息
        """
        # 获取Archive路径
        from config import Config as AppConfig
        from pathlib import Path
        archive_path = Path(os.path.join(AppConfig().get_config_path(), "bangumi_archive"))
        cache_file_path = archive_path / "archive_cache.zip"
        cache_info_path = archive_path / "cache_info.json"
        
        status = {
            "size": "-",
            "time": "-",
        }
        
        if archive_path.exists():
            # 获取目录大小
            try:
                size = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                          for dirpath, dirnames, filenames in os.walk(archive_path) 
                          for filename in filenames 
                          if filename not in ["archive_cache.zip", "cache_info.json"] and not filename.endswith('.idx'))  # 排除缓存文件和索引文件
                status["size"] = f"{size / (1024*1024):.2f} MB"
            except Exception as e:
                status["size"] = "计算失败"
            
            # 获取最后更新时间，从缓存信息中读取updated_at字段
            try:
                if cache_info_path.exists():
                    with open(cache_info_path, 'r', encoding='utf-8') as f:
                        cache_info = json.load(f)
                        updated_at = cache_info.get("updated_at")
                        if updated_at:
                            # 转换ISO时间格式为本地时间格式
                            from datetime import datetime
                            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                            status["time"] = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                status["time"] = "读取失败"
        
        return status
    
    def get_logs(self, limit=10):
        """
        获取更新日志
        """
        return self._read_logs(limit)
    
    def set_progress(self, progress: int, task_id: str = "default"):
        """
        设置更新进度
        """
        self._update_progress[task_id] = progress
        log.info(f"Bangumi Archive更新进度 [{task_id}]: {progress}%")
    
    def get_progress(self, task_id: str = "default"):
        """
        获取更新进度
        """
        return self._update_progress.get(task_id, 0)
    
    def _progress_callback(self, progress: int, task_id: str = "default"):
        """
        进度回调函数
        """
        self.set_progress(progress, task_id)
    
    def update_archive(self, task_id: str = "default"):
        """
        更新Bangumi Archive数据
        """
        self._write_log("手动更新", "开始")
        try:
            # 重置进度
            self.set_progress(0, task_id)
            
            from app.media.bangumi_archive_updater import BangumiArchiveUpdater
            updater = BangumiArchiveUpdater()
            
            # 定义进度回调
            def progress_callback(progress):
                self._progress_callback(progress, task_id)
            
            result = updater.download_and_update(progress_callback)
            self.set_progress(100 if result else -1, task_id)  # 成功设为100%，失败为-1
            
            # 记录日志
            if result:
                self._write_log("手动更新", "成功")
            else:
                self._write_log("手动更新", "失败", "下载或更新过程出错")
            
            # 更新完成后清除缓存，确保下次获取状态时能获取最新数据
            self._cached_status = None
            
            return result
        except Exception as e:
            log.error(f"更新Bangumi Archive数据出错：{e}")
            self.set_progress(-1, task_id)  # -1表示失败
            
            # 记录错误日志
            self._write_log("手动更新", "失败", str(e))
            
            # 出错时也清除缓存
            self._cached_status = None
            return False
    
    def clear_data(self):
        """
        清空Bangumi Archive数据，路径固定为配置目录下的 bangumi_archive
        保留缓存文件，只删除jsonlines数据文件
        """
        self._write_log("清空数据", "开始")
        try:
            from config import Config as AppConfig
            from app.media.bangumi_archive_updater import BangumiArchiveUpdater
            path = os.path.join(AppConfig().get_config_path(), "bangumi_archive")
            if os.path.exists(path):
                # 只删除jsonlines数据文件和索引文件，保留缓存文件
                for file in os.listdir(path):
                    file_path = os.path.join(path, file)
                    # 删除数据文件和索引文件
                    if file.endswith((".jsonlines", ".idx")):
                        os.remove(file_path)
            
            # 记录日志
            self._write_log("清空数据", "成功")
            
            # 清除缓存
            self._cached_status = None
            return True
        except Exception as e:
            log.error(f"清空Bangumi Archive数据出错：{e}")
            # 记录错误日志
            self._write_log("清空数据", "失败", str(e))
            return False