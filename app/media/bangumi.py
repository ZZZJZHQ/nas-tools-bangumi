from datetime import datetime
from threading import Lock
import requests
from app.media.bangumi_archive import BangumiArchive
from app.utils.types import MediaType
from app.utils.redis_store import RedisStore
from app.utils.tmdb_cache import TMDBCache
from app.helper.bangumi_archive_helper import BangumiArchiveHelper
from bgm_tv_wiki import parse

import log


class Bangumi(object):
    """
    Bangumi追番 (基于v0 API实现)
    """
    _instance = None
    _lock = Lock()

    def __init__(self):
        self._session = None
        # 使用BangumiArchiveHelper获取所有配置
        archive_helper = BangumiArchiveHelper()
        archive_config = archive_helper.get_config()
        
        # 从archive配置中获取所有配置项
        self.access_token = archive_config.get("access_token")
        self.enable_archive = archive_config.get("enabled", False)
        self.archive = BangumiArchive()
            
        # 初始化Redis缓存
        self.redis = RedisStore()
        self.cache = TMDBCache()
        
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
            "User-Agent": "zzzjzhq/nas-tools(https://github.com/zzzjzhq/nas-tools)"
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
                url = f"https://api.bgm.tv/{url}"
                
            headers = self.__get_headers()
                
            # 处理参数编码，特别是中文keyword
            encoded_kwargs = {}
            for key, value in kwargs.items():
                if isinstance(value, str):
                    # 对字符串参数进行URL编码，防止中文导致的编码问题
                    encoded_kwargs[key] = value
                else:
                    encoded_kwargs[key] = value
                    
            resp = self._session.get(url, params=encoded_kwargs, timeout=10, headers=headers)
            if resp.status_code == 404:
                return None
            if resp:
                # 检查响应内容编码
                if resp.encoding == 'ISO-8859-1':
                    # 尝试使用UTF-8解码
                    try:
                        resp.encoding = 'utf-8'
                    except:
                        pass
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
                url = f"https://api.bgm.tv/{url}"
            headers = self.__get_headers()
            headers["Content-Type"] = "application/json"
            
            resp = self._session.post(url, json=kwargs, headers=headers, timeout=10)
            if resp.status_code == 404:
                return None
            if resp:
                # 检查响应内容编码
                if resp.encoding == 'ISO-8859-1':
                    # 尝试使用UTF-8解码
                    try:
                        resp.encoding = 'utf-8'
                    except:
                        pass
                return resp.json()
        except Exception as e:
            log.error(f"【Bangumi】请求失败：{e}")
        return None
    
    def __async_cache(self, cache_key, data, ttl=600):
        """
        异步缓存ANIME
        """
        self.cache.set_tmdb_info_async(MediaType.TV, cache_key, data, "bangumi", ttl)
        
    def __get_cache(self, cache_key):
        """
        获取缓存ANIME
        """
        return self.cache.get_tmdb_info(MediaType.TV, cache_key, "bangumi")

    _urls = {
        "calendar": "calendar",
        "detail": "v0/subjects/%s",
        "subjects": "v0/subjects/%s/subjects",
        "characters": "v0/subjects/%s/characters",
        "character_detail": "v0/characters/%s",
        "search": "v0/search/subjects",
        "episodes": "v0/episodes",
        "image": "v0/subjects/%s/image"
    }

    def calendar(self):
        """
        获取每日放送
        """
        # 尝试从缓存获取
        cache_key = "calendar"
        cached = self.__get_cache(cache_key)
        if cached is not None:
            return cached
            
        result = self.__invoke(self._urls["calendar"], _ts=datetime.strftime(datetime.now(), '%Y%m%d'))
        
        # 缓存结果
        if result:
            # 异步缓存，避免阻塞
            self.__async_cache(cache_key, result, 600)
            
        return result

    def get_subject_images(self, subject_id, image_type="medium"):
        """
        获取番剧图片
        :param subject_id: 番剧ID
        :param image_type: 图片类型 (small|grid|large|medium|common)
        """
        # 尝试从缓存获取
        cache_key = f"image:{subject_id}:{image_type}"
        cached = self.__get_cache(cache_key)
        if cached is not None:
            log.info(f"【Bangumi】从缓存获取番剧图片，subject_id: {subject_id}, image_type: {image_type}")
            return cached
            
        try:
            # 确保session已初始化，与__invoke方法保持一致
            if not self._session:
                self._session = requests.Session()
                
            # 调用图片API获取重定向链接
            url = f"https://api.bgm.tv/{self._urls.get('image') % subject_id}"
            log.info(f"【Bangumi】请求番剧图片，URL: {url}, image_type: {image_type}")
            headers = self.__get_headers()
            resp = self._session.get(url, params={"type": image_type}, timeout=10, headers=headers, allow_redirects=False)
            
            if resp.status_code == 302:
                # 获取重定向地址
                image_url = resp.headers.get("Location")
                log.info(f"【Bangumi】获取番剧图片成功，subject_id: {subject_id}, image_url: {image_url}")
                # 缓存结果
                if image_url:
                    # 异步缓存，避免阻塞
                    self.__async_cache(cache_key, image_url, 3600)
                return image_url
            else:
                log.warn(f"【Bangumi】获取番剧图片失败，status_code: {resp.status_code}, subject_id: {subject_id}")
        except Exception as e:
            log.error(f"【Bangumi】获取番剧图片失败：{e}")
        return None

    def detail(self, bid):
        """
        获取番剧详情
        优先从本地Archive查询数据，如果不存在则使用在线API
        在网络异常时自动回退到本地Archive（如果启用）
        """ 
        # 尝试从缓存获取
        cache_key = f"detail:{bid}"
        cached = self.__get_cache(cache_key)
        if cached is not None:
            return cached
            
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            subject = self.archive.get_subject(int(bid))
            if subject:
                # 从在线API获取图片信息并补充到离线数据中
                images = self.get_subject_images(subject_id=bid, image_type='large')
                if images:
                    # 如果原数据中没有images字段，则创建一个
                    if "images" not in subject:
                        subject["images"] = {}
                    # 将获取到的图片链接添加到数据中
                    subject["images"]["large"] = images
                    
                # 异步缓存，避免阻塞
                self.__async_cache(cache_key, subject, 3600)
                return subject
        
        # 否则从在线API获取
        try:
            result = self.__invoke(self._urls["detail"] % bid)
            if result:
                # 异步缓存，避免阻塞
                self.__async_cache(cache_key, result, 3600)
                return result
        except Exception as e:
            # 网络异常时，如果启用了Archive则尝试从Archive获取
            log.warn(f"【Bangumi】网络请求失败：{e}，尝试从本地Archive获取数据")
            raise e

    def characters(self, subject_id):
        """
        获取条目角色列表
        """
        # 尝试从缓存获取
        cache_key = f"characters:{subject_id}"
        cached = self.__get_cache(cache_key)
        if cached is not None:
            return cached
                
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
                        if "infobox" in char_detail and isinstance(char_detail["infobox"], dict):
                            # 如果infobox已经被解析为dict对象
                            infobox = char_detail["infobox"]
                            if "简体中文名" in infobox:
                                character["name"] = infobox["简体中文名"]
                        elif "infobox" in char_detail and isinstance(char_detail["infobox"], str):
                            # 如果infobox还是字符串格式，则先解析再使用
                            try:
                                infobox = parse(char_detail["infobox"])
                                if "简体中文名" in infobox:
                                    character["name"] = infobox["简体中文名"]
                            except Exception as e:
                                log.warn(f"【Bangumi】使用bgm-tv-wiki解析在线API返回的infobox失败: {e}")
            # 缓存结果
            self.__async_cache(cache_key, result, 3600)
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
            'type': 'ANIME',
            'media_type': MediaType.ANIME.value,
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

    def get_bangumi_characters(self, bid):
        """
        获取番剧角色列表
        """
        return self.characters(bid)

    def get_bangumi_character_detail(self, character_id):
        """
        获取角色详情
        """
        # 尝试从缓存获取
        cache_key = f"character:{character_id}"
        cached = self.__get_cache(cache_key)
        if cached is not None:
            log.info(f"【Bangumi】从缓存获取角色详情，character_id: {character_id}")
            # 如果缓存数据中有infobox且是字符串格式，则解析它
            if isinstance(cached, dict) and "infobox" in cached and isinstance(cached["infobox"], str):
                try:
                    cached["infobox"] = parse(cached["infobox"])
                except Exception as e:
                    log.warn(f"【Bangumi】使用bgm-tv-wiki解析缓存中的infobox失败: {e}")
            return cached
            
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            log.info(f"【Bangumi】尝试从本地Archive获取角色详情，character_id: {character_id}")
            character = self.archive.get_character(int(character_id))
            if character:
                log.info(f"【Bangumi】从本地Archive获取角色详情成功，character_id: {character_id}")
                # 如果有infobox且是字符串格式，则解析它
                if "infobox" in character and isinstance(character["infobox"], str):
                    try:
                        character["infobox"] = parse(character["infobox"])
                    except Exception as e:
                        log.warn(f"【Bangumi】使用bgm-tv-wiki解析本地Archive中的infobox失败: {e}")
                # 缓存结果
                self.__async_cache(cache_key, character, 3600)
                return character
                
        log.info(f"【Bangumi】从在线API获取角色详情，character_id: {character_id}")
        result = self.__invoke(self._urls["character_detail"] % character_id)
        if result:
            log.info(f"【Bangumi】从在线API获取角色详情成功，character_id: {character_id}")
            # 如果有infobox且是字符串格式，则解析它
            if "infobox" in result and isinstance(result["infobox"], str):
                try:
                    result["infobox"] = parse(result["infobox"])
                except Exception as e:
                    log.warn(f"【Bangumi】使用bgm-tv-wiki解析在线API返回的infobox失败: {e}")
            # 异步缓存，避免阻塞
            self.__async_cache(cache_key, result, 3600)
        else:
            log.warn(f"【Bangumi】从在线API获取角色详情失败，character_id: {character_id}")
        return result

    def search_bangumi(self, keyword, filters=None, page=1, limit=20):
        """
        搜索番剧 (优先使用v0 API)
        :param keyword: 搜索关键词
        :param filters: 过滤条件，例如 {"type": [2]} 限制为动画类型
        :param page: 页码，默认为第一页
        :param limit: 每页条数，默认为20条
        """
        # 生成缓存键
        cache_key = f"search:{keyword}:{page}:{limit}"
        cached = self.__get_cache(cache_key)
        if cached is not None:
            return cached
            
        # 计算offset
        offset = (page - 1) * limit
                    
        # 优先使用v0 API
        params = {
            "keyword": keyword,
            "limit": limit,
            "offset": offset
        }
        
        if filters:
            params["filter"] = filters
            
        log.info(f"【Bangumi】开始搜索，关键词: {keyword}, 参数: {params}")
        ret = self.__post(self._urls["search"], **params)
        if ret:
            # 获取分页信息
            total = ret.get("total", 0)
            limit_ret = ret.get("limit", limit)
            offset_ret = ret.get("offset", offset)
            
            result = ret.get("data") or []
            log.info(f"【Bangumi】搜索结果数量: {len(result)}")
            # 将Bangumi数据格式转换为与TMDB一致的格式
            formatted_result = []
            for item in result:
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
                formatted_result.append({
                    'id': "BG:%s" % bid,
                    'orgid': bid,
                    'title': title,
                    'year': air_date[:4] if air_date else "",
                    'type': 'ANIME',
                    'media_type': MediaType.ANIME.value,
                    'vote': score,
                    'image': image,
                    'url': detail,
                })
            
            # 构造返回结果，包含分页信息
            response_data = {
                "items": formatted_result,
                "total": total,
                "limit": limit_ret,
                "offset": offset_ret,
                "page": page
            }
            
            log.info(f"【Bangumi】搜索完成，返回格式化结果数量: {len(formatted_result)}")
            
            # 异步缓存，避免阻塞
            self.__async_cache(cache_key, response_data, 1800)
            return response_data
        else:
            log.warn(f"【Bangumi】搜索无结果或请求失败，关键词: {keyword}")
            
        # 返回空结果
        result = {
            "items": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "page": page
        }
        
        # 异步缓存空结果，避免阻塞
        self.__async_cache(cache_key, result, 300)
        return result

    def get_bangumi_episodes(self, bid, limit=100, offset=0):
        """
        获取番剧剧集 (使用v0 API)
        :param bid: 番剧ID
        :param limit: 返回数据量限制
        :param offset: 偏移量
        """
        # 生成缓存键
        cache_key = f"episodes:{bid}:{limit}:{offset}"
        cached = self.__get_cache(cache_key)
        if cached is not None:
            return cached
            
        # 如果启用了Archive，优先从本地获取
        if self.enable_archive and self.archive.exists():
            log.info(f"【Bangumi】尝试从离线数据库获取番剧 {bid} 的剧集信息")
            episodes = self.archive.get_subject_episodes(int(bid))
            if episodes:
                log.info(f"【Bangumi】从离线数据库成功获取番剧 {bid} 的 {len(episodes)} 个剧集")

                # 实现分页逻辑
                start_idx = offset
                end_idx = offset + limit
                paged_episodes = episodes[start_idx:end_idx]
                
                # 构造返回结果，与API返回格式保持一致
                result = {
                    "data": paged_episodes,
                    "total": len(episodes),
                    "limit": limit,
                    "offset": offset
                }
                
                # 异步缓存，避免阻塞
                self.__async_cache(cache_key, result, 1800)
                return result
            else:
                log.info(f"【Bangumi】离线数据库中未找到番剧 {bid} 的剧集信息")
            
        params = {
            "subject_id": bid,
            "limit": limit,
            "offset": offset
        }
            
        ret = self.__invoke(self._urls["episodes"], **params)
        if ret:
            # 异步缓存，避免阻塞
            self.__async_cache(cache_key, ret, 1800)
            return ret
        # 异步缓存空结果，避免阻塞
        self.__async_cache(cache_key, {}, 300)
        return {}