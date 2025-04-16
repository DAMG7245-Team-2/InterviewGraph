import re
import os
import requests

def read_markdown(filepath: str) -> str:
    """Read markdown content from a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def extract_links(md_content: str, topic_name: str):
    """Extract all [title](url) links under a specific topic header."""
    pattern = rf"## {re.escape(topic_name)}\s+(.*?)(?=\n## |\Z)"
    match = re.search(pattern, md_content, re.DOTALL)
    if not match:
        return []
    section_text = match.group(1)
    return re.findall(r'\* \[(.*?)\]\((http.*?)\)', section_text)

def fetch_via_jina(url: str) -> str:
    """Fetch text using JinaAI's summarization endpoint."""
    try:
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error fetching {url} via Jina: {e}"

def save_markdown(topic: str, title: str, url: str, content: str, output_dir: str = "scraped_md"):
    """Save the scraped content as a Markdown file."""
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", title.strip())[:50]
    filename = os.path.join(output_dir, f"{topic}_{safe_title}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n**Source**: {url}\n\n---\n\n{content}")

def scrape_topic_links(md_content: str, topics: list):
    """Main logic to extract, scrape and save topic links."""
    os.makedirs("scraped_md", exist_ok=True)
    
    for topic in topics:
        links = extract_links(md_content, topic)
        print(f"\n TOPIC: {topic} ({len(links)} links)")
        for title, url in links:
            print(f"- {title}: {url}")
        
        for title, url in links:
            print(f"\n Scraping: {title}\nURL: {url}")
            content = fetch_via_jina(url)
            
            print(f"\n Markdown preview ({title}):\n")
            print(content[:1000])
            
            save_markdown(topic, title, url, content)

def main():
    filepath = "scraped_md/interviewQA_README.md"
    topics = ["DevOps", "Algorithms", "Data structures", "Networks"]  
    md_content = read_markdown(filepath)
    scrape_topic_links(md_content, topics)

if __name__ == "__main__":
    main()
