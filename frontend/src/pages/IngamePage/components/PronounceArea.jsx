import React, { useState, useEffect } from 'react';
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

export default function PronounceArea({ onFinish }) {
  const [step, setStep] = useState(1); // 1: 준비, 2: 녹음중, 3: 분석중, 4: 결과
  const [seconds, setSeconds] = useState(0);
  const [isExiting, setIsExiting] = useState(false);

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
      setSeconds(0);
      interval = setInterval(() => {
        setSeconds(prev => prev + 1);
      }, 1000);
    } else {
      setSeconds(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [step]);

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  useEffect(() => {
    if (step === 3) {
      const timer = setTimeout(() => {
        transitionToStep(4);
        if (onFinish) onFinish();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [step, onFinish]);

  return (
    <div className={styles.pronounceArea}>

      {step === 1 && (
        <div className={`${styles.stepContainer} ${styles.fadeIn} ${isExiting ? styles.fadeOut : ''}`}>
          <div className={styles.stepHeader}>
            발음을 듣고 녹음을 시작하세요.
          </div>
          <div className={styles.centerContent}>
            <PronounceButton word="쓰는" onClick={() => console.log('Play sound')} />
          </div>
          <SimpleIconButton type="record" onClick={() => transitionToStep(2)} />
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
          <SimpleIconButton type="stop" onClick={() => transitionToStep(3)} />
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
            “쓰다”에 대한 발음 정확성
          </div>
          <div className={styles.centerContentGap4}>
            <div className={styles.scoreText}>89점</div>
            <div className={styles.descText}>
              전체적인 발음의 정확도는 우수하나, 문장 끝부분의 억양 처리가 다소 부자연스러웠습니다. 특히 특정 단어의 모음 발음이 짧게 처리되어 명확도가 조금 떨어졌습니다.
            </div>
          </div>

          <SimpleIconButton type="retry" onClick={() => transitionToStep(1)} />
        </div>
      )}

    </div>
  );
}
