import React, { useState } from 'react';
import { resolveAssetUrl, submitCardAnswer } from 'src/api';
import AnswerButton from '../components/AnswerButton';
import PronounceArea from '../components/PronounceArea';
import HeartButton from '../components/HeartButton';

const sentenceToParts = (sentence, word) => {
  const index = sentence.indexOf(word);

  if (!word || index < 0) {
    return [{ text: sentence, type: 'normal' }];
  }

  return [
    { text: sentence.slice(0, index), type: 'normal' },
    { text: sentence.slice(index, index + word.length), type: 'highlight' },
    { text: sentence.slice(index + word.length), type: 'normal' },
  ].filter((part) => part.text);
};

export default function QuizView({ cards = [], title = '', onStageUnlock }) {
  const [cardIndex, setCardIndex] = useState(0);
  const [selectedChoiceId, setSelectedChoiceId] = useState(null);
  const [wrongChoiceIds, setWrongChoiceIds] = useState([]);
  const [correctChoiceId, setCorrectChoiceId] = useState(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const card = cards[cardIndex];

  const resetAnswerState = () => {
    setSelectedChoiceId(null);
    setWrongChoiceIds([]);
    setCorrectChoiceId(null);
    setIsAnswered(false);
    setErrorMessage('');
  };

  const handleAnswerClick = async (choice) => {
    if (!card || isSubmitting || correctChoiceId) return;

    setSelectedChoiceId(choice.choice_id);
    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const result = await submitCardAnswer(card.card_id, choice.choice_id);
      setIsAnswered(true);

      if (result.is_correct) {
        setCorrectChoiceId(choice.choice_id);
        return;
      }

      setWrongChoiceIds((current) => (
        current.includes(choice.choice_id) ? current : [...current, choice.choice_id]
      ));
    } catch (error) {
      console.error('정답 제출에 실패했습니다:', error);
      setErrorMessage(error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePronunciationFinish = () => {
    onStageUnlock?.();
  };

  const handleNextCard = () => {
    if (cardIndex < cards.length - 1) {
      setCardIndex((current) => current + 1);
      resetAnswerState();
    }
  };

  const getButtonStatus = (choice) => {
    if (choice.choice_id === correctChoiceId) return 'Correct';
    if (wrongChoiceIds.includes(choice.choice_id)) return 'Incorrect';
    if (!isAnswered) return choice.choice_id === selectedChoiceId ? 'Selected' : 'Default';
    if (choice.choice_id === selectedChoiceId) return 'Selected-Incorrect';
    
    return 'Disable';
  };

  if (!card) {
    return (
      <div className="self-stretch flex-1 flex justify-center items-center text-text text-lg font-extrabold font-sans">
        학습 카드가 없습니다.
      </div>
    );
  }

  const questionParts = sentenceToParts(card.prompt_sentence, card.polysemy_word);
  const selectedChoice = card.choices.find((choice) => choice.choice_id === selectedChoiceId);
  const selectedChoiceParts = selectedChoice
    ? sentenceToParts(selectedChoice.text, card.polysemy_word)
    : questionParts;

  return (
    <>
      <div className="self-stretch flex flex-col justify-start items-center gap-3">
        <div className="self-stretch flex flex-col justify-start items-start gap-2">
          <div className="self-stretch text-text text-[24px] font-extrabold font-sans leading-tight break-keep">
            같은 의미로 사용된 문장을 고르세요.
          </div>
          {title && (
            <div className="self-stretch text-text text-base font-extrabold font-sans">
              {title} {cardIndex + 1}/{cards.length}
            </div>
          )}
        </div>
        
        <div className="self-stretch min-h-12 px-1 inline-flex justify-center items-center gap-1 flex-wrap content-center text-center">
          <span className="text-text text-base font-extrabold font-sans">“</span>
          {(wrongChoiceIds.includes(selectedChoiceId) ? selectedChoiceParts : questionParts).map((part, index) => {
            if (part.type === 'highlight') {
              return (
                <div key={index} className="px-0.5 border-b-[1.60px] border-text flex justify-center items-center gap-2.5">
                  <span className="text-text text-base font-extrabold font-sans leading-tight">{part.text}</span>
                </div>
              );
            }
            return <span key={index} className="text-text text-base font-extrabold font-sans leading-tight">{part.text}</span>;
          })}
          <span className="text-text text-base font-extrabold font-sans">”</span>
        </div>

        {correctChoiceId ? (
          <PronounceArea
            cardId={card.card_id}
            targetText={card.pronunciation_target}
            onFinish={handlePronunciationFinish}
            hasNext={cardIndex < cards.length - 1}
            onNext={handleNextCard}
          />
        ) : (
          <div className="relative self-stretch h-[270px] rounded-[20px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text overflow-hidden bg-yellow-primary">
            <img
              className="w-full h-full object-cover"
              src={resolveAssetUrl(card.image_url)}
              alt="feed"
            />
            <HeartButton initialCount={25} className="absolute right-4 bottom-4" />
          </div>
        )}
        {errorMessage && (
          <div className="self-stretch text-center text-ari-primary text-sm font-semibold font-sans">
            {errorMessage}
          </div>
        )}
      </div>

      <div className="self-stretch flex flex-col justify-center items-center gap-2.5">
        <div className="self-stretch flex flex-col justify-end items-center gap-2.5">
          {card.choices.map((choice) => (
            <AnswerButton 
              key={choice.choice_id}
              parts={sentenceToParts(choice.text, card.polysemy_word)}
              status={getButtonStatus(choice)}
              onClick={() => handleAnswerClick(choice)}
            />
          ))}
        </div>
      </div>
    </>
  );
}
