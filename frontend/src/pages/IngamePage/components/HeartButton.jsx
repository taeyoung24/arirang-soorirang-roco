import React, { useState } from 'react';

export default function HeartButton({ initialCount = 25, active: initialActive = false, className = '' }) {
  const [active, setActive] = useState(initialActive);
  
  const handleClick = (e) => {
    e.stopPropagation(); // 부모 클릭 이벤트 전파 방지
    setActive(!active);
  };

  return (
    <div 
      onClick={handleClick}
      className={`p-3.5 bg-bg rounded-[32px] outline outline-[2.40px] outline-offset-[-2.40px] outline-text inline-flex justify-start items-center gap-6 overflow-hidden cursor-pointer transition-all active:scale-95 ${className}`}
    >
      <div className="flex justify-start items-center gap-1">
        <div className="relative">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path 
              d="M19.2373 6.23731C20.7839 7.78395 20.8432 10.2727 19.3718 11.8911L11.9995 20.0001L4.62812 11.8911C3.15679 10.2727 3.21605 7.7839 4.76269 6.23726C6.48961 4.51034 9.33372 4.66814 10.8594 6.5752L12 8.00045L13.1396 6.57504C14.6653 4.66798 17.5104 4.51039 19.2373 6.23731Z" 
              fill={active ? "var(--color-ari-primary, #D95B7A)" : "none"} 
              stroke="var(--color-text, #2C2C2C)" 
              strokeWidth="2.4" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
            />
          </svg>
        </div>
        <div className="justify-start text-text text-lg font-semibold font-sans">
          {active ? initialCount : 0}
        </div>
      </div>
    </div>
  );
}
