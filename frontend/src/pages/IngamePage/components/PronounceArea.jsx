import React, { useState, useEffect, useRef } from 'react';
import { evaluatePronunciation, resolveMediaUrl } from 'src/api';
import { PronounceButton, SimpleIconButton } from 'src/components/Button';
import styles from './PronounceArea.module.css';


function AudioWaveform() {
  const [bars, setBars] = useState([8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]);

  useEffect(() => {
    let audioContext = null;
    let analyser = null;
    let source = null;
    let stream = null;
    let animationRef = null;
    let isMounted = true; // 마운트 여부를 추적하는 플래그

    async function initAudio() {
      try {
        const s = await navigator.mediaDevices.getUserMedia({ audio: true });

        // await 완료 시점에 이미 언마운트 됐다면 즉시 트랙 종료
        if (!isMounted) {
          s.getTracks().forEach(track => track.stop());
          return;
        }

        stream = s;
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        audioContext = new AudioContextClass();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 32;

        source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const updateWaveform = () => {
          if (!analyser || !isMounted) return;
          analyser.getByteFrequencyData(dataArray);

          // Map frequency data to height (Min 8px, Max 70px)
          const newHeights = Array.from(dataArray).slice(0, 12).map(val => {
            return Math.max(8, (val / 255) * 70);
          });

          setBars(newHeights);
          animationRef = requestAnimationFrame(updateWaveform);
        };

        updateWaveform();
      } catch (err) {
        console.error('Failed to access microphone:', err);
      }
    }

    initAudio();

    return () => {
      isMounted = false; // 언마운트 시 플래그 해제
      if (animationRef) cancelAnimationFrame(animationRef);
      if (stream) stream.getTracks().forEach(track => track.stop());
      if (audioContext) audioContext.close();
    };
  }, []);

  return (
    <div className={styles.waveformContainer}>
      {bars.map((height, i) => (
        <div
          key={i}
          className={styles.waveBar}
          style={{ height: `${height}px` }}
        />
      ))}
    </div>
  );
}

