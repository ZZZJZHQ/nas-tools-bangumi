import log
import pickle
from typing import Optional, Dict, Any
from app.utils.redis_store import RedisStore
from app.utils.types import MediaType
from app.helper.thread_helper import ThreadHelper

class TMDBCache:
    def __init__(self):
        self.redis = RedisStore()

    def get_tmdb_info(self, mtype: MediaType, tmdbid: str, language: str = None) -> Optional[Any]:
        """从缓存获取TMDB信息，支持字典和对象"""
        if mtype == MediaType.ANIME:
            mtype = MediaType.TV
        cache_key = f"tmdb:{mtype.value}:{tmdbid}:{language or 'default'}"
        type = "TMDB"
        if language == 'bangumi':
             cache_key = f'{tmdbid}:{language}'
             type = "BANGUMI"
        
        cached = self.redis.get(cache_key)
        if cached:
            try:
                result = pickle.loads(cached)
                log.debug(f"从Redis缓存命中{type}信息: {cache_key}")
                return result
            except:
                log.debug(f"从Redis缓存命中{type}信息(原始值): {cache_key}")
                return cached
        return None

    def set_tmdb_info(self, mtype: MediaType, tmdbid: str, info: Any, 
                     language: str = None, ttl: int = 3600) -> None:
        """缓存TMDB信息，支持字典和对象，默认1小时"""
        if mtype == MediaType.ANIME:
            mtype = MediaType.TV

        cache_key = f"tmdb:{mtype.value}:{tmdbid}:{language or 'default'}"
        if language == 'bangumi':
             cache_key = f'{tmdbid}:{language}'
        # 其他类型则序列化存储
        value = pickle.dumps(info)
        self.redis.set(cache_key, value, ex=ttl)
        log.debug(f"已缓存{'BANGUMI' if language == 'bangumi' else 'TMDB'}信息到Redis: {cache_key}")

    def set_tmdb_info_async(self, mtype: MediaType, tmdbid: str, info: Any, 
                           language: str = None, ttl: int = 3600) -> None:
        """异步缓存TMDB信息，支持字典和对象，默认1小时"""
        def _set_cache():
            try:
                self.set_tmdb_info(mtype, tmdbid, info, language, ttl)
            except Exception as e:
                log.error(f"异步缓存TMDB信息失败: {e}")
        
        # 使用统一的线程管理
        ThreadHelper().start_thread(_set_cache, ())

    def get_media_info(self, title: str, year: str = None, 
                      mtype: MediaType = None) -> Optional[Any]:
        """从缓存获取媒体信息，支持字典和对象"""
        if mtype == MediaType.ANIME:
            mtype = MediaType.TV
        cache_key = self._get_media_cache_key(title, year, mtype)
        cached = self.redis.get(cache_key)
        if cached:
            try:
                # 尝试反序列化对象
                result = pickle.loads(cached)
                log.debug(f"从Redis缓存命中媒体信息: {cache_key}")
                return result
            except:
                # 如果反序列化失败，直接返回原始值(兼容旧字典数据)
                log.debug(f"从Redis缓存命中媒体信息(原始值): {cache_key}")
                return cached
        return None

    def set_media_info(self, title: str, info: Any, 
                      year: str = None, mtype: MediaType = None, 
                      ttl: int = 3600*12) -> None:
        """缓存媒体信息，支持字典和对象，默认1小时"""
        if mtype == MediaType.ANIME:
            mtype = MediaType.TV
        cache_key = self._get_media_cache_key(title, year, mtype)
        value = pickle.dumps(info)
        self.redis.set(cache_key, value, ex=ttl)
        log.debug(f"已缓存媒体信息到Redis: {cache_key}")

    def set_media_info_async(self, title: str, info: Any, 
                            year: str = None, mtype: MediaType = None, 
                            ttl: int = 3600*12) -> None:
        """异步缓存媒体信息，支持字典和对象，默认1小时"""
        def _set_cache():
            try:
                self.set_media_info(title, info, year, mtype, ttl)
                log.debug(f"使用异步缓存")
            except Exception as e:
                log.error(f"异步缓存媒体信息失败: {e}")
        
        # 使用统一的线程管理
        ThreadHelper().start_thread(_set_cache, ())

    def _get_media_cache_key(self, title: str, year: str = None, 
                           mtype: MediaType = None) -> str:
        """生成媒体信息缓存键"""
        parts = ["media", title]
        if year:
            parts.append(year)
        if mtype:
            parts.append(mtype.value)
        return ":".join(parts)

    def clear_tmdb_cache(self, tmdbid: str) -> None:
        """清除指定TMDB ID的所有缓存"""
        pattern = f"tmdb:*:{tmdbid}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
            log.debug(f"已清除TMDB ID {tmdbid} 的所有缓存")

    def clear_media_cache(self, title: str) -> None:
        """清除指定标题的所有媒体缓存"""
        pattern = f"media:{title}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
            log.debug(f"已清除标题 {title} 的所有媒体缓存")