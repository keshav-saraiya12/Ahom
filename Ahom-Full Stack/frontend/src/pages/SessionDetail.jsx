import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Calendar, MapPin, Users, Clock, ArrowLeft, CheckCircle } from "lucide-react";
import { format } from "date-fns";
import api from "../api";
import { useAuth } from "../context/AuthContext";
import LoadingSpinner from "../components/LoadingSpinner";

export default function SessionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);
  const [booked, setBooked] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get(`/sessions/${id}/`)
      .then((r) => setSession(r.data))
      .catch(() => navigate("/"))
      .finally(() => setLoading(false));
  }, [id, navigate]);

  const handleBook = async () => {
    if (!isAuthenticated) return navigate("/login");
    setBooking(true);
    setError("");
    try {
      if (session.price > 0) {
        const { data } = await api.post("/payments/checkout/", { session_id: session.id });
        if (data.checkout_url) {
          window.location.href = data.checkout_url;
          return;
        }
        if (data.free) {
          setBooked(true);
          return;
        }
      } else {
        await api.post("/bookings/", { session_id: session.id });
        setBooked(true);
      }
    } catch (err) {
      setError(err.response?.data?.error || "Booking failed. Please try again.");
    } finally {
      setBooking(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (!session) return null;

  const dateStr = session.date ? format(new Date(session.date), "EEEE, MMMM d, yyyy · h:mm a") : "";

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 mb-6">
        <ArrowLeft size={16} /> Back to catalog
      </Link>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {/* Image */}
        <div className="aspect-[21/9] bg-gradient-to-br from-brand-100 to-brand-300 relative">
          {session.image_url ? (
            <img src={session.image_url} alt={session.title} className="w-full h-full object-cover" />
          ) : (
            <div className="flex items-center justify-center h-full text-brand-500 text-7xl font-bold opacity-20">
              {session.title?.[0]}
            </div>
          )}
        </div>

        <div className="p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">{session.title}</h1>
              {session.creator && (
                <p className="text-sm text-gray-500">
                  by <span className="font-medium text-gray-700">{session.creator.first_name || session.creator.username}</span>
                </p>
              )}
            </div>
            <div className="text-right">
              <span className="text-3xl font-bold text-gray-900">
                {session.price > 0 ? `$${Number(session.price).toFixed(2)}` : "Free"}
              </span>
            </div>
          </div>

          {/* Meta */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-4 border-y border-gray-100">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Calendar size={16} className="text-brand-500" />
              <span>{dateStr || "TBD"}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Clock size={16} className="text-brand-500" />
              <span>{session.duration_minutes} min</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <MapPin size={16} className="text-brand-500" />
              <span>{session.location || "Online"}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Users size={16} className="text-brand-500" />
              <span>{session.seats_available} / {session.max_seats} seats</span>
            </div>
          </div>

          {/* Tags */}
          {session.tags && (
            <div className="flex flex-wrap gap-2">
              {session.tags.split(",").map((t) => (
                <span key={t.trim()} className="bg-brand-50 text-brand-700 text-xs px-3 py-1 rounded-full font-medium">
                  {t.trim()}
                </span>
              ))}
            </div>
          )}

          {/* Description */}
          <div className="prose prose-gray max-w-none">
            <p className="text-gray-700 whitespace-pre-line">{session.description}</p>
          </div>

          {/* Booking CTA */}
          {booked ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
              <CheckCircle size={24} className="text-green-600" />
              <div>
                <p className="font-semibold text-green-800">Booked Successfully!</p>
                <p className="text-sm text-green-600">
                  Check your <Link to="/dashboard" className="underline">dashboard</Link> for details.
                </p>
              </div>
            </div>
          ) : (
            <div>
              {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
              <button
                onClick={handleBook}
                disabled={booking || session.seats_available <= 0}
                className="w-full sm:w-auto px-8 py-3 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {booking ? "Processing..." : session.seats_available <= 0 ? "Sold Out" : "Book Now"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
