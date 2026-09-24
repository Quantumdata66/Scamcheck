import { useState } from 'react';
import './hero.css';

export default function Hero() {
  const [userInput, setUserInput] = useState('');

  const handleUserInputChange = (event) => {
    const { value } = event.target;
    setUserInput(value);
  };

  return (
    <>
      <section className='hero' id='check'>
        <div className='intro'>
          <h4>DIGITAL SAFETY, MADE SIMPLE</h4>

          <h1>
            Check before <br />
            you trust
          </h1>
          <p>
            Got a suspicious message? Paste it below. ScamCheck looks for common
            warning signs and helps you understand what to check.
          </p>
        </div>

        <div className='input-field'>
          <textarea
            name='user-input'
            value={userInput}
            onChange={handleUserInputChange}
            maxLength={200}
            placeholder='Paste the suspicious message here...'
          ></textarea>

          <div className='below-input'>
            <h5>{`${userInput.length} / 200`}</h5>

            <button disabled={!userInput.trim()}>Check Message</button>
          </div>
        </div>
        <p className='note'>ScamCheck gives an assessment, not a guarantee</p>
      </section>
    </>
  );
}
