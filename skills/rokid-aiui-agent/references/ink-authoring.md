# `.ink` and multi-file authoring

Read this when writing Page or Widget markup, data bindings, event handlers, styles, or converting between authoring modes.

New work targets **0.19.0**. Read [aiui-0.19.md](aiui-0.19.md) for current lifecycle, loading, input, style, and validation changes. Older pinned links below preserve explicit 0.17/0.18 compatibility evidence.

## Pick one mode per Page route

AIUI supports:

- single-file Page: `pages/home/index.ink`
- multi-file Page: `index.wxml`, `index.wxss`, `index.js`, and optional page configuration

Both use the same Page data, lifecycle, and event model. The official [0.17 Page overview](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/page.en-US.md#L12-L24) describes both modes. If both exist at one route, current documentation says `.ink` wins: [0.18 structure snapshot](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/0-guide/structure.md#L12-L20). Treat a mixed route as an ambiguity warning and remove the unused definition when safe.

## Page `.ink` contract

A Page `.ink` file may contain, at most once each:

- `<script def>`: strict JSON object for entry configuration
- `<script setup>`: default-exported Page object
- exactly one `<page>` root
- `<style>`: scoped entry styles

It must not contain a `<widget>` root. The current structure and block roles are documented [here](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/0-guide/structure.md#L77-L105).

```html
<script def>
{
  "description": "Show the current task and allow confirmation",
  "schema": {
    "data": {
      "type": "object",
      "properties": {
        "title": { "type": "string" }
      }
    }
  }
}
</script>

<script setup>
export default {
  data: { title: "Ready", confirmed: false },
  onLoad(query) {
    if (query.title) this.setData({ title: query.title });
  },
  confirm() {
    this.setData({ confirmed: true });
  }
};
</script>

<page>
  <view class="panel">
    <text>{{title}}</text>
    <button bindtap="confirm">Confirm</button>
    <text ink:if="{{confirmed}}">Done</text>
  </view>
</page>

<style>
.panel { padding: 12px; }
</style>
```

Use JSON-serializable initial `data`; update rendered state with `this.setData()`, including dotted paths when useful. The [0.17 Page definition](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/page-definition.en-US.md#L25-L52) documents the export model and data update pattern.

## Template and events

- Use `{{...}}` data binding.
- AIUI template control attributes use the `ink:*` namespace, not similarly named Mini Program directives. Use `ink:if` / `ink:elif` / `ink:else` for [0.17 conditional rendering](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/wxml/conditional-rendering.en-US.md), and `ink:for` with `ink:key` for [0.17 list rendering](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/wxml/list-rendering.en-US.md).
- Bind component events with the documented event names such as `bindtap`; keep handler names resolvable on the default-exported object.
- Do not assume HTML DOM behavior, React syntax, browser CSS, or arbitrary Web APIs. Check the exact AIUI component/API page first; see [runtime-capabilities.md](runtime-capabilities.md).

For 0.19, [data updates](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/wxml/data-binding.en-US.md) support array `.length` and reentrant `setData()` callbacks. Each loop has its own scope; keep conditional branches adjacent and query the current tree after updates. `hidden` retains a node while inactive conditional branches remove it. Read complete text input from `event.detail.value`.

## Widget `.ink` contract — 0.18 and 0.19

A Widget uses the same blocks but has exactly one `<widget>` root and no `<page>`. The family in `<script def>` must match the manifest declaration. Supported families are `1x1` and `1x2`; see the [0.19 Widget guide](https://github.com/yodaos-project/AIUI/blob/7d62c2d9ac1cdc1389ba06ed0651b395903accff/documentation/1-framework/open-agent-format/widget.en-US.md) or the historical [0.18 Widget guide](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/1-framework/open-agent-format/widget.en-US.md#L5-L64). Do not emit Widgets into an explicit 0.17 project.

```html
<script def>
{ "widget": { "family": "1x1" } }
</script>
<script setup>
export default { data: { count: 0 } };
</script>
<widget><text>{{count}}</text></widget>
<style>text { font-size: 14px; }</style>
```

Use relative root sizing, not the current glasses family's pixel dimensions. In 0.19, read opening query strings in `onCreate(options)` and use `onAttach`/`onDetach` for repeated visible work; no query produces `{}`. Declare metadata and placement in `app.json`; see [project-anatomy.md](project-anatomy.md).

## Styles and motion

- Use AIUI WXSS/CSS support, not a general browser compatibility assumption.
- For 0.19, verify the constrained `calc()` subset, ellipsis, concurrent animations, and `animationstart`/`animationiteration`/`animationend`/`animationcancel` in the [0.19 style map](aiui-0.19.md). Experimental `random()` needs literal fallbacks. Test cancellation and unrelated updates; do not assume 3D transforms or `animation-play-state`.
- The 0.17 stable reference already documents [transitions](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/wxss/property.md#L104-L115).
- The 0.18 preview expands animation across size, spacing, color, opacity, position, rotation, and scale with transitions or `@keyframes`: [v0.18 changelog](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/7-changelog/latest.en-US.md#L194-L210). It also includes a runnable [transition/animation sample](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/samples/capabilities/pages/transition_animation/index.ink#L169-L390).
- Prefer short event-driven motion. Confirm the exact properties on the target runtime and physical glasses.

## Authoring checks

- One entry root, no duplicate optional blocks.
- `<script def>` parses as a JSON object; no comments or trailing commas.
- Exported methods referenced by the template exist.
- Declared component paths and asset paths resolve from the project root.
- In 0.19, component directory entries explicitly name `index`; Page/component ready callbacks run once after their own first presented frame. Confirm return/show behavior and final cleanup separately.
- The page works with missing or malformed optional input without crashing.
- No empty declarations such as `margin-top:` remain.
