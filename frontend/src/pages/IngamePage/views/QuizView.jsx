import React, { useState } from 'react';
import AnswerButton from '../components/AnswerButton';
import PronounceArea from '../components/PronounceArea';

export default function QuizView({ onStageUnlock }) {
  const [selectedIdx, setSelectedIdx] = useState(null);
  const [isAnswered, setIsAnswered] = useState(false);

  const handleAnswerClick = (index) => {
    if (isAnswered) return;
    setSelectedIdx(index);
    setIsAnswered(true);
  };

  const getButtonStatus = (index) => {
    if (!isAnswered) return 'Default';
    
    // 첫 번째(index 0)를 정답으로 가정
    const isCorrect = index === 0;
    
    if (index === selectedIdx) {
      return isCorrect ? 'Correct' : 'Incorrect';
    }
    
    if (isCorrect) return 'Correct';
    
    return 'Disable';
  };

  const answers = [
    { parts: [{ text: "글씨", type: "normal" }, { text: "쓰는 ", type: "highlight" }, { text: "연습을 하세요.", type: "normal" }] },
    { parts: [{ text: "어제", type: "normal" }, { text: "쓴", type: "highlight" }, { text: "우산을 말리고 있어요.", type: "normal" }] },
    { parts: [{ text: "모자", type: "normal" }, { text: "쓴", type: "highlight" }, { text: "사람을 보았어요.", type: "normal" }] },
    { parts: [{ text: "이 소스는 조금", type: "normal" }, { text: "쓰네요", type: "highlight" }] }
  ];

  return (
    <>
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

        {/* Feed Image OR Pronounce Area */}
        {isAnswered ? (
          <PronounceArea onFinish={onStageUnlock} />
        ) : (
          <div className="relative self-stretch">
            <img
              className="w-full h-80 object-cover rounded-[20px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text"
              src="https://placehold.co/330x330"
              alt="feed"
            />
            {/* Heart Button */}
            <div className="absolute right-4 bottom-4 p-3.5 bg-bg rounded-[32px] outline outline-[2.40px] outline-offset-[-2.40px] outline-text inline-flex justify-start items-center gap-6 overflow-hidden">
              <div className="flex justify-start items-center gap-1">
                <div className="relative">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M19.2373 6.23731C20.7839 7.78395 20.8432 10.2727 19.3718 11.8911L11.9995 20.0001L4.62812 11.8911C3.15679 10.2727 3.21605 7.7839 4.76269 6.23726C6.48961 4.51034 9.33372 4.66814 10.8594 6.5752L12 8.00045L13.1396 6.57504C14.6653 4.66798 17.5104 4.51039 19.2373 6.23731Z" fill="var(--color-ari-primary, #D95B7A)" stroke="var(--color-text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div className="justify-start text-text text-lg font-semibold font-sans">25</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer (Answers) */}
      <div className="self-stretch h-60 flex flex-col justify-center items-center gap-2.5">
        <div className="self-stretch flex flex-col justify-end items-center gap-2.5">
          {answers.map((answer, index) => (
            <AnswerButton 
              key={index}
              parts={answer.parts}
              status={getButtonStatus(index)}
              onClick={() => handleAnswerClick(index)}
            />
          ))}
        </div>
      </div>
    </>
  );
}
