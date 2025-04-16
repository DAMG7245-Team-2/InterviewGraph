import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const MermaidComponent = ({ children }: { children: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize Mermaid
    mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  themeVariables: {
    fontFamily: 'sans-serif',
    fontSize: '16px',
    textColor: 'text-white',
    nodeTextColor: '#ffffff',
    labelColor: 'white'
  }
});

    // Generate a unique ID for the diagram
    const uniqueId = `mermaid-${Math.random().toString(36).substr(2, 9)}`;

    // Render the diagram
    if (containerRef.current) {
      mermaid
        .render(uniqueId, children)
        .then(({ svg, bindFunctions }) => {
          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
            if (bindFunctions) {
              bindFunctions(containerRef.current);
            }
          }
        })
        .catch((error) => {
          console.error('Mermaid render error:', error);
        });
    }
  }, [children]);

  return <div ref={containerRef} />;
};

export default MermaidComponent;