<template>
  <div class="mb-3 mx-2">
    <v-card
      :style="{ backgroundColor: getBackgroundColor() }"
      class="text-black"
    >
      <v-card-subtitle class="mt-2"
        ><b>{{ roleDisplay }}</b></v-card-subtitle
      >
      <v-card-text class="card-text" v-html="formattedContent"></v-card-text>
    </v-card>
  </div>
</template>

<script>
export default {
  props: {
    role: String,
    content: String,
  },
  computed: {
    roleDisplay() {
      return this.role === "user" ? "You" : "BPMN Assistant";
    },
    formattedContent() {
      return this.content
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n- /g, "<br>• ")
        .replace(/\n/g, "<br>");
    },
  },
  methods: {
    getBackgroundColor() {
      return this.role === "user"
        ? "rgba(0, 100, 255, 0.1)"
        : "rgba(255, 0, 0, 0.1)";
    },
  },
};
</script>

<style scoped>
.card-text {
  padding: 5px 15px 10px;
}
</style>
