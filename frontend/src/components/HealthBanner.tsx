import "./HealthBanner.css";

interface HealthBannerProps {
  status: "checking" | "ok" | "not-ready" | "unreachable";
  error?: string | null;
}

export function HealthBanner({ status, error }: HealthBannerProps) {
  if (status === "checking") {
    return <div className="health-banner">Checking API status...</div>;
  }
  if (status === "unreachable") {
    return (
      <div className="health-banner critical">
        Can't reach the API at the configured <code>VITE_API_BASE_URL</code>. Is it
        running? (<code>uvicorn api.main:app --reload --port 8000</code>) — {error}
      </div>
    );
  }
  if (status === "not-ready") {
    return (
      <div className="health-banner warning">
        Models are still loading on the API server (downloading weights on
        first run can take a few minutes). This page will work once they're
        ready.
      </div>
    );
  }
  return null;
}
