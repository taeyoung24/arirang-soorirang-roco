import React, { useState } from 'react';
import AnswerButton from '../components/AnswerButton';
import PronounceArea from '../components/PronounceArea';
import HeartButton from '../components/HeartButton';
import styles from './QuizView.module.css';

export default function QuizView({ onStageUnlock }) {
  const [selectedIdx, setSelectedIdx] = useState(null);
  const [initialWrongIdx, setInitialWrongIdx] = useState(null);
  const [isAnswered, setIsAnswered] = useState(false);

  const handleAnswerClick = (index) => {
    if (!isAnswered) {
      setIsAnswered(true); // 첫 클릭 시 답변 완료 상태로 전환
      if (index !== 0) {
        setInitialWrongIdx(index); // 처음 선택한 오답을 기억
      }
    }
    setSelectedIdx(index); // 클릭한 선택지로 뷰 전환
  };

  const getButtonStatus = (index) => {
    if (!isAnswered) return 'Default'; // 답변 전

    // 답변 후
    if (index === 0) return 'Correct'; // 정답은 항상 Correct (초록색)
    if (index === initialWrongIdx) return 'Incorrect'; // 처음 고른 오답은 영구적으로 Incorrect (빨간색)
    if (index === selectedIdx) return 'Selected-Incorrect'; // 현재 탐색 중인 다른 오답은 활성화 (흰색 배경에 X)

    return 'Disable'; // 선택되지 않은 오답은 비활성화
  };

  const answers = [
    { parts: [{ text: "글씨", type: "normal" }, { text: "쓰는 ", type: "highlight" }, { text: "연습을 하세요.", type: "normal" }] },
    { parts: [{ text: "어제", type: "normal" }, { text: "쓴", type: "highlight" }, { text: "우산을 말리고 있어요.", type: "normal" }] },
    { parts: [{ text: "모자", type: "normal" }, { text: "쓴", type: "highlight" }, { text: "사람을 보았어요.", type: "normal" }] },
    { parts: [{ text: "이 소스는 조금", type: "normal" }, { text: "쓰네요", type: "highlight" }] }
  ];

  return (
    <>
      <div className={styles.topArea}>
        {/* Text Area */}
        <div className={styles.textArea}>
          <div className={styles.title}>
            같은 의미로 사용된 문장을 고르세요.
          </div>
        </div>

        {/* Question Sentence */}
        {isAnswered && selectedIdx !== 0 && selectedIdx !== null ? (
          <div className={styles.questionWrapper}>
            <span className={styles.normalText}>“</span>
            {answers[selectedIdx].parts.map((part, index) => {
              if (part.type === 'highlight') {
                return (
                  <div key={index} className={styles.highlightBlock}>
                    <span className={styles.highlightText}>{part.text}</span>
                  </div>
                );
              }
              return <span key={index} className={styles.normalText}>{part.text}</span>;
            })}
            <span className={styles.normalText}>”</span>
          </div>
        ) : (
          <div className={styles.questionWrapper}>
            <span className={styles.normalText}>“</span>
            <span className={styles.normalText}>저는 매일 저녁에 일기를</span>
            <div className={styles.highlightBlock}>
              <span className={styles.highlightText}>써요</span>
            </div>
            <span className={styles.normalText}>”</span>
          </div>
        )}

        {/* Feed Image OR Pronounce Area */}
        {isAnswered && selectedIdx === 0 ? (
          <PronounceArea onFinish={onStageUnlock} />
        ) : (
          <div className={styles.imageWrapper}>
            <img
              className={styles.feedImage}
              src={selectedIdx !== null && selectedIdx !== 0 ? `https://placehold.co/330x330?text=Option+${selectedIdx + 1}` : "https://placehold.co/330x330?text=Initial+Image"}
              alt="feed"
            />
            {/* Heart Button */}
            <HeartButton initialCount={25} className={styles.heartButtonPos} />

          </div>
        )}
      </div>

      {/* Footer (Answers) */}
      <div data-testid="footer" className={styles.footer}>
        {answers.map((answer, index) => (
          <AnswerButton
            key={index}
            parts={answer.parts}
            status={getButtonStatus(index)}
            onClick={() => handleAnswerClick(index)}
          />
        ))}
      </div>
    </>
  );
}
