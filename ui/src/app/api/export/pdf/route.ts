import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const draft = await req.json();

  const response = await fetch(`${process.env.REMOTE_ACTION_URL}/export/pdf`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(draft),
  });

  if (!response.ok) {
    return NextResponse.json({ error: 'Failed to generate PDF' }, { status: response.status });
  }

  const pdfBlob = await response.blob();
  return new NextResponse(pdfBlob, {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': 'attachment; filename="research_draft.pdf"',
    },
  });
}
