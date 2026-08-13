export async function onRequestPost(context) {
  try {
    const { request, env } = context;
    const data = await request.json();
    const { fname, bname, email, phone, region, volume } = data;

    if (!fname || !bname || !email) {
      return new Response(JSON.stringify({ error: 'Missing required fields' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const subject = 'Wedding Partner Program inquiry — ' + (bname || fname);
    const text =
      'Name: ' + fname + '\n' +
      'Business: ' + bname + '\n' +
      'Email: ' + email + '\n' +
      'Phone: ' + (phone || '—') + '\n' +
      'Region: ' + (region || '—') + '\n' +
      'Expected couples / year: ' + (volume || '—');

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
