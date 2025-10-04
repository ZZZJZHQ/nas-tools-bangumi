import json
import time
from datetime import datetime
from threading import Lock
import requests
from app.media.bangumi_archive import BangumiArchive
from app.utils import RequestUtils
from app.utils.types import MediaType
from config import Config
import log


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
            
    @classmethod
    def instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

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
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            subject = self.archive.get_subject(int(bid))
            if subject:
                return subject
        
        # 否则从在线API获取
        try:
            return self.__invoke(self._urls["detail"] % bid)
        except Exception as e:
            # 网络异常时，如果启用了Archive则尝试从Archive获取
            log.warn(f"【Bangumi】网络请求失败：{e}，尝试从本地Archive获取数据")
            if self.enable_archive and self.archive.exists():
                subject = self.archive.get_subject(int(bid))
                if subject:
                    log.info(f"【Bangumi】从本地Archive成功获取番剧ID {bid} 的信息")
                    return subject
                else:
                    log.warn(f"【Bangumi】本地Archive中未找到番剧ID {bid} 的信息")
            
            # 重新抛出异常
            raise e

    def persons(self, subject_id):
        """
        获取条目制作人员
        """
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            persons = self.archive.get_subject_persons(int(subject_id))
            if persons:
                return persons
                
        return self.__invoke(self._urls["credits"] % subject_id)

    def characters(self, subject_id):
        """
        获取条目角色列表
        """
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            characters = self.archive.get_subject_characters(int(subject_id))
            if characters:
                return characters
                
        return self.__invoke(self._urls["characters"] % subject_id)

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
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            person = self.archive.get_person(int(person_id))
            if person:
                return person
                
        # 否则从在线API获取
        return self.__invoke(self._urls["person_detail"] % person_id)

    def get_bangumi_character_detail(self, character_id):
        """
        获取角色详情
        """
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            character = self.archive.get_character(int(character_id))
            if character:
                return character
                
        # 否则从在线API获取
        return self.__invoke(self._urls["character_detail"] % character_id)

    def get_bangumi_person_credits(self, person_id):
        """
        获取人物参演作品
        """
        ret = self.__invoke(self._urls["person_credits"] % person_id)
        if ret:
            return ret
        return []

    def get_bangumi_character_credits(self, character_id):
        """
        获取角色参演作品
        """
        ret = self.__invoke(self._urls["character_credits"] % character_id)
        if ret:
            return ret
        return []

    def search_bangumi(self, keyword, filters=None):
        """
        搜索番剧 (优先使用v0 API)
        :param keyword: 搜索关键词
        :param filters: 过滤条件，例如 {"type": [2]} 限制为动画类型
        """
        # 优先使用v0 API
        if filters is not None:
            params = {
                "keyword": keyword
            }
            
            if filters:
                params["filter"] = filters
                
            ret = self.__post(self._urls["search"], **params)
            if ret:
                return ret.get("data") or []
        return []

    def get_bangumi_episodes(self, bid, episode_type=None, limit=100, offset=0):
        """
        获取番剧剧集 (使用v0 API)
        :param bid: 番剧ID
        :param episode_type: 剧集类型 (可选)
        :param limit: 返回数据量限制
        :param offset: 偏移量
        """
        params = {
            "subject_id": bid,
            "limit": limit,
            "offset": offset
        }
        
        if episode_type is not None:
            params["type"] = episode_type
            
        ret = self.__invoke(self._urls["episodes"], **params)
        if ret:
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