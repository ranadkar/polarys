import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { sendChatMessage, type ChatMessage, type ChatResponse, type ChatHistoryMessage } from './services';

export interface ChatState {
    messages: ChatMessage[];
    status: 'idle' | 'loading' | 'succeeded' | 'failed';
    error: string | null;
}

const initialState: ChatState = {
    messages: [],
    status: 'idle',
    error: null,
};

// Define a minimal type for the thunk state to avoid circular dependency
interface ThunkState {
    search: { sessionId: string | null };
    chat: ChatState;
}

export const sendMessage = createAsyncThunk<
    ChatResponse,
    string,
    { rejectValue: string }
>('chat/sendMessage', async (message, { rejectWithValue, getState }) => {
    const state = getState() as unknown as ThunkState;
    const sessionId = state.search.sessionId;
    if (!sessionId) {
        return rejectWithValue('No active session');
    }

    // Build history from existing messages (strip follow_ups for API)
    const history: ChatHistoryMessage[] = state.chat.messages.map((msg: ChatMessage) => ({
        role: msg.role,
        content: msg.content,
    }));

    try {
        return await sendChatMessage(sessionId, message, history);
    } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Chat request failed';
        return rejectWithValue(errorMessage);
    }
});

const chatSlice = createSlice({
    name: 'chat',
    initialState,
    reducers: {
        clearChat(state) {
            state.messages = [];
            state.status = 'idle';
            state.error = null;
        },
        addUserMessage(state, action: PayloadAction<string>) {
            state.messages.push({
                role: 'user',
                content: action.payload,
            });
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(sendMessage.pending, (state, action) => {
                state.status = 'loading';
                state.error = null;
                // Add user message immediately when request starts
                state.messages.push({
                    role: 'user',
                    content: action.meta.arg,
                });
            })
            .addCase(sendMessage.fulfilled, (state, action) => {
                state.status = 'succeeded';
                // Add assistant response with follow-ups
                state.messages.push({
                    role: 'assistant',
                    content: action.payload.response,
                    follow_ups: action.payload.follow_up_suggestions,
                });
            })
            .addCase(sendMessage.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.payload ?? 'Chat request failed';
            });
    },
});

export const { clearChat, addUserMessage } = chatSlice.actions;
export default chatSlice.reducer;
