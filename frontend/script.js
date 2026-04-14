const form = document.getElementById("summarize-form");
const urlInput = document.getElementById("youtube-url");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const titleEl = document.getElementById("video-title");
const summaryEl = document.getElementById("summary");
const transcriptEl = document.getElementById("transcript");

function setStatus(message, type = "info") {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  statusEl.classList.remove("hidden");
}

function clearStatus() {
  statusEl.className = "status hidden";
  statusEl.textContent = "";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearStatus();
  resultEl.classList.add("hidden");

  const youtubeUrl = urlInput.value.trim();
  if (!youtubeUrl) {
    setStatus("Please enter a YouTube URL.", "error");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Processing...";
  setStatus("Downloading, transcribing, and summarizing. This can take 1-3 minutes.");

  try {
    const response = await fetch("/api/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ youtube_url: youtubeUrl }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Something went wrong.");
    }

    titleEl.textContent = data.video_title;
    summaryEl.textContent = data.summary;
    transcriptEl.textContent = data.transcript;
    resultEl.classList.remove("hidden");
    setStatus("Done.");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Generate";
  }
});
