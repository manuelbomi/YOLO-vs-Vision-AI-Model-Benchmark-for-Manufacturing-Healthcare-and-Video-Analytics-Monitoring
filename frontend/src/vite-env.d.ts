/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  // Optional TURN server for WebRTC across restrictive NATs -- see
  // README > Known limitations. Unset by default (native `npm run dev`);
  // docker-compose.yml passes these as build args pointing at the
  // bundled `coturn` service.
  readonly VITE_TURN_URL?: string;
  readonly VITE_TURN_USERNAME?: string;
  readonly VITE_TURN_CREDENTIAL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
