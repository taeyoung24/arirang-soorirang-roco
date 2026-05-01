export const PageButton = ({ children, onClick, className = "" }) => {
  return (
    <button
      onClick={onClick}
      className={`w-80 h-12 px-5 bg-bg rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text inline-flex justify-center items-center gap-2.5 overflow-hidden transition-all hover:opacity-90 active:scale-[0.98] cursor-pointer ${className}`}
    >
      <div className="justify-start text-text text-lg font-extrabold font-sans">
        {children}
      </div>
    </button>
  );
};


