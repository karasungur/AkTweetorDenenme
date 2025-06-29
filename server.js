const express = require("express");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.static("public"));
app.use(express.json());

// Route to serve the main page
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

// API route to simulate Twitter automation status
app.get("/api/status", (req, res) => {
  res.json({
    status: "ready",
    message: "AkTweetor Web Version - Twitter Automation Tool",
    version: "1.0.0",
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 AkTweetor Web Server running on port ${PORT}`);
  console.log(`✅ Server is ready at http://localhost:${PORT}`);
});
