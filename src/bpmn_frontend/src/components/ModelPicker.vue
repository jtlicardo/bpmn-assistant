<template>
  <v-select
      label="Model"
      density="compact"
      :items="availableModels"
      :modelValue="selectedModel"
      @update:modelValue="onModelChange"
      :list-props="{ density: 'compact' }"
      no-data-text="Please provide API keys to access models"
  ></v-select>
</template>

<script>
export default {
  name: "ModelPicker",
  data() {
    return {
      selectedModel: "",
      models: [
        {value: "gpt-4o-mini", title: "GPT-4o mini", provider: "openai"},
        {value: "gpt-4-turbo", title: "GPT-4 Turbo", provider: "openai"},
        {value: "gpt-4o-2024-08-06", title: "GPT-4o", provider: "openai"},
        {
          value: "claude-3-opus-20240229",
          title: "Claude 3 Opus",
          provider: "anthropic",
        },
        {
          value: "claude-3-sonnet-20240229",
          title: "Claude 3 Sonnet",
          provider: "anthropic",
        },
        {
          value: "claude-3-haiku-20240307",
          title: "Claude 3 Haiku",
          provider: "anthropic",
        },
        {
          value: "claude-3-5-sonnet-20240620",
          title: "Claude 3.5 Sonnet",
          provider: "anthropic",
        },
      ],
      availableProviders: [],
    };
  },
  computed: {
    availableModels() {
      return this.models.filter((model) =>
          this.availableProviders.includes(model.provider)
      );
    },
  },
  methods: {
    onModelChange(model) {
      this.selectedModel = model;
      this.$emit("select-model", model);
    },
    async fetchAvailableProviders() {
      try {
        const response = await fetch(
            "http://localhost:8000/available_providers",
            {
              method: "GET",
              headers: {"Content-Type": "application/json"},
            }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        this.availableProviders = Object.keys(data).filter(
            (provider) => data[provider]
        );

        if (this.availableProviders.includes("openai")) {
          this.onModelChange("gpt-4o-mini");
        } else if (this.availableProviders.includes("anthropic")) {
          this.onModelChange("claude-3-5-sonnet-20240620");
        }
      } catch (error) {
        console.error("Error fetching available providers", error);
      }
    },
  },
  mounted() {
    this.fetchAvailableProviders();
  },
};
</script>
