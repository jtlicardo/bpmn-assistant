<template>
  <div>
    <v-select
      class="model-picker"
      :placeholder="loadingProviders ? 'Connecting to backend...' : 'Select model'"
      :loading="loadingProviders"
      density="compact"
      :items="availableModels"
      :modelValue="selectedModel"
      @update:modelValue="onModelChange"
      hide-details
      :list-props="{ density: 'compact' }"
      :no-data-text="loadingProviders ? 'Waiting for the backend to start...' : 'Please provide API keys'"
      variant="outlined"
    ></v-select>
  </div>
</template>

<script>
import { bpmnAssistantUrl, isHostedVersion } from '../config';
import { getApiKeys } from '../utils/apiKeys';

const Models = Object.freeze({
  GPT_5_6_SOL: 'gpt-5.6-sol',
  GPT_5_6_LUNA: 'gpt-5.6-luna',
  OPUS_5: 'claude-opus-5',
  SONNET_5: 'claude-sonnet-5',
});

const Providers = Object.freeze({
  OPENAI: 'openai',
  ANTHROPIC: 'anthropic',
});

export default {
  name: 'ModelPicker',
  props: {
    hasImages: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      selectedModel: '',
      models: [
        {
          value: Models.GPT_5_6_SOL,
          title: 'GPT-5.6 Sol',
          provider: Providers.OPENAI,
        },
        {
          value: Models.GPT_5_6_LUNA,
          title: 'GPT-5.6 Luna',
          provider: Providers.OPENAI,
        },
        {
          value: Models.OPUS_5,
          title: 'Claude Opus 5',
          provider: Providers.ANTHROPIC,
        },
        {
          value: Models.SONNET_5,
          title: 'Claude Sonnet 5',
          provider: Providers.ANTHROPIC,
        },
      ],
      availableProviders: [],
      loadingProviders: !isHostedVersion,
      providerRetryTimer: null,
      providerController: null,
      disposed: false,
    };
  },
  computed: {
    availableModels() {
      let filteredModels = this.models.filter((model) =>
        this.availableProviders.includes(model.provider)
      );

      // If images are uploaded, only show OpenAI models
      if (this.hasImages) {
        filteredModels = filteredModels.filter(
          (model) => model.provider === Providers.OPENAI
        );
      }

      return filteredModels;
    },
  },
  methods: {
    onModelChange(model) {
      this.selectedModel = model;
      this.$emit('select-model', model);
    },
    async fetchAvailableProviders() {
      clearTimeout(this.providerRetryTimer);
      this.providerController?.abort();
      const controller = new AbortController();
      this.providerController = controller;
      let timeout;
      try {
        const apiKeys = getApiKeys();

        if (isHostedVersion) {
          // Production mode: determine providers from user-entered keys only
          this.availableProviders = [];
          if (apiKeys.openai_api_key) {
            this.availableProviders.push(Providers.OPENAI);
          }
          if (apiKeys.anthropic_api_key) {
            this.availableProviders.push(Providers.ANTHROPIC);
          }
        } else {
          this.loadingProviders = true;
          timeout = setTimeout(() => controller.abort(), 5000);
          // Local mode: check backend (which uses .env file)
          const response = await fetch(
            `${bpmnAssistantUrl}/available_providers`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ api_keys: apiKeys }),
              signal: controller.signal,
            }
          );

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();
          if (this.disposed || this.providerController !== controller) return;

          this.availableProviders = Object.keys(data).filter(
            (provider) => data[provider]
          );
        }

        // Notify parent if no providers available
        const hasProviders = this.availableProviders.length > 0;
        this.$parent.setHasAvailableProviders(hasProviders);

        if (!this.availableModels.some((model) => model.value === this.selectedModel)) {
          this.onModelChange(this.availableModels[0]?.value || '');
        }
        this.loadingProviders = false;
      } catch (error) {
        if (this.disposed || this.providerController !== controller) return;
        // The frontend may be ready before the local API. Recover without a reload.
        if (!isHostedVersion) {
          this.providerRetryTimer = setTimeout(() => this.fetchAvailableProviders(), 2000);
        } else {
          this.loadingProviders = false;
          console.error('Error fetching available providers', error);
        }
      } finally {
        clearTimeout(timeout);
      }
    },
  },
  mounted() {
    this.fetchAvailableProviders();
  },
  beforeUnmount() {
    this.disposed = true;
    clearTimeout(this.providerRetryTimer);
    this.providerController?.abort();
  },
};
</script>

<style scoped>
.model-picker {
  width: 200px;
}
</style>
