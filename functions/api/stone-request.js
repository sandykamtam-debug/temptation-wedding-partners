export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    const data = await request.json();
    const { name, partner, email, phone, month, stone } = data;

    if (!name || !email || !month) {
      return new Response(JSON.stringify({ error: 'Missing required fields' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const subject = 'Custom Stone Request — ' + (stone || month) + ' (' + name + ')';
    const text =
      'Name: ' + name + '\n' +
      'Partner: ' + (partner || '—') + '\n' +
      'Email: ' + email + '\n' +
      'Phone: ' + (phone || '—') + '\n' +
      'Birth month: ' + month + '\n' +
      'Stone: ' + (stone || '—');

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
