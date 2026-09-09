# Interaction, targets, and glasses design

Read this when choosing `_current` versus `_blank`, handling hardware/voice/head input, or styling for Rokid Glasses.

## Target is a hosting context

`_current` keeps a Page inline in the conversation/card context; `_blank` uses a standalone, fuller hosting space. A host may allow a user to expand an inline page. Target is chosen by the host/invocation, not declared as a fixed Page field. See the [0.17 Page overview](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/page.en-US.md#L26-L43) and [target reference](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/target.en-US.md).

Use target-aware layout, not target-aware business truth:

```css
@media (target: _current) {
  .details { display: none; }
}

@media (target: _blank) {
  .details { display: flex; }
}
```

Use `onTargetChanged(target, previousTarget)` when logic must react to a host transition. `_current` can contain interaction in current documentation, but its available size, host focus, navigation activation, and interception behavior vary by host/runtime. Always test the exact integration. Do not call it universally display-only, and do not promise desktop-style interaction.

## Focus before key handling

Separate:

- **host focus**: whether the Page is the active interactive surface
- **element focus**: which node is selected inside it

Use `:host-focus`, `onHostFocus()`, `onHostBlur()`, and documented element focus/blur events. The [0.17 focus reference](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/focus.en-US.md#L5-L43) explains the two layers and notes that exact unfocused behavior remains host-dependent.

## Hardware and voice events

Page-level input belongs on the exported Page object. The [0.17 events guide](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/page-events.en-US.md) documents `onKeyDown`, `onKeyUp`, and `onVoiceWakeup`.

```js
export default {
  onKeyUp(event) {
    if (event.code === 'Backspace' && this.data.hasUnsavedWork) {
      event.preventDefault();
      this.openDiscardConfirmation();
    }
  },
  onVoiceWakeup(event) {
    this.setData({ wakeword: event.keyword || '' });
  }
};
```

Default host actions commonly occur on `keyup`: back/close for `Backspace`, root scrolling for `ArrowUp`/`ArrowDown`, and navigation/activation for `Enter`. Call `preventDefault()` in `onKeyUp` **only when the Page implements a complete replacement behavior**. Otherwise preserve host navigation. Key codes and interception details are host-sensitive; record actual device events instead of inventing codes.

## World awareness and head gestures

For a Page that needs head gestures, explicitly enable awareness before handling them:

```js
export default {
  onLoad() {
    this.enableWorldAwareness();
  },
  onHeadGesture(event) {
    if (event.gesture === 'nod') this.confirm();
  }
};
```

Use only the callbacks documented for the target host, and provide a key/voice fallback. The pinned [Page API](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/framework/page.en-US.md#L130-L243) covers `enableWorldAwareness()`, the Page-private orientation sensor, head-gesture events, and cleanup. This is Page-scoped; 0.18 Widgets explicitly do not provide Page-only world-awareness methods: [Widget differences](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/documentation/1-framework/open-agent-format/widget.en-US.md#L119-L125).

## Two design layers; do not merge their coordinates

### Current AIUI monochrome-green beta layer

The official beta design is a **480 × 352** runtime/reference canvas for RokidGlasses1/2, with a transparent black floor and one green luminance channel: [scope and constraints](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/design/monochrome/design-system-green.md#L1-L23).

Use its current low-mass grammar:

- 1px normal structural lines; 2px only for strong focus
- 16px horizontal safe inset and 12px vertical safe inset
- primary readable text at no less than 72% green luminance
- 4px control radius; 6px panel/group radius
- normal large/local green fill at no more than 12%
- open rows and whitespace before repeated card wrappers
- full green reserved for active focus/key values; do not encode state by luminance alone
- short, event-driven motion; avoid multiple ambient loops

The exact layout and structural rules are [here](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/design/monochrome/design-system-green.md#L407-L455), motion guidance is [here](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/design/monochrome/design-system-green.md#L576-L636), and its device acceptance checklist is [here](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/design/monochrome/design-system-green.md#L751-L766).

This file is marked beta and is present in the 0.17 tag. Treat it as visual guidance for its named devices, not as evidence that an unrelated runtime capability exists.

### Older official optical guideline layer

The mutable [official Rokid Glasses recommended design guideline](https://custom.rokid.com/prod/rokid_web/57e35cd3ae294d16b1b8fc8dcbb1b7c7/pc/cn/5a71b66dbc1e4689886c7aa437299f2b.html), inspected 2026-09-07, presents an optical canvas of **480 × 640**, with a **480 × 400** preferred region and older examples using **1.5px** strokes and **12px** radii.

Treat those as optical/device-composition guidance, not as aliases for the repository's 480 × 352 Ink viewport or newer 1px/4px/6px beta grammar. When the layers disagree:

1. identify the actual runtime viewport and target;
2. keep essential content in the comfortable optical field;
3. preview both `_current` and `_blank` where relevant;
4. test bright, dark, and cluttered real backgrounds on physical glasses;
5. record which device/runtime made the final decision.
