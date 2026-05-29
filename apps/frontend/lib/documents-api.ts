// Documents microservice API client

const API_BASE_URL = process.env.NEXT_PUBLIC_DOCUMENTS_API_URL || 'Error: undefined NEXT_PUBLIC_DOCUMENTS_API_URL'

export interface Document {
  id: string
  title: string
  file_name: string
  author_id: string
  created_at: string
  updated_at: string
}

export interface DocumentChunk {
  id: string
  document_id: string
  content: string
  embedding: number[]
}

export interface DocumentUpdateDTO {
  title?: string | null
}

// List all documents with pagination
export async function listDocuments(skip = 0, limit = 50): Promise<Document[]> {
  const res = await fetch(`${API_BASE_URL}/documents?skip=${skip}&limit=${limit}`)
  if (!res.ok) {
    throw new Error('Failed to fetch documents')
  }
  return res.json()
}

// Get a single document by ID
export async function getDocument(documentId: string): Promise<Document> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}`)
  if (!res.ok) {
    throw new Error('Failed to fetch document')
  }
  return res.json()
}

// Create a new document (upload)
export async function createDocument(
  file: File,
  title: string,
  authorId: string
): Promise<Document> {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(
    `${API_BASE_URL}/documents?title=${encodeURIComponent(title)}&author_id=${authorId}`,
    {
      method: 'POST',
      body: formData,
    }
  )
  
  if (!res.ok) {
    throw new Error('Failed to create document')
  }
  return res.json()
}

// Update a document
export async function updateDocument(
  documentId: string,
  data: DocumentUpdateDTO
): Promise<Document> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  
  if (!res.ok) {
    throw new Error('Failed to update document')
  }
  return res.json()
}

// Delete a document
export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'DELETE',
  })
  
  if (!res.ok) {
    throw new Error('Failed to delete document')
  }
}

// Download a document (returns blob)
export async function downloadDocument(documentId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/download`)
  
  if (!res.ok) {
    throw new Error('Failed to download document')
  }
  return res.blob()
}

// Get document chunks
export async function getDocumentChunks(
  documentId: string,
  skip = 0,
  limit = 10
): Promise<DocumentChunk[]> {
  const res = await fetch(
    `${API_BASE_URL}/documents/${documentId}/chunks?skip=${skip}&limit=${limit}`
  )
  
  if (!res.ok) {
    throw new Error('Failed to fetch document chunks')
  }
  return res.json()
}

// Vector search within a document
export async function searchDocumentChunks(
  documentId: string,
  query: string,
  limit = 10
): Promise<DocumentChunk[]> {
  const res = await fetch(
    `${API_BASE_URL}/documents/${documentId}/chunks/search?query=${encodeURIComponent(query)}&limit=${limit}`
  )
  
  if (!res.ok) {
    throw new Error('Failed to search document')
  }
  return res.json()
}
