/**
 * App.jsx  –  Root component with React Router v6 setup.
 */
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { useEffect } from "react";
import useStore from "./store/useStore";
import Navbar from "./components/Navbar";
import HomePage from "./pages/HomePage";
import ChatPage from "./pages/ChatPage";
import SchemesPage from "./pages/SchemesPage";
import { LoginPage, RegisterPage } from "./pages/AuthPage";
import AdminPage from "./pages/AdminPage";
import AboutPage from "./pages/AboutPage";
import "./styles/globals.css";

function AppShell() {
  const { darkMode } = useStore();

  // Apply dark mode class to <html>
  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  return (
    <div className="min-h-screen bg-cream dark:bg-charcoal transition-colors">
      <Navbar />
      <main>
        <Routes>
          <Route path="/"         element={<HomePage />}    />
          <Route path="/chat"     element={<ChatPage />}    />
          <Route path="/schemes"  element={<SchemesPage />} />
          <Route path="/login"    element={<LoginPage />}   />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/admin"    element={<AdminPage />}   />
          <Route path="/about"    element={<AboutPage />}   />
        </Routes>
      </main>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: "#fff",
            color: "#1A1A2E",
            borderRadius: "12px",
            boxShadow: "0 4px 24px rgba(10,61,145,0.12)",
            fontSize: "14px",
          },
        }}
      />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}
