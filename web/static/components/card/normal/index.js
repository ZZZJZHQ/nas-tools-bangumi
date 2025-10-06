import { NormalCardPlaceholder } from "./placeholder.js"; export { NormalCardPlaceholder };

import { html, nothing } from "../../utility/lit-core.min.js";
import { CustomElement, Golbal } from "../../utility/utility.js";
import { observeState } from "../../utility/lit-state.js";
import { cardState } from "./state.js";

export class NormalCard extends observeState(CustomElement) {

  static properties = {
    tmdb_id: { attribute: "card-tmdbid" },
    res_type: { attribute: "card-restype" },
    media_type: { attribute: "card-mediatype" },
    show_sub: { attribute: "card-showsub"},
    title: { attribute: "card-title" },
    fav: { attribute: "card-fav" , reflect: true},
    date: { attribute: "card-date" },
    vote: { attribute: "card-vote" },
    image: { attribute: "card-image" },
    overview: { attribute: "card-overview" },
    year: { attribute: "card-year" },
    site: { attribute: "card-site" },
    weekday: { attribute: "card-weekday" },
    lazy: {},
    _placeholder: { state: true },
    _card_id: { state: true },
    _card_image_error: { state: true },
  };

  constructor() {
    super();
    this.lazy = "0";
    this._placeholder = true;
    this._card_image_error = false;
    this._card_id = Symbol("normalCard_data_card_id");
  }

  _render_left_up() {
    if (this.weekday || this.res_type) {
      let color;
      let text;
      if (this.weekday) {
        color = "bg-orange";
        text = this.weekday;
      } else if (this.res_type) {
        color = this.res_type === "电影" ? "bg-lime" : "bg-blue";
        text = this.res_type;
      }
      return html`
        <span class="badge badge-pill ${color}" style="position: absolute; top: 10px; left: 10px">
          ${text}
        </span>`;
    } else {
      return nothing;
    }
  }

  _render_right_up() {
     if (this.fav == "2") {
      return html`
        <div class="badge badge-pill bg-green" style="position:absolute;top:10px;right:10px;padding:0;">
          <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-check" width="24" height="24"
               viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round"
               stroke-linejoin="round">
            <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
            <path d="M5 12l5 5l10 -10"></path>
          </svg>
        </div>`;
    } else if (this.vote && this.vote != "0.0" && this.vote != "0") {
      return html`
      <div class="badge badge-pill bg-purple"
           style="position: absolute; top: 10px; right: 10px">
        ${this.vote}
      </div>`;
    } else {
      return nothing;
    }
  }

  _render_bottom() {
    if (this.show_sub == "1") {
      // 修改为通过是否有history_id来判断是否显示删除按钮
      const canDelete = this.history_id && this.history_id !== "None" && this.history_id !== "undefined";
      
      return html`
        <div class="d-flex justify-content-between">
          <a class="text-muted" title="搜索资源" @click=${(e) => { e.stopPropagation() }}
             href='javascript:media_search("${this.tmdb_id}", "${this.title}", "${this.media_type}")'>
            <span class="icon-pulse text-white">
              <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-search" width="24" height="24"
                  viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round"
                  stroke-linejoin="round">
                <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                <circle cx="10" cy="10" r="7"></circle>
                <line x1="21" y1="21" x2="15" y2="15"></line>
              </svg>
            </span>
          </a>
          <div class="ms-auto d-flex">
            ${canDelete ? html`
              <div class="text-muted" title="删除记录" style="cursor: pointer; margin-right: 10px;" @click=${this._deleteClick}>
                <span class="icon-pulse text-white">
                  <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-trash" width="24" height="24"
                      viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round"
                      stroke-linejoin="round">
                    <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                    <line x1="4" y1="7" x2="20" y2="7"></line>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                    <path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12"></path>
                    <path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3"></path>
                  </svg>
                </span>
              </div>
            ` : nothing}
            <div class="text-muted" title="加入/取消订阅" style="cursor: pointer" @click=${this._loveClick}>
              <span class="icon-pulse text-white">
                <svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-heart ${this.fav == "1" ? "icon-filled text-red" : ""}" width="24" height="24"
                    viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round"
                    stroke-linejoin="round">
                  <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                  <path d="M19.5 12.572l-7.5 7.428l-7.5 -7.428m0 0a5 5 0 1 1 7.5 -6.566a5 5 0 1 1 7.5 6.572"></path>
                </svg>
              </span>
            </div>
          </div>
        </div>`;
    } else {
      return nothing;
    }
  }

