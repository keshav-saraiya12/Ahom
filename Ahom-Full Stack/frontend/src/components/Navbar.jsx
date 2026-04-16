import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Menu, X, LogOut, User, LayoutDashboard, Plus } from "lucide-react";
import { useState } from "react";

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">SM</span>
            </div>
            <span className="font-semibold text-lg hidden sm:block">Sessions Marketplace</span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-4">
            <Link to="/" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium">
              Browse
            </Link>
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium flex items-center gap-1">
                  <LayoutDashboard size={16} /> Dashboard
                </Link>
                {user?.role === "creator" && (
                  <Link to="/creator" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium flex items-center gap-1">
                    <Plus size={16} /> Creator
                  </Link>
                )}
                <Link to="/profile" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium flex items-center gap-1">
                  {user?.avatar ? (
                    <img src={user.avatar} alt="" className="w-6 h-6 rounded-full" />
                  ) : (
                    <User size={16} />
                  )}
                  {user?.first_name || user?.username}
                </Link>
                <button onClick={handleLogout} className="text-gray-500 hover:text-red-600 p-2">
                  <LogOut size={18} />
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 transition"
              >
                Sign In
              </Link>
            )}
          </nav>

          {/* Mobile toggle */}
          <button className="md:hidden p-2" onClick={() => setOpen(!open)}>
            {open ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile nav */}
        {open && (
          <div className="md:hidden pb-4 space-y-1">
            <Link to="/" onClick={() => setOpen(false)} className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">
              Browse Sessions
            </Link>
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" onClick={() => setOpen(false)} className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">
                  Dashboard
                </Link>
                {user?.role === "creator" && (
                  <Link to="/creator" onClick={() => setOpen(false)} className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">
                    Creator Dashboard
                  </Link>
                )}
                <Link to="/profile" onClick={() => setOpen(false)} className="block px-3 py-2 text-gray-700 hover:bg-gray-100 rounded">
                  Profile
                </Link>
                <button
                  onClick={() => { handleLogout(); setOpen(false); }}
                  className="block w-full text-left px-3 py-2 text-red-600 hover:bg-red-50 rounded"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <Link to="/login" onClick={() => setOpen(false)} className="block px-3 py-2 bg-brand-600 text-white rounded text-center">
                Sign In
              </Link>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
