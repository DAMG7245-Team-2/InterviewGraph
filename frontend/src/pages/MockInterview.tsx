import { useState, useRef, useEffect } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Keyboard, Mic, Square, Volume2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import jsPDF from "jspdf";
import { useNavigate, useLocation } from "react-router-dom";
import "@/styles/animated-gradient.css";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

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
  const [threadId] = useState(() => localStorage.getItem("thread_id") || "");
  const [questions, setQuestions] = useState<string[]>([]);
  const [responses, setResponses] = useState<string[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showTextarea, setShowTextarea] = useState(false);
  const [feedbackList, setFeedbackList] = useState<{ question: string; feedback: string }[]>([]);
  const [completed, setCompleted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceId, setVoiceId] = useState(DEFAULT_VOICES[0].id);
  const [elapsedTime, setElapsedTime] = useState(0);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const hasPlayedRef = useRef(false);
  const hasStartedRef = useRef(false);

  useEffect(() => {
    if (
      location.state?.fromJobDescription &&
      questions.length === 0 &&
      !hasStartedRef.current
    ) {
      hasStartedRef.current = true;
      fetchNext("START");
    }
  }, [location]);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
  
    if (!completed && !loading) {
      timer = setInterval(() => setElapsedTime((prev) => prev + 1), 1000);
    }
  
    return () => clearInterval(timer);
  }, [completed, loading]);

  const fetchNext = async (message: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/interview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, thread_id: threadId }),
      });
      const data = await res.json();

      if (res.status === 418 || data.message === "Please provide a valid job description") {
        alert("Please provide a valid job description.");
        navigate("/");
        return;
      }

      if (data.feedback) {
        setCompleted(true);
        setLoading(false);

        // Update structured feedback
        setFeedbackList(
          data.feedback.map((f: any, i: number) => ({
            question: questions[i],
            feedback: f.feedback || f, 
          }))
        );

        return;
      }

      if (!data.message || data.message === "Interview complete") return;

      if (data.message !== questions[questions.length - 1]) {
        setQuestions((prev) => [...prev, data.message]);
        setResponses((prev) => [...prev, ""]);
        setCurrentIndex((prev) => prev + 1);
      }
    } catch (err) {
      console.error("Error fetching question:", err);
      setLoading(false);
    }
  };

  const currentResponse = responses[currentIndex - 1]?.trim();
  const currentQuestion = questions[currentIndex - 1] || "";

  const handleResponseChange = (value: string) => {
    const updated = [...responses];
    updated[currentIndex - 1] = value;
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
    setShowTextarea(false);
    hasPlayedRef.current = false;

    const responseToSend = responses[currentIndex - 1]?.trim() || "Skipped";

    if (currentIndex === 5) {
      setLoading(true);
    }

    fetchNext(responseToSend);
  };

  const playWithElevenLabs = async (text: string) => {
    try {
      const response = await fetch(`${BACKEND_URL}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice_id: voiceId }),
      });
      const audioBlob = await response.blob();
      const audioURL = URL.createObjectURL(audioBlob);
      new Audio(audioURL).play();
    } catch (err) {
      console.error("TTS error:", err);
    }
  };

  useEffect(() => {
    if (!completed && !hasPlayedRef.current && currentQuestion) {
      playWithElevenLabs(currentQuestion);
      hasPlayedRef.current = true;
    }
  }, [currentQuestion]);

  const handleStartVoice = () => {
    setShowTextarea(true);
    stopRecognition();
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return alert("Speech Recognition not supported");
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;
    let accumulated = responses[currentIndex - 1] || "";
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

  const restartInterview = () => {
    setResponses([]);
    setQuestions([]);
    setCurrentIndex(0);
    setShowTextarea(false);
    setFeedbackList([]);
    setCompleted(false);
    setElapsedTime(0);
    setLoading(false);
    stopRecognition();
    hasStartedRef.current = true;
    fetchNext("START");
  };

  const exportToPDF = () => {
    const doc = new jsPDF();
    const margin = 20;
    const lineHeight = 7;
    const pageHeight = doc.internal.pageSize.height;
  
    doc.setFontSize(16);
    doc.text("Mock Interview Review", margin, margin);
  
    doc.setFontSize(12);
    let y = margin + 10;
  
    doc.text(`Total Time: ${formatTime(elapsedTime)}`, margin, y);
    y += lineHeight;
  
    doc.text("Job Description:", margin, y);
    y += lineHeight;
  
    const descLines = doc.splitTextToSize(jobDescription, 170);
    descLines.forEach((line: string | string[]) => {
      if (y + lineHeight > pageHeight - margin) {
        doc.addPage();
        y = margin;
      }
      doc.text(line, margin, y);
      y += lineHeight;
    });
  
    y += lineHeight;
  
    feedbackList.forEach((f, i) => {
      const questionLines = doc.splitTextToSize(`Q${i + 1}: ${f.question}`, 170);
      const answer = responses[i]?.trim() || "Skipped";
      const answerLines = doc.splitTextToSize(`A: ${answer}`, 170);
      const feedbackLines = doc.splitTextToSize(`Feedback: ${f.feedback}`, 170);
  
      [...questionLines, ...answerLines, ...feedbackLines].forEach((line) => {
        if (y + lineHeight > pageHeight - margin) {
          doc.addPage();
          y = margin;
        }
        doc.text(line, margin, y);
        y += lineHeight;
      });
  
      y += lineHeight;
    });
  
    doc.save("mock_interview_review.pdf");
  };

  return (
    <div className="animated-gradient min-h-screen text-gray-800 flex flex-col items-center justify-start p-10">
      <div className="max-w-5xl w-full space-y-8">
  <div className="flex justify-start">
    <Button
      onClick={() => navigate("/")}
      variant="ghost"
      className="text-sm text-gray-600 hover:text-black flex items-center gap-2"
    >
      ← Back to Home
    </Button>
  </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 text-gray-700">
            <Mic className="w-7 h-7 text-green" />
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

        {!completed && !loading ? (
          <AnimatePresence mode="wait">
            {currentQuestion && (
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
                    {currentQuestion}
                  </p>
                  <Volume2 className="w-5 h-5 text-[#ba68c8] cursor-pointer" onClick={() => playWithElevenLabs(currentQuestion)} />
                </div>
                {showTextarea && (
                  <Textarea
                    value={responses[currentIndex - 1] || ""}
                    onChange={(e) => handleResponseChange(e.target.value)}
                    placeholder="Type your response here..."
                    rows={6}
                    className="rounded-lg border-gray-300 shadow-sm"
                  />
                )}
                <div className="flex flex-col space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-2">
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
            )}
          </AnimatePresence>
        ) : loading ? (
          <div className="relative flex flex-col items-center justify-center overflow-hidden bg-white/90 backdrop-blur-md rounded-2xl shadow-md p-10 animate-fade-in text-gray-700">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-200 via-transparent to-pink-100 opacity-30 animate-pulse-slow z-0" />
            <div className="relative z-10 flex flex-col items-center space-y-4 text-center">
              <p className="text-xl font-medium animate-pulse">Analyzing your responses…</p>
              <div className="flex space-x-2 mt-1">
                <div className="w-3 h-3 bg-purple-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <div className="w-3 h-3 bg-purple-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <div className="w-3 h-3 bg-purple-400 rounded-full animate-bounce" />
              </div>
              <p className="text-sm text-gray-500 max-w-md">
                Our AI is preparing personalized feedback for you. This won’t take long.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-6 w-full">
            <div className="p-6 border-l-4 border-[#f8bbd0] bg-white/90 backdrop-blur-md rounded-2xl shadow-md">
              <h2 className="text-2xl font-semibold mb-2 text-gray-700">🧠 AI Feedback</h2>
              <div className="space-y-4">
                {feedbackList.map((f, idx) => (
                  <div key={idx} className="border-t pt-3">
                    <p className="font-medium text-gray-800">Q{idx + 1}: {f.question}</p>
                    <p className="text-sm text-gray-700 mt-1">📝 <span className="font-semibold text-purple-700">Feedback:</span> {f.feedback}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6 border bg-white/90 backdrop-blur-md rounded-xl shadow space-y-4">
              <h2 className="text-lg font-semibold text-gray-700">Review Your Interview</h2>
              {questions.map((q, idx) => (
                <div key={idx} className="border-t pt-3">
                  <p className="font-medium">Q{idx + 1}. {q}</p>
                  <p className="text-sm mt-1 text-gray-700">{responses[idx]?.trim() || <span className="italic text-red-500">Skipped</span>}</p>
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