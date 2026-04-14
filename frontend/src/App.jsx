import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import Explorer from "./pages/Explorer";
import GeneView from "./pages/GeneView";
import VariantView from "./pages/VariantView";
import DrugView from "./pages/DrugView";
import NetworkView from "./pages/NetworkView";
import DiseaseView from "./pages/DiseaseView";
import "./index.css";

function NavBar() {
  const location = useLocation();
  const isActive = (path) => location.pathname === path ? "nav-link active" : "nav-link";

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" fill="var(--accent-cyan)" stroke="none" />
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" strokeLinecap="round" />
          </svg>
          <span>BioFusion</span>
          <span className="edition">Free</span>
        </Link>
        <div className="nav-links">
          <Link to="/" className={isActive("/")}>Explorer</Link>
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <main className="app-container" style={{ paddingTop: "1.5rem", paddingBottom: "4rem" }}>
        <Routes>
          <Route path="/" element={<Explorer />} />
          <Route path="/gene/:id" element={<GeneView />} />
          <Route path="/variant/:id" element={<VariantView />} />
          <Route path="/drug/:id" element={<DrugView />} />
          <Route path="/disease/:id" element={<DiseaseView />} />
          <Route path="/network/:gene" element={<NetworkView />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
