import axios from 'axios'

const api = axios.create({
    baseURL: '',
    withCredentials: true,
    headers: { 'Content-Type': 'application/json' },
})

// Fetch latest 10 emails and trigger background indexing
export const fetchEmails = () => api.get('/auth/emails/test')

// Start background Gmail indexing
export const startIndexing = () => api.post('/auth/index/start')

// Get indexing progress
export const getIndexStatus = () => api.get('/auth/index/status')

// Semantic search
// params: { q, category?, limit?, start_date?, end_date?, from_sender? }
export const semanticSearch = (params) => api.get('/auth/search', { params })

// RAG Q&A
// payload: { query, conversation_id?, category?, start_date?, end_date?, from_sender? }
export const askRag = (payload) => api.post('/auth/ask', payload)

// Conversations
export const createConversation = (payload = {}) => api.post('/auth/conversations', payload)
export const listConversations = (params = {}) => api.get('/auth/conversations', { params })
export const deleteConversation = (conversationId) => api.delete(`/auth/conversations/${conversationId}`)
export const getConversationMessages = (conversationId, params = {}) =>
    api.get(`/auth/conversations/${conversationId}/messages`, { params })

export default api
