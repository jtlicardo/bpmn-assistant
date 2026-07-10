<template>
  <div class="chat-interface">
    <div class="sticky-top">
      <div class="d-flex align-center justify-space-between pa-2 gap-4">
        <div class="d-flex align-center">
          <v-icon
            icon="mdi-chart-timeline-variant"
            color="primary"
            size="x-large"
            class="mr-2"
          />
          <span class="app-title">BPMN Assistant</span>
        </div>
        <div class="d-flex align-center">
          <v-tooltip text="New chat" location="bottom">
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                @click="reset"
                :disabled="isLoading || messages.length === 0"
                icon="mdi-refresh"
                variant="text"
                size="medium"
                color="blue"
                class="mr-5"
              >
              </v-btn>
            </template>
          </v-tooltip>

          <v-tooltip
            text="Download BPMN"
            v-if="isDownloadReady"
            location="bottom"
          >
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                @click="onDownload"
                :disabled="isLoading"
                icon="mdi-download"
                variant="text"
                size="medium"
                color="orange"
                class="mr-5"
              >
              </v-btn>
            </template>
          </v-tooltip>
          <v-tooltip text="API Keys" location="bottom" v-if="isHostedVersion">
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                @click="showApiKeysModal = true"
                icon="mdi-key"
                variant="text"
                size="medium"
                color="grey-darken-1"
                class="mr-2"
              >
              </v-btn>
            </template>
          </v-tooltip>
          <ModelPicker
            @select-model="setSelectedModel"
            :has-images="hasImages"
            ref="modelPicker"
          />
        </div>
      </div>
    </div>

    <ApiKeysModal
      v-if="isHostedVersion"
      :show="showApiKeysModal"
      :can-cancel="hasAvailableProviders"
      @close="showApiKeysModal = false"
      @keys-updated="handleKeysUpdated"
    />

    <div class="message-container">
      <div v-if="messages.length > 0" class="message-list">
        <MessageCard
          v-for="(message, index) in messages"
          :key="index"
          :role="message.role"
          :content="message.content"
          :images="message.images || []"
        />

        <LoadingIndicator v-if="isLoading" />
      </div>

      <div v-if="messages.length === 0">
        <MessageCard
          role="assistant"
          content="Welcome to BPMN Assistant! I can help you understand and create BPMN processes. Let's start by discussing your BPMN needs or creating a new process from scratch. How would you like to begin?"
        />
      </div>

      <v-alert
        v-if="hasError"
        type="error"
        :text="errorMessage || defaultErrorMessage"
        class="mb-5 text-body-2"
        closable
        @click:close="clearError"
      />
    </div>

    <div
      class="input-area"
      :class="{ 'drag-over': isDragging }"
      @dragover="handleDragOver"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
    >
      <div class="input-wrapper">
        <!-- Image previews -->
        <div v-if="selectedImages.length > 0" class="image-preview-container">
          <div
            v-for="(image, index) in selectedImages"
            :key="index"
            class="image-preview-item"
          >
            <img :src="image.preview" :alt="image.name" class="preview-image" />
            <v-btn
              @click="removeImage(index)"
              icon="mdi-close"
              size="x-small"
              class="remove-image-btn"
              color="error"
              variant="text"
            >
            </v-btn>
          </div>
        </div>
        <div class="input-controls">
          <input
            type="file"
            ref="fileInput"
            @change="handleFileSelect"
            accept="image/*"
            multiple
            style="display: none"
          />
          <v-tooltip
            :text="
              !isOpenAIModel
                ? 'Image uploads are only available for OpenAI models'
                : 'Upload image'
            "
            location="top"
          >
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                @click="triggerFileInput"
                :disabled="isLoading || !isOpenAIModel"
                icon="mdi-image-plus"
                variant="text"
                size="small"
                class="attach-button"
                color="grey-darken-1"
              >
              </v-btn>
            </template>
          </v-tooltip>
          <v-textarea
            label="Message BPMN Assistant..."
            v-model="currentInput"
            :counter="10000"
            rows="4"
            @keydown.enter.prevent="handleKeyDown"
            @paste="handlePaste"
            hide-details
            class="input-textarea"
            density="comfortable"
            variant="outlined"
            bg-color="white"
          >
          </v-textarea>
          <v-btn
            @click="handleMessageSubmit"
            :disabled="isLoading || (!currentInput.trim() && selectedImages.length === 0)"
            color="primary"
            class="send-button"
            icon="mdi-send"
            variant="text"
            size="small"
          >
          </v-btn>
        </div>
      </div>
    </div>

    <p class="text-caption text-center mt-2 mb-2">
      This application uses LLMs and may produce varying results.
    </p>

    <v-snackbar
      v-model="showImageLimitSnackbar"
      :timeout="3000"
      color="warning"
      location="top"
    >
      Only 3 images per message are allowed
      <template v-slot:actions>
        <v-btn
          color="white"
          variant="text"
          @click="showImageLimitSnackbar = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import ModelPicker from './ModelPicker.vue';
