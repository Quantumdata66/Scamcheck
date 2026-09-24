import './beforeyouact.css';

export default function BeforeYouAct() {
  return (
    <>
      <section className='before-you-act'>
        <div className='act-intro'>
          <h4>BEFORE YOU ACT</h4>

          <h2>
            A result is a reason to check, <br />
            not a reason to panic.
          </h2>

          <p>
            ScamCheck is there to help you look twice at a message. Important
            requests should still be verified independently.
          </p>
        </div>

        <div className='act-cards'>
          <div className='act-card'>
            <img
              src='https://unpkg.com/lucide-static@latest/icons/shield.svg'
              alt='Shield'
              className='card-icon'
            />
            <h3>No warning signs doesn’t mean safe.</h3>
            <p>
              A legitimate-looking message can still be fraudulent. Always
              verify important requests through a trusted channel.
            </p>
          </div>

          <div className='act-card'>
            <img
              src='https://unpkg.com/lucide-static@latest/icons/lock.svg'
              alt='Lock'
              className='card-icon'
            />
            <h3>Keep your information yours.</h3>
            <p>
              Don’t give out passwords, OTPs, payment details or other sensitive
              information because a message asks for them.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
