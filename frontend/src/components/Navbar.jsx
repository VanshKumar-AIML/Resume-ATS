import { Link, useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();
  const isLoggedIn = !!localStorage.getItem("access_token");

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <Link to="/" className="brand">
        AI Resume Builder
      </Link>
      <div className="nav-links">
        {isLoggedIn ? (
          <>
            <Link to="/upload">Analyze Resume</Link>
            <Link to="/dashboard">Dashboard</Link>
            <button onClick={handleLogout} className="link-button">
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}
