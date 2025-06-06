from pydantic import BaseModel

class CourseBase(BaseModel):
    name: str
    description: str

class CourseCreate(CourseBase):
    pass

class CourseUpdate(CourseBase):
    pass

class CourseOut(CourseBase):
    id: int

    class Config:
        orm_mode = True
