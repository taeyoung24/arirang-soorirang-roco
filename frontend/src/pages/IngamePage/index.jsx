import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from 'src/components/Layout'
import { IngameTopContainer } from 'src/components/TopContainer'

function AnswerButton({ parts, status = 'Default' }) {
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
    <button className={`self-stretch h-12 w-full ${bgClass} ${opacityClass} rounded-[20px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text inline-flex justify-between items-center transition-transform active:scale-[0.98] cursor-pointer`}>
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

export default function IngamePage() {
  const navigate = useNavigate()

  useEffect(() => {
    // 배경색을 피그마 디자인에 맞춰 yellow-primary로 변경
    document.body.style.backgroundColor = 'var(--color-yellow-primary)'
    return () => {
      document.body.style.backgroundColor = ''
    }
  }, [])

  return (
    <Layout className="bg-yellow-primary h-[770px]">
      <div className="w-80 h-[718px] mx-auto flex flex-col justify-start items-center gap-4">
        
        {/* Header */}
        <IngameTopContainer onBack={() => navigate('/home')} onHelp={() => {}} />

        {/* Body */}
        <div className="self-stretch flex-1 relative flex flex-col justify-end items-center gap-2.5">
          {/* Text Area */}
          <div className="self-stretch h-14 flex flex-col justify-between items-center">
            <div className="self-stretch justify-start text-text text-2xl font-extrabold font-sans">
              같은 의미로 사용된 문장을 고르세요.
            </div>
          </div>
          
          {/* Question Sentence */}
          <div className="self-stretch flex-1 pt-2 inline-flex justify-center items-center gap-1 flex-wrap content-center">
            <span className="text-text text-lg font-semibold font-sans">“</span>
            <span className="text-text text-lg font-semibold font-sans">저는 매일 저녁에 일기를</span>
            <div className="px-0.5 border-b-[1.60px] border-text flex justify-center items-center gap-2.5">
              <span className="text-text text-lg font-extrabold font-sans">써요</span>
            </div>
            <span className="text-text text-lg font-semibold font-sans">”</span>
          </div>

          {/* Feed Image & Heart Button */}
          <div className="relative self-stretch">
            <img 
              className="w-full h-80 object-cover rounded-[20px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text" 
              src="https://placehold.co/330x330" 
              alt="feed" 
            />
            {/* Heart Button: 피그마의 절대 좌표 대신 부모 요소(이미지) 기준 상대 좌표로 유연하게 배치 */}
            <div className="absolute right-4 bottom-4 p-3.5 bg-bg rounded-[32px] outline outline-[2.40px] outline-offset-[-2.40px] outline-text inline-flex justify-start items-center gap-6 overflow-hidden">
              <div className="flex justify-start items-center gap-1">
                <div className="relative">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M19.2373 6.23731C20.7839 7.78395 20.8432 10.2727 19.3718 11.8911L11.9995 20.0001L4.62812 11.8911C3.15679 10.2727 3.21605 7.7839 4.76269 6.23726C6.48961 4.51034 9.33372 4.66814 10.8594 6.5752L12 8.00045L13.1396 6.57504C14.6653 4.66798 17.5104 4.51039 19.2373 6.23731Z" fill="var(--color-ari-primary, #D95B7A)" stroke="var(--color-text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <div className="justify-start text-text text-lg font-semibold font-sans">25</div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer (Answers) */}
        <div className="self-stretch h-60 flex flex-col justify-center items-center gap-2.5">
          <div className="self-stretch flex flex-col justify-end items-center gap-2.5">
            <AnswerButton parts={[
              { text: "글씨", type: "normal" },
              { text: "쓰는 ", type: "highlight" },
              { text: "연습을 하세요.", type: "normal" }
            ]} />
            <AnswerButton parts={[
              { text: "어제", type: "normal" },
              { text: "쓴", type: "highlight" },
              { text: "우산을 말리고 있어요.", type: "normal" }
            ]} />
            <AnswerButton parts={[
              { text: "모자", type: "normal" },
              { text: "쓴", type: "highlight" },
              { text: "사람을 보았어요.", type: "normal" }
            ]} />
            <AnswerButton parts={[
              { text: "이 소스는 조금", type: "normal" },
              { text: "쓰네요", type: "highlight" }
            ]} />
          </div>
        </div>

      </div>
    </Layout>
  )
}
