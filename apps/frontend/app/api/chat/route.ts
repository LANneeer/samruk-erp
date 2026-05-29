import {
  consumeStream,
  convertToModelMessages,
  streamText,
  UIMessage,
} from 'ai'

export const maxDuration = 30

const API_BASE_URL = process.env.NEXT_PUBLIC_DOCUMENTS_API_URL || 'Error: undefined NEXT_PUBLIC_DOCUMENTS_API_URL'

// Helper to search document chunks for context
async function searchDocumentContext(documentId: string, query: string): Promise<string> {
  if (!API_BASE_URL || !documentId) return ''
  
  try {
    const res = await fetch(
      `${API_BASE_URL}/documents/${documentId}/chunks/search?query=${encodeURIComponent(query)}&limit=5`
    )
    
    if (!res.ok) return ''
    
    const chunks = await res.json()
    if (!chunks || chunks.length === 0) return ''
    
    return chunks.map((chunk: { content: string }) => chunk.content).join('\n\n---\n\n')
  } catch (err) {
    console.error('Failed to search document:', err)
    return ''
  }
}

export async function POST(req: Request) {
  const { messages, documentId, documentTitle }: { 
    messages: UIMessage[]
    documentId?: string
    documentTitle?: string 
  } = await req.json()

  // Get the last user message for context search
  const lastMessage = messages[messages.length - 1]
  const userQuery = lastMessage?.parts
    ?.filter((p): p is { type: 'text'; text: string } => p.type === 'text')
    .map((p) => p.text)
    .join('') || ''

  // Search for relevant document context
  let documentContext = ''
  if (documentId && userQuery) {
    documentContext = await searchDocumentContext(documentId, userQuery)
  }

  const systemPrompt = `You are an AI assistant for the Samruk-Kazyna Reports Portal, helping users analyze and understand business reports from portfolio companies of the Samruk-Kazyna National Welfare Fund of Kazakhstan.

Your capabilities:
- Analyze Excel report data and provide insights
- Answer questions about report contents
- Summarize key metrics and findings
- Help verify data integrity and identify anomalies
- Explain financial and business terminology

Guidelines:
- Be professional and concise
- When analyzing data, cite specific values when possible
- If you don't have enough context to answer a question, ask for clarification
- Focus on factual analysis rather than speculation

${documentTitle ? `Current document: ${documentTitle}` : 'No document currently selected.'}

${documentContext ? `
Relevant content from the document:
---
${documentContext}
---
` : ''}

If the user asks about specific data and no document context is available, suggest they open a specific report first.`

  const result = streamText({
    model: 'openai/gpt-4o-mini',
    system: systemPrompt,
    messages: await convertToModelMessages(messages),
    abortSignal: req.signal,
  })

  return result.toUIMessageStreamResponse({
    originalMessages: messages,
    consumeSseStream: consumeStream,
  })
}
