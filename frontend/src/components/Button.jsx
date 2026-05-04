export const PageButton = ({ label, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="w-80 h-12 px-5 bg-bg rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text inline-flex justify-center items-center gap-2.5 overflow-hidden transition-all hover:opacity-90 active:scale-[0.98] cursor-pointer"
    >
      <div className="justify-start text-text text-lg font-extrabold font-sans">
        {label}
      </div>
    </button>
  );
};

export const PronounceButton = ({ word, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="h-10 border-b-[2.40px] border-text inline-flex justify-center items-center gap-2 transition-all active:scale-95 cursor-pointer"
    >
      <div className="text-center text-text text-3xl font-extrabold font-sans">{word}</div>
      <div className="relative">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M18.82 4.68652C19.8191 5.61821 20.6167 6.74472 21.1636 7.99657C21.7105 9.24842 21.9952 10.5991 21.9999 11.9652C22.0047 13.3313 21.7295 14.6838 21.1914 15.9395C20.6532 17.1951 19.8635 18.3272 18.8709 19.2658M16.092 7.61194C16.6915 8.17095 17.17 8.84686 17.4982 9.59797C17.8263 10.3491 17.9971 11.1595 18 11.9791C18.0028 12.7988 17.8377 13.6103 17.5148 14.3637C17.1919 15.1171 16.7181 15.7963 16.1225 16.3595M7.4803 15.4069L9.15553 17.48C10.0288 18.5607 10.4655 19.1011 10.848 19.1599C11.1792 19.2108 11.5138 19.0925 11.7394 18.8448C12 18.5586 12 17.8638 12 16.4744V7.52572C12 6.13627 12 5.44155 11.7394 5.15536C11.5138 4.90761 11.1792 4.78929 10.848 4.84021C10.4655 4.89904 10.0288 5.43939 9.15553 6.52009L7.4803 8.59319C7.30388 8.81151 7.21567 8.92067 7.10652 8.99922C7.00982 9.06881 6.90147 9.12056 6.78656 9.15204C6.65687 9.18756 6.51652 9.18756 6.23583 9.18756H4.8125C4.0563 9.18756 3.6782 9.18756 3.37264 9.2885C2.77131 9.48716 2.2996 9.95887 2.10094 10.5602C2 10.8658 2 11.2439 2 12.0001C2 12.7563 2 13.1344 2.10094 13.4399C2.2996 14.0413 2.77131 14.513 3.37264 14.7116C3.6782 14.8126 4.0563 14.8126 4.8125 14.8126H6.23583C6.51652 14.8126 6.65687 14.8126 6.78656 14.8481C6.90147 14.8796 7.00982 14.9313 7.10652 15.0009C7.21567 15.0794 7.30388 15.1886 7.4803 15.4069Z" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </button>
  );
};

export const SimpleIconButton = ({ type, onClick }) => {
  const getIcon = () => {
    switch (type) {
      case 'back':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 12H5M5 12L11 6M5 12L11 18" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        );
      case 'help':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8.19531 8.76498C8.42304 8.06326 8.84053 7.43829 9.40137 6.95899C9.96221 6.47968 10.6444 6.16501 11.373 6.0494C12.1017 5.9338 12.8486 6.02202 13.5303 6.3042C14.2119 6.58637 14.8016 7.05166 15.2354 7.64844C15.6691 8.24521 15.9295 8.95008 15.9875 9.68554C16.0455 10.421 15.8985 11.1581 15.5636 11.8154C15.2287 12.4728 14.7192 13.0251 14.0901 13.4106C13.4611 13.7961 12.7377 14.0002 12 14.0002V14.9998M12.0498 19V19.1L11.9502 19.1002V19H12.0498Z" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        );
      case 'record':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 17V21M12 21H9M12 21H15" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M14 5C14 3.89543 13.1046 3 12 3C10.8954 3 10 3.89543 10 5V11C10 12.1046 10.8954 13 12 13C13.1046 13 14 12.1046 14 11V5Z" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M17.7378 12.7542C17.3674 13.9659 16.6228 15.0292 15.6109 15.7917C14.599 16.5543 13.3716 16.9769 12.1047 16.999C10.8378 17.0211 9.59648 16.6417 8.55855 15.9149C7.52062 15.1881 6.73942 14.1514 6.3269 12.9534" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        );
      case 'stop':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 8.2002V15.8002C5 16.9203 5 17.4796 5.21799 17.9074C5.40973 18.2837 5.71547 18.5905 6.0918 18.7822C6.5192 19 7.07899 19 8.19691 19H15.8036C16.9215 19 17.4805 19 17.9079 18.7822C18.2842 18.5905 18.5905 18.2837 18.7822 17.9074C19 17.48 19 16.921 19 15.8031V8.19691C19 7.07899 19 6.5192 18.7822 6.0918C18.5905 5.71547 18.2842 5.40973 17.9079 5.21799C17.4801 5 16.9203 5 15.8002 5H8.2002C7.08009 5 6.51962 5 6.0918 5.21799C5.71547 5.40973 5.40973 5.71547 5.21799 6.0918C5 6.51962 5 7.08009 5 8.2002Z" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        );
      case 'retry':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 8H5V3M5.29102 16.3569C6.22284 17.7918 7.59014 18.8902 9.19218 19.4907C10.7942 20.0913 12.547 20.1624 14.1925 19.6937C15.8379 19.225 17.2893 18.2413 18.3344 16.8867C19.3795 15.5321 19.963 13.878 19.9989 12.1675C20.0347 10.4569 19.5211 8.78001 18.5337 7.38281C17.5462 5.98561 16.1366 4.942 14.5122 4.40479C12.8878 3.86757 11.1341 3.86499 9.5083 4.39795C7.88252 4.93091 6.47059 5.97095 5.47949 7.36556" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <button 
      onClick={onClick}
      className="w-[52px] h-[52px] flex justify-center items-center bg-bg rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text overflow-hidden transition-all active:scale-95 cursor-pointer shrink-0"
    >
      {getIcon()}
    </button>
  );
};


