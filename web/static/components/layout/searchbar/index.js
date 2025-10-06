import { html, nothing } from "../../utility/lit-core.min.js";
import { CustomElement } from "../../utility/utility.js";

const search_source_icon = {
  tmdb: html`
    <!-- http://tabler-icons.io/i/square-letter-t -->
    <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-square-letter-t text-blue" width="24" height="24"
       viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round"
       stroke-linejoin="round">
      <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
      <path d="M4 4m0 2a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2z"></path>
      <path d="M10 8h4"></path>
      <path d="M12 8v8"></path>
    </svg>`,
  douban: html`
    <!-- http://tabler-icons.io/i/circle-letter-d -->
    <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-circle-letter-d text-green" width="24" height="24"
        viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round"
        stroke-linejoin="round">
      <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
      <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"></path>
      <path d="M10 8v8h2a2 2 0 0 0 2 -2v-4a2 2 0 0 0 -2 -2h-2z"></path>
    </svg>
  `,
  person: html`
    <!-- https://tabler-icons.io/i/square-rounded-letter-p -->
    <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-square-rounded-letter-p text-purple" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
       <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
       <path d="M10 12h2a2 2 0 1 0 0 -4h-2v8"></path>
       <path d="M12 3c7.2 0 9 1.8 9 9s-1.8 9 -9 9s-9 -1.8 -9 -9s1.8 -9 9 -9z"></path>
    </svg>
  `,
  bangumi: html`
    <!-- Bangumi番组计划图标 -->
    <svg class="icon" style="width: 1em;height: 1em;vertical-align: middle;fill: currentColor;overflow: hidden;" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="1435"><path d="M228.115268 615.399298a12.300795 12.300795 0 0 0 11.35458 7.569719 12.471113 12.471113 0 0 0 4.749999-0.965139l147.609537-61.882459a12.300795 12.300795 0 0 0 0.26494-22.557765l-147.609537-66.235049a12.300795 12.300795 0 1 0-10.067727 22.444219l121.740019 54.634453-121.456155 50.906366a12.300795 12.300795 0 0 0-6.585656 16.085655zM399.020617 627.965033H239.469848a12.300795 12.300795 0 0 0 0 24.601589h159.550769a12.300795 12.300795 0 0 0 0-24.601589zM399.020617 667.460046H239.469848a12.300795 12.300795 0 0 0 0 24.601589h159.550769a12.300795 12.300795 0 0 0 0-24.601589zM872.941851 476.892349l-133.283841 58.381464a12.300795 12.300795 0 0 0-0.397411 22.349598l133.302766 64.058754a12.073703 12.073703 0 0 0 5.317729 1.23008 12.300795 12.300795 0 0 0 5.336652-23.390435l-109.15536-52.42031L882.896033 499.469038a12.300795 12.300795 0 1 0-9.954182-22.576689zM877.881094 627.965033h-148.101569a12.300795 12.300795 0 0 0 0 24.601589h148.101569a12.300795 12.300795 0 0 0 0-24.601589zM877.881094 667.460046h-148.101569a12.300795 12.300795 0 0 0 0 24.601589h148.101569a12.300795 12.300795 0 0 0 0-24.601589zM644.866193 537.128395h-162.919295a12.28187 12.28187 0 0 0-10.711153 18.318722l81.374488 145.130453a12.300795 12.300795 0 0 0 21.460155 0l81.374489-145.130453a12.300795 12.300795 0 0 0-10.730078-18.318722z m-81.374488 132.299778l-60.444213-107.698189h120.888426z" fill="#F9389E" p-id="1436"></path><path d="M891.411968 334.960102H648.405037c-6.812748-15.13944-19.813742-28.386449-36.864535-38.018917L803.092262 19.283861a12.300795 12.300795 0 0 0-20.249001-13.966133L588.566402 286.873457a147.723082 147.723082 0 0 0-45.418319-7.001991 151.507942 151.507942 0 0 0-31.887445 3.368526L239.980804 4.712151A12.300795 12.300795 0 0 0 222.437978 21.87649l262.726051 269.803739c-22.14143 9.821711-39.116527 25.112546-47.310749 43.242025H132.547555A91.763929 91.763929 0 0 0 40.764702 426.705107v414.44216A91.763929 91.763929 0 0 0 132.547555 932.967969h268.024855l-19.908363 46.989036c-12.641432 29.881469 22.614538 57.094612 48.294812 37.299794L538.473781 932.967969h352.938187a91.763929 91.763929 0 0 0 91.782853-91.782853v-414.442161a91.763929 91.763929 0 0 0-91.782853-91.782853z m34.839635 463.815658a60.709153 60.709153 0 0 1-60.709153 60.709153H585.670984L487.870204 932.967969l-77.002975 57.851583 24.412346-57.851583 31.016927-73.483056H198.082405A60.728077 60.728077 0 0 1 137.27863 798.737912V440.330602a60.728077 60.728077 0 0 1 60.728077-60.728077h667.460046a60.709153 60.709153 0 0 1 60.709153 60.728077z" fill="#F9389E" p-id="1437"></path></svg>
  `
}

export class LayoutSearchbar extends CustomElement {
  static properties = {
    layout_systemflag: { attribute: "layout-systemflag" },
    layout_username: { attribute: "layout-username" },
    layout_search: { attribute: "layout-search"},
    layout_useradmin: { attribute: "layout-useradmin" },
    layout_search_source: { attribute: "layout-search-source" },
    _search_source: { state: true },
  };

