import React from 'react';

export const IngameTopContainer = ({ onBack, onHelp }) => {
  return (
    <div className="w-80 inline-flex justify-between items-center">
      {/* Back Button */}
      <button 
        onClick={onBack}
        className="w-12 h-12 relative bg-bg rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text overflow-hidden transition-all active:scale-95 cursor-pointer"
      >
        <div className="left-[14px] top-[14px] absolute">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 12H5M5 12L11 6M5 12L11 18" stroke="var(--text, #2C2C2C)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </button>

      {/* Stage Lock */}
      <div className="flex justify-start items-center gap-1">
        <div className="relative">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M7.69204 7.5H6.00014C5.06672 7.5 4.59966 7.5 4.24314 7.68166C3.92954 7.84144 3.67476 8.09623 3.51497 8.40983C3.33331 8.76635 3.33331 9.23341 3.33331 10.1668V14.8335C3.33331 15.7669 3.33331 16.2334 3.51497 16.5899C3.67476 16.9035 3.92954 17.1587 4.24314 17.3185C4.59931 17.5 5.06583 17.5 5.99743 17.5H14.0026C14.9342 17.5 15.4 17.5 15.7561 17.3185C16.0697 17.1587 16.3254 16.9035 16.4852 16.5899C16.6666 16.2337 16.6666 15.7679 16.6666 14.8363V10.1641C16.6666 9.23249 16.6666 8.766 16.4852 8.40983C16.3254 8.09623 16.0697 7.84144 15.7561 7.68166C15.3996 7.5 14.9336 7.5 14.0001 7.5H12.3074M7.69204 7.5H12.3074M7.69204 7.5C7.58583 7.5 7.49998 7.4139 7.49998 7.30769V5C7.49998 3.61929 8.61927 2.5 9.99998 2.5C11.3807 2.5 12.5 3.61929 12.5 5V7.30769C12.5 7.4139 12.4136 7.5 12.3074 7.5" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div className="justify-start text-text text-base font-extrabold font-sans">스테이지 잠김</div>
      </div>

      {/* Help Button */}
      <button 
        onClick={onHelp}
        className="w-12 h-12 relative bg-bg rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text overflow-hidden transition-all active:scale-95 cursor-pointer"
      >
        <div className="left-[14px] top-[14px] absolute">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8.19531 8.76498C8.42304 8.06326 8.84053 7.43829 9.40137 6.95899C9.96221 6.47968 10.6444 6.16501 11.373 6.0494C12.1017 5.9338 12.8486 6.02202 13.5303 6.3042C14.2119 6.58637 14.8016 7.05166 15.2354 7.64844C15.6691 8.24521 15.9295 8.95008 15.9875 9.68554C16.0455 10.421 15.8985 11.1581 15.5636 11.8154C15.2287 12.4728 14.7192 13.0251 14.0901 13.4106C13.4611 13.7961 12.7377 14.0002 12 14.0002V14.9998M12.0498 19V19.1L11.9502 19.1002V19H12.0498Z" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </button>
    </div>
  );
};

export const SearchTopContainer = ({ onBack, onSearch }) => {
  return (
    <div className="w-80 inline-flex justify-start items-start gap-2">
      {/* Back Button */}
      <button 
        onClick={onBack}
        className="w-12 h-12 relative bg-bg rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text overflow-hidden transition-all active:scale-95 cursor-pointer"
      >
        <div className="left-[14px] top-[14px] absolute">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 12H5M5 12L11 18M5 12L11 6" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </button>

      {/* Search Input Area */}
      <div className="flex-1 h-12 px-5 bg-white-primary rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text flex justify-center items-center gap-4 overflow-hidden">
        <input 
          type="text"
          placeholder="대화 검색"
          onChange={onSearch}
          className="flex-1 bg-transparent border-none outline-none text-text-light text-lg font-extrabold font-sans placeholder:text-text-light"
        />
        <div className="relative">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15 15L21 21M10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10C17 13.866 13.866 17 10 17Z" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
    </div>
  );
};

export const HomeTopContainer = ({ mascotSrc, onHelp }) => {
  return (
    <div className="w-80 inline-flex justify-between items-start">
      {/* Mascot Area */}
      <div className="w-16 h-12 px-0.5 inline-flex flex-col justify-center items-center overflow-hidden">
        <img src={mascotSrc} alt="mascot" className="w-16 h-14" />
      </div>

      {/* Help Button */}
      <button 
        onClick={onHelp}
        className="p-3.5 bg-bg rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text flex justify-start items-center gap-6 overflow-hidden transition-all active:scale-95 cursor-pointer"
      >
        <div className="relative">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8.19531 8.76498C8.42304 8.06326 8.84053 7.43829 9.40137 6.95899C9.96221 6.47968 10.6444 6.16501 11.373 6.0494C12.1017 5.9338 12.8486 6.02202 13.5303 6.3042C14.2119 6.58637 14.8016 7.05166 15.2354 7.64844C15.6691 8.24521 15.9295 8.95008 15.9875 9.68554C16.0455 10.421 15.8985 11.1581 15.5636 11.8154C15.2287 12.4728 14.7192 13.0251 14.0901 13.4106C13.4611 13.7961 12.7377 14.0002 12 14.0002V14.9998M12.0498 19V19.1L11.9502 19.1002V19H12.0498Z" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </button>
    </div>
  );
};
