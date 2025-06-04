<template>
  <transition name="fade" appear>
    <div class="message-container" :class="`message-${role}`">
      <div class="message-bubble">
        <div class="message-role">
          <b>{{ roleDisplay }}</b>
        </div>
        <div class="message-content" v-html="formattedContent"></div>
        <img v-if="imageUrl" :src="imageUrl" class="message-image" />
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  props: {
    role: String,
    content: String,
    imageUrl: String,
  },
  computed: {
    roleDisplay() {
      return this.role === 'user' ? 'You' : 'BPMN Assistant';
    },
    formattedContent() {
      return this.content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n- /g, '<br>• ')
        .replace(/\n/g, '<br>');
    },
  },
};
</script>

<style scoped>
.fade-enter-active {
  transition: opacity 0.5s ease-out;
}

.fade-enter-from {
  opacity: 0;
}

.fade-enter-to {
  opacity: 1;
}

.fade-enter-active {
  transition: opacity 0.5s ease-out, transform 0.3s ease-out;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-enter-to {
  opacity: 1;
  transform: translateY(0);
}

.message-container {
  display: flex;
  margin-bottom: 12px;
  max-width: 85%;
}

.message-user {
  justify-content: flex-end;
  margin-left: auto;
  margin-right: 8px;
}

.message-assistant {
  justify-content: flex-start;
  margin-left: 8px;
  margin-right: auto;
}

.message-bubble {
  padding: 10px 15px;
  border-radius: 18px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  word-wrap: break-word;
  position: relative;
}

.message-user .message-bubble {
  background-color: #e1f5fe;
  color: #333;
  border-bottom-right-radius: 4px;
}

.message-assistant .message-bubble {
  background-color: #f1f1f1;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-role {
  font-size: 0.8em;
  color: #555;
  margin-bottom: 4px;
}

.message-content {
  font-size: 1em;
  line-height: 1.4;
}

.message-image {
  margin-top: 8px;
  max-width: 100%;
  border-radius: 4px;
}

.message-content ::v-deep(strong) {
  font-weight: bold;
}

.message-content ::v-deep(br) {
  content: '';
  display: block;
  margin-bottom: 0.2em;
}
</style>
