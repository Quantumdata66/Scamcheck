import './theresult.css';

export default function Result() {
  return (
    <>
      <section className='result'>
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

        <div className='result-card'>
          <div className='badge'>Needs further verification</div>

          <h3>This message contains some warning signs.</h3>

          <p className='card-description'>
            This doesn’t prove that the message is a scam. It means there are
            things worth checking before you take action.
          </p>

          <hr className='divider' />

          <div className='result-details'>
            <div className='details-column'>
              <h5>What we noticed</h5>
              <ul>
                <li>Urgent request for payment</li>
                <li>Possible impersonation language</li>
                <li>Request for sensitive information</li>
              </ul>
            </div>

            <div className='details-column'>
              <h5>What you can do</h5>
              <ul>
                <li>Verify the sender independently</li>
                <li>Don’t share OTPs or passwords</li>
                <li>Don’t act while you’re unsure</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
