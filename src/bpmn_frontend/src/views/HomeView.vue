<template>
  <div class="workspace">
    <header id="workspace-header"></header>
    <div class="workspace-body">
    <div class="chat-container">
      <ChatInterface
        @bpmn-xml-received="handleBpmnXml"
        @bpmn-json-received="setBpmnJson"
        @download="downloadBpmnFile"
        :isDownloadReady="!!bpmnXml"
        :process="process"
      />
    </div>
    <div
      id="canvas"
      class="canvas-container"
      @dragover.prevent
      @drop="handleDrop"
    ></div>
    </div>
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script>
import BpmnModeler from 'bpmn-js/lib/Modeler';
import ChatInterface from '../components/ChatInterface.vue';
import { bpmnAssistantUrl, bpmnLayoutServerUrl } from '../config';
import { getApiKeys } from '../utils/apiKeys';
// import initialDiagram from "../assets/initialDiagram.js";
import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css';

export default {
  name: 'App',
  components: {
    ChatInterface,
  },
  data() {
    return {
      bpmnXml: '',
      process: null, // Process in JSON format
      bpmnViewer: null,
      snackbar: {
        show: false,
        text: '',
        color: 'success',
      },
    };
  },
  mounted() {
    this.bpmnViewer = new BpmnModeler({
      container: '#canvas',
    });

    // this.bpmnViewer
    //   .importXML(initialDiagram)
    //   .then((result) => {
    //     const { warnings } = result;
    //     console.log("BPMN diagram imported successfully", warnings);
    //     this.bpmnViewer.get("canvas").zoom("fit-viewport");
    //   })
    //   .catch((err) => {
    //     console.error("Failed to import BPMN diagram:", err);
    //   });
  },
  beforeUnmount() {
    if (this.bpmnViewer) {
      this.bpmnViewer.destroy();
    }
  },
  methods: {
    showSnackbar(text, color = 'success') {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.show = true;
    },
    async handleDrop(event) {
      event.preventDefault(); // Prevent the browser from default file handling
      if (event.dataTransfer.items) {
        for (let i = 0; i < event.dataTransfer.items.length; i++) {
          if (event.dataTransfer.items[i].kind === 'file') {
            const file = event.dataTransfer.items[i].getAsFile();

            if (file.name.endsWith('.bpmn')) {
              const reader = new FileReader();
              reader.onload = async (e) => {
                const xmlContent = e.target.result;
                try {
                  await this.bpmnViewer.importXML(xmlContent);
                  this.bpmnViewer.get('canvas').zoom('fit-viewport');
                  console.log('BPMN diagram loaded successfully');
                  this.bpmnXml = xmlContent;
                  await this.createBpmnJson();
                } catch (err) {
                  console.error('Failed to import BPMN diagram:', err);
                }
              };
              reader.readAsText(file);
            }
          }
        }
      }
    },
    async createBpmnJson() {
      try {
        const apiKeys = getApiKeys();
        const response = await fetch(`${bpmnAssistantUrl}/bpmn_to_json`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bpmn_xml: this.bpmnXml, api_keys: apiKeys }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        this.process = await response.json();
        console.log('BPMN JSON created successfully:', this.process);
        this.showSnackbar('BPMN successfully uploaded', 'success');
      } catch (error) {
        console.error('Error creating BPMN JSON:', error);
        this.showSnackbar(
          'There was a problem while loading the BPMN file',
          'error'
        );
      }
    },
    async handleBpmnXml(bpmnXmlValue) {
      if (bpmnXmlValue === '') {
        if (this.bpmnViewer) {
          this.bpmnViewer.destroy();
        }

        this.bpmnViewer = new BpmnModeler({
          container: '#canvas',
        });
        return;
      }

      try {
        // Auto-layout of the BPMN diagram
        const layoutedXml = await this.processDiagram(bpmnXmlValue);
        if (!layoutedXml) {
          throw new Error('Failed to layout the BPMN diagram');
        }
        this.bpmnXml = layoutedXml;
        if (this.bpmnViewer) {
          this.bpmnViewer
            .importXML(layoutedXml)
            .then((result) => {
              const { warnings } = result;
              console.log('BPMN diagram imported successfully', warnings);
              this.bpmnViewer.get('canvas').zoom('fit-viewport');
            })
            .catch((err) => {
              console.error('Failed to import BPMN diagram:', err);
            });
        }
      } catch (error) {
        console.error('Error handling BPMN XML:', error);
      }
    },
    async processDiagram(bpmnDiagram) {
      try {
        const response = await fetch(`${bpmnLayoutServerUrl}/process-bpmn`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ bpmnXml: bpmnDiagram }),
        });

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const { layoutedXml } = await response.json();

        console.log(layoutedXml);

        return layoutedXml;
      } catch (error) {
        console.error('Failed to process the diagram:', error);
      }
    },
    async downloadBpmnFile() {
      const { xml } = await this.bpmnViewer.saveXML();
      const blob = new Blob([xml], { type: 'text/xml' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'diagram.bpmn';
      a.click();
    },
    setBpmnJson(value) {
      this.process = value;
    },
  },
};
</script>

<style>
.workspace { height: 100dvh; display: flex; flex-direction: column; background: #f7f8fa; color: #202938; font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
#workspace-header { flex: 0 0 72px; background: white; border-bottom: 1px solid #e6e9ef; z-index: 5; }
.workspace-body { display: flex; flex: 1; min-height: 0; }
.chat-container { flex: 0 0 390px; min-width: 0; background: white; border-right: 1px solid #e6e9ef; }
.canvas-container { flex: 1; min-width: 0; margin: 12px; border: 1px solid #e1e5ec; border-radius: 12px; overflow: hidden; background: white; }
.canvas-container .djs-palette { border: 1px solid #e1e5ec; border-radius: 10px; background: #fff; box-shadow: 0 3px 12px #2636500a; }
@media (max-width: 900px) {
  .chat-container { flex-basis: 340px; }
  #workspace-header { flex-basis: 112px; }
}
@media (max-width: 600px) {
  .workspace-body { flex-direction: column-reverse; }
  .chat-container { flex: 1; min-height: 0; border-right: 0; }
  .canvas-container { flex: 0 0 35%; margin: 8px; }
}
</style>
