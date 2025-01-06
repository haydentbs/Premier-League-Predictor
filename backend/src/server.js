const express = require('express');
const cors = require('cors');
const apiRoutes = require('./routes/api');
const scheduler = require('./services/scheduler');

const app = express();
const port = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Mount API routes
app.use('/api', apiRoutes);

// Start the scheduler
scheduler.start();

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});