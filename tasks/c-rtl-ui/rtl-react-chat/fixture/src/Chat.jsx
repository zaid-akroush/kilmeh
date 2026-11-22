export default function Chat() {
  return (
    <main className="chat" data-testid="chat-ready">
      <header className="chat-header">
        <h1>خدمة العملاء</h1>
      </header>

      <section className="thread">
        <div className="row row-them">
          <span className="avatar" data-testid="avatar" style={{ position: 'absolute', left: 0 }}>
            CS
          </span>
          <div className="bubble" data-testid="bubble-them" style={{ marginLeft: 44 }}>
            <p>مرحباً، كيف يمكنني مساعدتك؟</p>
            <time className="time" style={{ textAlign: 'right' }}>10:02</time>
          </div>
        </div>

        <div className="bubble bubble-me" data-testid="bubble-me" style={{ marginLeft: 'auto' }}>
          <p>
            اشتريت هاتف <span data-testid="product">iPhone 17</span> من متجركم
          </p>
          <time className="time" style={{ textAlign: 'right' }}>10:03</time>
        </div>

        <div className="row row-them">
          <span className="avatar" data-testid="avatar" style={{ position: 'absolute', left: 0 }}>
            CS
          </span>
          <div className="bubble" data-testid="bubble-them" style={{ marginLeft: 44 }}>
            <p>
              رقم طلبك هو <span data-testid="order">ORD-48213</span> وهو في الطريق إليك
            </p>
            <time className="time" style={{ textAlign: 'right' }}>10:04</time>
          </div>
        </div>

        <div className="order-card" data-testid="order-card">
          <strong>تفاصيل الطلب</strong>
          <div className="bar" />
        </div>

        <div className="bubble bubble-me" data-testid="bubble-me" style={{ marginLeft: 'auto' }}>
          <p>شكراً، سأنتظر</p>
          <time className="time" style={{ textAlign: 'right' }}>10:05</time>
        </div>
      </section>

      <form className="composer" onSubmit={(e) => e.preventDefault()}>
        <textarea data-testid="composer" placeholder="اكتب رسالتك" rows={1} />
        <button className="send" type="submit">إرسال</button>
      </form>
    </main>
  );
}
