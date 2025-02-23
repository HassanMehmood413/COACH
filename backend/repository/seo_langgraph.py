from typing import Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini LLM using Google's Generative AI
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7
)

async def optimize_content_for_seo(content: str) -> Dict[str, str]:
    """
    Optimize the input content using Gemini for SEO and social media platforms.
    
    Steps:
    1. Create a specialized prompt that instructs the LLM to optimize the content.
    2. Create a chain that connects the prompt and the LLM.
    3. Invoke the chain asynchronously with the given content.
    4. Parse the returned text into sections using the specified format.
    5. Return a dictionary with keys:
       - 'seo_content': Optimized text for SEO
       - 'facebook_content': Version tailored for Facebook posting
       - 'hashtags': A list of hashtags (split by commas)
       - 'meta_description': A short meta description
       - 'image_alt': Suggested alternative text for images
       - 'original_content': The original content
    6. If any error occurs during the process, catch the exception and return fallback values.
    """
    # Step 1: Create a prompt with clear instructions for optimization.
    seo_prompt = ChatPromptTemplate.from_template("""
        As an SEO expert, optimize this content for social media and search engines:
        {content}

        Please provide:
        1. SEO-optimized version with relevant keywords
        2. Facebook-optimized version (engaging, shareable)
        3. Key hashtags (max 5, comma-separated)
        4. Meta description (under 160 characters)
        5. Suggested image description for better accessibility
        
        Format the response exactly as follows:
        SEO_VERSION: [optimized content]
        FACEBOOK_VERSION: [facebook content]
        HASHTAGS: [comma-separated hashtags]
        META_DESCRIPTION: [meta description]
        IMAGE_ALT: [image description]
    """)
    
    # Step 2: Create a chain connecting the prompt with the Gemini LLM.
    seo_chain = seo_prompt | llm
    
    try:
        # Step 3: Execute the chain asynchronously.
        result = await seo_chain.ainvoke({"content": content})
        response_text = result.content
        
        # Step 4: Parse the returned text.
        sections = {}
        current_section = None
        current_content = []
        for line in response_text.split('\n'):
            line = line.strip()
            if line:
                # Check if the line starts with one of the expected section headers.
                if ':' in line:
                    header, value = line.split(':', 1)
                    header = header.strip().upper()
                    if header in ['SEO_VERSION', 'FACEBOOK_VERSION', 'HASHTAGS', 'META_DESCRIPTION', 'IMAGE_ALT']:
                        # Save previous section if any.
                        if current_section:
                            sections[current_section] = '\n'.join(current_content).strip()
                        current_section = header
                        current_content = [value.strip()]
                    else:
                        # Append to current section content if it doesn't look like a header.
                        if current_section:
                            current_content.append(line)
                else:
                    if current_section:
                        current_content.append(line)
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # Step 5: Build the return dictionary with default fallbacks.
        return {
            "seo_content": sections.get('SEO_VERSION', content),
            "facebook_content": sections.get('FACEBOOK_VERSION', content),
            "hashtags": [tag.strip() for tag in sections.get('HASHTAGS', '').split(',') if tag.strip()],
            "meta_description": sections.get('META_DESCRIPTION', ''),
            "image_alt": sections.get('IMAGE_ALT', ''),
            "original_content": content
        }
    except Exception as e:
        print(f"SEO optimization error: {str(e)}")
        # Step 6: Fallback: return the original content with basic defaults.
        return {
            "seo_content": content,
            "facebook_content": content,
            "hashtags": [],
            "meta_description": content[:157] + "..." if len(content) > 160 else content,
            "image_alt": "",
            "original_content": content
        }
