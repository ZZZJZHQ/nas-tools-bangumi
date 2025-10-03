import { html, nothing } from "../../utility/lit-core.min.js";
import { CustomElement } from "../../utility/utility.js";

export class CustomFlow extends CustomElement {
  static properties = {
    flowTitle: { attribute: "flow-title" },
    flowClick: { attribute: "flow-click" },
    flowCard: { attribute: "flow-card", type: Array },
  };

  constructor() {
    super();
  }

  render() {
    return html`
      <div class="mb-3">
        <div class="d-flex align-items-center pt-2">
          <h2 class="mb-0">${this.flowTitle}</h3>
        </div>
        <div class="row row-cards">
          ${this.flowCard ?? nothing}
        </div>
      </div>
    `;
  }
}

window.customElements.define("custom-flow", CustomFlow);