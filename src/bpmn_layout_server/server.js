const express = require('express');
const bodyParser = require('body-parser');
const { layoutProcess } = require('bpmn-auto-layout');

const app = express();
const port = 3001;

app.use(bodyParser.json());

app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

app.post('/process-bpmn', async (req, res) => {
  const { bpmnXml } = req.body;

  try {
    const layoutedXml = await layoutProcess(bpmnXml);
    res.json({ layoutedXml });
  } catch (error) {
    console.error('Error processing BPMN XML:', error);
    res.status(500).send('Failed to process BPMN XML');
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
