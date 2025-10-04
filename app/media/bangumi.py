import json
import time
from datetime import datetime
from threading import Lock
import requests
from app.media.bangumi_archive import BangumiArchive
from app.utils import RequestUtils
from app.utils.types import MediaType
from app.utils.redis_store import RedisStore
import pickle
import log
from config import Config


class Bangumi(object):
    """
    Bangumi追番 (基于v0 API实现)
    """
    _instance = None
    _lock = Lock()

    def __init__(self):
        self._session = None
        # 读取配置
        config = Config()
        bangumi_conf = config.get_config("bangumi")
        if bangumi_conf:
            self.enable_archive = bangumi_conf.get("enable_archive", False)
            self.archive_path = bangumi_conf.get("archive_path")
            # 获取access_token配置（用户Token，用于访问私有数据）
            self.access_token = bangumi_conf.get("access_token")
        else:
            self.enable_archive = False
            self.archive_path = None
            self.access_token = None
            
        # 初始化Archive
        if self.enable_archive and self.archive_path:
            self.archive = BangumiArchive(self.archive_path)
        else:
            self.archive = BangumiArchive()
            
        # 初始化Redis缓存
        self.redis = RedisStore()
        
    @classmethod
    def instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    def __get_cache(self, key):
        """获取缓存"""
        try:
            cached = self.redis.get(key)
            if cached:
                result = pickle.loads(cached)
                log.debug(f"【Bangumi】从缓存命中: {key}")
                return result
        except Exception as e:
            log.error(f"【Bangumi】缓存读取失败: {e}")
        return None

    def __set_cache(self, key, data, ttl=3600):
        """设置缓存，默认1小时"""
        try:
            value = pickle.dumps(data)
            self.redis.set(key, value, ex=ttl)
            log.debug(f"【Bangumi】设置缓存: {key}")
        except Exception as e:
            log.error(f"【Bangumi】缓存设置失败: {e}")

    def __get_headers(self):
        """
        获取请求头
        """
        headers = {
            "User-Agent": "zzzjzhq/nas-tools-bangumi(https://github.com/ZZZJZHQ/nas-tools-bangumi)"
        }
        
        # 添加用户access_token认证头（如果存在，用于访问私有数据）
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def __invoke(self, url, **kwargs):
        """
        bangumi请求
        """
        try:
            if not self._session:
                self._session = requests.Session()
            if not url.startswith("http"):
                url = "https://api.bgm.tv/%s" % url
                
            headers = self.__get_headers()
                
            resp = self._session.get(url, params=kwargs, timeout=10, headers=headers)
            if resp.status_code == 404:
                return None
            if resp:
                return resp.json()
        except Exception as e:
            log.error(f"【Bangumi】请求失败：{e}")
        return None

    def __post(self, url, **kwargs):
        """
        bangumi post请求
        """
        try:
            if not self._session:
                self._session = requests.Session()
            if not url.startswith("http"):
                url = "https://api.bgm.tv/%s" % url
            headers = self.__get_headers()
            headers["Content-Type"] = "application/json"
            
            resp = self._session.post(url, json=kwargs, headers=headers, timeout=10)
            if resp.status_code == 404:
                return None
            if resp:
                return resp.json()
        except Exception as e:
            log.error(f"【Bangumi】请求失败：{e}")
        return None

    _urls = {
        "calendar": "calendar",
        "detail": "v0/subjects/%s",
        "credits": "v0/subjects/%s/persons",
        "subjects": "v0/subjects/%s/subjects",
        "characters": "v0/subjects/%s/characters",
        "person_detail": "v0/persons/%s",
        "character_detail": "v0/characters/%s",
        "person_credits": "v0/persons/%s/subjects",
        "character_credits": "v0/characters/%s/subjects",
        "search": "v0/search/subjects",
        "episodes": "v0/episodes",
        "episode_detail": "v0/episodes/%s"
    }

    def calendar(self):
        """
        获取每日放送
        """
        return self.__invoke(self._urls["calendar"], _ts=datetime.strftime(datetime.now(), '%Y%m%d'))

    def detail(self, bid):
        """
        获取番剧详情
        优先从本地Archive查询数据，如果不存在则使用在线API
        在网络异常时自动回退到本地Archive（如果启用）
        """
        # 检查缓存
        cache_key = f"bangumi:detail:{bid}"
        cached_result = self.__get_cache(cache_key)
        if cached_result:
            return cached_result
            
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            subject = self.archive.get_subject(int(bid))
            if subject:
                # 缓存结果
                self.__set_cache(cache_key, subject)
                return subject
        
        # 否则从在线API获取
        try:
            result = self.__invoke(self._urls["detail"] % bid)
            if result:
                # 缓存结果
                self.__set_cache(cache_key, result)
            return result
        except Exception as e:
            # 网络异常时，如果启用了Archive则尝试从Archive获取
            log.warn(f"【Bangumi】网络请求失败：{e}，尝试从本地Archive获取数据")
            if self.enable_archive and self.archive.exists():
                subject = self.archive.get_subject(int(bid))
                if subject:
                    log.info(f"【Bangumi】从本地Archive成功获取番剧ID {bid} 的信息")
                    # 缓存结果
                    self.__set_cache(cache_key, subject)
                    return subject
            
            # 重新抛出异常
            raise e

    def persons(self, subject_id):
        """
        获取条目制作人员
        """
        # 检查缓存
        cache_key = f"bangumi:persons:{subject_id}"
        cached_result = self.__get_cache(cache_key)
        if cached_result:
            return cached_result
            
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            persons = self.archive.get_subject_persons(int(subject_id))
            if persons:
                # 缓存结果
                self.__set_cache(cache_key, persons)
                return persons
                
        result = self.__invoke(self._urls["credits"] % subject_id)
        if result:
            # 缓存结果
            self.__set_cache(cache_key, result)
        return result

    def characters(self, subject_id):
        """
        获取条目角色列表
        """
        # 检查缓存
        cache_key = f"bangumi:characters:{subject_id}"
        cached_result = self.__get_cache(cache_key)
        if cached_result:
            return cached_result
            
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            characters = self.archive.get_subject_characters(int(subject_id))
            if characters:
                # 处理每个角色的简体中文名
                for character in characters:
                    character_id = character.get("id")
                    if character_id:
                        # 从离线数据库获取详细信息
                        char_detail = self.archive.get_character(character_id)
                        if char_detail:
                            # 使用简体中文名替换角色名
                            infobox = char_detail.get("infobox", [])
                            for item in infobox:
                                if item.get("key") == "简体中文名":
                                    character["name"] = item.get("value", character.get("name"))
                                    break
                # 缓存结果
                self.__set_cache(cache_key, characters, ttl=1800)  # 30分钟
                return characters
                
        result = self.__invoke(self._urls["characters"] % subject_id)
        if result:
            # 处理每个角色的简体中文名
            for character in result:
                character_id = character.get("id")
                if character_id:
                    # 从在线API获取详细信息
                    char_detail = self.get_bangumi_character_detail(character_id)
                    if char_detail:
                        # 使用简体中文名替换角色名
                        infobox = char_detail.get("infobox", [])
                        for item in infobox:
                            if item.get("key") == "简体中文名":
                                character["name"] = item.get("value", character.get("name"))
                                break
            # 缓存结果，角色信息缓存时间可以稍短一些
            self.__set_cache(cache_key, result, ttl=1800)  # 30分钟
        return result

    @staticmethod
    def __dict_item(item, weekday):
        """
        转换为字典
        """
        bid = item.get("id")
        detail = item.get("url")
        title = item.get("name_cn") or item.get("name")
        air_date = item.get("air_date")
        rating = item.get("rating")
        if rating:
            score = rating.get("score")
        else:
            score = 0
        images = item.get("images")
        if images:
            image = images.get("large")
        else:
            image = ''
        return {
            'id': "BG:%s" % bid,
            'orgid': bid,
            'title': title,
            'year': air_date[:4] if air_date else "",
            'type': 'TV',
            'media_type': MediaType.TV.value,
            'vote': score,
            'image': image,
            'url': detail,
            'weekday': weekday
        }

    def get_bangumi_calendar(self, page=1, week=None):
        """
        获取每日放送
        """
        infos = self.calendar()
        if not infos:
            return []
        start_pos = (int(page) - 1) * 30
        ret_list = []
        pos = 0
        for info in infos:
            weeknum = info.get("weekday", {}).get("id")
            if week and int(weeknum) != int(week):
                continue
            weekday = info.get("weekday", {}).get("cn")
            items = info.get("items")
            for item in items:
                dict_item = self.__dict_item(item, weekday)
                # 过滤掉image为空的数据
                if dict_item['image']:
                    if pos >= start_pos:
                        ret_list.append(dict_item)
                    pos += 1
                    if pos >= start_pos + 30:
                        break

        return ret_list

    def get_bangumi_detail(self, bid):
        """
        获取番剧详情
        """
        return self.detail(bid)

    def get_bangumi_credits(self, bid):
        """
        获取番剧制作人员
        """
        return self.persons(bid)

    def get_bangumi_characters(self, bid):
        """
        获取番剧角色列表
        """
        return self.characters(bid)

    def get_bangumi_person_detail(self, person_id):
        """
        获取人物详情
        """
        # 检查缓存
        cache_key = f"bangumi:person_detail:{person_id}"
        cached_result = self.__get_cache(cache_key)
        if cached_result:
            return cached_result
            
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            person = self.archive.get_person(int(person_id))
            if person:
                # 缓存结果
                self.__set_cache(cache_key, person)
                return person
                
        # 否则从在线API获取
        result = self.__invoke(self._urls["person_detail"] % person_id)
        if result:
            # 缓存结果
            self.__set_cache(cache_key, result)
        return result

    def get_bangumi_character_detail(self, character_id):
        """
        获取角色详情
        """
        # 检查缓存
        cache_key = f"bangumi:character_detail:{character_id}"
        cached_result = self.__get_cache(cache_key)
        if cached_result:
            return cached_result
            
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            character = self.archive.get_character(int(character_id))
            if character:
                # 缓存结果
                self.__set_cache(cache_key, character)
                return character
                
        # 否则从在线API获取
        result = self.__invoke(self._urls["character_detail"] % character_id)
        if result:
            # 处理简体中文名
            infobox = result.get("infobox", [])
            for item in infobox:
                if item.get("key") == "简体中文名":
                    result["name"] = item.get("value", result.get("name"))
                    break
            # 缓存结果
            self.__set_cache(cache_key, result)
        return result

    def get_bangumi_person_credits(self, person_id):
        """
        获取人物参演作品
        """
        # 检查缓存
        cache_key = f"bangumi:person_credits:{person_id}"
        cached_result = self.__get_cache(cache_key)
        if cached_result:
            return cached_result
            
        ret = self.__invoke(self._urls["person_credits"] % person_id)
        if ret:
            # 缓存结果
            self.__set_cache(cache_key, ret)
            return ret
        return []

    def get_bangumi_character_credits(self, character_id):
        """
        获取角色参演作品
        """
        # 检查缓存
        cache_key = f"bangumi:character_credits:{character_id}"
        cached_result = self.__get_cache(cache_key)
        if cached_result:
            return cached_result
            
        ret = self.__invoke(self._urls["character_credits"] % character_id)
        if ret:
            # 缓存结果
            self.__set_cache(cache_key, ret)
            return ret
        return []

    def search_bangumi(self, keyword, filters=None):
        """
        搜索番剧 (优先使用v0 API)
        :param keyword: 搜索关键词
        :param filters: 过滤条件，例如 {"type": [2]} 限制为动画类型
        """
        # 检查缓存
        cache_key = f"bangumi:search:{keyword}:{hash(str(filters))}"
        cached_result = self.__get_cache(cache_key)
        if cached_result:
            return cached_result
            
        # 优先使用v0 API
        if filters is not None:
            params = {
                "keyword": keyword
            }
            
            if filters:
                params["filter"] = filters
                
            ret = self.__post(self._urls["search"], **params)
            if ret:
                result = ret.get("data") or []
                # 缓存结果，搜索结果缓存时间可以短一些
                self.__set_cache(cache_key, result, ttl=600)  # 10分钟
                return result
        return []

    def get_bangumi_episodes(self, bid, episode_type=None, limit=100, offset=0):
        """
        获取番剧剧集 (使用v0 API)
        :param bid: 番剧ID
        :param episode_type: 剧集类型 (可选)
        :param limit: 返回数据量限制
        :param offset: 偏移量
        """
        # 检查缓存
        cache_key = f"bangumi:episodes:{bid}:{episode_type}:{limit}:{offset}"
        cached_result = self.__get_cache(cache_key)
        if cached_result:
            return cached_result
            
        params = {
            "subject_id": bid,
            "limit": limit,
            "offset": offset
        }
        
        if episode_type is not None:
            params["type"] = episode_type
            
        ret = self.__invoke(self._urls["episodes"], **params)
        if ret:
            # 缓存结果
            self.__set_cache(cache_key, ret)
            return ret
        return {}

    def get_bangumi_episode_detail(self, episode_id):
        """
        获取剧集详情
        """
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            episode = self.archive.get_episode(int(episode_id))
            if episode:
                return episode
                
        # 否则从在线API获取
        return self.__invoke(self._urls["episode_detail"] % episode_id)