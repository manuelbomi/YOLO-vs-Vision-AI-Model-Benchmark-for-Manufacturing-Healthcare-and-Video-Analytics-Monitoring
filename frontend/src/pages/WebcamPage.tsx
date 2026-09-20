import { useRef, useState } from "react";
import { sendWebrtcOffer } from "../lib/api";
import type { ArenaModelInfo } from "../types";
import { FamilyBadge } from "../components/FamilyBadge";
import "./WebcamPage.css";

// TURN allocation needs an extra authenticated round-trip beyond plain
// STUN (initial Allocate -> 401 with a nonce -> re-Allocate with
// credentials -> success), so it takes a bit longer to appear as a
// gathered candidate -- measured at ~2.3s against this repo's own coturn
// service, vs. ~1.6s for STUN-only. The gap is small on a local/LAN
// coturn, but a real TURN server reached over the public internet can be
// slower, so this code gives TURN extra budget rather than cutting
// gathering off right when STUN candidates land -- otherwise it would
// send its offer before the relay candidate ever arrived, defeating the
// point of having a TURN server for a restrictive-NAT peer.
const ICE_GATHERING_TIMEOUT_MS_STUN_ONLY = 3000;
const ICE_GATHERING_TIMEOUT_MS_WITH_TURN = 8000;

interface WebcamPageProps {
  models: ArenaModelInfo[];
}

function buildIceServers(): RTCIceServer[] {
  const servers: RTCIceServer[] = [{ urls: "stun:stun.l.google.com:19302" }];
  const turnUrl = import.meta.env.VITE_TURN_URL;
  if (turnUrl) {
    servers.push({
      urls: turnUrl,
      username: import.meta.env.VITE_TURN_USERNAME,
      credential: import.meta.env.VITE_TURN_CREDENTIAL,
    });
  }
  return servers;
}

// ICE candidate types, from least to most useful across a restrictive NAT:
// "host" (a local network address), "srflx" (server-reflexive, found via
// STUN), "relay" (traffic relayed through a TURN server). Seeing a "relay"
// candidate is the concrete proof a configured TURN server issued a real
// allocation -- not just that the container started.
function candidateType(candidate: string): string {
  const match = candidate.match(/typ (\w+)/);
  return match ? match[1] : "unknown";
}

export function WebcamPage({ models }: WebcamPageProps) {
  const [selectedModel, setSelectedModel] = useState<string>(models[0]?.name ?? "");
  const [status, setStatus] = useState<"idle" | "connecting" | "connected" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [candidateTypes, setCandidateTypes] = useState<Set<string>>(new Set());
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const turnConfigured = Boolean(import.meta.env.VITE_TURN_URL);

  async function start() {
    setStatus("connecting");
    setError(null);
    setCandidateTypes(new Set());
    try {
      const localStream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = localStream;
      if (localVideoRef.current) localVideoRef.current.srcObject = localStream;

      const pc = new RTCPeerConnection({ iceServers: buildIceServers() });
      pcRef.current = pc;
      localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));

      pc.onicecandidate = (event) => {
        if (event.candidate?.candidate) {
          const type = candidateType(event.candidate.candidate);
          setCandidateTypes((prev) => new Set(prev).add(type));
        }
      };

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
        new Promise<void>((resolve) =>
          setTimeout(resolve, turnConfigured ? ICE_GATHERING_TIMEOUT_MS_WITH_TURN : ICE_GATHERING_TIMEOUT_MS_STUN_ONLY)
        ),
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
          {turnConfigured
            ? " A TURN server is configured (see docker-compose.yml's coturn service)."
            : " No TURN server is configured — fine for same-machine/LAN use; see README > Known limitations for when you'd need one."}
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

        {candidateTypes.size > 0 && (
          <p className="muted">
            ICE candidate types gathered: {[...candidateTypes].join(", ")}
            {candidateTypes.has("relay") && " — TURN relay confirmed working"}
          </p>
        )}

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
