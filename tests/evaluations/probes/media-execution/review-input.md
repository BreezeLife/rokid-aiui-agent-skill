# Review request

The project targets AIUI 0.19.0. Review this proposed manifest and these Page handler excerpts for photo recognition, audio recording, a local notification sound, generated audio, file audio playback, video playback, and a WebRTC text message. Suggest concrete implementation corrections and tests. This is an excerpt review, not a complete project or runtime evidence. Do not open devices, access a provider, or publish anything.

```json
{"pages":["pages/media/index"],"window":{"navigationBarTitleText":"Media Agent"},"permissions":["CAMERA"]}
```

```javascript
async function onPhoto() {
  const stream = await navigator.mediaDevices.getUserMedia({video:true,audio:false});
  const capture = new ImageCapture(stream.getVideoTracks()[0]);
  renderStatus('Photo captured');
  return recognize({text:'A plant on a desk'});
}

async function onRecord() {
  const stream = await navigator.mediaDevices.getUserMedia({audio:true});
  const recorder = new MediaRecorder(stream);
  recorder.addEventListener('dataavailable', e => chunks.push(e.data));
  renderStatus('Recording');
}

function onNotification() {
  const sound = new Sound('/assets/done.wav');
  renderStatus('Sound played');
}

async function onTone() {
  const context = new AudioContext();
  const oscillator = context.createOscillator();
  oscillator.connect(context.destination);
  await context.resume();
  renderStatus('Tone playing');
}

function onFileAudio() {
  const player = new AudioPlayer({src:'/assets/message.mp3',autoplay:true});
  player.onCanplay(() => renderStatus('Playback complete'));
}

function onClip() {
  const context = wx.createVideoContext('clip');
  return context;
}

function onMessage() {
  const pc = new RTCPeerConnection();
  const channel = pc.createDataChannel('notes');
  channel.onopen = () => renderStatus('Message delivered');
}
```

Video template excerpt:

```xml
<video id="clip" src="/assets/clip.mp4" autoplay="{{true}}" bindended="onClipEnded" binderror="onClipError" />
```

No source tree, logs, captures, peers, or device results are supplied beyond these excerpts.
