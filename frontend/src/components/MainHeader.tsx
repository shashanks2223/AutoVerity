import { useState } from "react";
import { Link } from "react-router-dom";
import MobileNav from "./MobileNav";

interface MainHeaderProps {}

export default function MainHeader({}: MainHeaderProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-outline-variant bg-surface-container-lowest px-md shadow-sm">
      <div className="flex items-center gap-md">
        <button
          onClick={() => setIsMenuOpen(true)}
          className="flex items-center justify-center text-on-surface-variant hover:text-secondary"
        >
          <span className="material-symbols-outlined">
            menu
          </span>
        </button>

        <MobileNav
          isOpen={isMenuOpen}
          onClose={() => setIsMenuOpen(false)}
        />

        <Link
          to="/"
          className="ml-2 text-headline-sm font-black text-primary"
        >
          AutoVerity
        </Link>
      </div>

      <div className="flex items-center gap-md">
        <button className="text-primary hover:text-secondary">
          <span className="material-symbols-outlined">
            notifications
          </span>
        </button>

        <button className="text-primary hover:text-secondary">
          <span className="material-symbols-outlined">
            account_circle
          </span>
        </button>
      </div>
    </header>
  );
}