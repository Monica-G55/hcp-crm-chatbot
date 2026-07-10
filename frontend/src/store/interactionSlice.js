import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { createInteraction, listInteractions } from "../api/api";

export const fetchInteractions = createAsyncThunk(
  "interactions/fetchAll",
  async () => {
    const res = await listInteractions();
    return res.data;
  }
);

export const submitInteraction = createAsyncThunk(
  "interactions/submit",
  async (formData) => {
    const res = await createInteraction(formData);
    return res.data;
  }
);

const interactionSlice = createSlice({
  name: "interactions",
  initialState: {
    items: [],
    status: "idle",
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload;
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(submitInteraction.fulfilled, (state) => {
        // list is refreshed by the component via fetchInteractions
      });
  },
});

export default interactionSlice.reducer;
