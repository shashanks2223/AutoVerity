import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import MobileNav from "./MobileNav";

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

export default function Layout({ children, title }: LayoutProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { path: "/", label: "Dashboard", icon: "dashboard" },
    { path: "/upload", label: "Upload Image", icon: "upload" },
    { path: "/history", label: "Processing History", icon: "history" },
  ];

  return (
    <div className="flex min-h-screen bg-background">
      {/* Permanent Left Sidebar for Desktop */}
      <aside className="hidden md:flex w-64 flex-col border-r border-outline-variant bg-surface-container-lowest">
        <div className="flex h-16 items-center px-6 border-b border-outline-variant bg-white">
          <Link to="/" className="text-xl font-black text-secondary tracking-tight flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary" style={{ fontSize: "28px" }}>
              verified
            </span>
            AutoVerity
          </Link>
        </div>
        
        <nav className="flex-1 flex flex-col gap-1 p-4 bg-white">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-semibold transition-all ${
                  isActive
                    ? "bg-secondary/10 text-secondary"
                    : "text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface"
                }`}
              >
                <span className="material-symbols-outlined" style={{ fontSize: "22px" }}>
                  {item.icon}
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>
        
        <div className="p-4 border-t border-outline-variant flex items-center gap-3 bg-white">
          <span className="material-symbols-outlined text-outline" style={{ fontSize: "36px" }}>
            account_circle
          </span>
          <div className="min-w-0">
            <span className="block text-xs font-semibold truncate text-on-surface">Administrator</span>
            <span className="block text-[10px] truncate text-outline">admin@autoverity.com</span>
          </div>
        </div>
      </aside>

      {/* Main Content Pane */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Top Navbar */}
        <header className="sticky top-0 z-10 flex h-16 w-full items-center justify-between border-b border-outline-variant bg-surface-container-lowest px-6 shadow-sm">
          <div className="flex items-center gap-4">
            {/* Hamburger for Mobile */}
            <button
              onClick={() => setIsMenuOpen(true)}
              className="flex items-center justify-center p-2 rounded-lg text-on-surface-variant hover:bg-surface-container md:hidden transition-colors"
            >
              <span className="material-symbols-outlined">menu</span>
            </button>
            <h2 className="text-lg font-bold text-on-surface tracking-tight">
              {title || "AutoVerity"}
            </h2>
          </div>

          <div className="flex items-center gap-4">
            <button className="flex items-center justify-center p-2 rounded-lg text-outline hover:text-secondary hover:bg-surface-container-low transition-colors">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <button className="flex items-center justify-center p-2 rounded-lg text-outline hover:text-secondary hover:bg-surface-container-low transition-colors">
              <span className="material-symbols-outlined">settings</span>
            </button>
          </div>
        </header>

        {/* Slide-over Mobile Navigation Drawer */}
        <MobileNav isOpen={isMenuOpen} onClose={() => setIsMenuOpen(false)} />

        {/* Content View */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
