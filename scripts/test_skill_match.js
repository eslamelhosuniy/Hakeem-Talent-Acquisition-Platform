const fs = require("fs");
const http = require("http");
const path = require("path");

const SAMPLE_PATH = path.join(__dirname, "..", "samples", "sample_resume.txt");

function loadSampleText() {
  const text = fs.readFileSync(SAMPLE_PATH, "utf8");
  return text.toString();
}

function callSkillMatch(text) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      text,
      lang: "en",
    });

    const options = {
      hostname: "localhost",
      port: 8000,
      path: "/cv/parse",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(data),
      },
    };

    const req = http.request(options, (res) => {
      let body = "";

      res.on("data", (chunk) => {
        body += chunk;
      });

      res.on("end", () => {
        try {
          const json = JSON.parse(body);
          resolve(json);
        } catch (err) {
          reject(err);
        }
      });
    });

    req.on("error", (err) => {
      reject(err);
    });

    req.write(data);
    req.end();
  });
}

async function main() {
  try {
    const text = loadSampleText();
    console.log("Loaded sample resume text from:", SAMPLE_PATH);

    const result = await callSkillMatch(text);

    const skills = result.extracted_skills || [];
    const debug = result.skills_debug || [];

    console.log("\n=== Extracted Skills ===");
    console.log(skills);

    console.log("\n=== Top Debug Rows (up to 10) ===");
    console.log(
      debug.slice(0, 10).map((d) => ({
        skill: d.skill,
        method: d.method,
        score: d.score,
      }))
    );

    console.log("\nText preview:", (result.text_preview || "").slice(0, 200));
  } catch (err) {
    console.error("Error while testing skill match:", err);
    console.error(
      "Make sure the FastAPI app is running on http://localhost:8000 (uvicorn main:app --reload from src/)."
    );
    process.exit(1);
  }
}

main();

