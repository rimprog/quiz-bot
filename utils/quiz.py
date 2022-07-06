import os

from dotenv import load_dotenv


def get_quiz():
    questions_answers_path = os.getenv(
        'QUESTIONS_ANSWERS_PATH',
        default="quiz_questions/3f15.txt"
    )

    with open(questions_answers_path, "r", encoding="KOI8-R") as quiz_file:
      file_contents = quiz_file.read()
      questions_and_answers = file_contents.split('\n\n')

    merged_questions_and_answers = {}
    for sentence in questions_and_answers:
        if sentence.startswith('Вопрос'):
            question = sentence
        elif sentence.startswith('Ответ'):
            answer = sentence
            merged_questions_and_answers[question] = answer

    return merged_questions_and_answers
