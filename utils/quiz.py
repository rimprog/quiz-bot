import os
import random

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


def get_random_question(questions_and_answers):
    random_question, random_answer = random.choice(list(questions_and_answers.items()))

    return random_question


def get_answer(question, questions_and_answers):
    question_and_answer = list(
        filter(
            lambda question_and_answer: question_and_answer[0] == question,
            questions_and_answers.items()
        )
    )[0]

    answer = question_and_answer[1]

    return answer
