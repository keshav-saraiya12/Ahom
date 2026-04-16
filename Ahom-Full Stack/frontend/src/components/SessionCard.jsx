import { Link } from "react-router-dom";
import { Calendar, MapPin, Users, DollarSign } from "lucide-react";
import { format } from "date-fns";

export default function SessionCard({ session }) {
  const dateStr = session.date ? format(new Date(session.date), "MMM d, yyyy · h:mm a") : "";

  return (
    <Link
      to={`/sessions/${session.id}`}
      className="group bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow"
    >
      <div className="aspect-video bg-gradient-to-br from-brand-100 to-brand-300 relative overflow-hidden">
        {session.image_url ? (
          <img src={session.image_url} alt={session.title} className="w-full h-full object-cover" />
        ) : (
          <div className="flex items-center justify-center h-full text-brand-600 text-4xl font-bold opacity-30">
            {session.title?.[0]}
          </div>
        )}
        {session.price > 0 && (
          <span className="absolute top-3 right-3 bg-white/90 backdrop-blur px-2 py-1 rounded-md text-sm font-semibold text-gray-800">
            ${Number(session.price).toFixed(2)}
          </span>
        )}
        {session.price == 0 && (
          <span className="absolute top-3 right-3 bg-green-100 text-green-700 px-2 py-1 rounded-md text-sm font-semibold">
            Free
          </span>
        )}
      </div>

      <div className="p-4 space-y-2">
        <h3 className="font-semibold text-gray-900 group-hover:text-brand-600 transition-colors line-clamp-1">
          {session.title}
        </h3>
        <p className="text-sm text-gray-500 line-clamp-2">{session.description}</p>

        <div className="flex flex-wrap gap-3 text-xs text-gray-500 pt-1">
          {dateStr && (
            <span className="flex items-center gap-1">
              <Calendar size={13} /> {dateStr}
            </span>
          )}
          <span className="flex items-center gap-1">
            <MapPin size={13} /> {session.location || "Online"}
          </span>
          <span className="flex items-center gap-1">
            <Users size={13} /> {session.seats_available ?? "—"} left
          </span>
        </div>

        {session.tags && (
          <div className="flex flex-wrap gap-1 pt-1">
            {session.tags.split(",").map((t) => (
              <span key={t.trim()} className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">
                {t.trim()}
              </span>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
