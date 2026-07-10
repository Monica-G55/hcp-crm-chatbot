import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { sendChatMessage } from "../api/api";

export const sendMessage = createAsyncThunk(
  "chat/sendMessage",
  async ({ message, rep_name }) => {
    const res = await sendChatMessage(message, rep_name);
    return {
      userMessage: message,
      ...res.data,
    };
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    messages: [], // Chat messages
    status: "idle",
    interactionData: null, // <-- AI extracted interaction data
  },
  reducers: {
    clearInteractionData: (state) => {
      state.interactionData = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state, action) => {
        state.status = "loading";

        state.messages.push({
          role: "user",
          text: action.meta.arg.message,
        });
      })

      .addCase(sendMessage.fulfilled, (state, action) => {
        state.status = "succeeded";

        state.messages.push({
          role: "agent",
          text: action.payload.reply,
          tool: action.payload.tool_used,
        });

        // Store extracted interaction details
        state.interactionData = action.payload.data || null;
      })

      .addCase(sendMessage.rejected, (state) => {
        state.status = "failed";

        state.messages.push({
          role: "agent",
          text: "Something went wrong. Please try again.",
        });
      });
  },
});

export const { clearInteractionData } = chatSlice.actions;

export default chatSlice.reducer;