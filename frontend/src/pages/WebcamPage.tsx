import { useRef, useState } from "react";
import { sendWebrtcOffer } from "../lib/api";
import type { ArenaModelInfo } from "../types";
import { FamilyBadge } from "../components/FamilyBadge";
import "./WebcamPage.css";

const ICE_GATHERING_TIMEOUT_MS = 3000;

interface WebcamPageProps {
  models: ArenaModelInfo[];
}

export function WebcamPage({ models }: WebcamPageProps) {
  const [selectedModel, setSelectedModel] = useState<string>(models[0]?.name ?? "");
  const [status, setStatus] = useState<"idle" | "connecting" | "connected" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  async function start() {
    setStatus("connecting");
    setError(null);
    try {
      const localStream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = localStream;
      if (localVideoRef.current) localVideoRef.current.srcObject = localStream;

      const pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
      pcRef.current = pc;
      localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));

      pc.ontrack = (event) => {
        if (remoteVideoRef.current) remoteVideoRef.current.srcObject = event.streams[0];
        setStatus("connected");
      };

      const offerDesc = await pc.createOffer();
      await pc.setLocalDescription(offerDesc);

      // Don't wait forever for ICE gathering to fully complete -- a STUN
      // server can be slow or unreachable on some networks. Proceed with
      // whatever candidates were gathered within the timeout (this is what
      // real WebRTC apps do; waiting indefinitely here is a common
      // beginner mistake that makes "it just hangs" the default failure mode).
      await Promise.race([
        new Promise<void>((resolve) => {
          if (pc.iceGatheringState === "complete") return resolve();
          pc.addEventListener("icegatheringstatechange", () => {
            if (pc.iceGatheringState === "complete") resolve();
          });
        }),
        new Promise<void>((resolve) => setTimeout(resolve, ICE_GATHERING_TIMEOUT_MS)),
      ]);

      const localDesc = pc.localDescription!;
      const answer = await sendWebrtcOffer(localDesc.sdp, localDesc.type, selectedModel);
      await pc.setRemoteDescription(answer);
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  function stop() {
    pcRef.current?.close();
    pcRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setStatus("idle");
  }

  const model = models.find((m) => m.name === selectedModel);

  return (
    <div className="webcam-page">
      <section className="panel">
        <h3>Webcam demo (WebRTC)</h3>
        <p className="muted">
          Your browser's camera, streamed to this backend over WebRTC (no
          RTSP/MediaMTX involved here — see <code>api/ingestion/webrtc.py</code>),
          run through the chosen model, and streamed back annotated in real
          time. Uses a public STUN server for NAT traversal with a short
          timeout — see README &gt; Networking protocols for why RTSP, not
          WebRTC, is the more common choice for fixed industrial cameras.
        </p>

        <div className="model-select-row">
          <label>
            Model:
            <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} disabled={status === "connected"}>
              {models.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name}
                </option>
              ))}
            </select>
          </label>
          {model && <FamilyBadge family={model.family} />}
          {status === "idle" || status === "error" ? (
            <button className="run-button" onClick={start}>
              Start webcam
            </button>
          ) : (
            <button className="stop-button" onClick={stop}>
              Stop
            </button>
          )}
        </div>

        {status === "connecting" && <p className="muted">Connecting...</p>}
        {error && <p className="error">{error}</p>}

        <div className="video-pair">
          <div>
            <p className="video-label">Your camera</p>
            <video ref={localVideoRef} autoPlay playsInline muted />
          </div>
          <div>
            <p className="video-label">Annotated (from backend)</p>
            <video ref={remoteVideoRef} autoPlay playsInline />
          </div>
        </div>
      </section>
    </div>
  );
}
