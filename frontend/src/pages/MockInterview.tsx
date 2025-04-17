import { useState, useRef, useEffect } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Keyboard, Mic, Square, Volume2, Contact } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import jsPDF from "jspdf";
import { useNavigate, useLocation } from "react-router-dom";
import "@/styles/animated-gradient.css";

const mockQuestions = [
  "Tell me about yourself.",
  "Why are you interested in this role?",
  "What are your strengths and weaknesses?",
  "Describe a challenge you faced and how you handled it.",
  "Where do you see yourself in five years?"
];

const DEFAULT_VOICES = [
  { id: "EXAVITQu4vr4xnSDxMaL", label: "Rachel" },
  { id: "MF3mGyEYCl7XYWbV9V6O", label: "Domi" },
  { id: "TxGEqnHWrfWFTfGW9XjX", label: "Antoni" },
  { id: "21m00Tcm4TlvDq8ikWAM", label: "Bella" },
];

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export default function MockInterview() {
  const navigate = useNavigate();
  const location = useLocation();

  const [jobDescription] = useState(() => localStorage.getItem("job_description") || "");
  const [responses, setResponses] = useState(() => JSON.parse(localStorage.getItem("responses") || "[]") || Array(mockQuestions.length).fill(""));
  const [currentIndex, setCurrentIndex] = useState(() => Number(localStorage.getItem("currentIndex")) || 0);
  const [showTextarea, setShowTextarea] = useState(false);
  const [feedback, setFeedback] = useState(() => localStorage.getItem("feedback") || "");
  const [completed, setCompleted] = useState(() => localStorage.getItem("completed") === "true");
  const [isListening, setIsListening] = useState(false);
  const [voiceId, setVoiceId] = useState(DEFAULT_VOICES[0].id);
  const [elapsedTime, setElapsedTime] = useState(() => Number(localStorage.getItem("elapsedTime")) || 0);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const hasPlayedRef = useRef(false);

  useEffect(() => {
    if (location.state?.fromJobDescription) {
      // Clear only interview-specific data, NOT job description
      localStorage.removeItem("responses");
      localStorage.removeItem("currentIndex");
      localStorage.removeItem("feedback");
      localStorage.removeItem("completed");
      localStorage.removeItem("elapsedTime");

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

  useEffect(() => {
    let timer: string | number | NodeJS.Timeout | undefined;
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

  const handleResponseChange = (value: string) => {
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
    // Only clear interview-specific data, not job description
    localStorage.removeItem("responses");
    localStorage.removeItem("currentIndex");
    localStorage.removeItem("feedback");
    localStorage.removeItem("completed");
    localStorage.removeItem("elapsedTime");

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
    doc.text("Job Description:", 20, 40);
    const wrappedDesc = doc.splitTextToSize(jobDescription, 170);
    doc.text(wrappedDesc, 20, 50);
    let y = 50 + wrappedDesc.length * 7;

    doc.text(`Feedback: ${feedback}`, 20, y);
    y += 15;

    mockQuestions.forEach((q, i) => {
      const answer = responses[i]?.trim() || "Skipped";
      doc.text(`Q${i + 1}: ${q}`, 20, y);
      y += 7;
      doc.text(`A: ${answer}`, 20, y);
      y += 10;
    });

    doc.save("mock_interview_review.pdf");
  };

  const playWithElevenLabs = async (text: string) => {
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
    recognition.onresult = (ev: SpeechRecognitionEvent) => {
      let interim = "";
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        const txt = ev.results[i][0].transcript;
        if (ev.results[i].isFinal) accumulated += txt + " ";
        else interim += txt;
      }
      handleResponseChange(accumulated + interim);
    };
    recognitionRef.current = recognition;
    recognition.start();
  };

  const handleStopVoice = () => stopRecognition();

  return (
    <div className="animated-gradient min-h-screen text-gray-800 flex flex-col items-center justify-start p-10">
      <div className="max-w-5xl w-full space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 text-gray-700">
            <Contact className="w-7 h-7 text-green" />
            <h1 className="text-4xl font-semibold">Mock Interview</h1>
          </div>
          <div className="text-lg font-medium text-gray-600">⏱️ {formatTime(elapsedTime)}</div>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="voice-select" className="text-sm font-medium text-gray-700">Voice:</label>
          <select id="voice-select" value={voiceId} onChange={(e) => setVoiceId(e.target.value)} className="border rounded px-3 py-1 text-sm bg-white">
            {DEFAULT_VOICES.map((voice) => (
              <option key={voice.id} value={voice.id}>{voice.label}</option>
            ))}
          </select>
        </div>

        {!completed ? (
          <AnimatePresence mode="wait">
            <motion.div
              key={currentIndex}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="rounded-2xl shadow-lg p-10 bg-white/90 backdrop-blur-md space-y-6"
            >
              <div className="flex items-center justify-between">
                <p className="text-xl font-medium text-gray-700 leading-relaxed">
                  {mockQuestions[currentIndex]}
                </p>
                <Volume2 className="w-5 h-5 text-[#ba68c8] cursor-pointer" onClick={() => playWithElevenLabs(mockQuestions[currentIndex])} />
              </div>
              {showTextarea && (
                <Textarea
                  value={responses[currentIndex] || ""}
                  onChange={(e) => handleResponseChange(e.target.value)}
                  placeholder="Type your response here..."
                  rows={6}
                  className="rounded-lg border-gray-300 shadow-sm"
                />
              )}
              <div className="flex flex-col space-y-4">
                <div className="flex items-center space-x-4">
                  <Button variant="ghost" className="text-[#ba68c8] hover:text-[#ab47bc]" onClick={() => setShowTextarea(true)}>
                    <Keyboard className="mr-2" /> Answer by typing
                  </Button>
                  {!isListening ? (
                    <Button variant="ghost" className="text-[#ba68c8] hover:text-[#ab47bc]" onClick={handleStartVoice}>
                      <Mic className="mr-2" /> Answer by voice
                    </Button>
                  ) : (
                    <Button variant="ghost" className="text-red-600 hover:text-red-700" onClick={handleStopVoice}>
                      <Square className="mr-2" /> Stop recording
                    </Button>
                  )}
                </div>
                {isListening && <div className="text-sm text-purple-500">🎙️ Listening...</div>}
              </div>
              <div className="flex justify-end space-x-4 pt-2">
                <Button variant="outline" onClick={handleNext} className="text-gray-700 border-gray-300">Skip</Button>
                <Button onClick={handleNext} disabled={!currentResponse} className={`px-5 py-2 font-medium rounded-md shadow-md transition-colors duration-300 ${currentResponse ? "bg-[#f8bbd0] hover:bg-[#f48fb1] text-gray-800" : "bg-gray-200 text-white cursor-not-allowed"}`}>Next</Button>
              </div>
            </motion.div>
          </AnimatePresence>
        ) : (
          <div className="space-y-6 w-full">
            <div className="p-6 border-l-4 border-[#f8bbd0] bg-white/90 backdrop-blur-md rounded-2xl shadow-md">
              <h2 className="text-2xl font-semibold mb-2 text-gray-700">🧠 AI Feedback</h2>
              <p className="text-base leading-relaxed text-gray-700">{feedback}</p>
            </div>
            <div className="p-6 border bg-white/90 backdrop-blur-md rounded-xl shadow space-y-4">
              <h2 className="text-lg font-semibold text-gray-700">Review Your Interview</h2>
              {mockQuestions.map((q, idx) => (
                <div key={idx} className="border-t pt-3">
                  <p className="font-medium">Q{idx + 1}. {q}</p>
                  <p className="text-sm mt-1 text-gray-700">{responses[idx]?.trim() ? responses[idx] : <span className="italic text-red-500">Skipped</span>}</p>
                </div>
              ))}
            </div>
            <div className="flex flex-wrap gap-4 justify-end">
              <Button onClick={restartInterview} className="bg-gray-200 hover:bg-gray-300 text-gray-800">Restart Interview</Button>
              <Button onClick={() => navigate("/")} className="bg-[#f3e5f5] hover:bg-[#e1bee7] text-[#6a1b9a]">Change Job Description</Button>
              <Button onClick={exportToPDF} className="bg-[#ce93d8] hover:bg-[#ba68c8] text-white">Export as PDF</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}