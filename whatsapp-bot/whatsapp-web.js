// whatsapp-web.js — SafeTalk-AI + H.I.V.E. Honeypot Integration
const { Client, LocalAuth } = require("whatsapp-web.js");
const qrTerminal = require("qrcode-terminal");
const QRCode = require("qrcode");
const axios = require("axios");
const fs = require("fs");
const path = require("path");
const mime = require("mime-types");
const express = require("express");
const { exec } = require("child_process");

const API_BASE = "http://localhost:8000";

console.log("Initializing SafeTalk-AI + H.I.V.E. Honeypot bot...");

// Per-chat state: tracks active honeypot sessions
// Key = chat id, Value = { active, scamType, persona, history, intel }
const honeypotSessions = {};
let latestQR = null;

// Audio folder
const audioDir = path.resolve(__dirname, "audios");
if (!fs.existsSync(audioDir)) {
  fs.mkdirSync(audioDir, { recursive: true });
}

// WhatsApp client
const client = new Client({
  authStrategy: new LocalAuth(),
  puppeteer: {
    headless: false,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  },
});

let BOT_NUMBER = "";

client.on("loading_screen", (percent, message) => {
  console.log(`Loading WhatsApp... (${percent}%) ${message}`);
});

client.on("authenticated", () => {
  console.log("Authenticated successfully.");
});

client.on("auth_failure", (msg) => {
  console.error("Authentication failed:", msg);
});

client.on("disconnected", (reason) => {
  console.warn("Disconnected from WhatsApp. Reason:", reason);
});

client.on("qr", async (qr) => {
  // Terminal QR (fallback)
  qrTerminal.generate(qr, { small: true });

  // Save as image file
  const qrPath = path.resolve(__dirname, "qr-code.png");
  await QRCode.toFile(qrPath, qr, { width: 400 });
  console.log(`\nQR code saved to: ${qrPath}`);
  console.log("Open the file or go to http://localhost:3000/qr to scan.");

  // Store QR data so the Express server can serve it
  latestQR = qr;
});

client.on("ready", async () => {
  BOT_NUMBER = client.info.wid._serialized;
  console.log("Bot connected to WhatsApp!");
  console.log("My number is:", BOT_NUMBER);
  await client.sendMessage(
    BOT_NUMBER,
    "[SafeTalk-AI + H.I.V.E.] Bot started.\nCommands:\n!status - check bot status\n!honeypot on - enable auto-engage\n!honeypot off - disable\n!intel - show extracted intelligence",
  );
});

// ── Helpers ──────────────────────────────────────────────

function guessScamType(text) {
  const lower = text.toLowerCase();
  if (lower.includes("upi") || lower.includes("@")) return "upi_fraud";
  if (
    lower.includes("bank") ||
    lower.includes("account") ||
    lower.includes("otp")
  )
    return "bank_fraud";
  if (
    lower.includes("lottery") ||
    lower.includes("prize") ||
    lower.includes("winner")
  )
    return "lottery";
  if (
    lower.includes("click") ||
    lower.includes("link") ||
    lower.includes("http")
  )
    return "phishing";
  return "default";
}

// Whether honeypot auto-engage is globally on (default: on)
let honeypotEnabled = true;

// ── Message handler ──────────────────────────────────────

