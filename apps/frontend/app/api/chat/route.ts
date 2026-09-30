import {
  consumeStream,
  convertToModelMessages,
  streamText,
  UIMessage,
} from 'ai'
import { openai } from '@ai-sdk/openai';

export const maxDuration = 30


if(!process.env.NEXT_PUBLIC_DOCUMENTS_API_URL)
    throw new Error('Error: undefined NEXT_PUBLIC_DOCUMENTS_API_URL')
const DOCUMENTS_API_URL = process.env.NEXT_PUBLIC_DOCUMENTS_API_URL 

if(!process.env.OPENAI_CHAT_MODEL)
    throw new Error("Error: undefined OPENAI_CHAT_MODEL")
const OPENAI_CHAT_MODEL = process.env.OPENAI_CHAT_MODEL

if(!process.env.OPENAI_API_KEY)
    throw new Error("Error: undefined OPENAI_API_KEY")

// Helper to search document chunks for context
async function searchDocumentContext(documentId: string, query: string): Promise<string> {
  const res = await fetch(
    `${DOCUMENTS_API_URL}/documents/${documentId}/search_chunks?query=${encodeURIComponent(query)}&limit=5`
  )

  if (!res.ok)
    throw new Error(`Failed search_chunks in document '${documentId}'`)

  const chunks = await res.json()
  if (!chunks || chunks.length === 0) return ''

  return chunks.map((chunk: { content: string }) => chunk.content).join('\n\n---\n\n')
}

export async function POST(req: Request) {
  const { messages, documentId, documentTitle }: { 
    messages: UIMessage[]
    documentId: string
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

    console.log(systemPrompt)
  const result = streamText({
    model: openai(OPENAI_CHAT_MODEL),
    system: systemPrompt,
    messages: await convertToModelMessages(messages),
    abortSignal: req.signal,
  })

  return result.toUIMessageStreamResponse({
    originalMessages: messages,
    consumeSseStream: consumeStream,
  })
}
