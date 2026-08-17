export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    const data = await request.json();
    const { name, partner, email, phone, size, mm, uk } = data;

    if (!name || !email || !size) {
      return new Response(JSON.stringify({ error: 'Missing required fields' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const subject = 'Ring Size Request — Size ' + size + ' (' + name + ')';
    const text =
      'Name: ' + name + '\n' +
      'Partner: ' + (partner || '—') + '\n' +
      'Email: ' + email + '\n' +
      'Phone: ' + (phone || '—') + '\n' +
      'Ring size (EU): ' + size + '\n' +
      'Ring size (UK): ' + (uk || '—') + '\n' +
      'Diameter: ' + (mm || '—');

    const resendResponse = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + env.RESEND_API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: 'Temptation Jewellery <onboarding@resend.dev>',
        to: ['sandy@temptationjewellery.com'],
        reply_to: email,
        subject: subject,
        text: text
      })
    });

    if (!resendResponse.ok) {
      const errText = await resendResponse.text();
      return new Response(JSON.stringify({ error: 'Email failed to send', detail: errText }), {
        status: 502,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: 'Server error', detail: String(err) }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
