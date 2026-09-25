import './theresult.css';

const CATEGORY_NAMES = {
  bank_payment: 'Bank & Payment Scam',
  fake_job: 'Fake Job Offer',
  investment: 'Investment Scam',
};

export default function Result({
  status = 'idle',
  result = null,
  error = null,
  onReset,
}) {
  const categoryLabel = result?.category ? CATEGORY_NAMES[result.category] || result.category : null;

  return (
    <section className='result' id='result'>
      <div className='result-intro'>
        <h4>THE RESULT</h4>

        <h2>
          You get more than <br />
          just a label.
        </h2>

        <p>
          ScamCheck shows the warning signs behind an assessment so you can
          understand it.
        </p>
      </div>

      {/* IDLE STATE */}
      {status === 'idle' && (
        <div className='result-card result-card--idle'>
          <div className='badge badge--idle'>Ready to check</div>

          <h3>Paste a message above to see results</h3>

          <p className='card-description'>
            When you check a message, ScamCheck evaluates the text for common
            impersonation cues, urgency patterns, and financial traps.
          </p>

          <hr className='divider' />

          <div className='result-details'>
            <div className='details-column'>
              <h5>What we look for</h5>
              <ul>
                <li>Urgent threats and pressure</li>
                <li>Credential and PIN harvesting</li>
                <li>Unrealistic pay or investment returns</li>
              </ul>
            </div>

            <div className='details-column'>
              <h5>Safe next steps</h5>
              <ul>
                <li>Independent verification channels</li>
                <li>Protecting sensitive credentials</li>
                <li>Safe reporting guidance</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* LOADING STATE */}
      {status === 'loading' && (
        <div className='result-card result-card--loading'>
          <div className='badge badge--loading'>Analyzing message...</div>

          <h3>Evaluating message text patterns</h3>

          <p className='card-description'>
            Scanning for scam indicators across bank impersonation, fake job offers,
            and investment schemes...
          </p>

          <hr className='divider' />

          <div className='loading-spinner-container'>
            <div className='spinner'></div>
            <p className='loading-subtext'>Processing indicators and safety guidance...</p>
          </div>
        </div>
      )}

      {/* ERROR STATE */}
      {status === 'error' && (
        <div className='result-card result-card--error'>
          <div className='badge badge--error'>Analysis Error</div>

          <h3>Unable to complete analysis</h3>

          <p className='card-description error-message-text'>
            {error || 'An unexpected error occurred while communicating with the analysis server.'}
          </p>

          <hr className='divider' />

          <div className='result-actions'>
            <button type='button' className='btn-reset' onClick={onReset}>
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* SUCCESS STATE */}
      {status === 'success' && result && (
        <div className={`result-card result-card--${result.risk_level}`}>
          <div className='result-card-header'>
            <div className={`badge badge--${result.risk_level}`}>
              {result.risk_label}
            </div>

            {categoryLabel && (
              <span className='category-tag'>
                {categoryLabel}
              </span>
            )}
          </div>

          <h3>{result.summary}</h3>

          <p className='card-description'>
            {result.explanation}
          </p>

          <hr className='divider' />

          <div className='result-details'>
            <div className='details-column'>
              <h5>What we noticed</h5>
              {result.indicators && result.indicators.length > 0 ? (
                <ul>
                  {result.indicators.map((indicator, index) => (
                    <li key={index}>{indicator}</li>
                  ))}
                </ul>
              ) : (
                <p className='no-indicators-note'>
                  No specific high-risk warning signs were identified in the text.
                </p>
              )}
            </div>

            <div className='details-column'>
              <h5>What you can do</h5>
              {result.safety_guidance && result.safety_guidance.length > 0 ? (
                <ul>
                  {result.safety_guidance.map((guidance, index) => (
                    <li key={index}>{guidance}</li>
                  ))}
                </ul>
              ) : (
                <ul>
                  <li>Always verify unexpected requests through trusted channels.</li>
                  <li>Never share one-time passcodes or passwords.</li>
                </ul>
              )}
            </div>
          </div>

          <div className='result-disclaimer'>
            <p>
              <strong>Important:</strong> A low-risk assessment means no obvious indicators were found in the text, but it is not a guarantee of safety. Sophisticated scams can still look convincing.
            </p>
          </div>

          <div className='result-actions'>
            <button type='button' className='btn-reset' onClick={onReset}>
              Check another message
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
