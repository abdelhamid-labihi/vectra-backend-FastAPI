from dotenv import load_dotenv
import json
from lib import (
    cv_to_json,
    Experiences,
    Resume,
    generate_experience,
    generate_skills,
)
from fastapi import (
    Depends,
    FastAPI,
    Response,
    UploadFile,
)
from auth import (
    MagicNumberBody,
    UserLogin,
    UserSignup,
    get_current_user,
    login,
    sign_up,
    validate_magic_number,
)

load_dotenv()

app = FastAPI()


@app.post("/enhance_experience")
async def enhance_experience(experiences_input_json: Experiences):
    return await generate_experience(experiences_input_json)


@app.post("/suggest_skills")
async def suggest_skills(resume_json: Resume):
    return await generate_skills(resume_json)


@app.post("/resume_to_json")
async def test_resume_upload(resume_file: UploadFile):
    resume_binary = await resume_file.read()
    resume_json = cv_to_json(resume_binary)
    return resume_json


@app.post("/signup")
async def handle_sign_up(user_info: UserSignup):
    return await sign_up(user_info)


@app.post("/login")
async def handle_login(user_info: UserLogin):
    return await login(user_info)


@app.post("/verify")
async def verify(response: Response, magic_number: MagicNumberBody):
    return await validate_magic_number(response, magic_number)


@app.get("/protected")
def protected_route(json_user: str = Depends(get_current_user)):
    current_user = json.loads(json_user)
    return {
        "message": f"Hello {current_user['first_name']} {current_user['last_name']}"
    }
