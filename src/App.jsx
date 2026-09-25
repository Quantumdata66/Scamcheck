import { useState } from 'react';
import Header from './components/header/header';
import Hero from './components/hero/hero';
import HowItWorks from './components/howitworks/howitworks';
import TheResult from './components/theresult/theresult';
import WhatWeCheck from './components/whatwecheck/whatwecheck';
import BeforeYouAct from './components/beforeyouact/beforeyouact';
import FAQ from './components/faq/faq';
import Footer from './components/footer/footer';
import { checkMessage } from './services/api';

function App() {
  const [userInput, setUserInput] = useState('');
  const [status, setStatus] = useState('idle'); // 'idle' | 'loading' | 'success' | 'error'
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [validationError, setValidationError] = useState(null);

  const handleCheckMessage = async (text) => {
    // Client-side validation
    const trimmed = (text || '').trim();
    if (!trimmed) {
      setValidationError('Please enter a message to analyze.');
      return;
    }
    if (trimmed.length > 2000) {
      setValidationError('Message exceeds the 2000 character limit.');
      return;
    }

    setValidationError(null);
    setError(null);
    setStatus('loading');

    // Scroll toward result section when check starts
    const resultElement = document.getElementById('result');
    if (resultElement) {
      resultElement.scrollIntoView({ behavior: 'smooth' });
    }

    try {
      const data = await checkMessage(trimmed);
      setResult(data);
      setStatus('success');

      // Ensure smooth scroll to result card on completion
      setTimeout(() => {
        const target = document.getElementById('result');
        if (target) {
          target.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    } catch (err) {
      console.error('ScamCheck analysis failed:', err);
      setError(err.message || 'An error occurred during message analysis.');
      setStatus('error');
    }
  };

  const handleReset = () => {
    setUserInput('');
    setStatus('idle');
    setResult(null);
    setError(null);
    setValidationError(null);

    const checkElement = document.getElementById('check');
    if (checkElement) {
      checkElement.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <>
      <Header />
      <Hero
        userInput={userInput}
        setUserInput={setUserInput}
        onCheck={handleCheckMessage}
        isLoading={status === 'loading'}
        validationError={validationError}
      />
      <HowItWorks />
      <TheResult
        status={status}
        result={result}
        error={error}
        onReset={handleReset}
      />
      <WhatWeCheck />
      <BeforeYouAct />
      <FAQ />
      <Footer />
    </>
  );
}

export default App;
