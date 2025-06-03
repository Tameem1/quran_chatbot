# main.py
#!/usr/bin/env python3
"""
Run the Quranic QA chatbot from the command line:

    python main.py "ما معنى كلمة غفر؟"
"""
import sys
from pipeline import QuranQAPipeline


def main() -> None:
    if len(sys.argv) < 2:
        print("💡 Usage: python main.py \"<سؤالك بالعربية>\"")
        sys.exit(1)

    question = sys.argv[1]
    pipeline = QuranQAPipeline()
    answer = pipeline.answer_question(question)
    print(answer)


if __name__ == "__main__":
    main()