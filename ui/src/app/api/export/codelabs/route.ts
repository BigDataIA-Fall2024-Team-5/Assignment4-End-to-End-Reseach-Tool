import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const draft = await req.json();

  const response = await fetch('http://localhost:8000/export/codelabs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(draft),
  });

  if (!response.ok) {
    return NextResponse.json({ error: 'Failed to generate Codelabs file' }, { status: response.status });
  }

  const txtBlob = await response.blob();
  return new NextResponse(txtBlob, {
    headers: {
      'Content-Type': 'text/plain',
      'Content-Disposition': 'attachment; filename="research_draft_codelabs.txt"',
    },
  });
}
