import { useState, useRef, useEffect } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Keyboard, Mic, Square, Volume2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import jsPDF from "jspdf";
import { useNavigate, useLocation } from "react-router-dom";

const mockQuestions = [
  "Tell me about yourself.",
  "Why are you interested in this role?",
  "What are your strengths and weaknesses?",
  "Describe a challenge you faced and how you handled it.",
  "Where do you see yourself in five years?"
];

const ELEVENLABS_API_KEY = "sk_0c58373b505a6d26647ecc8baecaac4b6046b818b4feb3a5";
const DEFAULT_VOICES = [
  { id: "EXAVITQu4vr4xnSDxMaL", label: "Rachel" },
  { id: "MF3mGyEYCl7XYWbV9V6O", label: "Domi" },
  { id: "TxGEqnHWrfWFTfGW9XjX", label: "Antoni" },
  { id: "21m00Tcm4TlvDq8ikWAM", label: "Bella" },
];

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export default function MockInterview() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.state?.fromJobDescription) {
      localStorage.clear();
      setResponses(Array(mockQuestions.length).fill(""));
      setCurrentIndex(0);
      setShowTextarea(false);
      setFeedback("");
      setCompleted(false);
      setElapsedTime(0);
      stopRecognition();
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  const jobDescription = localStorage.getItem("jobDescription") || "Not provided.";

  const [responses, setResponses] = useState(() => JSON.parse(localStorage.getItem("responses") || "[]") || Array(mockQuestions.length).fill(""));
  const [currentIndex, setCurrentIndex] = useState(() => Number(localStorage.getItem("currentIndex")) || 0);
  const [showTextarea, setShowTextarea] = useState(false);
  const [feedback, setFeedback] = useState(() => localStorage.getItem("feedback") || "");
  const [completed, setCompleted] = useState(() => localStorage.getItem("completed") === "true");
  const [isListening, setIsListening] = useState(false);
  const [voiceId, setVoiceId] = useState(DEFAULT_VOICES[0].id);
  const [elapsedTime, setElapsedTime] = useState(() => Number(localStorage.getItem("elapsedTime")) || 0);

  const recognitionRef = useRef(null);
  const hasPlayedRef = useRef(false);

  useEffect(() => {
    let timer;
    if (!completed) {
      timer = setInterval(() => {
        setElapsedTime((prev) => {
          const newTime = prev + 1;
          localStorage.setItem("elapsedTime", newTime.toString());
          return newTime;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [completed]);

  useEffect(() => {
    localStorage.setItem("responses", JSON.stringify(responses));
    localStorage.setItem("currentIndex", currentIndex.toString());
    localStorage.setItem("feedback", feedback);
    localStorage.setItem("completed", completed.toString());
  }, [responses, currentIndex, feedback, completed]);

  const currentResponse = responses[currentIndex]?.trim();

  const handleResponseChange = (value) => {
    const updated = [...responses];
    updated[currentIndex] = value;
    setResponses(updated);
  };

  const stopRecognition = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
      setIsListening(false);
    }
  };

  const handleNext = () => {
    stopRecognition();
    if (currentIndex < mockQuestions.length - 1) {
      setShowTextarea(false);
      setCurrentIndex(currentIndex + 1);
      hasPlayedRef.current = false;
    } else {
      setCompleted(true);
      setFeedback("Great job! You answered all questions confidently. Improve time management slightly.");
    }
  };

  const restartInterview = () => {
    localStorage.clear();
    setResponses(Array(mockQuestions.length).fill(""));
    setCurrentIndex(0);
    setShowTextarea(false);
    setFeedback("");
    setCompleted(false);
    setElapsedTime(0);
    stopRecognition();
  };

  const exportToPDF = () => {
    const doc = new jsPDF();
    doc.setFontSize(16);
    doc.text("Mock Interview Review", 20, 20);
    doc.setFontSize(12);
    doc.text(`Total Time: ${formatTime(elapsedTime)}`, 20, 30);
    doc.text(`\nJob Description:`, 20, 40);
    doc.text(doc.splitTextToSize(jobDescription, 170), 20, 50);

    let y = 60 + doc.splitTextToSize(jobDescription, 170).length * 7;
    doc.text(`\nFeedback: ${feedback}`, 20, y);
    y += 15;

    mockQuestions.forEach((q, i) => {
      const answer = responses[i]?.trim() || "Skipped";
      doc.text(`Q${i + 1}: ${q}`, 20, y);
      doc.text(`A: ${answer}`, 20, y + 7);
      y += 15;
    });

    doc.save("mock_interview_review.pdf");
  };

  const playWithElevenLabs = async (text) => {
    try {
      const url = `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`;
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "xi-api-key": ELEVENLABS_API_KEY,
        },
        body: JSON.stringify({
          text,
          model_id: "eleven_monolingual_v1",
          voice_settings: { stability: 0.5, similarity_boost: 0.75 },
        }),
      });
      const audioBlob = await response.blob();
      const audioURL = URL.createObjectURL(audioBlob);
      new Audio(audioURL).play();
    } catch (err) {
      console.error("ElevenLabs error:", err);
    }
  };

  useEffect(() => {
    if (!completed && !hasPlayedRef.current) {
      playWithElevenLabs(mockQuestions[currentIndex]);
      hasPlayedRef.current = true;
    }
  }, [currentIndex, completed]);

  const handleStartVoice = () => {
    setShowTextarea(true);
    stopRecognition();
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return alert("Speech Recognition not supported");
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;
    let accumulated = responses[currentIndex] || "";
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognition.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const txt = e.results[i][0].transcript;
        if (e.results[i].isFinal) accumulated += txt + " ";
        else interim += txt;
      }
      handleResponseChange(accumulated + interim);
    };
    recognitionRef.current = recognition;
    recognition.start();
  };

  const handleStopVoice = () => stopRecognition();

  return (
    <div className="min-h-screen bg-neutral-50 text-gray-800 flex flex-col items-center justify-start p-10">
      <div className="max-w-5xl w-full space-y-8">
        <div className="flex justify-between items-center">
          <h1 className="text-5xl font-bold text-lavender-600">Mock Interview</h1>
          <div className="text-lg font-medium text-gray-700">⏱️ {formatTime(elapsedTime)}</div>
        </div>

        <div className="flex items-center justify-end space-x-2">
          <label htmlFor="voice-select" className="text-sm font-medium">Voice:</label>
          <select id="voice-select" value={voiceId} onChange={(e) => setVoiceId(e.target.value)} className="border rounded px-3 py-1 text-sm">
            {DEFAULT_VOICES.map((voice) => (
              <option key={voice.id} value={voice.id}>{voice.label}</option>
            ))}
          </select>
        </div>

        {!completed ? (
          <AnimatePresence mode="wait">
            <motion.div key={currentIndex} initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -30 }} transition={{ duration: 0.5 }} className="border rounded-3xl shadow-xl p-12 bg-white space-y-8 w-full">
              <div className="flex items-center justify-between">
                <p className="text-2xl font-semibold leading-relaxed">{mockQuestions[currentIndex]}</p>
                <Volume2 className="w-6 h-6 text-lavender-600 cursor-pointer" onClick={() => playWithElevenLabs(mockQuestions[currentIndex])} />
              </div>
              {showTextarea && (
                <Textarea value={responses[currentIndex] || ""} onChange={(e) => handleResponseChange(e.target.value)} placeholder="Type your response here..." rows={6} className="rounded-lg border-gray-300 shadow-sm" />
              )}
              <div className="flex flex-col space-y-4">
                <div className="flex items-center space-x-4">
                  <Button variant="ghost" className="text-lavender-600" onClick={() => setShowTextarea(true)}><Keyboard className="mr-2" />Answer by typing</Button>
                  {!isListening ? (
                    <Button variant="ghost" className="text-lavender-600" onClick={handleStartVoice}><Mic className="mr-2" />Answer by voice</Button>
                  ) : (
                    <Button variant="ghost" className="text-red-600" onClick={handleStopVoice}><Square className="mr-2" />Stop recording</Button>
                  )}
                </div>
                {isListening && <div className="text-sm text-purple-600">🎙️ Listening...</div>}
              </div>
              <div className="flex justify-end space-x-4">
                <Button variant="outline" onClick={handleNext} className="text-gray-700">Skip</Button>
                <Button onClick={handleNext} disabled={!currentResponse} className={`px-6 py-2 rounded-md shadow-md ${currentResponse ? "bg-purple-200 hover:bg-purple-300 text-gray-900" : "bg-gray-300 text-white cursor-not-allowed"}`}>Next</Button>
              </div>
            </motion.div>
          </AnimatePresence>
        ) : (
          <div className="space-y-6 w-full">
            <div className="p-6 border-l-4 border-lavender-500 bg-white rounded-2xl shadow-lg w-full">
              <h2 className="text-2xl font-bold mb-2">🧠 AI Feedback</h2>
              <p className="text-lg leading-relaxed text-gray-700">{feedback}</p>
            </div>
            <div className="p-6 border bg-white rounded-xl shadow space-y-4 w-full">
              <h2 className="text-xl font-semibold mb-2">Review Your Interview</h2>
              {mockQuestions.map((q, idx) => (
                <div key={idx} className="border-t pt-3">
                  <p className="font-semibold">Q{idx + 1}. {q}</p>
                  <p className="text-sm mt-1 text-gray-700">{responses[idx]?.trim() ? responses[idx] : <span className="italic text-red-500">Skipped</span>}</p>
                </div>
              ))}
            </div>
            <div className="flex flex-wrap gap-4 justify-end">
              <Button onClick={restartInterview} className="bg-gray-200 hover:bg-gray-300 text-gray-900">Restart Interview</Button>
              <Button onClick={() => navigate("/job-description")} className="bg-blue-200 hover:bg-blue-300 text-blue-900">Change Job Description</Button>
              <Button onClick={exportToPDF} className="bg-green-200 hover:bg-green-300 text-green-900">Export as PDF</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}