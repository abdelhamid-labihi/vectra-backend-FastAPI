from datetime import datetime
import json
import uuid
from openai import OpenAI
from pydantic import BaseModel
from typing import List
from mindee import Client, product  # type: ignore
from orm import db
from orm import User  # type: ignore


class UserSignup(BaseModel):
    first_name: str
    last_name: str
    email: str


class UserLogin(BaseModel):
    email: str


class MagicNumberBody(BaseModel):
    magic_number: str


class ExperienceItem(BaseModel):
    job_title: str
    company: str
    description: List[str]


class Experiences(BaseModel):
    experience: List[ExperienceItem]


class Resume(BaseModel):
    skills: List[str]
    job_title: str
    company: str
    job_description: str


def cv_to_json(resume_binary: bytes):
    mindee_client = Client()
    resume = mindee_client.source_from_bytes(resume_binary, "Resume.pdf")
    result = mindee_client.enqueue_and_parse(
        product.ResumeV1,  # type: ignore
        resume,
    )
    return result.document


def load_template(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def inject_variables(template, variables):
    for key, value in variables.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template


def is_user_email_duplicate(user_email):
    if db.query(User).filter_by(email=user_email).first():
        return True
    return False


def create_user(user_info: UserSignup):
    new_user = User(
        id=str(uuid.uuid4()),
        first_name=user_info.first_name,
        last_name=user_info.last_name,
        email=user_info.email,
        verified=False,
        created_at=datetime.now(),
    )
    db.add(new_user)
    db.commit()
    return new_user


def get_user(user_email):
    user = db.query(User).filter_by(email=user_email).first()
    return user


client = OpenAI()


async def generate_skills(resume_json: Resume):
    resume = json.dumps(resume_json.model_dump())

    file_path = "./system_prompts/Skills Section - System Prompt Vectra.txt"
    with open(file_path, "r") as file:
        skills_system_prompt_json = file.read()
    skills_system_prompt = json.dumps(skills_system_prompt_json)

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": skills_system_prompt},
            {"role": "user", "content": resume},
        ],
    )
    content = response.choices[0].message.content
    if content is None:
        content = ""
    return json.loads(content)


async def generate_experience(experiences_input_json: Experiences):
    experiences_input = json.dumps(experiences_input_json.model_dump())

    file_path = "./system_prompts/Experience Section - System Prompt Vectra.txt"
    with open(file_path, "r") as file:
        experience_system_prompt_json = file.read()
    experience_system_prompt = json.dumps(experience_system_prompt_json)

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": experience_system_prompt},
            {"role": "user", "content": experiences_input},
        ],
    )
    content = response.choices[0].message.content
    if content is None:
        content = ""
    return json.loads(content)