import MessageCard from './MessageCard.vue';
import LoadingIndicator from './LoadingIndicator.vue';
import ApiKeysModal from './ApiKeysModal.vue';
import { toRaw } from 'vue';
import Intent from '../enums/Intent';
import { bpmnAssistantUrl, isHostedVersion } from '../config';
import { getApiKeys } from '../utils/apiKeys';

const STREAM_IDLE_TIMEOUT_MS = 10000;
const STREAM_TOTAL_TIMEOUT_MS = 30000;
const FINAL_RESPONSE_FALLBACK_MESSAGE =
  'I finished the update, but the final response failed to render.';

export default {
  name: 'ChatInterface',
  components: {
    ModelPicker,
    MessageCard,
    LoadingIndicator,
    ApiKeysModal,
  },
  props: {
    onBpmnXmlReceived: Function,
    onBpmnJsonReceived: Function,
    onDownload: Function,
    isDownloadReady: Boolean,
    process: Object,
  },
  data() {
    return {
      isLoading: false,
      messages: [],
      currentInput: '',
      selectedModel: '',
      hasError: false,
      errorMessage: '',
      defaultErrorMessage: 'An error occurred while processing your request. Please try again.',
      selectedImages: [],
      isDragging: false,
      showImageLimitSnackbar: false,
      conversationHasImages: false,
      showApiKeysModal: false,
      hasAvailableProviders: false,
      isHostedVersion: isHostedVersion,
    };
  },
  computed: {
    isOpenAIModel() {
      return (
        this.selectedModel === 'gpt-5.6-sol' ||
        this.selectedModel === 'gpt-5.6-luna'
      );
    },
    hasImages() {
      return this.selectedImages.length > 0 || this.conversationHasImages;
    },
  },
  methods: {
    reset() {
      this.messages = [];
      this.currentInput = '';
      this.clearError();
      this.selectedImages = [];
      this.conversationHasImages = false;
      this.onBpmnJsonReceived(null);
      this.onBpmnXmlReceived('');
    },
    setSelectedModel(model) {
      this.selectedModel = model;
      console.log('Selected model:', model);
    },
    handleKeyDown(event) {
      if (event.shiftKey && event.key === 'Enter') {
        // Manually insert a newline character
        event.preventDefault();
        const cursorPosition = event.target.selectionStart;
        const textBeforeCursor = this.currentInput.slice(0, cursorPosition);
        const textAfterCursor = this.currentInput.slice(cursorPosition);
        this.currentInput = textBeforeCursor + '\n' + textAfterCursor;

        // Move the cursor to the correct position after inserting the newline
        this.$nextTick(() => {
          event.target.selectionStart = event.target.selectionEnd =
            cursorPosition + 1;
        });
      } else if (event.key === 'Enter') {
        // Submit message when only Enter is pressed
        event.preventDefault();
        this.handleMessageSubmit();
      }
    },
    async handleMessageSubmit() {
      if (this.isLoading) {
        return;
      }

      if (!this.currentInput.trim()) {
        return;
      }

      if (!this.selectedModel) {
        alert('You need to select a model first.');
        return;
      }

      if (this.currentInput.length > 20000) {
        alert('Message is too long. Please keep it under 20,000 characters.');
        return;
      }

      // Clear any previous errors
      this.clearError();

      // Create the message object with text and images
      const message = {
        content: this.currentInput,
        role: 'user',
        images: this.selectedImages.map((img) => ({
          preview: img.preview,
          name: img.name,
        })),
      };

      // Track if conversation has images
      if (this.selectedImages.length > 0) {
        this.conversationHasImages = true;
      }

      this.messages.push(message);
      this.currentInput = '';
      this.selectedImages = []; // Clear selected images after sending
      this.isLoading = true;

      this.$nextTick(() => {
        this.scrollToBottom();
      });

      const intent = await this.determineIntent();

      if (!intent) {
        this.isLoading = false;
        return;
      }

      switch (intent) {
        case Intent.TALK:
          await this.talk(this.process, this.selectedModel, false);
          this.$nextTick(() => {
            this.scrollToBottom();
          });
          break;
        case Intent.MODIFY:
          this.$nextTick(() => {
            this.scrollToBottom();
          });
          const { bpmnXml, bpmnJson } = await this.modify(
            this.process,
            this.selectedModel
          );
          this.onBpmnJsonReceived(bpmnJson);
          this.onBpmnXmlReceived(bpmnXml);
          await this.talk(bpmnJson, this.selectedModel, true); // Make final comment
          this.$nextTick(() => {
            this.scrollToBottom();
          });
          break;
        default:
          console.error('Unknown intent:', intent);
          this.isLoading = false;
          if (!this.hasError) {
            this.setError();
          }
      }
    },
    async determineIntent() {
      const apiKeys = getApiKeys();
      const payload = {
        message_history: toRaw(this.messages),
        model: this.selectedModel,
        api_keys: apiKeys,
      };

      try {
        const response = await fetch(`${bpmnAssistantUrl}/determine_intent`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          console.error(`HTTP error! Status: ${response.status}`);
          await this.handleErrorResponse(response, 'Failed to determine intent.');
          return;
        }

        const data = await response.json();

        if (!Object.values(Intent).includes(data.intent)) {
          console.error('Unknown intent:', data.intent);
          if (!this.hasError) {
            this.setError();
          }
          return;
        }

        return data.intent;
      } catch (error) {
        console.error('Error determining intent:', error);
        this.setError(error?.message);
      }
    },
    appendOrAddLastAssistantMessage(newText) {
      if (!newText) {
        return;
      }

      if (
        this.messages.length > 0 &&
        this.messages[this.messages.length - 1].role === 'assistant'
      ) {
        const lastMessage = this.messages[this.messages.length - 1];
        lastMessage.content = (lastMessage.content || '') + newText;
      } else {
        this.messages.push({ content: newText, role: 'assistant' });
      }
    },
    removeMessagesAddedAfter(index) {
      if (this.messages.length > index) {
        this.messages.splice(index);
      }
    },
    pushFinalResponseFallbackMessage() {
      this.messages.push({
        content: FINAL_RESPONSE_FALLBACK_MESSAGE,
        role: 'assistant',
      });
    },
    async streamTalkAttempt(payload) {
      const streamController = new AbortController();
      let timeoutReason = '';
      let idleTimeoutId = null;
      let totalTimeoutId = null;

      const clearTimers = () => {
        if (idleTimeoutId) {
          clearTimeout(idleTimeoutId);
          idleTimeoutId = null;
        }

        if (totalTimeoutId) {
          clearTimeout(totalTimeoutId);
          totalTimeoutId = null;
        }
      };

      const resetIdleTimeout = () => {
        if (idleTimeoutId) {
          clearTimeout(idleTimeoutId);
        }

        idleTimeoutId = setTimeout(() => {
          timeoutReason = 'idle';
          streamController.abort();
        }, STREAM_IDLE_TIMEOUT_MS);
      };

      totalTimeoutId = setTimeout(() => {
        timeoutReason = 'total';
        streamController.abort();
      }, STREAM_TOTAL_TIMEOUT_MS);

      try {
        const response = await fetch(`${bpmnAssistantUrl}/talk`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal: streamController.signal,
        });

        if (!response.ok) {
          const error = new Error(`HTTP error! Status: ${response.status}`);
          error.response = response;
          throw error;
        }

        if (!response.body) {
          const error = new Error('Stream body is empty.');
          error.code = 'empty_stream';
          throw error;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let hasStreamedText = false;

        resetIdleTimeout();

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          resetIdleTimeout();

          const chunk = decoder.decode(value, { stream: true });
          if (!chunk) {
            continue;
          }

          hasStreamedText = true;
          this.appendOrAddLastAssistantMessage(chunk);
        }

        const trailingChunk = decoder.decode();
        if (trailingChunk) {
          hasStreamedText = true;
          this.appendOrAddLastAssistantMessage(trailingChunk);
        }

        if (!hasStreamedText) {
          const error = new Error('Stream completed without assistant tokens.');
          error.code = 'empty_stream';
          throw error;
        }
      } catch (error) {
        if (timeoutReason === 'idle') {
          const timeoutError = new Error(
            `Stream idle timeout after ${STREAM_IDLE_TIMEOUT_MS / 1000}s without tokens.`
          );
          timeoutError.code = 'stream_idle_timeout';
          throw timeoutError;
        }

        if (timeoutReason === 'total') {
          const timeoutError = new Error(
            `Stream total timeout after ${STREAM_TOTAL_TIMEOUT_MS / 1000}s.`
          );
          timeoutError.code = 'stream_total_timeout';
          throw timeoutError;
        }

        throw error;
      } finally {
        clearTimers();
      }
    },
    async talk(process, selectedModel, needsToBeFinalComment) {
      const apiKeys = getApiKeys();
      const payload = {
        message_history: toRaw(this.messages),
        process: process,
        model: selectedModel,
        needs_to_be_final_comment: needsToBeFinalComment,
        api_keys: apiKeys,
      };

      const maxAttempts = needsToBeFinalComment ? 2 : 1;

      for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
        const messageCountBeforeAttempt = this.messages.length;

        try {
          await this.streamTalkAttempt(payload);
          this.isLoading = false;
          return;
        } catch (error) {
          console.error(
            `Error responding to user query (attempt ${attempt}/${maxAttempts}):`,
            error
          );

          this.removeMessagesAddedAfter(messageCountBeforeAttempt);

          const isStreamRenderFailure =
            error?.code === 'stream_idle_timeout' ||
            error?.code === 'stream_total_timeout' ||
            error?.code === 'empty_stream';
          const canRetrySilently =
            needsToBeFinalComment &&
            isStreamRenderFailure &&
            attempt < maxAttempts;

          if (canRetrySilently) {
            continue;
          }

          this.isLoading = false;

          if (needsToBeFinalComment && isStreamRenderFailure) {
            this.pushFinalResponseFallbackMessage();
            return;
          }

          if (error.response) {
            await this.handleErrorResponse(
              error.response,
              'Unable to process the assistant response.'
            );
          } else {
            this.setError(error?.message);
          }
          return;
        }
      }
    },
    async modify(process, selectedModel) {
      try {
        const apiKeys = getApiKeys();
        const payload = {
          message_history: toRaw(this.messages),
          process: process,
          model: selectedModel,
          api_keys: apiKeys,
        };

        const response = await fetch(`${bpmnAssistantUrl}/modify`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          console.error(`HTTP error! Status: ${response.status}`);
          this.isLoading = false;
          await this.handleErrorResponse(response, 'Unable to modify the BPMN process.');
          return;
        }

        const data = await response.json();

        console.log('BPMN JSON received:', data.bpmn_json);

        return {
          bpmnXml: data.bpmn_xml,
          bpmnJson: data.bpmn_json,
        };
      } catch (error) {
        console.error('Error modifying BPMN:', error);
        this.isLoading = false;
        this.setError(error?.message);
      }
    },
    scrollToBottom() {
      const messageContainer = this.$el.querySelector('.message-container');
      messageContainer.scrollTop = messageContainer.scrollHeight;
    },
    handleFileSelect(event) {
      const files = Array.from(event.target.files);
      this.processFiles(files);
    },
    processFiles(files) {
      const imageFiles = files.filter((file) =>
        file.type.startsWith('image/')
      );

      // Limit to max 3 images
      const remainingSlots = 3 - this.selectedImages.length;

      if (imageFiles.length > remainingSlots) {
        this.showImageLimitSnackbar = true;
      }

      const filesToAdd = imageFiles.slice(0, remainingSlots);

      filesToAdd.forEach((file) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          this.selectedImages.push({
            file: file,
            preview: e.target.result,
            name: file.name,
          });
        };
        reader.readAsDataURL(file);
      });
    },
    removeImage(index) {
      this.selectedImages.splice(index, 1);
    },
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    handleDragOver(event) {
      event.preventDefault();
      this.isDragging = true;
    },
    handleDragEnter(event) {
      event.preventDefault();
      this.isDragging = true;
    },
    handleDragLeave(event) {
      event.preventDefault();
      // Only set isDragging to false if we're leaving the input-area entirely
      if (event.target.classList.contains('input-area')) {
        this.isDragging = false;
      }
    },
    handleDrop(event) {
      event.preventDefault();
      this.isDragging = false;

      if (!this.isOpenAIModel) {
        return;
      }

      const files = Array.from(event.dataTransfer.files);
      this.processFiles(files);
    },
    handlePaste(event) {
      if (!this.isOpenAIModel) {
        return;
      }

      const items = event.clipboardData?.items;
      if (!items) return;

      const imageItems = Array.from(items).filter((item) =>
        item.type.startsWith('image/')
      );

      if (imageItems.length > 0) {
        event.preventDefault(); // Prevent default paste behavior for images

        const files = imageItems.map((item) => item.getAsFile()).filter(Boolean);
        this.processFiles(files);
      }
    },
    clearError() {
      this.hasError = false;
      this.errorMessage = '';
    },
    setError(message) {
      this.errorMessage =
        this.normalizeErrorMessage(message) || this.defaultErrorMessage;
      this.hasError = true;
    },
    async handleErrorResponse(response, fallbackMessage) {
      let message = fallbackMessage || this.defaultErrorMessage;
      const contentType = response.headers.get('content-type') || '';

      try {
        if (contentType.includes('application/json')) {
          const payload = await response.json();
          if (payload) {
            if (typeof payload.detail === 'string' && payload.detail.trim()) {
              message = payload.detail;
            } else if (Array.isArray(payload.detail) && payload.detail.length) {
              message = payload.detail.map((item) => item.msg || item).join(', ');
            } else if (typeof payload.message === 'string' && payload.message.trim()) {
              message = payload.message;
            } else if (payload.error) {
              message =
                typeof payload.error === 'string'
                  ? payload.error
                  : JSON.stringify(payload.error);
            }
          }
        } else {
          const text = await response.text();
          if (text && text.trim()) {
            message = text;
          }
        }
      } catch (parseError) {
        console.error('Error parsing response body:', parseError);
      }

      this.setError(message);
    },
    normalizeErrorMessage(rawMessage) {
      if (!rawMessage) {
        return '';
      }

      const sanitized = String(rawMessage);

      if (
        /incorrect api key provided/i.test(sanitized) ||
        /invalid x-api-key/i.test(sanitized) ||
        /api key not valid/i.test(sanitized) ||
        /api_key_invalid/i.test(sanitized) ||
        /unauthorized/i.test(sanitized)
      ) {
        return 'Authentication failed: please verify your API key in the API Keys modal.';
      }

      if (/credit balance is too low/i.test(sanitized)) {
        return 'The provider rejected the request because the account has insufficient credits.';
      }

      return sanitized;
    },
    handleKeysUpdated() {
      // Refresh available providers after keys are updated
      if (this.$refs.modelPicker) {
        this.$refs.modelPicker.fetchAvailableProviders();
      }
    },
    setHasAvailableProviders(hasProviders) {
      this.hasAvailableProviders = hasProviders;
      if (!hasProviders && !this.showApiKeysModal && this.isHostedVersion) {
        this.showApiKeysModal = true;
      }
    },
  },
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500&display=swap');

.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 600px;
  margin: 0 auto;
}

.sticky-top {
  position: sticky;
  top: 0;
  background-color: white;
  z-index: 1;
  padding: 4px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.message-container {
  flex-grow: 1;
  overflow-y: auto;
  padding: 16px;
}

.message-list {
  display: flex;
  flex-direction: column;
}

.input-area {
  margin-top: auto;
  padding: 16px;
  background-color: white;
  border-top: 1px solid rgba(0, 0, 0, 0.12);
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  position: relative;
}

.input-controls {
  display: flex;
  align-items: flex-end;
}

.input-textarea {
  flex-grow: 1;
}

.app-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.5rem;
  font-weight: 500;
  letter-spacing: 0.5px;
  background: linear-gradient(45deg, var(--v-primary-base), #666);
  margin-bottom: 0;
}

.input-area.drag-over {
  background-color: #e3f2fd;
  border-color: #2196f3;
}

.image-preview-container {
  display: flex;
  gap: 8px;
  padding: 0 0 8px 0;
  flex-wrap: wrap;
  margin-left: 44px;
}

.image-preview-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid #e0e0e0;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-image-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  background-color: rgba(255, 255, 255, 0.9);
}

.attach-button {
  margin-right: 4px;
}
</style>
