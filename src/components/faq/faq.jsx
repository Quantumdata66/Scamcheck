import { useState } from 'react';
import './faq.css';

export default function Faq() {
  const [openIndex, setOpenIndex] = useState(null);

  const faqData = [
    {
      question: 'What does ScamCheck check?',
      answer:
        'ScamCheck looks for patterns associated with known scam categories like bank fraud, fake job offers, and investment schemes.',
    },
    {
      question: 'Does it check where a link leads?',
      answer:
        'Currently, ScamCheck focuses on text-based patterns and language indicators rather than active link destination tracing.',
    },
    {
      question: 'Does a good result mean the message is safe?',
      answer:
        'Not necessarily. A clean result means no obvious warning signs were detected, but sophisticated scams can still bypass checks.',
    },
    {
      question: 'Should I rely on the result completely?',
      answer:
        'No. ScamCheck provides an initial assessment to help you stay vigilant, but important or financial requests should always be verified independently.',
    },
  ];

  const toggleFaq = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <>
      <section className='faq' id='faq'>
        <div className='faq-intro'>
          <h4>FAQ</h4>

          <h2>
            A few things you might <br />
            want to know.
          </h2>
        </div>

        <div className='faq-list'>
          {faqData.map((item, index) => (
            <div key={index} className='faq-item'>
              <div className='faq-question' onClick={() => toggleFaq(index)}>
                <h3>{item.question}</h3>
                <span className='faq-icon'>
                  {openIndex === index ? '−' : '+'}
                </span>
              </div>

              {openIndex === index && (
                <p className='faq-answer'>{item.answer}</p>
              )}
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
