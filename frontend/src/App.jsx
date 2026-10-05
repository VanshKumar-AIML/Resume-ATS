import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Upload from "./pages/Upload";
import Results from "./pages/Results";
import Dashboard from "./pages/Dashboard";

function RequireAuth({ children }) {
  const isLoggedIn = !!localStorage.getItem("access_token");
  return isLoggedIn ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Navigate to="/upload" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/upload"
          element={
            <RequireAuth>
              <Upload />
            </RequireAuth>
          }
        />
        <Route
          path="/results/:id"
          element={
            <RequireAuth>
              <Results />
            </RequireAuth>
          }
        />
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />
      </Routes>
    </>
  );
}
