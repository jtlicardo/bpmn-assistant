<template>
  <div class="chat-interface">
    <div class="sticky-top">
      <p class="text-h6 text-center mb-2">BPMN Assistant</p>
      <ModelPicker @select-model="setSelectedModel" />
    </div>

    <div class="message-container">
      <div v-if="messages.length > 0" class="message-list">
        <MessageCard
          v-for="(message, index) in messages"
          :key="index"
          :role="message.role"
          :content="message.content"
        />

        <v-alert
          v-if="isLoading"
          type="info"
          text="Generating BPMN..."
          class="mb-5"
        />
      </div>

      <div v-if="messages.length === 0">
        <v-alert
          type="warning"
          text="Supported elements: start and end events, tasks (user, service), gateways (exclusive, parallel), sequence flows"
          class="mb-5"
        />

        <v-alert
          type="info"
          text="Welcome to BPMN Assistant! I can help you understand and create BPMN processes. Let's start by discussing your BPMN needs or creating a new process from scratch. How would you like to begin?"
          class="mb-5"
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
          :counter="1000"
          rows="6"
          @keydown.enter.prevent="handleKeyDown"
          class="mx-2"
        >
        </v-textarea>
        <v-btn
          @click="handleMessageSubmit"
          :disabled="isLoading || !currentInput.trim()"
          color="primary"
          class="send-button"
          icon="mdi-send"
          density="comfortable"
        >
        </v-btn>
      </div>
    </div>

    <div class="d-flex justify-center">
      <v-btn
        class="mr-5"
        @click="reset"
        :disabled="isLoading || messages.length === 0"
        color="blue-lighten-5"
        density="compact"
      >
        New chat
      </v-btn>
      <v-btn
        @click="onDownload"
        :disabled="isLoading"
        v-if="isDownloadReady"
        color="red-lighten-5"
        density="compact"
      >
        Download
      </v-btn>
    </div>

    <p class="text-caption text-center mt-4 mb-2">
      This application uses LLMs and may produce varying results.
    </p>
  </div>
</template>

<script>
import ModelPicker from "./ModelPicker.vue";
import MessageCard from "./MessageCard.vue";
import { toRaw } from "vue";
import Intent from "../enums/Intent";

export default {
  name: "ChatInterface",
  components: {
    ModelPicker,
    MessageCard,
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
      currentInput: "",
      selectedModel: "",
      hasError: false,
    };
  },
  methods: {
    reset() {
      this.messages = [];
      this.currentInput = "";
      this.hasError = false;
      this.onBpmnJsonReceived(null);
      this.onBpmnXmlReceived("");
    },
    setSelectedModel(model) {
      this.selectedModel = model;
      console.log("Selected model:", model);
    },
    handleKeyDown(event) {
      if (event.shiftKey && event.key === "Enter") {
        // Manually insert a newline character
        event.preventDefault();
        const cursorPosition = event.target.selectionStart;
        const textBeforeCursor = this.currentInput.slice(0, cursorPosition);
        const textAfterCursor = this.currentInput.slice(cursorPosition);
        this.currentInput = textBeforeCursor + "\n" + textAfterCursor;

        // Move the cursor to the correct position after inserting the newline
        this.$nextTick(() => {
          event.target.selectionStart = event.target.selectionEnd =
            cursorPosition + 1;
        });
      } else if (event.key === "Enter") {
        // Submit message when only Enter is pressed
        event.preventDefault();
        this.handleMessageSubmit();
      }
    },
    async handleMessageSubmit() {
      if (!this.currentInput.trim() || this.currentInput.length > 1000) {
        return;
      }

      if (!this.selectedModel) {
        alert("You need to select a model first.");
        return;
      }

      // Clear any previous errors
      this.hasError = false;

      this.messages.push({ content: this.currentInput, role: "user" });
      this.currentInput = "";

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
          console.error("Unknown intent:", intent);
      }
    },
    async determineIntent() {
      const payload = {
        message_history: toRaw(this.messages),
        model: this.selectedModel,
      };

      try {
        const response = await fetch("http://localhost:8000/determine_intent", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          console.error(`HTTP error! Status: ${response.status}`);
          this.hasError = true;
          return;
        }

        const data = await response.json();

        if (!Object.values(Intent).includes(data.intent)) {
          console.error("Unknown intent:", data.intent);
          this.hasError = true;
          return;
        }

        return data.intent;
      } catch (error) {
        console.error("Error determining intent:", error);
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

        const response = await fetch("http://localhost:8000/talk", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
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
            this.messages[this.messages.length - 1].role === "assistant"
          ) {
            const lastMessage = this.messages[this.messages.length - 1];
            lastMessage.content = (lastMessage.content || "") + newText;
          } else {
            this.messages.push({ content: newText, role: "assistant" });
          }
        };

        const processText = async ({ done, value }) => {
          if (done) {
            console.log("Stream complete");
            return;
          }

          const chunk = new TextDecoder("utf-8").decode(value);
          // console.log(JSON.stringify(chunk));
          updateOrAddLastMessage(chunk);

          return reader.read().then(processText);
        };

        return reader.read().then(processText);
      } catch (error) {
        console.error("Error responding to user query:", error);
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

        const response = await fetch("http://localhost:8000/modify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          console.error(`HTTP error! Status: ${response.status}`);
          this.isLoading = false;
          this.hasError = true;
          return;
        }

        const data = await response.json();

        console.log("BPMN JSON received:", data.bpmn_json);

        return {
          bpmnXml: data.bpmn_xml,
          bpmnJson: data.bpmn_json,
        };
      } catch (error) {
        console.error("Error modifying BPMN:", error);
        this.isLoading = false;
        this.hasError = true;
      }
    },
    scrollToBottom() {
      const messageContainer = this.$el.querySelector(".message-container");
      messageContainer.scrollTop = messageContainer.scrollHeight;
    },
  },
};
</script>

<style scoped>
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
  padding: 10px;
}

.message-container {
  flex-grow: 1;
  overflow-y: auto;
  padding: 10px;
  max-height: calc(100vh - 300px); /* Adjust this value as needed */
}

.message-list {
  display: flex;
  flex-direction: column;
}

.input-area {
  margin-top: auto;
  padding: 10px;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
}

.send-button {
  margin-bottom: 90px;
}
</style>
