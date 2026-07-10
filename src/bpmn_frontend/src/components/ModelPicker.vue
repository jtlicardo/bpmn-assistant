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
  GPT_5_6_SOL: 'gpt-5.6-sol',
  GPT_5_6_LUNA: 'gpt-5.6-luna',
  OPUS_4_8: 'claude-opus-4-8',
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
          value: Models.OPUS_4_8,
          title: 'Claude Opus 4.8',
          provider: Providers.ANTHROPIC,
        },
        {
          value: Models.SONNET_5,
          title: 'Claude Sonnet 5',
          provider: Providers.ANTHROPIC,
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
          this.onModelChange(Models.GPT_5_6_SOL);
        } else if (this.availableProviders.includes(Providers.ANTHROPIC)) {
          this.onModelChange(Models.OPUS_4_8);
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
