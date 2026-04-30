export const PageButton = ({ children, onClick, className = "" }) => {
  return (
    <button
      onClick={onClick}
      className={`flex items-center justify-center bg-bg-light rounded-global-round-hard h-14 py-5 text-lg font-semibold text-text-main border-border-main border-black ${className}`}
    >
      {children}
    </button>
  );
};
