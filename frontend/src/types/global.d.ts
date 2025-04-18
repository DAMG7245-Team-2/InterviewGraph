interface Window {
  SpeechRecognition: typeof SpeechRecognition;
  webkitSpeechRecognition: typeof SpeechRecognition;
}

declare const ELEVENLABS_API_KEY: string;

interface JobDescription {
  title: string;
  description: string;
}

declare module '@/styles/animated-gradient.css';