export default function PronounceArea({ cardId, targetText, ttsUrl, onFinish }) {
  const [step, setStep] = useState(1); // 1: 준비, 2: 녹음중, 3: 분석중, 4: 결과
  const [seconds, setSeconds] = useState(0);
  const [isExiting, setIsExiting] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isPlayingTts, setIsPlayingTts] = useState(false);
  const ttsAudioRef = useRef(null);

  const transitionToStep = (nextStep) => {
    setIsExiting(true);
    setTimeout(() => {
      setStep(nextStep);
      setIsExiting(false);
    }, 300); // Wait for 300ms fadeOut to complete
  };

  useEffect(() => {
    let interval = null;
    if (step === 2) {
      interval = setInterval(() => {
        setSeconds(prev => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [step]);

  useEffect(() => {
    return () => {
      if (mediaRecorder?.stream) {
        mediaRecorder.stream.getTracks().forEach((track) => track.stop());
      }
      if (ttsAudioRef.current) {
        ttsAudioRef.current.pause();
        ttsAudioRef.current = null;
      }
    }
  }, [mediaRecorder]);

  const playTts = async () => {
    if (!ttsUrl || isPlayingTts) return;

    setErrorMessage('');
    try {
      if (ttsAudioRef.current) {
        ttsAudioRef.current.pause();
      }

      const audio = new Audio(resolveMediaUrl(ttsUrl));
      ttsAudioRef.current = audio;
      setIsPlayingTts(true);

      audio.onended = () => setIsPlayingTts(false);
      audio.onerror = () => {
        setIsPlayingTts(false);
        setErrorMessage('음성을 불러오지 못했습니다.');
      };

      await audio.play();
    } catch (error) {
      console.error('TTS 재생에 실패했습니다:', error);
      setIsPlayingTts(false);
      setErrorMessage('음성을 재생하지 못했습니다.');
    }
  };

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const submitAudio = async (chunks) => {
    transitionToStep(3);
    setErrorMessage('');

    // NOTE: [테스트용 임시 코드] 실제 발음 분석 API 호출 생략하고 즉시 통과 처리 (26. 6. 8., 정태영)
    setTimeout(() => {
      const mockResult = {
        score: 95,
        heard_text: targetText,
        feedback: "참 잘하셨습니다! (테스트용 자동 패스)"
      };
      setResult(mockResult);
      transitionToStep(4);
      onFinish?.(mockResult);
    }, 500);

    // API 호출 코드
    // try {
    //   const audioBlob = new Blob(chunks.length ? chunks : [''], { type: 'audio/webm' });
    //   const formData = new FormData();
    //   formData.append('target_text', targetText);
    //   formData.append('audio_file', audioBlob, `${cardId}.webm`);
    //   const pronunciationResult = await evaluatePronunciation(cardId, formData);

    //   setResult(pronunciationResult);
    //   transitionToStep(4);
    //   onFinish?.(pronunciationResult);
    // } catch (error) {
    //   console.error('발음 평가에 실패했습니다:', error);
    //   setErrorMessage(error.message);
    //   transitionToStep(1);
    // }

  };

  const startRecording = async () => {
    setResult(null);
    setAudioChunks([]);
    setSeconds(0);
    setErrorMessage('');

    try {
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        transitionToStep(2);
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
          setAudioChunks((current) => [...current, event.data]);
        }
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        submitAudio(chunks);
      };
      recorder.start();
      setMediaRecorder(recorder);
      transitionToStep(2);
    } catch (error) {
      console.error('마이크를 시작하지 못했습니다:', error);
      transitionToStep(2);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      return;
    }

    submitAudio(audioChunks);
  };

  return (
    <div className={styles.pronounceArea}>

      {step === 1 && (
        <div className={`${styles.stepContainer} ${styles.fadeIn} ${isExiting ? styles.fadeOut : ''}`}>
          <div className={styles.stepHeader}>
            발음을 듣고 녹음을 시작하세요.
          </div>
          <div className={styles.centerContent}>
            <PronounceButton
              word={targetText}
              onClick={playTts}
              disabled={!ttsUrl || isPlayingTts}
            />
          </div>
          {errorMessage && <div className={styles.descText}>{errorMessage}</div>}
          <SimpleIconButton type="record" onClick={startRecording} />
        </div>
      )}

      {step === 2 && (
        <div className={`${styles.stepContainer} ${styles.fadeIn} ${isExiting ? styles.fadeOut : ''}`}>
          <div className={styles.stepHeader}>
            따라 말해보세요.
          </div>
          <div className={styles.centerContent}>
            <AudioWaveform />
            <div className={styles.timer}>{formatTime(seconds)}</div>
          </div>
          <SimpleIconButton type="stop" onClick={stopRecording} />
        </div>
      )}

      {step === 3 && (
        <div className={`${styles.stepContainer} ${styles.fadeIn} ${isExiting ? styles.fadeOut : ''}`}>
          <div className={styles.centerContent}>
            <div className={styles.stepHeader}>
              음성을 분석하는 중입니다.
            </div>
            <div className={styles.aiLoadingBar}>
              <div className={styles.aiWave} />
            </div>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className={`${styles.stepContainer} ${styles.fadeIn} ${isExiting ? styles.fadeOut : ''}`}>
          <div className={styles.stepHeader}>
            “{targetText}”에 대한 발음 정확성
          </div>
          <div className={styles.resultContent}>
            <div className={styles.scoreText}>{result?.score ?? 0}점</div>
            {result?.heard_text && (
              <div className={styles.heardPanel}>
                <span className={styles.heardLabel}>AI가 들은 발음</span>
                <span className={styles.heardText}>“{result.heard_text}”</span>
              </div>
            )}
            <div className={styles.descText}>
              {result?.feedback || '분석 결과가 없습니다.'}
            </div>
          </div>

          <SimpleIconButton type="retry" onClick={() => transitionToStep(1)} />
        </div>
      )}

    </div>
  );
}
