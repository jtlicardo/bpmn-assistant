const express = require('express');
const bodyParser = require('body-parser');
const { layoutProcess } = require('bpmn-auto-layout');

const app = express();
const port = process.env.PORT || 3001;

app.use(bodyParser.json());

app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

app.get('/', (req, res) => {
  console.log('Health check');
  res.json({ status: 'ok' });
});

app.post('/process-bpmn', async (req, res) => {
  const { bpmnXml } = req.body;

  try {
    const { xml, warnings } = await layoutProcess(bpmnXml);
    res.json({ layoutedXml: xml, warnings: warnings.map(({ message, code }) => ({ message, code })) });
  } catch (error) {
    console.error('Error processing BPMN XML:', error);
    res.status(500).send('Failed to process BPMN XML');
  }
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Server running at http://0.0.0.0:${port}`);
});
