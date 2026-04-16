import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search, SlidersHorizontal } from "lucide-react";
import api from "../api";
import SessionCard from "../components/SessionCard";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import { useAuth } from "../context/AuthContext";

export default function Home() {
  const { isAuthenticated } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showUpcoming, setShowUpcoming] = useState(false);

  useEffect(() => {
    const params = { status: "published" };
    if (search) params.search = search;
    if (showUpcoming) params.upcoming = "true";

    setLoading(true);
    api
      .get("/sessions/", { params })
      .then((r) => setSessions(r.data.results || r.data))
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, [search, showUpcoming]);

  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-br from-brand-600 to-brand-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">
            Discover &amp; Book Amazing Sessions
          </h1>
          <p className="text-brand-100 text-lg max-w-2xl mx-auto mb-8">
            Browse live workshops, mentoring calls, and masterclasses from top creators. Find your next learning experience.
          </p>
          {!isAuthenticated && (
            <Link
              to="/login"
              className="inline-block bg-white text-brand-700 px-6 py-3 rounded-lg font-semibold hover:bg-brand-50 transition"
            >
              Get Started — It&rsquo;s Free
            </Link>
          )}
        </div>
      </section>

      {/* Catalog */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Search & filter bar */}
        <div className="flex flex-col sm:flex-row gap-3 mb-8">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search sessions..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            />
          </div>
          <button
            onClick={() => setShowUpcoming(!showUpcoming)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-medium transition ${
              showUpcoming
                ? "bg-brand-50 border-brand-300 text-brand-700"
                : "bg-white border-gray-300 text-gray-600 hover:bg-gray-50"
            }`}
          >
            <SlidersHorizontal size={16} />
            {showUpcoming ? "Upcoming Only" : "All Sessions"}
          </button>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : sessions.length === 0 ? (
          <EmptyState
            icon={Search}
            title="No sessions found"
            description="Try adjusting your search or check back later for new sessions."
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {sessions.map((s) => (
              <SessionCard key={s.id} session={s} />
            ))}
          </div>
        )}
      </section>
    </>
  );
}
