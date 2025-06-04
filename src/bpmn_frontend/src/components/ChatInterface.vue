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
          <ModelPicker @select-model="setSelectedModel" />
        </div>
      </div>
    </div>

    <div class="message-container">
      <div v-if="messages.length > 0" class="message-list">
        <MessageCard
          v-for="(message, index) in messages"
          :key="index"
          :role="message.role"
          :content="message.content"
          :image-url="message.image_url"
        />

        <LoadingIndicator v-if="isLoading" />
      </div>

      <div v-if="messages.length === 0">
        <v-alert
          text="Supported elements: start and end events, tasks (user, service), gateways (exclusive, parallel), sequence flows"
          class="mb-3"
          type="info"
        />

        <MessageCard
          role="assistant"
          content="Welcome to BPMN Assistant! I can help you understand and create BPMN processes. Let's start by discussing your BPMN needs or creating a new process from scratch. How would you like to begin?"
        />
      </div>

      <v-alert
        v-if="hasError"
        type="error"
        text="An error occurred while processing your request. Please try again."
        class="mb-5 text-body-2"
        closable
        @click:close="hasError = false"
      />
    </div>

    <div class="input-area">
      <div class="input-wrapper">
        <v-textarea
          label="Message BPMN Assistant..."
          v-model="currentInput"
          :disabled="isLoading"
          :counter="10000"
          rows="4"
          @keydown.enter.prevent="handleKeyDown"
          @paste="handlePaste"
          @dragover.prevent
          @drop.prevent="handleDrop"
          hide-details
          class="input-textarea"
          density="comfortable"
          variant="outlined"
          bg-color="white"
        >
        </v-textarea>
        <input
          type="file"
          accept="image/*"
          ref="imageInput"
          @change="handleImageChange"
          style="display: none"
        />
        <img v-if="selectedImage" :src="selectedImage" class="preview-image" />
        <v-btn
          icon="mdi-image"
          variant="text"
          size="small"
          :disabled="isLoading"
          @click="triggerImageSelect"
        ></v-btn>
        <v-btn
          @click="handleMessageSubmit"
          :disabled="isLoading || (!currentInput.trim() && !selectedImage)"
          color="primary"
          class="send-button"
          icon="mdi-send"
          variant="text"
          size="small"
        >
        </v-btn>
      </div>
    </div>

    <p class="text-caption text-center mt-2 mb-2">
      This application uses LLMs and may produce varying results.
    </p>
  </div>
</template>

<script>
import ModelPicker from './ModelPicker.vue';
import MessageCard from './MessageCard.vue';
import LoadingIndicator from './LoadingIndicator.vue';
import { toRaw } from 'vue';
import Intent from '../enums/Intent';

export default {
  name: 'ChatInterface',
  components: {
    ModelPicker,
    MessageCard,
    LoadingIndicator,
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
      selectedImage: null,
      hasError: false,
    };
  },
  methods: {
    reset() {
      this.messages = [];
      this.currentInput = '';
      this.hasError = false;
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
    triggerImageSelect() {
      this.$refs.imageInput.click();
    },
    handlePaste(event) {
      const items = event.clipboardData?.items || [];
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile();
          if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
              this.selectedImage = e.target.result;
            };
            reader.readAsDataURL(file);
          }
        }
      }
    },
    handleDrop(event) {
      const file = event.dataTransfer.files[0];
      if (!file || !file.type.startsWith('image/')) {
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        this.selectedImage = e.target.result;
      };
      reader.readAsDataURL(file);
    },
    handleImageChange(event) {
      const file = event.target.files[0];
      if (!file) {
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        this.selectedImage = e.target.result;
      };
      reader.readAsDataURL(file);
    },
    async handleMessageSubmit() {
      if (!this.currentInput.trim() && !this.selectedImage) {
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
      this.hasError = false;

      this.messages.push({ content: this.currentInput, role: 'user', image_url: this.selectedImage });
      this.currentInput = '';
      this.selectedImage = null;

      this.$nextTick(() => {
        this.scrollToBottom();
      });

      const intent = await this.determineIntent();

      switch (intent) {
        case Intent.TALK:
          await this.talk(this.process, this.selectedModel, false);
          this.$nextTick(() => {
            this.scrollToBottom();
          });
          break;
        case Intent.MODIFY:
          this.isLoading = true;
          this.$nextTick(() => {
            this.scrollToBottom();
          });
          const { bpmnXml, bpmnJson } = await this.modify(
            this.process,
            this.selectedModel
          );
          this.onBpmnJsonReceived(bpmnJson);
          this.onBpmnXmlReceived(bpmnXml);
          this.isLoading = false;
          await this.talk(bpmnJson, this.selectedModel, true); // Make final comment
          this.$nextTick(() => {
            this.scrollToBottom();
          });
          break;
        default:
          console.error('Unknown intent:', intent);
      }
    },
    async determineIntent() {
      const payload = {
        message_history: toRaw(this.messages),
        model: this.selectedModel,
      };

      try {
        const response = await fetch('http://localhost:8000/determine_intent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          console.error(`HTTP error! Status: ${response.status}`);
          this.hasError = true;
          return;
        }

        const data = await response.json();

        if (!Object.values(Intent).includes(data.intent)) {
          console.error('Unknown intent:', data.intent);
          this.hasError = true;
          return;
        }

        return data.intent;
      } catch (error) {
        console.error('Error determining intent:', error);
        this.hasError = true;
      }
    },
    async talk(process, selectedModel, needsToBeFinalComment) {
      try {
        const payload = {
          message_history: toRaw(this.messages),
          process: process,
          model: selectedModel,
          needs_to_be_final_comment: needsToBeFinalComment,
        };

        const response = await fetch('http://localhost:8000/talk', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          console.error(`HTTP error! Status: ${response.status}`);
          this.hasError = true;
          return;
        }

        // Handle the response as a stream
        const reader = response.body.getReader();

        const updateOrAddLastMessage = (newText) => {
          if (
            this.messages.length > 0 &&
            this.messages[this.messages.length - 1].role === 'assistant'
          ) {
            const lastMessage = this.messages[this.messages.length - 1];
            lastMessage.content = (lastMessage.content || '') + newText;
          } else {
            this.messages.push({ content: newText, role: 'assistant' });
          }
        };

        const processText = async ({ done, value }) => {
          if (done) {
            console.log('Stream complete');
            return;
          }

          const chunk = new TextDecoder('utf-8').decode(value);
          // console.log(JSON.stringify(chunk));
          updateOrAddLastMessage(chunk);

          return reader.read().then(processText);
        };

        return reader.read().then(processText);
      } catch (error) {
        console.error('Error responding to user query:', error);
        this.hasError = true;
      }
    },
    async modify(process, selectedModel) {
      try {
        const payload = {
          message_history: toRaw(this.messages),
          process: process,
          model: selectedModel,
        };

        const response = await fetch('http://localhost:8000/modify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          console.error(`HTTP error! Status: ${response.status}`);
          this.isLoading = false;
          this.hasError = true;
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
        this.hasError = true;
      }
    },
    scrollToBottom() {
      const messageContainer = this.$el.querySelector('.message-container');
      messageContainer.scrollTop = messageContainer.scrollHeight;
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
  align-items: flex-end;
  position: relative;
}

.input-textarea {
  flex-grow: 1;
}

.preview-image {
  max-width: 80px;
  max-height: 80px;
  margin-right: 8px;
  border-radius: 4px;
}

.app-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.5rem;
  font-weight: 500;
  letter-spacing: 0.5px;
  background: linear-gradient(45deg, var(--v-primary-base), #666);
  margin-bottom: 0;
}
</style>