client.on("message", async (msg) => {
  if (msg.fromMe) return;

  const chatId = msg.from;

  console.log(`\n--- Message from ${chatId} ---`);
  console.log("Content:", msg.body || "[media]");
  console.log("Type:", msg.type);

  // ── Bot commands ──
  if (msg.body?.startsWith("!")) {
    const cmd = msg.body.toLowerCase().trim();

    if (cmd === "!status") {
      const sessionCount = Object.keys(honeypotSessions).length;
      await client.sendMessage(
        chatId,
        `[SafeTalk-AI] Status: Online\nHoneypot: ${honeypotEnabled ? "ON" : "OFF"}\nActive sessions: ${sessionCount}`,
      );
      return;
    }

    if (cmd === "!honeypot on") {
      honeypotEnabled = true;
      await client.sendMessage(
        chatId,
        "[SafeTalk-AI] Honeypot auto-engage: ON",
      );
      return;
    }

    if (cmd === "!honeypot off") {
      honeypotEnabled = false;
      await client.sendMessage(
        chatId,
        "[SafeTalk-AI] Honeypot auto-engage: OFF",
      );
      return;
    }

    if (cmd === "!intel") {
      const session = honeypotSessions[chatId];
      if (!session || !session.intel) {
        await client.sendMessage(
          chatId,
          "[SafeTalk-AI] No intelligence collected for this chat yet.",
        );
        return;
      }
      const i = session.intel;
      await client.sendMessage(
        chatId,
        `[Intelligence Report]\nUPI IDs: ${i.upiIds?.join(", ") || "none"}\nPhone Numbers: ${i.phoneNumbers?.join(", ") || "none"}\nLinks: ${i.phishingLinks?.join(", ") || "none"}\nKeywords: ${i.suspiciousKeywords?.join(", ") || "none"}\nMessages tracked: ${session.history?.length || 0}`,
      );
      return;
    }

    if (cmd === "!reset") {
      delete honeypotSessions[chatId];
      await client.sendMessage(
        chatId,
        "[SafeTalk-AI] Honeypot session reset for this chat.",
      );
      return;
    }

    return;
  }

  // ── Audio handling ──
  if (msg.hasMedia) {
    try {
      const media = await msg.downloadMedia();
      if (media && media.mimetype?.startsWith("audio")) {
        const extension = mime.extension(media.mimetype) || "ogg";
        const filename = `audio_${Date.now()}.${extension}`;
        const filepath = path.join(audioDir, filename);

        fs.writeFileSync(filepath, Buffer.from(media.data, "base64"));
        console.log(`Audio saved: ${filename}`);

        const transcribePath = path.resolve(__dirname, "../transcribe.py");
        const command = `python "${transcribePath}" "${filepath}"`;

        console.log("Starting transcription...");
        exec(command, async (error, stdout, stderr) => {
          if (error) {
            console.error("Transcription error:", error.message);
            return;
          }
          // Extract transcribed text and process it like a normal message
          const match = stdout.match(/Transcription:\s*(.+)/);
          if (match) {
            const transcribed = match[1].trim();
            console.log("Transcribed:", transcribed);
            await processTextMessage(transcribed, chatId);
          }
        });
      }
    } catch (err) {
      console.error("Error processing media:", err.message);
    }
    return;
  }

  // ── Regular text messages ──
  if (msg.body) {
    await processTextMessage(msg.body, chatId);
  }
});

// ── Core logic ──────────────────────────────────────────

async function processTextMessage(text, chatId) {
  try {
    // If there's already an active honeypot session for this chat, continue it
    if (honeypotSessions[chatId]?.active) {
      await continueHoneypot(text, chatId);
      return;
    }

    // Step 1: Analyze with SafeTalk-AI ML model
    const { data: detection } = await axios.post(`${API_BASE}/analyze-text`, {
      message: text,
    });

    console.log("ML Detection:", detection);

    const isScam =
      detection.risk && detection.risk.toLowerCase().includes("scam");

    if (isScam && honeypotEnabled) {
      // Scam detected — start honeypot session
      console.log("SCAM DETECTED — Starting honeypot session for", chatId);

      const scamType = guessScamType(text);

      // Notify the user (bot owner) about the detection
      await client.sendMessage(
        BOT_NUMBER,
        `[SCAM DETECTED]\nFrom: ${chatId}\nMessage: "${text}"\nRisk: ${detection.risk}\nConfidence: ${detection.confidence}\nAction: Honeypot engaged (${scamType})`,
      );

      // Initialize session
      honeypotSessions[chatId] = {
        active: true,
        scamType: scamType,
        history: [],
        intel: null,
        startTime: Date.now(),
      };

      // Generate first honeypot reply
      await continueHoneypot(text, chatId);
    } else if (isScam && !honeypotEnabled) {
      // Scam detected but honeypot is off — just alert
      const alert = `[SCAM ALERT]\nMessage: "${text}"\nRisk: ${detection.risk}\nConfidence: ${detection.confidence}\nReason: ${detection.reason}`;
      await client.sendMessage(chatId, alert);
    } else {
      // Legitimate message — do nothing or optionally respond
      console.log("Message appears legitimate. No action.");
    }
  } catch (error) {
    console.error("Error processing message:", error.message);
  }
}

