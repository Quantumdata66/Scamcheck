import './hero.css';

export default function Hero({
  userInput = '',
  setUserInput,
  onCheck,
  isLoading = false,
  validationError = null,
}) {
  const handleUserInputChange = (event) => {
    const { value } = event.target;
    setUserInput(value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!userInput.trim() || isLoading) return;
    onCheck(userInput);
  };

  const handleKeyDown = (e) => {
    // Allow Ctrl+Enter or Cmd+Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  return (
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

      <form className='input-field' onSubmit={handleSubmit}>
        <textarea
          name='user-input'
          value={userInput}
          onChange={handleUserInputChange}
          onKeyDown={handleKeyDown}
          maxLength={2000}
          disabled={isLoading}
          placeholder='Paste the suspicious message here (up to 2000 characters)...'
          aria-label='Suspicious message input'
        ></textarea>

        {validationError && (
          <div className='hero-error-text' role='alert'>
            {validationError}
          </div>
        )}

        <div className='below-input'>
          <h5>{`${userInput.length} / 2000`}</h5>

          <button
            type='submit'
            disabled={!userInput.trim() || isLoading}
            className={isLoading ? 'btn-loading' : ''}
          >
            {isLoading ? 'Analyzing...' : 'Check Message'}
          </button>
        </div>
      </form>
      <p className='note'>ScamCheck gives an assessment, not a guarantee</p>
    </section>
  );
}
