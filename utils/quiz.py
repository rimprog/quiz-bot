import random


def get_quiz():
    with open("quiz_questions/3f15.txt", "r", encoding="KOI8-R") as my_file:
      file_contents = my_file.read()
      questions_and_answers = file_contents.split('\n\n')

    questions = []
    answers = []
    for sentence in questions_and_answers:
        if sentence.startswith('Вопрос'):
            questions.append(sentence)
        elif sentence.startswith('Ответ'):
            answers.append(sentence)

    merged_questions_and_answers = list(zip(questions, answers))

    return merged_questions_and_answers


def get_random_question():
    questions_and_answers = get_quiz()
    random_question_number = random.randint(1, len(questions_and_answers)-1)
    random_question = get_quiz()[random_question_number][0]

    return random_question


def get_answer(question):
    question_and_answer = list(
        filter(
            lambda question_and_answer: question_and_answer[0] == question,
            get_quiz()
        )
    )[0]
    answer = question_and_answer[1]

    return answer
