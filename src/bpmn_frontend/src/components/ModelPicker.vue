<template>
  <div>
    <v-select
      class="model-picker"
      placeholder="Select model"
      density="compact"
      :items="availableModels"
      :modelValue="selectedModel"
      @update:modelValue="onModelChange"
      hide-details
      :list-props="{ density: 'compact' }"
      no-data-text="Please provide API keys"
      variant="outlined"
    ></v-select>
  </div>
</template>

<script>
import { bpmnAssistantUrl, isHostedVersion } from '../config';
import { getApiKeys } from '../utils/apiKeys';

const Models = Object.freeze({
  GPT_5_2: 'gpt-5.2-2025-12-11',
  GPT_4_1: 'gpt-4.1',
  SONNET_4_5: 'claude-sonnet-4-5-20250929',
  OPUS_4_6: 'claude-opus-4-6',
  GEMINI_3_1_PRO: 'gemini/gemini-3.1-pro-preview',
  GEMINI_3_FLASH: 'gemini/gemini-3-flash-preview',
  KIMI_K2P5: 'fireworks_ai/kimi-k2p5',
});

const Providers = Object.freeze({
  OPENAI: 'openai',
  ANTHROPIC: 'anthropic',
  GOOGLE: 'google',
  FIREWORKS_AI: 'fireworks_ai',
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
          value: Models.GPT_5_2,
          title: 'GPT-5.2',
          provider: Providers.OPENAI,
        },
        { value: Models.GPT_4_1, title: 'GPT-4.1', provider: Providers.OPENAI },
        {
          value: Models.SONNET_4_5,
          title: 'Claude Sonnet 4.5',
          provider: Providers.ANTHROPIC,
        },
        {
          value: Models.OPUS_4_6,
          title: 'Claude Opus 4.6',
          provider: Providers.ANTHROPIC,
        },
        {
          value: Models.GEMINI_3_FLASH,
          title: 'Gemini 3 Flash',
          provider: Providers.GOOGLE,
        },
        {
          value: Models.GEMINI_3_1_PRO,
          title: 'Gemini 3.1 Pro',
          provider: Providers.GOOGLE,
        },
        {
          value: Models.KIMI_K2P5,
          title: 'Kimi K2.5',
          provider: Providers.FIREWORKS_AI,
        },
      ],
      availableProviders: [],
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
          if (apiKeys.google_api_key) {
            this.availableProviders.push(Providers.GOOGLE);
          }
          if (apiKeys.fireworks_api_key) {
            this.availableProviders.push(Providers.FIREWORKS_AI);
          }
        } else {
          // Local mode: check backend (which uses .env file)
          const response = await fetch(
            `${bpmnAssistantUrl}/available_providers`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ api_keys: apiKeys }),
            }
          );

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();

          this.availableProviders = Object.keys(data).filter(
            (provider) => data[provider]
          );
        }

        // Notify parent if no providers available
        const hasProviders = this.availableProviders.length > 0;
        this.$parent.setHasAvailableProviders(hasProviders);

        if (this.availableProviders.includes(Providers.OPENAI)) {
          this.onModelChange(Models.GPT_5_2);
        } else if (this.availableProviders.includes(Providers.ANTHROPIC)) {
          this.onModelChange(Models.OPUS_4_6);
        } else if (this.availableProviders.includes(Providers.GOOGLE)) {
          this.onModelChange(Models.GEMINI_3_1_PRO);
        } else if (this.availableProviders.includes(Providers.FIREWORKS_AI)) {
          this.onModelChange(Models.KIMI_K2P5);
        }
      } catch (error) {
        console.error('Error fetching available providers', error);
      }
    },
  },
  mounted() {
    this.fetchAvailableProviders();
  },
};
</script>

<style scoped>
.model-picker {
  width: 200px;
}
</style>
