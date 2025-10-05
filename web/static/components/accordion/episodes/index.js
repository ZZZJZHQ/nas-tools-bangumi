import { html, nothing } from "../../utility/lit-core.min.js";
import { CustomElement, Golbal } from "../../utility/utility.js";

export class BangumiEpisodes extends CustomElement {
  static properties = {
    // 番剧ID
    bangumi_id: { attribute: "bangumi-id" },
    episodes_data: {  },
    loading: {  },
    current_page: {  },
  };

  constructor() {
    super();
    this.bangumi_id = "";
    this.episodes_data = [];
    this.loading = true;
    this.current_page = 1;
    this.page_size = 100; // 默认每页显示100集
    this.total_episodes = 0;
  }

  firstUpdated() {
    // 获取番剧集数信息
    if (this.bangumi_id) {
      this._fetchEpisodes();
    }
  }

  updated(changedProperties) {
    // 当番剧ID更新时重新获取数据
    if ((changedProperties.has("bangumi_id") && this.bangumi_id) || 
        (changedProperties.has("current_page") && this.bangumi_id)) {
      this._fetchEpisodes();
    }
    // 当loading、episodes_data或current_page更新时，触发UI更新
    if (changedProperties.has("loading") || 
        changedProperties.has("episodes_data") || 
        changedProperties.has("current_page")) {
      // LitElement会自动处理属性变化并触发重新渲染，这里不需要额外操作
      // 这个条件判断的存在是为了确保这些属性变化时组件会重新渲染
      console.log(changedProperties)
    }
  }

  _fetchEpisodes() {
    this.loading = true;
    // 传递分页参数
    const requestData = {
      "subject_id": this.bangumi_id,
      "limit": this.page_size,
      "offset": (this.current_page - 1) * this.page_size
    };
    
    Golbal.get_cache_or_ajax("bangumi_episodes", `ep_${this.bangumi_id}_${this.current_page}`, 
      requestData,
      (ret) => {
        this.loading = false;
        if (ret.code === 0) {
          // 正确处理返回的数据结构
          this.episodes_data = ret.data || []; // 数据在ret.data中
          this.total_episodes = ret.total || (ret.data ? ret.data.length : 0);
        } else {
          console.error("获取番剧集数信息失败:", ret);
          // 即使失败也要设置loading为false，避免一直显示骨架屏
          this.loading = false;
        }
      }
    );
  }

  // 格式化集数显示编号（例如：1 -> 01）
  _formatEpisodeNumber(number) {
    const num = Math.floor(number);
    return num < 10 ? `0${num}` : num.toString();
  }

  // 处理页码变化
  _handlePageChange(newPage) {
    if (newPage >= 1 && newPage <= this._getTotalPages()) {
      this.current_page = newPage;
    }
  }

  // 获取总页数
  _getTotalPages() {
    return Math.ceil(this.total_episodes / this.page_size);
  }

  // 渲染分页控件
  _renderPagination() {
    if (this.total_episodes <= this.page_size) {
      return nothing;
    }

    const totalPages = this._getTotalPages();
    const currentPage = this.current_page;
    
    // 计算要显示的页码范围
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);
    
    // 确保显示5个页码（如果可能）
    if (endPage - startPage < 4) {
      if (startPage === 1) {
        endPage = Math.min(totalPages, startPage + 4);
      } else {
        startPage = Math.max(1, endPage - 4);
      }
    }

    const pages = [];
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    return html`
      <div class="d-flex justify-content-center mt-4">
        <ul class="pagination">
          <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" @click=${(e) => {
              e.preventDefault();
              this._handlePageChange(currentPage - 1);
            }} tabindex="-1" aria-disabled="true">上一页</a>
          </li>
          
          ${startPage > 1 ? html`
            <li class="page-item">
              <a class="page-link" href="#" @click=${(e) => {
                e.preventDefault();
                this._handlePageChange(1);
              }}>1</a>
            </li>
            ${startPage > 2 ? html`<li class="page-item disabled"><span class="page-link">...</span></li>` : ''}
          ` : ''}
          
          ${pages.map(page => html`
            <li class="page-item ${page === currentPage ? 'active' : ''}">
              <a class="page-link" href="#" @click=${(e) => {
                e.preventDefault();
                this._handlePageChange(page);
              }}>${page}</a>
            </li>
          `)}
          
          ${endPage < totalPages ? html`
            ${endPage < totalPages - 1 ? html`<li class="page-item disabled"><span class="page-link">...</span></li>` : ''}
            <li class="page-item">
              <a class="page-link" href="#" @click=${(e) => {
                e.preventDefault();
                this._handlePageChange(totalPages);
              }}>${totalPages}</a>
            </li>
          ` : ''}
          
          <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" @click=${(e) => {
              e.preventDefault();
              this._handlePageChange(currentPage + 1);
            }}>下一页</a>
          </li>
        </ul>
      </div>
    `;
  }

  render() {
    if (this.loading) {
      return html`
        <div class="container">
          <div class="row">
            <div class="col-12">
              <div class="placeholder-glow">
                <div class="placeholder col-12" style="height: 40px; margin-bottom: 10px;"></div>
                <div class="placeholder col-12" style="height: 40px; margin-bottom: 10px;"></div>
                <div class="placeholder col-12" style="height: 40px; margin-bottom: 10px;"></div>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    if (!this.episodes_data || this.episodes_data.length === 0) {
      return html`
        <div class="container">
          <div class="row">
            <div class="col-12">
              <div class="alert alert-info" role="alert">
                <h4 class="alert-heading">暂无集数信息</h4>
                <p>当前番剧暂无集数详情。</p>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    // 过滤出普通剧集（排除OP、ED等特殊类型）
    const normalEpisodes = this.episodes_data.filter && this.episodes_data.filter(ep => ep.type === 0) || [];
    
    return html`
      <div class="container">
        <div class="row">
          <div class="col-12">
            <div class="card">
              <div class="card-header">
                <h3 class="card-title">剧集列表</h3>
                <div class="card-actions">
                  <div class="d-flex align-items-center text-muted">
                    <small>共 ${this.total_episodes} 集</small>
                  </div>
                </div>
              </div>
              <div class="card-body">
                <div class="row g-2">
                  ${normalEpisodes.map((episode) => html`
                    <div class="col-auto">
                      <button class="btn btn-outline-primary" 
                              style="min-width: 100px; text-align: left;"
                              title="${(episode.name_cn || episode.name || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}">
                        <div class="d-flex flex-column">
                          <span class="fw-bold">${this._formatEpisodeNumber(episode.sort || episode.ep)}</span>
                          <span class="text-truncate" style="font-size: 0.8rem; max-width: 90px;" ?hidden=${!(episode.name_cn.trim() && episode.name.trim())}>
                            ${(episode.name_cn || episode.name).replace(/</g, '&lt;').replace(/>/g, '&gt;')}
                          </span>
                        </div>
                      </button>
                    </div>
                  `)}
                </div>
              </div>
              ${this._renderPagination()}
            </div>
          </div>
        </div>
      </div>
    `;
  }
}

window.customElements.define("bangumi-episodes", BangumiEpisodes);