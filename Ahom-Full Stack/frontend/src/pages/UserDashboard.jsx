import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Calendar, Clock, XCircle, Ticket } from "lucide-react";
import { format } from "date-fns";
import api from "../api";
import { useAuth } from "../context/AuthContext";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";

export default function UserDashboard() {
  const { user } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    const params = {};
    if (filter === "upcoming") params.time = "upcoming";
    if (filter === "past") params.time = "past";

    setLoading(true);
    api
      .get("/bookings/", { params })
      .then((r) => setBookings(r.data))
      .catch(() => setBookings([]))
      .finally(() => setLoading(false));
  }, [filter]);

  const handleCancel = async (id) => {
    if (!window.confirm("Cancel this booking?")) return;
    try {
      await api.delete(`/bookings/${id}/`);
      setBookings((prev) =>
        prev.map((b) => (b.id === id ? { ...b, status: "cancelled" } : b))
      );
    } catch {
      alert("Failed to cancel booking.");
    }
  };

  const activeBookings = bookings.filter((b) => b.status !== "cancelled");
  const cancelledBookings = bookings.filter((b) => b.status === "cancelled");

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Dashboard</h1>
          <p className="text-gray-500 text-sm">
            Welcome back, {user?.first_name || user?.username}
          </p>
        </div>
        <Link
          to="/profile"
          className="text-sm text-brand-600 hover:text-brand-700 font-medium"
        >
          Edit Profile &rarr;
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Bookings</p>
          <p className="text-2xl font-bold text-gray-900">{bookings.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Active</p>
          <p className="text-2xl font-bold text-green-600">{activeBookings.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Cancelled</p>
          <p className="text-2xl font-bold text-gray-400">{cancelledBookings.length}</p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6">
        {["all", "upcoming", "past"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${
              filter === f
                ? "bg-brand-600 text-white"
                : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Bookings list */}
      {loading ? (
        <LoadingSpinner />
      ) : bookings.length === 0 ? (
        <EmptyState
          icon={Ticket}
          title="No bookings yet"
          description="Browse our catalog and book your first session."
          action={
            <Link to="/" className="inline-block mt-2 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium">
              Browse Sessions
            </Link>
          }
        />
      ) : (
        <div className="space-y-4">
          {bookings.map((b) => (
            <div
              key={b.id}
              className={`bg-white rounded-xl border p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center gap-4 ${
                b.status === "cancelled" ? "border-gray-200 opacity-60" : "border-gray-200"
              }`}
            >
              <div className="flex-1 min-w-0">
                <Link
                  to={`/sessions/${b.session.id}`}
                  className="font-semibold text-gray-900 hover:text-brand-600 line-clamp-1"
                >
                  {b.session.title}
                </Link>
                <div className="flex flex-wrap gap-3 mt-1 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <Calendar size={14} />
                    {b.session.date
                      ? format(new Date(b.session.date), "MMM d, yyyy · h:mm a")
                      : "TBD"}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock size={14} />
                    {b.session.duration_minutes} min
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span
                  className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                    b.status === "confirmed"
                      ? "bg-green-100 text-green-700"
                      : b.status === "pending"
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {b.status}
                </span>
                {b.status !== "cancelled" && (
                  <button
                    onClick={() => handleCancel(b.id)}
                    className="text-gray-400 hover:text-red-500 transition"
                    title="Cancel booking"
                  >
                    <XCircle size={20} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
