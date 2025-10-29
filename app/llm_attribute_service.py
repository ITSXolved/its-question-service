"""
LLM Attribute Generation Service using OpenRouter models for extracting
attributes and 3PL parameters from questions
"""
import os
import json
import requests
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMAttributeService:
    def __init__(self, api_key=None):
        """Initialize the LLM service with OpenRouter API credentials."""
        self.api_key = api_key 
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            raise ValueError("OpenRouter API key must be set in environment variables")
            
    # [Rest of your class code remains the same...]
    def get_headers(self) -> Dict[str, str]:
        """Generate request headers for OpenRouter API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
           # "HTTP-Referer": os.getenv("APP_URL", "https://your-app-url.com"),  # Replace with your app URL
            "X-Title": "Computer Adaptive Mastery Test System"
        }

    def extract_attributes(self,
                         question_text: str,
                         exam: str,
                         subject: str,
                         chapter: str,
                         topic: str,
                         concept: str,
                         model: str = "deepseek/deepseek-chat-v3-0324:free") -> List[Dict[str, str]]:
        """
        Extract cognitive attributes from question text based on educational hierarchy.

        Args:
            question_text: The question text to analyze
            exam: Exam name
            subject: Subject name
            chapter: Chapter name
            topic: Topic name
            concept: Concept name
            model: OpenRouter model to use

        Returns:
            List of attributes with name and description
        """
        prompt = f"""
        You are an expert cognitive diagnostic model specialist for educational assessment.

        Please analyze the following question and extract key knowledge attributes that a student
        needs to master to correctly answer it. Each attribute should represent a specific skill,
        knowledge component, or cognitive process required.

        Educational context:
        - Exam: {exam}
        - Subject: {subject}
        - Chapter: {chapter}
        - Topic: {topic}
        - Concept: {concept}

        Question: {question_text}

        Please identify 3-7 specific cognitive attributes needed to answer this question.
        For each attribute:
        1. Provide a concise name (2-5 words)
        2. Write a brief description explaining what this attribute entails

        Return your answer as a JSON array of objects with 'name' and 'description' keys.
        Example format:
        [
            {{"name": "Attribute name", "description": "Detailed description of the attribute"}},
            ...
        ]
        """

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1500
        }

        response = requests.post(
            self.api_url,
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")

        content = response.json()["choices"][0]["message"]["content"]

        # Extract JSON from the response
        try:
            # Try to parse the entire content as JSON
            attributes = json.loads(content)
        except json.JSONDecodeError:
            # If that fails, look for JSON array in the content
            import re
            json_match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
            if json_match:
                attributes = json.loads(json_match.group(0))
            else:
                raise ValueError("Could not parse attributes from LLM response")

        return attributes

    def generate_3pl_parameters(self,
                              question_text: str,
                              options: List[str],
                              correct_answer: str,
                              exam: str,
                              subject: str,
                              model: str = "deepseek/deepseek-chat-v3-0324:free") -> Dict[str, float]:
        """
        Generate 3PL (three-parameter logistic) model parameters for a question.

        Args:
            question_text: The question text
            options: List of answer options
            correct_answer: The correct answer
            exam: Exam name for context
            subject: Subject name for context
            model: OpenRouter model to use

        Returns:
            Dictionary with difficulty, discrimination, and guessing parameters
        """
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])

        prompt = f"""
        You are an expert in Item Response Theory and psychometrics.

        Please analyze the following multiple-choice question and estimate the three parameters
        for the 3PL (three-parameter logistic) model:

        1. Difficulty (b): A value between -3 (very easy) and 3 (very difficult), with 0 being average difficulty.
        2. Discrimination (a): A value between 0.5 and 2.5, where higher values indicate the item better discriminates between students of different ability levels.
        3. Guessing (c): A value between 0.05 and 0.5, representing the probability a student with minimal ability would answer correctly by guessing.

        Context:
        - Exam: {exam}
        - Subject: {subject}

        Question: {question_text}

        Options:
        {options_text}

        Correct answer: {correct_answer}

        For each parameter, provide a numerical value and a brief justification for your estimation.
        Return your answer as a JSON object with 'difficulty', 'discrimination', and 'guessing' keys.
        Example format:
        {{
            "difficulty": 1.2,
            "discrimination": 1.8,
            "guessing": 0.25,
            "justification": "Brief explanation of your reasoning"
        }}
        """

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 2000
        }

        response = requests.post(
            self.api_url,
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")

        content = response.json()["choices"][0]["message"]["content"]

        # Extract JSON from the response
        try:
            # Try to parse the entire content as JSON
            parameters = json.loads(content)
        except json.JSONDecodeError:
            # If that fails, look for JSON object in the content
            import re
            json_match = re.search(r'{.*}', content, re.DOTALL)
            if json_match:
                parameters = json.loads(json_match.group(0))
            else:
                raise ValueError("Could not parse 3PL parameters from LLM response")

        # Extract only the parameters we need
        return {
            "difficulty": parameters.get("difficulty", 0.0),
            "discrimination": parameters.get("discrimination", 1.0),
            "guessing": parameters.get("guessing", 0.25),
        }

    def process_question_attributes_and_parameters(self,
                                                      question_text: str,
                                                      options: List[str],
                                                      correct_answer: str,
                                                      exam: str,
                                                      subject: str,
                                                      chapter: str,
                                                      topic: str,
                                                      concept: str,
                                                      model: str = "deepseek/deepseek-chat-v3-0324:free") -> Tuple[List[Dict[str, str]], Dict[str, float]]:
        """
        Process a question to extract both attributes and 3PL parameters.

        Args:
            question_text: The question text
            options: List of answer options
            correct_answer: The correct answer
            exam, subject, chapter, topic, concept: Educational hierarchy
            model: OpenRouter model to use

        Returns:
            Tuple of (attributes, parameters)
        """
        # In a production environment, you might want to run these in parallel
        # For simplicity, we run them sequentially here
        attributes = self.extract_attributes(
            question_text, exam, subject, chapter, topic, concept, model
        )

        parameters = self.generate_3pl_parameters(
            question_text, options, correct_answer, exam, subject, model
        )

        return attributes, parameters

# Usage example

