<template>
  <transition name="fade" appear>
    <div class="message-container" :class="`message-${role}`">
      <div class="message-bubble">
        <div class="message-role">
          <b>{{ roleDisplay }}</b>
        </div>
        <!-- Display images above the text content -->
        <div v-if="images && images.length > 0" class="message-images">
          <img
            v-for="(image, index) in images"
            :key="index"
            :src="image.preview"
            :alt="image.name"
            class="message-image"
          />
        </div>
        <div class="message-content" v-html="sanitizedContent"></div>
      </div>
    </div>
  </transition>
</template>

<script>
import DOMPurify from 'dompurify';

export default {
  props: {
    role: String,
    content: String,
    images: {
      type: Array,
      default: () => [],
    },
  },
  computed: {
    roleDisplay() {
      return this.role === 'user' ? 'You' : 'BPMN Assistant';
    },
    sanitizedContent() {
      const formattedContent = (this.content || '')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n- /g, '<br>• ')
        .replace(/\n/g, '<br>');
      return DOMPurify.sanitize(formattedContent, {
        ALLOWED_TAGS: ['br', 'strong'],
        ALLOWED_ATTR: [],
      });
    },
  },
};
</script>

<style scoped>
.fade-enter-active { transition: opacity .2s ease-out; }
.fade-enter-from { opacity: 0; }
.message-container { display: flex; margin-bottom: 24px; max-width: 100%; }
.message-user { margin-left: 20px; }
.message-bubble { width: 100%; padding: 14px 16px; border-radius: 12px; overflow-wrap: anywhere; }
.message-user .message-bubble { background: #f0f4fc; color: #33415a; border: 1px solid #e7edf7; }
.message-assistant .message-bubble { padding: 4px 2px; color: #475166; }
.message-role { font-size: 11px; color: #7c879a; margin-bottom: 8px; }
.message-assistant .message-role { color: #4169d5; }
.message-content { font-size: 13px; line-height: 1.75; }
.message-content :deep(strong) { color: #25334b; font-weight: 600; }
.message-content :deep(br) { content: ''; display: block; margin-bottom: .3em; }
.message-images { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.message-image { max-width: 100%; max-height: 200px; border-radius: 8px; object-fit: cover; }
@media (prefers-reduced-motion: reduce) { .fade-enter-active { transition: none; } }
</style>