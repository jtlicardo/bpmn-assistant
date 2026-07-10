<template>
  <v-dialog v-model="localShow" max-width="600" persistent>
    <v-card>
      <v-card-title class="text-h5 pa-4">
        API Keys Configuration
      </v-card-title>
      <v-card-text class="pa-4">
        <v-alert type="info" variant="tonal" class="mb-4">
          Keys are stored in your browser session only and never sent to our servers.
          They will be cleared when you close this tab.
        </v-alert>

        <v-text-field
          v-model="keys.openai"
          label="OpenAI API Key (optional)"
          placeholder="sk-..."
          type="password"
          variant="outlined"
          density="comfortable"
          class="mb-3"
          hint="For GPT models"
          persistent-hint
        />

        <v-text-field
          v-model="keys.anthropic"
          label="Anthropic API Key (optional)"
          placeholder="sk-ant-..."
          type="password"
          variant="outlined"
          density="comfortable"
          class="mb-3"
          hint="For Claude models"
          persistent-hint
        />

        <v-alert v-if="errorMessage" type="error" variant="tonal" class="mt-3">
          {{ errorMessage }}
        </v-alert>
      </v-card-text>

      <v-card-actions class="pa-4">
        <v-btn
          v-if="canCancel"
          color="grey"
          variant="text"
          @click="cancel"
        >
          Cancel
        </v-btn>
        <v-spacer />
        <v-btn
          v-if="hasExistingKeys"
          color="error"
          variant="text"
          @click="clearKeys"
        >
          Clear All Keys
        </v-btn>
        <v-btn
          color="primary"
          variant="elevated"
          @click="save"
          :disabled="!hasAtLeastOneKey"
        >
          Save Keys
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'ApiKeysModal',
  props: {
    show: {
      type: Boolean,
      default: false,
    },
    canCancel: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      keys: {
        openai: '',
        anthropic: '',
      },
      errorMessage: '',
    };
  },
  computed: {
    localShow: {
      get() {
        return this.show;
      },
      set(value) {
        if (value === false && this.canCancel) {
          this.$emit('close');
        }
      },
    },
    hasAtLeastOneKey() {
      return Object.values(this.keys).some(key => key.trim() !== '');
    },
    hasExistingKeys() {
      return sessionStorage.getItem('bpmn_api_keys') !== null;
    },
  },
  mounted() {
    this.loadKeys();
  },
  methods: {
    loadKeys() {
      const stored = sessionStorage.getItem('bpmn_api_keys');
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          this.keys.openai = parsed.openai_api_key || '';
          this.keys.anthropic = parsed.anthropic_api_key || '';
        } catch (e) {
          console.error('Failed to parse stored API keys', e);
        }
      }
    },
    save() {
      const apiKeys = {};

      if (this.keys.openai.trim()) {
        apiKeys.openai_api_key = this.keys.openai.trim();
      }
      if (this.keys.anthropic.trim()) {
        apiKeys.anthropic_api_key = this.keys.anthropic.trim();
      }
      sessionStorage.setItem('bpmn_api_keys', JSON.stringify(apiKeys));
      this.$emit('keys-updated');
      this.$emit('close');
    },
    clearKeys() {
      sessionStorage.removeItem('bpmn_api_keys');
      this.keys = {
        openai: '',
        anthropic: '',
      };
      this.$emit('keys-updated');
      this.$emit('close');
    },
    cancel() {
      this.$emit('close');
    },
  },
};
</script>