  render() {
    return html`
      <div class="card card-sm lit-normal-card rounded-3 cursor-pointer ratio shadow-sm"
           @click=${() => { if (Golbal.is_touch_device()){ cardState.more_id = this._card_id } } }
           @mouseenter=${() => { if (!Golbal.is_touch_device()){ cardState.more_id = this._card_id } } }
           @mouseleave=${() => { if (!Golbal.is_touch_device()){ cardState.more_id = undefined } } }>
        ${this._placeholder ? NormalCardPlaceholder.render_placeholder() : nothing}
        <div ?hidden=${this._placeholder} class="rounded-3">
          <img class="card-img rounded-3" alt="" style="box-shadow:0 0 0 1px #888888; display: block; min-width: 100%; max-width: 100%; min-height: 100%; max-height: 100%; object-fit: cover;"
             src=${this.lazy == "1" ? "" : this.image ?? Golbal.noImage}
             @error=${() => { if (this.lazy != "1") {this.image = Golbal.noImage; this._card_image_error = true} }}
             @load=${() => { this._placeholder = false }}/>
          ${this._render_left_up()}
          ${this._render_right_up()}
        </div>
        <div class="card-img-overlay rounded-3 ms-auto"
             style="background: linear-gradient(to bottom,  rgba(0,0,0,0) 0%,rgba(0,0,0,0.7) 100%);  box-shadow:0 0 0 1px #dddddd;"
             @click=${() => { navmenu(`media_detail?type=${this.media_type}&id=${this.tmdb_id}`) }}>
          <div style="cursor: pointer">
            ${this.year ? html`<div class="text-white" 
                style="-webkit-line-clamp:1; display: -webkit-box; -webkit-box-orient:vertical; overflow:hidden; text-overflow: ellipsis;"><strong>${this.site ? this.site : this.year}</strong></div>` : nothing }
            ${this.title
            ? html`
              <h2 class="lh-sm text-white"
                  style="margin-bottom: 5px; -webkit-line-clamp:2; display: -webkit-box; -webkit-box-orient:vertical; overflow:hidden; text-overflow: ellipsis;">
                <strong>${this.title}</strong>
              </h2>`
            : nothing }
            ${this.date
            ? html`
              <p class="lh-sm text-white"
                style="margin-bottom: 5px; -webkit-line-clamp:1; display: -webkit-box; -webkit-box-orient:vertical; overflow:hidden; text-overflow: ellipsis;">
                <small>${this.date}</small>
              </p>`
            : nothing }
          </div>
          ${this._render_bottom()}
        </div>
      </div>
    `;
  }

  _fav_change() {
    const options = {
      detail: {
        fav: this.fav
      },
      bubbles: true,
      composed: true,
    };
    this.dispatchEvent(new CustomEvent("fav_change", options));
  }

  _loveClick(e) {
    e.stopPropagation();
    Golbal.lit_love_click(this.title, this.year, this.media_type, this.tmdb_id, this.fav,
      () => {
        this.fav = "0";
        this._fav_change();
      },
      () => {
        this.fav = "1";
        this._fav_change();
      });
  }
  
  _deleteClick(e) {
    e.stopPropagation();
    // 触发删除事件，传递tmdb_id
    const options = {
      detail: {
        tmdb_id: this.tmdb_id,
        title: this.title,
        date: this.date,
        history_id: this.history_id
      },
      bubbles: true,
      composed: true,
    };
    this.dispatchEvent(new CustomEvent("delete_click", options));
  }
  
}

window.customElements.define("normal-card", NormalCard);