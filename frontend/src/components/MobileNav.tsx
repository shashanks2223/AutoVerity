import { Link } from "react-router-dom";

interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function MobileNav({
  isOpen,
  onClose,
}: MobileNavProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col gap-md bg-background/95 p-md backdrop-blur-sm">
      <div className="mb-md flex items-center justify-between">
        <span className="text-headline-sm font-black text-primary">
          Menu
        </span>

        <button onClick={onClose} className="p-sm">
          <span className="material-symbols-outlined">
            close
          </span>
        </button>
      </div>

      <nav className="flex flex-col gap-sm">
        <Link
          to="/"
          onClick={onClose}
          className="flex items-center gap-md rounded p-md hover:bg-surface-container-highest"
        >
          <span className="material-symbols-outlined">
            dashboard
          </span>
          Dashboard
        </Link>

        <Link
          to="/upload"
          onClick={onClose}
          className="flex items-center gap-md rounded p-md hover:bg-surface-container-highest"
        >
          <span className="material-symbols-outlined">
            upload
          </span>
          Batch Upload
        </Link>

        <Link
          to="/history"
          onClick={onClose}
          className="flex items-center gap-md rounded p-md hover:bg-surface-container-highest"
        >
          <span className="material-symbols-outlined">
            history
          </span>
          Processing History
        </Link>
      </nav>
    </div>
  );
}