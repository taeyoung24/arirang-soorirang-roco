import React from 'react';

export default function AnswerButton({ parts, status = 'Default', onClick }) {
  let bgClass = 'bg-bg';
  let opacityClass = '';
  let textColorClass = 'text-text';
  let highlightBorderClass = 'border-text';
  let iconSvg = null;

  switch(status) {
    case 'Disable':
      bgClass = 'bg-bg-softdark';
      opacityClass = 'opacity-60';
      iconSvg = (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M18 18L12 12M12 12L6 6M12 12L18 6M12 12L6 18" stroke="var(--color-bg-softdark, #E8DDD0)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      );
      break;
    case 'Selected-Incorrect':
      bgClass = 'bg-bg';
      iconSvg = (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M18 18L12 12M12 12L6 6M12 12L18 6M12 12L6 18" stroke="var(--color-text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      );
      break;
    case 'Selected':
      bgClass = 'bg-soori-primary';
      textColorClass = 'text-white-primary';
      highlightBorderClass = 'border-white-primary';
      iconSvg = (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4Z" stroke="var(--color-soori-primary-dimmed, #443EEA)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M12 7.19702C9.34751 7.19702 7.1972 9.34732 7.1972 11.9999C7.1972 14.6524 9.34751 16.8027 12 16.8027C14.6526 16.8027 16.8029 14.6524 16.8029 11.9999C16.8029 9.34732 14.6526 7.19702 12 7.19702Z" fill="var(--color-soori-primary-dimmed, #443EEA)"/>
        </svg>
      );
      break;
    case 'Correct':
      bgClass = 'bg-green-primary';
      iconSvg = (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M15 20C15 17.7909 12.3137 16 9 16C5.68629 16 3 17.7909 3 20M16.8281 6.17188C17.1996 6.54331 17.4942 6.98427 17.6952 7.46957C17.8962 7.95487 17.9999 8.47533 17.9999 9.00062C17.9999 9.52591 17.8963 10.045 17.6953 10.5303C17.4943 11.0156 17.1996 11.457 16.8281 11.8285M19 4C19.6566 4.65661 20.1775 5.43612 20.5328 6.29402C20.8882 7.15192 21.0718 8.07127 21.0718 8.99985C21.0718 9.92844 20.8886 10.8482 20.5332 11.7061C20.1778 12.564 19.6566 13.3435 19 14.0001M9 13C6.79086 13 5 11.2091 5 9C5 6.79086 6.79086 5 9 5C11.2091 5 13 6.79086 13 9C13 11.2091 11.2091 13 9 13Z" stroke="var(--color-text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      );
      break;
    case 'Incorrect':
      bgClass = 'bg-ari-primary';
      iconSvg = (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M18 18L12 12M12 12L6 6M12 12L18 6M12 12L6 18" stroke="var(--color-text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      );
      break;
    case 'Default':
    default:
      iconSvg = (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4Z" stroke="var(--color-bg-softdark, #E8DDD0)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      );
      break;
  }

  return (
    <button 
      onClick={onClick}
      className={`self-stretch h-[52px] w-full ${bgClass} ${opacityClass} rounded-[20px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text inline-flex justify-between items-center transition-transform active:scale-[0.98] cursor-pointer`}
    >



      <div className="flex-1 self-stretch pl-4 inline-flex flex-col justify-center items-start gap-2.5">
        <div className="self-stretch inline-flex justify-start items-center gap-0.5 flex-wrap content-center">
          {parts.map((part, index) => {
            if (part.type === 'highlight') {
              return (
                <div key={index} className={`px-0.5 border-b-[1.60px] ${highlightBorderClass} flex justify-center items-center gap-2.5`}>
                  <span className={`${textColorClass} text-base font-extrabold font-sans`}>{part.text}</span>
                </div>
              );
            }
            return (
              <span key={index} className={`${textColorClass} text-base font-semibold font-sans`}>{part.text}</span>
            );
          })}
        </div>
      </div>
      <div className="w-12 self-stretch inline-flex flex-col justify-center items-center overflow-hidden">
        <div className="relative">
          {iconSvg}
        </div>
      </div>
    </button>
  );
}