async function continueHoneypot(scammerText, chatId) {
  const session = honeypotSessions[chatId];

  // Add scammer message to history
  session.history.push({ sender: "scammer", text: scammerText });

  try {
    // Generate AI honeypot reply
    const { data: honeypot } = await axios.post(`${API_BASE}/honeypot/reply`, {
      scammer_message: scammerText,
      scam_type: session.scamType,
      conversation_history: session.history,
    });

    const reply = honeypot.reply;
    console.log(`Honeypot [${honeypot.persona_name}]: ${reply}`);

    // Add our reply to history
    session.history.push({ sender: "victim", text: reply });

    // Send the honeypot reply to the scammer
    await client.sendMessage(chatId, reply);

    // Extract intelligence from the full conversation so far
    const fullText = session.history.map((m) => m.text).join(" ");
    const { data: intel } = await axios.post(`${API_BASE}/honeypot/extract`, {
      message: fullText,
    });
    session.intel = intel;

    // Log intel if anything new found
    const hasIntel =
      intel.upiIds?.length ||
      intel.phoneNumbers?.length ||
      intel.phishingLinks?.length;
    if (hasIntel) {
      console.log("Intelligence update:", JSON.stringify(intel, null, 2));

      // Notify bot owner about new intel
      await client.sendMessage(
        BOT_NUMBER,
        `[Intel Update - ${chatId}]\nUPI: ${intel.upiIds?.join(", ") || "-"}\nPhones: ${intel.phoneNumbers?.join(", ") || "-"}\nLinks: ${intel.phishingLinks?.join(", ") || "-"}`,
      );
    }
  } catch (error) {
    console.error("Honeypot reply error:", error.message);
  }
}

client.initialize();

// ── Express server for external alerts ──
const app = express();
app.use(express.json());

app.post("/alert", (req, res) => {
  const { number, message } = req.body;
  if (number && message) {
    client.sendMessage(number, message);
    res.send({ status: "Alert sent." });
  } else {
    res.status(400).send({ error: "Missing number or message." });
  }
});

app.get("/sessions", (req, res) => {
  const summary = {};
  for (const [chatId, session] of Object.entries(honeypotSessions)) {
    summary[chatId] = {
      active: session.active,
      scamType: session.scamType,
      turns: session.history.length,
      intel: session.intel,
      duration: Math.round((Date.now() - session.startTime) / 1000) + "s",
    };
  }
  res.json(summary);
});

// Serve QR code as a scannable page
app.get("/qr", async (req, res) => {
  if (!latestQR) {
    res.send("<h2>No QR code available. Bot may already be connected.</h2>");
    return;
  }
  try {
    const qrDataUrl = await QRCode.toDataURL(latestQR, { width: 500 });
    res.send(`
      <html>
      <head><title>SafeTalk-AI - Scan QR</title></head>
      <body style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;background:#f5f5f5;">
        <h2>SafeTalk-AI + H.I.V.E. — WhatsApp QR</h2>
        <p>Scan this with your WhatsApp app:</p>
        <img src="${qrDataUrl}" alt="QR Code" />
        <p style="color:#888;margin-top:16px;">QR refreshes automatically. Reload if expired.</p>
      </body>
      </html>
    `);
  } catch (e) {
    res.status(500).send("Error generating QR: " + e.message);
  }
});

app.listen(3000, () => {
  console.log("Express server at http://localhost:3000");
  console.log("  GET  /qr       — scan QR code in browser");
  console.log("  POST /alert    — send external alerts");
  console.log("  GET  /sessions — view active honeypot sessions");
});
