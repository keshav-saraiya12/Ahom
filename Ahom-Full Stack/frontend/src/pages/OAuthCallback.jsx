import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import api from "../api";
import { useAuth } from "../context/AuthContext";
import LoadingSpinner from "../components/LoadingSpinner";

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");

    if (!code) {
      setError("Missing authorization code");
      return;
    }

    const provider = state === "github" ? "github" : "google";
    const redirect_uri = `${window.location.origin}/auth/callback`;

    api
      .post(`/auth/${provider}/`, { code, redirect_uri })
      .then(({ data }) => {
        login({ access: data.access, refresh: data.refresh }, data.user);
        navigate("/dashboard", { replace: true });
      })
      .catch((err) => {
        setError(err.response?.data?.error || "Authentication failed. Please try again.");
      });
  }, [searchParams, login, navigate]);

  if (error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-red-600 font-medium mb-4">{error}</p>
          <button
            onClick={() => navigate("/login")}
            className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center">
      <LoadingSpinner />
      <p className="text-gray-500 mt-4">Signing you in...</p>
    </div>
  );
}
