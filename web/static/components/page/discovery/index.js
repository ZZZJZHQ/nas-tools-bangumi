import { html, nothing } from "../../utility/lit-core.min.js";
import { CustomElement, Golbal } from "../../utility/utility.js";

export class PageDiscovery extends CustomElement {
  static properties = {
    discovery_type: { attribute: "discovery-type" },
    _slide_card_list: { state: true },
    _media_type_list: { state: true },
  };

  constructor() {
    super();
    this._slide_card_list = {};
    this._media_type_list = {
      "RANKING": [
        {
          type: "MOV",
          title:"正在热映",
          subtype :"dbom",
        },
        {
          type: "MOV",
          title:"即将上映",
          subtype :"dbnm",
        },
        {
          type: "TRENDING",
          title:"TMDB流行趋势",
          subtype :"tmdb",
        },
        {
          type: "MOV",
          title:"豆瓣热门电影",
          subtype :"dbhm",
        },
        {
          type: "MOV",
          title:"豆瓣电影TOP250",
          subtype :"dbtop",
        },
        {
          type: "TV",
          title:"豆瓣热门剧集",
          subtype :"dbht",
        },
        {
          type: "TV",
          title:"豆瓣热门动漫",
          subtype :"dbdh",
        },
        {
          type: "TV",
          title:"豆瓣热门综艺",
          subtype :"dbzy",
        },
        {
          type: "TV",
          title:"华语口碑剧集榜",
          subtype :"dbct",
        },
        {
          type: "TV",
          title:"全球口碑剧集榜",
          subtype :"dbgt",
        }
      ],
      "BANGUMI": [
        {
          type: "TV",
          title:"星期一",
          subtype :"bangumi",
          week :"1",
        },
        {
          type: "TV",
          title:"星期二",
          subtype :"bangumi",
          week :"2",
        },
        {
          type: "TV",
          title:"星期三",
          subtype :"bangumi",
          week :"3",
        },
        {
          type: "TV",
          title:"星期四",
          subtype :"bangumi",
          week :"4",
        },
        {
          type: "TV",
          title:"星期五",
          subtype :"bangumi",
          week :"5",
        },
        {
          type: "TV",
          title:"星期六",
          subtype :"bangumi",
          week :"6",
        },
        {
          type: "TV",
          title:"星期日",
          subtype :"bangumi",
          week :"7",
        },
      ]
    }
  }

  firstUpdated() {
    for (const item of this._media_type_list[this.discovery_type]) {
      Golbal.get_cache_or_ajax(
          "get_recommend",
          self.discovery_type + item.title,
          { "type": item.type, "subtype": item.subtype, "page": 1, "week": item.week},
          (ret) => {
            this._slide_card_list = {...this._slide_card_list, [item.title]: ret.Items};
          }
       );
    }
  }

  render() {
      return html`
        <div class="container-xl">
          ${this._media_type_list[this.discovery_type]?.map((item) => ( html`
            <custom-flow
              flow-title=${item.title}
              flow-click="javascript:navmenu('recommend?type=${item.type}&subtype=${item.subtype}&week=${item.week ?? ""}&title=${item.title}')"
              .flowCard=${this._slide_card_list[item.title]
                ? this._slide_card_list[item.title].map((card, index) => ( html`
                  <div class="col-6 col-sm-4 col-md-3 col-lg-2">
                    <normal-card
                      style="display: flex;"
                      @fav_change=${(e) => {
                        Golbal.update_fav_data("get_recommend", item.subtype, (extra) => (
                          extra.Items[index].fav = e.detail.fav, extra
                        ));
                      }}
                      lazy=0
                      card-tmdbid=${card.id}
                      card-mediatype=${card.type}
                      card-showsub=1
                      card-image=${'/img?url='+card.image}
                      card-fav=${card.fav}
                      card-vote=${card.vote}
                      card-year=${card.year}
                      card-title=${card.title}
                      card-restype=${card.media_type}
                      class="px-2"
                    ></normal-card>
                  </div>`))
                : Array(20).fill(html`<div class="col-6 col-sm-4 col-md-3 col-lg-2"><normal-card-placeholder></normal-card-placeholder></div>`)
              }
            ></custom-flow>`
          ))}
        </div>
      `;
  }
}


window.customElements.define("page-discovery", PageDiscovery);