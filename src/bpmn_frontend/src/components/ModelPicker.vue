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
    <div
      v-if="showReasoningModelWarning"
      class="text-caption text-warning mt-1"
      style="width: 200px; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis"
      title="Reasoning model - may be slower"
    >
      ⚠️ Reasoning model - slower
    </div>
  </div>
</template>

<script>
import { bpmnAssistantUrl, isHostedVersion } from '../config';
import { getApiKeys } from '../utils/apiKeys';

const Models = Object.freeze({
  GPT_5_1: 'gpt-5.1',
  GPT_5_MINI: 'gpt-5-mini',
  GPT_4_1: 'gpt-4.1',
  SONNET_4_5: 'claude-sonnet-4-5-20250929',
  OPUS_4_1: 'claude-opus-4-1-20250805',
  GEMINI_2_5_PRO: 'gemini/gemini-2.5-pro',
  GEMINI_2_5_FLASH: 'gemini/gemini-2.5-flash',
  LLAMA_4_MAVERICK:
    'fireworks_ai/accounts/fireworks/models/llama4-maverick-instruct-basic',
  QWEN_3_235B: 'fireworks_ai/accounts/fireworks/models/qwen3-235b-a22b',
  DEEPSEEK_V3_1: 'fireworks_ai/accounts/fireworks/models/deepseek-v3p1-terminus',
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
      customOpenAIModelName: null,
      models: [
        { value: Models.GPT_5_1, title: 'GPT-5.1', provider: Providers.OPENAI },
        {
          value: Models.GPT_5_MINI,
          title: 'GPT-5 mini',
          provider: Providers.OPENAI,
        },
        { value: Models.GPT_4_1, title: 'GPT-4.1', provider: Providers.OPENAI },
        {
          value: Models.SONNET_4_5,
          title: 'Claude Sonnet 4.5',
          provider: Providers.ANTHROPIC,
        },
        {
          value: Models.OPUS_4_1,
          title: 'Claude Opus 4.1',
          provider: Providers.ANTHROPIC,
        },
        {
          value: Models.GEMINI_2_5_FLASH,
          title: 'Gemini 2.5 Flash',
          provider: Providers.GOOGLE,
        },
        {
          value: Models.GEMINI_2_5_PRO,
          title: 'Gemini 2.5 Pro',
          provider: Providers.GOOGLE,
        },
        {
          value: Models.LLAMA_4_MAVERICK,
          title: 'Llama 4 Maverick',
          provider: Providers.FIREWORKS_AI,
        },
        {
          value: Models.QWEN_3_235B,
          title: 'Qwen 3',
          provider: Providers.FIREWORKS_AI,
        },
        {
          value: Models.DEEPSEEK_V3_1,
          title: 'Deepseek V3.1',
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

      // Replace OpenAI models with single custom model entry if custom name is set
      if (this.customOpenAIModelName && this.availableProviders.includes(Providers.OPENAI)) {
        const openaiModels = filteredModels.filter(
          (model) => model.provider === Providers.OPENAI
        );
        const otherModels = filteredModels.filter(
          (model) => model.provider !== Providers.OPENAI
        );
        if (openaiModels.length > 0) {
          // Show only one OpenAI model entry with custom name (use first model's value for backend mapping)
          filteredModels = [
            { ...openaiModels[0], title: this.customOpenAIModelName },
            ...otherModels,
          ];
        }
      }

      return filteredModels;
    },
    showReasoningModelWarning() {
      return (
        this.selectedModel === Models.GPT_5 ||
        this.selectedModel === Models.GPT_5_MINI
      );
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
            (provider) => data[provider] && provider !== 'openai_model_name'
          );

          // Store custom OpenAI model name if provided
          if (data.openai_model_name) {
            this.customOpenAIModelName = data.openai_model_name;
          }
        }

        // Notify parent if no providers available
        const hasProviders = this.availableProviders.length > 0;
        this.$parent.setHasAvailableProviders(hasProviders);

        if (this.availableProviders.includes(Providers.OPENAI)) {
          // When custom model name is set, select the first OpenAI model (which will be shown with custom name)
          // Otherwise default to GPT_4_1
          let modelToSelect = Models.GPT_4_1;
          if (this.customOpenAIModelName) {
            const firstOpenAIModel = this.models.find(
              (model) => model.provider === Providers.OPENAI
            );
            if (firstOpenAIModel) {
              modelToSelect = firstOpenAIModel.value;
            }
          }
          this.onModelChange(modelToSelect);
        } else if (this.availableProviders.includes(Providers.ANTHROPIC)) {
          this.onModelChange(Models.SONNET_4_5);
        } else if (this.availableProviders.includes(Providers.GOOGLE)) {
          this.onModelChange(Models.GEMINI_2_5_PRO);
        } else if (this.availableProviders.includes(Providers.FIREWORKS_AI)) {
          this.onModelChange(Models.DEEPSEEK_V3_1);
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