  constructor() {
    super();
    this.layout_systemflag = "Docker";
    this.layout_username = "admin";
    this.layout_search_source = "bangumi";
    this._search_source = "bangumi";
    this.classList.add("navbar", "fixed-top", "lit-searchbar");
  }

  firstUpdated() {
    this._search_source = localStorage.getItem("SearchSource") ?? this.layout_search_source;
    // 当前状态：是否模糊
    let blur = false;
    window.addEventListener("scroll", () => {
      const scroll_length = document.body.scrollTop || window.pageYOffset;
      // 滚动发生时改变模糊状态
      if (!blur && scroll_length >= 5) {
        // 模糊状态
        blur = true;
        this.classList.add("lit-searchbar-blur");
      } else if (blur && scroll_length < 5) {
        // 非模糊状态
       blur = false
       this.classList.remove("lit-searchbar-blur");
      }
    });
  }

  // 卸载事件
  disconnectedCallback() {
    super.disconnectedCallback();
  }

  get input() {
    return this.querySelector(".home_search_bar") ?? null;
  }

  render() {
    return html`
      <div class="container-fluid nav-search-bar">
        <div class="d-flex flex-row flex-grow-1 align-items-center py-1">
          <!-- 导航展开按钮 -->
          <layout-navbar-button></layout-navbar-button>
          <!-- 搜索栏 -->
          <div class="input-group input-group-flat mx-2">
            <span class="input-group-text form-control-rounded">
              <a href="#" class="link-secondary"
                @click=${ () => {
                  let source_dict = {
                    bangumi: "tmdb",
                    tmdb: "douban",
                    douban: "person",
                    person: "bangumi",
                  };
                  this._search_source = source_dict[this._search_source];
                  localStorage.setItem("SearchSource", this._search_source);
                }}>
                ${search_source_icon[this._search_source]}
              </a>
            </span>
            <input type="text" class="home_search_bar form-control form-control-rounded" placeholder=${this._search_source === "person" ? "搜索人物" : (this._search_source === "bangumi" ? "搜索番剧" : "搜索电影、电视剧")} autocomplete="new-password" ?readonly=${this.layout_search == 0}
              @keypress=${ (e) => {
                if(e.which === 13 && this.input.value){
                  if (this._search_source === "person") {
                    navmenu("discovery_person?&type=ALL&title=演员搜索&subtitle=" + this.input.value + "&keyword=" + this.input.value);
                  } else if (this._search_source === "bangumi") {
                    navmenu("recommend?type=BANGUMI_SEARCH&title=番剧搜索结果&subtitle=" + this.input.value + "&keyword=" + this.input.value);
                  } else {
                    navmenu("recommend?type=SEARCH&title=搜索结果&subtitle=" + this.input.value + "&keyword=" + this.input.value + "&source=" + this._search_source);                   
                  }
                  this.input.value = "";
                }
              }}>
            <span class="input-group-text form-control-rounded">
              <a href="${this.layout_search > 0 ? "javascript:show_search_advanced_modal()":"javascript:void(0)"}" class="link-secondary">
                <!-- http://tabler-icons.io/i/adjustments -->
                <svg xmlns="http://www.w3.org/2000/svg" class="icon" width="24" height="24" viewBox="0 0 24 24" stroke-width="2"
                    stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                  <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                  <circle cx="6" cy="10" r="2"></circle>
                  <line x1="6" y1="4" x2="6" y2="8"></line>
                  <line x1="6" y1="12" x2="6" y2="20"></line>
                  <circle cx="12" cy="16" r="2"></circle>
                  <line x1="12" y1="4" x2="12" y2="14"></line>
                  <line x1="12" y1="18" x2="12" y2="20"></line>
                  <circle cx="18" cy="7" r="2"></circle>
                  <line x1="18" y1="4" x2="18" y2="5"></line>
                  <line x1="18" y1="9" x2="18" y2="20"></line>
                </svg>
              </a>
            </span>
          </div>
          <!-- 头像 -->
          <div class="nav-item dropdown me-2">
              <a href="#" class="nav-link d-flex lh-1 text-reset ms-1 p-0" data-bs-toggle="dropdown">
                <!-- http://tabler-icons.io/i/user -->
                <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-user"
                    width="24" height="24" viewBox="0 0 24 24"
                    stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                  <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                  <path d="M6 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2"></path>
                </svg>
              </a>
              <div class="dropdown-menu dropdown-menu-end dropdown-menu-arrow">
                <a class="dropdown-item hide-theme-dark" href="?theme=dark" role="button">暗黑风格</a>
                <a class="dropdown-item hide-theme-light" href="?theme=light" role="button">明亮风格</a>
                <div class="dropdown-divider"></div>
                ${this.layout_useradmin === "1"
                ? html`
                    <a class="dropdown-item" data-bs-toggle="offcanvas" href="#offcanvasEnd" role="button"
                      aria-controls="offcanvasEnd">消息中心</a>
                    <a class="dropdown-item" href="javascript:show_logging_modal()" role="button">实时日志</a>
                    <div class="dropdown-divider"></div>
                  `
                : nothing }
                <a href="javascript:logout()" class="dropdown-item">
                  注销 <span class="text-muted mx-3">${this.layout_username}</span>
                </a>
                <a href="javascript:restart()" class="dropdown-item">
                  重启
                </a>
                <div class="dropdown-divider"></div>
                <a href="https://github.com/zzzjzhq/nas-tools" target="_blank" class="dropdown-item">帮助中心</a>
              </div>
            </div>
          </div>
      </div>
    `;
  }

}


window.customElements.define("layout-searchbar", LayoutSearchbar);