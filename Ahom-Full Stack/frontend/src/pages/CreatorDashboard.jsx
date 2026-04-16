import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Eye, Users, CalendarPlus } from "lucide-react";
import { format } from "date-fns";
import api from "../api";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";

const DEFAULT_FORM = {
  title: "",
  description: "",
  image_url: "",
  date: "",
  duration_minutes: 60,
  max_seats: 20,
  price: 0,
  tags: "",
  location: "Online",
  status: "published",
};

export default function CreatorDashboard() {
  const [sessions, setSessions] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("sessions");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(DEFAULT_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const loadData = () => {
    setLoading(true);
    Promise.all([
      api.get("/sessions/mine/"),
      api.get("/bookings/creator/"),
    ])
      .then(([s, b]) => {
        setSessions(s.data.results || s.data);
        setBookings(b.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadData(); }, []);

  const openCreate = () => {
    setEditing(null);
    setForm(DEFAULT_FORM);
    setFormError("");
    setShowForm(true);
  };

  const openEdit = (s) => {
    setEditing(s.id);
    setForm({
      title: s.title,
      description: s.description,
      image_url: s.image_url || "",
      date: s.date ? s.date.slice(0, 16) : "",
      duration_minutes: s.duration_minutes,
      max_seats: s.max_seats,
      price: s.price,
      tags: s.tags || "",
      location: s.location || "Online",
      status: s.status,
    });
    setFormError("");
    setShowForm(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      const payload = {
        ...form,
        date: form.date ? new Date(form.date).toISOString() : null,
        price: parseFloat(form.price) || 0,
        duration_minutes: parseInt(form.duration_minutes) || 60,
        max_seats: parseInt(form.max_seats) || 20,
      };
      if (editing) {
        await api.patch(`/sessions/${editing}/`, payload);
      } else {
        await api.post("/sessions/", payload);
      }
      setShowForm(false);
      loadData();
    } catch (err) {
      setFormError(
        typeof err.response?.data === "object"
          ? Object.values(err.response.data).flat().join(", ")
          : "Failed to save session"
      );
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this session? This cannot be undone.")) return;
    try {
      await api.delete(`/sessions/${id}/`);
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch {
      alert("Failed to delete session.");
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Creator Dashboard</h1>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 px-4 py-2.5 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition"
        >
          <Plus size={16} /> New Session
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Sessions</p>
          <p className="text-2xl font-bold">{sessions.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Bookings</p>
          <p className="text-2xl font-bold">{bookings.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Published</p>
          <p className="text-2xl font-bold text-green-600">
            {sessions.filter((s) => s.status === "published").length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Draft</p>
          <p className="text-2xl font-bold text-gray-400">
            {sessions.filter((s) => s.status === "draft").length}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {["sessions", "bookings"].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${
              tab === t
                ? "bg-brand-600 text-white"
                : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Sessions tab */}
      {tab === "sessions" && (
        sessions.length === 0 ? (
          <EmptyState
            icon={CalendarPlus}
            title="No sessions yet"
            description="Create your first session and start accepting bookings."
            action={
              <button onClick={openCreate} className="mt-2 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium">
                Create Session
              </button>
            }
          />
        ) : (
          <div className="space-y-3">
            {sessions.map((s) => (
              <div
                key={s.id}
                className="bg-white rounded-xl border border-gray-200 p-4 flex flex-col sm:flex-row sm:items-center gap-4"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900 line-clamp-1">{s.title}</h3>
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        s.status === "published"
                          ? "bg-green-100 text-green-700"
                          : s.status === "draft"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-red-100 text-red-600"
                      }`}
                    >
                      {s.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">
                    {s.date ? format(new Date(s.date), "MMM d, yyyy · h:mm a") : "No date"} · {s.seats_booked}/{s.max_seats} booked · ${Number(s.price).toFixed(2)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <a
                    href={`/sessions/${s.id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="p-2 text-gray-400 hover:text-brand-600 transition"
                    title="View"
                  >
                    <Eye size={18} />
                  </a>
                  <button onClick={() => openEdit(s)} className="p-2 text-gray-400 hover:text-brand-600 transition" title="Edit">
                    <Pencil size={18} />
                  </button>
                  <button onClick={() => handleDelete(s.id)} className="p-2 text-gray-400 hover:text-red-500 transition" title="Delete">
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )
      )}

      {/* Bookings tab */}
      {tab === "bookings" && (
        bookings.length === 0 ? (
          <EmptyState icon={Users} title="No bookings yet" description="Bookings from users will appear here." />
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-gray-500">
                <tr>
                  <th className="px-4 py-3 font-medium">User</th>
                  <th className="px-4 py-3 font-medium">Session</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Date Booked</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {bookings.map((b) => (
                  <tr key={b.id}>
                    <td className="px-4 py-3 flex items-center gap-2">
                      {b.user?.avatar && (
                        <img src={b.user.avatar} alt="" className="w-6 h-6 rounded-full" />
                      )}
                      {b.user?.first_name || b.user?.username || "—"}
                    </td>
                    <td className="px-4 py-3">{b.session?.title}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          b.status === "confirmed"
                            ? "bg-green-100 text-green-700"
                            : "bg-gray-100 text-gray-500"
                        }`}
                      >
                        {b.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {b.created_at ? format(new Date(b.created_at), "MMM d, yyyy") : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}

      {/* Session form modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <form onSubmit={handleSave} className="p-6 space-y-4">
              <h2 className="text-xl font-bold">
                {editing ? "Edit Session" : "Create Session"}
              </h2>

              {formError && (
                <p className="text-sm text-red-600 bg-red-50 p-2 rounded">{formError}</p>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                <input
                  required
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
                <textarea
                  required
                  rows={3}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Date & Time *</label>
                  <input
                    required
                    type="datetime-local"
                    value={form.date}
                    onChange={(e) => setForm({ ...form, date: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Duration (min)</label>
                  <input
                    type="number"
                    min={15}
                    value={form.duration_minutes}
                    onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max Seats</label>
                  <input
                    type="number"
                    min={1}
                    value={form.max_seats}
                    onChange={(e) => setForm({ ...form, max_seats: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price ($)</label>
                  <input
                    type="number"
                    min={0}
                    step="0.01"
                    value={form.price}
                    onChange={(e) => setForm({ ...form, price: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Image URL</label>
                <input
                  type="url"
                  value={form.image_url}
                  onChange={(e) => setForm({ ...form, image_url: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                  placeholder="https://..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tags (comma-separated)</label>
                <input
                  value={form.tags}
                  onChange={(e) => setForm({ ...form, tags: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                  placeholder="react, javascript, web"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
                >
                  <option value="published">Published</option>
                  <option value="draft">Draft</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 py-2.5 bg-brand-600 text-white rounded-lg font-medium text-sm hover:bg-brand-700 disabled:opacity-50 transition"
                >
                  {saving ? "Saving..." : editing ? "Update Session" : "Create Session"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
