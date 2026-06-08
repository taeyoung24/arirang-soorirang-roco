import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { resolveAssetUrl, submitCardAnswer } from 'src/api'
import AnswerButton from '../components/AnswerButton'
import PronounceArea from '../components/PronounceArea'
import styles from './QuizView.module.css'

const sentenceToParts = (sentence = '', word = '') => {
  const index = sentence.indexOf(word)

  if (!word || index < 0) {
    return [{ text: sentence, type: 'normal' }]
  }

  return [
    { text: sentence.slice(0, index), type: 'normal' },
    { text: sentence.slice(index, index + word.length), type: 'highlight' },
    { text: sentence.slice(index + word.length), type: 'normal' },
  ].filter((part) => part.text)
}

export default function QuizView({ card, title = '', progress = '', onStageUnlock }) {
  const { t } = useTranslation()
  const [selectedChoiceId, setSelectedChoiceId] = useState(null)
  const [wrongChoiceIds, setWrongChoiceIds] = useState([])
  const [correctChoiceId, setCorrectChoiceId] = useState(null)
  const [isAnswered, setIsAnswered] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  if (!card) {
    return (
      <div className={styles.topArea}>
        <div className={styles.textArea}>
          <div className={styles.title}>학습 카드가 없습니다.</div>
        </div>
      </div>
    )
  }

  const handleAnswerClick = async (choice) => {
    if (!card || isSubmitting || correctChoiceId) return

    setSelectedChoiceId(choice.choice_id)
    setIsSubmitting(true)
    setErrorMessage('')

    try {
      const result = await submitCardAnswer(card.card_id, choice.choice_id)
      setIsAnswered(true)

      if (result.is_correct) {
        setCorrectChoiceId(choice.choice_id)
        return
      }

      setWrongChoiceIds((current) => (
        current.includes(choice.choice_id) ? current : [...current, choice.choice_id]
      ))
    } catch (error) {
      console.error('정답 제출에 실패했습니다:', error)
      setErrorMessage(error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const getButtonStatus = (choice) => {
    if (choice.choice_id === correctChoiceId) return 'Correct'
    if (wrongChoiceIds.includes(choice.choice_id)) return 'Incorrect'
    if (!isAnswered) return choice.choice_id === selectedChoiceId ? 'Selected' : 'Default'
    if (choice.choice_id === selectedChoiceId) return 'Selected-Incorrect'

    return 'Disable'
  }

  const selectedChoice = card.choices.find((choice) => choice.choice_id === selectedChoiceId)
  const correctChoice = card.choices.find((choice) => choice.choice_id === correctChoiceId)
  const pronunciationTarget = card.prompt_sentence
  const questionParts = sentenceToParts(card.prompt_sentence, card.highlight || card.polysemy_word)
  const selectedChoiceParts = selectedChoice
    ? sentenceToParts(selectedChoice.text, selectedChoice.highlight || card.polysemy_word)
    : questionParts
  const displayParts = wrongChoiceIds.includes(selectedChoiceId)
    ? selectedChoiceParts
    : questionParts

  return (
    <>
      <div className={styles.topArea}>
        <div className={styles.textArea}>
          <div className={styles.title}>
            {t('quiz_instruction')}
          </div>
          {(title || progress) && (
            <div className={styles.normalText}>
              {title} {progress}
            </div>
          )}
        </div>

        <div className={styles.questionWrapper}>
          <span className={styles.normalText}>“</span>
          {displayParts.map((part, index) => {
            if (part.type === 'highlight') {
              return (
                <div key={index} className={styles.highlightBlock}>
                  <span className={styles.highlightText}>{part.text}</span>
                </div>
              )
            }
            return <span key={index} className={styles.normalText}>{part.text}</span>
          })}
          <span className={styles.normalText}>”</span>
        </div>

        {correctChoiceId ? (
          <PronounceArea
            cardId={card.card_id}
            targetText={pronunciationTarget}
            ttsUrl={card.tts_url}
            onFinish={onStageUnlock}
          />
        ) : (
          <div className={styles.imageWrapper}>
            <img
              className={styles.feedImage}
              src={resolveAssetUrl(card.image_url)}
              alt="feed"
            />
          </div>
        )}

        {errorMessage && (
          <div className={styles.normalText}>
            {errorMessage}
          </div>
        )}
      </div>

      <div data-testid="footer" className={styles.footer}>
        {card.choices.map((choice) => (
          <AnswerButton
            key={choice.choice_id}
            parts={sentenceToParts(choice.text, choice.highlight || card.polysemy_word)}
            status={getButtonStatus(choice)}
            onClick={() => handleAnswerClick(choice)}
          />
        ))}
      </div>
    </>
  )
}
